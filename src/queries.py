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

