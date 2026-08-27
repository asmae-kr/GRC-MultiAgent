"""
Agent 5 — Report Generator Agent
Rédige la synthèse à partir des comptages (Conforme/Partiel/Non conforme),
plus le détail complet par question (avec son score individuel).
"""
from typing import List
from models import ComplianceResult, FinalReport, ReportResponse
from agents.llm_helper import ask_claude_for_json

SYSTEM_PROMPT = """Tu es un consultant en cybersécurité qui rédige la synthèse
d'un rapport d'évaluation fournisseur pour un public managérial (non technique).

À partir des résultats de conformité fournis (avec le nombre de questions
Conforme / Partiellement conforme / Non conforme), rédige :
- un résumé exécutif (3-4 phrases)
- une liste des principaux risques identifiés (points non conformes ou critiques)
- une liste de recommandations concrètes

Réponds UNIQUEMENT avec un JSON de cette forme :
{
  "executive_summary": "...",
  "main_risks": ["...", "..."],
  "recommendations": ["...", "..."]
}"""


class ReportGeneratorAgent:

    def __init__(self):
        self.name = "Report Generator Agent"

    def generate(
        self,
        document_id: str,
        results: List[ComplianceResult],
        total_questions: int,
        conforme_count: int,
        partiellement_conforme_count: int,
        non_conforme_count: int,
    ) -> ReportResponse:
        if not results:
            return ReportResponse(success=False, error="Aucun résultat à synthétiser.")

        results_text = "\n".join(
            f"- {r.criterion} ({r.importance}) : {r.status} (score {r.score}/5) — {r.justification}"
            for r in results
        )

        try:
            data = ask_claude_for_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=(
                    f"Résultats : {conforme_count} Conforme / "
                    f"{partiellement_conforme_count} Partiellement conforme / "
                    f"{non_conforme_count} Non conforme (sur {total_questions} questions)\n\n"
                    f"Détail des résultats :\n{results_text}"
                ),
            )

            report = FinalReport(
                document_id=document_id,
                executive_summary=data.get("executive_summary", ""),
                total_questions=total_questions,
                conforme_count=conforme_count,
                partiellement_conforme_count=partiellement_conforme_count,
                non_conforme_count=non_conforme_count,
                compliance_results=results,
                main_risks=data.get("main_risks", []),
                recommendations=data.get("recommendations", []),
            )

            return ReportResponse(success=True, report=report)

        except Exception as e:
            return ReportResponse(success=False, error=str(e))