"""
Modulo de gerenciamento de banco de dados MySQL.
Salva, verifica e gerencia ferramentas de seguranca descobertas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql = None
    Error = Exception

logger = logging.getLogger(__name__)


class MySQLDatabase:
    """Gerenciador de banco de dados MySQL para armazenar ferramentas OSINT."""

    def __init__(self, host: str, user: str, password: str, database: str = "osint_tools"):
        """
        Inicializa conexao com o banco de dados.
        
        Args:
            host: Endereco do servidor MySQL
            user: Usuario do MySQL
            password: Senha do usuario
            database: Nome do banco de dados
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.is_connected = False

    def connect(self) -> bool:
        """
        Estabelece conexao com o MySQL.
        
        Returns:
            True se conectou com sucesso, False caso contrario
        """
        if not mysql:
            logger.error("mysql-connector-python nao instalado. Instale com: pip install mysql-connector-python")
            return False

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            self.is_connected = True
            logger.info(f"Conectado ao MySQL: {self.host}/{self.database}")
            return True
        except Error as e:
            logger.error(f"Erro ao conectar ao MySQL: {e}")
            self.is_connected = False
            return False

    def create_tables(self) -> bool:
        """
        Cria as tabelas necessarias se nao existirem.
        
        Returns:
            True se criou ou ja existem, False se erro
        """
        if not self.is_connected:
            logger.error("Nao conectado ao banco de dados")
            return False

        try:
            cursor = self.connection.cursor()

            # Tabela de ferramentas
            create_tools_table = """
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

            # Tabela de varreduras
            create_scans_table = """
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

            cursor.execute(create_tools_table)
            cursor.execute(create_scans_table)
            cursor.close()

            logger.info("Tabelas criadas ou ja existem")
            return True
        except Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            return False

    def ferramenta_existe(self, nome: str, url: Optional[str] = None) -> bool:
        """
        Verifica se uma ferramenta ja existe no banco.
        
        Args:
            nome: Nome da ferramenta
            url: URL do repositorio (opcional)
            
        Returns:
            True se existe, False caso contrario
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor(dictionary=True)
            if url:
                cursor.execute(
                    "SELECT id FROM ferramentas WHERE nome = %s OR url = %s LIMIT 1",
                    (nome, url),
                )
            else:
                cursor.execute("SELECT id FROM ferramentas WHERE nome = %s LIMIT 1", (nome,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado is not None
        except Error as e:
            logger.error(f"Erro ao verificar ferramenta: {e}")
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
        query: str
    ) -> bool:
        """
        Salva uma ferramenta no banco de dados.
        
        Args:
            nome: Nome da ferramenta
            url: URL do repositorio
            descricao: Descricao da ferramenta
            linguagem: Linguagem de programacao
            stars: Numero de stars
            topics: Topicos/tags
            categoria: Categoria de busca
            query: Query utilizada
            
        Returns:
            True se salvou com sucesso, False caso contrario
        """
        if not self.is_connected:
            logger.error("Nao conectado ao banco de dados")
            return False

        # Verifica duplicata
        if self.ferramenta_existe(nome, url):
            logger.info(f"Ferramenta '{nome}' ja existe no banco")
            return False

        try:
            cursor = self.connection.cursor()
            sql = """
            INSERT INTO ferramentas 
            (nome, url, descricao, linguagem, stars, topics, categoria, query)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (nome, url, descricao, linguagem, stars, topics, categoria, query)
            cursor.execute(sql, values)
            cursor.close()

            logger.info(f"Ferramenta '{nome}' salva no banco")
            return True
        except Error as e:
            logger.error(f"Erro ao salvar ferramenta: {e}")
            return False

    def obter_ferramenta(self, nome: str) -> Optional[Dict[str, Any]]:
        """
        Obtem informacoes de uma ferramenta.
        
        Args:
            nome: Nome da ferramenta
            
        Returns:
            Dicionario com dados da ferramenta ou None
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM ferramentas WHERE nome = %s", (nome,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado
        except Error as e:
            logger.error(f"Erro ao obter ferramenta: {e}")
            return None

    def listar_por_categoria(self, categoria: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lista ferramentas por categoria.
        
        Args:
            categoria: Nome da categoria
            limit: Limite de resultados
            
        Returns:
            Lista de ferramentas
        """
        if not self.is_connected:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            sql = "SELECT * FROM ferramentas WHERE categoria = %s ORDER BY data_insercao DESC LIMIT %s"
            cursor.execute(sql, (categoria, limit))
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except Error as e:
            logger.error(f"Erro ao listar ferramentas: {e}")
            return []

    def listar_por_query(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lista ferramentas encontradas por uma query especifica.
        
        Args:
            query: Query de busca
            limit: Limite de resultados
            
        Returns:
            Lista de ferramentas
        """
        if not self.is_connected:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            sql = "SELECT * FROM ferramentas WHERE query = %s ORDER BY stars DESC LIMIT %s"
            cursor.execute(sql, (query, limit))
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except Error as e:
            logger.error(f"Erro ao listar ferramentas: {e}")
            return []

    def registrar_varredura(
        self,
        categoria: str,
        queries: str,
        quantidade_encontradas: int,
        quantidade_novas: int,
        quantidade_duplicadas: int,
        tempo_execucao: float
    ) -> bool:
        """
        Registra uma varredura realizada.
        
        Args:
            categoria: Categoria de busca
            queries: Queries utilizadas (separadas por virgula)
            quantidade_encontradas: Total de ferramentas encontradas
            quantidade_novas: Quantidade de ferramentas novas
            quantidade_duplicadas: Quantidade de duplicatas
            tempo_execucao: Tempo em segundos
            
        Returns:
            True se registrou com sucesso
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            sql = """
            INSERT INTO varreduras 
            (categoria, queries, quantidade_encontradas, quantidade_novas, quantidade_duplicadas, tempo_execucao_segundos)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (categoria, queries, quantidade_encontradas, quantidade_novas, quantidade_duplicadas, tempo_execucao)
            cursor.execute(sql, values)
            cursor.close()

            logger.info(f"Varredura registrada: {quantidade_novas} novas, {quantidade_duplicadas} duplicadas")
            return True
        except Error as e:
            logger.error(f"Erro ao registrar varredura: {e}")
            return False

    def obter_stats(self) -> Dict[str, Any]:
        """
        Obtem estatisticas do banco de dados.
        
        Returns:
            Dicionario com estatisticas
        """
        if not self.is_connected:
            return {}

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            stats = {}
            
            # Total de ferramentas
            cursor.execute("SELECT COUNT(*) as total FROM ferramentas")
            stats['total_ferramentas'] = cursor.fetchone()['total']
            
            # Ferramentas por categoria
            cursor.execute("""
            SELECT categoria, COUNT(*) as quantidade 
            FROM ferramentas 
            GROUP BY categoria 
            ORDER BY quantidade DESC
            """)
            stats['por_categoria'] = cursor.fetchall()
            
            # Top 5 mais streladas
            cursor.execute("""
            SELECT nome, url, stars 
            FROM ferramentas 
            ORDER BY stars DESC 
            LIMIT 5
            """)
            stats['top_stars'] = cursor.fetchall()
            
            # Varreduras totais
            cursor.execute("SELECT COUNT(*) as total FROM varreduras")
            stats['total_varreduras'] = cursor.fetchone()['total']
            
            cursor.close()
            return stats
        except Error as e:
            logger.error(f"Erro ao obter stats: {e}")
            return {}

    def disconnect(self):
        """Fecha a conexao com o banco de dados."""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("Desconectado do MySQL")
