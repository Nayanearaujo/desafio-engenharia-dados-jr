"""
Orquestrador principal do pipeline em Arquitetura Medalha (Bronze -> Silver -> Gold).
Garante execucao idempotente e rastreabilidade via logging.
"""

import logging
import os
import sqlite3
from typing import Any

from database import conectar
from pipeline.bronze import PASTA_RAW_PADRAO, carregar_bronze
from pipeline.gerar_dados import SEMENTE_PADRAO, gerar_arquivos_raw
from pipeline.gold import PASTA_EXPORTS_PADRAO, construir_gold, exportar_camada_gold
from pipeline.qualidade import gerar_relatorio_qualidade
from pipeline.silver import processar_silver

logger = logging.getLogger(__name__)


def _configurar_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def run_pipeline(
    conn: sqlite3.Connection | None = None,
    pasta_raw: str = PASTA_RAW_PADRAO,
    pasta_exports: str = PASTA_EXPORTS_PADRAO,
    semente: int = SEMENTE_PADRAO,
    num_clientes: int = 200,
    num_pedidos: int = 5000,
    regerar_csv: bool = True,
) -> dict[str, Any]:
    """
    Executa o pipeline completo:
      1. Gera CSVs brutos em data/raw/ com Faker (semente fixa)
      2. Carrega camada Bronze (imutavel com _ingested_at e _source_file)
      3. Processa camada Silver (tipagem, FKs e quarentena silver_rejeitados)
      4. Gera relatorio de qualidade de dados
      5. Constroi views analiticas da camada Gold e exporta CSVs em exports/
    """
    _configurar_logging()
    fechar_ao_final = False
    if conn is None:
        conn = conectar()
        fechar_ao_final = True

    try:
        arquivos_esperados = [
            os.path.join(pasta_raw, arq)
            for arq in ("clientes.csv", "produtos.csv", "pedidos.csv", "itens_pedido.csv")
        ]
        if regerar_csv or not all(os.path.exists(p) for p in arquivos_esperados):
            gerados = gerar_arquivos_raw(
                pasta_destino=pasta_raw,
                semente=semente,
                num_clientes=num_clientes,
                num_pedidos=num_pedidos,
            )
        else:
            gerados = {}

        contagens_bronze = carregar_bronze(conn, pasta_raw=pasta_raw)
        metricas_silver = processar_silver(conn)
        resumo_qualidade = gerar_relatorio_qualidade(conn, pasta_exports=pasta_exports)
        construir_gold(conn)
        exportados_gold = exportar_camada_gold(conn, pasta_exports=pasta_exports)

        return {
            "raw": gerados,
            "bronze": contagens_bronze,
            "silver": metricas_silver,
            "qualidade": resumo_qualidade,
            "exports": exportados_gold,
        }
    finally:
        if fechar_ao_final:
            conn.close()
