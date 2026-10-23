"""
Formatacao e exibicao dos relatorios no terminal.
"""

import sqlite3
from queries import (
    clientes_acima_de_meta,
    desempenho_produtos_cte,
    faturamento_por_categoria,
    filtrar_por_categoria,
    listar_clientes,
    listar_produtos,
    pedidos_detalhados,
    produtos_acima_da_media,
    produtos_mais_vendidos,
    resumo_por_cliente,
)


def _linha(caractere: str = "-", largura: int = 65) -> str:
    return caractere * largura


def _cabecalho(titulo: str) -> None:
    print(f"\n{_linha('=')}")
    print(f"  {titulo.upper()}")
    print(_linha("="))


def _sem_resultados() -> None:
    print("  Nenhum resultado encontrado.")


def relatorio_produtos(conn: sqlite3.Connection) -> None:
    """Exibe todos os produtos formatados em tabela."""
    _cabecalho("Catalogo de Produtos")
    linhas = listar_produtos(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'ID':<4} {'NOME':<38} {'CATEGORIA':<10} {'PRECO':>8} {'ESTOQUE':>8}")
    print(f"  {_linha('-', 4)} {_linha('-', 38)} {_linha('-', 10)} {_linha('-', 8)} {_linha('-', 8)}")
    for row in linhas:
        print(
            f"  {row['id']:<4} {row['nome']:<38} {row['categoria']:<10}"
            f"  R${row['preco']:>7.2f}  {row['estoque']:>7}"
        )
    print(f"\n  Total: {len(linhas)} produto(s)\n")


def relatorio_categoria(conn: sqlite3.Connection) -> None:
    """Solicita uma categoria ao usuario e exibe os produtos filtrados."""
    _cabecalho("Filtrar Produtos por Categoria")
    print("  Categorias disponiveis: Curso | E-book | Template")
    categoria = input("  Digite a categoria: ").strip()

    if not categoria:
        print("  Categoria nao informada.")
        return

    linhas = filtrar_por_categoria(conn, categoria)

    if not linhas:
        print(f"  Nenhum produto encontrado na categoria '{categoria}'.")
        return

    print(f"\n  {'ID':<4} {'NOME':<38} {'PRECO':>8} {'ESTOQUE':>8}")
    print(f"  {_linha('-', 4)} {_linha('-', 38)} {_linha('-', 8)} {_linha('-', 8)}")
    for row in linhas:
        print(f"  {row['id']:<4} {row['nome']:<38}  R${row['preco']:>7.2f}  {row['estoque']:>7}")
    print(f"\n  Total: {len(linhas)} produto(s) na categoria '{categoria}'\n")


def relatorio_clientes(conn: sqlite3.Connection) -> None:
    """Exibe todos os clientes cadastrados."""
    _cabecalho("Clientes Cadastrados")
    linhas = listar_clientes(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'ID':<4} {'NOME':<22} {'E-MAIL':<30} {'CIDADE':<18} CADASTRO")
    print(f"  {_linha('-', 4)} {_linha('-', 22)} {_linha('-', 30)} {_linha('-', 18)} {_linha('-', 10)}")
    for row in linhas:
        print(
            f"  {row['id']:<4} {row['nome']:<22} {row['email']:<30}"
            f" {row['cidade']:<18} {row['criado_em']}"
        )
    print(f"\n  Total: {len(linhas)} cliente(s)\n")


def relatorio_pedidos(conn: sqlite3.Connection) -> None:
    """Exibe pedidos detalhados usando a view do banco."""
    _cabecalho("Pedidos Detalhados (View SQL)")
    linhas = pedidos_detalhados(conn)

    if not linhas:
        _sem_resultados()
        return

    print(
        f"  {'PED':<5} {'CLIENTE':<22} {'DATA':<12} {'STATUS':<11}"
        f" {'ITENS':>5} {'TOTAL':>10}"
    )
    print(
        f"  {_linha('-', 5)} {_linha('-', 22)} {_linha('-', 12)} {_linha('-', 11)}"
        f" {_linha('-', 5)} {_linha('-', 10)}"
    )
    for row in linhas:
        print(
            f"  {row['pedido_id']:<5} {row['cliente']:<22} {row['data_pedido']:<12}"
            f" {row['status']:<11}  {row['total_itens']:>4}   R${row['valor_total']:>7.2f}"
        )
    print(f"\n  Total: {len(linhas)} pedido(s)\n")


def relatorio_ranking(conn: sqlite3.Connection) -> None:
    """Exibe ranking dos produtos mais vendidos."""
    _cabecalho("Ranking de Produtos Mais Vendidos")
    linhas = produtos_mais_vendidos(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'#':<4} {'PRODUTO':<38} {'CAT':<10} {'UNID':>5} {'RECEITA':>12}")
    print(f"  {_linha('-', 4)} {_linha('-', 38)} {_linha('-', 10)} {_linha('-', 5)} {_linha('-', 12)}")
    for pos, row in enumerate(linhas, start=1):
        print(
            f"  {pos:<4} {row['produto']:<38} {row['categoria']:<10}"
            f"  {row['unidades_vendidas']:>4}   R${row['receita_total']:>9.2f}"
        )
    print()


