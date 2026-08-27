from fastapi import APIRouter
from models import UnifiedAgentRequest
from orchestrator.workflow import run_pipeline

router = APIRouter()


@router.post("/agent/requirements")
def evaluate_requirements(request: UnifiedAgentRequest):
    """
    Endpoint unique appelé par Power Automate, quel que soit le format
    d'origine du fichier (PDF, Word, ou Excel) — Power Automate envoie
    soit 'text' (PDF/Word), soit 'excel_rows' (Excel).
    """
    result = run_pipeline(
        document_id=request.document_id,
        text=request.text,
        excel_rows=request.excel_rows,
    )
    return result