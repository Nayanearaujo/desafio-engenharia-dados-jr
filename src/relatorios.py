"""
Formatacao e exibicao dos relatorios no terminal, geracao do Dashboard Executivo
em Matplotlib e exportacao automatizada de CSVs.
"""

import os
import sqlite3
from typing import Any

from pipeline.executar import run_pipeline
from pipeline.gold import calcular_carta_controle_diaria, exportar_camada_gold
from queries import (
    calcular_kpis_executivos,
    cancelamento_categoria_mes,
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
    receita_mensal_mom,
    resumo_por_cliente,
    resumo_qualidade_dados,
    resumo_segmentos_rfm,
    retencao_coorte,
    segmentacao_rfm,
    taxa_recompra_global,
)


def _linha(caractere: str = "-", largura: int = 72) -> str:
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

    print(f"  {'ID':<4} {'NOME':<40} {'CATEGORIA':<10} {'PRECO':>9} {'ESTOQUE':>8}")
    print(f"  {_linha('-', 4)} {_linha('-', 40)} {_linha('-', 10)} {_linha('-', 9)} {_linha('-', 8)}")
    for row in linhas:
        nome = row["nome"][:39]
        print(
            f"  {row['id']:<4} {nome:<40} {row['categoria']:<10}"
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

    print(f"\n  {'ID':<4} {'NOME':<40} {'PRECO':>9} {'ESTOQUE':>8}")
    print(f"  {_linha('-', 4)} {_linha('-', 40)} {_linha('-', 9)} {_linha('-', 8)}")
    for row in linhas:
        nome = row["nome"][:39]
        print(f"  {row['id']:<4} {nome:<40}  R${row['preco']:>7.2f}  {row['estoque']:>7}")
    print(f"\n  Total: {len(linhas)} produto(s) na categoria '{categoria}'\n")


def relatorio_clientes(conn: sqlite3.Connection) -> None:
    """Exibe os clientes cadastrados (ate 25 no terminal para legibilidade)."""
    _cabecalho("Clientes Cadastrados")
    linhas = listar_clientes(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'ID':<5} {'NOME':<26} {'E-MAIL':<30} {'CIDADE':<16} CADASTRO")
    print(f"  {_linha('-', 5)} {_linha('-', 26)} {_linha('-', 30)} {_linha('-', 16)} {_linha('-', 10)}")
    for row in linhas[:25]:
        print(
            f"  {row['id']:<5} {row['nome'][:25]:<26} {row['email'][:29]:<30}"
            f" {row['cidade'][:15]:<16} {row['criado_em']}"
        )
    if len(linhas) > 25:
        print(f"  ... exibindo 25 de {len(linhas)} clientes.")
    print(f"\n  Total: {len(linhas)} cliente(s)\n")


def relatorio_pedidos(conn: sqlite3.Connection) -> None:
    """Exibe pedidos detalhados usando a view resumo_pedidos."""
    _cabecalho("Pedidos Detalhados (View SQL)")
    linhas = pedidos_detalhados(conn)

    if not linhas:
        _sem_resultados()
        return

    print(
        f"  {'PED':<6} {'CLIENTE':<24} {'DATA':<12} {'STATUS':<11}"
        f" {'ITENS':>5} {'TOTAL':>11}"
    )
    print(
        f"  {_linha('-', 6)} {_linha('-', 24)} {_linha('-', 12)} {_linha('-', 11)}"
        f" {_linha('-', 5)} {_linha('-', 11)}"
    )
    for row in linhas[:25]:
        print(
            f"  {row['pedido_id']:<6} {row['cliente'][:23]:<24} {row['data_pedido']:<12}"
            f" {row['status']:<11}  {row['total_itens']:>4}   R${row['valor_total']:>8.2f}"
        )
    if len(linhas) > 25:
        print(f"  ... exibindo os 25 pedidos mais recentes de {len(linhas)}.")
    print(f"\n  Total: {len(linhas)} pedido(s)\n")


def relatorio_ranking(conn: sqlite3.Connection) -> None:
    """Exibe ranking dos produtos mais vendidos."""
    _cabecalho("Ranking de Produtos Mais Vendidos")
    linhas = produtos_mais_vendidos(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'#':<4} {'PRODUTO':<40} {'CAT':<10} {'UNID':>6} {'RECEITA':>13}")
    print(f"  {_linha('-', 4)} {_linha('-', 40)} {_linha('-', 10)} {_linha('-', 6)} {_linha('-', 13)}")
    for pos, row in enumerate(linhas[:20], start=1):
        print(
            f"  {pos:<4} {row['produto'][:39]:<40} {row['categoria']:<10}"
            f"  {row['unidades_vendidas']:>5}   R${row['receita_total']:>10.2f}"
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
        f" {'TICKET MEDIO':>13} {'RECEITA TOTAL':>15}"
    )
    print(
        f"  {_linha('-', 12)} {_linha('-', 9)} {_linha('-', 9)}"
        f" {_linha('-', 13)} {_linha('-', 15)}"
    )

    total_geral = 0.0
    for row in linhas:
        print(
            f"  {row['categoria']:<12}  {row['produtos_distintos']:>8}  {row['unidades_vendidas']:>8}"
            f"    R${row['ticket_medio']:>9.2f}    R${row['receita_total']:>10.2f}"
        )
        total_geral += row["receita_total"]

    print(f"  {_linha('-', 62)}")
    print(f"  {'TOTAL GERAL':>46}    R${total_geral:>10.2f}\n")


def relatorio_clientes_vip(conn: sqlite3.Connection) -> None:
    """Exibe resumo de gastos por cliente."""
    _cabecalho("Clientes por Volume de Compras")
    linhas = resumo_por_cliente(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'#':<4} {'CLIENTE':<26} {'CIDADE':<18} {'PEDIDOS':>8} {'TOTAL GASTO':>13}")
    print(f"  {_linha('-', 4)} {_linha('-', 26)} {_linha('-', 18)} {_linha('-', 8)} {_linha('-', 13)}")
    for pos, row in enumerate(linhas[:20], start=1):
        print(
            f"  {pos:<4} {row['cliente'][:25]:<26} {row['cidade'][:17]:<18}"
            f"  {row['total_pedidos']:>7}   R${row['total_gasto']:>10.2f}"
        )
    if len(linhas) > 20:
        print(f"  ... exibindo top 20 de {len(linhas)} clientes ativos.")
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
    print(f"  {'#':<4} {'CLIENTE':<26} {'CIDADE':<18} {'PEDIDOS':>8} {'TOTAL GASTO':>13}")
    print(f"  {_linha('-', 4)} {_linha('-', 26)} {_linha('-', 18)} {_linha('-', 8)} {_linha('-', 13)}")
    for pos, row in enumerate(linhas[:20], start=1):
        print(
            f"  {pos:<4} {row['cliente'][:25]:<26} {row['cidade'][:17]:<18}"
            f"  {row['total_pedidos']:>7}   R${row['total_gasto']:>10.2f}"
        )
    print()


def relatorio_produtos_acima_media(conn: sqlite3.Connection) -> None:
    """Exibe produtos com preco acima da media geral."""
    _cabecalho("Produtos Acima da Media de Preco")
    linhas = produtos_acima_da_media(conn)

    if not linhas:
        _sem_resultados()
        return

    print(f"  {'ID':<4} {'NOME':<40} {'CATEGORIA':<10} {'PRECO':>8} {'ACIMA MEDIA':>12}")
    print(f"  {_linha('-', 4)} {_linha('-', 40)} {_linha('-', 10)} {_linha('-', 8)} {_linha('-', 12)}")
    for row in linhas:
        print(
            f"  {row['id']:<4} {row['nome'][:39]:<40} {row['categoria']:<10}"
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
        f"  {'PRODUTO':<40} {'CAT':<10} {'PRECO':>7}"
        f" {'UNID':>5} {'RECEITA':>11} {'DESEMPENHO':>10}"
    )
    print(
        f"  {_linha('-', 40)} {_linha('-', 10)} {_linha('-', 7)}"
        f" {_linha('-', 5)} {_linha('-', 11)} {_linha('-', 10)}"
    )
    for row in linhas[:20]:
        print(
            f"  {row['produto'][:39]:<40} {row['categoria']:<10}"
            f"  R${row['preco_unitario']:>5.2f}  {row['unidades_vendidas']:>4}"
            f"   R${row['receita_total']:>8.2f}  {row['desempenho']:>10}"
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
        if preco <= 0 or estoque < 0:
            print("  Erro: preco deve ser maior que zero e estoque nao negativo.")
            return
    except ValueError:
        print("  Erro: informe valores numericos validos para preco e estoque.")
        return

    novo_id = inserir_produto(conn, nome, categoria, preco, estoque)
    print(f"\n  Produto '{nome}' cadastrado com sucesso (ID: {novo_id}).\n")


def relatorio_kpis_pareto(conn: sqlite3.Connection) -> None:
    """Exibe indicadores executivos (KPIs) e curva ABC/Pareto com Window Functions."""
    _cabecalho("KPIs Executivos e Curva de Pareto 80/20 (Window Functions)")
    kpis = calcular_kpis_executivos(conn)

    if kpis:
        print(f"  Receita Confirmada (Paga) : R$ {kpis['receita_paga']:>10.2f}")
        print(f"  Receita em Aberto         : R$ {kpis['receita_pendente']:>10.2f}")
        print(f"  Ticket Medio por Pedido   : R$ {kpis['ticket_medio_pedido']:>10.2f}")
        print(f"  LTV Medio por Cliente     : R$ {kpis['ltv_medio_cliente']:>10.2f}")
        print(f"  Taxa de Conversao (Pagos) :    {kpis['taxa_conversao_pct']:>9.1f}%")
        print(f"  Taxa de Cancelamento      :    {kpis['taxa_cancelamento_pct']:>9.1f}%")
        print(f"  {_linha('-', 66)}")

    linhas = ranking_window_function(conn)
    if not linhas:
        return

    prods_80 = [r for r in linhas if r["pareto_acumulado_pct"] <= 85.0] or linhas[:1]
    print(
        f"\n  Insight Pareto: {len(prods_80)} de {len(linhas)} produtos concentram "
        f"{prods_80[-1]['pareto_acumulado_pct']:.1f}% da receita total.\n"
    )

    print(
        f"  {'RANK':<5} {'PRODUTO':<38} {'RECEITA':>11}"
        f" {'SHARE %':>9} {'ACUMULADO %':>12}"
    )
    print(
        f"  {_linha('-', 5)} {_linha('-', 38)} {_linha('-', 11)}"
        f" {_linha('-', 9)} {_linha('-', 12)}"
    )
    for row in linhas[:15]:
        marcador = " <-- ~80%" if abs(row["pareto_acumulado_pct"] - 80.0) <= 6.0 else ""
        print(
            f"  #{row['posicao_ranking']:<4} {row['produto'][:37]:<38}"
            f" R${row['receita']:>9.2f}   {row['share_receita_pct']:>6.1f}%"
            f"      {row['pareto_acumulado_pct']:>6.1f}%{marcador}"
        )
    print()


def gerar_grafico_faturamento(conn: sqlite3.Connection) -> None:
    """
    Gera Dashboard Executivo em Matplotlib (assets/dashboard_executivo.png)
    com titulos orientados a insights, Pareto 80/20, Receita Mensal + MM3M,
    Segmentacao RFM e Carta de Controle Lean Six Sigma (3-Sigma).
    """
    _cabecalho("Painel Visual de KPIs e Controle de Processo")
    carta = calcular_carta_controle_diaria(conn)
    linhas_cat = faturamento_por_categoria(conn)
    linhas_pareto = conn.execute("SELECT * FROM gold_pareto_produtos").fetchall()
    linhas_rfm = resumo_segmentos_rfm(conn)
    linhas_mes = receita_mensal_mom(conn)
    kpis = calcular_kpis_executivos(conn)

    if not linhas_cat:
        _sem_resultados()
        return

    maior_receita = max(row["receita_total"] for row in linhas_cat) or 1.0
    for row in linhas_cat:
        blocos = int((row["receita_total"] / maior_receita) * 30)
        barra = "#" * blocos
        print(
            f"  {row['categoria']:<10} | {barra:<30} R$ {row['receita_total']:>10.2f}"
        )
    print()

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
        plt.rcParams["text.parse_math"] = False
        fig = plt.figure(figsize=(15, 9.8), facecolor="#0f172a")
        gs = fig.add_gridspec(3, 2, height_ratios=[0.27, 1, 1], hspace=0.55, wspace=0.24)

        ax_header = fig.add_subplot(gs[0, :])
        ax_header.set_facecolor("#0f172a")
        ax_header.axis("off")
        ax_header.text(
            0.0, 0.82, "LOJA DIGITAL  |  ARQUITETURA MEDALHA E CONTROLE DE PROCESSO (GOLD)",
            color="#f8fafc", fontsize=15, fontweight="bold"
        )
        if kpis:
            recompra = taxa_recompra_global(conn)
            tx_rec = recompra["taxa_recompra_pct"] if recompra else 0.0
            cards = [
                ("RECEITA PAGA", f"R$ {kpis['receita_paga']:,.2f}", "#38bdf8"),
                ("TICKET MEDIO PAGO", f"R$ {kpis['ticket_medio_pedido']:,.2f}", "#818cf8"),
                ("LTV MEDIO PAGO", f"R$ {kpis['ltv_medio_cliente']:,.2f}", "#34d399"),
                ("CONVERSAO PAGOS", f"{kpis['taxa_conversao_pct']:.1f}%", "#fbbf24"),
                ("TAXA DE RECOMPRA", f"{tx_rec:.1f}%", "#f43f5e"),
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
                    x0 + 0.014, 0.40, rotulo,
                    color="#94a3b8", fontsize=8, fontweight="bold",
                    transform=ax_header.transAxes
                )
                ax_header.text(
                    x0 + 0.014, 0.12, valor,
                    color=cor, fontsize=11.5, fontweight="bold",
                    transform=ax_header.transAxes
                )

        def estilizar_eixo(ax: Any, titulo: str) -> None:
            ax.set_facecolor("#1e293b")
            ax.set_title(titulo, color="#f1f5f9", fontsize=10.5, fontweight="bold", pad=11, loc="left")
            ax.tick_params(colors="#cbd5e1", labelsize=8.5)
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            for spine in ("bottom", "left"):
                ax.spines[spine].set_color("#334155")
            ax.grid(axis="both", linestyle="--", alpha=0.2, color="#94a3b8")

        # Painel 1: Pareto 80/20 (Top 8 produtos para legibilidade)
        ax1 = fig.add_subplot(gs[1, 0])
        prods_80 = [r for r in linhas_pareto if r["pareto_acumulado_pct"] <= 83.0] or linhas_pareto[:1]
        pct_top = prods_80[-1]["pareto_acumulado_pct"]
        estilizar_eixo(
            ax1,
            f"1. Pareto 80/20: {len(prods_80)} de {len(linhas_pareto)} produtos geram {pct_top:.1f}% da receita paga",
        )
        amostra_p = linhas_pareto[:8]
        nomes_curtos = [r["produto"][:13] + "." if len(r["produto"]) > 13 else r["produto"] for r in amostra_p]
        rec_prod = [r["receita"] for r in amostra_p]
        acum_pct = [r["pareto_acumulado_pct"] for r in amostra_p]
        x_pos = list(range(len(nomes_curtos)))
        ax1.bar(x_pos, rec_prod, color="#6366f1", width=0.52)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(nomes_curtos, rotation=18, ha="right", fontsize=8)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(x_pos, acum_pct, color="#f59e0b", marker="o", linewidth=2)
        ax1_twin.set_ylim(0, 112)
        ax1_twin.tick_params(colors="#f59e0b", labelsize=8)
        ax1_twin.spines["top"].set_visible(False)
        ax1_twin.spines["right"].set_color("#f59e0b")
        ax1_twin.axhline(80, color="#f59e0b", linestyle="--", linewidth=1.2, alpha=0.85)
        ax1_twin.text(0.1, 83, "Meta 80%", color="#f59e0b", fontsize=8, fontweight="bold")

        # Painel 2: Receita Mensal e Media Movel 3M (ou Categorias se houver so 1 mes)
        ax2 = fig.add_subplot(gs[1, 1])
        if len(linhas_mes) >= 3:
            meses = [r["mes"][2:] for r in linhas_mes]
            rec_m = [r["receita_liquida"] for r in linhas_mes]
            mm3 = [r["media_movel_3m"] for r in linhas_mes]
            melhor_mes = max(linhas_mes, key=lambda x: x["receita_liquida"])
            estilizar_eixo(
                ax2,
                f"2. Evolucao Mensal Paga e MM3M: pico em {melhor_mes['mes']} (R$ {melhor_mes['receita_liquida']:,.0f})",
            )
            x_m = list(range(len(meses)))
            ax2.bar(x_m, rec_m, color="#38bdf8", alpha=0.75, width=0.55, label="Receita Mensal Paga")
            ax2.plot(x_m, mm3, color="#f43f5e", marker="o", linewidth=2.2, label="Media Movel 3M")
            ax2.set_xticks(x_m)
            ax2.set_xticklabels(meses, rotation=20, ha="right", fontsize=8)
            ax2.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#f8fafc", fontsize=8)
        else:
            cats = [r["categoria"] for r in linhas_cat]
            recs = [r["receita_total"] for r in linhas_cat]
            estilizar_eixo(
                ax2,
                f"2. Receita por Categoria: {cats[0]} lidera com R$ {recs[0]:,.0f}",
            )
            barras2 = ax2.bar(cats, recs, color=["#38bdf8", "#818cf8", "#34d399"][: len(cats)], width=0.5)
            ax2.set_ylim(0, max(recs) * 1.25)
            for b, v in zip(barras2, recs):
                ax2.text(
                    b.get_x() + b.get_width() / 2, b.get_height() + max(recs) * 0.03,
                    f"R$ {v:,.0f}", ha="center", color="#f8fafc", fontsize=8.5, fontweight="bold"
                )

        # Painel 3: Segmentacao RFM de Clientes
        ax3 = fig.add_subplot(gs[2, 0])
        if linhas_rfm:
            segs = [r["segmento_rfm"] for r in linhas_rfm][::-1]
            rec_segs = [r["receita_segmento"] for r in linhas_rfm][::-1]
            top_seg = linhas_rfm[0]
            estilizar_eixo(
                ax3,
                f"3. Matriz RFM: segmento '{top_seg['segmento_rfm']}' gera {top_seg['share_receita_pct']:.1f}% da receita paga",
            )
            barras3 = ax3.barh(segs, rec_segs, color="#10b981", height=0.55)
            ax3.set_xlim(0, max(rec_segs) * 1.25)
            for b, v in zip(barras3, rec_segs):
                ax3.text(
                    v + max(rec_segs) * 0.02, b.get_y() + b.get_height() / 2,
                    f"R$ {v:,.0f}", va="center", color="#f8fafc", fontsize=8.5, fontweight="bold"
                )

        # Painel 4: Carta de Controle I-MR Dessazonalizada (Tendencia MM15d +/- 3 sigma_IMR)
        ax4 = fig.add_subplot(gs[2, 1])
        serie_cep = carta["serie"]
        qtd_fora = carta["dias_fora_controle"]
        estilizar_eixo(
            ax4,
            f"4. Carta I-MR Dessazonalizada: {qtd_fora} dia(s) fora de 3s (s_IMR R$ {carta['desvio_padrao']:,.0f})",
        )
        if serie_cep:
            valores_dia = [r["receita_liquida_dia"] for r in serie_cep]
            tend_dia = [r["tendencia_sazonal"] for r in serie_cep]
            lsc_dia = [r["lsc_3sigma"] for r in serie_cep]
            lic_dia = [r["lic_3sigma"] for r in serie_cep]
            idx_dias = list(range(len(valores_dia)))
            ax4.plot(idx_dias, valores_dia, color="#94a3b8", linewidth=1.0, alpha=0.80, label="Receita Diaria Paga")
            ax4.plot(idx_dias, tend_dia, color="#38bdf8", linestyle="-", linewidth=1.6, label="Tendencia Sazonal (MM15d)")
            ax4.plot(idx_dias, lsc_dia, color="#f43f5e", linestyle="--", linewidth=1.3, label=f"LSC +3s I-MR (s=R$ {carta['desvio_padrao']:,.0f})")
            ax4.plot(idx_dias, lic_dia, color="#fbbf24", linestyle=":", linewidth=1.2, label="LIC -3s I-MR")

            x_fora = [i for i, r in enumerate(serie_cep) if r["fora_de_controle"]]
            y_fora = [serie_cep[i]["receita_liquida_dia"] for i in x_fora]
            if x_fora:
                ax4.scatter(x_fora, y_fora, color="#f43f5e", s=45, zorder=5, label="Causa Especial (>3s)")
            ax4.legend(loc="upper right", facecolor="#1e293b", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5)

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
    """Automatiza a exportacao de todas as tabelas analiticas da camada Gold para exports/."""
    _cabecalho("Automacao: Exportar Camada Analitica Gold (CSV)")
    contagens = exportar_camada_gold(conn)
    for nome_arquivo, total in contagens.items():
        print(f"  [OK] Exportado: exports/{nome_arquivo:<32} ({total} registros)")
    print("\n  Camada analitica exportada com sucesso!\n")


def relatorio_executar_pipeline(conn: sqlite3.Connection) -> None:
    """Executa o pipeline completo (Faker -> Bronze -> Silver -> Gold) a partir do menu."""
    _cabecalho("Pipeline Arquitetura Medalha (Bronze -> Silver -> Gold)")
    resultado = run_pipeline(conn=conn)
    print("\n  Resumo da Execucao do Pipeline:")
    for tabela, m in resultado["silver"].items():
        print(
            f"  - {tabela:<14}: {m['lidas']:>5} lidas | "
            f"{m['validas']:>5} validas (Silver) | {m['rejeitadas']:>3} rejeitadas (Quarentena)"
        )
    print(f"\n  Arquivos analiticos atualizados em exports/: {len(resultado['exports'])}\n")


def relatorio_qualidade(conn: sqlite3.Connection) -> None:
    """Exibe o relatorio de registros bloqueados na quarentena silver_rejeitados."""
    _cabecalho("Qualidade de Dados: Quarentena Silver (silver_rejeitados)")
    linhas = resumo_qualidade_dados(conn)

    if not linhas:
        print("  Nenhum registro rejeitado na camada Silver (0 anomalias).\n")
        return

    print(f"  {'TABELA ORIGEM':<22} {'MOTIVO DA REJEICAO':<34} {'QTD':>8}")
    print(f"  {_linha('-', 22)} {_linha('-', 34)} {_linha('-', 8)}")
    total = 0
    for row in linhas:
        print(
            f"  {row['tabela_origem']:<22} {row['motivo']:<34} {row['total_rejeitados']:>8}"
        )
        total += row["total_rejeitados"]
    print(f"  {_linha('-', 66)}")
    print(f"  {'TOTAL BLOQUEADO NA QUARENTENA':<57} {total:>8}\n")


def relatorio_receita_mensal(conn: sqlite3.Connection) -> None:
    """Exibe receita mensal, variacao MoM (%) e media movel de 3 meses."""
    _cabecalho("Receita Mensal, Crescimento MoM (LAG) e Media Movel 3M")
    linhas = receita_mensal_mom(conn)

    if not linhas:
        _sem_resultados()
        return

    print(
        f"  {'MES':<9} {'PEDIDOS':>8} {'RECEITA LIQUIDA':>16}"
        f" {'MOM %':>10} {'MEDIA MOVEL 3M':>16}"
    )
    print(
        f"  {_linha('-', 9)} {_linha('-', 8)} {_linha('-', 16)}"
        f" {_linha('-', 10)} {_linha('-', 16)}"
    )
    for row in linhas:
        mom_str = f"{row['variacao_mom_pct']:>+8.1f}%" if row["variacao_mom_pct"] is not None else "     N/A "
        print(
            f"  {row['mes']:<9} {row['total_pedidos']:>8}"
            f"    R${row['receita_liquida']:>11.2f} {mom_str:>10}"
            f"    R${row['media_movel_3m']:>11.2f}"
        )
    print()


def relatorio_rfm(conn: sqlite3.Connection) -> None:
    """Exibe o resumo por segmento RFM e os top clientes."""
    _cabecalho("Segmentacao RFM (Recencia, Frequencia e Valor)")
    resumo = resumo_segmentos_rfm(conn)
    clientes = segmentacao_rfm(conn)

    if not resumo:
        _sem_resultados()
        return

    print("  Resumo dos Segmentos:")
    print(
        f"  {'SEGMENTO':<14} {'CLIENTES':>9} {'RECENCIA MED':>13}"
        f" {'FREQ MED':>9} {'RECEITA TOTAL':>15} {'SHARE %':>8}"
    )
    print(
        f"  {_linha('-', 14)} {_linha('-', 9)} {_linha('-', 13)}"
        f" {_linha('-', 9)} {_linha('-', 15)} {_linha('-', 8)}"
    )
    for r in resumo:
        print(
            f"  {r['segmento_rfm']:<14} {r['total_clientes']:>9}"
            f" {r['recencia_media_dias']:>10.1f} d"
            f" {r['frequencia_media']:>9.1f}   R${r['receita_segmento']:>11.2f}"
            f"  {r['share_receita_pct']:>6.1f}%"
        )

    print("\n  Top 15 Clientes na Matriz RFM:")
    print(
        f"  {'CLIENTE':<25} {'REC(d)':>6} {'FREQ':>5}"
        f" {'VALOR (R$)':>12} {'SCORES':>8} {'SEGMENTO':<12}"
    )
    print(
        f"  {_linha('-', 25)} {_linha('-', 6)} {_linha('-', 5)}"
        f" {_linha('-', 12)} {_linha('-', 8)} {_linha('-', 12)}"
    )
    for c in clientes[:15]:
        scores = f"{c['r_score']}-{c['f_score']}-{c['m_score']}"
        print(
            f"  {c['cliente'][:24]:<25} {c['recencia_dias']:>6} {c['frequencia_pedidos']:>5}"
            f"  R${c['valor_monetario']:>9.2f} {scores:>8} {c['segmento_rfm']:<12}"
        )
    print()


def relatorio_coorte_recompra(conn: sqlite3.Connection) -> None:
    """Exibe a taxa global de recompra e a retencao por coorte de entrada."""
    _cabecalho("Taxa de Recompra e Retencao por Coorte")
    recompra = taxa_recompra_global(conn)
    coortes = retencao_coorte(conn)

    if recompra:
        print(
            f"  Clientes Compradores : {recompra['clientes_compradores']}  |  "
            f"Recorrentes (2+ pedidos): {recompra['clientes_recorrentes']}  |  "
            f"Taxa de Recompra: {recompra['taxa_recompra_pct']:.1f}%  |  "
            f"Media Pedidos/Cliente: {recompra['media_pedidos_por_cliente']:.2f}\n"
        )

    if not coortes:
        _sem_resultados()
        return

    print(
        f"  {'COORTE':<9} {'MES ATIVO':<10} {'MES +N':>6}"
        f" {'ATIVOS':>8} {'INICIAIS':>9} {'RETENCAO %':>11}"
    )
    print(
        f"  {_linha('-', 9)} {_linha('-', 10)} {_linha('-', 6)}"
        f" {_linha('-', 8)} {_linha('-', 9)} {_linha('-', 11)}"
    )
    for row in coortes[:24]:
        print(
            f"  {row['coorte_mes']:<9} {row['mes_pedido']:<10} M+{row['indice_mes']:<4}"
            f" {row['clientes_ativos']:>8} {row['clientes_iniciais']:>9}"
            f"     {row['taxa_retencao_pct']:>6.1f}%"
        )
    if len(coortes) > 24:
        print(f"  ... exibindo 24 de {len(coortes)} celulas de coorte (completo em exports/coorte_retencao.csv).")
    print()


def relatorio_carta_controle(conn: sqlite3.Connection) -> None:
    """Exibe analise de cancelamentos por categoria/mes e Carta de Controle Lean Six Sigma."""
    _cabecalho("Cancelamentos e Carta de Controle Lean Six Sigma (3-Sigma)")
    cancs = cancelamento_categoria_mes(conn)
    carta = calcular_carta_controle_diaria(conn)

    print("  Parametros da Carta de Controle (Receita Liquida Diaria):")
    print(f"  - Media do Processo (LC)          : R$ {carta['media']:>10.2f}")
    print(f"  - Desvio-Padrao Amostral (Sigma)  : R$ {carta['desvio_padrao']:>10.2f}")
    print(f"  - Limite Superior (LSC = +3 Sigma): R$ {carta['lsc_3sigma']:>10.2f}")
    print(f"  - Limite Inferior (LIC = -3 Sigma): R$ {carta['lic_3sigma']:>10.2f}")
    print(f"  - Dias Analisados: {carta['total_dias']} | Dias Fora de Controle: {carta['dias_fora_controle']}\n")

    if carta["pontos_fora_controle"]:
        print("  Pontos Fora de Controle Estatistico (> +3 Sigma ou < -3 Sigma):")
        for pt in carta["pontos_fora_controle"]:
            print(
                f"    [!] Data: {pt['data_pedido']} | Receita: R$ {pt['receita_liquida_dia']:,.2f} "
                f"| Z-Score: {pt['z_score']:+.2f} | Pedidos: {pt['total_pedidos']}"
            )
        print()

    if cancs:
        print("  Cancelamento por Categoria e Mes (Top 12 registros mais recentes):")
        print(
            f"  {'MES':<9} {'CATEGORIA':<12} {'PEDIDOS':>8}"
            f" {'CANCELADOS':>11} {'TAXA %':>9} {'RECEITA PERDIDA':>16}"
        )
        print(
            f"  {_linha('-', 9)} {_linha('-', 12)} {_linha('-', 8)}"
            f" {_linha('-', 11)} {_linha('-', 9)} {_linha('-', 16)}"
        )
        for row in cancs[:12]:
            print(
                f"  {row['mes']:<9} {row['categoria']:<12} {row['total_pedidos']:>8}"
                f" {row['pedidos_cancelados']:>11}   {row['taxa_cancelamento_pct']:>6.1f}%"
                f"    R${row['receita_cancelada']:>11.2f}"
            )
    print()
