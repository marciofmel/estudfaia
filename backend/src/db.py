# backend/src/db.py
"""Persistência real do ConcursosAI usando SQLite (stdlib, zero dependência).

Substitui os mocks: usuários, respostas, revisões, concursos, questões,
editais, cronogramas e estado do WhatsApp ficam gravados em backend/concursos.db
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, date, timedelta

from seed_data import CONCURSOS, QUESTOES, EDITAIS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("DB_PATH") or os.path.join(BASE_DIR, "concursos.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    telefone TEXT,
    plano TEXT DEFAULT 'free',
    role TEXT DEFAULT 'aluno',
    criado_em TEXT
);

CREATE TABLE IF NOT EXISTS concursos (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    orgao TEXT,
    banca TEXT,
    cargo TEXT,
    salario REAL,
    data_prova TEXT,
    area TEXT,
    uf TEXT,
    status TEXT,
    vagas INTEGER
);

CREATE TABLE IF NOT EXISTS questoes (
    id TEXT PRIMARY KEY,
    concurso_id TEXT,
    disciplina TEXT,
    topico TEXT,
    banca TEXT,
    ano INTEGER,
    dificuldade INTEGER,
    enunciado TEXT,
    alternativas TEXT,
    correta TEXT,
    explicacao TEXT,
    estatistica REAL DEFAULT 60.0
);

CREATE TABLE IF NOT EXISTS respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    questao_id TEXT,
    alternativa TEXT,
    correta INTEGER,
    tempo_gasto INTEGER DEFAULT 0,
    criado_em TEXT
);

CREATE TABLE IF NOT EXISTS revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    questao_id TEXT,
    repeticoes INTEGER DEFAULT 0,
    intervalo INTEGER DEFAULT 1,
    facilidade REAL DEFAULT 2.5,
    proxima_revisao TEXT,
    status TEXT DEFAULT 'pendente',
    UNIQUE(usuario_id, questao_id)
);

CREATE TABLE IF NOT EXISTS editais (
    id TEXT PRIMARY KEY,
    titulo TEXT,
    orgao TEXT,
    banca TEXT,
    cargo TEXT,
    salario REAL,
    data_prova TEXT,
    url TEXT,
    fonte TEXT,
    score INTEGER DEFAULT 50,
    status TEXT DEFAULT 'novo',
    area TEXT,
    uf TEXT
);

CREATE TABLE IF NOT EXISTS interesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    edital_id TEXT,
    tipo TEXT,
    criado_em TEXT,
    UNIQUE(usuario_id, edital_id, tipo)
);

CREATE TABLE IF NOT EXISTS preferencias (
    usuario_id TEXT PRIMARY KEY,
    areas TEXT,
    regioes TEXT,
    salario_min REAL DEFAULT 0,
    notificacoes TEXT
);

CREATE TABLE IF NOT EXISTS cronogramas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    concurso_id TEXT,
    horas_dia REAL DEFAULT 3,
    plano TEXT,
    criado_em TEXT
);

CREATE TABLE IF NOT EXISTS whatsapp_sessao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    instance TEXT,
    telefone TEXT,
    estado TEXT DEFAULT 'desconectado',
    qr TEXT,
    atualizado_em TEXT,
    UNIQUE(usuario_id)
);

CREATE TABLE IF NOT EXISTS whatsapp_mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    direcao TEXT,
    telefone TEXT,
    texto TEXT,
    criado_em TEXT
);

CREATE TABLE IF NOT EXISTS simulados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id TEXT,
    titulo TEXT,
    questoes TEXT,
    respostas TEXT,
    acertos INTEGER,
    total INTEGER,
    criado_em TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --------------------------- senhas ---------------------------
def hash_senha(senha: str, salt: str = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        salt, digest = armazenado.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_senha(senha, salt).split("$", 1)[1], digest)


# --------------------------- seed ---------------------------
def init_db(force: bool = False) -> dict:
    conn = get_conn()
    conn.executescript(SCHEMA)

    if force:
        for tabela in ("usuarios", "concursos", "questoes", "respostas", "revisoes",
                       "editais", "interesses", "preferencias", "cronogramas",
                       "whatsapp_sessao", "whatsapp_mensagens", "simulados"):
            conn.execute(f"DELETE FROM {tabela}")

    inseridos = {"concursos": 0, "questoes": 0, "editais": 0, "usuarios": 0}

    for c in CONCURSOS:
        cur = conn.execute(
            """INSERT OR IGNORE INTO concursos
               (id,titulo,orgao,banca,cargo,salario,data_prova,area,uf,status,vagas)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (c["id"], c["titulo"], c["orgao"], c["banca"], c["cargo"], c["salario"],
             c["data_prova"], c["area"], c["uf"], c["status"], c["vagas"]),
        )
        inseridos["concursos"] += cur.rowcount

    for q in QUESTOES:
        qid, cid, disc, topico, banca, ano, dif, enun, alts, correta, explic = q
        estat = 55 + (hash(qid) % 40)
        cur = conn.execute(
            """INSERT OR IGNORE INTO questoes
               (id,concurso_id,disciplina,topico,banca,ano,dificuldade,enunciado,
                alternativas,correta,explicacao,estatistica)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (qid, cid, disc, topico, banca, ano, dif, enun,
             json.dumps(alts, ensure_ascii=False), correta, explic, estat),
        )
        inseridos["questoes"] += cur.rowcount

    for e in EDITAIS:
        cur = conn.execute(
            """INSERT OR IGNORE INTO editais
               (id,titulo,orgao,banca,cargo,salario,data_prova,url,fonte,score,status,area,uf)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (e["id"], e["titulo"], e["orgao"], e["banca"], e["cargo"], e["salario"],
             e["data_prova"], e["url"], e["fonte"], e["score"], e["status"], e["area"], e["uf"]),
        )
        inseridos["editais"] += cur.rowcount

    # Usuário demo para o app já abrir logado/funcional
    demo_email = "demo@concursosai.com.br"
    existe = conn.execute("SELECT id FROM usuarios WHERE email=?", (demo_email,)).fetchone()
    if not existe:
        uid = "usr-demo"
        conn.execute(
            """INSERT INTO usuarios (id,nome,email,senha_hash,telefone,plano,role,criado_em)
               VALUES (?,?,?,?,?,?,?,?)""",
            (uid, "Aluno Demo", demo_email, hash_senha("demo1234"), None, "pro", "aluno", agora()),
        )
        conn.execute(
            """INSERT INTO preferencias (usuario_id,areas,regioes,salario_min,notificacoes)
               VALUES (?,?,?,?,?)""",
            (uid, json.dumps(["Policial", "Tribunal"]), json.dumps(["MS", "Nacional"]), 4000.0,
             json.dumps({"editais": True, "revisao": True, "prazos": True, "cronograma": True})),
        )
        inseridos["usuarios"] += 1

    conn.commit()
    conn.close()
    return inseridos


# --------------------------- helpers ---------------------------
def row_to_dict(row):
    return {k: row[k] for k in row.keys()} if row else None


def usuario_demo_id() -> str:
    return "usr-demo"
