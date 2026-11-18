# backend/src/routes/questoes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class QuestaoResponse(BaseModel):
    id: str
    enunciado: str
    alternativas: List[dict]
    disciplina: str
    banca: str
    ano: int
    dificuldade: int

class RespostaRequest(BaseModel):
    questao_id: str
    alternativa: str
    tempo_gasto: int

@router.get("/proxima")
async def proxima_questao(concurso_id: str = None, disciplina: str = None):
    return {
        "id": "q-001",
        "enunciado": "Assinale a alternativa em que a concordância verbal está INCORRETA:",
        "alternativas": [
            {"letra": "A", "texto": "Havia muitas pessoas na sala."},
            {"letra": "B", "texto": "Fazem dois anos que não chove."},
            {"letra": "C", "texto": "Os alunos e o professor chegaram."},
            {"letra": "D", "texto": "A maioria dos alunos passou."}
        ],
        "disciplina": "Português",
        "banca": "Cebraspe",
        "ano": 2024,
        "dificuldade": 3,
        "explicacao": "O verbo 'fazer' (tempo decorrido) é impessoal e deve ficar no singular.",
        "resposta_correta": "B",
        "estatistica_acerto": 62.5
    }

@router.post("/responder")
async def responder_questao(data: RespostaRequest):
    correta = data.alternativa == "B"
    return {
        "correta": correta,
        "resposta_correta": "B",
        "explicacao": "O verbo 'fazer' (tempo decorrido) é impessoal e deve ficar no singular: 'Faz dois anos que não chove.'",
        "proxima_revisao": "2024-11-17" if not correta else None,
        "dominada": False
    }

@router.get("/caderno-erros")
async def caderno_erros():
    return {
        "total": 47,
        "questoes": [
            {
                "id": "q-001",
                "enunciado": "Fazem dois anos que não chove...",
                "disciplina": "Português",
                "topico": "Concordância Verbal",
                "data_erro": "2024-11-15",
                "proxima_revisao": "2024-11-17",
                "status": "pendente"  # pendente, revisado, dominada
            }
        ]
    }
