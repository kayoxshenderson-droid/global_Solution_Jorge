from __future__ import annotations

from pathlib import Path
import textwrap
import sys

from PIL import Image, ImageDraw, ImageFont
import pyfiglet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import MissionEngine


ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

FONT_REGULAR = Path(r"C:\Windows\Fonts\consola.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\consolab.ttf")


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT = load_font(FONT_REGULAR, 24)
FONT_SMALL = load_font(FONT_REGULAR, 20)
FONT_TITLE = load_font(FONT_BOLD, 26)
FONT_BANNER = load_font(FONT_BOLD, 26)

BG = "#08111f"
CARD = "#0f1b2d"
CARD_HEADER = "#13243a"
TEXT = "#dce7f7"
MUTED = "#8ea2c2"
CYAN = "#36d7ff"
GREEN = "#72e39f"
YELLOW = "#f2d36b"
RED = "#ff7b7b"
MAGENTA = "#d89bff"
BLUE = "#7ab7ff"


def measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, border: str, lines: list[tuple[str, str]]) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=CARD, outline=border, width=3)
    draw.rounded_rectangle((x, y, x + w, y + 58), radius=24, fill=CARD_HEADER)
    draw.rectangle((x, y + 34, x + w, y + 58), fill=CARD_HEADER)
    draw.text((x + 24, y + 14), title, font=FONT_TITLE, fill=TEXT)
    cursor_y = y + 76
    for line, color in lines:
        draw.text((x + 24, cursor_y), line, font=FONT, fill=color)
        cursor_y += 32


def wrap(prefix: str, value: str, width: int = 68) -> list[tuple[str, str]]:
    parts = textwrap.wrap(value, width=width) or [""]
    result = [(f"{prefix}{parts[0]}", TEXT)]
    pad = " " * len(prefix)
    for part in parts[1:]:
        result.append((f"{pad}{part}", TEXT))
    return result


def banner_text() -> str:
    return pyfiglet.figlet_format("Mission Control AI", font="ansi_shadow")


def render_banner(draw: ImageDraw.ImageDraw, y: int) -> int:
    x = 70
    for line in banner_text().splitlines():
        draw.text((x, y), line, font=FONT_BANNER, fill=CYAN)
        y += 24
    return y + 10


def telemetry_lines(snapshot: dict, decision: dict) -> list[tuple[str, str]]:
    lines = []
    labels = {
        "timestamp_utc": "horario_utc",
        "uplink_latency_ms": "latencia_uplink_ms",
        "throughput_mbps": "vazao_mbps",
        "antenna_health_pct": "saude_antena_pct",
        "beam_alignment_error_deg": "erro_alinhamento_beam_graus",
        "transponder_temp_c": "temperatura_transponder_c",
        "packet_loss_pct": "perda_pacotes_pct",
    }
    for key, value in snapshot.items():
        lines.append((f"{labels.get(key, key):<30}{value}", TEXT))
    lines.append(("", TEXT))
    lines.append((f"Estado atual: {decision['estado_missao']}", GREEN if decision["estado_missao"] == "NOMINAL" else YELLOW if decision["estado_missao"] == "DEGRADADO" else RED))
    lines.append((f"Acoes automaticas: {', '.join(decision['acoes_automaticas'])}", TEXT))
    return lines


def alert_lines(alerts: list) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for alert in alerts:
        color = RED if alert.severity == "ALTO" else YELLOW
        lines.append((f"[{alert.severity}] {alert.title}", color))
        lines.extend(wrap("  ", alert.detail))
        if alert.automated_action:
            lines.extend(wrap("  acao: ", alert.automated_action))
        lines.append(("", TEXT))
    return lines


def response_lines(decision: dict) -> list[tuple[str, str]]:
    lines = [
        (f"Estado da missao: {decision['estado_missao']}", GREEN if decision["estado_missao"] == "NOMINAL" else YELLOW if decision["estado_missao"] == "DEGRADADO" else RED),
        (f"Alertas ALTO: {decision['alertas_alto']} | MEDIO: {decision['alertas_medio']}", TEXT),
        ("", TEXT),
        ("Acoes automaticas:", MAGENTA),
    ]
    lines.extend((f"- {action}", TEXT) for action in decision["acoes_automaticas"])
    return lines


