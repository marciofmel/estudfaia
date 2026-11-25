# backend/src/routes/cronograma.py
"""Cronograma persistido, gerado pelo motor de IA local."""

import json
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

import db
import ia_engine
from security import usuario_id

router = APIRouter()


class GerarRequest(BaseModel):
    concurso_id: Optional[str] = None
    horas_dia: float = 3.0
    incluir_domingo: bool = False


def _disciplinas_do_concurso(conn, concurso_id: str):
    rows = conn.execute(
        "SELECT disciplina, COUNT(*) total FROM questoes WHERE concurso_id=? GROUP BY disciplina",
        (concurso_id,)).fetchall()
    return [
        {"nome": r["disciplina"], "peso": r["total"],
         "topicos": ia_engine.DISCIPLINAS.get(r["disciplina"], ("", 0, []))[2]}
        for r in rows
    ]


@router.get("")
@router.get("/")
async def obter_cronograma(request: Request, concurso_id: str = None):
    uid = usuario_id(request)
    conn = db.get_conn()
    if concurso_id:
        row = conn.execute(
            "SELECT * FROM cronogramas WHERE usuario_id=? AND concurso_id=? ORDER BY id DESC LIMIT 1",
            (uid, concurso_id)).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM cronogramas WHERE usuario_id=? ORDER BY id DESC LIMIT 1", (uid,)
        ).fetchone()
    if not row:
        # gera no primeiro acesso para a tela nunca ficar vazia
        alvo = concurso_id or conn.execute(
            "SELECT id, data_prova FROM concursos ORDER BY data_prova ASC LIMIT 1").fetchone()
        cid = alvo["id"] if alvo else None
        dp = alvo["data_prova"] if alvo else None
        disciplinas = _disciplinas_do_concurso(conn, cid) if cid else []
        if not disciplinas:
            disciplinas = [
                {"nome": n, "peso": p, "topicos": ia_engine.DISCIPLINAS.get(n, ("", 0, []))[2]}
                for n, p in ia_engine.PERFIL_AREA["Policial"].items()
            ]
        plano = ia_engine.gerar_cronograma(disciplinas, dp, 3.0)
        conn.execute(
            """INSERT INTO cronogramas (usuario_id, concurso_id, horas_dia, plano, criado_em)
               VALUES (?,?,?,?,?)""",
            (uid, cid, 3.0, json.dumps(plano, ensure_ascii=False), db.agora()))
        conn.commit()
        conn.close()
        plano["existe"] = True
        plano["concurso_id"] = cid
        return plano
    conn.close()
    plano = json.loads(row["plano"])
    plano["existe"] = True
    plano["concurso_id"] = row["concurso_id"]
    plano["criado_em_registro"] = row["criado_em"]
    return plano


@router.post("/gerar")
async def gerar(request: Request, data: GerarRequest):
    uid = usuario_id(request)
    conn = db.get_conn()
    padrao = conn.execute(
        "SELECT id, data_prova FROM concursos ORDER BY data_prova ASC LIMIT 1").fetchone()
    cid = data.concurso_id or (padrao["id"] if padrao else None)
    info = conn.execute("SELECT data_prova FROM concursos WHERE id=?", (cid,)).fetchone()
    disciplinas = _disciplinas_do_concurso(conn, cid) or [
        {"nome": n, "peso": p, "topicos": ia_engine.DISCIPLINAS.get(n, ("", 0, []))[2]}
        for n, p in ia_engine.PERFIL_AREA["Tribunal"].items()
    ]
    plano = ia_engine.gerar_cronograma(
        disciplinas, info["data_prova"] if info else None,
        data.horas_dia, data.incluir_domingo)
    conn.execute(
        """INSERT INTO cronogramas (usuario_id, concurso_id, horas_dia, plano, criado_em)
           VALUES (?,?,?,?,?)""",
        (uid, cid, data.horas_dia, json.dumps(plano, ensure_ascii=False), db.agora()))
    conn.commit()
    conn.close()
    plano["existe"] = True
    plano["concurso_id"] = cid
    return plano
