import os
from fastapi import FastAPI, Depends, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from firebase_admin import firestore
from .database import engine, Base, get_db
from .services.firebase_auth import verify_firebase_token
from .services.firebase_firestore import get_firestore_client
from .services.llm_summary import gerar_resumo_clinico_paciente
from .services.test_results import listar_historico_teste, salvar_resultado_teste

app = FastAPI(title="Mente Ativa API")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
print(f"Origem do Front-end configurada no CORS: {FRONTEND_ORIGIN}")
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


class TestResultSchema(BaseModel):
    userKey: str
    userEmail: str | None = None
    userName: str | None = None
    userPhoto: str | None = None
    testId: str
    testName: str
    summary: dict
    questionResults: list[dict]


class LinkPatientSchema(BaseModel):
    patientEmail: str

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

    # Tenta buscar usuário no banco, mas não falha se banco não estiver disponível
    nome_usuario = nome
    try:
        usuario = db.execute(
            text("SELECT nome FROM usuarios WHERE email = :email"),
            {"email": email},
        ).fetchone()
        
        if usuario:
            nome_usuario = usuario.nome
    except Exception as exc:
        # Se banco falhar, usa o nome do token Firebase
        print(f"Aviso: Não foi possível acessar banco de dados. Usando dados do Firebase: {exc}")
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
        "mensagem": "API Mente Ativa conectada ao Firebase!",
        "status": "Online"
    }

# Rota de teste para verificar se a conexão com o banco está ok
@app.get("/test_db")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Conexão com banco de dados bem-sucedida!"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail=f"Falha na conexão com banco: {str(e)}")


@app.get('/firebase/status')
def firebase_status():
    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "sucesso", "project": os.getenv("FIREBASE_PROJECT_ID")}


@app.post("/tests/results")
def salvar_resultado_teste_api(dados: TestResultSchema):
    documento_id = salvar_resultado_teste(dados.model_dump())
    return {"status": "sucesso", "id": documento_id}


