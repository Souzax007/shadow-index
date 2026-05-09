"""
Funções auxiliares utilitárias para a aplicação.
"""
import re
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse
import json


def normalize_url(url: str) -> str:
    """Normaliza URL removendo barras finais e padronizando."""
    url = url.strip().rstrip("/")
    return url


def extract_repo_name(url: str) -> Optional[str]:
    """Extrai o nome do repositório de uma URL do GitHub."""
    import re
    pattern = r"github\.com/([^/]+/[^/]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def compute_hash(content: str) -> str:
    """Gera hash SHA-256 do conteúdo."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def clean_text(text: str) -> str:
    """Limpa texto: remove espaços extras, quebras de linha excessivas."""
    if not text:
        return ""
    # Remove múltiplas quebras de linha
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove espaços no início/fim de cada linha
    text = "\n".join(line.strip() for line in text.split("\n"))
    # Remove linhas vazias excessivas
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Trunca texto para um tamanho máximo."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def parse_topics(topics: Optional[str]) -> List[str]:
    """Converte string de tópicos para lista."""
    if not topics:
        return []
    try:
        if isinstance(topics, str):
            return json.loads(topics)
        return list(topics)
    except (json.JSONDecodeError, TypeError):
        return []


def format_time_ago(dt: Optional[datetime]) -> str:
    """Formata tempo relativo (ex: '2 dias atrás')."""
    if not dt:
        return "desconhecido"
    now = datetime.now(timezone.utc)
    diff = now - dt
    days = diff.days
    if days < 0:
        return "no futuro"
    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            return f"{minutes} minuto(s) atrás"
        return f"{hours} hora(s) atrás"
    if days < 30:
        return f"{days} dia(s) atrás"
    if days < 365:
        months = days // 30
        return f"{months} mês(es) atrás"
    years = days // 365
    return f"{years} ano(s) atrás"


def rate_limit_sleep(remaining: int, reset_time: int) -> int:
    """Calcula tempo de espera para respeitar rate limit."""
    if remaining <= 0:
        from time import time
        now = time()
        wait_time = max(reset_time - now, 1)
        return int(wait_time) + 1
    return 0


def safe_int(value: Any, default: int = 0) -> int:
    """Converte valor para inteiro de forma segura."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def format_number(num: int) -> str:
    """Formata números grandes (ex: 1.5k, 2.3M)."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)