# backend/src/middleware/tenant.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Identificar tenant pelo domínio ou header
        host = request.headers.get("host", "")
        tenant_slug = request.headers.get("X-Tenant-Slug")
        
        if not tenant_slug:
            subdomain = host.split(".")[0]
            if subdomain not in ["localhost", "www", "api", "app"]:
                tenant_slug = subdomain
        
        # Por enquanto, usar tenant padrão
        request.state.tenant_id = tenant_slug or "default"
        request.state.tenant = {
            "id": tenant_slug or "default",
            "nome": "Plataforma Concursos",
            "slug": tenant_slug or "default",
            "plano": "pro",
            "cor_primaria": "#1E40AF"
        }
        
        response = await call_next(request)
        return response