@app.post('/links')
def create_link(payload: dict = Body(...)):
    doctor = payload.get('doctorKey')
    patient = payload.get('patientKey')

    if not doctor or not patient:
        raise HTTPException(status_code=400, detail='doctorKey and patientKey are required')

    try:
        with engine.begin() as conn:
            conn.execute(
                text('INSERT INTO vinculos_medicos (doctor_key, patient_key) VALUES (:doctor, :patient) ON CONFLICT DO NOTHING'),
                {'doctor': doctor, 'patient': patient}
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {'status': 'sucesso'}


@app.delete('/links')
def delete_link(payload: dict = Body(...)):
    doctor = payload.get('doctorKey')
    patient = payload.get('patientKey')

    if not doctor or not patient:
        raise HTTPException(status_code=400, detail='doctorKey and patientKey are required')

    try:
        with engine.begin() as conn:
            conn.execute(
                text('DELETE FROM vinculos_medicos WHERE doctor_key = :doctor AND patient_key = :patient'),
                {'doctor': doctor, 'patient': patient}
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {'status': 'sucesso'}


@app.get('/links/doctor/{doctor_key}')
def list_patients_for_doctor(doctor_key: str):
    try:
        with engine.connect() as conn:
            resultados = conn.execute(
                text('SELECT patient_key, created_at FROM vinculos_medicos WHERE doctor_key = :doctor ORDER BY created_at DESC'),
                {'doctor': doctor_key}
            ).fetchall()

            return {'status': 'sucesso', 'patients': [dict(r) for r in resultados]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get('/links/patient/{patient_key}')
def list_doctors_for_patient(patient_key: str):
    try:
        with engine.connect() as conn:
            resultados = conn.execute(
                text('SELECT doctor_key, created_at FROM vinculos_medicos WHERE patient_key = :patient ORDER BY created_at DESC'),
                {'patient': patient_key}
            ).fetchall()

            return {'status': 'sucesso', 'doctors': [dict(r) for r in resultados]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/tests/results")
def listar_resultados_teste_api(userKey: str, request: Request, limit: int = 20): # 1. Adicionei o request aqui
    try:
        # Se a função listar_historico_teste precisar do token, passe o request para ela:
        # resultados = listar_historico_teste(userKey=userKey, limit_count=limit, request=request)
        
        resultados = listar_historico_teste(userKey=userKey, limit_count=limit)
        
        return {"status": "sucesso", "resultados": resultados}
        
    except Exception as exc:
        # 2. Isso vai printar o erro EXATO no seu terminal Python para você ver
        print(f"--- ERRO CRÍTICO NO BACKEND ---")
        import traceback
        traceback.print_exc() 
        print(f"--------------------------------")
        
        # Retorna um erro formatado para o Vue não se perder no CORS
        raise HTTPException(status_code=500, detail=str(exc))


def _get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization") or ""

    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return ""


def _fetch_firestore_doc_by_uid(collection_name: str, uid: str):
    client = get_firestore_client()
    documento = client.collection(collection_name).document(uid).get()
    if documento.exists:
        data = documento.to_dict() or {}
        data["id"] = documento.id
        return data
    return None


@app.post("/doctor-links/link")
def vincular_paciente_medico(payload: LinkPatientSchema, request: Request):
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    doctor_info = verify_firebase_token(token)
    doctor_uid = doctor_info.get("uid")
    if not doctor_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o medico")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    email = payload.patientEmail.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="patientEmail e obrigatorio")

    pacientes = list(
        client.collection("usuarios")
        .where("email", "==", email)
        .limit(1)
        .stream()
    )

    if not pacientes:
        raise HTTPException(status_code=404, detail="Paciente nao encontrado para este e-mail")

    paciente_doc = pacientes[0]
    paciente_data = paciente_doc.to_dict() or {}
    patient_uid = paciente_data.get("uid") or paciente_doc.id

    vinculo_id = f"{doctor_uid}__{patient_uid}"
    documento_vinculo = {
        "doctorUid": doctor_uid,
        "doctorEmail": doctor_info.get("email"),
        "patientUid": patient_uid,
        "patientEmail": paciente_data.get("email") or email,
        "patientName": paciente_data.get("nome") or paciente_data.get("email") or email,
        "createdAtMs": int(__import__("time").time() * 1000),
        "createdAtIso": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }

    client.collection("vinculos_medico_paciente").document(vinculo_id).set(documento_vinculo, merge=True)

    return {
        "status": "sucesso",
        "vinculo": documento_vinculo,
    }


@app.get("/doctor-links/patients")
def listar_pacientes_do_medico(request: Request):
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    doctor_info = verify_firebase_token(token)
    doctor_uid = doctor_info.get("uid")
    if not doctor_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o medico")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    pacientes = []
    query = client.collection("vinculos_medico_paciente").where("doctorUid", "==", doctor_uid)

    for documento in query.stream():
        link = documento.to_dict() or {}
        patient_uid = link.get("patientUid")
        patient_profile = _fetch_firestore_doc_by_uid("usuarios", patient_uid) or {}

        historico = listar_historico_teste(user_key=patient_uid, limit_count=1)
        ultimo_teste = historico[0] if historico else None

        pacientes.append({
            "linkId": documento.id,
            "doctorUid": link.get("doctorUid"),
            "doctorEmail": link.get("doctorEmail"),
            "patientUid": patient_uid,
            "patientEmail": link.get("patientEmail") or patient_profile.get("email"),
            "patientName": link.get("patientName") or patient_profile.get("nome") or link.get("patientEmail"),
            "patientPhoto": patient_profile.get("foto"),
            "linkedAtMs": link.get("createdAtMs"),
            "linkedAtIso": link.get("createdAtIso"),
            "testsCount": len(listar_historico_teste(user_key=patient_uid, limit_count=200)),
            "latestTest": ultimo_teste,
        })

    pacientes.sort(key=lambda item: item.get("linkedAtMs") or 0, reverse=True)

    return {
        "status": "sucesso",
        "patients": pacientes,
    }


@app.get("/doctor-links/patients/{patient_uid}/summary")
def resumir_paciente_para_medico(patient_uid: str, request: Request):
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    doctor_info = verify_firebase_token(token)
    doctor_uid = doctor_info.get("uid")
    if not doctor_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o medico")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    patient_profile = _fetch_firestore_doc_by_uid("usuarios", patient_uid) or {}
    historico = listar_historico_teste(user_key=patient_uid, limit_count=20)
    resumo = gerar_resumo_clinico_paciente(
        patient_profile=patient_profile,
        historico_testes=historico,
    )

    return {
        "status": "sucesso",
        "patientUid": patient_uid,
        "patientName": patient_profile.get("nome") or patient_profile.get("email") or patient_uid,
        "patientEmail": patient_profile.get("email"),
        **resumo,
    }


@app.get("/doctor-links/patients/{patient_uid}/tests")
def listar_testes_do_paciente(patient_uid: str, request: Request):
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    doctor_info = verify_firebase_token(token)
    doctor_uid = doctor_info.get("uid")
    if not doctor_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o medico")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    historico = listar_historico_teste(user_key=patient_uid, limit_count=50)

    return {
        "status": "sucesso",
        "patientUid": patient_uid,
        "tests": historico,
    }