from fastapi import APIRouter

router = APIRouter()

@router.get("/config")
async def tenant_config():
    return {
        "nome": "ConcursosAI",
        "logo_url": None,
        "cor_primaria": "#1E40AF",
        "dominio": "localhost"
    }
