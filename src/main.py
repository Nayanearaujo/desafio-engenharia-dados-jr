"""
Ponto de entrada da aplicacao.
Suporta argumentos de linha de comando (--pipeline, --demo) e menu interativo.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import relatorios
from database import CAMINHO_BANCO, conectar, criar_banco
from pipeline.executar import run_pipeline
from pipeline.gold import construir_gold

OPCOES = {
    "1": ("Listar todos os produtos", relatorios.relatorio_produtos),
    "2": ("Filtrar produtos por categoria", relatorios.relatorio_categoria),
    "3": ("Listar clientes cadastrados", relatorios.relatorio_clientes),
    "4": ("Pedidos detalhados (View SQL)", relatorios.relatorio_pedidos),
    "5": ("Ranking de produtos mais vendidos", relatorios.relatorio_ranking),
    "6": ("Faturamento por categoria", relatorios.relatorio_faturamento),
    "7": ("Clientes por volume de compras", relatorios.relatorio_clientes_vip),
    "8": ("Clientes acima de meta (HAVING)", relatorios.relatorio_clientes_meta),
    "9": ("Produtos acima da media (Subquery)", relatorios.relatorio_produtos_acima_media),
    "10": ("Desempenho dos produtos (CTE + CASE WHEN)", relatorios.relatorio_desempenho_cte),
    "11": ("KPIs executivos e Curva de Pareto (Window Function)", relatorios.relatorio_kpis_pareto),
    "12": ("Cadastrar novo produto", relatorios.cadastrar_produto),
    "13": ("Gerar Dashboard Executivo (Matplotlib)", relatorios.gerar_grafico_faturamento),
    "14": ("Automatizar exportacao analitica (CSV)", relatorios.exportar_relatorios_csv),
    "15": ("Executar pipeline Medalha (Bronze -> Silver -> Gold)", relatorios.relatorio_executar_pipeline),
    "16": ("Relatorio de qualidade e quarentena (Silver)", relatorios.relatorio_qualidade),
    "17": ("Receita mensal, MoM e media movel 3M (Gold)", relatorios.relatorio_receita_mensal),
    "18": ("Segmentacao RFM de clientes (Gold)", relatorios.relatorio_rfm),
    "19": ("Taxa de recompra e retencao por coorte (Gold)", relatorios.relatorio_coorte_recompra),
    "20": ("Cancelamentos e Carta de Controle 3-Sigma (Gold)", relatorios.relatorio_carta_controle),
}


def exibir_menu() -> None:
    print("\n" + "=" * 62)
    print("  LOJA DIGITAL - PAINEL DE RELATORIOS E ARQUITETURA MEDALHA")
    print("=" * 62)
    for chave, (descricao, _) in OPCOES.items():
        print(f"  [{chave:>2}] {descricao}")
    print("  [ 0] Sair")
    print("-" * 62)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Loja Digital - Pipeline Medalha (Bronze, Silver, Gold) e Analytics"
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Gera CSVs sinteticos em data/raw/ e executa a carga completa (Faker -> Bronze -> Silver -> Gold).",
    )
    parser.add_argument(
        "--reprocessar",
        action="store_true",
        help="Reprocessa os CSVs ja existentes em data/raw/ (Bronze -> Silver -> Gold) sem regerar dados sinteticos.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Inicializa o banco com o seed.sql pequeno de demonstracao antes de abrir o menu.",
    )
    return parser.parse_args(argv)


def _banco_possui_pipeline() -> bool:
    """Verifica se o arquivo SQLite ja existe e contem carga do pipeline Medalha."""
    if not os.path.exists(CAMINHO_BANCO):
        return False
    try:
        conn = conectar()
        total = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        conn.close()
        return int(total) > 50
    except Exception:  # noqa: BLE001
        return False


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.pipeline or args.reprocessar:
        if not os.path.exists(CAMINHO_BANCO):
            criar_banco()
        conn = conectar()
        try:
            run_pipeline(conn=conn, regerar_csv=not args.reprocessar)
            relatorios.gerar_grafico_faturamento(conn)
        finally:
            conn.close()
        return

    if args.demo or not _banco_possui_pipeline():
        criar_banco()
    else:
        conn_init = conectar()
        construir_gold(conn_init)
        conn_init.close()

    try:
        conn = conectar()
    except Exception:  # noqa: BLE001
        print("[ERRO] Nao foi possivel conectar ao banco. Encerrando.")
        sys.exit(1)

    try:
        while True:
            exibir_menu()

            try:
                escolha = input("  Escolha uma opcao: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Encerrando sistema.\n")
                break

            if escolha == "0":
                print("\n  Encerrando sistema.\n")
                break

            if escolha not in OPCOES:
                print(f"\n  Opcao '{escolha}' invalida. Tente novamente.")
                continue

            _, funcao = OPCOES[escolha]

            try:
                funcao(conn)
            except Exception as erro:  # noqa: BLE001
                print(f"\n  [ERRO] Falha ao gerar relatorio: {erro}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
