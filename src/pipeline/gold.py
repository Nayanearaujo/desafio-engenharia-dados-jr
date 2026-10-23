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
    Calcula a Carta de Controle de Individuos e Amplitude Movel (I-MR) do Lean Six Sigma
    ajustada para sazonalidade sobre a serie diaria da camada Gold:
      - Tendencia sazonal local (T_t): media movel centrada de 15 dias
      - Residuo dessazonalizado (e_t): y_t - T_t
      - Amplitude Movel (MR_t): |e_t - e_{t-1}|
      - Sigma de curto prazo (I-MR): sigma_imr = MR_medio / 1.128 (constante d2 para n=2)
      - Banda dinamica 3-Sigma: T_t +/- 3 * sigma_imr
    Tambem registra o desvio-padrao amostral global para comparacao metodologica.
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
            "desvio_padrao_amostral": 0.0,
            "mr_medio": 0.0,
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
    desvio_amostral = float(serie_valores.std(ddof=1)) if len(df) > 1 else 0.0

    # Ajuste sazonal por media movel centrada de 15 dias e estimador I-MR (d2 = 1.128)
    tendencia = serie_valores.rolling(window=15, center=True, min_periods=1).mean()
    residuo = serie_valores - tendencia
    amplitude_movel = residuo.diff().abs()
    mr_medio = float(amplitude_movel.mean()) if len(df) > 1 else 0.0
    sigma_imr = (mr_medio / 1.128) if mr_medio > 0 else desvio_amostral

    lsc_global = round(media + 3.0 * sigma_imr, 2)
    lic_global = round(max(0.0, media - 3.0 * sigma_imr), 2)
    media_round = round(media, 2)
    sigma_imr_round = round(sigma_imr, 2)
    desvio_amostral_round = round(desvio_amostral, 2)
    mr_medio_round = round(mr_medio, 2)

    df["media_processo"] = media_round
    df["tendencia_sazonal"] = tendencia.round(2)
    df["residuo_sazonal"] = residuo.round(2)
    df["amplitude_movel_mr"] = amplitude_movel.fillna(0.0).round(2)
    df["desvio_padrao"] = sigma_imr_round
    df["desvio_padrao_amostral"] = desvio_amostral_round
    df["lsc_3sigma"] = (tendencia + 3.0 * sigma_imr).round(2)
    df["lic_3sigma"] = (tendencia - 3.0 * sigma_imr).clip(lower=0.0).round(2)
    df["z_score"] = (
        (residuo / sigma_imr).round(2) if sigma_imr > 0 else 0.0
    )
    df["fora_de_controle"] = residuo.abs() > (3.0 * sigma_imr)
    df["status_cep"] = df["fora_de_controle"].map(
        lambda x: "FORA_DE_CONTROLE" if x else "SOB_CONTROLE"
    )

    registros = df.to_dict(orient="records")
    fora = [r for r in registros if r["fora_de_controle"]]

    return {
        "metrica": coluna_metrica,
        "media": media_round,
        "desvio_padrao": sigma_imr_round,
        "desvio_padrao_amostral": desvio_amostral_round,
        "mr_medio": mr_medio_round,
        "lsc_3sigma": lsc_global,
        "lic_3sigma": lic_global,
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
