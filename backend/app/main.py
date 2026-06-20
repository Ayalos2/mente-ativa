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

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip("/")

# Lista de origens permitidas baseada na variável de ambiente
origins = [
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Passa a lista aqui
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

class RequestDoctorLinkSchema(BaseModel):
    doctorUid: str

class DiagnosisSchema(BaseModel):
    diagnosis: str

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
        
        resultados = listar_historico_teste(user_key=userKey, limit_count=limit)
        
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
    print(f"👉 TOKEN RECEBIDO NO BACKEND: {token}") # <--- Adicione isso para debugar
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

        # Busca resumo de saúde salvo pelo paciente
        resumo_saude = _fetch_firestore_doc_by_uid("resumos_saude_paciente", patient_uid)

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
            "healthSummary": resumo_saude.get("summary") if resumo_saude else None,
            "healthSummaryGeneratedAt": resumo_saude.get("generatedAtIso") if resumo_saude else None,
            "healthSummarySource": resumo_saude.get("source") if resumo_saude else None,
        })

    pacientes.sort(key=lambda item: item.get("linkedAtMs") or 0, reverse=True)

    return {
        "status": "sucesso",
        "patients": pacientes,
    }


@app.get("/doctor-links/my-doctors")
def listar_medicos_do_paciente(request: Request):
    """Retorna a lista de médicos vinculados ao paciente autenticado."""
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    patient_info = verify_firebase_token(token)
    patient_uid = patient_info.get("uid")
    if not patient_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o paciente")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    medicos = []
    query = client.collection("vinculos_medico_paciente").where("patientUid", "==", patient_uid)

    for documento in query.stream():
        link = documento.to_dict() or {}
        doctor_uid = link.get("doctorUid")

        # Busca dados do médico no Firestore
        doctor_profile = _fetch_firestore_doc_by_uid("usuarios", doctor_uid) or {}

        medicos.append({
            "linkId": documento.id,
            "doctorUid": doctor_uid,
            "doctorEmail": link.get("doctorEmail") or doctor_profile.get("email"),
            "doctorName": link.get("doctorName") or doctor_profile.get("nome") or link.get("doctorEmail"),
            "doctorPhoto": doctor_profile.get("foto"),
            "doctorEspecialidade": doctor_profile.get("especialidade"),
            "doctorInstituicao": doctor_profile.get("instituicao"),
            "doctorCrmcrp": doctor_profile.get("crmcrp"),
            "linkedAtMs": link.get("createdAtMs"),
            "linkedAtIso": link.get("createdAtIso"),
        })

    medicos.sort(key=lambda item: item.get("linkedAtMs") or 0, reverse=True)

    return {
        "status": "sucesso",
        "doctors": medicos,
    }


@app.post("/doctor-links/request")
def solicitar_vinculo_medico(payload: RequestDoctorLinkSchema, request: Request):
    """Paciente solicita vínculo com um médico especialista."""
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    patient_info = verify_firebase_token(token)
    patient_uid = patient_info.get("uid")
    if not patient_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o paciente")

    doctor_uid = payload.doctorUid
    if not doctor_uid:
        raise HTTPException(status_code=400, detail="doctorUid é obrigatorio")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Verifica se o médico existe
    doctor_profile = _fetch_firestore_doc_by_uid("usuarios", doctor_uid)
    if not doctor_profile:
        raise HTTPException(status_code=404, detail="Médico nao encontrado")

    # Verifica se o médico é especialista
    if doctor_profile.get("cargo") != "especialista":
        raise HTTPException(status_code=400, detail="O usuario informado nao é um especialista")

    # Busca dados do paciente
    patient_profile = _fetch_firestore_doc_by_uid("usuarios", patient_uid) or {}

    vinculo_id = f"{doctor_uid}__{patient_uid}"
    now_ms = int(__import__("time").time() * 1000)
    now_iso = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    documento_vinculo = {
        "doctorUid": doctor_uid,
        "doctorEmail": doctor_profile.get("email"),
        "doctorName": doctor_profile.get("nome") or doctor_profile.get("email"),
        "patientUid": patient_uid,
        "patientEmail": patient_info.get("email"),
        "patientName": patient_profile.get("nome") or patient_info.get("email"),
        "createdAtMs": now_ms,
        "createdAtIso": now_iso,
    }

    client.collection("vinculos_medico_paciente").document(vinculo_id).set(documento_vinculo, merge=True)

    return {
        "status": "sucesso",
        "vinculo": documento_vinculo,
    }


