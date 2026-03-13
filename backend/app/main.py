from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .database import engine, Base, get_db

app = FastAPI(title="Mente Ativa API")


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