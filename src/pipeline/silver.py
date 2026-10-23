"""
Camada Silver: limpeza, tipagem, deduplicacao, validacao de integridade
e envio de registros invalidos para a quarentena (silver_rejeitados).
"""

import json
import logging
import os
import sqlite3
from typing import Any

from pipeline.qualidade import (
    validar_chave_duplicada,
    validar_data_iso,
    validar_email,
    validar_fk_existente,
    validar_inteiro_nao_negativo,
    validar_numero_positivo,
    validar_obrigatorios,
    validar_status_pedido,
)

logger = logging.getLogger(__name__)

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SQL_SCHEMA = os.path.join(_DIR_RAIZ, "sql", "schema.sql")


def _garantir_tabelas_silver(conn: sqlite3.Connection) -> None:
    """Garante que as tabelas Silver existam e limpa os dados anteriores de forma idempotente."""
    conn.execute("PRAGMA foreign_keys = OFF")
    with open(_SQL_SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.execute("PRAGMA foreign_keys = ON")


def _registrar_rejeitado(
    rejeitados: list[tuple[str, str, str]],
    tabela_origem: str,
    motivo: str,
    registro: dict[str, Any],
) -> None:
    dados_limpos = {
        k: v for k, v in registro.items() if not k.startswith("_")
    }
    rejeitados.append(
        (tabela_origem, motivo, json.dumps(dados_limpos, ensure_ascii=False))
    )


def processar_silver(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """
    Transforma os dados de bronze_* para as tabelas Silver (clientes, produtos,
    pedidos, itens_pedido) respeitando a ordem de chaves estrangeiras e isolando
    anomalias em silver_rejeitados.
    """
    _garantir_tabelas_silver(conn)

    rejeitados_batch: list[tuple[str, str, str]] = []
    metricas: dict[str, dict[str, int]] = {}

    # 1. CLIENTES
    rows_cli = [
        dict(r) for r in conn.execute("SELECT * FROM bronze_clientes").fetchall()
    ]
    clientes_validos: list[tuple[int, str, str, str, str]] = []
    ids_clientes: set[int] = set()
    emails_clientes: set[str] = set()
    rej_cli = 0

    for row in rows_cli:
        ok, motivo = validar_obrigatorios(
            row, ["id", "nome", "email", "cidade", "criado_em"]
        )
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_clientes", motivo or "nulo", row)
            rej_cli += 1
            continue

        ok, motivo = validar_chave_duplicada(row["id"], ids_clientes)
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_clientes", motivo or "id_invalido", row)
            rej_cli += 1
            continue

        ok, motivo = validar_email(row["email"], emails_clientes)
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_clientes", motivo or "email_invalido", row)
            rej_cli += 1
            continue

        ok, motivo = validar_data_iso(row["criado_em"], "criado_em")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_clientes", motivo or "data_invalida", row)
            rej_cli += 1
            continue

        cid = int(str(row["id"]).strip())
        email_limpo = str(row["email"]).strip().lower()
        ids_clientes.add(cid)
        emails_clientes.add(email_limpo)
        clientes_validos.append(
            (
                cid,
                str(row["nome"]).strip(),
                email_limpo,
                str(row["cidade"]).strip(),
                str(row["criado_em"]).strip(),
            )
        )

    conn.executemany(
        "INSERT INTO clientes (id, nome, email, cidade, criado_em) VALUES (?, ?, ?, ?, ?)",
        clientes_validos,
    )
    metricas["clientes"] = {
        "lidas": len(rows_cli),
        "validas": len(clientes_validos),
        "rejeitadas": rej_cli,
    }
    logger.info(
        "bronze_clientes: %d linhas -> silver clientes: %d validas, %d rejeitadas",
        len(rows_cli),
        len(clientes_validos),
        rej_cli,
    )

    # 2. PRODUTOS
    rows_prod = [
        dict(r) for r in conn.execute("SELECT * FROM bronze_produtos").fetchall()
    ]
    produtos_validos: list[tuple[int, str, str, float, int]] = []
    ids_produtos: set[int] = set()
    rej_prod = 0

    for row in rows_prod:
        ok, motivo = validar_obrigatorios(
            row, ["id", "nome", "categoria", "preco", "estoque"]
        )
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_produtos", motivo or "nulo", row)
            rej_prod += 1
            continue

        ok, motivo = validar_chave_duplicada(row["id"], ids_produtos)
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_produtos", motivo or "id_invalido", row)
            rej_prod += 1
            continue

        ok, motivo = validar_numero_positivo(row["preco"], "preco")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_produtos", motivo or "preco_invalido", row)
            rej_prod += 1
            continue

        ok, motivo = validar_inteiro_nao_negativo(row["estoque"], "estoque")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_produtos", motivo or "estoque_invalido", row)
            rej_prod += 1
            continue

        pr_id = int(str(row["id"]).strip())
        ids_produtos.add(pr_id)
        produtos_validos.append(
            (
                pr_id,
                str(row["nome"]).strip(),
                str(row["categoria"]).strip(),
                round(float(str(row["preco"]).strip()), 2),
                int(str(row["estoque"]).strip()),
            )
        )

    conn.executemany(
        "INSERT INTO produtos (id, nome, categoria, preco, estoque) VALUES (?, ?, ?, ?, ?)",
        produtos_validos,
    )
    metricas["produtos"] = {
        "lidas": len(rows_prod),
        "validas": len(produtos_validos),
        "rejeitadas": rej_prod,
    }
    logger.info(
        "bronze_produtos: %d linhas -> silver produtos: %d validas, %d rejeitadas",
        len(rows_prod),
        len(produtos_validos),
        rej_prod,
    )

    # 3. PEDIDOS
    rows_ped = [
        dict(r) for r in conn.execute("SELECT * FROM bronze_pedidos").fetchall()
    ]
    pedidos_validos: list[tuple[int, int, str, str]] = []
    ids_pedidos: set[int] = set()
    rej_ped = 0

    for row in rows_ped:
        ok, motivo = validar_obrigatorios(
            row, ["id", "cliente_id", "data_pedido", "status"]
        )
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_pedidos", motivo or "nulo", row)
            rej_ped += 1
            continue

        ok, motivo = validar_chave_duplicada(row["id"], ids_pedidos)
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_pedidos", motivo or "id_invalido", row)
            rej_ped += 1
            continue

        ok, motivo = validar_fk_existente(row["cliente_id"], ids_clientes, "cliente_id")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_pedidos", motivo or "fk_orfa", row)
            rej_ped += 1
            continue

        ok, motivo = validar_data_iso(row["data_pedido"], "data_pedido")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_pedidos", motivo or "data_invalida", row)
            rej_ped += 1
            continue

        ok, motivo = validar_status_pedido(row["status"])
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_pedidos", motivo or "status_invalido", row)
            rej_ped += 1
            continue

        pid = int(str(row["id"]).strip())
        cid = int(str(row["cliente_id"]).strip())
        ids_pedidos.add(pid)
        pedidos_validos.append(
            (
                pid,
                cid,
                str(row["data_pedido"]).strip(),
                str(row["status"]).strip().lower(),
            )
        )

    conn.executemany(
        "INSERT INTO pedidos (id, cliente_id, data_pedido, status) VALUES (?, ?, ?, ?)",
        pedidos_validos,
    )
    metricas["pedidos"] = {
        "lidas": len(rows_ped),
        "validas": len(pedidos_validos),
        "rejeitadas": rej_ped,
    }
    logger.info(
        "bronze_pedidos: %d linhas -> silver pedidos: %d validas, %d rejeitadas",
        len(rows_ped),
        len(pedidos_validos),
        rej_ped,
    )

    # 4. ITENS DE PEDIDO
    rows_itens = [
        dict(r) for r in conn.execute("SELECT * FROM bronze_itens_pedido").fetchall()
    ]
    itens_validos: list[tuple[int, int, int, int, float]] = []
    ids_itens: set[int] = set()
    rej_itens = 0

    for row in rows_itens:
        ok, motivo = validar_obrigatorios(
            row, ["id", "pedido_id", "produto_id", "quantidade", "preco_unit"]
        )
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "nulo", row)
            rej_itens += 1
            continue

        ok, motivo = validar_chave_duplicada(row["id"], ids_itens)
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "id_invalido", row)
            rej_itens += 1
            continue

        ok, motivo = validar_fk_existente(row["pedido_id"], ids_pedidos, "pedido_id")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "fk_orfa", row)
            rej_itens += 1
            continue

        ok, motivo = validar_fk_existente(row["produto_id"], ids_produtos, "produto_id")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "fk_orfa", row)
            rej_itens += 1
            continue

        ok, motivo = validar_numero_positivo(row["quantidade"], "quantidade")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "qtd_invalida", row)
            rej_itens += 1
            continue

        ok, motivo = validar_inteiro_nao_negativo(row["quantidade"], "quantidade")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "qtd_invalida", row)
            rej_itens += 1
            continue

        ok, motivo = validar_numero_positivo(row["preco_unit"], "preco_unit")
        if not ok:
            _registrar_rejeitado(rejeitados_batch, "bronze_itens_pedido", motivo or "preco_invalido", row)
            rej_itens += 1
            continue

        iid = int(str(row["id"]).strip())
        ped_id = int(str(row["pedido_id"]).strip())
        prod_id = int(str(row["produto_id"]).strip())
        qtd = int(str(row["quantidade"]).strip())
        preco_u = round(float(str(row["preco_unit"]).strip()), 2)

        ids_itens.add(iid)
        itens_validos.append((iid, ped_id, prod_id, qtd, preco_u))

    conn.executemany(
        "INSERT INTO itens_pedido (id, pedido_id, produto_id, quantidade, preco_unit) VALUES (?, ?, ?, ?, ?)",
        itens_validos,
    )
    metricas["itens_pedido"] = {
        "lidas": len(rows_itens),
        "validas": len(itens_validos),
        "rejeitadas": rej_itens,
    }
    logger.info(
        "bronze_itens_pedido: %d linhas -> silver itens_pedido: %d validas, %d rejeitadas",
        len(rows_itens),
        len(itens_validos),
        rej_itens,
    )

    conn.executemany(
        "INSERT INTO silver_rejeitados (tabela_origem, motivo, registro_raw) VALUES (?, ?, ?)",
        rejeitados_batch,
    )
    conn.commit()
    return metricas
