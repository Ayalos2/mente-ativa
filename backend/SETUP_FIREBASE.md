Configuração Firebase para o backend

Passos rápidos:

1) Gerar service account
- Acesse Firebase Console -> Project Settings -> Service Accounts
- Clique em "Generate new private key" e baixe o JSON
- Salve o arquivo como `backend/service-account.json`

2) Ajustar variáveis de ambiente
- O backend lê `backend/.env` por padrão.
- Garanta as variáveis abaixo configuradas:
  - `FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json`
  - `FIREBASE_SERVICE_ACCOUNT_JSON=<json-em-uma-linha>` (opcional, alternativa ao arquivo)
  - `FIREBASE_PROJECT_ID=<seu-project-id>`
  - `FIREBASE_API_KEY=<sua-web-api-key>`
  - `GEMINI_API_KEY=<sua-chave-opcional-para-resumo-ia>`
  - `GEMINI_MODEL=gemini-2.5-flash`

3) Reiniciar backend
- No diretório `backend/` rode seu servidor (uvicorn):

```powershell
# ativar virtualenv (se aplicável)
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

4) Testar conexão com Firestore
- Acesse:
  - `http://localhost:8000/firebase/status`
- Se o service account estiver faltando ou inválido você verá uma mensagem de erro clara indicando o problema.

5) Testar vincular paciente
- Faça login no frontend e copie o token ID (o código `loginComGoogle` retorna `token`).
- Exemplo curl:

```bash
curl -X POST http://localhost:8000/doctor-links/link \
  -H "Authorization: Bearer <ID_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"patientEmail":"paciente@example.com"}'
```

Respostas esperadas:
- 200: `{"status":"sucesso","vinculo":{...}}`
- 401: Token inválido ou não informado
- 503: Service account ausente ou problemas ao inicializar Firestore
- 404: Paciente não encontrado na coleção `usuarios` do Firestore

6) Observações de segurança
- Nunca comite `service-account.json` no repositório.
- O caminho `FIREBASE_SERVICE_ACCOUNT_PATH` é resolvido relativo ao diretório `backend/`.
- Use segredos gerenciados em produção (Azure Key Vault, AWS Secrets Manager, etc.)
