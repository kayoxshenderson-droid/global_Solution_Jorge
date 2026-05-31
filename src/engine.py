from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client

from src.alertas import Alert, automated_actions, evaluate_alerts, mission_state
from src.telemetria import (
    generate_connectsat_snapshot,
    generate_snapshot_for_scenario,
    list_scenarios,
)

load_dotenv()

CLOUD_HOST = "https://ollama.com"
LOCAL_HOST = os.environ.get("OLLAMA_LOCAL_HOST", "http://localhost:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
PREFERRED_CLOUD_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b")
PREFERRED_LOCAL_MODEL = os.environ.get("OLLAMA_LOCAL_MODEL", "").strip() or "llama3.2"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "system_prompt.md"
USE_CLOUD = bool(OLLAMA_API_KEY)
OLLAMA_HOST = (
    os.environ.get("OLLAMA_HOST", CLOUD_HOST) if USE_CLOUD else os.environ.get("OLLAMA_LOCAL_HOST", LOCAL_HOST)
)

if OLLAMA_API_KEY:
    client = Client(
        host=OLLAMA_HOST,
        headers={"Authorization": "Bearer " + OLLAMA_API_KEY},
    )
else:
    client = Client(host=OLLAMA_HOST)


def _available_local_models() -> list[tuple[str, int]]:
    try:
        response = client.list()
    except Exception:
        return []

    models: list[tuple[str, int]] = []
    for item in getattr(response, "models", []) or []:
        model_name = getattr(item, "model", "")
        if model_name and not model_name.endswith("-cloud"):
            models.append((model_name, int(getattr(item, "size", 0) or 0)))
    return models


def _resolve_model() -> str:
    if USE_CLOUD:
        return PREFERRED_CLOUD_MODEL

    available_models = _available_local_models()
    available_names = [name for name, _size in available_models]
    if PREFERRED_LOCAL_MODEL in available_names:
        return PREFERRED_LOCAL_MODEL
    if available_models:
        return min(available_models, key=lambda item: item[1])[0]
    return PREFERRED_LOCAL_MODEL


def llm(prompt: str, max_tokens: int = 500, temperature: float = 0.2) -> str:
    """Envia prompt ao modelo configurado no Ollama local/cloud e retorna texto."""
    model = _resolve_model()
    try:
        return client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )["message"]["content"].strip()
    except Exception as e:
        if USE_CLOUD:
            return (
                "Nao foi possivel consultar a Ollama Cloud. "
                "Verifique a OLLAMA_API_KEY ou execute `ollama signin` na sua instalação local."
            )
        available_models = _available_local_models()
        available_names = [name for name, _size in available_models]
        if available_names:
            return (
                "Nao foi possivel consultar o Ollama local. "
                f"Erro: {e}. "
                f"Modelo tentado: `{model}`. "
                f"Modelos locais encontrados: {', '.join(available_names)}."
            )
        return (
            "Nao foi possivel consultar o Ollama local. "
            f"Erro: {e}. "
            f"Garanta que o Ollama esteja rodando em {OLLAMA_HOST} e que um modelo local esteja instalado, "
            "por exemplo com `ollama pull gpt-oss:20b`."
        )


def _load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return (
        "Você é a Central de Missao com IA da trilha ConnectSat.\n"
        "Analise a telemetria, destaque riscos e explique o impacto terrestre."
    )


class MissionEngine:
    def __init__(self) -> None:
        self.system_prompt = _load_system_prompt()
        self.last_snapshot: dict | None = None
        self.last_alerts: list[Alert] = []
        self.last_scenario = "aleatorio"

    def status(self) -> dict:
        return {
            "host": OLLAMA_HOST,
            "has_api_key": bool(OLLAMA_API_KEY),
            "model": _resolve_model(),
            "mode": "cloud" if USE_CLOUD else "local",
            "track": "ConnectSat",
            "scenario": self.last_scenario,
            "prompt_ready": bool(self.system_prompt),
        }

    def collect(self, scenario: str | None = None) -> dict:
        if scenario:
            snapshot = generate_snapshot_for_scenario(scenario).to_dict()
            self.last_scenario = scenario
        else:
            snapshot = generate_connectsat_snapshot().to_dict()
            self.last_scenario = "aleatorio"
        self.last_snapshot = snapshot
        self.last_alerts = evaluate_alerts(snapshot)
        return snapshot

    def get_alerts(self) -> list[Alert]:
        return self.last_alerts

    def available_scenarios(self) -> list[str]:
        return list_scenarios()

    def decision_summary(self) -> dict:
        state = mission_state(self.last_alerts)
        alto_count = sum(1 for a in self.last_alerts if a.severity == "ALTO")
        medio_count = sum(1 for a in self.last_alerts if a.severity == "MEDIO")
        impact = {
            "CRITICO": "Risco alto de interrupcao para escolas rurais e telemedicina.",
            "DEGRADADO": "Servico pode oscilar e afetar qualidade de aulas remotas.",
            "NOMINAL": "Conectividade estavel para operacao regular nas comunidades.",
        }[state]
        return {
            "estado_missao": state,
            "alertas_alto": alto_count,
            "alertas_medio": medio_count,
            "acoes_automaticas": automated_actions(self.last_alerts),
            "impacto_terrestre": impact,
        }

    def analyze(
        self,
        user_question: str = "Como esta a missao?",
        llm_runner=llm,
    ) -> str:
        if not self.last_snapshot:
            self.collect()

        telemetry_json = json.dumps(self.last_snapshot, ensure_ascii=False, indent=2)
        alerts_compact = [
            {
                "severity": a.severity,
                "title": a.title,
                "detail": a.detail,
                "automated_action": a.automated_action,
            }
            for a in self.last_alerts
        ]
        alerts_json = json.dumps(alerts_compact, ensure_ascii=False, indent=2)
        decision_json = json.dumps(self.decision_summary(), ensure_ascii=False, indent=2)

        prompt = f"""{self.system_prompt}

Pergunta do operador:
{user_question}

Telemetria atual (JSON):
{telemetry_json}

Alertas de regra Python (JSON):
{alerts_json}

Resumo de decisao automatica (JSON):
{decision_json}
"""
        return llm_runner(prompt)
