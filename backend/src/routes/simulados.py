from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def listar_simulados():
    return [
        {"id": "1", "titulo": "PRF 2024 — Prova Completa", "questoes": 120, "tempo": 270, "alunos": 1250},
        {"id": "2", "titulo": "PM-MS 2024 — Soldado", "questoes": 80, "tempo": 180, "alunos": 890},
        {"id": "3", "titulo": "INSS 2024 — Técnico", "questoes": 60, "tempo": 210, "alunos": 2100}
    ]
