from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Alert:
    severity: str
    title: str
    detail: str
    automated_action: str | None = None


def evaluate_alerts(telemetry: dict) -> list[Alert]:
    alerts: list[Alert] = []

    if telemetry["uplink_latency_ms"] > 180:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Latencia de uplink elevada",
                detail=f"Latencia em {telemetry['uplink_latency_ms']} ms (limite 180 ms).",
                automated_action="Rebalancear beam e reduzir taxa de modulação por 60s.",
            )
        )
    elif telemetry["uplink_latency_ms"] > 130:
        alerts.append(
            Alert(
                severity="MEDIO",
                title="Latencia de uplink em observacao",
                detail=f"Latencia em {telemetry['uplink_latency_ms']} ms.",
            )
        )

    if telemetry["throughput_mbps"] < 35:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Throughput critico",
                detail=f"Vazao em {telemetry['throughput_mbps']} Mbps (minimo 35 Mbps).",
                automated_action="Priorizar trafego essencial (telemedicina/escolas) e rerotear clientes.",
            )
        )
    elif telemetry["throughput_mbps"] < 60:
        alerts.append(
            Alert(
                severity="MEDIO",
                title="Throughput degradado",
                detail=f"Vazao em {telemetry['throughput_mbps']} Mbps.",
            )
        )

    if telemetry["antenna_health_pct"] < 72:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Saude da antena abaixo do minimo",
                detail=f"Saude em {telemetry['antenna_health_pct']}%.",
                automated_action="Agendar janela de manutencao e ativar compensacao por satelite vizinho.",
            )
        )

    if telemetry["beam_alignment_error_deg"] > 1.3:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Erro de alinhamento de beam",
                detail=f"Erro angular de {telemetry['beam_alignment_error_deg']} graus.",
                automated_action="Executar realinhamento automatico do feixe e recalibrar rastreamento.",
            )
        )

    if telemetry["transponder_temp_c"] > 85:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Carga termica critica",
                detail=f"Transponder em {telemetry['transponder_temp_c']} C.",
                automated_action="Acionar modo de cooling e reduzir carga nao critica.",
            )
        )
    elif telemetry["transponder_temp_c"] > 75:
        alerts.append(
            Alert(
                severity="MEDIO",
                title="Carga termica elevada",
                detail=f"Transponder em {telemetry['transponder_temp_c']} C.",
            )
        )

    if telemetry["packet_loss_pct"] > 8:
        alerts.append(
            Alert(
                severity="ALTO",
                title="Perda de pacotes severa",
                detail=f"Packet loss em {telemetry['packet_loss_pct']}% (limite 8%).",
                automated_action="Trocar codificacao de canal e priorizar sessoes de emergencia.",
            )
        )
    elif telemetry["packet_loss_pct"] > 4:
        alerts.append(
            Alert(
                severity="MEDIO",
                title="Perda de pacotes moderada",
                detail=f"Packet loss em {telemetry['packet_loss_pct']}%.",
            )
        )

    return alerts


def mission_state(alerts: list[Alert]) -> str:
    alto_count = sum(1 for a in alerts if a.severity == "ALTO")
    medio_count = sum(1 for a in alerts if a.severity == "MEDIO")
    if alto_count >= 2:
        return "CRITICO"
    if alto_count == 1 or medio_count >= 2:
        return "DEGRADADO"
    return "NOMINAL"


def automated_actions(alerts: list[Alert]) -> list[str]:
    actions: list[str] = []
    for alert in alerts:
        if alert.automated_action and alert.automated_action not in actions:
            actions.append(alert.automated_action)
    if actions:
        return actions[:3]
    return ["Manter monitoramento continuo com coleta a cada minuto."]
