"""
queries.py
----------
Todas as consultas SQL usadas nos relatórios do terminal.
Cada função recebe uma conexão aberta e retorna lista de sqlite3.Row.

Conceitos SQL cobertos:
  - SELECT, FROM, ORDER BY          (módulo 02)
  - WHERE com parâmetro             (módulo 03)
  - LOWER()                         (módulo 04)
  - date('now')                     (módulo 05)
  - COUNT, SUM, AVG                 (módulo 08)
  - GROUP BY                        (módulo 09)
  - HAVING                          (módulo 09) ← clientes_acima_de_meta()
  - INNER JOIN (3+ tabelas)         (módulo 10)
  - Subconsulta (subquery)          (módulo 12) ← produtos_acima_da_media()
  - CTE (WITH)                      (módulo 14) ← desempenho_produtos_cte()
  - CASE WHEN                       (módulo 07) ← desempenho_produtos_cte()
  - VIEW                            (schema.sql)
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


def clientes_acima_de_meta(conn: sqlite3.Connection, meta: float = 200.0) -> list[Any]:
    """
    Clientes que gastaram ACIMA de um valor mínimo (padrão: R$ 200,00).

    Usa: JOIN + GROUP BY + SUM + HAVING
    ---------------------------------
    Diferença entre WHERE e HAVING:
      - WHERE filtra ANTES do agrupamento (linha por linha)
      - HAVING filtra DEPOIS do GROUP BY (sobre o resultado agregado)
    Não dá para usar WHERE para filtrar o resultado de SUM().
    Módulo 09 da Trilha SQL.
    """
    cursor = conn.execute(
        """
        SELECT
            c.nome                                       AS cliente,
            c.email,
            c.cidade,
            COUNT(DISTINCT p.id)                         AS total_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS total_gasto
        FROM   clientes c
        JOIN   pedidos p       ON p.cliente_id  = c.id
        JOIN   itens_pedido ip ON ip.pedido_id  = p.id
        WHERE  p.status != 'cancelado'
        GROUP  BY c.id, c.nome, c.email, c.cidade
        HAVING SUM(ip.quantidade * ip.preco_unit) > ?
        ORDER  BY total_gasto DESC
        """,
        (meta,),
    )
    return cursor.fetchall()


def produtos_acima_da_media(conn: sqlite3.Connection) -> list[Any]:
    """
    Produtos cujo preço está ACIMA da média geral de preços.

    Usa: subconsulta (subquery) no WHERE
    ------------------------------------
    A subquery calcula a média primeiro; a query externa usa esse
    resultado como filtro — tudo numa única instrução SQL.
    Módulo 12 da Trilha SQL.
    """
    cursor = conn.execute(
        """
        SELECT
            id,
            nome,
            categoria,
            preco,
            ROUND(preco - (SELECT AVG(preco) FROM produtos), 2) AS diferenca_da_media
        FROM   produtos
        WHERE  preco > (SELECT AVG(preco) FROM produtos)
        ORDER  BY preco DESC
        """
    )
    return cursor.fetchall()


def desempenho_produtos_cte(conn: sqlite3.Connection) -> list[Any]:
    """
    Classifica cada produto pelo desempenho de vendas.

    Usa:
      - CTE (WITH)       → módulo 14: divide o cálculo em etapas legíveis
      - CASE WHEN        → módulo 07: rotula o desempenho por faixa de receita
      - COALESCE         → módulo 06: trata produtos sem venda (NULL → 0)
      - LEFT JOIN        → módulo 10: inclui produtos sem nenhuma venda

    Fluxo:
      1. CTE calcula receita e unidades por produto (LEFT JOIN para incluir todos)
      2. Query principal aplica CASE WHEN para classificar:
           'Alto'  → receita > R$ 400
           'Médio' → R$ 100 a R$ 400
           'Baixo' → abaixo de R$ 100
    """
    cursor = conn.execute(
        """
        WITH vendas_por_produto AS (
            SELECT
                pr.id,
                pr.nome                                                   AS produto,
                pr.categoria,
                pr.preco                                                  AS preco_unitario,
                COALESCE(SUM(ip.quantidade), 0)                           AS unidades_vendidas,
                ROUND(COALESCE(SUM(ip.quantidade * ip.preco_unit), 0), 2) AS receita_total
            FROM   produtos pr
            LEFT JOIN itens_pedido ip ON ip.produto_id = pr.id
            LEFT JOIN pedidos p       ON p.id = ip.pedido_id
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
                WHEN receita_total > 400  THEN 'Alto'
                WHEN receita_total >= 100 THEN 'Medio'
                ELSE                           'Baixo'
            END AS desempenho
        FROM   vendas_por_produto
        ORDER  BY receita_total DESC
        """
    )
    return cursor.fetchall()
