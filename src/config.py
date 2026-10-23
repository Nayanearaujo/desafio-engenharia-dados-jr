"""
Configuracao centralizada de caminhos, sementes e janelas de negocio do pipeline.
"""

import os

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SQL = os.path.join(DIR_RAIZ, "sql")
CAMINHO_BANCO = os.path.join(DIR_RAIZ, "loja_digital.db")
PASTA_RAW_PADRAO = os.path.join(DIR_RAIZ, "data", "raw")
PASTA_EXPORTS_PADRAO = os.path.join(DIR_RAIZ, "exports")

SEMENTE_PADRAO = 42
NUM_CLIENTES_PADRAO = 200
NUM_PEDIDOS_PADRAO = 5000

DATA_MIN_NEGOCIO = "2020-01-01"
DATA_MAX_NEGOCIO = "2030-12-31"
