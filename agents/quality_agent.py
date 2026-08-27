"""
Agent 6 — Quality Checker Agent
Rôle : dernier filet de sécurité avant d'envoyer le résultat à Power Automate.
Vérifie la cohérence générale — PAS besoin d'IA ici non plus, ce sont des
vérifications simples et rapides en code Python (donc pas de coût API, pas
de lenteur supplémentaire).
"""
from models import FinalReport, QualityCheckResponse


class QualityCheckerAgent:

    def __init__(self):
        self.name = "Quality Checker Agent"

    def check(self, report: FinalReport) -> QualityCheckResponse:
        issues = []

        if not report.compliance_results:
            issues.append("Aucun critère évalué.")

        for r in report.compliance_results:
            if not r.justification or not r.justification.strip():
                issues.append(f"Justification manquante pour le critère '{r.criterion}'.")
            if r.status not in ("Conforme", "Partiellement conforme", "Non conforme"):
                issues.append(f"Statut invalide pour le critère '{r.criterion}' : '{r.status}'.")

        if report.total_questions != len(report.compliance_results):
            issues.append("Le nombre total de questions ne correspond pas au détail fourni.")

        if not report.executive_summary or not report.executive_summary.strip():
            issues.append("Résumé exécutif manquant.")

        return QualityCheckResponse(success=True, passed=(len(issues) == 0), issues=issues)
