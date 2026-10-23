"""
Testes automatizados para o pipeline da Arquitetura Medalha (Bronze -> Silver -> Gold),
determinismo do Faker, idempotencia, KPIs Gold, carta de controle 3-Sigma e CLI/Menu.
"""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from src import database, main, queries, relatorios
from src.pipeline.executar import run_pipeline
from src.pipeline.gerar_dados import gerar_arquivos_raw
from src.pipeline.gold import calcular_carta_controle_diaria


def test_gerador_dados_deterministico_mesma_semente(tmp_path: Path) -> None:
    """Garante que a mesma semente gera exatamente os mesmos arquivos CSV."""
    pasta1 = tmp_path / "raw1"
    pasta2 = tmp_path / "raw2"

    c1 = gerar_arquivos_raw(str(pasta1), semente=42, num_clientes=30, num_pedidos=100)
    c2 = gerar_arquivos_raw(str(pasta2), semente=42, num_clientes=30, num_pedidos=100)

    assert c1 == c2
    for nome_arq in ["clientes.csv", "produtos.csv", "pedidos.csv", "itens_pedido.csv"]:
        conteudo1 = (pasta1 / nome_arq).read_text(encoding="utf-8")
        conteudo2 = (pasta2 / nome_arq).read_text(encoding="utf-8")
        assert conteudo1 == conteudo2


@pytest.fixture(scope="module")
def pipeline_isolado(tmp_path_factory: pytest.TempPathFactory):
    """Executa o pipeline medalha completo em banco temporario para testes rapidos."""
    base_dir = tmp_path_factory.mktemp("medalha_suite")
    caminho_banco = base_dir / "medalha_test.db"
    pasta_raw = base_dir / "raw"
    pasta_exports = base_dir / "exports"

    banco_original_db = database.CAMINHO_BANCO
    banco_original_main = main.CAMINHO_BANCO
    database.CAMINHO_BANCO = str(caminho_banco)
    main.CAMINHO_BANCO = str(caminho_banco)

    database.criar_banco()
    conn = database.conectar()

    resumo = run_pipeline(
        conn=conn,
        pasta_raw=str(pasta_raw),
        pasta_exports=str(pasta_exports),
        semente=42,
        regerar_csv=True,
    )
    yield {
        "conn": conn,
        "caminho_banco": str(caminho_banco),
        "pasta_raw": str(pasta_raw),
        "pasta_exports": str(pasta_exports),
        "resumo": resumo,
    }
    conn.close()
    database.CAMINHO_BANCO = banco_original_db
    main.CAMINHO_BANCO = banco_original_main


def test_bronze_silver_gold_fluxo_completo_e_quarentena(pipeline_isolado: dict) -> None:
    """Verifica contagens de Bronze, Silver, quarentena por motivo e views Gold."""
    conn: sqlite3.Connection = pipeline_isolado["conn"]
    resumo = pipeline_isolado["resumo"]

    assert resumo["bronze"]["bronze_clientes"] == 205
    assert resumo["bronze"]["bronze_produtos"] == 34
    assert resumo["bronze"]["bronze_pedidos"] == 5075

    assert resumo["silver"]["clientes"]["validas"] == 200
    assert resumo["silver"]["clientes"]["rejeitadas"] == 5
    assert resumo["silver"]["produtos"]["validas"] == 30
    assert resumo["silver"]["produtos"]["rejeitadas"] == 4
    assert resumo["silver"]["pedidos"]["validas"] == 5000
    assert resumo["silver"]["pedidos"]["rejeitadas"] == 75
    assert resumo["silver"]["itens_pedido"]["rejeitadas"] == 60

    # Verifica motivos registrados em silver_rejeitados
    relatorio_qual = queries.resumo_qualidade_dados(conn)
    assert len(relatorio_qual) > 0
    motivos_encontrados = {r["motivo"] for r in relatorio_qual}
    assert "chave_duplicada" in motivos_encontrados
    assert "email_formato_invalido" in motivos_encontrados
    assert "status_fora_do_dominio" in motivos_encontrados
    assert "fk_orfa:cliente_id" in motivos_encontrados

    # Verifica arquivo de auditoria de qualidade exportado
    arq_qualidade = Path(pipeline_isolado["pasta_exports"]) / "qualidade_rejeitados.csv"
    assert arq_qualidade.exists()


