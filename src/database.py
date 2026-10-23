"""
Modulo responsavel pela conexao com o SQLite e criacao do banco de dados.
"""

import os
import sqlite3

from config import CAMINHO_BANCO, DIR_SQL

_DIR_SQL = DIR_SQL
_BRONZE = os.path.join(_DIR_SQL, "bronze.sql")
_SCHEMA = os.path.join(_DIR_SQL, "schema.sql")
_SEED = os.path.join(_DIR_SQL, "seed.sql")
_GOLD = os.path.join(_DIR_SQL, "gold.sql")


def conectar(caminho_banco: str | None = None) -> sqlite3.Connection:
    """Abre e retorna uma conexao com o banco SQLite com chaves estrangeiras ativas."""
    alvo = caminho_banco or CAMINHO_BANCO
    try:
        conn = sqlite3.connect(alvo)
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


def criar_banco(caminho_banco: str | None = None) -> None:
    """Recria o banco de demonstracao executando bronze.sql, schema.sql, seed.sql e gold.sql."""
    alvo = caminho_banco or CAMINHO_BANCO
    if alvo != ":memory:" and os.path.exists(alvo):
        os.remove(alvo)

    try:
        conn = conectar(alvo)
        print("Inicializando banco de dados...")
        if os.path.exists(_BRONZE):
            _executar_script(conn, _BRONZE)
        _executar_script(conn, _SCHEMA)
        _executar_script(conn, _SEED)
        if os.path.exists(_GOLD):
            _executar_script(conn, _GOLD)
        conn.close()
        print("Banco de dados pronto!\n")
    except Exception as erro:
        print(f"[ERRO] Falha ao criar o banco: {erro}")
        raise
