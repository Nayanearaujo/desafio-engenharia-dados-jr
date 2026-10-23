"""
Testes unitarios para o motor de validacao de qualidade de dados (qualidade.py).
Cobre individualmente todas as regras da camada Silver e o relatorio de quarentena.
"""

import os
import sqlite3
import sys

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_RAIZ, "src"))

from pipeline.qualidade import (
    gerar_relatorio_qualidade,
    validar_chave_duplicada,
    validar_data_iso,
    validar_email,
    validar_fk_existente,
    validar_inteiro_nao_negativo,
    validar_numero_positivo,
    validar_obrigatorios,
    validar_status_pedido,
)


def test_validar_obrigatorios_sucesso_e_falha():
    reg_ok = {"id": "1", "nome": "Ana", "email": "ana@teste.com"}
    ok, motivo = validar_obrigatorios(reg_ok, ["id", "nome", "email"])
    assert ok is True
    assert motivo is None

    reg_nulo = {"id": "1", "nome": "   ", "email": "ana@teste.com"}
    ok2, motivo2 = validar_obrigatorios(reg_nulo, ["id", "nome", "email"])
    assert ok2 is False
    assert motivo2 == "nulo_obrigatorio:nome"


def test_validar_chave_duplicada_e_invalida():
    vistos = {1, 2, 3}
    ok, motivo = validar_chave_duplicada("4", vistos)
    assert ok is True
    assert motivo is None

    ok_dup, motivo_dup = validar_chave_duplicada("2", vistos)
    assert ok_dup is False
    assert motivo_dup == "chave_duplicada"

    ok_inv, motivo_inv = validar_chave_duplicada("abc", vistos)
    assert ok_inv is False
    assert motivo_inv == "chave_invalida"

    ok_neg, motivo_neg = validar_chave_duplicada("-5", vistos)
    assert ok_neg is False
    assert motivo_neg == "chave_invalida"


def test_validar_numero_positivo():
    assert validar_numero_positivo("197.50", "preco") == (True, None)
    assert validar_numero_positivo("0", "preco") == (
        False,
        "valor_menor_ou_igual_zero:preco",
    )
    assert validar_numero_positivo("-10", "quantidade") == (
        False,
        "valor_menor_ou_igual_zero:quantidade",
    )
    assert validar_numero_positivo("texto", "preco") == (
        False,
        "valor_nao_numerico:preco",
    )


def test_validar_inteiro_nao_negativo():
    assert validar_inteiro_nao_negativo("0", "estoque") == (True, None)
    assert validar_inteiro_nao_negativo("100", "estoque") == (True, None)
    assert validar_inteiro_nao_negativo("-1", "estoque") == (
        False,
        "inteiro_negativo:estoque",
    )
    assert validar_inteiro_nao_negativo("12.5", "estoque") == (
        False,
        "inteiro_invalido:estoque",
    )


def test_validar_status_pedido():
    for st in ("pago", "pendente", "cancelado", "PAGO"):
        assert validar_status_pedido(st) == (True, None)

    assert validar_status_pedido("em_analise") == (False, "status_fora_do_dominio")
    assert validar_status_pedido("") == (False, "status_fora_do_dominio")


def test_validar_email_formato_e_duplicidade():
    emails = {"ana@exemplo.com.br"}
    assert validar_email("novo.cliente@dominio.com", emails) == (True, None)
    assert validar_email("ana@exemplo.com.br", emails) == (False, "email_duplicado")
    assert validar_email("email_sem_arroba.com", emails) == (
        False,
        "email_formato_invalido",
    )


def test_validar_data_iso():
    assert validar_data_iso("2026-10-20", "data_pedido") == (True, None)
    assert validar_data_iso("2026-02-30", "data_pedido") == (
        False,
        "data_invalida:data_pedido",
    )
    assert validar_data_iso("20/10/2026", "criado_em") == (
        False,
        "data_invalida:criado_em",
    )


def test_validar_fk_existente():
    pais = {10, 20, 30}
    assert validar_fk_existente("20", pais, "cliente_id") == (True, None)
    assert validar_fk_existente("99", pais, "cliente_id") == (
        False,
        "fk_orfa:cliente_id",
    )
    assert validar_fk_existente("invalido", pais, "produto_id") == (
        False,
        "fk_orfa:produto_id",
    )


def test_gerar_relatorio_qualidade_exporta_csv(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE silver_rejeitados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela_origem TEXT NOT NULL,
            motivo TEXT NOT NULL,
            registro_raw TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO silver_rejeitados (tabela_origem, motivo, registro_raw) VALUES (?, ?, ?)",
        [
            ("bronze_pedidos", "status_fora_do_dominio", "{}"),
            ("bronze_pedidos", "status_fora_do_dominio", "{}"),
            ("bronze_clientes", "email_formato_invalido", "{}"),
        ],
    )
    resumo = gerar_relatorio_qualidade(conn, pasta_exports=str(tmp_path))
    assert len(resumo) == 2
    assert resumo[0]["motivo"] == "status_fora_do_dominio"
    assert resumo[0]["total_rejeitados"] == 2
    assert (tmp_path / "qualidade_rejeitados.csv").exists()
    conn.close()
