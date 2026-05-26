from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from datetime import datetime, UTC


@dataclass
class TelemetrySnapshot:
    timestamp_utc: str
    uplink_latency_ms: float
    throughput_mbps: float
    antenna_health_pct: float
    beam_alignment_error_deg: float
    transponder_temp_c: float
    packet_loss_pct: float

    def to_dict(self) -> dict:
        return asdict(self)


SCENARIOS: dict[str, dict[str, float]] = {
    "normal": {
        "uplink_latency_ms": 48.0,
        "throughput_mbps": 180.0,
        "antenna_health_pct": 95.0,
        "beam_alignment_error_deg": 0.12,
        "transponder_temp_c": 56.0,
        "packet_loss_pct": 0.8,
    },
    "latencia": {
        "uplink_latency_ms": 192.0,
        "throughput_mbps": 70.0,
        "antenna_health_pct": 90.0,
        "beam_alignment_error_deg": 0.78,
        "transponder_temp_c": 67.0,
        "packet_loss_pct": 3.5,
    },
    "critico": {
        "uplink_latency_ms": 210.0,
        "throughput_mbps": 22.0,
        "antenna_health_pct": 68.0,
        "beam_alignment_error_deg": 1.55,
        "transponder_temp_c": 89.0,
        "packet_loss_pct": 11.2,
    },
    "apagao": {
        "uplink_latency_ms": 235.0,
        "throughput_mbps": 12.0,
        "antenna_health_pct": 66.0,
        "beam_alignment_error_deg": 1.72,
        "transponder_temp_c": 92.0,
        "packet_loss_pct": 13.6,
    },
}


def generate_connectsat_snapshot() -> TelemetrySnapshot:
    now = datetime.now(UTC).isoformat(timespec="seconds")
    return TelemetrySnapshot(
        timestamp_utc=now,
        uplink_latency_ms=round(random.uniform(18, 220), 2),
        throughput_mbps=round(random.uniform(15, 250), 2),
        antenna_health_pct=round(random.uniform(65, 100), 2),
        beam_alignment_error_deg=round(random.uniform(0.02, 1.9), 3),
        transponder_temp_c=round(random.uniform(35, 95), 2),
        packet_loss_pct=round(random.uniform(0.0, 14.0), 2),
    )


def list_scenarios() -> list[str]:
    return sorted(SCENARIOS.keys())


def generate_snapshot_for_scenario(name: str) -> TelemetrySnapshot:
    scenario = SCENARIOS.get(name.lower())
    if not scenario:
        raise ValueError(f"Cenario invalido: {name}")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    return TelemetrySnapshot(timestamp_utc=now, **scenario)
