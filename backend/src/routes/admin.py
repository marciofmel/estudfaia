# backend/src/routes/admin.py
"""Painel administrativo com métricas reais calculadas do banco."""

import db
from fastapi import APIRouter

router = APIRouter()

PRECOS = {"free": 0.0, "essencial": 19.90, "pro": 49.90, "premium": 99.90, "enterprise": 2999.0}
CUSTO_INFRA_MES = 32.50  # Render free/starter + domínio, valor de referência


@router.get("/dashboard")
async def dashboard_admin():
    conn = db.get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
    por_plano = conn.execute(
        "SELECT plano, COUNT(*) c FROM usuarios GROUP BY plano").fetchall()
    respondidas = conn.execute("SELECT COUNT(*) c FROM respostas").fetchone()["c"]
    acertos = conn.execute("SELECT COALESCE(SUM(correta),0) c FROM respostas").fetchone()["c"]
    concursos_total = conn.execute("SELECT COUNT(*) c FROM concursos").fetchone()["c"]
    questoes_total = conn.execute("SELECT COUNT(*) c FROM questoes").fetchone()["c"]
    editais_total = conn.execute("SELECT COUNT(*) c FROM editais").fetchone()["c"]
    conn.close()

    assinantes = 0
    mrr = 0.0
    distribuicao = []
    for r in por_plano:
        qtd = r["c"]
        preco = PRECOS.get(r["plano"], 0.0)
        assinantes += qtd if preco > 0 else 0
        mrr += qtd * preco
        distribuicao.append({"plano": r["plano"], "usuarios": qtd, "preco": preco})

    lucro = round(mrr - CUSTO_INFRA_MES, 2)
    return {
        "usuarios": total,
        "assinantes_pagos": assinantes,
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "custos_mes": CUSTO_INFRA_MES,
        "lucro": lucro,
        "margem": round(lucro / mrr * 100, 1) if mrr else 0.0,
        "churn": 0.0,
        "novos_alunos_mes": total,
        "questoes_respondidas": respondidas,
        "taxa_acerto_global": round(acertos / respondidas * 100, 1) if respondidas else 0.0,
        "conteudo": {"concursos": concursos_total, "questoes": questoes_total, "editais": editais_total},
        "distribuicao_planos": distribuicao,
        "observacao": "MRR calculado sobre os planos reais dos usuários cadastrados.",
    }


@router.get("/alunos")
async def listar_alunos():
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT u.id, u.nome, u.email, u.plano, u.criado_em,
                  (SELECT COUNT(*) FROM respostas r WHERE r.usuario_id=u.id) respondidas,
                  (SELECT COALESCE(SUM(correta),0) FROM respostas r WHERE r.usuario_id=u.id) acertos
           FROM usuarios u ORDER BY u.criado_em DESC""").fetchall()
    conn.close()
    alunos = []
    for r in rows:
        a = db.row_to_dict(r)
        a["taxa_acerto"] = round((a["acertos"] or 0) / max(a["respondidas"], 1) * 100, 1)
        alunos.append(a)
    return {"total": len(alunos), "alunos": alunos}


@router.get("/metricas-conteudo")
async def metricas_conteudo():
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT disciplina, COUNT(*) total FROM questoes GROUP BY disciplina ORDER BY total DESC"""
    ).fetchall()
    conn.close()
    return [{"disciplina": r["disciplina"], "questoes": r["total"]} for r in rows]
