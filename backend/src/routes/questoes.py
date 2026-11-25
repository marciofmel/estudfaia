# backend/src/routes/questoes.py
"""Questões reais com persistência, correção e revisão espaçada (SM-2)."""

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import db
import ia_engine
from security import usuario_id

router = APIRouter()


class RespostaRequest(BaseModel):
    questao_id: str
    alternativa: str
    tempo_gasto: int = 0


def _serializar_questao(row):
    q = db.row_to_dict(row)
    q["alternativas"] = json.loads(q["alternativas"])
    q.pop("correta", None)  # não entrega o gabarito antes da resposta
    return q


@router.get("/proxima")
async def proxima_questao(request: Request, disciplina: str = None, concurso_id: str = None):
    uid = usuario_id(request)
    conn = db.get_conn()
    sql = """
        SELECT q.* FROM questoes q
        WHERE NOT EXISTS (
            SELECT 1 FROM respostas r WHERE r.questao_id = q.id AND r.usuario_id = ?
        )
    """
    params = [uid]
    if disciplina:
        sql += " AND q.disciplina = ?"
        params.append(disciplina)
    if concurso_id:
        sql += " AND q.concurso_id = ?"
        params.append(concurso_id)
    sql += " ORDER BY RANDOM() LIMIT 1"
    row = conn.execute(sql, params).fetchone()

    # Se já respondeu todas, reinicia o ciclo (mantendo o histórico de revisão)
    if not row:
        sql2 = "SELECT * FROM questoes WHERE 1=1"
        p2 = []
        if disciplina:
            sql2 += " AND disciplina = ?"
            p2.append(disciplina)
        if concurso_id:
            sql2 += " AND concurso_id = ?"
            p2.append(concurso_id)
        sql2 += " ORDER BY RANDOM() LIMIT 1"
        row = conn.execute(sql2, p2).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Nenhuma questão disponível")

    questao = _serializar_questao(row)
    questao["total_disponiveis"] = _contar_questoes(disciplina, concurso_id)
    return questao


def _contar_questoes(disciplina=None, concurso_id=None) -> int:
    conn = db.get_conn()
    sql = "SELECT COUNT(*) c FROM questoes WHERE 1=1"
    p = []
    if disciplina:
        sql += " AND disciplina = ?"
        p.append(disciplina)
    if concurso_id:
        sql += " AND concurso_id = ?"
        p.append(concurso_id)
    total = conn.execute(sql, p).fetchone()["c"]
    conn.close()
    return total


