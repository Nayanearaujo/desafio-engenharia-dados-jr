"""
test_queries.py
---------------
Testes unitários automatizados com pytest.
Cria um banco SQLite em memória (:memory:), executa schema.sql e seed.sql,
e valida todas as consultas SQL do módulo queries.py.

Como rodar:
    pytest -v
"""

import os
import sqlite3
import sys
import pytest

# Adiciona src/ ao path para importar os módulos do projeto
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_RAIZ, "src"))

import queries  # noqa: E402

_DIR_SQL = os.path.join(_DIR_RAIZ, "sql")


@pytest.fixture
def conn():
    """Cria e popula um banco SQLite em memória isolado para cada teste."""
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    for nome_arquivo in ("schema.sql", "seed.sql"):
        caminho = os.path.join(_DIR_SQL, nome_arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            conexao.executescript(f.read())

    yield conexao
    conexao.close()


def test_listar_produtos_retorna_todos(conn):
    """Deve retornar os 7 produtos cadastrados no seed."""
    produtos = queries.listar_produtos(conn)
    assert len(produtos) >= 5
    assert len(produtos) == 7
    assert "nome" in produtos[0].keys()
    assert "preco" in produtos[0].keys()


def test_filtrar_por_categoria_existente(conn):
    """Deve filtrar corretamente os produtos da categoria 'Curso' (case-insensitive)."""
    cursos = queries.filtrar_por_categoria(conn, "curso")
    assert len(cursos) == 4
    nomes = [c["nome"] for c in cursos]
    assert "Python do Zero ao Avançado" in nomes


def test_filtrar_por_categoria_inexistente(conn):
    """Deve retornar lista vazia para categoria que não existe."""
    resultado = queries.filtrar_por_categoria(conn, "Hardware")
    assert resultado == []


def test_listar_clientes_retorna_todos(conn):
    """Deve retornar os 7 clientes cadastrados no seed."""
    clientes = queries.listar_clientes(conn)
    assert len(clientes) >= 5
    assert len(clientes) == 7


def test_resumo_por_cliente_exclui_cancelados(conn):
    """Deve agregar compras por cliente ignorando pedidos cancelados."""
    resumo = queries.resumo_por_cliente(conn)
    assert len(resumo) == 6
    # Ana Lima tem 2 pedidos pagos somando R$ 575,00
    primeiro = resumo[0]
    assert primeiro["cliente"] == "Ana Lima"
    assert primeiro["total_pedidos"] == 2
    assert primeiro["total_gasto"] == 575.00


def test_produtos_mais_vendidos_ordenacao(conn):
    """Deve retornar o ranking ordenado pela quantidade de unidades vendidas."""
    ranking = queries.produtos_mais_vendidos(conn)
    assert len(ranking) > 0
    quantidades = [item["unidades_vendidas"] for item in ranking]
    assert quantidades == sorted(quantidades, reverse=True)
    assert ranking[0]["produto"] == "Template de Dashboard SQL"
    assert ranking[0]["unidades_vendidas"] == 5


def test_pedidos_detalhados_usa_view(conn):
    """Deve consultar a VIEW resumo_pedidos e retornar todos os 8 pedidos."""
    pedidos = queries.pedidos_detalhados(conn)
    assert len(pedidos) == 8
    assert "valor_total" in pedidos[0].keys()
    assert "total_itens" in pedidos[0].keys()


def test_faturamento_por_categoria(conn):
    """Deve agrupar receita e ticket médio pelas 3 categorias."""
    faturamento = queries.faturamento_por_categoria(conn)
    assert len(faturamento) == 3
    categorias = [f["categoria"] for f in faturamento]
    assert set(categorias) == {"Curso", "E-book", "Template"}


def test_clientes_acima_de_meta_having(conn):
    """Deve filtrar clientes com gasto acumulado acima da meta usando HAVING."""
    acima_200 = queries.clientes_acima_de_meta(conn, 200.0)
    assert len(acima_200) == 4
    for cliente in acima_200:
        assert cliente["total_gasto"] > 200.0


def test_produtos_acima_da_media_subquery(conn):
    """Deve retornar apenas produtos com preço superior à média geral."""
    acima_media = queries.produtos_acima_da_media(conn)
    assert len(acima_media) == 3
    for prod in acima_media:
        assert prod["diferenca_da_media"] > 0


def test_desempenho_produtos_cte_case_when(conn):
    """Deve classificar todos os produtos em Alto, Medio ou Baixo via CTE + CASE WHEN."""
    desempenho = queries.desempenho_produtos_cte(conn)
    assert len(desempenho) == 7
    rotulos = {item["desempenho"] for item in desempenho}
    assert rotulos.issubset({"Alto", "Medio", "Baixo"})
    assert desempenho[0]["produto"] == "Fundamentos de IA com Python"
    assert desempenho[0]["desempenho"] == "Alto"
