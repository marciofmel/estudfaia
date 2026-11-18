# backend/src/routes/cronograma.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def obter_cronograma(concurso_id: str = None):
    return {
        "concurso_id": concurso_id or "1",
        "dias_ate_prova": 90,
        "horas_por_dia": 3.0,
        "semanas": [
            {
                "numero": 1,
                "dias": [
                    {
                        "data": "2024-11-18",
                        "dia_semana": "Segunda",
                        "atividades": [
                            {"tipo": "estudo", "disciplina": "Português", "duracao": 1.5, "topicos": ["Gramática", "Concordância"]},
                            {"tipo": "estudo", "disciplina": "CTB", "duracao": 1.5, "topicos": ["Sinalização", "Legislação"]}
                        ]
                    }
                ]
            }
        ]
    }

@router.post("/gerar")
async def gerar_cronograma(concurso_id: str):
    return {"status": "gerando", "concurso_id": concurso_id}
