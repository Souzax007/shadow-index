#!/usr/bin/env python3
"""Entrada principal da aplicacao modular de varredura."""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from collectors.github_collector import GitHubCollector
from modulo.banner import show_banner
from modulo.database import MySQLDatabase
from modulo.loading import PhraseLoader
from modulo.menu import interactive_setup
from modulo.report import export_static_html
from utils.helpers import format_number
from utils.logger import log

load_dotenv()

console = Console()

# Configuracao do banco de dados
DB_HOST = os.getenv("DB_HOST", "SEU_HOST_MYSQL")
DB_USER = os.getenv("DB_USER", "SEU_USUARIO_MYSQL")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SUA_SENHA_MYSQL")
DB_NAME = os.getenv("DB_NAME", "osint_tools")


def build_results_table(results: List[Dict[str, Any]]) -> Table:
    table = Table(
        title="[bold cyan]Top resultados[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Repositorio", style="bold", width=28)
    table.add_column("Linguagem", width=14)
    table.add_column("Stars", justify="right", width=10)
    table.add_column("Topicos", width=32)

    top = sorted(results, key=lambda item: item.get("stars", 0), reverse=True)[:20]
    for idx, repo in enumerate(top, 1):
        topics = repo.get("topics") or []
        if isinstance(topics, str):
            topics = [topics]

        table.add_row(
            str(idx),
            (repo.get("full_name") or repo.get("name") or "N/A")[:28],
            str(repo.get("language") or "Unknown"),
            format_number(int(repo.get("stars", 0) or 0)),
            ", ".join(topics[:3]) if topics else "-",
        )

    return table


