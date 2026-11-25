# backend/src/routes/concursos.py
"""Concursos reais do banco com progresso calculado por usuário."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import db
from security import usuario_id
from fastapi import Request

router = APIRouter()


class ConcursoCreate(BaseModel):
    titulo: str
    orgao: str
    banca: Optional[str] = None
    cargo: Optional[str] = None
    salario: Optional[float] = None
    vagas: Optional[int] = None
    area: Optional[str] = None
    uf: Optional[str] = None
    data_prova: Optional[str] = None


def _progresso(conn, uid: str, concurso_id: str) -> dict:
    row = conn.execute(
        """SELECT COUNT(*) total, SUM(r.correta) acertos
           FROM respostas r JOIN questoes q ON q.id = r.questao_id
           WHERE r.usuario_id=? AND q.concurso_id=?""",
        (uid, concurso_id)).fetchone()
    total_concurso = conn.execute(
        "SELECT COUNT(*) c FROM questoes WHERE concurso_id=?", (concurso_id,)).fetchone()["c"]
    respondidas = row["total"] or 0
    acertos = row["acertos"] or 0
    return {
        "total_questoes": total_concurso,
        "respondidas": respondidas,
        "acertos": acertos,
        "progresso": round(respondidas / total_concurso * 100, 1) if total_concurso else 0.0,
        "taxa_acerto": round(acertos / respondidas * 100, 1) if respondidas else 0.0,
    }


def _dias_para_prova(data_prova: str):
    if not data_prova:
        return None
    try:
        return (date.fromisoformat(data_prova) - date.today()).days
    except ValueError:
        return None


@router.get("")
@router.get("/")
async def listar_concursos(request: Request, area: str = None, uf: str = None):
    uid = usuario_id(request)
    conn = db.get_conn()
    sql = "SELECT * FROM concursos WHERE 1=1"
    p = []
    if area:
        sql += " AND area = ?"
        p.append(area)
    if uf:
        sql += " AND uf = ?"
        p.append(uf)
    sql += " ORDER BY data_prova ASC"
    rows = conn.execute(sql, p).fetchall()
    saida = []
    for r in rows:
        c = db.row_to_dict(r)
        c.update(_progresso(conn, uid, c["id"]))
        c["dias_para_prova"] = _dias_para_prova(c["data_prova"])
        saida.append(c)
    conn.close()
    return saida


@router.post("")
@router.post("/")
async def criar_concurso(data: ConcursoCreate):
    cid = "c-" + data.titulo.lower().replace(" ", "-")[:40]
    conn = db.get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO concursos
           (id,titulo,orgao,banca,cargo,salario,data_prova,area,uf,status,vagas)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (cid, data.titulo, data.orgao, data.banca, data.cargo, data.salario,
         data.data_prova, data.area, data.uf, "aberto", data.vagas),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM concursos WHERE id=?", (cid,)).fetchone()
    conn.close()
    return db.row_to_dict(row)


@router.get("/{concurso_id}")
async def detalhar_concurso(concurso_id: str, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM concursos WHERE id=?", (concurso_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Concurso não encontrado")
    c = db.row_to_dict(row)
    c.update(_progresso(conn, uid, concurso_id))
    c["dias_para_prova"] = _dias_para_prova(c["data_prova"])

    # disciplinas reais com peso (nº de questões cadastradas) e progresso
    discs = conn.execute(
        """SELECT q.disciplina,
                  COUNT(*) total,
                  SUM(CASE WHEN r.correta=1 THEN 1 ELSE 0 END) acertos,
                  COUNT(r.id) respondidas
           FROM questoes q
           LEFT JOIN respostas r ON r.questao_id=q.id AND r.usuario_id=?
           WHERE q.concurso_id=?
           GROUP BY q.disciplina ORDER BY total DESC""",
        (uid, concurso_id)).fetchall()
    c["disciplinas"] = [
        {"nome": d["disciplina"], "questoes": d["total"], "respondidas": d["respondidas"],
         "progresso": round((d["respondidas"] or 0) / d["total"] * 100, 1),
         "taxa_acerto": round((d["acertos"] or 0) / max(d["respondidas"] or 0, 1) * 100, 1)}
        for d in discs
    ]
    conn.close()
    return c
