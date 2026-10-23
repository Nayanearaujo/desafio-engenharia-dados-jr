"""
Consultas SQL utilizadas nos relatorios do sistema.
"""

import sqlite3
from typing import Any


def listar_produtos(conn: sqlite3.Connection) -> list[Any]:
    """Retorna todos os produtos cadastrados."""
    cursor = conn.execute(
        """
        SELECT id, nome, categoria, preco, estoque
        FROM produtos
        ORDER BY categoria, nome
        """
    )
    return cursor.fetchall()


def filtrar_por_categoria(conn: sqlite3.Connection, categoria: str) -> list[Any]:
    """Filtra produtos por categoria (case-insensitive)."""
    cursor = conn.execute(
        """
        SELECT id, nome, preco, estoque
        FROM produtos
        WHERE LOWER(categoria) = LOWER(?)
        ORDER BY preco
        """,
        (categoria,),
    )
    return cursor.fetchall()


def listar_clientes(conn: sqlite3.Connection) -> list[Any]:
    """Retorna todos os clientes ordenados por nome."""
    cursor = conn.execute(
        """
        SELECT id, nome, email, cidade, criado_em
        FROM clientes
        ORDER BY nome
        """
    )
    return cursor.fetchall()


def resumo_por_cliente(conn: sqlite3.Connection) -> list[Any]:
    """Total gasto e quantidade de pedidos por cliente (ignora cancelados)."""
    cursor = conn.execute(
        """
        SELECT
            c.nome AS cliente,
            c.cidade,
            COUNT(DISTINCT p.id) AS total_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS total_gasto
        FROM clientes c
        JOIN pedidos p ON p.cliente_id = c.id
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        WHERE p.status != 'cancelado'
        GROUP BY c.id, c.nome, c.cidade
        ORDER BY total_gasto DESC
        """
    )
    return cursor.fetchall()


def produtos_mais_vendidos(conn: sqlite3.Connection) -> list[Any]:
    """Ranking de produtos por volume de vendas e receita."""
    cursor = conn.execute(
        """
        SELECT
            pr.nome AS produto,
            pr.categoria,
            SUM(ip.quantidade) AS unidades_vendidas,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_total
        FROM produtos pr
        JOIN itens_pedido ip ON ip.produto_id = pr.id
        JOIN pedidos p ON p.id = ip.pedido_id
        WHERE p.status != 'cancelado'
        GROUP BY pr.id, pr.nome, pr.categoria
        ORDER BY unidades_vendidas DESC
        """
    )
    return cursor.fetchall()


