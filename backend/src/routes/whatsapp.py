# backend/src/routes/whatsapp.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import os
import httpx

router = APIRouter()
webhook_router = APIRouter()

EVOLUTION_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "concursos")

class VincularRequest(BaseModel):
    telefone: str

class EnviarMensagemRequest(BaseModel):
    telefone: str
    mensagem: str

@router.post("/vincular")
async def vincular_whatsapp(data: VincularRequest):
    numero = data.telefone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("55"):
        numero = "55" + numero
    
    # TODO: Salvar no banco e verificar
    return {"status": "vinculado", "telefone": numero, "verificado": False}

@router.post("/enviar")
async def enviar_mensagem(data: EnviarMensagemRequest):
    url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    payload = {"number": data.telefone, "text": data.mensagem}
    headers = {"apikey": EVOLUTION_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def status_conexao():
    url = f"{EVOLUTION_URL}/instance/connectionState/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=headers)
            return r.json()
        except Exception as e:
            return {"state": "disconnected", "error": str(e)}

# === WEBHOOK (recebe mensagens) ===
@webhook_router.post("/evolution")
async def webhook_evolution(request: Request):
    body = await request.json()
    
    event = body.get("event")
    
    if event == "messages.upsert":
        msg = body.get("data", {})
        key = msg.get("key", {})
        
        # Ignorar mensagens enviadas por nós
        if key.get("fromMe"):
            return {"status": "ok"}
        
        numero = key.get("remoteJid", "").replace("@s.whatsapp.net", "")
        msg_type = msg.get("messageType")
        
        if msg_type == "conversation":
            texto = msg.get("message", {}).get("conversation", "").lower().strip()
            await processar_comando(numero, texto)
        
        elif msg_type == "buttonsResponseMessage":
            button_id = msg.get("message", {}).get("buttonsResponseMessage", {}).get("selectedButtonId", "")
            await processar_botao(numero, button_id)
    
    elif event == "connection.update":
        state = body.get("data", {}).get("state")
        print(f"WhatsApp connection: {state}")
    
    return {"status": "ok"}

async def processar_comando(numero: str, texto: str):
    """Processa comandos de texto livre."""
    if texto in ["status", "meu status", "progresso"]:
        await enviar_texto(numero, "📊 Seu Progresso:\n\nQuestões: 245\nAcerto: 78%\nStreak: 7 dias 🔥\nRevisões pendentes: 12")
    elif texto in ["revisoes", "revisar", "revisão"]:
        await enviar_texto(numero, "📚 Você tem 12 questões para revisar hoje.\n\nAcesse: https://plataforma.com/revisao")
    elif texto in ["simulados", "simulado"]:
        await enviar_texto(numero, "📝 Simulados disponíveis:\n\n1. PRF 2024 — Completo\n2. PM-MS 2024 — Soldado\n\nAcesse: https://plataforma.com/simulados")
    else:
        await enviar_texto(numero, "Comandos: status, revisoes, simulados, buscar [termo]")

async def processar_botao(numero: str, button_id: str):
    """Processa clique em botão."""
    if button_id.startswith("aceitar_"):
        await enviar_texto(numero, "✅ Ótimo! Criando seu cronograma de estudos...")
    elif button_id.startswith("recusar_"):
        await enviar_texto(numero, "Entendido! Ajustando sugestões futuras.")
    elif button_id.startswith("salvar_"):
        await enviar_texto(numero, "📌 Salvo! Ative quando quiser pela plataforma.")

async def enviar_texto(numero: str, mensagem: str):
    url = f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    payload = {"number": numero, "text": mensagem}
    headers = {"apikey": EVOLUTION_KEY}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)
