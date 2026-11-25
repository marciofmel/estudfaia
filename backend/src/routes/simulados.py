# backend/src/routes/simulados.py
"""Simulados gerados a partir do banco real, com correção e histórico."""

import json
import random
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import db
from security import usuario_id

router = APIRouter()


class IniciarRequest(BaseModel):
    concurso_id: Optional[str] = None
    quantidade: int = 10


class FinalizarRequest(BaseModel):
    respostas: Dict[str, str]  # questao_id -> letra


def _alternativas_lista(bruto):
    """Converte {"A": "texto"} ou JSON em [{"letra": "A", "texto": "texto"}]."""
    dados = bruto
    if isinstance(bruto, str):
        try:
            dados = json.loads(bruto)
        except Exception:
            dados = {}
    if isinstance(dados, dict):
        return [{"letra": k, "texto": v} for k, v in dados.items()]
    if isinstance(dados, list):
        saida = []
        for item in dados:
            if isinstance(item, dict):
                saida.append({"letra": item.get("letra") or item.get("id"),
                              "texto": item.get("texto") or item.get("text") or ""})
            else:
                saida.append({"letra": chr(65 + len(saida)), "texto": str(item)})
        return saida
    return []


@router.get("")
@router.get("/")
async def listar_simulados(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT c.id, c.titulo, c.banca, COUNT(q.id) AS questoes
           FROM concursos c JOIN questoes q ON q.concurso_id = c.id
           GROUP BY c.id ORDER BY questoes DESC""").fetchall()
    feitos = conn.execute(
        "SELECT COUNT(*) c, AVG(CAST(acertos AS REAL)/total)*100 media FROM simulados WHERE usuario_id=?",
        (uid,)).fetchone()
    conn.close()
    return {
        "disponiveis": [
            {"id": r["id"], "titulo": r["titulo"], "banca": r["banca"],
             "questoes": r["questoes"], "tempo_min": max(20, r["questoes"] * 2)}
            for r in rows
        ],
        "realizados": feitos["c"],
        "media_aproveitamento": round(feitos["media"] or 0, 1),
    }


@router.post("/iniciar")
async def iniciar(data: IniciarRequest, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    sql = "SELECT id, enunciado, alternativas, disciplina, banca, ano, dificuldade FROM questoes"
    p = []
    if data.concurso_id:
        sql += " WHERE concurso_id=?"
        p.append(data.concurso_id)
    rows = conn.execute(sql, p).fetchall()
    if not rows:
        conn.close()
        raise HTTPException(status_code=404, detail="Sem questões para esse concurso")

    qtd = max(1, min(data.quantidade, len(rows)))
    selecionadas = random.sample(rows, qtd)
    questoes = []
    for r in selecionadas:
        questoes.append({
            "id": r["id"], "enunciado": r["enunciado"],
            "alternativas": _alternativas_lista(r["alternativas"]),
            "disciplina": r["disciplina"], "banca": r["banca"],
            "ano": r["ano"], "dificuldade": r["dificuldade"],
        })
    titulo = f"Simulado {data.concurso_id or 'geral'} — {qtd} questões"
    cur = conn.execute(
        """INSERT INTO simulados (usuario_id, titulo, questoes, respostas, acertos, total, criado_em)
           VALUES (?,?,?,?,?,?,?)""",
        (uid, titulo, json.dumps([q["id"] for q in questoes]), "{}", None, qtd, db.agora()))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return {"simulado_id": sid, "titulo": titulo, "questoes": questoes,
            "tempo_min": max(10, qtd * 2)}


@router.post("/{simulado_id}/finalizar")
async def finalizar(simulado_id: int, data: FinalizarRequest, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    sim = conn.execute("SELECT * FROM simulados WHERE id=? AND usuario_id=?",
                       (simulado_id, uid)).fetchone()
    if not sim:
        conn.close()
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    ids = json.loads(sim["questoes"])
    gabaritos = {r["id"]: r["correta"] for r in conn.execute(
        f"SELECT id, correta FROM questoes WHERE id IN ({','.join('?'*len(ids))})", ids)}
    detalhes = []
    acertos = 0
    for qid in ids:
        marcada = (data.respostas.get(qid) or "").upper()
        correta = gabaritos.get(qid, "")
        ok = marcada == correta
        acertos += int(ok)
        detalhes.append({"questao_id": qid, "marcada": marcada, "correta": correta, "acertou": ok})
        if marcada:
            conn.execute(
                """INSERT INTO respostas (usuario_id, questao_id, alternativa, correta, tempo_gasto, criado_em)
                   VALUES (?,?,?,?,?,?)""",
                (uid, qid, marcada, int(ok), 0, db.agora()))
    conn.execute("UPDATE simulados SET respostas=?, acertos=? WHERE id=?",
                 (json.dumps(data.respostas, ensure_ascii=False), acertos, simulado_id))
    conn.commit()
    conn.close()
    total = len(ids)
    return {
        "simulado_id": simulado_id,
        "acertos": acertos,
        "total": total,
        "aproveitamento": round(acertos / total * 100, 1) if total else 0,
        "detalhes": detalhes,
    }


@router.get("/historico")
async def historico(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, titulo, acertos, total, criado_em FROM simulados WHERE usuario_id=? ORDER BY id DESC",
        (uid,)).fetchall()
    conn.close()
    return [
        {**db.row_to_dict(r),
         "aproveitamento": round((r["acertos"] or 0) / max(r["total"], 1) * 100, 1)}
        for r in rows
    ]
