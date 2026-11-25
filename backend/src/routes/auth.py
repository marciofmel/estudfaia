# backend/src/routes/auth.py
"""Autenticação real com SQLite + PBKDF2 + JWT."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import db
from security import criar_token, usuario_id

router = APIRouter()


class RegistroRequest(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    senha: str


def _usuario_publico(row):
    return {
        "id": row["id"], "nome": row["nome"], "email": row["email"],
        "telefone": row["telefone"], "plano": row["plano"], "role": row["role"],
    }


@router.post("/registro")
async def registro(data: RegistroRequest):
    email = data.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=422, detail="E-mail inválido")
    if len(data.senha) < 6:
        raise HTTPException(status_code=422, detail="A senha precisa ter ao menos 6 caracteres")

    conn = db.get_conn()
    if conn.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    uid = "usr-" + email.split("@")[0][:16] + "-" + str(len(email))
    conn.execute(
        """INSERT OR REPLACE INTO usuarios (id,nome,email,senha_hash,telefone,plano,role,criado_em)
           VALUES (?,?,?,?,?,?,?,?)""",
        (uid, data.nome.strip(), email, db.hash_senha(data.senha), data.telefone,
         "free", "aluno", db.agora()))
    conn.execute(
        """INSERT OR IGNORE INTO preferencias (usuario_id,areas,regioes,salario_min,notificacoes)
           VALUES (?,?,?,?,?)""",
        (uid, json.dumps(["Policial"]), json.dumps(["Nacional"]), 3000.0,
         json.dumps({"editais": True, "revisao": True, "prazos": True, "cronograma": True})))
    conn.commit()
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
    conn.close()
    return {"access_token": criar_token(uid), "token_type": "bearer",
            "usuario": _usuario_publico(row)}


@router.post("/login")
async def login(data: LoginRequest):
    email = data.email.strip().lower()
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
    conn.close()
    if not row or not db.verificar_senha(data.senha, row["senha_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    return {"access_token": criar_token(row["id"]), "token_type": "bearer",
            "usuario": _usuario_publico(row)}


@router.get("/me")
async def me(request: Request):
    uid = usuario_id(request)
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
    conn.close()
    if not row:
        return {"id": uid, "nome": "Aluno Demo", "email": "demo@concursosai.com.br", "plano": "pro"}
    return _usuario_publico(row)


@router.api_route("/demo", methods=["GET", "POST"])
async def conta_demo():
    """Login rápido para testar o app (usuário demo já populado)."""
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM usuarios WHERE id='usr-demo'").fetchone()
    conn.close()
    return {"access_token": criar_token("usr-demo"), "token_type": "bearer",
            "usuario": _usuario_publico(row)}
