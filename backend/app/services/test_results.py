from datetime import datetime, timezone

from fastapi import HTTPException
from firebase_admin import firestore

from .firebase_firestore import get_firestore_client


COLLECTION_NAME = "historico_testes"


def salvar_resultado_teste(payload: dict):
    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    documento = {
        **payload,
        "createdAtMs": int(datetime.now(timezone.utc).timestamp() * 1000),
        "createdAtIso": datetime.now(timezone.utc).isoformat(),
    }

    documento_ref = client.collection(COLLECTION_NAME).add(documento)
    return documento_ref[1].id


def listar_historico_teste(user_key: str, limit_count: int = 20):
    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    resultados = []
    query = client.collection(COLLECTION_NAME).where("userKey", "==", user_key)

    for documento in query.stream():
        data = documento.to_dict() or {}
        data["id"] = documento.id
        resultados.append(data)

    resultados.sort(key=lambda item: item.get("createdAtMs") or 0, reverse=True)

    return resultados[:limit_count]
