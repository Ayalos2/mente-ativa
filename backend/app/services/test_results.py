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
    # 1. Proteção: Se o user_key for nulo, vazio ou a string "undefined"/"null" enviado pelo front
    if not user_key or user_key in ["undefined", "null", "None"]:
        return []

    try:
        client = get_firestore_client()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    resultados = []
    
    # Executa a query no Firestore
    query = client.collection(COLLECTION_NAME).where("userKey", "==", user_key)

    for documento in query.stream():
        data = documento.to_dict() or {}
        data["id"] = documento.id
        resultados.append(data)

    # Se a lista estiver vazia (usuário novo), retorna imediatamente sem tentar ordenar
    if not resultados:
        return []

    # Helper interno para garantir conversão numérica sem quebrar o lambda
    def para_numero(valor):
        try:
            return int(valor) if valor is not None else 0
        except (ValueError, TypeError):
            return 0

    # 2. Ordenação robusta simulando o toNumber do frontend
    resultados.sort(key=lambda item: para_numero(item.get("createdAtMs")), reverse=True)

    return resultados[:limit_count]