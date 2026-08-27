"""
Version simplifiée : plus de RAG / vector store.
Ce module a un seul rôle : lire le texte du document de référence
(grille de critères) UNE FOIS, au démarrage de l'API, et le garder
en mémoire pour que les agents puissent s'en servir directement.
"""
from config import REFERENCE_DOCUMENT_PATH


def load_reference_text() -> str:
    """
    Lit le contenu du document de référence sur disque.
    Supporte pour l'instant un fichier .txt (le plus simple).
    Si vous déposez un .pdf ou .docx, convertissez-le d'abord en .txt,
    ou adaptez cette fonction avec une librairie de lecture adaptée
    (ex: python-docx, pypdf) — dites-le-moi si besoin, je l'ajoute.
    """
    try:
        with open(REFERENCE_DOCUMENT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Document de référence introuvable : {REFERENCE_DOCUMENT_PATH}. "
            "Déposez votre fichier de critères dans le dossier reference_docs/."
        )


# Chargé une seule fois, au moment où ce module est importé (donc au démarrage de l'API)
REFERENCE_TEXT = load_reference_text()
