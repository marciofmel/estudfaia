# backend/src/routes/ia.py
"""Endpoints da IA real (motor local, sem depender de chave paga)."""

import json
import re

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

import db
import ia_engine
from security import usuario_id

router = APIRouter()


class AnalisarEditalRequest(BaseModel):
    texto: Optional[str] = None
    url: Optional[str] = None
    area: Optional[str] = None


class CronogramaRequest(BaseModel):
    concurso_id: Optional[str] = None
    disciplinas: Optional[List[dict]] = None
    data_prova: Optional[str] = None
    horas_dia: float = 3.0
    incluir_domingo: bool = False


def _html_para_texto(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    texto = re.sub(r"(?s)<[^>]+>", " ", html)
    texto = re.sub(r"&nbsp;?", " ", texto)
    texto = re.sub(r"&amp;?", "&", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return "\n".join(l.strip() for l in texto.splitlines() if l.strip())


@router.get("/status")
async def status_ia():
    return {
        "motor": "ia-local-v1",
        "online": True,
        "depende_de_api_paga": False,
        "capacidades": [
            "Leitura e extração de editais (texto ou URL)",
            "Geração de cronograma por peso de disciplina",
            "Revisão espaçada (SM-2) e diagnóstico de desempenho",
            "Explicação de questões com estratégia por tópico",
            "Monitoramento de portais públicos de concursos",
        ],
    }


@router.post("/analisar-edital")
async def analisar_edital(data: AnalisarEditalRequest):
    texto = data.texto or ""
    origem = "texto"
    if data.url:
        try:
            with httpx.Client(timeout=12, follow_redirects=True,
                              headers={"User-Agent": "Mozilla/5.0 ConcursosAI"}) as cli:
                r = cli.get(data.url)
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Fonte respondeu HTTP {r.status_code}")
            texto = _html_para_texto(r.text)
            origem = data.url
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Não foi possível ler a URL: {exc}")

    if len(texto.strip()) < 40:
        raise HTTPException(status_code=422,
                            detail="Envie o texto do edital (mínimo 40 caracteres) ou uma URL válida")

    resultado = ia_engine.analisar_edital(texto, area=data.area)
    resultado["origem"] = origem
    resultado["caracteres_lidos"] = len(texto)
    return resultado


@router.post("/cronograma")
async def gerar_cronograma_ia(data: CronogramaRequest, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()

    disciplinas = data.disciplinas
    data_prova = data.data_prova

    if not disciplinas and data.concurso_id:
        rows = conn.execute(
            "SELECT disciplina, COUNT(*) total FROM questoes WHERE concurso_id=? GROUP BY disciplina",
            (data.concurso_id,)).fetchall()
        disciplinas = [
            {"nome": r["disciplina"], "peso": r["total"],
             "topicos": ia_engine.DISCIPLINAS.get(r["disciplina"], ("", 0, []))[2]}
            for r in rows
        ]
        if not data_prova:
            c = conn.execute("SELECT data_prova FROM concursos WHERE id=?",
                             (data.concurso_id,)).fetchone()
            data_prova = c["data_prova"] if c else None

    if not disciplinas:
        rows = conn.execute(
            "SELECT disciplina, COUNT(*) total FROM questoes GROUP BY disciplina ORDER BY total DESC"
        ).fetchall()
        disciplinas = [
            {"nome": r["disciplina"], "peso": r["total"],
             "topicos": ia_engine.DISCIPLINAS.get(r["disciplina"], ("", 0, []))[2]}
            for r in rows
        ]

    plano = ia_engine.gerar_cronograma(disciplinas, data_prova, data.horas_dia, data.incluir_domingo)
    conn.execute(
        """INSERT INTO cronogramas (usuario_id, concurso_id, horas_dia, plano, criado_em)
           VALUES (?,?,?,?,?)""",
        (uid, data.concurso_id, data.horas_dia, json.dumps(plano, ensure_ascii=False), db.agora()),
    )
    conn.commit()
    conn.close()
    return plano


@router.get("/cronograma")
async def cronograma_atual(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    row = conn.execute(
        "SELECT * FROM cronogramas WHERE usuario_id=? ORDER BY id DESC LIMIT 1", (uid,)
    ).fetchone()
    conn.close()
    if not row:
        return {"existe": False}
    plano = json.loads(row["plano"])
    plano["existe"] = True
    plano["concurso_id"] = row["concurso_id"]
    plano["criado_em_registro"] = row["criado_em"]
    return plano


@router.get("/explicar/{questao_id}")
async def explicar(questao_id: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM questoes WHERE id=?", (questao_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    q = db.row_to_dict(row)
    q["alternativas"] = json.loads(q["alternativas"])
    return ia_engine.explicar_questao(q)


@router.get("/desempenho")
async def desempenho(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT r.correta, q.disciplina, q.topico FROM respostas r
           JOIN questoes q ON q.id=r.questao_id WHERE r.usuario_id=?""",
        (uid,)).fetchall()
    pendentes = conn.execute(
        "SELECT COUNT(*) c FROM revisoes WHERE usuario_id=? AND status='pendente'", (uid,)
    ).fetchone()["c"]
    conn.close()
    return ia_engine.analisar_desempenho([db.row_to_dict(r) for r in rows], pendentes)


@router.get("/monitorar")
async def monitorar():
    return ia_engine.monitorar_editais()
