# 🧠 Mente Ativa

Plataforma para monitoramento cognitivo — pacientes realizam testes cognitivos e médicos especialistas acompanham a evolução por meio de resumos clínicos gerados por IA.

> **Monorepo** contendo backend (FastAPI + Firebase) e frontend (Vue 3 + Vite + Tailwind CSS).

---

## 📋 Índice

- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração do Backend](#configuração-do-backend)
- [Configuração do Frontend](#configuração-do-frontend)
- [Docker Compose](#docker-compose)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Firebase](#firebase)
- [API Endpoints](#api-endpoints)
- [CI/CD](#cicd)
- [Segurança](#segurança)
- [Comandos Úteis](#comandos-úteis)

---

## Tecnologias

### Backend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **Python** | 3.11 | Linguagem principal |
| **FastAPI** | — | Framework web assíncrono |
| **Uvicorn** | — | Servidor ASGI |
| **Firebase Admin SDK** | — | Autenticação e Firestore |
| **SQLAlchemy** | — | ORM para banco local (apenas login legado) |
| **Pydantic** | — | Validação de schemas |
| **python-dotenv** | — | Gerenciamento de variáveis de ambiente |
| **Requests** | — | Chamadas HTTP (Gemini API e Firebase Auth REST) |
| **Docker** | — | Containerização |

### Frontend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **Vue 3** | ^3.5.30 | Framework reativo |
| **Vite** | ^8.0.0 | Bundler e dev server |
| **Vue Router** | ^4.6.4 | Roteamento SPA |
| **Axios** | ^1.13.6 | Cliente HTTP |
| **Firebase JS SDK** | ^12.12.1 | Auth e Firestore no cliente |
| **Tailwind CSS** | ^4.2.1 | Estilização utilitária |
| **PostCSS** | — | Processamento CSS |
| **Node.js / npm** | 18+ | Runtime e gerenciador de pacotes |

### Serviços Externos

- **Firebase Authentication** — Login com Google e e-mail/senha
- **Firebase Firestore** — Banco de dados principal: perfis, testes, vínculos e resumos
- **Google Gemini API** — Geração opcional de resumos clínicos por LLM (fallback local quando não configurada)

### Infraestrutura

- **Docker Compose** — Orquestração dos serviços em desenvolvimento
- **GitHub Actions** — CI com verificação de sintaxe Python e build do frontend

---

## Pré-requisitos

- **Python 3.11+**
- **Node.js 18+** e **npm**
- **Conta Firebase** com Authentication e Firestore ativados
- **Docker** e **Docker Compose** (opcional, para ambiente conteinerizado)

---

## Estrutura do Projeto

```
mente-ativa/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Rotas e configuração FastAPI
│   │   ├── database.py          # Conexão SQLAlchemy (uso legado)
│   │   └── services/
│   │       ├── firebase_auth.py     # Verificação de token Firebase
│   │       ├── firebase_firestore.py # Cliente Firestore
│   │       ├── llm_summary.py       # Resumo clínico (Gemini + fallback)
│   │       └── test_results.py      # CRUD de resultados no Firestore
│   ├── .env.sample              # Exemplo de variáveis de ambiente
│   ├── .env.example             # Exemplo alternativo
│   ├── Dockerfile               # Imagem Docker do backend
│   ├── requirements.txt         # Dependências Python
│   ├── service-account.json.sample  # Template da service account Firebase
│   └── SETUP_FIREBASE.md        # Guia de configuração Firebase
│
├── frontend/
│   ├── mente-ativa/             # Aplicação Vue 3
│   │   ├── src/
│   │   │   ├── main.js              # Entry point
│   │   │   ├── App.vue              # Componente raiz
│   │   │   ├── style.css            # Estilos globais + Tailwind
│   │   │   ├── config/
│   │   │   │   └── firebase.js      # Inicialização Firebase
│   │   │   ├── router/
│   │   │   │   └── index.js         # Rotas com guardas de autenticação
│   │   │   ├── services/
│   │   │   │   └── doctorLinks.js   # API de vínculo médico-paciente
│   │   │   ├── views/               # Páginas da aplicação
│   │   │   ├── components/          # Componentes reutilizáveis
│   │   │   ├── composables/         # Composables Vue 3
│   │   │   ├── stores/              # Gerenciamento de estado
│   │   │   ├── utils/               # Utilitários
│   │   │   └── data/                # Dados estáticos
│   │   ├── .env.example             # Exemplo de variáveis do frontend
│   │   ├── index.html
│   │   ├── vite.config.js
│   │   ├── postcss.config.js
│   │   └── package.json
│   ├── firebase.json            # Configuração Firebase Hosting
│   ├── firestore.rules          # Regras de segurança Firestore
│   └── firestore.indexes.json   # Índices compostos Firestore
│
├── docker-compose.yml           # Orquestração dos serviços
├── .gitignore
└── README.md
```

---

## Configuração do Backend

### 1. Clone o repositório

```bash
git clone https://github.com/Ayalos2/mente-ativa.git
cd mente-ativa
```

### 2. Configure as variáveis de ambiente

```powershell
copy backend\.env.sample backend\.env
```

Edite `backend/.env` com suas credenciais:

```env
DATABASE_URL=sqlite:///./mente_ativa.db
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
FIREBASE_PROJECT_ID=seu-project-id
FIREBASE_API_KEY=sua-web-api-key
FRONTEND_ORIGIN=http://localhost:5173
```

> **Nota:** O `DATABASE_URL` com SQLite é usado apenas para login legado por email/senha. Todos os dados principais (testes, perfis, vínculos) são armazenados no **Firebase Firestore**.

### 3. Crie e ative o virtualenv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Instale as dependências

```powershell
pip install -r backend/requirements.txt
```

### 5. Configure o Firebase

Siga o guia detalhado em [backend/SETUP_FIREBASE.md](backend/SETUP_FIREBASE.md):

1. Acesse Firebase Console → Project Settings → Service Accounts
2. Gere uma nova chave privada e salve como `backend/service-account.json`
3. Configure as variáveis `FIREBASE_PROJECT_ID` e `FIREBASE_API_KEY` no `.env`

### 6. Inicie o servidor

```powershell
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

Acesse a documentação interativa em: http://localhost:8000/docs

### 7. (Opcional) Habilite resumo por LLM

```powershell
setx GEMINI_API_KEY "sua-chave-gemini"
setx GEMINI_MODEL "gemini-2.5-flash"
```

Sem essa chave, o sistema usa um resumo local conservador como fallback.

---

## Configuração do Frontend

### 1. Acesse a pasta do frontend

```bash
cd frontend/mente-ativa
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

Edite `frontend/mente-ativa/.env` com as credenciais do seu projeto Firebase:

```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
```

### 3. Instale as dependências

```bash
npm ci
```

### 4. Inicie o servidor de desenvolvimento

```bash
npm run dev
```

Acesse em: http://localhost:5173

---

## Docker Compose

Para rodar ambos os serviços simultaneamente:

```bash
docker-compose up --build
```

Isso iniciará:
- **Backend** em http://localhost:8000
- **Frontend** em http://localhost:5173

Certifique-se de que o arquivo `backend/.env` esteja configurado antes de executar.

---

## Variáveis de Ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | ❌ | URL de conexão SQLite (apenas login legado por email/senha) |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | ✅* | Caminho para o JSON da service account |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | ✅* | Conteúdo da service account em JSON (alternativa ao path) |
| `FIREBASE_PROJECT_ID` | ✅ | ID do projeto Firebase |
| `FIREBASE_API_KEY` | ✅ | Web API Key do Firebase |
| `FRONTEND_ORIGIN` | ❌ | Origem permitida para CORS (padrão: `http://localhost:5173`) |
| `GEMINI_API_KEY` | ❌ | Chave da API Google Gemini (para resumo por IA) |
| `GEMINI_MODEL` | ❌ | Modelo Gemini (padrão: `gemini-2.5-flash`) |

\* É necessário configurar `FIREBASE_SERVICE_ACCOUNT_PATH` **ou** `FIREBASE_SERVICE_ACCOUNT_JSON`.

### Frontend (`frontend/mente-ativa/.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `VITE_FIREBASE_API_KEY` | ✅ | Web API Key do Firebase |
| `VITE_FIREBASE_AUTH_DOMAIN` | ✅ | Auth domain do Firebase |
| `VITE_FIREBASE_PROJECT_ID` | ✅ | ID do projeto Firebase |
| `VITE_FIREBASE_APP_ID` | ✅ | App ID do Firebase |

---

## Firebase

### Autenticação

O projeto utiliza Firebase Authentication com dois provedores:
- **Google Sign-In** — Login com conta Google
- **E-mail/Senha** — Cadastro e login tradicionais

### Firestore (Banco de Dados Principal)

O Firestore é o banco de dados principal da aplicação. Coleções utilizadas:

| Coleção | Descrição |
|---|---|
| `usuarios` | Perfis de usuários (pacientes e médicos) |
| `historico_testes` | Resultados de testes cognitivos |
| `vinculos_medico_paciente` | Vínculos entre médicos e pacientes |
| `resumos_saude_paciente` | Resumos clínicos gerados por IA |
| `diagnosticos_medicos` | Diagnósticos textuais salvos por médicos |

### Regras de Segurança

As regras do Firestore (`frontend/firestore.rules`) garantem que:
- Usuários só acessam seus próprios dados (`request.auth.uid == userId`)
- Resultados de testes são vinculados ao `userKey` do usuário autenticado
- Demais documentos têm acesso negado por padrão

---

## API Endpoints

### Saúde e Diagnóstico

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Status da API |
| `GET` | `/test_db` | Testa conexão com o banco local (SQLite legado) |
| `GET` | `/firebase/status` | Status da conexão Firebase |

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/login` | Login com e-mail e senha (SQLite legado) |
| `POST` | `/auth/google` | Login com Google (token Firebase) |

### Testes Cognitivos (Firestore)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/tests/results` | Salva resultado de um teste no Firestore |
| `GET` | `/tests/results?userKey=...` | Lista histórico de testes do usuário do Firestore |

### Vínculo Médico-Paciente (Firestore)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/doctor-links/link` | Médico vincula paciente por e-mail |
| `GET` | `/doctor-links/patients` | Médico lista seus pacientes |
| `GET` | `/doctor-links/patients/{uid}/tests` | Médico vê testes de um paciente |
| `GET` | `/doctor-links/patients/{uid}/summary` | Médico vê resumo clínico de um paciente |
| `GET` | `/doctor-links/my-doctors` | Paciente lista seus médicos |
| `POST` | `/doctor-links/request` | Paciente solicita vínculo com médico |
| `GET` | `/doctor-links/my-health-summary` | Paciente vê seu resumo de saúde |
| `POST` | `/doctor-links/my-health-summary/generate` | Paciente gera seu resumo de saúde |
| `POST` | `/doctor-links/patients/{uid}/generate-summary` | Médico gera resumo LLM do paciente |
| `POST` | `/doctor-links/patients/{uid}/diagnosis` | Médico salva diagnóstico textual |
| `GET` | `/doctor-links/patients/{uid}/diagnosis` | Médico visualiza diagnóstico salvo |
| `POST` | `/doctor-links/patients/{uid}/publish-summary` | Médico disponibiliza resumo para paciente |

### Vínculos (SQLite Legado)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/links` | Cria vínculo médico-paciente no SQLite |
| `DELETE` | `/links` | Remove vínculo |
| `GET` | `/links/doctor/{key}` | Lista pacientes de um médico |
| `GET` | `/links/patient/{key}` | Lista médicos de um paciente |

---

## CI/CD

O workflow do GitHub Actions (`.github/workflows/ci.yml`) executa:

1. **Verificação de sintaxe Python** — `python -m py_compile` em todos os arquivos `.py`
2. **Build do frontend** — `npm ci && npm run build`

Para configurar segredos no CI, utilize:

| Segredo | Descrição |
|---|---|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Service account do Firebase (JSON em uma linha) |
| `FIREBASE_API_KEY` | Web API Key do Firebase |
| `FIREBASE_PROJECT_ID` | ID do projeto Firebase |

---

## Segurança

- **Nunca comite** `backend/service-account.json` — está no `.gitignore`
- **Nunca comite** arquivos `.env` com credenciais reais
- Use **segredos gerenciados** em produção (GitHub Secrets, Azure Key Vault, AWS Secrets Manager, etc.)
- As regras do Firestore garantem isolamento de dados entre usuários
- Tokens Firebase são validados em todas as rotas protegidas do backend

---

## Comandos Úteis

### Iniciar backend (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; & .\.venv\Scripts\Activate.ps1; Set-Location backend; python -m uvicorn app.main:app --reload --host localhost --port 8000
```

### Iniciar frontend (PowerShell)

```powershell
Set-Location frontend\mente-ativa; npm run dev -- --host localhost
```

### Build do frontend para produção

```bash
cd frontend/mente-ativa
npm run build
```

### Deploy Firebase Hosting

```bash
cd frontend
firebase deploy
```

---

## Licença

Projeto desenvolvido para fins acadêmicos e de pesquisa.