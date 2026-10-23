"""
Modulo responsavel pela conexao com o SQLite e criacao do banco de dados.
"""

import os
import sqlite3

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_BANCO = os.path.join(_DIR_RAIZ, "loja_digital.db")

_DIR_SQL = os.path.join(_DIR_RAIZ, "sql")
_SCHEMA = os.path.join(_DIR_SQL, "schema.sql")
_SEED = os.path.join(_DIR_SQL, "seed.sql")


def conectar() -> sqlite3.Connection:
    """Abre e retorna uma conexao com o banco SQLite."""
    try:
        conn = sqlite3.connect(CAMINHO_BANCO)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as erro:
        print(f"[ERRO] Nao foi possivel conectar ao banco: {erro}")
        raise


def _executar_script(conn: sqlite3.Connection, caminho_sql: str) -> None:
    """Le e executa um arquivo .sql no banco."""
    try:
        with open(caminho_sql, "r", encoding="utf-8") as arquivo:
            script = arquivo.read()
        conn.executescript(script)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo SQL nao encontrado: {caminho_sql}")
        raise
    except sqlite3.Error as erro:
        print(f"[ERRO] Falha ao executar script SQL: {erro}")
        raise


def criar_banco() -> None:
    """Recria o banco de dados executando o schema.sql e o seed.sql."""
    if os.path.exists(CAMINHO_BANCO):
        os.remove(CAMINHO_BANCO)

    try:
        conn = conectar()
        print("Inicializando banco de dados...")
        _executar_script(conn, _SCHEMA)
        _executar_script(conn, _SEED)
        conn.close()
        print("Banco de dados pronto!\n")
    except Exception as erro:
        print(f"[ERRO] Falha ao criar o banco: {erro}")
        raise
