# backend/src/routes/whatsapp.py
"""Integração REAL com a Evolution API: conectar o WhatsApp do usuário via QR Code.

Fluxo implementado:
  POST /api/whatsapp/conectar  -> cria a instância (se preciso) e devolve o QR
  GET  /api/whatsapp/qrcode    -> QR atualizado (a Evolution gira o código)
  GET  /api/whatsapp/estado    -> 'open' quando o celular escaneou
  POST /api/whatsapp/desconectar
  POST /api/whatsapp/enviar    -> mensagem real
  POST /api/whatsapp/teste     -> envia mensagem de teste para o número conectado
  GET  /api/whatsapp/diagnostico -> diz se a Evolution está no ar

Se a Evolution API não estiver rodando, os endpoints respondem 503 com instruções
claras (docker compose up -d) — nunca "fingem" que conectou.
"""

import json
import os
import re
from datetime import datetime
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

import db
from security import usuario_id

router = APIRouter()
webhook_router = APIRouter()

EVOLUTION_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY", "concursos123")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "concursos")
TIMEOUT = 15.0

INSTRUCOES = {
    "como_subir": "Abra o Docker Desktop e rode: docker compose up -d (na pasta do projeto)",
    "url_esperada": EVOLUTION_URL,
    "arquivo": "docker-compose.yml",
    "teste": f"{EVOLUTION_URL}/",
}


class VincularRequest(BaseModel):
    telefone: Optional[str] = None


class EnviarMensagemRequest(BaseModel):
    telefone: Optional[str] = None
    mensagem: str


def _headers():
    return {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}


def _limpar_numero(numero: str) -> str:
    n = re.sub(r"\D", "", numero or "")
    if not n:
        return ""
    if not n.startswith("55"):
        n = "55" + n
    return n


def _normalizar_estado(payload) -> str:
    """Evolution devolve formatos diferentes entre versões."""
    if not isinstance(payload, dict):
        return "desconectado"
    if "instance" in payload and isinstance(payload["instance"], dict):
        return payload["instance"].get("state") or payload["instance"].get("connectionStatus") or "desconectado"
    return payload.get("state") or payload.get("connectionStatus") or payload.get("status") or "desconectado"


def _extrair_qr(payload) -> dict:
    """Aceita {qrcode:{base64,code}} (v2), {base64,code} (v1) e variações."""
    if not isinstance(payload, dict):
        return {}
    bruto = payload.get("qrcode") if isinstance(payload.get("qrcode"), dict) else payload
    base64_ = bruto.get("base64") or bruto.get("qrcode") or payload.get("base64")
    code = bruto.get("code") or payload.get("code") or bruto.get("pairingCode") or payload.get("pairingCode")
    if isinstance(base64_, str) and base64_.startswith("data:image"):
        base64_ = base64_.split(",", 1)[-1]
    return {"qrcode": base64_, "codigo_pareamento": code,
            "count": bruto.get("count") or payload.get("count")}


