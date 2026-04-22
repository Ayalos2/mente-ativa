import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .services.firebase_auth import verify_firebase_token

app = FastAPI(title="Mente Ativa API")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de dados para receber o login
class LoginSchema(BaseModel):
    email: str
    senha: str


class GoogleLoginSchema(BaseModel):
    credential: str
    user: dict | None = None

@app.post("/login")
def login(dados: LoginSchema, db: Session = Depends(get_db)):
    # Busca o usuário no banco
    usuario = db.execute(
        text("SELECT * FROM usuarios WHERE email = :email AND senha = :senha"),
        {"email": dados.email, "senha": dados.senha},
    ).fetchone()
    
    if usuario:
        return {"status": "sucesso", "usuario": usuario.nome}
    else:
        return {"status": "erro", "mensagem": "E-mail ou senha incorretos"}


@app.post("/auth/google")
def login_google(dados: GoogleLoginSchema, db: Session = Depends(get_db)):
    token_info = verify_firebase_token(dados.credential)

    email = token_info.get("email")
    nome = token_info.get("name") or (dados.user.get("nome") if dados.user else email)

    if not email:
        raise HTTPException(status_code=400, detail="Token Google sem e-mail")

    usuario = db.execute(
        text("SELECT nome FROM usuarios WHERE email = :email"),
        {"email": email},
    ).fetchone()

    if usuario:
        nome_usuario = usuario.nome
    else:
        nome_usuario = nome

    return {
        "status": "sucesso",
        "usuario": nome_usuario,
        "email": email,
        "provedor": "google",
    }


@app.on_event("startup")
def init_database():
    # Mantem a API de pe mesmo se o banco estiver indisponivel no boot.
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        print(f"Aviso ao inicializar banco: {exc}")

@app.get("/")
def home():
    return {
        "mensagem": "API Mente Ativa conectada ao Supabase!",
        "status": "Online"
    }

# Rota de teste para verificar se a conexão com o banco está ok
@app.get("/test_db")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Conexão com Supabase bem-sucedida!"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Falha na conexão com banco: {str(e)}")