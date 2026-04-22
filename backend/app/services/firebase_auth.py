import os
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException


def _resolve_service_account_path() -> Path:
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

    if not service_account_path:
        raise HTTPException(
            status_code=500,
            detail='FIREBASE_SERVICE_ACCOUNT_PATH nao configurado no backend',
        )

    candidate_path = Path(service_account_path)

    if not candidate_path.is_absolute():
        candidate_path = Path(__file__).resolve().parents[2] / service_account_path

    return candidate_path


def initialize_firebase_admin() -> None:
    if firebase_admin._apps:
        return

    service_account_path = _resolve_service_account_path()

    if not service_account_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f'Arquivo de credenciais do Firebase nao encontrado: {service_account_path}',
        )

    firebase_admin.initialize_app(credentials.Certificate(str(service_account_path)))


def verify_firebase_token(token: str):
    initialize_firebase_admin()

    try:
        return auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail='Token Firebase invalido') from exc