def _salvar_sessao(uid: str, estado: str, telefone: str = None, qr: str = None):
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO whatsapp_sessao (usuario_id, instance, telefone, estado, qr, atualizado_em)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(usuario_id) DO UPDATE SET
             instance=excluded.instance,
             telefone=COALESCE(excluded.telefone, whatsapp_sessao.telefone),
             estado=excluded.estado,
             qr=COALESCE(excluded.qr, whatsapp_sessao.qr),
             atualizado_em=excluded.atualizado_em""",
        (uid, EVOLUTION_INSTANCE, telefone, estado, qr, db.agora()),
    )
    conn.commit()
    conn.close()


def _ler_sessao(uid: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM whatsapp_sessao WHERE usuario_id=?", (uid,)).fetchone()
    conn.close()
    return db.row_to_dict(row)


async def _evolution_online() -> bool:
    try:
        async with httpx.AsyncClient(timeout=4) as cli:
            r = await cli.get(f"{EVOLUTION_URL}/")
            return r.status_code < 500
    except Exception:
        return False


async def _garantir_instancia(cli: httpx.AsyncClient) -> dict:
    """Cria a instância se ela ainda não existir. Retorna o payload de criação."""
    lista = await cli.get(f"{EVOLUTION_URL}/instance/fetchInstances", headers=_headers())
    existentes = []
    if lista.status_code == 200:
        try:
            dados = lista.json()
            if isinstance(dados, list):
                for item in dados:
                    nome = item.get("name") or item.get("instanceName") or \
                        (item.get("instance") or {}).get("instanceName")
                    if nome:
                        existentes.append(nome)
        except json.JSONDecodeError:
            pass
    if EVOLUTION_INSTANCE in existentes:
        return {"existia": True}

    criacao = await cli.post(
        f"{EVOLUTION_URL}/instance/create",
        headers=_headers(),
        json={"instanceName": EVOLUTION_INSTANCE, "qrcode": True,
              "integration": "WHATSAPP-BAILEYS"},
    )
    try:
        corpo = criacao.json()
    except Exception:
        corpo = {"raw": criacao.text}
    return {"existia": False, "status": criacao.status_code, "resposta": corpo}


@router.get("/diagnostico")
async def diagnostico(request: Request):
    uid = usuario_id(request)
    online = await _evolution_online()
    sessao = _ler_sessao(uid) or {}
    return {
        "evolution_online": online,
        "url": EVOLUTION_URL,
        "instancia": EVOLUTION_INSTANCE,
        "estado_salvo": sessao.get("estado", "desconectado"),
        "telefone": sessao.get("telefone"),
        "instrucoes": None if online else INSTRUCOES,
    }


@router.post("/conectar")
async def conectar(request: Request):
    uid = usuario_id(request)
    if not await _evolution_online():
        _salvar_sessao(uid, "evolution_offline")
        raise HTTPException(status_code=503, detail={
            "erro": "Evolution API não está respondendo",
            **INSTRUCOES,
        })

    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        criacao = await _garantir_instancia(cli)

        # já conectado?
        estado_resp = await cli.get(
            f"{EVOLUTION_URL}/instance/connectionState/{EVOLUTION_INSTANCE}", headers=_headers())
        estado = _normalizar_estado(estado_resp.json() if estado_resp.status_code == 200 else {})
        if estado == "open":
            telefone = await _buscar_telefone(cli)
            _salvar_sessao(uid, "open", telefone)
            return {"estado": "open", "conectado": True, "telefone": telefone,
                    "mensagem": "WhatsApp já está conectado."}

        # pede o QR de conexão
        qr_resp = await cli.get(
            f"{EVOLUTION_URL}/instance/connect/{EVOLUTION_INSTANCE}", headers=_headers())
        qr = _extrair_qr(qr_resp.json() if qr_resp.status_code == 200 else
                         criacao.get("resposta", {}))
        if not qr.get("qrcode"):
            # fallback: alguns setups devolvem o QR só na criação
            qr = _extrair_qr(criacao.get("resposta", {}))
        if not qr.get("qrcode"):
            raise HTTPException(status_code=502, detail={
                "erro": "A Evolution não devolveu QR Code",
                "resposta_evolution": criacao.get("resposta"),
                "estado": estado,
            })

        _salvar_sessao(uid, "aguardando_qr", qr=qr["qrcode"])
        return {
            "estado": "aguardando_qr",
            "conectado": False,
            "qrcode": qr["qrcode"],
            "codigo_pareamento": qr.get("codigo_pareamento"),
            "instancia": EVOLUTION_INSTANCE,
            "instrucao": "Abra o WhatsApp > Dispositivos conectados > Conectar dispositivo e escaneie o QR.",
            "validade_segundos": 40,
        }


@router.get("/qrcode")
async def qrcode(request: Request):
    uid = usuario_id(request)
    if not await _evolution_online():
        raise HTTPException(status_code=503, detail={"erro": "Evolution API offline", **INSTRUCOES})
    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        r = await cli.get(f"{EVOLUTION_URL}/instance/connect/{EVOLUTION_INSTANCE}", headers=_headers())
        qr = _extrair_qr(r.json() if r.status_code == 200 else {})
    if not qr.get("qrcode"):
        raise HTTPException(status_code=502, detail="QR indisponível no momento")
    _salvar_sessao(uid, "aguardando_qr", qr=qr["qrcode"])
    return qr


async def _buscar_telefone(cli: httpx.AsyncClient) -> Optional[str]:
    try:
        r = await cli.get(f"{EVOLUTION_URL}/instance/fetchInstances", headers=_headers())
        dados = r.json()
        for item in dados if isinstance(dados, list) else []:
            nome = item.get("name") or (item.get("instance") or {}).get("instanceName")
            if nome == EVOLUTION_INSTANCE:
                dono = item.get("ownerJid") or item.get("owner") or \
                    (item.get("instance") or {}).get("owner")
                if dono:
                    return str(dono).split("@")[0]
    except Exception:
        return None
    return None


@router.get("/estado")
async def estado(request: Request):
    uid = usuario_id(request)
    if not await _evolution_online():
        return {"estado": "evolution_offline", "conectado": False,
                "instrucoes": INSTRUCOES, "sessao": _ler_sessao(uid)}
    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        r = await cli.get(f"{EVOLUTION_URL}/instance/connectionState/{EVOLUTION_INSTANCE}",
                          headers=_headers())
        atual = _normalizar_estado(r.json() if r.status_code == 200 else {})
        telefone = await _buscar_telefone(cli) if atual == "open" else None
    _salvar_sessao(uid, atual, telefone)
    return {"estado": atual, "conectado": atual == "open", "telefone": telefone,
            "instancia": EVOLUTION_INSTANCE}


@router.post("/desconectar")
async def desconectar(request: Request):
    uid = usuario_id(request)
    if not await _evolution_online():
        raise HTTPException(status_code=503, detail={"erro": "Evolution API offline", **INSTRUCOES})
    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        await cli.delete(f"{EVOLUTION_URL}/instance/logout/{EVOLUTION_INSTANCE}", headers=_headers())
        await cli.delete(f"{EVOLUTION_URL}/instance/delete/{EVOLUTION_INSTANCE}", headers=_headers())
    _salvar_sessao(uid, "desconectado", "")
    return {"estado": "desconectado", "conectado": False}


async def _enviar_texto(numero: str, mensagem: str) -> dict:
    numero = _limpar_numero(numero)
    if not numero:
        raise HTTPException(status_code=422, detail="Telefone inválido")
    if not await _evolution_online():
        raise HTTPException(status_code=503, detail={"erro": "Evolution API offline", **INSTRUCOES})

    async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
        # Evolution v2 / v1 (payloads diferentes)
        tentativas = [
            {"number": numero, "text": mensagem},
            {"number": numero, "textMessage": {"text": mensagem}},
            {"number": numero, "textMessage": {"text": mensagem}, "options": {"delay": 800}},
        ]
        ultimo = None
        for corpo in tentativas:
            r = await cli.post(f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
                               headers=_headers(), json=corpo)
            if r.status_code in (200, 201):
                try:
                    return r.json()
                except Exception:
                    return {"status": "enviado", "resposta": r.text}
            ultimo = {"status": r.status_code, "corpo": r.text[:400]}
    raise HTTPException(status_code=502, detail={"erro": "Falha ao enviar", "detalhe": ultimo})


@router.post("/enviar")
async def enviar_mensagem(data: EnviarMensagemRequest, request: Request):
    uid = usuario_id(request)
    numero = data.telefone or (_ler_sessao(uid) or {}).get("telefone")
    if not numero:
        raise HTTPException(status_code=422, detail="Nenhum WhatsApp conectado/telefone informado")
    resultado = await _enviar_texto(numero, data.mensagem)
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO whatsapp_mensagens (usuario_id,direcao,telefone,texto,criado_em) VALUES (?,?,?,?,?)",
        (uid, "saida", _limpar_numero(numero), data.mensagem, db.agora()))
    conn.commit()
    conn.close()
    return {"status": "enviado", "telefone": _limpar_numero(numero), "evolution": resultado}


@router.post("/teste")
async def enviar_teste(request: Request):
    uid = usuario_id(request)
    sessao = _ler_sessao(uid) or {}
    numero = sessao.get("telefone")
    if not numero:
        raise HTTPException(status_code=422, detail="Conecte o WhatsApp primeiro para receber o teste")
    mensagem = ("✅ *ConcursosAI conectado!*\n\n"
                "A partir de agora você recebe aqui:\n"
                "• novos editais compatíveis\n• lembretes de revisão\n• alertas de prazo\n\n"
                "Responda *status* para ver seu progresso.")
    resultado = await _enviar_texto(numero, mensagem)
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO whatsapp_mensagens (usuario_id,direcao,telefone,texto,criado_em) VALUES (?,?,?,?,?)",
        (uid, "saida", _limpar_numero(numero), mensagem, db.agora()))
    conn.commit()
    conn.close()
    return {"status": "enviado", "telefone": _limpar_numero(numero), "evolution": resultado}


@router.get("/link")
async def link_whatsapp(telefone: str, mensagem: str = "Olá! Vim pelo ConcursosAI"):
    """Fallback sem Evolution: abre o WhatsApp Web/app com a mensagem pronta."""
    return {"url": f"https://wa.me/{_limpar_numero(telefone)}?text={quote(mensagem)}"}


@router.get("/mensagens")
async def listar_mensagens(request: Request, limite: int = 30):
    uid = usuario_id(request)
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT * FROM whatsapp_mensagens WHERE usuario_id=? ORDER BY id DESC LIMIT ?",
        (uid, limite)).fetchall()
    conn.close()
    return [db.row_to_dict(r) for r in rows]


# ============================ WEBHOOK ============================
@webhook_router.post("/evolution")
async def webhook_evolution(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignorado"}

    evento = body.get("event")
    dados = body.get("data") or {}

    if evento in ("messages.upsert", "MESSAGES_UPSERT"):
        msg = dados if isinstance(dados, dict) else {}
        key = msg.get("key") or {}
        if key.get("fromMe"):
            return {"status": "ok"}
        numero = str(key.get("remoteJid", "")).split("@")[0]
        texto = _texto_da_mensagem(msg)
        if texto:
            await processar_comando(numero, texto)
    return {"status": "ok"}


def _texto_da_mensagem(msg: dict) -> str:
    m = msg.get("message") or {}
    for chave in ("conversation", "extendedTextMessage", "buttonsResponseMessage",
                  "listResponseMessage"):
        valor = m.get(chave)
        if isinstance(valor, str):
            return valor.strip()
        if isinstance(valor, dict):
            return (valor.get("text") or valor.get("selectedButtonId") or
                    valor.get("selectedRowId") or "").strip()
    return ""


def _usuario_por_telefone(numero: str) -> str:
    conn = db.get_conn()
    row = conn.execute("SELECT usuario_id FROM whatsapp_sessao WHERE telefone=?",
                       (numero,)).fetchone()
    conn.close()
    return row["usuario_id"] if row else "usr-demo"


async def processar_comando(numero: str, texto: str):
    """Responde comandos com dados REAIS do banco."""
    uid = _usuario_por_telefone(numero)
    cmd = texto.lower().strip()
    conn = db.get_conn()

    if cmd in ("status", "meu status", "progresso"):
        stat = conn.execute(
            "SELECT COUNT(*) t, SUM(correta) a FROM respostas WHERE usuario_id=?", (uid,)).fetchone()
        pend = conn.execute(
            "SELECT COUNT(*) c FROM revisoes WHERE usuario_id=? AND status='pendente'",
            (uid,)).fetchone()["c"]
        total, acertos = stat["t"] or 0, stat["a"] or 0
        taxa = round(acertos / total * 100, 1) if total else 0
        resposta = (f"📊 *Seu progresso*\n\nQuestões respondidas: {total}\n"
                    f"Acertos: {acertos} ({taxa}%)\nRevisões pendentes: {pend}")
    elif cmd.startswith(("revis", "revisao", "revisão")):
        rows = conn.execute(
            """SELECT q.disciplina, q.topico FROM revisoes v JOIN questoes q ON q.id=v.questao_id
               WHERE v.usuario_id=? AND v.status='pendente' LIMIT 5""", (uid,)).fetchall()
        if rows:
            linhas = "\n".join(f"• {r['disciplina']} — {r['topico']}" for r in rows)
            resposta = f"📚 *Revisões pendentes* ({len(rows)})\n\n{linhas}\n\nAcesse: {_app_url()}/revisao"
        else:
            resposta = "✅ Nenhuma revisão pendente agora. Bom trabalho!"
    elif cmd.startswith("simulado"):
        n = conn.execute("SELECT COUNT(*) c FROM questoes").fetchone()["c"]
        resposta = f"📝 Temos {n} questões no banco. Monte um simulado em {_app_url()}/simulados"
    elif cmd.startswith("buscar"):
        termo = texto[6:].strip()
        rows = conn.execute(
            "SELECT titulo FROM editais WHERE titulo LIKE ? LIMIT 5", (f"%{termo}%",)).fetchall()
        resposta = ("🔎 Encontrei:\n" + "\n".join(f"• {r['titulo']}" for r in rows)) if rows \
            else f"Nenhum edital encontrado para '{termo}'."
    elif cmd.startswith("editais"):
        rows = conn.execute(
            "SELECT titulo, data_prova FROM editais WHERE status='novo' ORDER BY score DESC LIMIT 5"
        ).fetchall()
        resposta = "🆕 *Novos editais*\n\n" + "\n".join(
            f"• {r['titulo']} (prova: {r['data_prova'] or 'a definir'})" for r in rows)
    else:
        resposta = ("Comandos disponíveis:\n\n"
                    "*status* — seu progresso\n*revisoes* — revisões pendentes\n"
                    "*simulados* — simulados disponíveis\n*editais* — novos editais\n"
                    "*buscar [termo]* — procurar concurso")
    conn.close()
    await enviar_texto(numero, resposta)


def _app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:5173")


async def enviar_texto(numero: str, mensagem: str):
    try:
        await _enviar_texto(numero, mensagem)
        conn = db.get_conn()
        conn.execute(
            "INSERT INTO whatsapp_mensagens (usuario_id,direcao,telefone,texto,criado_em) VALUES (?,?,?,?,?)",
            (_usuario_por_telefone(numero), "saida", numero, mensagem, db.agora()))
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[whatsapp] falha ao responder {numero}: {exc}")
