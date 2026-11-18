# backend/src/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, EmailStr
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_EXPIRES = os.getenv("JWT_EXPIRES_IN", "7d")

class RegistroRequest(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str = None

class LoginRequest(BaseModel):
    email: str
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: dict

@router.post("/registro", response_model=TokenResponse)
async def registro(data: RegistroRequest):
    # TODO: Salvar no banco (Prisma)
    # Por enquanto, mock
    usuario = {
        "id": "mock-uuid",
        "nome": data.nome,
        "email": data.email,
        "role": "aluno",
        "plano": "free"
    }
    
    token = jwt.encode(
        {"sub": usuario["id"], "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    
    return TokenResponse(access_token=token, usuario=usuario)

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    # TODO: Verificar no banco
    usuario = {
        "id": "mock-uuid",
        "nome": "João Silva",
        "email": data.email,
        "role": "aluno",
        "plano": "pro"
    }
    
    token = jwt.encode(
        {"sub": usuario["id"], "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    
    return TokenResponse(access_token=token, usuario=usuario)

@router.get("/me")
async def me():
    return {"id": "mock-uuid", "nome": "João Silva", "email": "joao@email.com", "plano": "pro"}
