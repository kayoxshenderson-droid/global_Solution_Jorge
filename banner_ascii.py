"""Gerador de banner ASCII para a Mission Control AI."""

import argparse

import pyfiglet
from rich.align import Align
from rich.console import Console

console = Console()


def render_banner(font: str = "ansi_shadow", text: str = "Mission Control AI") -> None:
    banner = pyfiglet.figlet_format(text, font=font)
    console.print(Align.center(f"[bold cyan]{banner}[/bold cyan]"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Banner ASCII da Mission Control AI")
    parser.add_argument("--fonts", action="store_true", help="Lista as fontes disponíveis")
    parser.add_argument("--font", default="ansi_shadow", help="Fonte do pyfiglet")
    parser.add_argument("--text", default="Mission Control AI", help="Texto para renderizar")
    args = parser.parse_args()

    if args.fonts:
        for name in sorted(pyfiglet.FigletFont.getFonts()):
            print(name)
        return

    render_banner(font=args.font, text=args.text)


if __name__ == "__main__":
    main()

