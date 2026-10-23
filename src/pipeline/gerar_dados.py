"""
Gerador de dados sinteticos deterministico com Faker (pt_BR) para a camada Bronze.
Injeta entre 1% e 3% de anomalias controladas para validacao na camada Silver.
"""

import csv
import logging
import os
import random
from datetime import date, timedelta
from typing import Any

from faker import Faker

logger = logging.getLogger(__name__)

SEMENTE_PADRAO = 42

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASTA_RAW_PADRAO = os.path.join(_DIR_RAIZ, "data", "raw")

CATALOGO_PRODUTOS_BASE = [
    # Top 6 produtos (concentram ~80% da receita para a Curva de Pareto 80/20)
    ("Formacao Completa Engenharia de Dados", "Curso", 497.00, 500, 24.0),
    ("Bootcamp Arquitetura Medalha e Lakehouse", "Curso", 397.00, 500, 19.0),
    ("Fundamentos de IA Generativa com Python", "Curso", 347.00, 500, 15.0),
    ("Python do Zero ao Avancado para Dados", "Curso", 297.00, 500, 12.0),
    ("SQL Avancado e Tuning de Consultas", "Curso", 247.00, 500, 10.0),
    ("Especializacao Lean Six Sigma Analytics", "Curso", 297.00, 500, 9.0),
    # Demais 24 produtos (cauda longa de Cursos, E-books e Templates)
    ("Dominando Git, GitHub e CI/CD", "Curso", 147.00, 500, 1.2),
    ("Orquestracao de Pipelines com Airflow", "Curso", 197.00, 500, 1.0),
    ("Modelagem Dimensional e Star Schema", "Curso", 167.00, 500, 0.9),
    ("Testes Automatizados com Pytest", "Curso", 127.00, 500, 0.8),
    ("Introducao ao Apache Spark e PySpark", "Curso", 217.00, 500, 0.8),
    ("Docker e Containers para Dados", "Curso", 157.00, 500, 0.7),
    ("Governanca e Qualidade de Dados", "Curso", 177.00, 500, 0.6),
    ("E-book Guia Definitivo de SQL", "E-book", 47.00, 999, 0.8),
    ("E-book Boas Praticas em Python", "E-book", 37.00, 999, 0.7),
    ("E-book Estatistica Aplicada a Processos", "E-book", 57.00, 999, 0.6),
    ("E-book Pack de Prompts para Engenharia", "E-book", 47.00, 999, 0.6),
    ("E-book Manual do Engenheiro de Dados Jr", "E-book", 39.00, 999, 0.5),
    ("E-book Dicionario de Expressoes Regulares", "E-book", 29.00, 999, 0.4),
    ("E-book Arquitetura Cloud para Iniciantes", "E-book", 49.00, 999, 0.4),
    ("E-book Storytelling com Dados Executivos", "E-book", 45.00, 999, 0.4),
    ("E-book Preparacao para Entrevistas SQL", "E-book", 55.00, 999, 0.4),
    ("Template Dashboard Executivo Matplotlib", "Template", 35.00, 999, 0.5),
    ("Template Controle Estatistico de Processo", "Template", 42.00, 999, 0.4),
    ("Template Checklist de Pipeline ETL", "Template", 27.00, 999, 0.4),
    ("Template Documentacao de Data Warehouse", "Template", 32.00, 999, 0.3),
    ("Template Matriz RFM e Coorte em SQL", "Template", 39.00, 999, 0.3),
    ("Template Monitoramento de SLA de Dados", "Template", 29.00, 999, 0.3),
    ("Template Estrutura de Projeto Python", "Template", 25.00, 999, 0.3),
    ("Template Auditoria de Qualidade Silver", "Template", 33.00, 999, 0.3),
]


