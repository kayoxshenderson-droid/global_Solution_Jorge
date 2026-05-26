from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.engine import MissionEngine


class MissionCLI:
    def __init__(self) -> None:
        self.console = Console()
        self.engine = MissionEngine()

    def _banner(self) -> None:
        banner = """
  __  __ _         _               ____            _             _    _   ___
 |  \\/  (_)___ ___(_) ___  _ __   / ___|___  _ __ | |_ _ __ ___ | |  / \\ |_ _|
 | |\\/| | / __/ __| |/ _ \\| '_ \\ | |   / _ \\| '_ \\| __| '__/ _ \\| | / _ \\ | |
 | |  | | \\__ \\__ \\ | (_) | | | || |__| (_) | | | | |_| | | (_) | |/ ___ \\| |
 |_|  |_|_|___/___/_|\\___/|_| |_| \\____\\___/|_| |_|\\__|_|  \\___/|_/_/   \\_\\___|
"""
        self.console.print(f"[cyan]{banner}[/cyan]")

    def _help(self) -> None:
        self.console.print(
            Panel.fit(
                "Comandos: [bold]ajuda[/bold], [bold]status[/bold], [bold]telemetria[/bold], "
                "[bold]alertas[/bold], [bold]cenario <nome>[/bold], [bold]resposta[/bold], "
                "[bold]impacto[/bold], [bold]analisar <pergunta>[/bold], [bold]sair[/bold]\n"
                "Atalhos: [bold]/help[/bold], [bold]/status[/bold], [bold]/exit[/bold]",
                title="Central da Missao",
            )
        )

    def _print_status(self) -> None:
        status = self.engine.status()
        color = "green" if status["has_api_key"] else "yellow"
        txt = (
            f"Trilha: {status['track']}\n"
            f"Modelo: {status['model']}\n"
            f"Servidor: {status['host']}\n"
            f"Cenario: {status['scenario']}\n"
            f"Chave de API: {'OK' if status['has_api_key'] else 'AUSENTE'}"
        )
        self.console.print(Panel(txt, title="Status do Motor", border_style=color))

    def _print_telemetry(self) -> None:
        snapshot = self.engine.collect()
        table = Table(title="Telemetria Atual")
        table.add_column("Parametro")
        table.add_column("Valor", justify="right")
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
            table.add_row(labels.get(key, key), str(value))
        self.console.print(table)

    def _print_alerts(self) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        alerts = self.engine.get_alerts()
        if not alerts:
            self.console.print(Panel("Sem alertas no momento.", border_style="green"))
            return
        rows = [
            {
                "severidade": a.severity,
                "titulo": a.title,
                "detalhe": a.detail,
                "acao": a.automated_action or "-",
            }
            for a in alerts
        ]
        self.console.print(
            Panel(json.dumps(rows, ensure_ascii=False, indent=2), title="Alertas", border_style="red")
        )

    def _set_scenario(self, scenario_name: str) -> None:
        if not scenario_name:
            valid = ", ".join(self.engine.available_scenarios())
            self.console.print(Panel(f"Informe um cenario: {valid}", border_style="yellow"))
            return
        try:
            self.engine.collect(scenario_name)
            self.console.print(Panel(f"Cenario aplicado: {scenario_name}", border_style="cyan"))
        except ValueError:
            valid = ", ".join(self.engine.available_scenarios())
            self.console.print(Panel(f"Cenario invalido. Opcoes: {valid}", border_style="red"))

    def _print_response(self) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        decision = self.engine.decision_summary()
        lines = [
            f"Estado da missao: {decision['estado_missao']}",
            f"Alertas ALTO: {decision['alertas_alto']} | MEDIO: {decision['alertas_medio']}",
            "",
            "Acoes automaticas:",
        ]
        lines.extend(f"- {action}" for action in decision["acoes_automaticas"])
        self.console.print(Panel("\n".join(lines), title="Resposta Automatizada", border_style="magenta"))

    def _print_impact(self) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        decision = self.engine.decision_summary()
        self.console.print(Panel(decision["impacto_terrestre"], title="Impacto Terrestre", border_style="blue"))

    def _analyze(self, question: str) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        with self.console.status("[bold cyan]Consultando IA...[/bold cyan]"):
            answer = self.engine.analyze(question or "Como esta a missao?")
        self.console.print(Panel(answer, title="Analise da IA", border_style="cyan"))

    def run(self) -> None:
        self._banner()
        self._help()
        self._print_status()
        while True:
            cmd = self.console.input("\n[bold cyan]❯[/bold cyan] ").strip()
            if not cmd:
                continue
            if cmd in {"sair", "exit", "/exit"}:
                self.console.print("[green]Encerrando Central da Missao.[/green]")
                break
            if cmd in {"ajuda", "help", "/help"}:
                self._help()
                continue
            if cmd in {"status", "/status"}:
                self._print_status()
                continue
            if cmd in {"telemetria", "telemetry"}:
                self._print_telemetry()
                continue
            if cmd in {"alertas", "alerts"}:
                self._print_alerts()
                continue
            if cmd in {"resposta", "response"}:
                self._print_response()
                continue
            if cmd in {"impacto", "impact"}:
                self._print_impact()
                continue
            if cmd.startswith("cenario ") or cmd == "cenario" or cmd.startswith("scenario "):
                prefix = "cenario" if cmd.startswith("cenario") else "scenario"
                scenario_name = cmd.replace(prefix, "", 1).strip()
                self._set_scenario(scenario_name)
                continue
            if cmd.startswith("analisar ") or cmd == "analisar" or cmd.startswith("analyze "):
                prefix = "analisar" if cmd.startswith("analisar") else "analyze"
                question = cmd.replace(prefix, "", 1).strip()
                self._analyze(question)
                continue
            self.console.print("[yellow]Comando invalido. Digite 'ajuda'.[/yellow]")
