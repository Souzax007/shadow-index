from rich.console import Console
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.table import Table

from modulo.filters import CATEGORY_QUERIES, SearchConfig, build_queries


# Mapa de descrições amigáveis para cada categoria
CATEGORY_DESCRIPTIONS = {
    # === OSINT CLÁSSICO ===
    "all": "Todas as categorias",
    "email": "Email OSINT",
    "username": "Username OSINT",
    "domain": "Domain Recon",
    "social": "Redes Sociais OSINT",
    "phone": "Phone Lookup",
    "ip": "IP Lookup",
    "geolocation": "Geolocalização",
    
    # === RECONNAISSANCE ===
    "enumeration": "Enumeração",
    "dns": "DNS Recon",
    "subdomain": "Subdomain Enum",
    "nmap": "Port Scanning",
    "fingerprinting": "Web Fingerprinting",
    
    # === WORDLISTS & FUZZING ===
    "wordlist": "Wordlists",
    "fuzzing": "Fuzzing Tools",
    "brute_force": "Brute Force",
    
    # === VULNERABILITIES ===
    "vulnerability": "Vulnerability Scanner",
    "sql_injection": "SQL Injection",
    "xss": "XSS Tools",
    "rce": "Remote Code Exec",
    "privilege_escalation": "PrivEsc",
    "web_exploitation": "Web Exploitation",
    
    # === PENTESTING FRAMEWORKS ===
    "metasploit": "Metasploit",
    "pentest": "Penetration Testing",
    "burpsuite": "Burp Suite",
    "sqlmap": "SQLMap",
    
    # === NETWORK ===
    "network": "Network Tools",
    "wireshark": "Wireshark",
    "proxy": "Proxy Tools",
    "vpn": "VPN Tools",
    
    # === WEB SECURITY ===
    "web_scanner": "Web Scanner",
    "cms": "CMS Detection",
    "jwt": "JWT Vulnerabilities",
    "csrf": "CSRF Tools",
    
    # === EXPLOITATION ===
    "exploit": "Exploit Code",
    "payload": "Payload Generator",
    "reverse_shell": "Reverse Shell",
    "webshell": "Web Shell",
    
    # === CRYPTOGRAPHY ===
    "crypto": "Cryptography",
    "hash": "Hash Cracking",
    "steganography": "Steganography",
    
    # === MALWARE ===
    "malware": "Malware Analysis",
    "reverse_engineering": "Reverse Engineering",
    "sandbox": "Sandbox Analysis",
    
    # === SOCIAL ENGINEERING ===
    "phishing": "Phishing",
    "social_engineering": "Social Engineering",
    
    # === AUTHENTICATION ===
    "auth": "Auth Bypass",
    "mfa": "MFA Bypass",
    "ldap": "LDAP Injection",
    
    # === API & CLOUD ===
    "api": "API Security",
    "cloud": "Cloud Security",
    "s3": "S3 Buckets",
    
    # === THREAT INTELLIGENCE ===
    "threat": "Threat Intelligence",
    "ioc": "IOC Indicators",
    
    # === DARK WEB ===
    "dark_web": "Dark Web OSINT",
    "tor": "Tor Tools",
    
    # === HARDENING ===
    "hardening": "Hardening",
    "firewall": "Firewall Tools",
    
    # === CODE ANALYSIS ===
    "code": "Code Search & Leaks",
    "sast": "Static Analysis",
    
    # === REPORTING ===
    "report": "Reporting Tools",
    
    # === MISC ===
    "automation": "Automation",
    "framework": "Security Framework",
    "tool": "General Tools",
}


def _build_category_map() -> tuple[dict[int, str], list[str]]:
    """Constrói mapa dinâmico de categorias."""
    categories = list(CATEGORY_QUERIES.keys())
    category_map = {i + 1: cat for i, cat in enumerate(categories)}
    choices = [str(i + 1) for i in range(len(categories))]
    return category_map, choices