@app.post("/doctor-links/patients/{patient_uid}/diagnosis")
def salvar_diagnostico_medico(patient_uid: str, payload: DiagnosisSchema, request: Request):
    """Médico salva o diagnóstico textual do paciente."""
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

    # Verifica vínculo
    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    diagnostico = payload.diagnosis

    if not diagnostico or not diagnostico.strip():
        raise HTTPException(status_code=400, detail="O diagnostico nao pode estar vazio")

    now_ms = int(__import__("time").time() * 1000)
    now_iso = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    documento_diagnostico = {
        "patientUid": patient_uid,
        "diagnosis": diagnostico.strip(),
        "doctorUid": doctor_uid,
        "doctorEmail": doctor_info.get("email"),
        "doctorName": doctor_info.get("name") or doctor_info.get("email"),
        "updatedAtMs": now_ms,
        "updatedAtIso": now_iso,
        "availableToPatient": False,
    }

    client.collection("diagnosticos_medicos").document(patient_uid).set(documento_diagnostico, merge=True)

    return {
        "status": "sucesso",
        "patientUid": patient_uid,
        "diagnosis": diagnostico.strip(),
        "updatedAtIso": now_iso,
    }


@app.get("/doctor-links/patients/{patient_uid}/diagnosis")
def visualizar_diagnostico_medico(patient_uid: str, request: Request):
    """Médico visualiza o diagnóstico salvo de um paciente."""
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

    # Verifica vínculo
    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    diagnostico = _fetch_firestore_doc_by_uid("diagnosticos_medicos", patient_uid)

    if not diagnostico:
        return {
            "status": "sucesso",
            "hasDiagnosis": False,
            "patientUid": patient_uid,
        }

    return {
        "status": "sucesso",
        "hasDiagnosis": True,
        "patientUid": patient_uid,
        "diagnosis": diagnostico.get("diagnosis"),
        "doctorUid": diagnostico.get("doctorUid"),
        "doctorName": diagnostico.get("doctorName"),
        "updatedAtIso": diagnostico.get("updatedAtIso"),
        "availableToPatient": diagnostico.get("availableToPatient", False),
    }


@app.post("/doctor-links/patients/{patient_uid}/publish-summary")
def publicar_resumo_para_paciente(patient_uid: str, request: Request):
    """Médico disponibiliza o resumo LLM e diagnóstico para o paciente visualizar."""
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

    # Verifica vínculo
    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    # Verifica se tem resumo salvo
    resumo = _fetch_firestore_doc_by_uid("resumos_saude_paciente", patient_uid)
    if not resumo:
        raise HTTPException(status_code=400, detail="Nenhum resumo LLM foi gerado para este paciente ainda. Gere o resumo primeiro.")

    now_ms = int(__import__("time").time() * 1000)
    now_iso = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    # Marca resumo como disponível para o paciente
    client.collection("resumos_saude_paciente").document(patient_uid).update({
        "availableToPatient": True,
        "publishedAtMs": now_ms,
        "publishedAtIso": now_iso,
        "publishedByDoctorUid": doctor_uid,
    })

    # Também marca diagnóstico como disponível se existir
    diagnostico = _fetch_firestore_doc_by_uid("diagnosticos_medicos", patient_uid)
    if diagnostico:
        client.collection("diagnosticos_medicos").document(patient_uid).update({
            "availableToPatient": True,
            "publishedAtMs": now_ms,
            "publishedAtIso": now_iso,
        })

    return {
        "status": "sucesso",
        "patientUid": patient_uid,
        "publishedAtIso": now_iso,
        "summaryAvailable": True,
        "diagnosisAvailable": bool(diagnostico),
    }


