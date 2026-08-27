"""
Surveille en continu le dossier OneDrive "A_Traiter", traite chaque nouveau
fichier JSON reçu de Power Automate, dépose le résultat JSON dans "Resultats",
ET génère automatiquement le rapport Excel final dans "Rapports".

Lancer avec : python watcher.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

from models import IncomingJob
from agents.excel_adapter import questionnaire_to_matches
from agents.compliance_agent import ComplianceEvaluatorAgent
from agents.risk_agent import RiskScorerAgent
from agents.report_agent import ReportGeneratorAgent
from agents.quality_agent import QualityCheckerAgent
from agents.excel_report import generate_excel_from_template
from rag.document_loader import REFERENCE_TEXT

import sys
from generate_report_pptx import generate_report_pptx

ONEDRIVE_ROOT = Path(r"C:\Users\asmae.kaddar\OneDrive - Accenture")
A_TRAITER = ONEDRIVE_ROOT / "A_Traiter"
TRAITES = ONEDRIVE_ROOT / "A_Traiter" / "Traites"
RESULTATS = ONEDRIVE_ROOT / "Resultats"
RAPPORTS = ONEDRIVE_ROOT / "Rapports"
TEMPLATE_PATH = ONEDRIVE_ROOT / "Modeles" / "Template_Rapport.xlsx"

POLL_INTERVAL_SECONDS = 10

compliance_evaluator = ComplianceEvaluatorAgent()
risk_scorer = RiskScorerAgent()
report_generator = ReportGeneratorAgent()
quality_checker = QualityCheckerAgent()


def process_file(filepath: Path):
    print(f"[Traitement] {filepath.name}")

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    inner = json.loads(raw["content"])
    inner["file_type"] = raw.get("file_type")

    job = IncomingJob(**inner)
    document_id = job.document_id or filepath.stem

    matches = questionnaire_to_matches(job.questionnaire)

    compliance = compliance_evaluator.evaluate(matches, reference_text=REFERENCE_TEXT)
    if not compliance.success:
        write_error_result(document_id, "compliance_evaluator", compliance.error, filepath)
        return

    counts = risk_scorer.score(compliance.results)
    if not counts.success:
        write_error_result(document_id, "risk_scorer", counts.error, filepath)
        return

    report_response = report_generator.generate(
        document_id=document_id,
        results=compliance.results,
        total_questions=counts.total_questions,
        conforme_count=counts.conforme_count,
        partiellement_conforme_count=counts.partiellement_conforme_count,
        non_conforme_count=counts.non_conforme_count,
    )
    if not report_response.success:
        write_error_result(document_id, "report_generator", report_response.error, filepath)
        return

    quality = quality_checker.check(report_response.report)

    result = {
        "success": True,
        "quality_passed": quality.passed,
        "quality_issues": quality.issues,
        "report": report_response.report.model_dump(),
    }
    write_result(document_id, result)

    # ── Génération du rapport Excel final ──────────────────────────
    try:
        RAPPORTS.mkdir(parents=True, exist_ok=True)
        supplier_name = next(
            (c["Valeur"] for c in inner.get("cover", []) if c["Champ"] == "Supplier name"),
            document_id,
        )
        safe_name = "".join(ch for ch in supplier_name if ch.isalnum() or ch in " -_").strip() or document_id
        excel_output = RAPPORTS / f"Rapport_{safe_name}.xlsx"
        generate_excel_from_template(str(TEMPLATE_PATH), inner, result, str(excel_output))
        print(f"[Rapport Excel] {excel_output.name} genere")
    except Exception as e:
        print(f"[Erreur generation Excel] {e}")
        # — Génération du rapport PowerPoint ——————
    try:
        RAPPORTS.mkdir(parents=True, exist_ok=True)
        pptx_output = RAPPORTS / f"Rapport_{safe_name}.pptx"
        generate_report_pptx(result, str(pptx_output), supplier_name=supplier_name)
        print(f"[Rapport PPTX] {pptx_output.name} genere")
    except Exception as e:
        print(f"[Erreur generation PPTX] {e}")

    TRAITES.mkdir(parents=True, exist_ok=True)
    shutil.move(str(filepath), str(TRAITES / filepath.name))
    print(f"[Termine] {filepath.name} -> resultat depose, fichier archive")


def write_result(document_id: str, result: dict):
    RESULTATS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTATS / f"Resultat_{document_id}_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def write_error_result(document_id: str, step: str, error: str, filepath: Path = None):
    write_result(document_id, {"success": False, "step": step, "error": error})
    print(f"[Erreur] {document_id} - etape {step} : {error}")
    if filepath:
        ERREURS = A_TRAITER / "Erreurs"
        ERREURS.mkdir(parents=True, exist_ok=True)
        shutil.move(str(filepath), str(ERREURS / filepath.name))


def main():
    print(f"Surveillance de : {A_TRAITER}")
    A_TRAITER.mkdir(parents=True, exist_ok=True)

    if not TEMPLATE_PATH.exists():
        print(f"[ATTENTION] Template introuvable : {TEMPLATE_PATH}")
        print("Deposez votre template Excel a cet emplacement avant de continuer.")

    while True:
        json_files = [f for f in A_TRAITER.glob("*.json") if f.is_file()]
        for filepath in json_files:
            try:
                process_file(filepath)
            except Exception as e:
                print(f"[Erreur inattendue] {filepath.name} : {e}")
                ERREURS = A_TRAITER / "Erreurs"
                ERREURS.mkdir(parents=True, exist_ok=True)
                shutil.move(str(filepath), str(ERREURS / filepath.name))
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()