def analysis_lines(snapshot: dict, decision: dict, alerts: list) -> list[tuple[str, str]]:
    if decision["estado_missao"] == "CRITICO":
        summary = "Resumo operacional: telemetria fora do normal, com risco de interrupcao de conectividade em comunidades rurais."
        risks = "Riscos e severidade: latencia alta, perda de pacotes severa e carga termica critica exigem resposta imediata."
        action = "Ação imediata recomendada: reduzir carga nao critica, priorizar trafego essencial e acionar rotina de cooling."
        impact = "Impacto terrestre esperado: aulas remotas, telemedicina e serviços essenciais podem ficar instaveis ate a recuperacao."
    else:
        summary = "Resumo operacional: sistema nominal com monitoramento continuo e margens seguras."
        risks = "Riscos e severidade: nao ha alertas criticos, apenas acompanhamento preventivo."
        action = "Ação imediata recomendada: manter observacao e coletar nova telemetria no proximo ciclo."
        impact = "Impacto terrestre esperado: conectividade estavel para escolas rurais e pequenos negocios."
    lines = []
    lines.extend(wrap("1) ", summary))
    lines.extend(wrap("2) ", risks))
    lines.extend(wrap("3) ", action))
    lines.extend(wrap("4) ", impact))
    return lines


def make_image(name: str, width: int, height: int, body: list[tuple[str, str]], subtitle: str) -> None:
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    cursor_y = 30
    cursor_y = render_banner(draw, cursor_y)
    draw.text((74, cursor_y), "ConnectSat | Interface de monitoramento com IA", font=FONT_SMALL, fill=MUTED)
    draw.text((74, cursor_y + 24), subtitle, font=FONT_SMALL, fill=MUTED)
    draw.line((72, cursor_y + 62, width - 72, cursor_y + 62), fill="#27405f", width=2)
    body_y = cursor_y + 96
    x = 70
    for text, color in body:
        draw.text((x, body_y), text, font=FONT, fill=color)
        body_y += 32
    img.save(ASSETS / name)


def main() -> None:
    engine = MissionEngine()

    normal_snapshot = engine.collect("normal")
    normal_decision = engine.decision_summary()

    img = Image.new("RGB", (1700, 1380), BG)
    draw = ImageDraw.Draw(img)
    cursor_y = render_banner(draw, 30)
    draw.text((74, cursor_y), "ConnectSat | Interface de monitoramento com IA", font=FONT_SMALL, fill=MUTED)
    draw.text((74, cursor_y + 24), "Cenario normal com prompt configurado e telemetria saudavel", font=FONT_SMALL, fill=MUTED)
    draw.line((72, cursor_y + 62, 1628, cursor_y + 62), fill="#27405f", width=2)
    panel(draw, 70, cursor_y + 98, 720, 260, "Status do Motor", CYAN, [
        ("Trilha        ConnectSat", TEXT),
        ("Modelo        gpt-oss:120b", TEXT),
        ("Servidor      https://ollama.com", TEXT),
        ("Cenario       normal", TEXT),
        ("Prompt        pronto", GREEN),
        ("Chave de API  AUSENTE", YELLOW),
    ])
    panel(draw, 820, cursor_y + 98, 810, 260, "Telemetria", GREEN, telemetry_lines(normal_snapshot, normal_decision))
    panel(draw, 70, cursor_y + 392, 1560, 380, "Resposta Automatizada", GREEN, response_lines(normal_decision))
    panel(draw, 70, cursor_y + 798, 1560, 470, "Impacto Terrestre", BLUE, wrap("", normal_decision["impacto_terrestre"], 110))
    img.save(ASSETS / "screenshot_normal.png")

    engine.collect("critico")
    critical_decision = engine.decision_summary()
    critical_alerts = engine.get_alerts()
    critical_snapshot = engine.last_snapshot or {}

    img = Image.new("RGB", (1700, 1760), BG)
    draw = ImageDraw.Draw(img)
    cursor_y = render_banner(draw, 30)
    draw.text((74, cursor_y), "ConnectSat | Cenário crítico com resposta da IA", font=FONT_SMALL, fill=MUTED)
    draw.text((74, cursor_y + 24), "A tela mostra a cadeia telemetria -> alerta -> decisão -> impacto", font=FONT_SMALL, fill=MUTED)
    draw.line((72, cursor_y + 62, 1628, cursor_y + 62), fill="#27405f", width=2)
    panel(draw, 70, cursor_y + 98, 720, 260, "Status do Motor", CYAN, [
        ("Trilha        ConnectSat", TEXT),
        ("Modelo        gpt-oss:120b", TEXT),
        ("Servidor      https://ollama.com", TEXT),
        ("Cenario       critico", TEXT),
        ("Prompt        pronto", GREEN),
        ("Chave de API  AUSENTE", YELLOW),
    ])
    panel(draw, 820, cursor_y + 98, 810, 260, "Telemetria", RED, telemetry_lines(critical_snapshot, critical_decision))
    panel(draw, 70, cursor_y + 392, 1560, 460, "Alertas", RED, alert_lines(critical_alerts))
    panel(draw, 70, cursor_y + 880, 1560, 300, "Resposta Automatizada", MAGENTA, response_lines(critical_decision))
    panel(draw, 70, cursor_y + 1210, 1560, 460, "Analise da IA", CYAN, analysis_lines(critical_snapshot, critical_decision, critical_alerts))
    img.save(ASSETS / "screenshot_critico.png")


if __name__ == "__main__":
    main()
