# backend/src/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

load_dotenv()

from middleware.tenant import TenantMiddleware
from routes import auth, tenant, billing, concursos, questoes, simulados
from routes import cronograma, whatsapp, admin, editais

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Concursos SaaS iniciando...")
    yield
    # Shutdown
    print("Concursos SaaS encerrando...")

app = FastAPI(
    title="Concursos SaaS API",
    description="Plataforma de estudos para concursos públicos",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant Middleware
app.add_middleware(TenantMiddleware)

# Rotas
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(tenant.router, prefix="/api/tenant", tags=["Tenant"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(concursos.router, prefix="/api/concursos", tags=["Concursos"])
app.include_router(questoes.router, prefix="/api/questoes", tags=["Questões"])
app.include_router(simulados.router, prefix="/api/simulados", tags=["Simulados"])
app.include_router(cronograma.router, prefix="/api/cronograma", tags=["Cronograma"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(editais.router, prefix="/api/editais", tags=["Editais"])

# Webhook Evolution (sem prefixo /api)
app.include_router(whatsapp.webhook_router, prefix="/webhook", tags=["Webhook"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "concursos-saas"}

@app.get("/")
async def root():
    return {"message": "Concursos SaaS API v1.0", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
