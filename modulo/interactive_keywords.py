"""
Painel interativo para selecao e gerenciamento de palavras-chave.
Permite ao usuario escolher, sugerir e customizar palavras-chave para busca.
"""

from typing import List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

from modulo.keywords_fetcher import KeywordsFetcher


def interactive_keywords_panel(console: Console) -> List[str]:
    """
    Painel interativo para selecao de palavras-chave.
    Retorna lista de palavras-chave selecionadas pelo usuario.
    """
    selected_keywords: List[str] = []
    fetcher = KeywordsFetcher()

    console.print("\n[bold cyan]Painel de Palavras-Chave[/bold cyan]")
    console.print("Carregando sugestoes de palavras-chave...", style="dim")

    # Carrega keywords de forma sincrona
    fetcher.warmup_sync()

    while True:
        console.print("\n[bold]Opcoes:[/bold]")
        console.print("1. Ver sugestoes de palavras-chave")
        console.print("2. Buscar palavras-chave")
        console.print("3. Adicionar palavra customizada")
        console.print("4. Ver palavras selecionadas")
        console.print("5. Remover palavra")
        console.print("6. Finalizar selecao")

        choice = Prompt.ask("Escolha uma opcao", choices=["1", "2", "3", "4", "5", "6"])

        if choice == "1":
            # Mostra sugestoes
            suggestions = fetcher.get_suggestions(limit=20)
            if suggestions:
                table = Table(title="Sugestoes de Palavras-Chave")
                table.add_column("# ", style="bold cyan")
                table.add_column("Palavra-Chave")

                for i, kw in enumerate(suggestions, 1):
                    selected_mark = " [X]" if kw in selected_keywords else ""
                    table.add_row(str(i), f"{kw}{selected_mark}")

                console.print(table)

                add = Prompt.ask(
                    "Digite numeros separados por virgula para adicionar (ex: 1,3,5)",
                    default="",
                )
                if add:
                    try:
                        indices = [int(x.strip()) - 1 for x in add.split(",")]
                        for idx in indices:
                            if 0 <= idx < len(suggestions):
                                kw = suggestions[idx]
                                if kw not in selected_keywords:
                                    selected_keywords.append(kw)
                                    console.print(f"[green][+][/green] Adicionado: {kw}")
                    except (ValueError, IndexError):
                        console.print("[red]Entrada invalida[/red]")

        elif choice == "2":
            # Busca palavras-chave
            query = Prompt.ask("Digite a palavra-chave para buscar")
            if query:
                matches = fetcher.get_suggestions(query, limit=15)
                if matches:
                    table = Table(title=f"Resultados para '{query}'")
                    table.add_column("# ", style="bold cyan")
                    table.add_column("Palavra-Chave")

                    for i, kw in enumerate(matches, 1):
                        selected_mark = " [X]" if kw in selected_keywords else ""
                        table.add_row(str(i), f"{kw}{selected_mark}")

                    console.print(table)

                    add = Prompt.ask(
                        "Digite numeros para adicionar (ex: 1,2,3)",
                        default="",
                    )
                    if add:
                        try:
                            indices = [int(x.strip()) - 1 for x in add.split(",")]
                            for idx in indices:
                                if 0 <= idx < len(matches):
                                    kw = matches[idx]
                                    if kw not in selected_keywords:
                                        selected_keywords.append(kw)
                                        console.print(f"[green][+][/green] Adicionado: {kw}")
                        except (ValueError, IndexError):
                            console.print("[red]Entrada invalida[/red]")
                else:
                    console.print(f"[yellow]Nenhuma palavra encontrada para '{query}'[/yellow]")

        elif choice == "3":
            # Adiciona customizada
            custom = Prompt.ask("Digite a palavra-chave customizada")
            if custom:
                custom = custom.lower().strip()
                if custom not in selected_keywords:
                    selected_keywords.append(custom)
                    fetcher.add_custom([custom])
                    console.print(f"[green][+][/green] Adicionado: {custom}")
                else:
                    console.print(f"[yellow]'{custom}' ja esta na lista[/yellow]")

        elif choice == "4":
            # Mostra selecionadas
            if selected_keywords:
                table = Table(title="Palavras-Chave Selecionadas")
                table.add_column("# ", style="bold cyan")
                table.add_column("Palavra-Chave")

                for i, kw in enumerate(selected_keywords, 1):
                    table.add_row(str(i), kw)

                console.print(table)
                console.print(f"\n[green]Total:[/green] {len(selected_keywords)} palavras-chave")
            else:
                console.print("[yellow]Nenhuma palavra-chave selecionada[/yellow]")

        elif choice == "5":
            # Remove palavra
            if selected_keywords:
                table = Table(title="Remover Palavra-Chave")
                table.add_column("# ", style="bold cyan")
                table.add_column("Palavra-Chave")

                for i, kw in enumerate(selected_keywords, 1):
                    table.add_row(str(i), kw)

                console.print(table)

                remove = Prompt.ask(
                    "Digite o numero para remover",
                    default="",
                )
                if remove:
                    try:
                        idx = int(remove) - 1
                        if 0 <= idx < len(selected_keywords):
                            removed = selected_keywords.pop(idx)
                            console.print(f"[red][-][/red] Removido: {removed}")
                    except ValueError:
                        console.print("[red]Entrada invalida[/red]")
            else:
                console.print("[yellow]Nenhuma palavra-chave para remover[/yellow]")

        elif choice == "6":
            # Finaliza
            if selected_keywords:
                console.print(Panel(
                    f"[green][+] {len(selected_keywords)} palavras-chave selecionadas[/green]",
                    title="Selecao Finalizada"
                ))
            else:
                use_default = Confirm.ask(
                    "Nenhuma palavra selecionada. Usar padroes?",
                    default=True,
                )
                if use_default:
                    selected_keywords = fetcher.get_suggestions(limit=10)
                    console.print(f"[cyan]Usando {len(selected_keywords)} palavras padrao[/cyan]")
            break

    return selected_keywords


def show_keywords_summary(console: Console, keywords: List[str]) -> None:
    """Mostra resumo das palavras-chave selecionadas."""
    if keywords:
        table = Table(title="Palavras-Chave para a Busca")
        table.add_column("Palavra")

        for kw in keywords:
            table.add_row(kw)

        console.print(table)
