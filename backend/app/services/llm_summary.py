import json
import os
import re
from datetime import datetime, timezone

import requests


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _to_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if number != number:
        return 0.0

    return number


def _format_metric_list(values):
    cleaned = [item for item in values if item]
    return cleaned or ["Sem destaques relevantes."]


def _pick_recent_tests(historico_testes, limit=8):
    ordenado = sorted(historico_testes or [], key=lambda item: item.get("createdAtMs") or 0, reverse=True)
    recortes = []

    for teste in ordenado[:limit]:
        summary = teste.get("summary") or {}
        recortes.append(
            {
                "testId": teste.get("testId"),
                "testName": teste.get("testName"),
                "testType": teste.get("testType"),
                "createdAtIso": teste.get("createdAtIso"),
                "createdAtMs": teste.get("createdAtMs"),
                "summary": {
                    "accuracyPercent": summary.get("accuracyPercent"),
                    "totalCorrect": summary.get("totalCorrect"),
                    "correctResponses": summary.get("correctResponses"),
                    "incorrectResponses": summary.get("incorrectResponses"),
                    "averageLatencyMs": summary.get("averageLatencyMs"),
                    "completionTimeMs": summary.get("completionTimeMs"),
                    "errorCount": summary.get("errorCount"),
                    "totalIntrusions": summary.get("totalIntrusions"),
                    "totalPerseverations": summary.get("totalPerseverations"),
                },
            }
        )

    return recortes


def _compute_statistics(historico_testes):
    tests = historico_testes or []
    summary_items = [item.get("summary") or {} for item in tests]

    accuracy_values = [
        _to_number(item.get("accuracyPercent"))
        for item in summary_items
        if item.get("accuracyPercent") is not None
    ]
    latency_values = [
        _to_number(item.get("averageLatencyMs"))
        for item in summary_items
        if item.get("averageLatencyMs") is not None
    ]
    completion_values = [
        _to_number(item.get("completionTimeMs"))
        for item in summary_items
        if item.get("completionTimeMs") is not None
    ]
    error_values = [
        _to_number(item.get("errorCount"))
        for item in summary_items
        if item.get("errorCount") is not None
    ]

    def _avg(values):
        return round(sum(values) / len(values), 2) if values else None

    def _max(values):
        return round(max(values), 2) if values else None

    def _min(values):
        return round(min(values), 2) if values else None

    tests_by_type = {}
    for item in tests:
        test_type = item.get("testType") or "desconhecido"
        tests_by_type[test_type] = tests_by_type.get(test_type, 0) + 1

    latest = tests[0] if tests else {}

    return {
        "testsCount": len(tests),
        "testsByType": tests_by_type,
        "latestTest": {
            "testId": latest.get("testId"),
            "testName": latest.get("testName"),
            "testType": latest.get("testType"),
            "createdAtIso": latest.get("createdAtIso"),
            "summary": latest.get("summary") or {},
        },
        "averageAccuracyPercent": _avg(accuracy_values),
        "averageLatencyMs": _avg(latency_values),
        "averageCompletionTimeMs": _avg(completion_values),
        "averageErrorCount": _avg(error_values),
        "maxAccuracyPercent": _max(accuracy_values),
        "minAccuracyPercent": _min(accuracy_values),
    }


