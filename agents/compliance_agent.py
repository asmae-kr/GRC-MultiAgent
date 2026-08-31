"""
Agent 3 — Compliance Evaluator Agent
Utilise l'outil URL Context pour lire un lien de preuve précis si présent.
Se base à la fois sur : (1) le requirement de chaque ligne, ET
(2) le fichier de critères de référence complet, si celui-ci est fourni.
Génère des questions de clarification pour "Partiellement conforme" ET
"Non conforme" — pas seulement pour "Partiellement conforme".
"""
from typing import List, Optional
from models import MatchedResponse, ComplianceResult, ComplianceResponse
from agents.llm_helper import ask_claude_for_json

STATUS_SCORE = {"Conforme": 5, "Partiellement conforme": 3, "Non conforme": 1, "Non applicable": None}

SYSTEM_PROMPT = """Tu es un auditeur expert en cybersécurité et conformité GRC.

Pour chaque exigence et réponse associée, détermine "Conforme",
"Partiellement conforme" ou "Non conforme", avec une justification courte.

Si un DOCUMENT DE RÉFÉRENCE est fourni ci-dessous, base ton jugement sur le
niveau de détail précis qu'il décrit pour chaque critère.

Si un lien de preuve est fourni, consulte-le et prends son contenu réel en
compte dans ton jugement. Si le lien est illisible/inaccessible, indique-le.

Si la réponse est "Aucune réponse trouvée", le statut doit être "Non conforme".

Si la reponse indique "NA" (non applicable, ou equivalent explicite de non-applicabilite),
le statut doit etre "Non applicable". Dans ce cas, ne pose aucune question de clarification
(follow_up_questions reste vide) et la justification doit expliquer brievement pourquoi
l'exigence ne s'applique pas a ce fournisseur.

Si le statut est "Partiellement conforme" ou "Non conforme", ajoute 1 à 3
questions de clarification précises à poser au fournisseur pour obtenir
les informations manquantes ou lever l'ambiguïté. Si le statut est
"Conforme", laisse la liste vide.

Réponds UNIQUEMENT avec un JSON de cette forme :
{
  "results": [
    {
      "requirement_id": "REQ-001",
      "status": "Partiellement conforme",
      "justification": "...",
      "follow_up_questions": ["...", "..."]
    }
  ]
}"""


class ComplianceEvaluatorAgent:

    def __init__(self):
        self.name = "Compliance Evaluator Agent"

    def evaluate(
        self,
        matches: List[MatchedResponse],
        reference_text: Optional[str] = None,
    ) -> ComplianceResponse:
        if not matches:
            return ComplianceResponse(success=False, error="Aucune correspondance à évaluer.")

        with_link = [m for m in matches if m.proof_link]
        without_link = [m for m in matches if not m.proof_link]

        results: List[ComplianceResult] = []

        try:
            if without_link:
                results += self._evaluate_batch(without_link, reference_text, use_url_context=False)
            if with_link:
                for m in with_link:
                    results += self._evaluate_batch([m], reference_text, use_url_context=True)

            return ComplianceResponse(success=True, results=results)

        except Exception as e:
            return ComplianceResponse(success=False, error=str(e))

    def _evaluate_batch(
        self,
        matches: List[MatchedResponse],
        reference_text: Optional[str],
        use_url_context: bool,
    ) -> List[ComplianceResult]:
        matches_text = "\n".join(
            f"- {m.requirement_id} | Exigence: {m.requirement} | "
            f"Réponse: {m.matched_text}"
            + (f" | Lien de preuve à consulter : {m.proof_link}" if m.proof_link else "")
            for m in matches
        )

        reference_block = (
            f"DOCUMENT DE RÉFÉRENCE (à utiliser pour juger le niveau de détail attendu) :\n{reference_text}\n\n"
            if reference_text else ""
        )

        data = ask_claude_for_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"{reference_block}Paires à évaluer :\n{matches_text}",
            use_url_context=use_url_context,
        )

        match_by_id = {m.requirement_id: m for m in matches}
        results = []
        for r in data.get("results", []):
            m = match_by_id.get(r["requirement_id"])
            if m is None:
                continue
            status = r.get("status", "Non conforme")
            results.append(
                ComplianceResult(
                    requirement_id=m.requirement_id,
                    criterion=m.criterion,
                    status=status,
                    score=STATUS_SCORE.get(status),
                    justification=r.get("justification", ""),
                    importance=m.importance,
                    proof_link_checked=bool(m.proof_link),
                    follow_up_questions=r.get("follow_up_questions", []),
                )
            )
        return results