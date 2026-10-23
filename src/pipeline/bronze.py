"""
Camada Bronze: ingestao bruta dos arquivos CSV sem alteracao dos dados originais.
Adiciona apenas metadados de auditoria (_ingested_at e _source_file).
"""

import csv
import logging
import os
import sqlite3
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SQL_BRONZE = os.path.join(_DIR_RAIZ, "sql", "bronze.sql")
PASTA_RAW_PADRAO = os.path.join(_DIR_RAIZ, "data", "raw")


def carregar_bronze(
    conn: sqlite3.Connection, pasta_raw: str = PASTA_RAW_PADRAO
) -> dict[str, int]:
    """
    Recria a estrutura da camada Bronze e carrega os CSVs brutos de data/raw/.
    Retorna a contagem de registros ingeridos por tabela.
    """
    with open(_SQL_BRONZE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    instante_ingestao = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    mapeamento = [
        (
            "bronze_clientes",
            "clientes.csv",
            ["id", "nome", "email", "cidade", "criado_em"],
        ),
        (
            "bronze_produtos",
            "produtos.csv",
            ["id", "nome", "categoria", "preco", "estoque"],
        ),
        (
            "bronze_pedidos",
            "pedidos.csv",
            ["id", "cliente_id", "data_pedido", "status"],
        ),
        (
            "bronze_itens_pedido",
            "itens_pedido.csv",
            ["id", "pedido_id", "produto_id", "quantidade", "preco_unit"],
        ),
    ]

    contagens: dict[str, int] = {}

    for tabela, arquivo_csv, colunas in mapeamento:
        caminho = os.path.join(pasta_raw, arquivo_csv)
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo bruto nao encontrado: {caminho}")

        with open(caminho, "r", encoding="utf-8") as f:
            leitor = csv.DictReader(f)
            registros = [
                tuple(row.get(col, "") for col in colunas)
                + (instante_ingestao, arquivo_csv)
                for row in leitor
            ]

        placeholders = ", ".join(["?"] * (len(colunas) + 2))
        cols_sql = ", ".join(colunas + ["_ingested_at", "_source_file"])
        conn.executemany(
            f"INSERT INTO {tabela} ({cols_sql}) VALUES ({placeholders})",
            registros,
        )
        conn.commit()
        contagens[tabela] = len(registros)
        logger.info("Camada Bronze carregada: %s (%d linhas)", tabela, len(registros))

    return contagens
