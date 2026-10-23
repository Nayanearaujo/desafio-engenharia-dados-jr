"""
database.py
-----------
Gerencia a conexão com o banco SQLite e a criação/reset do banco de dados.
Funções exportadas: conectar(), criar_banco(), CAMINHO_BANCO
"""

import sqlite3
import os

# Caminho do banco — fica na raiz do projeto, fora do src/
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_BANCO = os.path.join(_DIR_RAIZ, "loja_digital.db")

_DIR_SQL = os.path.join(_DIR_RAIZ, "sql")
_SCHEMA  = os.path.join(_DIR_SQL, "schema.sql")
_SEED    = os.path.join(_DIR_SQL, "seed.sql")


def conectar() -> sqlite3.Connection:
    """Abre e retorna uma conexão com o banco SQLite."""
    try:
        conn = sqlite3.connect(CAMINHO_BANCO)
        conn.row_factory = sqlite3.Row   # permite acessar colunas por nome
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as erro:
        print(f"[ERRO] Não foi possível conectar ao banco: {erro}")
        raise


def _executar_script(conn: sqlite3.Connection, caminho_sql: str) -> None:
    """Lê e executa um arquivo .sql no banco."""
    try:
        with open(caminho_sql, "r", encoding="utf-8") as arquivo:
            script = arquivo.read()
        conn.executescript(script)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo SQL não encontrado: {caminho_sql}")
        raise
    except sqlite3.Error as erro:
        print(f"[ERRO] Falha ao executar script SQL: {erro}")
        raise


def criar_banco() -> None:
    """
    Cria (ou recria) o banco do zero:
    1. Remove o arquivo .db existente, se houver.
    2. Executa o schema (tabelas + view).
    3. Executa o seed (dados de exemplo).
    """
    # Remove banco antigo para garantir estado limpo
    if os.path.exists(CAMINHO_BANCO):
        os.remove(CAMINHO_BANCO)

    try:
        conn = conectar()
        print("⚙️  Criando banco de dados...")
        _executar_script(conn, _SCHEMA)
        _executar_script(conn, _SEED)
        conn.close()
        print("✅  Banco criado com sucesso!\n")
    except Exception as erro:
        print(f"[ERRO] Falha ao criar o banco: {erro}")
        raise
