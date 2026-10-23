"""
Ponto de entrada da aplicacao.
Exibe o menu interativo no terminal e chama os relatorios.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import conectar, criar_banco
import relatorios


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
}


def exibir_menu() -> None:
    print("\n" + "=" * 55)
    print("  LOJA DIGITAL - PAINEL DE RELATORIOS")
    print("=" * 55)
    for chave, (descricao, _) in OPCOES.items():
        print(f"  [{chave:>2}] {descricao}")
    print("  [ 0] Sair")
    print("-" * 55)


def main() -> None:
    criar_banco()

    try:
        conn = conectar()
    except Exception:
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
            except Exception as erro:
                print(f"\n  [ERRO] Falha ao gerar relatorio: {erro}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
