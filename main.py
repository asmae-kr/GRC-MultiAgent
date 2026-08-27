"""
Point d'entrée de l'API GRC-MultiAgent.
Lancer avec : uvicorn main:app --reload
"""
from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="GRC Multi-Agent System",
    description="AI system for cybersecurity and GRC supplier assessment",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def home():
    """Endpoint de vérification que l'API tourne bien."""
    return {"application": "GRC Multi-Agent System", "status": "running"}