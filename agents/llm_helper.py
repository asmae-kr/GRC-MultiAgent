"""
Utilitaire partagé par tous les agents pour appeler l'IA (Google Gemini).
- Système de nouvelle tentative automatique en cas de surcharge (erreur 503)
- Support de l'outil "URL Context" pour lire un lien de preuve fourni par le fournisseur
"""
import json
import re
import time
from google import genai
from google.genai.types import Tool, GenerateContentConfig, UrlContext
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


def ask_claude_for_json(
    system_prompt: str,
    user_prompt: str,
    use_url_context: bool = False,
    max_retries: int = 5,
) -> dict:
    last_error = None

    config = None
    if use_url_context:
        config = GenerateContentConfig(tools=[Tool(url_context=UrlContext)])

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config=config,
            )
            raw_text = response.text.strip()
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            json_text = match.group(0) if match else raw_text
            return json.loads(json_text)

        except Exception as e:
            last_error = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = attempt * 5  # 5s, 10s, 15s, 20s, 25s
                print(f"[Gemini surchargé] Tentative {attempt}/{max_retries}, nouvelle tentative dans {wait}s...")
                time.sleep(wait)
                continue
            else:
                raise

    raise ValueError(f"Échec après {max_retries} tentatives : {last_error}")