from __future__ import annotations

import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from banner_ascii import render_banner
from src.engine import MissionEngine


class MissionCLI:
    def __init__(self) -> None:
        self.console = Console()
        self.engine = MissionEngine()
        self._interactive = sys.stdin.isatty() and sys.stdout.isatty()
        self.session: PromptSession | None = None

    def _get_session(self) -> PromptSession:
        if self.session is None:
            history_dir = Path.home() / ".mission_control_ai"
            history_dir.mkdir(parents=True, exist_ok=True)
            self.session = PromptSession(
                history=FileHistory(str(history_dir / "history.txt")),
                auto_suggest=AutoSuggestFromHistory(),
            )
        return self.session

    def _help(self) -> None:
        commands = Table.grid(padding=(0, 2))
        commands.add_column(style="cyan", no_wrap=True)
        commands.add_column(style="white")
        commands.add_row("ajuda", "Mostra esta ajuda.")
        commands.add_row("status", "Exibe host, modelo e estado atual.")
        commands.add_row("telemetria", "Gera uma amostra nova de telemetria.")
        commands.add_row("alertas", "Lista os alertas calculados em Python.")
        commands.add_row("cenario <nome>", "Aplica normal, latencia, critico ou apagao.")
        commands.add_row("resposta", "Mostra a decisão automatizada.")
        commands.add_row("impacto", "Explica o efeito terrestre esperado.")
        commands.add_row("analisar <pergunta>", "Consulta a IA com o contexto atual.")
        commands.add_row("sair", "Encerra a sessão.")
        self.console.print(
            Panel.fit(
                commands,
                title="Central da Missao",
                subtitle="Use as setas do prompt para recuperar comandos anteriores",
                border_style="cyan",
            )
        )

    def _print_status(self) -> None:
        status = self.engine.status()
        border = "green" if status["has_api_key"] else "yellow"
        state = "pronto" if status["prompt_ready"] else "prompt ausente"
        connection = "CLOUD ATIVO" if status["mode"] == "cloud" else "LOCAL ATIVO"
        connection_style = "green" if status["mode"] == "cloud" else "cyan"
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column(style="white")
        table.add_row("Conexao", f"[{connection_style}]{connection}[/{connection_style}]")
        table.add_row("Trilha", status["track"])
        table.add_row("Modo", status["mode"])
        table.add_row("Modelo", status["model"])
        table.add_row("Servidor", status["host"])
        table.add_row("Cenario", status["scenario"])
        table.add_row("Prompt", state)
        table.add_row("Chave de API", "OK" if status["has_api_key"] else "AUSENTE")
        self.console.print(Panel(table, title="Status do Motor", border_style=border))

    def _mission_state_style(self, state: str) -> str:
        return {
            "CRITICO": "red",
            "DEGRADADO": "yellow",
            "NOMINAL": "green",
        }.get(state, "cyan")

    def _print_telemetry(self) -> None:
        snapshot = self.engine.collect()
        decision = self.engine.decision_summary()
        table = Table(title="Telemetria Atual", box=None, show_lines=False)
        table.add_column("Parametro", style="cyan")
        table.add_column("Valor", justify="right", style="white")
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
        footer = Text()
        footer.append("Estado atual: ", style="bold")
        footer.append(decision["estado_missao"], style=f"bold {self._mission_state_style(decision['estado_missao'])}")
        footer.append("\nAcoes automaticas: ", style="bold")
        footer.append(", ".join(decision["acoes_automaticas"]))
        self.console.print(
            Panel(
                table,
                title="Telemetria",
                subtitle=footer,
                border_style=self._mission_state_style(decision["estado_missao"]),
            )
        )

    def _print_alerts(self) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        alerts = self.engine.get_alerts()
        if not alerts:
            self.console.print(Panel("Sem alertas no momento.", border_style="green"))
            return
        table = Table(title="Alertas", box=None)
        table.add_column("Severidade", style="cyan", no_wrap=True)
        table.add_column("Titulo", style="white")
        table.add_column("Detalhe", style="white")
        table.add_column("Acao automatica", style="magenta")
        for alert in alerts:
            table.add_row(
                alert.severity,
                alert.title,
                alert.detail,
                alert.automated_action or "-",
            )
        self.console.print(Panel(table, border_style="red"))

    def _set_scenario(self, scenario_name: str) -> None:
        if not scenario_name:
            valid = ", ".join(self.engine.available_scenarios())
            self.console.print(Panel(f"Informe um cenario: {valid}", border_style="yellow"))
            return
        try:
            self.engine.collect(scenario_name)
            self.console.print(Panel(f"Cenario aplicado: {scenario_name}", border_style="cyan"))
        except ValueError as exc:
            valid = ", ".join(self.engine.available_scenarios())
            self.console.print(Panel(f"{exc}\nOpcoes: {valid}", border_style="red"))

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
        self.console.print(
            Panel(
                "\n".join(lines),
                title="Resposta Automatizada",
                border_style=self._mission_state_style(decision["estado_missao"]),
            )
        )

    def _print_impact(self) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        decision = self.engine.decision_summary()
        self.console.print(
            Panel(
                decision["impacto_terrestre"],
                title="Impacto Terrestre",
                border_style="blue",
            )
        )

    def _analyze(self, question: str) -> None:
        if not self.engine.last_snapshot:
            self.engine.collect()
        with self.console.status("[bold cyan]Consultando IA...[/bold cyan]"):
            answer = self.engine.analyze(question or "Como esta a missao?")
        self.console.print(Panel(answer, title="Analise da IA", border_style="cyan"))

    def _read_command(self) -> str:
        if self._interactive:
            try:
                return self._get_session().prompt(HTML("<ansicyan><b>❯</b></ansicyan> ")).strip()
            except (EOFError, KeyboardInterrupt):
                raise
        try:
            return input("\n❯ ").strip()
        except EOFError:
            raise

    def run(self) -> None:
        render_banner()
        self._help()
        self._print_status()
        while True:
            try:
                cmd = self._read_command()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[green]Encerrando Central da Missao.[/green]")
                break
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
            if cmd.startswith(("cenario ", "scenario ")):
                prefix = "cenario" if cmd.startswith("cenario ") else "scenario"
                scenario_name = cmd.replace(prefix, "", 1).strip()
                self._set_scenario(scenario_name)
                continue
            if cmd in {"cenario", "scenario"}:
                self._set_scenario("")
                continue
            if cmd.startswith(("analisar ", "analyze ")):
                prefix = "analisar" if cmd.startswith("analisar ") else "analyze"
                question = cmd.replace(prefix, "", 1).strip()
                self._analyze(question)
                continue
            if cmd in {"analisar", "analyze"}:
                self._analyze("")
                continue
            self.console.print("[yellow]Comando invalido. Digite 'ajuda'.[/yellow]")
