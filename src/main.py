"""
main.py
-------
Ponto de entrada da aplicação.
Exibe o menu no terminal e orquestra a navegação entre relatórios.

Uso:
    python src/main.py
"""

import sys
import os

# Garante que 'src/' esteja no path quando rodado de fora do diretório
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import criar_banco, conectar
import relatorios


# ── Menu ─────────────────────────────────────────────────────────────────────

OPCOES = {
    "1": ("📦 Listar todos os produtos",            relatorios.relatorio_produtos),
    "2": ("🔍 Filtrar produtos por categoria",       relatorios.relatorio_categoria),
    "3": ("👥 Listar clientes cadastrados",          relatorios.relatorio_clientes),
    "4": ("🧾 Pedidos detalhados (via View SQL)",    relatorios.relatorio_pedidos),
    "5": ("🏆 Ranking: produtos mais vendidos",      relatorios.relatorio_ranking),
    "6": ("💰 Faturamento por categoria",            relatorios.relatorio_faturamento),
    "7": ("⭐ Clientes por volume de compras",       relatorios.relatorio_clientes_vip),
}


def exibir_menu() -> None:
    print("\n" + "═" * 55)
    print("  🛒  LOJA DIGITAL — PAINEL DE RELATÓRIOS")
    print("═" * 55)
    for chave, (descricao, _) in OPCOES.items():
        print(f"  [{chave}] {descricao}")
    print("  [0] Sair")
    print("─" * 55)


def main() -> None:
    # 1. Cria/recria o banco na primeira execução
    criar_banco()

    # 2. Abre conexão persistente para a sessão inteira
    try:
        conn = conectar()
    except Exception:
        print("[ERRO] Não foi possível conectar ao banco. Encerrando.")
        sys.exit(1)

    # 3. Loop principal do menu
    try:
        while True:
            exibir_menu()

            try:
                escolha = input("  Escolha uma opção: ").strip()
            except (EOFError, KeyboardInterrupt):
                # Ctrl+C ou Ctrl+D: encerra sem stack trace
                print("\n\n  Até logo! 👋\n")
                break

            if escolha == "0":
                print("\n  Até logo! 👋\n")
                break

            if escolha not in OPCOES:
                print(f"\n  ⚠️  Opção '{escolha}' inválida. Tente novamente.")
                continue

            _, funcao = OPCOES[escolha]

            try:
                funcao(conn)
            except Exception as erro:
                # Captura erros de query sem derrubar o programa
                print(f"\n  [ERRO] Falha ao gerar relatório: {erro}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
