import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from fastapi import HTTPException

# Carrega variaveis do .env para garantir que estejam disponiveis
BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)


def verify_firebase_token(token: str):
    """Verifica token Firebase ID usando a API REST do Google"""
    api_key = os.getenv('FIREBASE_API_KEY')
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail='FIREBASE_API_KEY nao configurado no backend',
        )
    
    # URL da API REST do Google para verificar tokens
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
    
    try:
        # Usa lookup com idToken para obter informações do usuário
        payload = {"idToken": token}
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code != 200:
            data = response.json()
            error_detail = data.get('error', {}).get('message', 'Token invalido')
            print(f"Erro Firebase API: {error_detail}")
            raise HTTPException(status_code=401, detail=f'Token Firebase invalido: {error_detail}')
        
        data = response.json()
        
        # Retorna um dicionário compatível com verify_id_token
        user_info = data.get('users', [{}])[0]
        return {
            'email': user_info.get('email'),
            'name': user_info.get('displayName'),
            'uid': user_info.get('localId'),
            'email_verified': user_info.get('emailVerified', False),
        }
    
    except requests.exceptions.RequestException as exc:
        error_msg = str(exc)
        print(f"Erro ao validar token Firebase: {error_msg}")
        raise HTTPException(status_code=401, detail=f'Token Firebase invalido: {error_msg}') from exc
