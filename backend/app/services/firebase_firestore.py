import json
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore


BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Carrega variaveis do .env para garantir que estejam disponiveis
ENV_FILE = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)


@lru_cache(maxsize=1)
def get_firestore_client():
    if not firebase_admin._apps:
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        project_id = os.getenv("FIREBASE_PROJECT_ID")

        if service_account_json:
            service_account_info = json.loads(service_account_json)
            firebase_credential = credentials.Certificate(service_account_info)
        elif service_account_path:
            resolved_path = Path(service_account_path)

            if not resolved_path.is_absolute():
                resolved_path = BACKEND_ROOT / resolved_path

            if not resolved_path.exists():
                raise RuntimeError(
                    f"FIREBASE_SERVICE_ACCOUNT_PATH configurado, mas o arquivo nao foi encontrado: {resolved_path}.\n"
                    "Baixe a chave do Service Account no Firebase Console e coloque o arquivo nesse caminho, ou use FIREBASE_SERVICE_ACCOUNT_JSON."
                )

            firebase_credential = credentials.Certificate(str(resolved_path))
        else:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON ou FIREBASE_SERVICE_ACCOUNT_PATH nao configurado no backend"
            )

        options = {}
        if project_id:
            options["projectId"] = project_id

        firebase_admin.initialize_app(firebase_credential, options if options else None)

    return firestore.client()
