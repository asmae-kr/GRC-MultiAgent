"""
Agent 2 — Response Matcher Agent
Cas Excel : la paire exigence/réponse est déjà connue -> pas d'appel IA, on la réutilise.
Cas texte libre / exigence du référentiel sans réponse déjà associée -> l'IA cherche.
"""
from typing import List, Dict
from models import Requirement, MatchedResponse, MatchingResponse
from agents.llm_helper import ask_claude_for_json

SYSTEM_PROMPT = """Tu es un assistant qui associe des exigences de sécurité
à des réponses de fournisseur.

Pour CHAQUE exigence fournie, retrouve dans le texte disponible le passage
qui y répond. S'il n'y a aucune réponse correspondante, mets
"matched_text": "Aucune réponse trouvée".

Réponds UNIQUEMENT avec un JSON de cette forme :
{
  "matches": [
    {"requirement_id": "REQ-001", "matched_text": "..."}
  ]
}"""


class ResponseMatcherAgent:

    def __init__(self):
        self.name = "Response Matcher Agent"

    def match(
        self,
        requirements: List[Requirement],
        supplier_text: str,
        excel_pairs: Dict[str, dict] = None,
    ) -> MatchingResponse:

        if not requirements:
            return MatchingResponse(success=False, error="Aucune exigence à traiter.")

        excel_pairs = excel_pairs or {}
        matches: List[MatchedResponse] = []
        requirements_needing_ai_matching = []

        for r in requirements:
            if r.source == "excel" and r.requirement in excel_pairs:
                pair = excel_pairs[r.requirement]
                matches.append(
                    MatchedResponse(
                        requirement_id=r.id,
                        criterion=r.criterion,
                        requirement=r.requirement,
                        matched_text=pair["response"],
                        importance=r.importance,
                        proof_link=pair.get("proof_link"),
                    )
                )
            else:
                requirements_needing_ai_matching.append(r)

        if requirements_needing_ai_matching:
            if not supplier_text or not supplier_text.strip():
                for r in requirements_needing_ai_matching:
                    matches.append(
                        MatchedResponse(
                            requirement_id=r.id, criterion=r.criterion, requirement=r.requirement,
                            matched_text="Aucune réponse trouvée", importance=r.importance,
                        )
                    )
            else:
                requirements_list = "\n".join(
                    f"- {r.id} : {r.criterion} — {r.requirement}" for r in requirements_needing_ai_matching
                )
                try:
                    data = ask_claude_for_json(
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=f"Exigences à couvrir :\n{requirements_list}\n\nTexte disponible :\n{supplier_text}",
                    )
                    req_by_id = {r.id: r for r in requirements_needing_ai_matching}
                    for m in data.get("matches", []):
                        req = req_by_id.get(m["requirement_id"])
                        if req is None:
                            continue
                        matches.append(
                            MatchedResponse(
                                requirement_id=req.id, criterion=req.criterion, requirement=req.requirement,
                                matched_text=m.get("matched_text", "Aucune réponse trouvée"),
                                importance=req.importance,
                            )
                        )
                except Exception as e:
                    return MatchingResponse(success=False, error=str(e))

        return MatchingResponse(success=True, matches=matches)