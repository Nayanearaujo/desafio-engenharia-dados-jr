"""
Regras de validacao de qualidade de dados para a transicao Bronze -> Silver.
Cada regra possui funcao isolada para facilitar testes unitarios e auditoria.
"""

import csv
import logging
import os
import re
import sqlite3
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

STATUS_PEDIDO_VALIDOS = {"pago", "pendente", "cancelado"}
_REGEX_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASTA_EXPORTS_PADRAO = os.path.join(_DIR_RAIZ, "exports")


def validar_obrigatorios(
    registro: dict[str, Any], campos: list[str]
) -> tuple[bool, str | None]:
    """Verifica se todos os campos obrigatorios estao preenchidos e nao nulos."""
    for campo in campos:
        valor = registro.get(campo)
        if valor is None or str(valor).strip() == "":
            return False, f"nulo_obrigatorio:{campo}"
    return True, None


def validar_chave_duplicada(
    valor_id: Any, ids_vistos: set[int]
) -> tuple[bool, str | None]:
    """Verifica se o ID e um inteiro positivo e se ainda nao apareceu no lote."""
    try:
        id_int = int(str(valor_id).strip())
        if id_int <= 0:
            return False, "chave_invalida"
    except (ValueError, TypeError):
        return False, "chave_invalida"

    if id_int in ids_vistos:
        return False, "chave_duplicada"
    return True, None


def validar_numero_positivo(
    valor: Any, nome_campo: str = "valor"
) -> tuple[bool, str | None]:
    """Verifica se o valor numerico (preco ou quantidade) e estritamente maior que zero."""
    try:
        numero = float(str(valor).strip())
    except (ValueError, TypeError):
        return False, f"valor_nao_numerico:{nome_campo}"

    if numero <= 0:
        return False, f"valor_menor_ou_igual_zero:{nome_campo}"
    return True, None


def validar_inteiro_nao_negativo(
    valor: Any, nome_campo: str = "estoque"
) -> tuple[bool, str | None]:
    """Verifica se o valor e um inteiro maior ou igual a zero."""
    try:
        numero = int(str(valor).strip())
    except (ValueError, TypeError):
        return False, f"inteiro_invalido:{nome_campo}"

    if numero < 0:
        return False, f"inteiro_negativo:{nome_campo}"
    return True, None


def validar_status_pedido(status: Any) -> tuple[bool, str | None]:
    """Verifica se o status do pedido pertence ao dominio permitido."""
    texto = str(status or "").strip().lower()
    if texto not in STATUS_PEDIDO_VALIDOS:
        return False, "status_fora_do_dominio"
    return True, None


def validar_email(
    email: Any, emails_vistos: set[str] | None = None
) -> tuple[bool, str | None]:
    """Valida formato de e-mail e unicidade opcional no lote."""
    texto = str(email or "").strip().lower()
    if not _REGEX_EMAIL.match(texto):
        return False, "email_formato_invalido"
    if emails_vistos is not None and texto in emails_vistos:
        return False, "email_duplicado"
    return True, None


def validar_data_iso(
    valor_data: Any, nome_campo: str = "data"
) -> tuple[bool, str | None]:
    """Verifica se a string representa uma data ISO valida (YYYY-MM-DD)."""
    texto = str(valor_data or "").strip()
    try:
        date.fromisoformat(texto)
    except ValueError:
        return False, f"data_invalida:{nome_campo}"
    return True, None


def validar_fk_existente(
    valor_fk: Any, ids_pai_validos: set[int], nome_fk: str = "fk"
) -> tuple[bool, str | None]:
    """Verifica se a chave estrangeira aponta para um registro pai valido."""
    try:
        fk_int = int(str(valor_fk).strip())
    except (ValueError, TypeError):
        return False, f"fk_orfa:{nome_fk}"

    if fk_int not in ids_pai_validos:
        return False, f"fk_orfa:{nome_fk}"
    return True, None


def gerar_relatorio_qualidade(
    conn: sqlite3.Connection, pasta_exports: str = PASTA_EXPORTS_PADRAO
) -> list[dict[str, Any]]:
    """
    Consulta a contagem de registros em silver_rejeitados por tabela e motivo,
    registra no logging e exporta para exports/qualidade_rejeitados.csv.
    """
    os.makedirs(pasta_exports, exist_ok=True)
    cursor = conn.execute(
        """
        SELECT
            tabela_origem,
            motivo,
            COUNT(*) AS total_rejeitados
        FROM silver_rejeitados
        GROUP BY tabela_origem, motivo
        ORDER BY total_rejeitados DESC, tabela_origem, motivo
        """
    )
    linhas = [dict(row) for row in cursor.fetchall()]

    caminho_csv = os.path.join(pasta_exports, "qualidade_rejeitados.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["tabela_origem", "motivo", "total_rejeitados"]
        )
        writer.writeheader()
        writer.writerows(linhas)

    total_geral = sum(item["total_rejeitados"] for item in linhas)
    logger.info(
        "Relatorio de qualidade gerado em %s (%d rejeicoes totais em %d motivos)",
        caminho_csv,
        total_geral,
        len(linhas),
    )
    for item in linhas:
        logger.info(
            "  [QUARENTENA] %s | %s: %d registro(s)",
            item["tabela_origem"],
            item["motivo"],
            item["total_rejeitados"],
        )

    return linhas
