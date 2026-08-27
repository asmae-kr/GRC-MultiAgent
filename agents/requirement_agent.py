"""
Agent 1 — Requirement Extractor Agent
Combine DEUX sources possibles : le fichier de critères de référence (si présent)
et les exigences déjà écrites dans l'Excel du fournisseur (si présentes).
"""
from typing import List, Optional
from models import Requirement, RequirementExtractionResponse
from agents.llm_helper import ask_claude_for_json

SYSTEM_PROMPT = """Tu es un expert en cybersécurité et conformité GRC.
Tu reçois potentiellement deux sources d'exigences :
1. Un référentiel de sécurité interne (le plus autoritaire)
2. Une liste d'exigences déjà présente dans le questionnaire du fournisseur

Ta tâche : produis une liste UNIQUE et fusionnée d'exigences, en :
- reprenant les exigences du questionnaire fournisseur
- les complétant avec les exigences du référentiel interne qui ne sont pas déjà couvertes
- indiquant "source": "excel" si l'exigence vient du questionnaire fournisseur,
  ou "source": "reference_file" si elle vient uniquement du référentiel interne

Réponds UNIQUEMENT avec un JSON de cette forme :
{
  "requirements": [
    {
      "id": "REQ-001",
      "criterion": "Nom court du critère",
      "requirement": "Description de l'exigence",
      "importance": "High",
      "source": "excel"
    }
  ]
}"""


class RequirementExtractorAgent:

    def __init__(self):
        self.name = "Requirement Extractor Agent"

    def analyze(
        self,
        reference_text: Optional[str] = None,
        excel_requirements: Optional[List[str]] = None,
    ) -> RequirementExtractionResponse:

        if not reference_text and not excel_requirements:
            return RequirementExtractionResponse(
                success=False, error="Aucune source d'exigences fournie."
            )

        parts = []
        if reference_text:
            parts.append(f"Référentiel de sécurité interne :\n{reference_text}")
        if excel_requirements:
            excel_text = "\n".join(f"- {r}" for r in excel_requirements)
            parts.append(f"Exigences déjà présentes dans le questionnaire fournisseur :\n{excel_text}")

        user_prompt = "\n\n".join(parts)

        try:
            data = ask_claude_for_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
            requirements = [Requirement(**r) for r in data.get("requirements", [])]

            if not requirements:
                return RequirementExtractionResponse(
                    success=False, error="Aucune exigence n'a pu être produite."
                )

            return RequirementExtractionResponse(success=True, requirements=requirements)

        except Exception as e:
            return RequirementExtractionResponse(success=False, error=str(e))