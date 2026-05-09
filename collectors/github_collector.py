"""
Coletor de repositórios do GitHub via scraping de páginas HTML.
Sem uso de API.
"""
import json
import os
import asyncio
import aiohttp
import re
import random
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, AsyncGenerator
from urllib.parse import quote_plus, urljoin
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from utils.logger import log
from utils.helpers import safe_int, normalize_url

load_dotenv()

# Constantes
GITHUB_WEB_BASE = "https://github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
PER_PAGE = int(os.getenv("PER_PAGE", "30"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Headers padrão para GitHub HTML
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "OSINT-Tool-Finder/1.0",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"
    log.info("Token do GitHub configurado para requests web.")
else:
    log.warning("Sem token do GitHub. Usando limites conservadores de request.")


class GitHubCollector:
    """
    Coletor de ferramentas OSINT do GitHub.
    Busca repositórios em páginas HTML do GitHub.
    """

    def __init__(
        self,
        min_delay: float = 1.2,
        max_delay: float = 3.0,
        max_requests_per_minute: int = 15,
        random_page_choices: Optional[List[int]] = None,
        novelty_threshold: float = 0.15,
        low_novelty_streak_limit: int = 2,
    ):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 60
        self.rate_limit_reset = 0
        self.min_delay = max(min_delay, 0.1)
        self.max_delay = max(max_delay, self.min_delay)
        self.max_requests_per_minute = max(max_requests_per_minute, 1)
        self.random_page_choices = random_page_choices or [1, 2, 3]
        self.request_times: List[float] = []
        # Se a taxa de novos por pagina cair abaixo deste limite por N paginas,
        # trocamos automaticamente de perfil/janela para buscar mais novidade.
        self.novelty_threshold = max(0.0, min(novelty_threshold, 1.0))
        self.low_novelty_streak_limit = max(1, low_novelty_streak_limit)

    async def _respect_request_budget(self) -> None:
        """Respeita o limite de requests por minuto definido no menu."""
        now = time.time()
        self.request_times = [ts for ts in self.request_times if now - ts < 60]

        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]) + random.uniform(0.1, 0.8)
            if sleep_time > 0:
                log.info(f"Aguardando {sleep_time:.1f}s para respeitar o limite de requisicoes/minuto")
                await asyncio.sleep(sleep_time)

        self.request_times.append(time.time())

    async def _random_human_delay(self) -> None:
        """Adiciona atraso aleatorio para evitar rajadas de requests."""
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(
        self, url: str, retries: int = MAX_RETRIES
    ) -> Optional[str]:
        """
        Faz requisição HTML ao GitHub com retry e rate limit handling.
        """
        for attempt in range(retries):
            try:
                await self._respect_request_budget()

                async with self.session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    allow_redirects=True,
                ) as response:
                    log.debug(f"Request: {url} | Status: {response.status}")

                    if response.status == 200:
                        content = await response.text()
                        await self._random_human_delay()
                        return content

                    if response.status in {403, 429}:
                        wait_time = 5 * (attempt + 1)
                        log.warning(f"GitHub bloqueou/limitou a requisição. Aguardando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status == 404:
                        log.warning(f"Recurso não encontrado: {url}")
                        return None

                    if response.status >= 500:
                        log.warning(f"Erro servidor {response.status}. Tentativa {attempt + 1}/{retries}")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        continue

                    log.error(f"Erro inesperado {response.status}: {url}")
                    return None

            except asyncio.TimeoutError:
                log.warning(f"Timeout na requisição. Tentativa {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except aiohttp.ClientError as e:
                log.error(f"Erro de conexão: {e}. Tentativa {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                log.error(f"Erro inesperado na requisição: {e}")
                return None

        log.error(f"Falha após {retries} tentativas: {url}")
        return None

    def _parse_stars(self, text: str) -> int:
        """Converte texto de estrelas do GitHub para inteiro aproximado."""
        if not text:
            return 0

        cleaned = text.strip().lower().replace(",", "")
        match = re.search(r"([\d.]+)\s*([km]?)", cleaned)
        if not match:
            return safe_int(cleaned, 0)

        value = float(match.group(1))
        suffix = match.group(2)
        if suffix == "k":
            value *= 1_000
        elif suffix == "m":
            value *= 1_000_000
        return int(value)

    def _find_repo_container(self, anchor: Any) -> Any:
        """Sobe a árvore até encontrar um container com dados do resultado."""
        current = anchor
        while current and getattr(current, "parent", None):
            current = current.parent
            if not current or not getattr(current, "select_one", None):
                continue
            if current.select_one('a[href$="/stargazers"]'):
                return current
        return anchor.parent if getattr(anchor, "parent", None) else anchor

    def _build_incremental_time_qualifiers(self) -> List[str]:
        """
        Monta qualificadores de tempo para variar os resultados entre execucoes.
        A ideia é alternar entre repos recentes, intermediarios e mais antigos.
        """
        today = datetime.now(timezone.utc).date()

        d7 = (today - timedelta(days=7)).isoformat()
        d30 = (today - timedelta(days=30)).isoformat()
        d180 = (today - timedelta(days=180)).isoformat()
        d365 = (today - timedelta(days=365)).isoformat()
        d730 = (today - timedelta(days=730)).isoformat()

        return [
            "",  # sem filtro de tempo (baseline)
            f"pushed:>={d30}",
            f"pushed:{d180}..{d30}",
            f"pushed:{d730}..{d365}",
            f"created:>={d7}",
            f"created:{d365}..{d180}",
        ]

    def _parse_repo_card(self, heading_link: Any) -> Optional[Dict[str, Any]]:
        """Extrai dados do resultado de busca usando o link do heading."""
        href = heading_link.get("href", "")
        full_name = href.strip("/")
        if full_name.count("/") != 1:
            return None

        container = self._find_repo_container(heading_link)
        repo_url = normalize_url(urljoin(GITHUB_WEB_BASE, href))

        description = ""
        description_node = None
        if getattr(container, "select_one", None):
            description_node = container.select_one("p") or container.select_one('div:not(:has(h3))')
        if description_node:
            description = description_node.get_text(" ", strip=True)

        language = "Unknown"
        language_node = None
        if getattr(container, "select_one", None):
            language_node = container.select_one('span[itemprop="programmingLanguage"]')
        if language_node:
            language = language_node.get_text(" ", strip=True)
        else:
            for text_node in getattr(container, "stripped_strings", []):
                if text_node and text_node not in {description, full_name.split("/")[-1]}:
                    if text_node.lower() in {"python", "javascript", "typescript", "html", "go", "rust", "shell", "css", "php", "java", "ruby", "c", "c++", "swift"}:
                        language = text_node
                        break

        stars = 0
        star_link = None
        if getattr(container, "select_one", None):
            star_link = container.select_one('a[href$="/stargazers"]')
        if star_link:
            stars = self._parse_stars(star_link.get_text(" ", strip=True))

        topics = []
        if getattr(container, "select", None):
            topics = [tag.get_text(" ", strip=True) for tag in container.select('a[href^="/topics/"]')]

        return {
            "name": full_name.split("/")[-1],
            "full_name": full_name,
            "html_url": repo_url,
            "description": description,
            "language": language,
            "stargazers_count": stars,
            "forks_count": 0,
            "topics": topics,
            "readme_content": None,
        }

    async def search_repositories(
        self, query: str, max_pages: int = MAX_PAGES
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Busca repositórios no GitHub por termo de pesquisa via HTML.
        Gera resultados página por página.
        """
        # Faz varredura em modos diferentes para aumentar diversidade entre execucoes.
        search_profiles = [
            {"s": "stars", "o": "desc", "label": "stars_desc"},
            {"s": "updated", "o": "desc", "label": "updated_desc"},
            {"s": "forks", "o": "desc", "label": "forks_desc"},
            {"s": "", "o": "", "label": "best_match"},
        ]
        random.shuffle(search_profiles)

        # Em scans mais profundos, usa 3 perfis; em scans rapidos, 2 perfis.
        profiles_per_query = 3 if max_pages >= 6 else 2
        selected_profiles = search_profiles[:profiles_per_query]

        # Estrategia incremental por tempo para trazer ferramentas diferentes.
        time_qualifiers = self._build_incremental_time_qualifiers()
        random.shuffle(time_qualifiers)
        selected_time_qualifiers = time_qualifiers[:2]

        max_pages = max(1, max_pages)
        page_budget = min(max_pages, max(1, random.choice(self.random_page_choices)))

        if page_budget >= max_pages:
            pages_to_scan = list(range(1, max_pages + 1))
        else:
            pages_to_scan = sorted(random.sample(range(1, max_pages + 1), k=page_budget))

        yielded_full_names = set()

        for profile in selected_profiles:
            for time_q in selected_time_qualifiers:
                final_query = query if not time_q else f"{query} {time_q}"
                encoded_query = quote_plus(final_query)
                low_novelty_streak = 0

                for current_page in pages_to_scan:
                    url = (
                        f"{GITHUB_WEB_BASE}/search"
                        f"?q={encoded_query}"
                        f"&type=repositories"
                        f"&s={profile['s']}"
                        f"&o={profile['o']}"
                        f"&p={current_page}"
                    )

                    # Remove parametros vazios para modo best_match.
                    url = url.replace("&s=&o=", "")

                    label_time = time_q or "no_time_filter"
                    log.info(
                        f"Buscando pagina {current_page} [{profile['label']} | {label_time}]: '{query}'"
                    )
                    html = await self._make_request(url)

                    if not html:
                        continue

                    soup = BeautifulSoup(html, "html.parser")
                    results: List[Dict[str, Any]] = []
                    seen_names = set()

                    heading_links = soup.select('h3 a[href^="/"]')

                    for heading_link in heading_links:
                        repo = self._parse_repo_card(heading_link)
                        if repo and repo["full_name"] not in seen_names:
                            repo["source_query"] = query
                            repo["readme_content"] = ""
                            results.append(repo)
                            seen_names.add(repo["full_name"])

                    if not results:
                        fallback_links = soup.select('a[href^="/"][href*="/"]')
                        for link in fallback_links:
                            href = link.get("href", "")
                            if href.count("/") != 2:
                                continue
                            if any(segment in href for segment in ["topics", "login", "search", "sponsors", "pulls", "issues"]):
                                continue
                            repo = self._parse_repo_card(link)
                            if repo and repo["full_name"] not in seen_names:
                                repo["source_query"] = query
                                repo["readme_content"] = ""
                                results.append(repo)
                                seen_names.add(repo["full_name"])

                    if not results:
                        log.info(
                            f"Nenhum resultado para '{query}' na pagina {current_page} [{profile['label']} | {label_time}]"
                        )
                        continue

                    log.info(
                        f"Pagina {current_page} [{profile['label']} | {label_time}]: {len(results)} resultados"
                    )

                    page_new = 0
                    for repo in results:
                        full_name = repo.get("full_name")
                        if not full_name or full_name in yielded_full_names:
                            continue
                        yielded_full_names.add(full_name)
                        page_new += 1
                        yield repo

                    page_total = len(results)
                    novelty_ratio = (page_new / page_total) if page_total else 0.0

                    if novelty_ratio < self.novelty_threshold:
                        low_novelty_streak += 1
                        log.info(
                            "Baixa novidade detectada "
                            f"({novelty_ratio:.0%}) [{low_novelty_streak}/{self.low_novelty_streak_limit}]"
                        )
                    else:
                        low_novelty_streak = 0

                    if low_novelty_streak >= self.low_novelty_streak_limit:
                        log.info(
                            "Trocando automaticamente de estrategia devido a baixa novidade."
                        )
                        break

                    await self._random_human_delay()

    async def get_repository_details(self, full_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de um repositório específico.
        """
        return None

    async def get_readme(self, full_name: str) -> Optional[str]:
        """
        Mantido para compatibilidade; neste modo não usamos API nem coletamos README.
        """
        return None

    async def get_repository_topics(self, full_name: str) -> List[str]:
        """
        Mantido para compatibilidade; neste modo os tópicos vêm do card de busca.
        """
        return []

    async def collect_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza o resultado coletado no card de busca.
        """
        repo_data = dict(repo_data)
        repo_data["name"] = repo_data.get("name", "")
        repo_data["full_name"] = repo_data.get("full_name", "")
        repo_data["url"] = normalize_url(repo_data.get("html_url", repo_data.get("url", "")))
        repo_data["description"] = repo_data.get("description", "") or ""
        repo_data["language"] = repo_data.get("language") or "Unknown"
        repo_data["stars"] = safe_int(repo_data.get("stargazers_count", repo_data.get("stars", 0)), 0)
        repo_data["forks"] = safe_int(repo_data.get("forks_count", repo_data.get("forks", 0)), 0)
        topics = repo_data.get("topics") or []
        if isinstance(topics, str):
            try:
                topics = json.loads(topics)
            except Exception:
                topics = []
        repo_data["topics"] = topics
        repo_data.setdefault("readme_content", "")
        repo_data.setdefault("category", None)
        repo_data.setdefault("summary", None)
        return repo_data

    async def search_osint_tools(
        self, queries: List[str], max_pages_per_query: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Busca ferramentas OSINT usando múltiplos termos de pesquisa.
        Gera repositórios coletados um por um.
        """
        for query in queries:
            log.info(f"\n{'='*60}")
            log.info(f"Iniciando busca por: '{query}'")
            log.info(f"{'='*60}")

            async for repo in self.search_repositories(query, max_pages=max_pages_per_query):
                try:
                    collected = await self.collect_repository(repo)
                    collected["source_query"] = query
                    yield collected
                except Exception as e:
                    log.error(f"Erro ao coletar repositório {repo.get('name', 'unknown')}: {e}")
                    continue

            # Pausa entre queries diferentes
            await asyncio.sleep(1)

    async def search_osint_repositories(
        self, query: str, max_pages: int = MAX_PAGES
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Compatibilidade com o fluxo atual da aplicação principal.
        Busca um termo por vez e devolve repositórios já enriquecidos.
        """
        async for repo in self.search_repositories(query, max_pages=max_pages):
            collected = await self.collect_repository(repo)
            collected["source_query"] = query
            yield collected


async def collect_from_github(queries: List[str]) -> List[Dict[str, Any]]:
    """
    Função de alto nível para coletar ferramentas OSINT do GitHub.
    """
    results = []
    async with GitHubCollector() as collector:
        async for repo in collector.search_osint_tools(queries):
            results.append(repo)
    return results


# Lista de termos para busca OSINT
OSINT_QUERIES = [
    "osint",
    "osint tool",
    "osint framework",
    "reconnaissance",
    "recon tool",
    "email osint",
    "email lookup",
    "username search",
    "username osint",
    "threat intelligence",
    "threat intel",
    "social media osint",
    "social media scraper",
    "phone lookup osint",
    "phone number osint",
    "domain recon",
    "subdomain enumeration",
    "metadata analysis",
    "dark web osint",
    "people search osint",
]