def _fallback_summary(patient_profile, historico_testes):
    statistics = _compute_statistics(historico_testes)
    latest_test = statistics.get("latestTest") or {}
    latest_summary = latest_test.get("summary") or {}

    trends = []
    if statistics["testsCount"]:
        trends.append(
            f"Foram registrados {statistics['testsCount']} teste(s) no histórico, cobrindo {len(statistics['testsByType'])} tipo(s) diferentes."
        )

    if statistics.get("averageAccuracyPercent") is not None:
        trends.append(f"A precisão média observada foi de {round(statistics['averageAccuracyPercent'])}%.")

    if statistics.get("averageLatencyMs") is not None:
        trends.append(f"A latência média ficou em torno de {round(statistics['averageLatencyMs'])} ms.")

    if statistics.get("averageErrorCount") is not None and statistics["averageErrorCount"] > 0:
        trends.append(f"A média de erros por sessão foi {round(statistics['averageErrorCount'], 1)}.")

    alerts = []
    latest_accuracy = _to_number(latest_summary.get("accuracyPercent"))
    latest_errors = _to_number(latest_summary.get("errorCount"))
    latest_latency = _to_number(latest_summary.get("averageLatencyMs"))

    if latest_accuracy and latest_accuracy < 40:
        alerts.append("O teste mais recente indica desempenho abaixo do esperado em precisão.")
    if latest_errors >= 6:
        alerts.append("O teste mais recente apresentou um número elevado de erros.")
    if latest_latency > 3000:
        alerts.append("O teste mais recente mostrou latência elevada nas respostas.")

    if not alerts:
        alerts.append("Nao ha alertas objetivos relevantes no conjunto analisado.")

    recommendations = []
    if latest_accuracy and latest_accuracy < 40:
        recommendations.append("Rever memoria, atencao e qualidade do sono antes da nova avaliacao.")
    if latest_errors >= 6 or latest_latency > 3000:
        recommendations.append("Considerar reavaliacao em curto prazo e correlacionar com sintomas clinicos.")
    if not recommendations:
        recommendations.append("Manter acompanhamento longitudinal e comparar com as proximas sessoes.")

    overview = (
        f"Paciente {patient_profile.get('nome') or patient_profile.get('email') or 'sem identificacao'} com {statistics['testsCount']} teste(s) registrados. "
        f"O ultimo teste foi {latest_test.get('testName') or latest_test.get('testType') or 'desconhecido'}."
    )

    if latest_summary:
        overview += " Os dados da ultima sessao foram usados para destacar possiveis pontos de monitoramento."

    return {
        "provider": "local",
        "model": None,
        "source": "fallback",
        "generatedAtIso": datetime.now(timezone.utc).isoformat(),
        "testsAnalyzed": statistics["testsCount"],
        "summary": {
            "title": "Resumo clinico baseado nos testes",
            "overview": overview,
            "confidence": "media",
            "trends": _format_metric_list(trends),
            "alerts": _format_metric_list(alerts),
            "recommendations": _format_metric_list(recommendations),
            "disclaimer": "Resumo automatizado de apoio ao medico. Nao substitui avaliacao clinica.",
        },
    }


def _build_prompt(patient_profile, historico_testes):
    payload = {
        "patient": {
            "name": patient_profile.get("nome"),
            "email": patient_profile.get("email"),
            "gender": patient_profile.get("genero"),
            "age": patient_profile.get("idade"),
        },
        "statistics": _compute_statistics(historico_testes),
        "recentTests": _pick_recent_tests(historico_testes),
    }

    return (
        "Voce e um assistente clinico para apoio ao medico. "
        "Use somente os dados fornecidos abaixo, sem inventar diagnosticos. "
        "Nao substitua a avaliacao profissional e evite linguagem alarmista. "
        "Responda APENAS com JSON valido e com estas chaves: "
        "title, overview, confidence, trends, alerts, recommendations, disclaimer. "
        "Cada uma das listas deve conter apenas strings curtas. "
        "Se faltarem dados, explique isso de forma conservadora. "
        f"Dados do paciente: {json.dumps(payload, ensure_ascii=True)}"
    )


def _extract_json_text(raw_text):
    if not raw_text:
        return None

    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None

    return None


def _extract_gemini_text(response_json):
    candidates = response_json.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            text = part.get("text")
            if text:
                return text

    return response_json.get("text") or ""


def _call_gemini(patient_profile, historico_testes):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    prompt = _build_prompt(patient_profile, historico_testes)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "maxOutputTokens": 900,
            "responseMimeType": "application/json",
        },
    }

    response = requests.post(url, json=payload, timeout=45)
    response.raise_for_status()
    response_json = response.json()
    text = _extract_gemini_text(response_json)
    data = _extract_json_text(text)

    if not data:
        raise ValueError("A resposta do modelo nao continha JSON valido")

    return {
        "provider": "gemini",
        "model": model,
        "source": "llm",
        "generatedAtIso": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "title": data.get("title") or "Resumo clinico gerado por IA",
            "overview": data.get("overview") or "Sem resumo textual retornado pelo modelo.",
            "confidence": data.get("confidence") or "media",
            "trends": _format_metric_list(data.get("trends") or []),
            "alerts": _format_metric_list(data.get("alerts") or []),
            "recommendations": _format_metric_list(data.get("recommendations") or []),
            "disclaimer": data.get("disclaimer") or "Resumo automatizado de apoio ao medico.",
        },
        "testsAnalyzed": len(historico_testes or []),
    }


def gerar_resumo_clinico_paciente(patient_profile, historico_testes):
    try:
        resumo_llm = _call_gemini(patient_profile or {}, historico_testes or [])
        if resumo_llm:
            return resumo_llm
    except Exception as exc:
        fallback = _fallback_summary(patient_profile or {}, historico_testes or [])
        fallback["provider_error"] = str(exc)
        return fallback

    return _fallback_summary(patient_profile or {}, historico_testes or [])