def test_idempotencia_pipeline_duas_execucoes(pipeline_isolado: dict) -> None:
    """Rodar o pipeline duas vezes deve manter exatamente as mesmas contagens."""
    conn: sqlite3.Connection = pipeline_isolado["conn"]
    pasta_raw = pipeline_isolado["pasta_raw"]
    pasta_exports = pipeline_isolado["pasta_exports"]

    resumo_1 = pipeline_isolado["resumo"]
    resumo_2 = run_pipeline(
        conn=conn,
        pasta_raw=pasta_raw,
        pasta_exports=pasta_exports,
        semente=42,
        regerar_csv=False,
    )

    assert resumo_1["bronze"] == resumo_2["bronze"]
    assert resumo_1["silver"] == resumo_2["silver"]
    assert len(resumo_1["qualidade"]) == len(resumo_2["qualidade"])


def test_kpis_gold_mom_rfm_coorte_cancelamento_e_carta_controle(pipeline_isolado: dict) -> None:
    """Valida todas as novas consultas Gold e a carta de controle 3-Sigma."""
    conn: sqlite3.Connection = pipeline_isolado["conn"]

    mom = queries.receita_mensal_mom(conn)
    assert len(mom) >= 10
    assert "variacao_mom_pct" in dict(mom[0])
    assert "media_movel_3m" in dict(mom[0])

    rfm = queries.segmentacao_rfm(conn)
    assert len(rfm) > 0
    segmentos = {r["segmento_rfm"] for r in rfm}
    assert segmentos.issubset({"Campeoes", "Leais", "Em risco", "Inativos"})

    resumo_rfm = queries.resumo_segmentos_rfm(conn)
    assert sum(r["total_clientes"] for r in resumo_rfm) == len(rfm)

    coortes = queries.retencao_coorte(conn)
    assert len(coortes) >= 6
    assert all(0 <= c["taxa_retencao_pct"] <= 100 for c in coortes)

    recompra = queries.taxa_recompra_global(conn)
    assert 0 < recompra["taxa_recompra_pct"] < 100
    assert recompra["clientes_recorrentes"] > 0

    canc_cat = queries.cancelamento_categoria_mes(conn)
    assert len(canc_cat) > 0
    assert "taxa_cancelamento_pct" in dict(canc_cat[0])

    carta = calcular_carta_controle_diaria(conn)
    assert carta["total_dias"] > 100
    assert carta["lsc_3sigma"] > carta["media"]
    assert carta["dias_fora_controle"] >= 1


def test_exportacoes_e_dashboard_executivo(pipeline_isolado: dict) -> None:
    """Testa exportacoes CSV e geracao do dashboard executivo em PNG."""
    conn: sqlite3.Connection = pipeline_isolado["conn"]
    relatorios.exportar_relatorios_csv(conn)
    relatorios.gerar_grafico_faturamento(conn)
    caminho_img = Path(__file__).resolve().parent.parent / "assets" / "dashboard_executivo.png"
    assert caminho_img.exists()
    assert caminho_img.stat().st_size > 10000


def test_menu_opcoes_1_a_20_e_entradas_invalidas(pipeline_isolado: dict) -> None:
    """Garante que o menu interativo navega pelas opcoes 1 a 20 e trata entradas invalidas."""
    entradas = iter([
        "1",
        "2", "1",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8", "500",
        "9",
        "10",
        "11",
        "12", "Curso Menu Teste", "1", "199.90", "50",
        "14",
        "16",
        "17",
        "18",
        "19",
        "20",
        "99",
        "0",
    ])
    with patch("builtins.input", lambda _: next(entradas)):
        main.main([])


def test_cli_parse_args(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Testa parsing de flags --pipeline e --demo."""
    args_pipe = main._parse_args(["--pipeline"])
    assert args_pipe.pipeline is True
    assert args_pipe.demo is False

    args_demo = main._parse_args(["--demo"])
    assert args_demo.demo is True
    assert args_demo.pipeline is False

    # Testa execucao de --demo saindo imediatamente com 0
    banco_demo = tmp_path / "demo_cli.db"
    monkeypatch.setattr(database, "CAMINHO_BANCO", str(banco_demo))
    monkeypatch.setattr(main, "CAMINHO_BANCO", str(banco_demo))
    with patch("builtins.input", lambda _: "0"):
        main.main(["--demo"])
