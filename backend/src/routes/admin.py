# backend/src/routes/admin.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
async def dashboard_admin():
    return {
        "alunos": 450,
        "mrr": 14760.00,
        "custos": 2390.00,
        "lucro": 12370.00,
        "margem": 83.8,
        "churn": 3.2,
        "novos_alunos_mes": 70
    }

@router.get("/alunos")
async def listar_alunos():
    return {"total": 450, "alunos": []}