def pedidos_detalhados(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a view resumo_pedidos com os dados consolidados de cada pedido."""
    cursor = conn.execute(
        """
        SELECT *
        FROM resumo_pedidos
        ORDER BY data_pedido DESC
        """
    )
    return cursor.fetchall()


def faturamento_por_categoria(conn: sqlite3.Connection) -> list[Any]:
    """Agrupa vendas, ticket medio e receita por categoria de produto."""
    cursor = conn.execute(
        """
        SELECT
            pr.categoria,
            COUNT(DISTINCT pr.id) AS produtos_distintos,
            SUM(ip.quantidade) AS unidades_vendidas,
            ROUND(AVG(ip.preco_unit), 2) AS ticket_medio,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_total
        FROM produtos pr
        JOIN itens_pedido ip ON ip.produto_id = pr.id
        JOIN pedidos p ON p.id = ip.pedido_id
        WHERE p.status != 'cancelado'
        GROUP BY pr.categoria
        ORDER BY receita_total DESC
        """
    )
    return cursor.fetchall()


def clientes_acima_de_meta(conn: sqlite3.Connection, meta: float = 200.0) -> list[Any]:
    """Filtra clientes cujo gasto total supera a meta informada (usando HAVING)."""
    cursor = conn.execute(
        """
        SELECT
            c.nome AS cliente,
            c.email,
            c.cidade,
            COUNT(DISTINCT p.id) AS total_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS total_gasto
        FROM clientes c
        JOIN pedidos p ON p.cliente_id = c.id
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        WHERE p.status != 'cancelado'
        GROUP BY c.id, c.nome, c.email, c.cidade
        HAVING SUM(ip.quantidade * ip.preco_unit) > ?
        ORDER BY total_gasto DESC
        """,
        (meta,),
    )
    return cursor.fetchall()


def produtos_acima_da_media(conn: sqlite3.Connection) -> list[Any]:
    """Lista produtos com preco acima da media geral usando subconsulta."""
    cursor = conn.execute(
        """
        SELECT
            id,
            nome,
            categoria,
            preco,
            ROUND(preco - (SELECT AVG(preco) FROM produtos), 2) AS diferenca_da_media
        FROM produtos
        WHERE preco > (SELECT AVG(preco) FROM produtos)
        ORDER BY preco DESC
        """
    )
    return cursor.fetchall()


def desempenho_produtos_cte(conn: sqlite3.Connection) -> list[Any]:
    """Classifica os produtos em faixas de receita usando CTE e CASE WHEN."""
    cursor = conn.execute(
        """
        WITH vendas_por_produto AS (
            SELECT
                pr.id,
                pr.nome AS produto,
                pr.categoria,
                pr.preco AS preco_unitario,
                COALESCE(SUM(ip.quantidade), 0) AS unidades_vendidas,
                ROUND(COALESCE(SUM(ip.quantidade * ip.preco_unit), 0), 2) AS receita_total
            FROM produtos pr
            LEFT JOIN itens_pedido ip ON ip.produto_id = pr.id
            LEFT JOIN pedidos p ON p.id = ip.pedido_id
                               AND p.status != 'cancelado'
            GROUP BY pr.id, pr.nome, pr.categoria, pr.preco
        )
        SELECT
            produto,
            categoria,
            preco_unitario,
            unidades_vendidas,
            receita_total,
            CASE
                WHEN receita_total > 400 THEN 'Alto'
                WHEN receita_total >= 100 THEN 'Medio'
                ELSE 'Baixo'
            END AS desempenho
        FROM vendas_por_produto
        ORDER BY receita_total DESC
        """
    )
    return cursor.fetchall()


def inserir_produto(
    conn: sqlite3.Connection, nome: str, categoria: str, preco: float, estoque: int
) -> int:
    """Insere um novo produto no banco e retorna o ID gerado."""
    cursor = conn.execute(
        """
        INSERT INTO produtos (nome, categoria, preco, estoque)
        VALUES (?, ?, ?, ?)
        """,
        (nome, categoria, preco, estoque),
    )
    conn.commit()
    return int(cursor.lastrowid)


def calcular_kpis_executivos(conn: sqlite3.Connection) -> Any:
    """Calcula os principais KPIs executivos de vendas, ticket medio, LTV e conversao."""
    cursor = conn.execute(
        """
        WITH totais_pedidos AS (
            SELECT
                p.id AS pedido_id,
                p.cliente_id,
                p.status,
                SUM(ip.quantidade * ip.preco_unit) AS valor_pedido
            FROM pedidos p
            JOIN itens_pedido ip ON ip.pedido_id = p.id
            GROUP BY p.id, p.cliente_id, p.status
        )
        SELECT
            COUNT(pedido_id) AS total_pedidos,
            SUM(CASE WHEN status = 'pago' THEN 1 ELSE 0 END) AS pedidos_pagos,
            ROUND(SUM(CASE WHEN status = 'pago' THEN valor_pedido ELSE 0 END), 2) AS receita_paga,
            ROUND(SUM(CASE WHEN status = 'pendente' THEN valor_pedido ELSE 0 END), 2) AS receita_pendente,
            ROUND(AVG(CASE WHEN status = 'pago' THEN valor_pedido END), 2) AS ticket_medio_pedido,
            ROUND(
                SUM(CASE WHEN status = 'pago' THEN valor_pedido ELSE 0 END)
                / NULLIF(COUNT(DISTINCT CASE WHEN status = 'pago' THEN cliente_id END), 0),
                2
            ) AS ltv_medio_cliente,
            ROUND(
                100.0 * SUM(CASE WHEN status = 'pago' THEN 1 ELSE 0 END) / COUNT(pedido_id),
                1
            ) AS taxa_conversao_pct,
            ROUND(
                100.0 * SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) / COUNT(pedido_id),
                1
            ) AS taxa_cancelamento_pct
        FROM totais_pedidos
        """
    )
    return cursor.fetchone()


def ranking_window_function(conn: sqlite3.Connection) -> list[Any]:
    """Calcula ranking e participacao percentual (share) usando Window Functions (RANK e SUM OVER)."""
    cursor = conn.execute(
        """
        WITH receita_produtos AS (
            SELECT
                pr.nome AS produto,
                pr.categoria,
                COALESCE(SUM(ip.quantidade), 0) AS unidades,
                ROUND(COALESCE(SUM(ip.quantidade * ip.preco_unit), 0), 2) AS receita
            FROM produtos pr
            LEFT JOIN itens_pedido ip ON ip.produto_id = pr.id
            LEFT JOIN pedidos p ON p.id = ip.pedido_id AND p.status != 'cancelado'
            GROUP BY pr.id, pr.nome, pr.categoria
        )
        SELECT
            RANK() OVER (ORDER BY receita DESC) AS posicao_ranking,
            produto,
            categoria,
            unidades,
            receita,
            ROUND(100.0 * receita / SUM(receita) OVER (), 1) AS share_receita_pct,
            ROUND(
                100.0 * SUM(receita) OVER (ORDER BY receita DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                / SUM(receita) OVER (),
                1
            ) AS pareto_acumulado_pct
        FROM receita_produtos
        ORDER BY posicao_ranking
        """
    )
    return cursor.fetchall()


def receita_mensal_mom(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a view gold_receita_mensal com crescimento MoM (LAG) e media movel 3M."""
    cursor = conn.execute("SELECT * FROM gold_receita_mensal ORDER BY mes")
    return cursor.fetchall()


def segmentacao_rfm(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a view gold_rfm_clientes com scores R, F, M e segmento atribuido."""
    cursor = conn.execute("SELECT * FROM gold_rfm_clientes ORDER BY valor_monetario DESC")
    return cursor.fetchall()


def resumo_segmentos_rfm(conn: sqlite3.Connection) -> list[Any]:
    """Agrega contagem de clientes, frequencia media e receita total por segmento RFM."""
    cursor = conn.execute(
        """
        SELECT
            segmento_rfm,
            COUNT(cliente_id) AS total_clientes,
            ROUND(AVG(recencia_dias), 1) AS recencia_media_dias,
            ROUND(AVG(frequencia_pedidos), 1) AS frequencia_media,
            ROUND(SUM(valor_monetario), 2) AS receita_segmento,
            ROUND(100.0 * SUM(valor_monetario) / NULLIF(SUM(SUM(valor_monetario)) OVER (), 0), 1) AS share_receita_pct
        FROM gold_rfm_clientes
        GROUP BY segmento_rfm
        ORDER BY receita_segmento DESC
        """
    )
    return cursor.fetchall()


def retencao_coorte(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a matriz de retencao por coorte mensal na view gold_coorte_retencao."""
    cursor = conn.execute(
        "SELECT * FROM gold_coorte_retencao ORDER BY coorte_mes, indice_mes"
    )
    return cursor.fetchall()


def taxa_recompra_global(conn: sqlite3.Connection) -> Any:
    """Consulta a taxa de recompra global na view gold_taxa_recompra."""
    cursor = conn.execute("SELECT * FROM gold_taxa_recompra")
    return cursor.fetchone()


def cancelamento_categoria_mes(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a taxa de cancelamento e receita perdida por categoria e mes."""
    cursor = conn.execute(
        "SELECT * FROM gold_cancelamento_categoria_mes ORDER BY mes DESC, taxa_cancelamento_pct DESC"
    )
    return cursor.fetchall()


def resumo_qualidade_dados(conn: sqlite3.Connection) -> list[Any]:
    """Consulta a contagem de registros rejeitados na camada Silver por tabela e motivo."""
    cursor = conn.execute(
        "SELECT * FROM gold_qualidade_resumo ORDER BY total_rejeitados DESC, tabela_origem"
    )
    return cursor.fetchall()



