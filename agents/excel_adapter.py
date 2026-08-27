"""
Adapte le format réel du questionnaire (Domain, Requirement, Question,
Criticality, Response, Comments) vers le format interne MatchedResponse
utilisé par l'Agent 3 (Compliance Evaluator) et les suivants.
"""
import re
from typing import List
from models import QuestionnaireRow, MatchedResponse

CRITICALITY_TO_IMPORTANCE = {
    "Major": "High",
    "Standard": "Medium",
    "Minor": "Low",
}

URL_PATTERN = re.compile(r"https?://\S+")


def extract_proof_link(comments: str) -> str | None:
    """Cherche une URL dans le champ commentaires/preuves, s'il y en a une."""
    if not comments:
        return None
    match = URL_PATTERN.search(comments)
    return match.group(0) if match else None


def questionnaire_to_matches(rows: List[QuestionnaireRow]) -> List[MatchedResponse]:
    matches = []
    for i, row in enumerate(rows, start=1):
        response_text = row.response.strip() if row.response else ""
        if row.comments:
            response_text = f"{response_text} (Commentaire fournisseur : {row.comments})".strip()

        matches.append(
            MatchedResponse(
                requirement_id=f"REQ-{i:03d}",
                criterion=row.Requirement,
                requirement=f"{row.Requirement} — {row.question}",
                matched_text=response_text if response_text else "Aucune réponse trouvée",
                importance=CRITICALITY_TO_IMPORTANCE.get(row.Criticality, "Medium"),
                proof_link=extract_proof_link(row.comments),
            )
        )
    return matches