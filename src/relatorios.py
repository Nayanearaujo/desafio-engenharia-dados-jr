"""
Formatacao e exibicao dos relatorios no terminal.
"""

import os
import sqlite3
from queries import (
    clientes_acima_de_meta,
    desempenho_produtos_cte,
    faturamento_por_categoria,
    filtrar_por_categoria,
    inserir_produto,
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


def cadastrar_produto(conn: sqlite3.Connection) -> None:
    """Permite cadastrar um novo produto via terminal com validacao de dados."""
    _cabecalho("Cadastrar Novo Produto")

    nome = input("  Nome do produto: ").strip()
    if not nome:
        print("  Operacao cancelada: o nome nao pode ficar vazio.")
        return

    categoria = input("  Categoria (Curso / E-book / Template): ").strip()
    if not categoria:
        print("  Operacao cancelada: a categoria nao pode ficar vazia.")
        return

    try:
        preco = float(input("  Preco (R$): ").strip().replace(",", "."))
        estoque = int(input("  Estoque inicial: ").strip())
        if preco < 0 or estoque < 0:
            print("  Erro: preco e estoque nao podem ser negativos.")
            return
    except ValueError:
        print("  Erro: informe valores numericos validos para preco e estoque.")
        return

    novo_id = inserir_produto(conn, nome, categoria, preco, estoque)
    print(f"\n  Produto '{nome}' cadastrado com sucesso (ID: {novo_id}).\n")


def gerar_grafico_faturamento(conn: sqlite3.Connection) -> None:
    """Exibe grafico de faturamento por categoria e salva imagem PNG com matplotlib."""
    _cabecalho("Grafico de Faturamento por Categoria")
    linhas = faturamento_por_categoria(conn)

    if not linhas:
        _sem_resultados()
        return

    maior_receita = max(row["receita_total"] for row in linhas) or 1.0
    for row in linhas:
        blocos = int((row["receita_total"] / maior_receita) * 30)
        barra = "#" * blocos
        print(
            f"  {row['categoria']:<10} | {barra:<30} R$ {row['receita_total']:>8.2f}"
        )
    print()

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        categorias = [row["categoria"] for row in linhas]
        receitas = [row["receita_total"] for row in linhas]

        fig, ax = plt.subplots(figsize=(8, 5))
        barras = ax.bar(categorias, receitas, color=["#2563eb", "#0891b2", "#0d9488"])
        ax.set_title("Faturamento por Categoria (R$)", fontsize=13, pad=12)
        ax.set_xlabel("Categoria")
        ax.set_ylabel("Receita Total (R$)")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        for barra, valor in zip(barras, receitas):
            ax.text(
                barra.get_x() + barra.get_width() / 2,
                barra.get_height() + 15,
                f"R$ {valor:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_ylim(0, max(receitas) * 1.15)
        plt.tight_layout()

        dir_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_img = os.path.join(dir_raiz, "grafico_faturamento.png")
        plt.savefig(caminho_img, dpi=150)
        plt.close(fig)
        print(f"  Arquivo de imagem salvo em: {caminho_img}\n")
    except ImportError:
        print("  (Dica: instale 'matplotlib' para tambem exportar o grafico em PNG)\n")

