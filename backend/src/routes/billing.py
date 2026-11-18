# backend/src/routes/billing.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class AssinaturaRequest(BaseModel):
    plano: str
    metodo: str = "mercadopago"

@router.get("/planos")
async def listar_planos():
    return [
        {"id": "free", "nome": "Gratuito", "preco": 0, "limite_questoes": 20, "limite_concursos": 1},
        {"id": "essencial", "nome": "Essencial", "preco": 19.90, "limite_questoes": 100, "limite_concursos": 3},
        {"id": "pro", "nome": "Pro", "preco": 49.90, "limite_questoes": 999999, "limite_concursos": 10},
        {"id": "premium", "nome": "Premium", "preco": 99.90, "limite_questoes": 999999, "limite_concursos": 999999},
        {"id": "enterprise", "nome": "Enterprise", "preco": 2999.00, "limite_alunos": 500}
    ]

@router.post("/assinar")
async def criar_assinatura(data: AssinaturaRequest):
    return {"checkout_url": "https://mercadopago.com/checkout/xxx", "plano": data.plano}

@router.post("/webhook/mercadopago")
async def webhook_mercadopago(request: dict):
    return {"status": "ok"}
