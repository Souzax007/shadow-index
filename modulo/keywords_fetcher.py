"""
Módulo para buscar palavras-chave dinâmicas de várias fontes na internet.
Permite enriquecer os filtros de busca com termos frescos e relevantes.
"""

import asyncio
import json
from typing import List, Set
from urllib.parse import quote

try:
    import aiohttp
except ImportError:
    aiohttp = None

from utils.logger import logger


class KeywordsFetcher:
    """Busca palavras-chave de múltiplas fontes."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.keywords: Set[str] = set()

    async def fetch_github_trending(self) -> List[str]:
        """Busca palavras-chave de repositórios trending do GitHub."""
        if not aiohttp:
            logger.warning("aiohttp não disponível. Pulando GitHub trending.")
            return []

        try:
            async with aiohttp.ClientSession() as session:
                # Busca repositórios com star recentes
                urls = [
                    "https://api.github.com/search/repositories?q=language:python+pentesting&sort=stars&order=desc&per_page=20",
                    "https://api.github.com/search/repositories?q=language:python+osint&sort=stars&order=desc&per_page=20",
                    "https://api.github.com/search/repositories?q=language:go+security&sort=stars&order=desc&per_page=20",
                ]

                keywords = set()
                for url in urls:
                    try:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                for item in data.get("items", []):
                                    # Extrai palavras-chave dos nomes
                                    name = item.get("name", "").lower()
                                    topics = item.get("topics", [])
                                    keywords.update([t.lower() for t in topics])
                                    # Extrai palavras do nome
                                    for word in name.split("-"):
                                        if len(word) > 3:
                                            keywords.add(word)
                    except Exception as e:
                        logger.debug(f"Erro ao buscar GitHub trending: {e}")

                return list(keywords)[:30]
        except Exception as e:
            logger.warning(f"Erro ao buscar GitHub trending: {e}")
            return []

    async def fetch_awesome_lists(self) -> List[str]:
        """Busca palavras-chave de awesome-lists no GitHub."""
        if not aiohttp:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                # Busca awesome lists relacionadas a security
                searches = ["awesome-security", "awesome-pentest", "awesome-hacking"]
                keywords = set()

                for search in searches:
                    try:
                        url = f"https://api.github.com/search/repositories?q={search}&per_page=10"
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                for item in data.get("items", []):
                                    topics = item.get("topics", [])
                                    keywords.update([t.lower() for t in topics])
                                    # Extrai descrição
                                    desc = item.get("description", "").lower()
                                    for word in desc.split():
                                        if len(word) > 4 and word.isalpha():
                                            keywords.add(word)
                    except Exception as e:
                        logger.debug(f"Erro ao buscar awesome list {search}: {e}")

                return list(keywords)[:30]
        except Exception as e:
            logger.warning(f"Erro ao buscar awesome lists: {e}")
            return []

    async def fetch_default_keywords(self) -> List[str]:
        """Retorna palavras-chave padrão pré-definidas (não requer internet)."""
        default_keywords = {
            # Pentesting tools
            "nmap", "metasploit", "burpsuite", "sqlmap", "nikto", "hydra",
            "hashcat", "john", "aircrack", "meterpreter", "shellcode",
            # Exploitation
            "exploit", "payload", "rce", "xss", "sql injection", "lfi", "rfi",
            "ssti", "xxe", "csrf", "idor", "auth bypass", "privilege escalation",
            # Enumeration
            "enumeration", "subdomain enumeration", "port scanning", "service enum",
            "user enumeration", "version detection", "fingerprinting",
            # Wordlists
            "wordlist", "rockyou", "crunch", "cewl", "hashcat", "fuzz",
            # Web security
            "xss payload", "sql injection payload", "web shell", "reverse shell",
            "bind shell", "one liner", "web vulnerability", "cms vulnerability",
            # Network
            "wireshark", "tcpdump", "netcat", "nessus", "openvas", "masscan",
            # Cryptography
            "encryption", "decryption", "hash", "md5", "sha", "bcrypt",
            "rsa", "aes", "cipher", "steganography", "encoding",
            # Malware
            "malware analysis", "reverse engineering", "sandbox", "virustotal",
            "dynamic analysis", "static analysis", "binary analysis",
            # Dark web
            "tor", "onion", "dark web", "darknet", "anonymous",
            # OSINT
            "social media", "email finder", "phone lookup", "ip geolocation",
            "domain recon", "dns enumeration", "subdomain discovery",
            # API Security
            "api vulnerability", "api security", "endpoint", "swagger",
            # Cloud
            "aws hacking", "azure hacking", "s3 bucket", "gcp security",
            # Misc
            "cve", "vulnerability", "exploit database", "proof of concept",
            "poc", "security research", "bug bounty", "writeup",
        }
        return list(default_keywords)

    async def fetch_all(self) -> List[str]:
        """Busca palavras-chave de todas as fontes."""
        results = []

        # Executa buscas em paralelo
        tasks = [
            self.fetch_github_trending(),
            self.fetch_awesome_lists(),
            self.fetch_default_keywords(),
        ]

        try:
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in all_results:
                if isinstance(result, list):
                    results.extend(result)
                elif isinstance(result, Exception):
                    logger.debug(f"Erro ao buscar keywords: {result}")
        except Exception as e:
            logger.debug(f"Erro ao buscar keywords em paralelo: {e}")
            # Fallback para palavras padrão
            results = await self.fetch_default_keywords()

        # Remove duplicatas e retorna
        return list(set(results))

    def fetch_all_sync(self) -> List[str]:
        """Busca palavras-chave de forma síncrona (sem async)."""
        # Retorna apenas as palavras-chave padrão (não requer I/O)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se há um loop rodando, use apenas palavras padrão
                return asyncio.run_coroutine_threadsafe(
                    self.fetch_default_keywords(), loop
                ).result(timeout=2)
        except Exception:
            pass
        
        # Fallback: retorna apenas palavras padrão
        return {
            "nmap", "metasploit", "burpsuite", "sqlmap", "nikto", "hydra",
            "hashcat", "john", "aircrack", "meterpreter", "shellcode",
            "exploit", "payload", "rce", "xss", "sql injection", "lfi", "rfi",
            "ssti", "xxe", "csrf", "idor", "auth bypass", "privilege escalation",
            "enumeration", "subdomain enumeration", "port scanning", "service enum",
            "user enumeration", "version detection", "fingerprinting",
            "wordlist", "rockyou", "crunch", "cewl", "hashcat", "fuzz",
            "xss payload", "sql injection payload", "web shell", "reverse shell",
            "bind shell", "one liner", "web vulnerability", "cms vulnerability",
            "wireshark", "tcpdump", "netcat", "nessus", "openvas", "masscan",
            "encryption", "decryption", "hash", "md5", "sha", "bcrypt",
            "rsa", "aes", "cipher", "steganography", "encoding",
            "malware analysis", "reverse engineering", "sandbox", "virustotal",
            "dynamic analysis", "static analysis", "binary analysis",
            "tor", "onion", "dark web", "darknet", "anonymous",
            "social media", "email finder", "phone lookup", "ip geolocation",
            "domain recon", "dns enumeration", "subdomain discovery",
            "api vulnerability", "api security", "endpoint", "swagger",
            "aws hacking", "azure hacking", "s3 bucket", "gcp security",
            "cve", "vulnerability", "exploit database", "proof of concept",
            "poc", "security research", "bug bounty", "writeup",
        }

    async def warmup(self) -> None:
        """Carrega palavras-chave na memória."""
        logger.info("Carregando palavras-chave...")
        keywords = await self.fetch_all()
        self.keywords = set(keywords)
        logger.info(f"Carregadas {len(self.keywords)} palavras-chave")

    def warmup_sync(self) -> None:
        """Carrega palavras-chave na memória (síncrono)."""
        logger.info("Carregando palavras-chave...")
        keywords = self.fetch_all_sync()
        self.keywords = set(keywords)
        logger.info(f"Carregadas {len(self.keywords)} palavras-chave")

    def get_suggestions(self, query: str = "", limit: int = 10) -> List[str]:
        """Retorna sugestões de palavras-chave baseadas em um query."""
        if not query:
            return list(self.keywords)[:limit]

        query_lower = query.lower()
        matches = [k for k in self.keywords if query_lower in k.lower()]
        return matches[:limit]

    def add_custom(self, keywords: List[str]) -> None:
        """Adiciona palavras-chave customizadas."""
        self.keywords.update([k.lower().strip() for k in keywords])