def gerar_arquivos_raw(
    pasta_destino: str = PASTA_RAW_PADRAO,
    semente: int = SEMENTE_PADRAO,
    num_clientes: int = 200,
    num_pedidos: int = 5000,
) -> dict[str, int]:
    """
    Gera os 4 arquivos CSV na pasta data/raw/ com semente fixa e sujeira controlada.
    Retorna dicionario com a quantidade total de linhas geradas em cada arquivo.
    """
    os.makedirs(pasta_destino, exist_ok=True)
    rng = random.Random(semente)
    fake = Faker("pt_BR")
    fake.seed_instance(semente)

    cidades_br = [
        "São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba",
        "Porto Alegre", "Recife", "Salvador", "Fortaleza", "Brasília",
        "Campinas", "Florianópolis", "Goiânia",
    ]

    # 1. Clientes (~200 validos + 5 anomalias = ~2.4% de sujeira)
    linhas_clientes: list[dict[str, Any]] = []
    data_base_cadastro = date(2025, 10, 1)
    emails_usados: set[str] = set()

    for cid in range(1, num_clientes + 1):
        nome = fake.name()
        letras_ascii = "".join(
            ch for ch in nome.lower() if "a" <= ch <= "z"
        )[:10] or "cliente"
        email = f"{letras_ascii}.{cid}@exemplo.com.br"
        emails_usados.add(email)
        dias_offset = rng.randint(0, 180)
        criado_em = (data_base_cadastro + timedelta(days=dias_offset)).isoformat()
        cidade = rng.choice(cidades_br)
        linhas_clientes.append({
            "id": str(cid),
            "nome": nome,
            "email": email,
            "cidade": cidade,
            "criado_em": criado_em,
        })

    # Anomalias em clientes
    linhas_clientes.extend([
        {"id": "10", "nome": "Cliente Duplicado", "email": "dup10@exemplo.com.br", "cidade": "São Paulo", "criado_em": "2025-11-10"},
        {"id": str(num_clientes + 1), "nome": "", "email": "sem.nome@exemplo.com.br", "cidade": "Curitiba", "criado_em": "2025-11-12"},
        {"id": str(num_clientes + 2), "nome": "Email Invalido Silva", "email": "email_invalido_sem_arroba", "cidade": "Recife", "criado_em": "2025-11-15"},
        {"id": str(num_clientes + 3), "nome": "Data Invalida Souza", "email": "data.invalida@exemplo.com.br", "cidade": "Salvador", "criado_em": "2025-13-40"},
        {"id": str(num_clientes + 4), "nome": "Email Repetido", "email": linhas_clientes[0]["email"], "cidade": "Fortaleza", "criado_em": "2025-11-20"},
    ])

    # 2. Produtos (30 validos + 4 anomalias)
    linhas_produtos: list[dict[str, Any]] = []
    pesos_produtos: list[float] = []
    precos_map: dict[int, float] = {}

    for idx, (nome_prod, cat, preco, estoque, peso) in enumerate(CATALOGO_PRODUTOS_BASE, start=1):
        linhas_produtos.append({
            "id": str(idx),
            "nome": nome_prod,
            "categoria": cat,
            "preco": f"{preco:.2f}",
            "estoque": str(estoque),
        })
        pesos_produtos.append(peso)
        precos_map[idx] = preco

    linhas_produtos.extend([
        {"id": "1", "nome": "Produto ID Duplicado", "categoria": "Curso", "preco": "199.00", "estoque": "10"},
        {"id": "31", "nome": "Curso Preco Negativo", "categoria": "Curso", "preco": "-49.90", "estoque": "100"},
        {"id": "32", "nome": "E-book Preco Zero", "categoria": "E-book", "preco": "0", "estoque": "100"},
        {"id": "33", "nome": "", "categoria": "Template", "preco": "29.90", "estoque": "50"},
    ])

    # 3. Pedidos (~5000 validos em 12 meses + ~1.5% anomalias) e 4. Itens de Pedido
    linhas_pedidos: list[dict[str, Any]] = []
    linhas_itens: list[dict[str, Any]] = []

    inicio_pedidos = date(2025, 11, 1)
    total_dias = 350  # ~12 meses (nov/2025 a out/2026)

    # Perfis de frequencia dos clientes para RFM e Coorte realistas
    clientes_vips = list(range(1, int(num_clientes * 0.20) + 1))
    clientes_regulares = list(range(int(num_clientes * 0.20) + 1, int(num_clientes * 0.82) + 1))
    clientes_compra_unica = list(range(int(num_clientes * 0.82) + 1, num_clientes + 1))

    ids_produtos_validos = list(range(1, len(CATALOGO_PRODUTOS_BASE) + 1))
    item_id_seq = 1

    # Seleciona 2 dias especificos para terem anomalia de processo (> 3 sigma na carta de controle)
    dia_pico_1 = (inicio_pedidos + timedelta(days=95)).isoformat()
    dia_pico_2 = (inicio_pedidos + timedelta(days=245)).isoformat()

    for pid in range(1, num_pedidos + 1):
        sorteio_grupo = rng.random()
        if sorteio_grupo < 0.52 or not clientes_regulares:
            cid = rng.choice(clientes_vips)
        elif sorteio_grupo < 0.96 or not clientes_compra_unica:
            cid = rng.choice(clientes_regulares)
        else:
            cid = clientes_compra_unica.pop(0)

        dia_offset = int(rng.triangular(0, total_dias, total_dias * 0.65))
        data_ped = (inicio_pedidos + timedelta(days=dia_offset)).isoformat()

        r_status = rng.random()
        if r_status < 0.76:
            status = "pago"
        elif r_status < 0.90:
            status = "pendente"
        else:
            status = "cancelado"

        linhas_pedidos.append({
            "id": str(pid),
            "cliente_id": str(cid),
            "data_pedido": data_ped,
            "status": status,
        })

        # Quantidade de itens no pedido (1 a 3)
        qtd_itens = 1 if rng.random() < 0.72 else rng.randint(2, 3)
        prods_escolhidos = rng.choices(ids_produtos_validos, weights=pesos_produtos, k=qtd_itens)
        # Evita repetir o mesmo produto no mesmo pedido
        for prod_id in dict.fromkeys(prods_escolhidos):
            qtd = 1 if rng.random() < 0.82 else rng.randint(2, 3)
            if data_ped in (dia_pico_1, dia_pico_2) and status == "pago":
                qtd = rng.randint(4, 6)
            preco_u = precos_map[prod_id]
            linhas_itens.append({
                "id": str(item_id_seq),
                "pedido_id": str(pid),
                "produto_id": str(prod_id),
                "quantidade": str(qtd),
                "preco_unit": f"{preco_u:.2f}",
            })
            item_id_seq += 1

    # Injeta ~1.5% de anomalias em pedidos (75 registros invalidos)
    motivos_pedidos_sujos = [
        ("15", "1", "2026-03-10", "pago"),                  # ID duplicado
        (str(num_pedidos + 1), "", "2026-03-11", "pago"),   # cliente_id nulo
        (str(num_pedidos + 2), "99999", "2026-03-12", "pago"),  # FK cliente orfa
        (str(num_pedidos + 3), "2", "2026-03-15", "em_analise"),  # status invalido
        (str(num_pedidos + 4), "3", "2026-02-30", "pago"),  # data invalida
    ]
    for idx_extra in range(5, 75):
        pid_sujo = str(num_pedidos + idx_extra)
        tipo_erro = idx_extra % 5
        if tipo_erro == 0:
            motivos_pedidos_sujos.append(("25", "4", "2026-04-01", "pago"))
        elif tipo_erro == 1:
            motivos_pedidos_sujos.append((pid_sujo, "", "2026-04-02", "pendente"))
        elif tipo_erro == 2:
            motivos_pedidos_sujos.append((pid_sujo, "88888", "2026-04-03", "pago"))
        elif tipo_erro == 3:
            motivos_pedidos_sujos.append((pid_sujo, "5", "2026-04-04", "estornado"))
        else:
            motivos_pedidos_sujos.append((pid_sujo, "6", "data_invalida", "pago"))

    for pid_s, cid_s, dt_s, st_s in motivos_pedidos_sujos:
        linhas_pedidos.append({
            "id": pid_s,
            "cliente_id": cid_s,
            "data_pedido": dt_s,
            "status": st_s,
        })

    # Injeta ~1% de anomalias em itens_pedido (60 registros invalidos)
    for idx_item_sujo in range(1, 61):
        id_s = str(item_id_seq + idx_item_sujo)
        tipo_erro = idx_item_sujo % 5
        if tipo_erro == 0:
            linhas_itens.append({"id": "10", "pedido_id": "1", "produto_id": "1", "quantidade": "1", "preco_unit": "497.00"})
        elif tipo_erro == 1:
            linhas_itens.append({"id": id_s, "pedido_id": "1", "produto_id": "1", "quantidade": "0", "preco_unit": "497.00"})
        elif tipo_erro == 2:
            linhas_itens.append({"id": id_s, "pedido_id": "1", "produto_id": "2", "quantidade": "1", "preco_unit": "-99.00"})
        elif tipo_erro == 3:
            linhas_itens.append({"id": id_s, "pedido_id": "999999", "produto_id": "1", "quantidade": "1", "preco_unit": "497.00"})
        else:
            linhas_itens.append({"id": id_s, "pedido_id": "2", "produto_id": "7777", "quantidade": "1", "preco_unit": "100.00"})

    arquivos = [
        ("clientes.csv", ["id", "nome", "email", "cidade", "criado_em"], linhas_clientes),
        ("produtos.csv", ["id", "nome", "categoria", "preco", "estoque"], linhas_produtos),
        ("pedidos.csv", ["id", "cliente_id", "data_pedido", "status"], linhas_pedidos),
        ("itens_pedido.csv", ["id", "pedido_id", "produto_id", "quantidade", "preco_unit"], linhas_itens),
    ]

    contagens: dict[str, int] = {}
    for nome_arq, colunas, registros in arquivos:
        caminho = os.path.join(pasta_destino, nome_arq)
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            writer.writerows(registros)
        contagens[nome_arq] = len(registros)
        logger.info("Arquivo raw gerado: %s (%d linhas)", nome_arq, len(registros))

    return contagens