@router.post("/responder")
async def responder_questao(data: RespostaRequest, request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    q = conn.execute("SELECT * FROM questoes WHERE id=?", (data.questao_id,)).fetchone()
    if not q:
        conn.close()
        raise HTTPException(status_code=404, detail="Questão não encontrada")

    correta = (data.alternativa or "").strip().upper() == q["correta"].strip().upper()
    conn.execute(
        """INSERT INTO respostas (usuario_id, questao_id, alternativa, correta, tempo_gasto, criado_em)
           VALUES (?,?,?,?,?,?)""",
        (uid, data.questao_id, (data.alternativa or "").upper(), int(correta),
         data.tempo_gasto or 0, db.agora()),
    )

    # ---------------- SM-2 ----------------
    rev = conn.execute("SELECT * FROM revisoes WHERE usuario_id=? AND questao_id=?",
                       (uid, data.questao_id)).fetchone()
    if rev:
        repeticoes = rev["repeticoes"]
        intervalo = rev["intervalo"]
        facilidade = rev["facilidade"]
    else:
        repeticoes, intervalo, facilidade = 0, 1, 2.5

    qualidade = 5 if correta else 2
    if qualidade >= 3:
        repeticoes += 1
        if repeticoes == 1:
            intervalo = 1
        elif repeticoes == 2:
            intervalo = 3
        else:
            intervalo = int(round(intervalo * facilidade))
        facilidade = min(2.9, max(1.3, facilidade + 0.1))
    else:
        repeticoes = 0
        intervalo = 1
        facilidade = max(1.3, facilidade - 0.2)

    proxima = (date.today() + timedelta(days=intervalo)).isoformat()
    if rev:
        conn.execute(
            """UPDATE revisoes SET repeticoes=?, intervalo=?, facilidade=?,
               proxima_revisao=?, status=? WHERE id=?""",
            (repeticoes, intervalo, round(facilidade, 2), proxima,
             "pendente" if not correta else "agendada", rev["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO revisoes
               (usuario_id, questao_id, repeticoes, intervalo, facilidade, proxima_revisao, status)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, data.questao_id, repeticoes, intervalo, round(facilidade, 2), proxima,
             "pendente" if not correta else "agendada"),
        )
    conn.commit()

    questao_dict = db.row_to_dict(q)
    questao_dict["alternativas"] = json.loads(q["alternativas"])
    explicacao_ia = ia_engine.explicar_questao(questao_dict)

    estat = conn.execute(
        "SELECT COUNT(*) t, SUM(correta) a FROM respostas WHERE questao_id=?",
        (data.questao_id,)).fetchone()
    taxa = round((estat["a"] or 0) / max(estat["t"], 1) * 100, 1)

    progresso = conn.execute(
        "SELECT COUNT(*) total, SUM(correta) acertos FROM respostas WHERE usuario_id=?",
        (uid,)).fetchone()
    conn.close()

    return {
        "correta": correta,
        "resposta_correta": q["correta"],
        "explicacao": q["explicacao"],
        "explicacao_ia": explicacao_ia,
        "proxima_revisao": proxima,
        "intervalo_dias": intervalo,
        "dominada": repeticoes >= 3 and correta,
        "estatistica_acerto": taxa,
        "total_respondidas": progresso["total"],
        "acertos": progresso["acertos"] or 0,
        "taxa_acerto": round((progresso["acertos"] or 0) / max(progresso["total"], 1) * 100, 1),
    }


@router.get("/caderno-erros")
async def caderno_erros(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT q.id, q.enunciado, q.disciplina, q.topico, q.banca, q.ano,
                  MAX(r.criado_em) AS data_erro,
                  (SELECT proxima_revisao FROM revisoes v
                     WHERE v.usuario_id=r.usuario_id AND v.questao_id=r.questao_id) AS proxima_revisao,
                  (SELECT status FROM revisoes v
                     WHERE v.usuario_id=r.usuario_id AND v.questao_id=r.questao_id) AS status
           FROM respostas r JOIN questoes q ON q.id = r.questao_id
           WHERE r.usuario_id=? AND r.correta=0
           GROUP BY q.id ORDER BY data_erro DESC""",
        (uid,)).fetchall()
    conn.close()
    return {
        "total": len(rows),
        "questoes": [db.row_to_dict(r) for r in rows],
    }


@router.get("/revisoes")
async def revisoes_do_dia(request: Request):
    uid = usuario_id(request)
    hoje = date.today().isoformat()
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT v.*, q.enunciado, q.disciplina, q.topico, q.banca, q.ano
           FROM revisoes v JOIN questoes q ON q.id = v.questao_id
           WHERE v.usuario_id=? AND v.proxima_revisao <= ?
           ORDER BY v.proxima_revisao ASC""",
        (uid, hoje)).fetchall()
    total = conn.execute("SELECT COUNT(*) c FROM revisoes WHERE usuario_id=?", (uid,)).fetchone()["c"]
    conn.close()
    return {
        "hoje": hoje,
        "pendentes": len(rows),
        "agendadas_total": total,
        "revisoes": [db.row_to_dict(r) for r in rows],
    }


@router.get("/estatisticas")
async def estatisticas(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    geral = conn.execute(
        "SELECT COUNT(*) total, SUM(correta) acertos FROM respostas WHERE usuario_id=?",
        (uid,)).fetchone()
    por_disc = conn.execute(
        """SELECT q.disciplina, COUNT(*) total, SUM(r.correta) acertos
           FROM respostas r JOIN questoes q ON q.id=r.questao_id
           WHERE r.usuario_id=? GROUP BY q.disciplina ORDER BY total DESC""",
        (uid,)).fetchall()
    conn.close()
    return {
        "total_respondidas": geral["total"],
        "acertos": geral["acertos"] or 0,
        "taxa_acerto": round((geral["acertos"] or 0) / max(geral["total"], 1) * 100, 1),
        "por_disciplina": [
            {"disciplina": r["disciplina"], "total": r["total"], "acertos": r["acertos"] or 0,
             "taxa_acerto": round((r["acertos"] or 0) / max(r["total"], 1) * 100, 1)}
            for r in por_disc
        ],
    }


@router.get("/disciplinas")
async def listar_disciplinas():
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT disciplina, COUNT(*) total FROM questoes GROUP BY disciplina ORDER BY disciplina"
    ).fetchall()
    conn.close()
    return [{"disciplina": r["disciplina"], "total": r["total"]} for r in rows]


@router.get("/{questao_id}")
async def obter_questao(questao_id: str):
    """Questão específica (sem gabarito) — usada na revisão."""
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM questoes WHERE id=?", (questao_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return _serializar_questao(row)
