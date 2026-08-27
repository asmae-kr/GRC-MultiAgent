"""
Orchestrateur — utilisé par api/routes.py (endpoint HTTP /agent/requirements).
S'adapte au format reçu : texte libre (PDF/Word) ou excel_rows déjà structuré.
"""
from typing import List, Optional
from models import MatchedResponse
from agents.document_parser import DocumentParserAgent
from agents.requirement_agent import RequirementExtractorAgent
from agents.matching_agent import ResponseMatcherAgent
from agents.compliance_agent import ComplianceEvaluatorAgent
from agents.risk_agent import RiskScorerAgent
from agents.report_agent import ReportGeneratorAgent
from agents.quality_agent import QualityCheckerAgent
from rag.document_loader import REFERENCE_TEXT

document_parser = DocumentParserAgent()
requirement_extractor = RequirementExtractorAgent()
response_matcher = ResponseMatcherAgent()
compliance_evaluator = ComplianceEvaluatorAgent()
risk_scorer = RiskScorerAgent()
report_generator = ReportGeneratorAgent()
quality_checker = QualityCheckerAgent()


def _run_from_text(supplier_text: str):
    parsed = document_parser.process(supplier_text)
    if not parsed.success:
        return None, {"success": False, "step": "document_parser", "error": parsed.error}

    extraction = requirement_extractor.analyze(REFERENCE_TEXT)
    if not extraction.success:
        return None, {"success": False, "step": "requirement_extractor", "error": extraction.error}

    matching = response_matcher.match(extraction.requirements, parsed.text)
    if not matching.success:
        return None, {"success": False, "step": "response_matcher", "error": matching.error}

    return matching.matches, None


def _run_from_excel(excel_rows: list):
    if not excel_rows:
        return None, {"success": False, "step": "input", "error": "Aucune ligne Excel reçue."}

    matches = [
        MatchedResponse(
            requirement_id=f"REQ-{i:03d}",
            criterion=row.get("requirement", ""),
            requirement=row.get("requirement", ""),
            matched_text=(row.get("response") or "").strip() or "Aucune réponse trouvée",
            importance="High",
            proof_link=row.get("proof_link"),
        )
        for i, row in enumerate(excel_rows, start=1)
    ]
    return matches, None


def run_pipeline(document_id: str, text: Optional[str] = None, excel_rows: Optional[list] = None) -> dict:
    if excel_rows:
        matches, error = _run_from_excel(excel_rows)
    elif text:
        matches, error = _run_from_text(text)
    else:
        return {"success": False, "step": "input", "error": "Ni 'text' ni 'excel_rows' n'ont été fournis."}

    if error:
        return error

    compliance = compliance_evaluator.evaluate(matches, reference_text=REFERENCE_TEXT)
    if not compliance.success:
        return {"success": False, "step": "compliance_evaluator", "error": compliance.error}

    counts = risk_scorer.score(compliance.results)
    if not counts.success:
        return {"success": False, "step": "risk_scorer", "error": counts.error}

    report_response = report_generator.generate(
        document_id=document_id,
        results=compliance.results,
        total_questions=counts.total_questions,
        conforme_count=counts.conforme_count,
        partiellement_conforme_count=counts.partiellement_conforme_count,
        non_conforme_count=counts.non_conforme_count,
    )
    if not report_response.success:
        return {"success": False, "step": "report_generator", "error": report_response.error}

    quality = quality_checker.check(report_response.report)

    return {
        "success": True,
        "quality_passed": quality.passed,
        "quality_issues": quality.issues,
        "report": report_response.report.model_dump(),
    }