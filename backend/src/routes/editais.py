# backend/src/routes/editais.py
"""Editais reais vindos do banco + monitor de novas publicações."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

import db
import ia_engine
from security import usuario_id

router = APIRouter()


class RespostaEdital(BaseModel):
    resposta: str


@router.get("/novos")
async def novos_editais(request: Request, area: str = None, uf: str = None, limite: int = 20):
    conn = db.get_conn()
    sql = "SELECT * FROM editais WHERE status = 'novo'"
    p = []
    if area:
        sql += " AND area = ?"
        p.append(area)
    if uf:
        sql += " AND uf = ?"
        p.append(uf)
    sql += " ORDER BY score DESC LIMIT ?"
    p.append(limite)
    rows = conn.execute(sql, p).fetchall()
    conn.close()
    return [db.row_to_dict(r) for r in rows]


@router.get("/passados")
async def editais_passados(area: str = None):
    conn = db.get_conn()
    sql = "SELECT * FROM editais WHERE status = 'passado'"
    p = []
    if area:
        sql += " AND area = ?"
        p.append(area)
    rows = conn.execute(sql, p).fetchall()
    conn.close()
    return [db.row_to_dict(r) for r in rows]


@router.get("/monitorar")
async def monitorar(request: Request):
    """IA varre portais públicos de concursos e grava o que encontrar."""
    resultado = ia_engine.monitorar_editais()
    novos = 0
    if resultado["editais"]:
        conn = db.get_conn()
        for e in resultado["editais"]:
            cur = conn.execute(
                """INSERT OR IGNORE INTO editais
                   (id,titulo,orgao,banca,cargo,salario,data_prova,url,fonte,score,status,area,uf)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (e["id"], e["titulo"], e.get("orgao"), e.get("banca"), e.get("cargo"),
                 e.get("salario"), e.get("data_prova"), e.get("url"), e.get("fonte"),
                 e.get("score", 60), "novo", e.get("area"), e.get("uf")),
            )
            novos += cur.rowcount
        conn.commit()
        conn.close()
    resultado["gravados"] = novos
    resultado["total_base"] = _total_editais()
    return resultado


def _total_editais() -> int:
    conn = db.get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM editais").fetchone()["c"]
    conn.close()
    return total


@router.post("/{edital_id}/responder")
async def responder_edital(edital_id: str, data: RespostaEdital, request: Request):
    uid = usuario_id(request)
    tipo = (data.resposta or "").lower()
    if tipo not in ("interesse", "descartar", "salvar", "aceitar", "recusar"):
        tipo = "interesse"
    conn = db.get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO interesses (usuario_id, edital_id, tipo, criado_em)
           VALUES (?,?,?,?)""",
        (uid, edital_id, tipo, db.agora()),
    )
    if tipo in ("descartar", "recusar"):
        conn.execute("UPDATE editais SET status='descartado' WHERE id=?", (edital_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "edital_id": edital_id, "resposta": tipo}


@router.get("/interesses")
async def meus_interesses(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT e.*, i.tipo AS meu_status FROM interesses i
           JOIN editais e ON e.id = i.edital_id
           WHERE i.usuario_id=? ORDER BY i.criado_em DESC""",
        (uid,)).fetchall()
    conn.close()
    return [db.row_to_dict(r) for r in rows]
