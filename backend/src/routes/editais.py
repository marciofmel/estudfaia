# backend/src/routes/editais.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class EditalResponse(BaseModel):
    id: str
    titulo: str
    orgao: str
    banca: Optional[str]
    cargo: Optional[str]
    salario: Optional[float]
    data_prova: Optional[str]
    score_compatibilidade: Optional[int]
    status: str

@router.get("/novos", response_model=List[EditalResponse])
async def novos_editais():
    return [
        {
            "id": "e-001",
            "titulo": "PM-MS 2024",
            "orgao": "Polícia Militar do Mato Grosso do Sul",
            "banca": "Quadrix",
            "cargo": "Soldado PM",
            "salario": 4500.00,
            "data_prova": "2025-02-15",
            "score_compatibilidade": 85,
            "status": "novo"
        },
        {
            "id": "e-002",
            "titulo": "TJ-MS 2024",
            "orgao": "Tribunal de Justiça do Mato Grosso do Sul",
            "banca": "FCC",
            "cargo": "Técnico Judiciário",
            "salario": 5200.00,
            "data_prova": "2025-03-20",
            "score_compatibilidade": 72,
            "status": "novo"
        }
    ]

@router.post("/{edital_id}/responder")
async def responder_edital(edital_id: str, resposta: str):
    return {"status": "ok", "edital_id": edital_id, "resposta": resposta}

@router.get("/passados")
async def editais_passados(area: str = None):
    return [
        {
            "id": "e-p-001",
            "titulo": "PM-MS 2022",
            "orgao": "Polícia Militar do Mato Grosso do Sul",
            "banca": "Quadrix",
            "data_prova": "2022-08-15",
            "status": "passado"
        }
    ]
