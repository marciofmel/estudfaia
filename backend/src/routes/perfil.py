# backend/src/routes/perfil.py
"""Preferências e resumo do usuário (usados pela tela de Perfil/Dashboard)."""

import json
from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

import db
from security import usuario_id

router = APIRouter()


class PreferenciasRequest(BaseModel):
    areas: Optional[List[str]] = None
    regioes: Optional[List[str]] = None
    salario_min: Optional[float] = None
    notificacoes: Optional[dict] = None


@router.get("/preferencias")
async def obter_preferencias(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM preferencias WHERE usuario_id=?", (uid,)).fetchone()
    conn.close()
    if not row:
        return {"areas": [], "regioes": [], "salario_min": 0,
                "notificacoes": {"editais": True, "revisao": True, "prazos": True, "cronograma": True}}
    d = db.row_to_dict(row)
    return {
        "areas": json.loads(d["areas"] or "[]"),
        "regioes": json.loads(d["regioes"] or "[]"),
        "salario_min": d["salario_min"] or 0,
        "notificacoes": json.loads(d["notificacoes"] or "{}"),
    }


@router.put("/preferencias")
async def salvar_preferencias(data: PreferenciasRequest, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    atual = conn.execute("SELECT * FROM preferencias WHERE usuario_id=?", (uid,)).fetchone()
    areas = json.dumps(data.areas) if data.areas is not None else (atual["areas"] if atual else "[]")
    regioes = json.dumps(data.regioes) if data.regioes is not None else (atual["regioes"] if atual else "[]")
    salario = data.salario_min if data.salario_min is not None else (atual["salario_min"] if atual else 0)
    notif = json.dumps(data.notificacoes) if data.notificacoes is not None else \
        (atual["notificacoes"] if atual else "{}")
    conn.execute(
        """INSERT INTO preferencias (usuario_id, areas, regioes, salario_min, notificacoes)
           VALUES (?,?,?,?,?)
           ON CONFLICT(usuario_id) DO UPDATE SET
             areas=excluded.areas, regioes=excluded.regioes,
             salario_min=excluded.salario_min, notificacoes=excluded.notificacoes""",
        (uid, areas, regioes, salario, notif))
    conn.commit()
    conn.close()
    return {"status": "salvo", "areas": json.loads(areas), "regioes": json.loads(regioes),
            "salario_min": salario, "notificacoes": json.loads(notif)}


@router.get("/resumo")
async def resumo(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    usuario = conn.execute("SELECT nome, email, plano FROM usuarios WHERE id=?", (uid,)).fetchone()
    stat = conn.execute(
        "SELECT COUNT(*) t, COALESCE(SUM(correta),0) a FROM respostas WHERE usuario_id=?",
        (uid,)).fetchone()
    pend = conn.execute(
        "SELECT COUNT(*) c FROM revisoes WHERE usuario_id=? AND proxima_revisao <= ?",
        (uid, db.agora()[:10])).fetchone()["c"]
    editais_novos = conn.execute("SELECT COUNT(*) c FROM editais WHERE status='novo'").fetchone()["c"]
    conn.close()
    return {
        "usuario": db.row_to_dict(usuario) if usuario else {"nome": "Aluno Demo", "plano": "pro"},
        "respondidas": stat["t"],
        "acertos": stat["a"],
        "taxa_acerto": round(stat["a"] / stat["t"] * 100, 1) if stat["t"] else 0,
        "revisoes_hoje": pend,
        "editais_novos": editais_novos,
    }
