# backend/src/security.py
"""Identificação do usuário a partir do JWT (com fallback para o usuário demo).

O app funciona sem login obrigatório: se não houver token válido, usa o usuário
demo — assim nenhuma tela fica quebrada.
"""

import os
from datetime import datetime, timedelta

from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "concursosai-secret-local")
JWT_ALG = "HS256"
DEMO_ID = "usr-demo"


def criar_token(usuario_id: str, dias: int = 7) -> str:
    payload = {"sub": usuario_id, "exp": datetime.utcnow() + timedelta(days=dias),
               "iat": datetime.utcnow()}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decodificar(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        return None


def usuario_id(request) -> str:
    """Extrai o id do usuário do header Authorization; cai no demo se ausente."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        dados = decodificar(auth.split(" ", 1)[1].strip())
        if dados and dados.get("sub"):
            return dados["sub"]
    return DEMO_ID