async def run_scan() -> None:
    show_banner(console)

    config = interactive_setup(console)

    # Conecta ao backend de persistencia conforme escolha do menu
    db = MySQLDatabase(
        DB_HOST,
        DB_USER,
        DB_PASSWORD,
        DB_NAME,
        preferred_backend=config.storage_backend,
    )
    db_connected = False

    if db.connect() and db.create_tables():
        db_connected = True
        if db.is_offline_mode:
            if config.storage_backend == "local":
                console.print(
                    f"[yellow]Salvamento local ativado (SQLite offline):[/yellow] [bold]{db.offline_db_path}[/bold]"
                )
            else:
                console.print(
                    f"[yellow]MySQL indisponivel. Modo offline ativado em SQLite:[/yellow] [bold]{db.offline_db_path}[/bold]"
                )
        else:
            console.print("[green]Banco de dados conectado e pronto (MySQL)[/green]")
    else:
        console.print("[red]Erro: Nao foi possivel conectar ao MySQL nem iniciar banco offline SQLite[/red]")
        console.print(f"[dim]Host: {DB_HOST}, Usuario: {DB_USER}[/dim]")
    phrase_loader = PhraseLoader()
    await phrase_loader.warmup()

    stats: Dict[str, Any] = {
        "total_found": 0,
        "new_added": 0,
        "duplicates_skipped": 0,
        "errors": 0,
        "queries": config.queries,
        "start_time": datetime.now(timezone.utc),
        "end_time": None,
        "db_new_tools": 0,
        "db_duplicates": 0,
    }

    results: List[Dict[str, Any]] = []
    seen_urls = set()

    collector = GitHubCollector(
        min_delay=config.min_delay,
        max_delay=config.max_delay,
        max_requests_per_minute=config.max_requests_per_minute,
        random_page_choices=config.page_choices,
    )

    console.print("\n[cyan]Iniciando varredura publica...[/cyan]\n")

    with Progress(
        SpinnerColumn(spinner_name="star2", style="bold yellow"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
        console=console,
    ) as progress:
        search_task = progress.add_task("[cyan]Preparando varredura...[/cyan]", total=len(config.queries))

        async with collector:
            for query in config.queries:
                phrase = phrase_loader.next_phrase()
                progress.update(
                    search_task,
                    description=f"[cyan]★ Buscando '{query}'[/cyan] | [dim]{phrase}[/dim]",
                )

                try:
                    async for repo in collector.search_osint_repositories(query, max_pages=config.max_pages):
                        stats["total_found"] += 1
                        url = repo.get("url") or repo.get("html_url") or ""
                        if url and url in seen_urls:
                            stats["duplicates_skipped"] += 1
                            continue

                        if url:
                            seen_urls.add(url)

                        results.append(repo)
                        stats["new_added"] += 1

                        # Salva no banco de dados
                        if db_connected:
                            # Usa owner/repo como identificador principal para evitar colisoes de nome.
                            nome = repo.get("full_name") or repo.get("name") or ""
                            descricao = repo.get("description") or ""
                            linguagem = repo.get("language") or "Unknown"
                            stars = repo.get("stars") or 0
                            topics = ", ".join(repo.get("topics") or [])
                            
                            if db.salvar_ferramenta(
                                nome=nome,
                                url=url,
                                descricao=descricao,
                                linguagem=linguagem,
                                stars=stars,
                                topics=topics,
                                categoria=config.category,
                                query=query
                            ):
                                stats["db_new_tools"] += 1
                                console.print(f"[green][+][/green] Nova ferramenta salva: {nome}")
                            else:
                                stats["db_duplicates"] += 1
                                console.print(f"[yellow][!][/yellow] Ferramenta ja existe: {nome}")

                except Exception as exc:
                    stats["errors"] += 1
                    log.error(f"Erro na query '{query}': {exc}")

                progress.update(search_task, advance=1)

        progress.update(search_task, completed=len(config.queries))

    stats["end_time"] = datetime.now(timezone.utc)

    # Registra a varredura no banco
    if db_connected:
        elapsed_seconds = (stats["end_time"] - stats["start_time"]).total_seconds()
        db.registrar_varredura(
            categoria=config.category,
            queries=", ".join(config.queries),
            quantidade_encontradas=stats["total_found"],
            quantidade_novas=stats["db_new_tools"],
            quantidade_duplicadas=stats["db_duplicates"],
            tempo_execucao=elapsed_seconds
        )

    report_path = Path("exports") / "osint_report.html"
    export_static_html(results, stats, report_path)

    elapsed_seconds = (stats["end_time"] - stats["start_time"]).total_seconds()
    elapsed = f"{elapsed_seconds:.1f}s" if elapsed_seconds < 60 else f"{elapsed_seconds / 60:.1f}min"

    summary_lines = [
        "[bold cyan]Resumo da execucao[/bold cyan]",
        f"Total encontrado: [bold]{stats['total_found']}[/bold]",
        f"Resultados unicos: [bold green]{stats['new_added']}[/bold green]",
        f"Duplicados ignorados: [bold yellow]{stats['duplicates_skipped']}[/bold yellow]",
        f"Erros: [bold red]{stats['errors']}[/bold red]",
        f"Tempo: [bold]{elapsed}[/bold]",
        f"Queries: [bold]{len(config.queries)}[/bold]",
    ]

    if db_connected:
        summary_lines.extend([
            "",
            "[bold cyan]Banco de Dados[/bold cyan]",
            f"Backend ativo: [bold]{db.backend_label}[/bold]",
            f"Ferramentas novas: [bold green]{stats['db_new_tools']}[/bold green]",
            f"Duplicatas detectadas: [bold yellow]{stats['db_duplicates']}[/bold yellow]",
        ])

    panel = Panel(
        "\n".join(summary_lines),
        border_style="cyan",
        box=box.ROUNDED,
    )

    console.print(panel)
    if results:
        console.print(build_results_table(results))
    else:
        console.print("[yellow]Nenhum resultado encontrado.[/yellow]")

    console.print(f"\n[green]Relatorio HTML:[/green] [bold]{report_path}[/bold]\n")

    # Exibe estatisticas do banco
    if db_connected:
        stats_db = db.obter_stats()
        if stats_db:
            console.print(Panel(
                f"""[bold cyan]Estatisticas do Banco[/bold cyan]
Total de ferramentas: [bold]{stats_db.get('total_ferramentas', 0)}[/bold]
Total de varreduras: [bold]{stats_db.get('total_varreduras', 0)}[/bold]""",
                border_style="blue",
                box=box.ROUNDED,
            ))

    # Desconecta do banco
    db.disconnect()


async def main() -> None:
    try:
        await run_scan()
    except KeyboardInterrupt:
        console.print("\n[yellow]Execucao interrompida.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[red]Erro fatal: {exc}[/red]")
        log.critical(f"Erro fatal: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
