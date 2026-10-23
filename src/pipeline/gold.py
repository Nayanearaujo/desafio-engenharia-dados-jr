"""
Camada Gold: materializacao das views analiticas, calculo estatistico da
Carta de Controle Lean Six Sigma (3-Sigma) com pandas e exportacao de CSVs.
"""

import csv
import logging
import os
import sqlite3
from typing import Any
import pandas as pd

logger = logging.getLogger(__name__)

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SQL_GOLD = os.path.join(_DIR_RAIZ, "sql", "gold.sql")
PASTA_EXPORTS_PADRAO = os.path.join(_DIR_RAIZ, "exports")


def construir_gold(conn: sqlite3.Connection) -> None:
    """Executa o script sql/gold.sql para criar/atualizar todas as views gold_*."""
    with open(_SQL_GOLD, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    logger.info("Camada Gold atualizada com sucesso (views gold_* prontas).")


def calcular_carta_controle_diaria(
    conn: sqlite3.Connection, coluna_metrica: str = "receita_liquida_dia"
) -> dict[str, Any]:
    """
    Calcula os limites de controle estatistico de processo (CEP / Lean Six Sigma)
    sobre a serie diaria da camada Gold usando pandas para o desvio-padrao:
      - Media (LC) = mu
      - Limite Superior de Controle (LSC / UCL) = mu + 3 * sigma
      - Limite Inferior de Controle (LIC / LCL) = max(0, mu - 3 * sigma)
    Destaca os dias fora de controle estatistico.
    """
    construir_gold(conn)
    rows = [
        dict(r) for r in conn.execute("SELECT * FROM gold_receita_diaria").fetchall()
    ]
    if not rows:
        return {
            "metrica": coluna_metrica,
            "media": 0.0,
            "desvio_padrao": 0.0,
            "lsc_3sigma": 0.0,
            "lic_3sigma": 0.0,
            "total_dias": 0,
            "dias_fora_controle": 0,
            "pontos_fora_controle": [],
            "serie": [],
        }

    df = pd.DataFrame(rows)
    serie_valores = df[coluna_metrica].astype(float)
    media = float(serie_valores.mean())
    desvio = float(serie_valores.std(ddof=1)) if len(df) > 1 else 0.0

    lsc = round(media + 3.0 * desvio, 2)
    lic = round(max(0.0, media - 3.0 * desvio), 2)
    media_round = round(media, 2)
    desvio_round = round(desvio, 2)

    df["media_processo"] = media_round
    df["desvio_padrao"] = desvio_round
    df["lsc_3sigma"] = lsc
    df["lic_3sigma"] = lic
    df["z_score"] = (
        ((serie_valores - media) / desvio).round(2) if desvio > 0 else 0.0
    )
    df["fora_de_controle"] = (serie_valores > lsc) | (serie_valores < lic)
    df["status_cep"] = df["fora_de_controle"].map(
        lambda x: "FORA_DE_CONTROLE" if x else "SOB_CONTROLE"
    )

    registros = df.to_dict(orient="records")
    fora = [r for r in registros if r["fora_de_controle"]]

    return {
        "metrica": coluna_metrica,
        "media": media_round,
        "desvio_padrao": desvio_round,
        "lsc_3sigma": lsc,
        "lic_3sigma": lic,
        "total_dias": len(registros),
        "dias_fora_controle": len(fora),
        "pontos_fora_controle": fora,
        "serie": registros,
    }


def _salvar_csv(
    caminho: str, registros: list[dict[str, Any]], colunas: list[str] | None = None
) -> int:
    if not registros:
        return 0
    cols = colunas or list(registros[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(registros)
    return len(registros)


def exportar_camada_gold(
    conn: sqlite3.Connection, pasta_exports: str = PASTA_EXPORTS_PADRAO
) -> dict[str, int]:
    """Exporta todas as visoes Gold e a Carta de Controle para CSVs em exports/."""
    os.makedirs(pasta_exports, exist_ok=True)
    construir_gold(conn)

    consultas_views = [
        ("faturamento_categorias.csv", "SELECT * FROM gold_faturamento_categoria"),
        ("pareto_produtos_window.csv", "SELECT * FROM gold_pareto_produtos"),
        (
            "ltv_clientes.csv",
            "SELECT cliente, cidade, frequencia_pedidos AS total_pedidos, valor_monetario AS total_gasto FROM gold_rfm_clientes",
        ),
        ("pedidos_consolidados.csv", "SELECT * FROM gold_resumo_pedidos ORDER BY data_pedido DESC"),
        ("receita_mensal_mom.csv", "SELECT * FROM gold_receita_mensal"),
        ("rfm_clientes.csv", "SELECT * FROM gold_rfm_clientes"),
        ("coorte_retencao.csv", "SELECT * FROM gold_coorte_retencao"),
        ("taxa_recompra.csv", "SELECT * FROM gold_taxa_recompra"),
        ("cancelamento_categoria_mes.csv", "SELECT * FROM gold_cancelamento_categoria_mes"),
        ("qualidade_rejeitados.csv", "SELECT * FROM gold_qualidade_resumo"),
    ]

    contagens: dict[str, int] = {}
    for nome_arquivo, sql in consultas_views:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        caminho = os.path.join(pasta_exports, nome_arquivo)
        contagens[nome_arquivo] = _salvar_csv(caminho, rows)

    carta = calcular_carta_controle_diaria(conn)
    caminho_carta = os.path.join(pasta_exports, "carta_controle_diaria.csv")
    contagens["carta_controle_diaria.csv"] = _salvar_csv(
        caminho_carta, carta["serie"]
    )

    logger.info(
        "Exportacao Gold concluida em %s (%d arquivos gerados)",
        pasta_exports,
        len(contagens),
    )
    return contagens