@app.get("/doctor-links/my-health-summary")
def meu_resumo_saude(request: Request):
    """Paciente visualiza seu proprio resumo de saúde salvo e diagnóstico."""
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token de autenticacao nao informado")

    patient_info = verify_firebase_token(token)
    patient_uid = patient_info.get("uid")
    if not patient_uid:
        raise HTTPException(status_code=401, detail="Nao foi possivel identificar o paciente")

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    patient_profile = _fetch_firestore_doc_by_uid("usuarios", patient_uid) or {}

    # Busca resumo salvo
    resumo_salvo = _fetch_firestore_doc_by_uid("resumos_saude_paciente", patient_uid)

    # Busca diagnóstico médico
    diagnostico = _fetch_firestore_doc_by_uid("diagnosticos_medicos", patient_uid)

    if not resumo_salvo:
        return {
            "status": "sucesso",
            "hasSummary": False,
            "patientUid": patient_uid,
            "patientName": patient_profile.get("nome") or patient_info.get("email"),
        }

    # Verifica se o médico disponibilizou para o paciente
    available_to_patient = resumo_salvo.get("availableToPatient", False)

    if not available_to_patient:
        return {
            "status": "sucesso",
            "hasSummary": False,
            "availableToPatient": False,
            "patientUid": patient_uid,
            "patientName": patient_profile.get("nome") or patient_info.get("email"),
        }

    return {
        "status": "sucesso",
        "hasSummary": True,
        "availableToPatient": True,
        "patientUid": patient_uid,
        "patientName": patient_profile.get("nome") or patient_info.get("email"),
        "summary": resumo_salvo.get("summary"),
        "source": resumo_salvo.get("source"),
        "generatedAtIso": resumo_salvo.get("generatedAtIso"),
        "testsAnalyzed": resumo_salvo.get("testsAnalyzed"),
        "diagnosis": diagnostico.get("diagnosis") if diagnostico and diagnostico.get("availableToPatient") else None,
        "diagnosisDoctorName": diagnostico.get("doctorName") if diagnostico and diagnostico.get("availableToPatient") else None,
    }


@app.post("/doctor-links/patients/{patient_uid}/generate-summary")
def gerar_resumo_llm_paciente(patient_uid: str, request: Request):
    """Médico gera o resumo LLM do paciente e o disponibiliza."""
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

    # Verifica vínculo
    vinculo_id = f"{doctor_uid}__{patient_uid}"
    vinculo = client.collection("vinculos_medico_paciente").document(vinculo_id).get()
    if not vinculo.exists:
        raise HTTPException(status_code=403, detail="Paciente nao vinculado a este medico")

    patient_profile = _fetch_firestore_doc_by_uid("usuarios", patient_uid) or {}
    historico = listar_historico_teste(user_key=patient_uid, limit_count=20)

    if not historico:
        raise HTTPException(status_code=400, detail="O paciente precisa ter pelo menos um teste realizado para gerar o resumo.")

    resumo = gerar_resumo_clinico_paciente(
        patient_profile=patient_profile,
        historico_testes=historico,
    )

    # Salva no Firestore como resumo gerado pelo médico
    documento_resumo = {
        "patientUid": patient_uid,
        "patientName": patient_profile.get("nome") or patient_uid,
        "patientEmail": patient_profile.get("email"),
        "generatedByDoctorUid": doctor_uid,
        "generatedByDoctorEmail": doctor_info.get("email"),
        **resumo,
        "updatedAtMs": int(__import__("time").time() * 1000),
    }

    client.collection("resumos_saude_paciente").document(patient_uid).set(documento_resumo, merge=True)

    return {
        "status": "sucesso",
        "patientUid": patient_uid,
        "generatedByDoctorUid": doctor_uid,
        **resumo,
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