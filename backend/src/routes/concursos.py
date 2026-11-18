# backend/src/routes/concursos.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ConcursoCreate(BaseModel):
    titulo: str
    orgao: str
    banca: str
    cargo: str
    salario: float
    vagas: Optional[int] = None
    nivel: str = "medio"
    regiao: str = "nacional"
    data_prova: Optional[str] = None
    inscricao_fim: Optional[str] = None

class ConcursoResponse(BaseModel):
    id: str
    titulo: str
    orgao: str
    banca: str
    cargo: str
    salario: float
    vagas: Optional[int]
    nivel: str
    regiao: str
    data_prova: Optional[str]
    total_questoes: int
    progresso: float = 0.0

@router.get("/", response_model=List[ConcursoResponse])
async def listar_concursos():
    # Mock data
    return [
        {
            "id": "1",
            "titulo": "PRF 2024",
            "orgao": "Polícia Rodoviária Federal",
            "banca": "Cebraspe",
            "cargo": "Policial Rodoviário Federal",
            "salario": 11500.00,
            "vagas": 1500,
            "nivel": "superior",
            "regiao": "nacional",
            "data_prova": "2025-03-15",
            "total_questoes": 120,
            "progresso": 78.0
        },
        {
            "id": "2",
            "titulo": "PM-MS 2024",
            "orgao": "Polícia Militar do Mato Grosso do Sul",
            "banca": "Quadrix",
            "cargo": "Soldado PM",
            "salario": 4500.00,
            "vagas": 500,
            "nivel": "medio",
            "regiao": "MS",
            "data_prova": "2025-02-15",
            "total_questoes": 80,
            "progresso": 0.0
        }
    ]

@router.post("/", response_model=ConcursoResponse)
async def criar_concurso(data: ConcursoCreate):
    return {
        "id": "new-id",
        "titulo": data.titulo,
        "orgao": data.orgao,
        "banca": data.banca,
        "cargo": data.cargo,
        "salario": data.salario,
        "vagas": data.vagas,
        "nivel": data.nivel,
        "regiao": data.regiao,
        "data_prova": data.data_prova,
        "total_questoes": 0,
        "progresso": 0.0
    }

@router.get("/{concurso_id}")
async def detalhar_concurso(concurso_id: str):
    return {
        "id": concurso_id,
        "titulo": "PRF 2024",
        "orgao": "Polícia Rodoviária Federal",
        "banca": "Cebraspe",
        "cargo": "Policial Rodoviário Federal",
        "salario": 11500.00,
        "vagas": 1500,
        "nivel": "superior",
        "regiao": "nacional",
        "data_prova": "2025-03-15",
        "total_questoes": 120,
        "progresso": 78.0,
        "disciplinas": [
            {"id": "1", "nome": "Português", "peso": 10, "progresso": 85},
            {"id": "2", "nome": "Direito Constitucional", "peso": 8, "progresso": 72},
            {"id": "3", "nome": "Direito Administrativo", "peso": 8, "progresso": 65},
            {"id": "4", "nome": "CTB", "peso": 12, "progresso": 40},
            {"id": "5", "nome": "RLM", "peso": 6, "progresso": 90}
        ]
    }
