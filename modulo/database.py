"""
Modulo de persistencia com MySQL e fallback offline em SQLite.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception

logger = logging.getLogger(__name__)


class MySQLDatabase:
    """Gerenciador de persistencia: tenta MySQL e cai para SQLite offline."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str = "osint_tools",
        preferred_backend: str = "mysql",
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.preferred_backend = preferred_backend
        self.connection = None
        self.is_connected = False
        self.backend = "none"
        self.offline_db_path = Path("offline") / f"{database}.sqlite3"

    @property
    def is_offline_mode(self) -> bool:
        return self.backend == "sqlite"

    @property
    def backend_label(self) -> str:
        if self.backend == "mysql":
            return "MySQL"
        if self.backend == "sqlite":
            return "SQLite (offline)"
        return "Nenhum"

    def connect(self) -> bool:
        """Conecta no MySQL; em falha, ativa banco offline SQLite automaticamente."""
        if self.preferred_backend == "local":
            logger.info("Persistencia local selecionada pelo usuario. Usando SQLite offline.")
            return self._connect_sqlite_fallback()

        if mysql:
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=True,
                )
                self.is_connected = True
                self.backend = "mysql"
                logger.info(f"Conectado ao MySQL: {self.host}/{self.database}")
                return True
            except MySQLError as exc:
                logger.warning(f"MySQL indisponivel ({exc}). Ativando modo offline SQLite.")
        else:
            logger.warning("mysql-connector-python nao instalado. Ativando modo offline SQLite.")

        return self._connect_sqlite_fallback()

    def _connect_sqlite_fallback(self) -> bool:
        try:
            self.offline_db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(self.offline_db_path))
            self.connection.row_factory = sqlite3.Row
            self.is_connected = True
            self.backend = "sqlite"
            logger.info(f"Conectado ao SQLite offline: {self.offline_db_path}")
            return True
        except sqlite3.Error as exc:
            logger.error(f"Erro ao conectar no SQLite offline: {exc}")
            self.connection = None
            self.is_connected = False
            self.backend = "none"
            return False

    def create_tables(self) -> bool:
        if not self.is_connected:
            logger.error("Nao conectado ao banco de dados")
            return False

        try:
            cursor = self.connection.cursor()

            if self.backend == "mysql":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ferramentas (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        nome VARCHAR(255) NOT NULL UNIQUE,
                        url VARCHAR(500) NOT NULL,
                        descricao LONGTEXT,
                        linguagem VARCHAR(100),
                        stars INT DEFAULT 0,
                        topics VARCHAR(500),
                        categoria VARCHAR(100) NOT NULL,
                        query VARCHAR(255) NOT NULL,
                        data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_categoria (categoria),
                        INDEX idx_query (query),
                        INDEX idx_data (data_insercao),
                        INDEX idx_nome (nome)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS varreduras (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        categoria VARCHAR(100) NOT NULL,
                        queries LONGTEXT NOT NULL,
                        quantidade_encontradas INT DEFAULT 0,
                        quantidade_novas INT DEFAULT 0,
                        quantidade_duplicadas INT DEFAULT 0,
                        tempo_execucao_segundos FLOAT,
                        data_varredura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ferramentas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE,
                        url TEXT NOT NULL,
                        descricao TEXT,
                        linguagem TEXT,
                        stars INTEGER DEFAULT 0,
                        topics TEXT,
                        categoria TEXT NOT NULL,
                        query TEXT NOT NULL,
                        data_insercao TEXT DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS varreduras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categoria TEXT NOT NULL,
                        queries TEXT NOT NULL,
                        quantidade_encontradas INTEGER DEFAULT 0,
                        quantidade_novas INTEGER DEFAULT 0,
                        quantidade_duplicadas INTEGER DEFAULT 0,
                        tempo_execucao_segundos REAL,
                        data_varredura TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ferramentas_categoria ON ferramentas(categoria)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ferramentas_query ON ferramentas(query)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ferramentas_data ON ferramentas(data_insercao)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ferramentas_nome ON ferramentas(nome)")

            if self.backend == "sqlite":
                self.connection.commit()

            cursor.close()
            logger.info(f"Tabelas prontas no backend {self.backend_label}")
            return True
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao criar tabelas: {exc}")
            return False

    def ferramenta_existe(self, nome: str, url: Optional[str] = None) -> bool:
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            if url:
                if self.backend == "mysql":
                    cursor.execute("SELECT id FROM ferramentas WHERE nome = %s OR url = %s LIMIT 1", (nome, url))
                else:
                    cursor.execute("SELECT id FROM ferramentas WHERE nome = ? OR url = ? LIMIT 1", (nome, url))
            else:
                if self.backend == "mysql":
                    cursor.execute("SELECT id FROM ferramentas WHERE nome = %s LIMIT 1", (nome,))
                else:
                    cursor.execute("SELECT id FROM ferramentas WHERE nome = ? LIMIT 1", (nome,))

            resultado = cursor.fetchone()
            cursor.close()
            return resultado is not None
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao verificar ferramenta: {exc}")
            return False

    def salvar_ferramenta(
        self,
        nome: str,
        url: str,
        descricao: str,
        linguagem: str,
        stars: int,
        topics: str,
        categoria: str,
        query: str,
    ) -> bool:
        if not self.is_connected:
            logger.error("Nao conectado ao banco de dados")
            return False

        if self.ferramenta_existe(nome, url):
            logger.info(f"Ferramenta '{nome}' ja existe no banco")
            return False

        try:
            cursor = self.connection.cursor()
            values = (nome, url, descricao, linguagem, stars, topics, categoria, query)

            if self.backend == "mysql":
                cursor.execute(
                    """
                    INSERT INTO ferramentas
                    (nome, url, descricao, linguagem, stars, topics, categoria, query)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO ferramentas
                    (nome, url, descricao, linguagem, stars, topics, categoria, query)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
                self.connection.commit()

            cursor.close()
            logger.info(f"Ferramenta '{nome}' salva no banco")
            return True
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao salvar ferramenta: {exc}")
            return False

    def obter_ferramenta(self, nome: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None

        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM ferramentas WHERE nome = %s", (nome,))
                resultado = cursor.fetchone()
                cursor.close()
                return resultado

            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM ferramentas WHERE nome = ?", (nome,))
            resultado = cursor.fetchone()
            cursor.close()
            return dict(resultado) if resultado else None
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao obter ferramenta: {exc}")
            return None

    def listar_por_categoria(self, categoria: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []

        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM ferramentas WHERE categoria = %s ORDER BY data_insercao DESC LIMIT %s", (categoria, limit))
                resultados = cursor.fetchall()
                cursor.close()
                return resultados

            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM ferramentas WHERE categoria = ? ORDER BY data_insercao DESC LIMIT ?", (categoria, limit))
            resultados = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return resultados
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao listar ferramentas: {exc}")
            return []

    def listar_por_query(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []

        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM ferramentas WHERE query = %s ORDER BY stars DESC LIMIT %s", (query, limit))
                resultados = cursor.fetchall()
                cursor.close()
                return resultados

            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM ferramentas WHERE query = ? ORDER BY stars DESC LIMIT ?", (query, limit))
            resultados = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return resultados
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao listar ferramentas: {exc}")
            return []

    def registrar_varredura(
        self,
        categoria: str,
        queries: str,
        quantidade_encontradas: int,
        quantidade_novas: int,
        quantidade_duplicadas: int,
        tempo_execucao: float,
    ) -> bool:
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            values = (categoria, queries, quantidade_encontradas, quantidade_novas, quantidade_duplicadas, tempo_execucao)

            if self.backend == "mysql":
                cursor.execute(
                    """
                    INSERT INTO varreduras
                    (categoria, queries, quantidade_encontradas, quantidade_novas, quantidade_duplicadas, tempo_execucao_segundos)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO varreduras
                    (categoria, queries, quantidade_encontradas, quantidade_novas, quantidade_duplicadas, tempo_execucao_segundos)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
                self.connection.commit()

            cursor.close()
            logger.info(f"Varredura registrada: {quantidade_novas} novas, {quantidade_duplicadas} duplicadas")
            return True
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao registrar varredura: {exc}")
            return False

    def obter_stats(self) -> Dict[str, Any]:
        if not self.is_connected:
            return {}

        try:
            cursor = self.connection.cursor()
            stats: Dict[str, Any] = {}

            cursor.execute("SELECT COUNT(*) as total FROM ferramentas")
            total_row = cursor.fetchone()
            if self.backend == "mysql":
                stats["total_ferramentas"] = total_row[0]
            else:
                stats["total_ferramentas"] = total_row["total"]

            cursor.execute(
                """
                SELECT categoria, COUNT(*) as quantidade
                FROM ferramentas
                GROUP BY categoria
                ORDER BY quantidade DESC
                """
            )
            if self.backend == "mysql":
                stats["por_categoria"] = [
                    {"categoria": row[0], "quantidade": row[1]}
                    for row in cursor.fetchall()
                ]
            else:
                stats["por_categoria"] = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT nome, url, stars
                FROM ferramentas
                ORDER BY stars DESC
                LIMIT 5
                """
            )
            if self.backend == "mysql":
                stats["top_stars"] = [
                    {"nome": row[0], "url": row[1], "stars": row[2]}
                    for row in cursor.fetchall()
                ]
            else:
                stats["top_stars"] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) as total FROM varreduras")
            scans_row = cursor.fetchone()
            if self.backend == "mysql":
                stats["total_varreduras"] = scans_row[0]
            else:
                stats["total_varreduras"] = scans_row["total"]

            cursor.close()
            return stats
        except (MySQLError, sqlite3.Error) as exc:
            logger.error(f"Erro ao obter stats: {exc}")
            return {}

    def disconnect(self):
        """Fecha a conexao com o backend atual."""
        if self.connection and self.is_connected:
            self.connection.close()
            backend = self.backend_label
            self.is_connected = False
            self.backend = "none"
            logger.info(f"Desconectado do backend {backend}")