def _print_categories(console: Console) -> None:
    table = Table(title="Categorias de busca", border_style="cyan")
    table.add_column("Opcao", style="bold")
    table.add_column("Chave")
    table.add_column("Descricao")

    category_map, _ = _build_category_map()
    for option, key in category_map.items():
        desc = CATEGORY_DESCRIPTIONS.get(key, key.capitalize())
        table.add_row(str(option), key, desc)

    console.print(table)


def interactive_setup(console: Console) -> SearchConfig:
    """Menu interativo principal."""
    console.print("\n[bold cyan]Menu interativo[/bold cyan]")

    source_option = IntPrompt.ask(
        "Fonte de busca (1=GitHub)",
        default=1,
        choices=["1"],
        show_choices=False,
    )
    source = "github" if source_option == 1 else "github"

    _print_categories(console)
    category_map, choices = _build_category_map()
    category_option = IntPrompt.ask(
        "Escolha a categoria",
        default=1,
        choices=choices,
        show_choices=False,
    )

    category = category_map[category_option]

    # Pergunta se quer usar o painel interativo de palavras-chave
    use_keywords_panel = Confirm.ask(
        "\nUsar painel interativo de palavras-chave?",
        default=False,
    )
    
    extra_keywords = []
    if use_keywords_panel:
        try:
            from modulo.interactive_keywords import interactive_keywords_panel
            
            console.print("\n[cyan]Iniciando painel de palavras-chave...[/cyan]")
            extra_keywords = interactive_keywords_panel(console)
        except Exception as e:
            console.print(f"[yellow]Erro ao carregar painel de palavras-chave: {e}[/yellow]")
            extra_keywords = []

    topic = Prompt.ask(
        "Topico livre opcional (enter para ignorar)",
        default="",
    )

    max_pages = IntPrompt.ask(
        "Maximo de paginas por query",
        default=8,
        choices=[str(i) for i in range(1, 21)],
        show_choices=False,
    )

    page_choices_raw = Prompt.ask(
        "Valores aleatorios de paginas por query (ex: 1,2,3)",
        default="1,2,3",
    )
    page_choices = []
    for item in page_choices_raw.split(","):
        item = item.strip()
        if item.isdigit():
            value = int(item)
            if value > 0:
                page_choices.append(value)
    if not page_choices:
        page_choices = [1, 2, 3]

    rpm = IntPrompt.ask(
        "Limite maximo de requisicoes por minuto",
        default=15,
        choices=[str(i) for i in range(5, 31)],
        show_choices=False,
    )

    min_delay_raw = Prompt.ask("Delay minimo entre requisicoes (segundos)", default="1.2")
    max_delay_raw = Prompt.ask("Delay maximo entre requisicoes (segundos)", default="3.0")

    try:
        min_delay = float(min_delay_raw)
    except ValueError:
        min_delay = 1.2

    try:
        max_delay = float(max_delay_raw)
    except ValueError:
        max_delay = 3.0

    if max_delay < min_delay:
        max_delay = min_delay

    queries = build_queries(category, topic)
    
    # Adiciona palavras-chave extras do painel
    if extra_keywords:
        queries.extend(extra_keywords)
        # Remove duplicatas mantendo ordem
        queries = list(dict.fromkeys(queries))

    # Garante no maximo a quantidade de paginas selecionada no menu
    page_choices = [min(value, max_pages) for value in page_choices]
    page_choices = [value for value in page_choices if value >= 1]
    if not page_choices:
        page_choices = [max_pages]

    console.print(
        f"\n[green]Config pronta:[/green] {len(queries)} queries | fonte={source} | categoria={category}"
        + (f" | +{len(extra_keywords)} keywords extras" if extra_keywords else "")
    )

    return SearchConfig(
        source=source,
        category=category,
        topic=topic,
        queries=queries,
        max_pages=max_pages,
        page_choices=page_choices,
        max_requests_per_minute=rpm,
        min_delay=min_delay,
        max_delay=max_delay,
    )
