"""
Formatacao e exibicao dos relatorios no terminal.
"""

import csv
import os
import sqlite3
from queries import (
    calcular_kpis_executivos,
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
    ranking_window_function,
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


def relatorio_kpis_pareto(conn: sqlite3.Connection) -> None:
    """Exibe indicadores executivos (KPIs) e curva ABC/Pareto com Window Functions."""
    _cabecalho("KPIs Executivos e Curva de Pareto (Window Functions)")
    kpis = calcular_kpis_executivos(conn)

    if kpis:
        print(f"  Receita Confirmada (Paga) : R$ {kpis['receita_paga']:>8.2f}")
        print(f"  Receita em Aberto         : R$ {kpis['receita_pendente']:>8.2f}")
        print(f"  Ticket Medio por Pedido   : R$ {kpis['ticket_medio_pedido']:>8.2f}")
        print(f"  LTV Medio por Cliente     : R$ {kpis['ltv_medio_cliente']:>8.2f}")
        print(f"  Taxa de Conversao (Pagos) :    {kpis['taxa_conversao_pct']:>7.1f}%")
        print(f"  Taxa de Cancelamento      :    {kpis['taxa_cancelamento_pct']:>7.1f}%")
        print(f"  {_linha('-', 61)}")

    linhas = ranking_window_function(conn)
    if not linhas:
        return

    print(
        f"\n  {'RANK':<5} {'PRODUTO':<34} {'RECEITA':>10}"
        f" {'SHARE %':>9} {'ACUMULADO %':>12}"
    )
    print(
        f"  {_linha('-', 5)} {_linha('-', 34)} {_linha('-', 10)}"
        f" {_linha('-', 9)} {_linha('-', 12)}"
    )
    for row in linhas:
        print(
            f"  #{row['posicao_ranking']:<4} {row['produto']:<34}"
            f" R${row['receita']:>8.2f}   {row['share_receita_pct']:>6.1f}%"
            f"      {row['pareto_acumulado_pct']:>6.1f}%"
        )
    print()


def gerar_grafico_faturamento(conn: sqlite3.Connection) -> None:
    """Gera painel executivo com 4 graficos (KPIs, Pareto, Categorias e LTV) em PNG."""
    _cabecalho("Painel Visual de KPIs e Faturamento")
    linhas_cat = faturamento_por_categoria(conn)
    linhas_pareto = ranking_window_function(conn)
    linhas_cli = resumo_por_cliente(conn)
    kpis = calcular_kpis_executivos(conn)

    if not linhas_cat:
        _sem_resultados()
        return

    maior_receita = max(row["receita_total"] for row in linhas_cat) or 1.0
    for row in linhas_cat:
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

        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
        plt.rcParams["text.parse_math"] = False
        fig = plt.figure(figsize=(14, 9.2), facecolor="#0f172a")
        gs = fig.add_gridspec(3, 2, height_ratios=[0.28, 1, 1], hspace=0.58, wspace=0.25)

        ax_header = fig.add_subplot(gs[0, :])
        ax_header.set_facecolor("#0f172a")
        ax_header.axis("off")
        ax_header.text(
            0.0, 0.82, "LOJA DIGITAL  |  DASHBOARD EXECUTIVO DE DADOS",
            color="#f8fafc", fontsize=15, fontweight="bold"
        )
        if kpis:
            cards = [
                ("RECEITA PAGA", f"R$ {kpis['receita_paga']:.2f}", "#38bdf8"),
                ("RECEITA PENDENTE", f"R$ {kpis['receita_pendente']:.2f}", "#fbbf24"),
                ("TICKET MEDIO", f"R$ {kpis['ticket_medio_pedido']:.2f}", "#818cf8"),
                ("LTV MEDIO / CLIENTE", f"R$ {kpis['ltv_medio_cliente']:.2f}", "#34d399"),
                ("TAXA DE CONVERSAO", f"{kpis['taxa_conversao_pct']:.1f}%", "#f43f5e"),
            ]
            for idx, (rotulo, valor, cor) in enumerate(cards):
                x0 = idx * 0.202
                rect = matplotlib.patches.FancyBboxPatch(
                    (x0, 0.02), 0.185, 0.56,
                    boxstyle="round,pad=0.02,rounding_size=0.03",
                    facecolor="#1e293b", edgecolor="#334155", linewidth=1,
                    transform=ax_header.transAxes
                )
                ax_header.add_patch(rect)
                ax_header.text(
                    x0 + 0.015, 0.40, rotulo,
                    color="#94a3b8", fontsize=8, fontweight="bold",
                    transform=ax_header.transAxes
                )
                ax_header.text(
                    x0 + 0.015, 0.12, valor,
                    color=cor, fontsize=12, fontweight="bold",
                    transform=ax_header.transAxes
                )

        def estilizar_eixo(ax, titulo):
            ax.set_facecolor("#1e293b")
            ax.set_title(titulo, color="#f1f5f9", fontsize=11, fontweight="bold", pad=12, loc="left")
            ax.tick_params(colors="#cbd5e1", labelsize=9)
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            for spine in ("bottom", "left"):
                ax.spines[spine].set_color("#334155")
            ax.grid(axis="both", linestyle="--", alpha=0.2, color="#94a3b8")

        # 1. Receita por Categoria
        ax1 = fig.add_subplot(gs[1, 0])
        estilizar_eixo(ax1, "1. Receita Total por Categoria (R$)")
        cats = [r["categoria"] for r in linhas_cat]
        recs = [r["receita_total"] for r in linhas_cat]
        cores_cat = ["#38bdf8", "#818cf8", "#34d399"]
        barras1 = ax1.bar(cats, recs, color=cores_cat[: len(cats)], width=0.5)
        ax1.set_ylim(0, max(recs) * 1.25)
        for b, v in zip(barras1, recs):
            ax1.text(
                b.get_x() + b.get_width() / 2, b.get_height() + 25,
                f"R$ {v:.0f}", ha="center", color="#f8fafc", fontsize=9, fontweight="bold"
            )

        # 2. Curva de Pareto (Produtos + % Acumulado)
        ax2 = fig.add_subplot(gs[1, 1])
        estilizar_eixo(ax2, "2. Curva de Pareto (Receita e % Acumulado)")
        nomes_curtos = [r["produto"][:13] + "." if len(r["produto"]) > 13 else r["produto"] for r in linhas_pareto]
        rec_prod = [r["receita"] for r in linhas_pareto]
        acum_pct = [r["pareto_acumulado_pct"] for r in linhas_pareto]
        x_pos = range(len(nomes_curtos))
        ax2.bar(x_pos, rec_prod, color="#6366f1", width=0.52, label="Receita (R$)")
        ax2.set_xticks(list(x_pos))
        ax2.set_xticklabels(nomes_curtos, rotation=18, ha="right", fontsize=8)
        ax2_twin = ax2.twinx()
        ax2_twin.plot(list(x_pos), acum_pct, color="#f59e0b", marker="o", linewidth=2, label="% Acumulado")
        ax2_twin.set_ylim(0, 112)
        ax2_twin.tick_params(colors="#f59e0b", labelsize=8)
        ax2_twin.spines["top"].set_visible(False)
        ax2_twin.spines["right"].set_color("#f59e0b")
        ax2_twin.axhline(80, color="#f59e0b", linestyle=":", alpha=0.6)

        # 3. Top Clientes por LTV (Gasto Total)
        ax3 = fig.add_subplot(gs[2, 0])
        estilizar_eixo(ax3, "3. Top Clientes por Volume de Compras (LTV)")
        clientes_nomes = [r["cliente"] for r in linhas_cli][::-1]
        clientes_gasto = [r["total_gasto"] for r in linhas_cli][::-1]
        barras3 = ax3.barh(clientes_nomes, clientes_gasto, color="#10b981", height=0.6)
        ax3.set_xlim(0, max(clientes_gasto) * 1.2)
        for b, v in zip(barras3, clientes_gasto):
            ax3.text(
                v + 10, b.get_y() + b.get_height() / 2,
                f"R$ {v:.0f}", va="center", color="#f8fafc", fontsize=8.5
            )

        # 4. Ticket Medio vs Receita por Categoria
        ax4 = fig.add_subplot(gs[2, 1])
        estilizar_eixo(ax4, "4. Ticket Medio Unitario por Categoria (R$)")
        tickets = [r["ticket_medio"] for r in linhas_cat]
        barras4 = ax4.bar(cats, tickets, color="#f43f5e", width=0.5)
        ax4.set_ylim(0, max(tickets) * 1.25)
        for b, v in zip(barras4, tickets):
            ax4.text(
                b.get_x() + b.get_width() / 2, b.get_height() + 4,
                f"R$ {v:.2f}", ha="center", color="#f8fafc", fontsize=9, fontweight="bold"
            )

        dir_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_assets = os.path.join(dir_raiz, "assets")
        os.makedirs(pasta_assets, exist_ok=True)
        caminho_img = os.path.join(pasta_assets, "dashboard_executivo.png")
        plt.savefig(caminho_img, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"  Dashboard salvo com sucesso em: {caminho_img}\n")
    except ImportError:
        print("  (Dica: instale 'matplotlib' para exportar o dashboard em PNG)\n")


def exportar_relatorios_csv(conn: sqlite3.Connection) -> None:
    """Automatiza a exportacao das tabelas analiticas para arquivos CSV na pasta exports/."""
    _cabecalho("Automacao: Exportar Camada Analitica (CSV)")
    dir_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_exports = os.path.join(dir_raiz, "exports")
    os.makedirs(pasta_exports, exist_ok=True)

    tarefas = [
        ("faturamento_categorias.csv", faturamento_por_categoria(conn)),
        ("pareto_produtos_window.csv", ranking_window_function(conn)),
        ("ltv_clientes.csv", resumo_por_cliente(conn)),
        ("pedidos_consolidados.csv", pedidos_detalhados(conn)),
    ]

    for nome_arquivo, dados in tarefas:
        if not dados:
            continue
        caminho = os.path.join(pasta_exports, nome_arquivo)
        colunas = dados[0].keys()
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(colunas)
            for linha in dados:
                writer.writerow([linha[col] for col in colunas])
        print(f"  [OK] Exportado: exports/{nome_arquivo} ({len(dados)} registros)")

    print("\n  Camada analitica exportada com sucesso!\n")


