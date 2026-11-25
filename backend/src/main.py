# backend/src/main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

import db
from middleware.tenant import TenantMiddleware
from routes import auth, tenant, billing, concursos, questoes, simulados
from routes import cronograma, whatsapp, admin, editais, ia, perfil


@asynccontextmanager
async def lifespan(app: FastAPI):
    inseridos = db.init_db()
    print(f"Concursos SaaS iniciando — banco: {db.DB_PATH} (novos: {inseridos})")
    yield
    print("Concursos SaaS encerrando...")


app = FastAPI(
    title="ConcursosAI API",
    description="Plataforma SaaS de estudos para concursos públicos com IA local e WhatsApp (Evolution API)",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

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
app.include_router(ia.router, prefix="/api/ia", tags=["IA"])
app.include_router(perfil.router, prefix="/api/perfil", tags=["Perfil"])

# Webhook Evolution (sem /api, é o que o docker-compose aponta)
app.include_router(whatsapp.webhook_router, prefix="/webhook", tags=["Webhook"])


@app.get("/health")
async def health():
    conn = db.get_conn()
    try:
        q = conn.execute("SELECT COUNT(*) c FROM questoes").fetchone()["c"]
        e = conn.execute("SELECT COUNT(*) c FROM editais").fetchone()["c"]
        u = conn.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
    except Exception:
        q = e = u = 0
    conn.close()
    return {"status": "ok", "service": "concursos-saas", "versao": "1.1.0",
            "banco": {"questoes": q, "editais": e, "usuarios": u}}


@app.get("/api/info")
async def info():
    return {"message": "ConcursosAI API v1.1", "docs": "/docs",
            "ia": "/api/ia/status", "whatsapp": "/api/whatsapp/diagnostico"}


# Serve o frontend buildado (quando existir), para rodar tudo num só processo
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "..", "frontend", "dist")
FRONTEND_DIST = os.path.abspath(FRONTEND_DIST)
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")),
              name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    async def spa(caminho: str):
        if caminho.startswith(("api", "webhook", "docs", "openapi", "health")):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        arquivo = os.path.join(FRONTEND_DIST, caminho)
        if caminho and os.path.isfile(arquivo):
            return FileResponse(arquivo)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn
    porta = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=porta)
