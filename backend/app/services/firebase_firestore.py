import json
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore


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
            firebase_credential = credentials.Certificate(service_account_path)
        else:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON ou FIREBASE_SERVICE_ACCOUNT_PATH nao configurado no backend"
            )

        options = {}
        if project_id:
            options["projectId"] = project_id

        firebase_admin.initialize_app(firebase_credential, options if options else None)

    return firestore.client()
