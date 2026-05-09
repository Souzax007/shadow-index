from pyfiglet import Figlet
from rich import box
from rich.console import Console
from rich.panel import Panel


def show_banner(console: Console) -> None:
    """Exibe o banner principal."""
    text = Figlet(font="slant").renderText("shadow-index")
    console.print(
        Panel.fit(
            f"[bold cyan]{text}[/bold cyan]\n"
            "[white]Coleta publica e responsavel para prova de conceito.[/white]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
