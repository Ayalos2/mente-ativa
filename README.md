# Mente Ativa — monorepo

Resumo rápido de como rodar localmente e usar os recursos adicionados.

## Backend (local)

1. Copie o exemplo de env:

```powershell
copy backend\.env.sample backend\.env
# edite backend/.env e preencha DATABASE_URL e Firebase
```

2. Crie e ative virtualenv e instale dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

3. Rode o servidor:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Opcional: habilite o resumo por LLM para o painel médico

```powershell
setx GEMINI_API_KEY "sua-chave"
setx GEMINI_MODEL "gemini-2.5-flash"
```

Sem essa chave, o sistema usa um resumo local conservador como fallback.

## Frontend (local)

```bash
cd frontend/mente-ativa
npm ci
npm run dev
```

## Usando Docker Compose (dev)

```bash
docker-compose up --build
```

## CI

Adicionado workflow GitHub Actions em `.github/workflows/ci.yml` que faz checagem de sintaxe Python e build do frontend.

## Segurança

- Nunca comite `backend/service-account.json`. Está no `.gitignore`.
- Use segredos do CI para configurar variáveis sensíveis em deploy.

---

Se quiser, posso:
- Gerar um `Dockerfile` para o frontend e otimizar o `docker-compose` para produção;
- Adicionar testes automatizados (backend + frontend) e configurar o CI para executá-los;
- Criar issues/checklist detalhado com subtasks para as pendências.
