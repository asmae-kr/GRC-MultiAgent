"""
Modèles de données partagés entre tous les agents.
"""
from pydantic import BaseModel, Field
from typing import List, Optional

# ── Entrée reçue depuis Power Automate ──────────────────────────────
class SupplierResponseItem(BaseModel):
    """Une ligne déjà présente dans l'Excel du fournisseur :
    une exigence + la réponse associée, éventuellement un lien de preuve."""
    requirement: str
    response_text: str
    proof_link: Optional[str] = None


class AgentRequest(BaseModel):
    document_id: str
    text: str = ""                                             # cas PDF/Word : texte libre
    excel_rows: Optional[List[SupplierResponseItem]] = None     # cas Excel : déjà structuré


# ── Agent 0 : Document Parser ───────────────────────────────────────
class ParsedDocument(BaseModel):
    success: bool
    text: str = ""
    text_length: int = 0
    error: Optional[str] = None


# ── Agent 1 : Requirement Extractor ─────────────────────────────────
class Requirement(BaseModel):
    id: str
    criterion: str
    requirement: str
    importance: str
    source: str = "reference_file"  # "reference_file" ou "excel"


class RequirementExtractionResponse(BaseModel):
    success: bool
    requirements: List[Requirement] = []
    error: Optional[str] = None


# ── Agent 2 : Response Matcher ──────────────────────────────────────
class MatchedResponse(BaseModel):
    requirement_id: str
    criterion: str
    requirement: str
    matched_text: str
    importance: str
    proof_link: Optional[str] = None


class MatchingResponse(BaseModel):
    success: bool
    matches: List[MatchedResponse] = []
    error: Optional[str] = None


# ── Agent 3 : Compliance Evaluator ──────────────────────────────────
class ComplianceResult(BaseModel):
    requirement_id: str
    criterion: str
    status: str
    score: int              # ← nouveau : 5 (Conforme) / 3 (Partiel) / 1 (Non conforme)
    justification: str
    importance: str
    proof_link_checked: bool = False
    follow_up_questions: List[str] = []

class ComplianceResponse(BaseModel):
    success: bool
    results: List[ComplianceResult] = []
    error: Optional[str] = None


# ── Agent 4 : Risk Scorer ───────────────────────────────────────────
class ComplianceCounts(BaseModel):
    success: bool
    total_questions: int = 0
    conforme_count: int = 0
    partiellement_conforme_count: int = 0
    non_conforme_count: int = 0
    error: Optional[str] = None

# ── Agent 5 : Report Generator ──────────────────────────────────────
class FinalReport(BaseModel):
    document_id: str
    executive_summary: str
    total_questions: int
    conforme_count: int
    partiellement_conforme_count: int
    non_conforme_count: int
    compliance_results: List[ComplianceResult]
    main_risks: List[str]
    recommendations: List[str]

class ReportResponse(BaseModel):
    success: bool
    report: Optional[FinalReport] = None
    error: Optional[str] = None


# ── Agent 6 : Quality Checker ───────────────────────────────────────
class QualityCheckResponse(BaseModel):
    success: bool
    passed: bool
    issues: List[str] = []

    # ── Nouveau : format d'entrée basé sur l'Excel structuré ───────────
class ExcelRow(BaseModel):
    domain: Optional[str] = None
    requirement: str
    question: Optional[str] = None
    criticality: Optional[str] = None   # High / Medium / Low (à confirmer selon vos valeurs réelles)
    response: str
    justification: Optional[str] = None  # texte libre, peut contenir une URL

class ExcelAgentRequest(BaseModel):
    document_id: str
    excel_rows: List[ExcelRow]

# ── Entrée unifiée, quel que soit le format d'origine (PDF/Word/Excel) ──
class UnifiedAgentRequest(BaseModel):
    document_id: str
    # Cas PDF/Word : texte libre extrait par OCR (Power Automate)
    text: Optional[str] = None
    # Cas Excel : lignes déjà structurées (requirement + réponse)
    excel_rows: Optional[List[ExcelRow]] = None

    # ── Format réel reçu depuis Power Automate (fichier RFP SaaS/Cloud) ────
class QuestionnaireRow(BaseModel):
    Domain: str = ""
    Requirement: str = ""
    question: str = Field("", alias="Question / Description")
    Criticality: str = "Standard"
    response: str = Field("", alias="Response (Y/N/P/NA)")
    comments: str = Field("", alias="Comments / Evidence reference")

    class Config:
        populate_by_name = True


class CoverField(BaseModel):
    Champ: str
    Valeur: str = ""


class IncomingJob(BaseModel):
    file_type: str
    document_id: Optional[str] = None
    cover: List[CoverField] = []
    questionnaire: List[QuestionnaireRow] = []