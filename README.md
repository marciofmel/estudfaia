# ConcursosAI — Plataforma SaaS de Estudos para Concursos Públicos

## 🚀 Funcionalidades

- **Banco de Questões** — Milhares de questões por banca, disciplina e assunto
- **Simulados** — Provas reais com cronômetro e ranking
- **IA Monitora Editais** — Busca diária de novos editais, notifica via WhatsApp
- **Cronograma Automático** — IA monta plano de estudos personalizado a partir do edital
- **Revisão Espaçada (SM-2)** — Questões erradas revisadas em intervalos otimizados
- **Multi-Concurso** — Estude para PRF, INSS, PM-MS simultaneamente
- **WhatsApp** — Notificações, lembretes e comandos via WhatsApp (Evolution API)
- **SaaS Multi-Tenant** — White-label para escolas e cursinhos
- **Billing** — MercadoPago (PIX, cartão, boleto)

## 📁 Estrutura

```
concursos-saas/
├── backend/          # FastAPI (Python)
│   ├── src/
│   │   ├── main.py
│   │   ├── middleware/
│   │   ├── routes/
│   │   └── ...
│   └── prisma/
├── frontend/         # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── ...
├── crawler/          # Scraper de editais
├── docker-compose.yml # Evolution API + PostgreSQL + Redis
└── .env.example
```

## 🛠️ Setup Local

### 1. Clone e configure
```bash
cd concursos-saas
cp .env.example .env
# Preencha as variáveis no .env
```

### 2. Suba a infra (Docker)
```bash
docker-compose up -d
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
cd src
python main.py
# API em http://localhost:8000
# Docs em http://localhost:8000/docs
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
# App em http://localhost:5173
```

## 📱 WhatsApp (Evolution API)

1. Suba o Docker: `docker-compose up -d`
2. Acesse: http://localhost:8080
3. Crie instância "concursos"
4. Escaneie QR Code com WhatsApp
5. Configure webhook: http://localhost:8000/webhook/evolution

## 💰 Planos

| Plano | Preço | Questões/dia | Concursos |
|-------|-------|-------------|-----------|
| Gratuito | R$ 0 | 20 | 1 |
| Essencial | R$ 19,90 | 100 | 3 |
| Pro | R$ 49,90 | Ilimitado | 10 |
| Premium | R$ 99,90 | Ilimitado | Ilimitado |
| Enterprise | R$ 2.999/mês | Ilimitado | Ilimitado (500 alunos) |

## 🚢 Deploy

- **Backend:** Render (render.yaml)
- **Frontend:** Vercel
- **Banco:** Neon (PostgreSQL)
- **WhatsApp:** Evolution API (VPS)

## 📞 Suporte

Desenvolvido com ❤️ para concurseiros.
