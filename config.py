"""
Configuration centrale du projet.
Toutes les valeurs sensibles (clés API) viennent du fichier .env,
jamais écrites en dur dans le code.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # charge le contenu du fichier .env dans les variables d'environnement

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-flash-lite-latest"  # modèle utilisé par tous les agents (palier gratuit)

# Chemin vers votre document de référence (critères / ISO 27001 résumé).
# Ce fichier est lu UNE SEULE FOIS au démarrage de l'API (voir rag/document_loader.py) —
# pas de re-lecture à chaque fournisseur, pas de base vectorielle.
REFERENCE_DOCUMENT_PATH = os.path.join(
    os.path.dirname(__file__), "reference_docs", "grille_criteres.txt"
)