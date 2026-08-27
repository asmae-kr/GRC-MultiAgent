"""
Agent 0 — Document Parser Agent
Rôle : valider et nettoyer le texte du fournisseur reçu de Power Automate,
AVANT de le transmettre aux agents suivants (qui, eux, appellent l'IA
et coûtent donc du temps/argent — inutile de les déclencher sur du texte vide).
"""
from models import ParsedDocument


class DocumentParserAgent:

    def __init__(self):
        self.name = "Document Parser Agent"

    def process(self, text: str) -> ParsedDocument:
        if not text or not text.strip():
            return ParsedDocument(
                success=False,
                error="Le document est vide ou n'a pas pu être lu.",
            )

        cleaned = text.strip()
        return ParsedDocument(
            success=True,
            text=cleaned,
            text_length=len(cleaned),
        )
