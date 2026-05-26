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

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

if OLLAMA_API_KEY:
    client = Client(
        host=OLLAMA_HOST,
        headers={"Authorization": "Bearer " + OLLAMA_API_KEY},
    )
else:
    client = Client(host=OLLAMA_HOST)


def llm(prompt: str, max_tokens: int = 500, temperature: float = 0.2) -> str:
    """Envia prompt ao modelo configurado no Ollama local/cloud e retorna texto."""
    try:
        return client.chat(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": max_tokens, "temperature": temperature},
            stream=False,
        )["message"]["content"].strip()
    except Exception as e:
        return f"Erro ao consultar IA: {e}"


class MissionEngine:
    def __init__(self) -> None:
        self.system_prompt = Path("prompts/system_prompt.md").read_text(encoding="utf-8")
        self.last_snapshot: dict | None = None
        self.last_alerts: list[Alert] = []
        self.last_scenario = "aleatorio"

    def status(self) -> dict:
        return {
            "host": OLLAMA_HOST,
            "has_api_key": bool(OLLAMA_API_KEY),
            "model": DEFAULT_MODEL,
            "track": "ConnectSat",
            "scenario": self.last_scenario,
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

    def analyze(self, user_question: str = "Como esta a missao?") -> str:
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
        return llm(prompt)
