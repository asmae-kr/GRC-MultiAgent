"""
Agent 4 — Compliance Counter Agent (anciennement Risk Scorer)
Ne calcule plus de score global sur 100 — compte simplement combien de
questions sont Conforme / Partiellement conforme / Non conforme.
Calcul déterministe (pas d'IA), pour rester exact et vérifiable.
"""
from typing import List
from models import ComplianceResult, ComplianceCounts


class RiskScorerAgent:

    def __init__(self):
        self.name = "Compliance Counter Agent"

    def score(self, results: List[ComplianceResult]) -> ComplianceCounts:
        if not results:
            return ComplianceCounts(success=False, error="Aucun résultat à compter.")

        conforme = sum(1 for r in results if r.status == "Conforme")
        partiel = sum(1 for r in results if r.status == "Partiellement conforme")
        non_conforme = sum(1 for r in results if r.status == "Non conforme")

        return ComplianceCounts(
            success=True,
            total_questions=len(results),
            conforme_count=conforme,
            partiellement_conforme_count=partiel,
            non_conforme_count=non_conforme,
        )