def relatorio_faturamento(conn: sqlite3.Connection) -> None:
    """Exibe faturamento agrupado por categoria."""
    _cabecalho("Faturamento por Categoria")
    linhas = faturamento_por_categoria(conn)

    if not linhas:
        _sem_resultados()
        return

    print(
        f"  {'CATEGORIA':<12} {'PRODUTOS':>9} {'UNIDADES':>9}"
        f" {'TICKET MEDIO':>13} {'RECEITA TOTAL':>14}"
    )
    print(
        f"  {_linha('-', 12)} {_linha('-', 9)} {_linha('-', 9)}"
        f" {_linha('-', 13)} {_linha('-', 14)}"
    )

    total_geral = 0.0
    for row in linhas:
        print(
            f"  {row['categoria']:<12}  {row['produtos_distintos']:>8}  {row['unidades_vendidas']:>8}"
            f"    R${row['ticket_medio']:>9.2f}    R${row['receita_total']:>9.2f}"
        )
        total_geral += row["receita_total"]

    print(f"  {_linha('-', 60)}")
    print(f"  {'TOTAL GERAL':>50}    R${total_geral:>9.2f}\n")


def relatorio_clientes_vip(conn: sqlite3.Connection) -> None:
    """Exibe resumo de gastos por cliente."""
    _cabecalho("Clientes por Volume de Compras")
    linhas = resumo_por_cliente(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'#':<4} {'CLIENTE':<22} {'CIDADE':<18} {'PEDIDOS':>8} {'TOTAL GASTO':>12}")
    print(f"  {_linha('-', 4)} {_linha('-', 22)} {_linha('-', 18)} {_linha('-', 8)} {_linha('-', 12)}")
    for pos, row in enumerate(linhas, start=1):
        print(
            f"  {pos:<4} {row['cliente']:<22} {row['cidade']:<18}"
            f"  {row['total_pedidos']:>7}   R${row['total_gasto']:>9.2f}"
        )
    print()


def relatorio_clientes_meta(conn: sqlite3.Connection) -> None:
    """Exibe clientes que superaram uma meta de gasto."""
    _cabecalho("Clientes Acima da Meta (HAVING)")

    try:
        entrada = input("  Digite o valor minimo em R$ (Enter para 200): ").strip()
        meta = float(entrada) if entrada else 200.0
    except ValueError:
        print("  Valor invalido. Usando R$ 200,00 como padrao.")
        meta = 200.0

    linhas = clientes_acima_de_meta(conn, meta)

    if not linhas:
        print(f"  Nenhum cliente gastou acima de R$ {meta:.2f}.")
        return

    print(f"\n  Meta: R$ {meta:.2f} | {len(linhas)} cliente(s) encontrado(s)\n")
    print(f"  {'#':<4} {'CLIENTE':<22} {'CIDADE':<18} {'PEDIDOS':>8} {'TOTAL GASTO':>12}")
    print(f"  {_linha('-', 4)} {_linha('-', 22)} {_linha('-', 18)} {_linha('-', 8)} {_linha('-', 12)}")
    for pos, row in enumerate(linhas, start=1):
        print(
            f"  {pos:<4} {row['cliente']:<22} {row['cidade']:<18}"
            f"  {row['total_pedidos']:>7}   R${row['total_gasto']:>9.2f}"
        )
    print()


def relatorio_produtos_acima_media(conn: sqlite3.Connection) -> None:
    """Exibe produtos com preco acima da media geral."""
    _cabecalho("Produtos Acima da Media de Preco")
    linhas = produtos_acima_da_media(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'ID':<4} {'NOME':<38} {'CATEGORIA':<10} {'PRECO':>8} {'ACIMA MEDIA':>12}")
    print(f"  {_linha('-', 4)} {_linha('-', 38)} {_linha('-', 10)} {_linha('-', 8)} {_linha('-', 12)}")
    for row in linhas:
        print(
            f"  {row['id']:<4} {row['nome']:<38} {row['categoria']:<10}"
            f"  R${row['preco']:>5.2f}   +R${row['diferenca_da_media']:>7.2f}"
        )
    print(f"\n  Total: {len(linhas)} produto(s) acima da media\n")


def relatorio_desempenho_cte(conn: sqlite3.Connection) -> None:
    """Exibe o desempenho de cada produto classificado por faixa de receita."""
    _cabecalho("Desempenho de Produtos (CTE e CASE WHEN)")
    linhas = desempenho_produtos_cte(conn)

    if not linhas:
        _sem_resultados()
        return

    print(
        f"  {'PRODUTO':<38} {'CAT':<10} {'PRECO':>7}"
        f" {'UNID':>5} {'RECEITA':>10} {'DESEMPENHO':>12}"
    )
    print(
        f"  {_linha('-', 38)} {_linha('-', 10)} {_linha('-', 7)}"
        f" {_linha('-', 5)} {_linha('-', 10)} {_linha('-', 12)}"
    )
    for row in linhas:
        print(
            f"  {row['produto']:<38} {row['categoria']:<10}"
            f"  R${row['preco_unitario']:>5.2f}  {row['unidades_vendidas']:>4}"
            f"   R${row['receita_total']:>7.2f}  {row['desempenho']:>10}"
        )
    print()
