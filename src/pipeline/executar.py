"""
Orquestrador principal do pipeline em Arquitetura Medalha (Bronze -> Silver -> Gold).
Garante execucao idempotente, separacao entre geracao/reprocessamento e auditoria em pipeline_execucoes.
"""

import logging
import os
import sqlite3
from datetime import UTC, datetime
from typing import Any

from config import (
    NUM_CLIENTES_PADRAO,
    NUM_PEDIDOS_PADRAO,
    PASTA_EXPORTS_PADRAO,
    PASTA_RAW_PADRAO,
    SEMENTE_PADRAO,
)
from database import conectar
from pipeline.bronze import carregar_bronze
from pipeline.gerar_dados import gerar_arquivos_raw
from pipeline.gold import construir_gold, exportar_camada_gold
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


def _registrar_execucao_pipeline(
    conn: sqlite3.Connection,
    inicio_iso: str,
    fim_iso: str,
    status: str,
    modo_geracao: str,
    total_bronze: int,
    total_silver: int,
    total_rejeitados: int,
) -> dict[str, Any]:
    """Registra metadados de rastreabilidade da execucao na tabela pipeline_execucoes."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_execucoes (
            run_id              INTEGER PRIMARY KEY AUTOINCREMENT,
            inicio_execucao     TEXT    NOT NULL,
            fim_execucao        TEXT    NOT NULL,
            status              TEXT    NOT NULL,
            modo_geracao        TEXT    NOT NULL DEFAULT 'regerado',
            registros_bronze    INTEGER NOT NULL DEFAULT 0,
            registros_silver    INTEGER NOT NULL DEFAULT 0,
            registros_rejeitados INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cursor = conn.execute(
        """
        INSERT INTO pipeline_execucoes (
            inicio_execucao,
            fim_execucao,
            status,
            modo_geracao,
            registros_bronze,
            registros_silver,
            registros_rejeitados
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            inicio_iso,
            fim_iso,
            status,
            modo_geracao,
            total_bronze,
            total_silver,
            total_rejeitados,
        ),
    )
    conn.commit()
    run_id = int(cursor.lastrowid)
    logger.info(
        "Execucao registrada em pipeline_execucoes (run_id=%d, status=%s, modo=%s)",
        run_id,
        status,
        modo_geracao,
    )
    return {
        "run_id": run_id,
        "inicio_execucao": inicio_iso,
        "fim_execucao": fim_iso,
        "status": status,
        "modo_geracao": modo_geracao,
        "registros_bronze": total_bronze,
        "registros_silver": total_silver,
        "registros_rejeitados": total_rejeitados,
    }


def run_pipeline(
    conn: sqlite3.Connection | None = None,
    pasta_raw: str = PASTA_RAW_PADRAO,
    pasta_exports: str = PASTA_EXPORTS_PADRAO,
    semente: int = SEMENTE_PADRAO,
    num_clientes: int = NUM_CLIENTES_PADRAO,
    num_pedidos: int = NUM_PEDIDOS_PADRAO,
    regerar_csv: bool = True,
) -> dict[str, Any]:
    """
    Executa o pipeline completo:
      1. Gera CSVs brutos em data/raw/ com Faker (se regerar_csv=True ou ausentes)
      2. Carrega camada Bronze (imutavel com _ingested_at e _source_file)
      3. Processa camada Silver (tipagem, FKs e quarentena silver_rejeitados)
      4. Gera relatorio de qualidade de dados
      5. Constroi views analiticas da camada Gold e exporta CSVs em exports/
      6. Persiste metadados da execucao em pipeline_execucoes
    """
    _configurar_logging()
    inicio_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
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
            modo_geracao = "regerado"
        else:
            gerados = {}
            modo_geracao = "reprocessado"

        contagens_bronze = carregar_bronze(conn, pasta_raw=pasta_raw)
        metricas_silver = processar_silver(conn)
        resumo_qualidade = gerar_relatorio_qualidade(conn, pasta_exports=pasta_exports)
        construir_gold(conn)
        exportados_gold = exportar_camada_gold(conn, pasta_exports=pasta_exports)

        fim_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        total_bronze = sum(contagens_bronze.values())
        total_silver = sum(m["validas"] for m in metricas_silver.values())
        total_rejeitados = sum(m["rejeitadas"] for m in metricas_silver.values())

        execucao_info = _registrar_execucao_pipeline(
            conn=conn,
            inicio_iso=inicio_iso,
            fim_iso=fim_iso,
            status="sucesso",
            modo_geracao=modo_geracao,
            total_bronze=total_bronze,
            total_silver=total_silver,
            total_rejeitados=total_rejeitados,
        )

        return {
            "raw": gerados,
            "bronze": contagens_bronze,
            "silver": metricas_silver,
            "qualidade": resumo_qualidade,
            "exports": exportados_gold,
            "execucao": execucao_info,
        }
    finally:
        if fechar_ao_final:
            conn.close()
