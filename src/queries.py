"""
queries.py
----------
Todas as consultas SQL usadas nos relatórios do terminal.
Cada função recebe uma conexão aberta e retorna lista de sqlite3.Row.

Conceitos SQL cobertos:
  - JOIN (INNER JOIN entre 2 ou mais tabelas)
  - WHERE  (filtro por coluna)
  - GROUP BY + funções de agregação (COUNT, SUM, AVG, MAX)
  - VIEW   (resumo_pedidos — definida no schema.sql)
"""

import sqlite3
from typing import Any


def listar_produtos(conn: sqlite3.Connection) -> list[Any]:
    """Retorna todos os produtos com nome, categoria, preço e estoque."""
    cursor = conn.execute(
        """
        SELECT id, nome, categoria, preco, estoque
        FROM   produtos
        ORDER  BY categoria, nome
        """
    )
    return cursor.fetchall()


def filtrar_por_categoria(conn: sqlite3.Connection, categoria: str) -> list[Any]:
    """
    Retorna produtos de uma categoria específica.
    Usa: WHERE com parâmetro (evita SQL injection).
    """
    cursor = conn.execute(
        """
        SELECT id, nome, preco, estoque
        FROM   produtos
        WHERE  LOWER(categoria) = LOWER(?)
        ORDER  BY preco
        """,
        (categoria,),
    )
    return cursor.fetchall()


def listar_clientes(conn: sqlite3.Connection) -> list[Any]:
    """Retorna todos os clientes cadastrados."""
    cursor = conn.execute(
        """
        SELECT id, nome, email, cidade, criado_em
        FROM   clientes
        ORDER  BY nome
        """
    )
    return cursor.fetchall()


def resumo_por_cliente(conn: sqlite3.Connection) -> list[Any]:
    """
    Total gasto e número de pedidos por cliente.
    Usa: JOIN + GROUP BY + SUM + COUNT.
    Exclui pedidos cancelados.
    """
    cursor = conn.execute(
        """
        SELECT
            c.nome                                  AS cliente,
            c.cidade,
            COUNT(DISTINCT p.id)                    AS total_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS total_gasto
        FROM   clientes c
        JOIN   pedidos p        ON p.cliente_id  = c.id
        JOIN   itens_pedido ip  ON ip.pedido_id  = p.id
        WHERE  p.status != 'cancelado'
        GROUP  BY c.id, c.nome, c.cidade
        ORDER  BY total_gasto DESC
        """
    )
    return cursor.fetchall()


def produtos_mais_vendidos(conn: sqlite3.Connection) -> list[Any]:
    """
    Ranking dos produtos mais vendidos por quantidade.
    Usa: JOIN + GROUP BY + SUM (agregação) + ORDER BY.
    """
    cursor = conn.execute(
        """
        SELECT
            pr.nome                     AS produto,
            pr.categoria,
            SUM(ip.quantidade)          AS unidades_vendidas,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_total
        FROM   produtos pr
        JOIN   itens_pedido ip ON ip.produto_id = pr.id
        JOIN   pedidos p       ON p.id = ip.pedido_id
        WHERE  p.status != 'cancelado'
        GROUP  BY pr.id, pr.nome, pr.categoria
        ORDER  BY unidades_vendidas DESC
        """
    )
    return cursor.fetchall()


def pedidos_detalhados(conn: sqlite3.Connection) -> list[Any]:
    """
    Usa a VIEW resumo_pedidos (definida no schema.sql).
    Mostra todos os pedidos com total de itens e valor.
    """
    cursor = conn.execute(
        """
        SELECT *
        FROM   resumo_pedidos
        ORDER  BY data_pedido DESC
        """
    )
    return cursor.fetchall()


def faturamento_por_categoria(conn: sqlite3.Connection) -> list[Any]:
    """
    Receita total agrupada por categoria de produto.
    Usa: JOIN + GROUP BY + SUM + AVG.
    """
    cursor = conn.execute(
        """
        SELECT
            pr.categoria,
            COUNT(DISTINCT pr.id)               AS produtos_distintos,
            SUM(ip.quantidade)                  AS unidades_vendidas,
            ROUND(AVG(ip.preco_unit), 2)        AS ticket_medio,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_total
        FROM   produtos pr
        JOIN   itens_pedido ip ON ip.produto_id = pr.id
        JOIN   pedidos p       ON p.id = ip.pedido_id
        WHERE  p.status != 'cancelado'
        GROUP  BY pr.categoria
        ORDER  BY receita_total DESC
        """
    )
    return cursor.fetchall()
