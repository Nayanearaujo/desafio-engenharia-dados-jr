# Loja Digital - Painel de Relatorios e Analytics

Projeto final desenvolvido para a Trilha de Engenharia de Dados Junior.

Aplicacao de terminal que utiliza Python e SQLite para gerenciar dados, calcular indicadores executivos (KPIs), exportar camadas analiticas em CSV e gerar visualizacoes de vendas de uma loja de produtos digitais (cursos, e-books e templates).

## Dashboard Executivo Gerado pelo Sistema

![Dashboard Executivo](assets/dashboard_executivo.png)

## Estrutura do Projeto

```text
desafio-engenharia-dados-jr/
├── assets/
│   └── dashboard_executivo.png  # Painel visual gerado via Matplotlib
├── sql/
│   ├── schema.sql               # Criacao das tabelas, relacionamentos e view
│   └── seed.sql                 # Dados iniciais de exemplo
├── src/
│   ├── main.py                  # Menu interativo no terminal
│   ├── database.py              # Conexao com o SQLite e criacao do banco
│   ├── queries.py               # Consultas SQL e calculo de KPIs
│   └── relatorios.py            # Formatacao, dashboard visual e exportacao CSV
├── tests/
│   └── test_queries.py          # 14 testes unitarios automatizados com pytest
├── .gitignore
├── requirements.txt
└── README.md
```

## Banco de Dados e Engenharia SQL

O arquivo `.db` nao fica salvo no repositorio. Sempre que o `main.py` e executado, o sistema le os arquivos `sql/schema.sql` e `sql/seed.sql` e recria o banco automaticamente.

### Tabelas Relacionadas

- `clientes`: dados cadastrais dos clientes (`id`, `nome`, `email`, `cidade`, `criado_em`)
- `produtos`: catalogo de itens digitais (`id`, `nome`, `categoria`, `preco`, `estoque`)
- `pedidos`: registro dos pedidos com chave estrangeira para `clientes`
- `itens_pedido`: itens de cada pedido com chaves estrangeiras para `pedidos` e `produtos`

### Cobertura Completa de SQL

- Modelagem relacional com `PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, `UNIQUE` e `CHECK`
- Insercao dinamica de novos produtos pelo terminal (`INSERT INTO` parametrizado)
- Juncoes com `INNER JOIN` e `LEFT JOIN`
- Filtros com `WHERE` parametrizado e `LOWER()`
- Agregacoes com `GROUP BY`, `COUNT`, `SUM`, `AVG` e `ROUND`
- Filtro pos-agrupamento com `HAVING`
- Subconsulta (`Subquery`) para comparar precos com a media geral
- `CTE (WITH)` combinada com `CASE WHEN` e `COALESCE` para classificar faixas de receita
- `Window Functions` (`RANK() OVER` e `SUM() OVER`) para calculo de participacao percentual (Share %) e Curva ABC / Pareto acumulada
- `VIEW` (`resumo_pedidos`) para consolidar o total de itens e valor de cada pedido

## Indicadores de Negocio (KPIs) e Automacao

O sistema calcula automaticamente os principais indicadores da operacao:
- **Receita Confirmada (Paga)** e **Receita Pendente**
- **Ticket Medio por Pedido**
- **LTV Medio por Cliente (Lifetime Value)**
- **Taxa de Conversao de Pedidos Pagos (%)** e **Taxa de Cancelamento (%)**
- **Curva de Pareto (80/20)** por produto com percentual acumulado
- **Automacao ETL para CSV**: exporta automaticamente as tabelas analiticas (`faturamento_categorias.csv`, `pareto_produtos_window.csv`, `ltv_clientes.csv` e `pedidos_consolidados.csv`) para a pasta `exports/`.

## Como Executar

### 1. Clonar o repositorio e ativar o ambiente virtual

```bash
git clone https://github.com/Nayanearaujo/desafio-engenharia-dados-jr.git
cd desafio-engenharia-dados-jr

python3 -m venv .venv
source .venv/bin/activate
```

No Windows, ative com:
```bash
.venv\Scripts\activate
```

### 2. Instalar dependencias (usado para testes e geracao do dashboard PNG)

```bash
pip install -r requirements.txt
```

### 3. Iniciar a aplicacao

```bash
python src/main.py
```

## Opcoes do Menu

```text
=======================================================
  LOJA DIGITAL - PAINEL DE RELATORIOS
=======================================================
  [ 1] Listar todos os produtos
  [ 2] Filtrar produtos por categoria
  [ 3] Listar clientes cadastrados
  [ 4] Pedidos detalhados (View SQL)
  [ 5] Ranking de produtos mais vendidos
  [ 6] Faturamento por categoria
  [ 7] Clientes por volume de compras
  [ 8] Clientes acima de meta (HAVING)
  [ 9] Produtos acima da media (Subquery)
  [10] Desempenho dos produtos (CTE + CASE WHEN)
  [11] KPIs executivos e Curva de Pareto (Window Function)
  [12] Cadastrar novo produto
  [13] Gerar Dashboard Executivo (Matplotlib)
  [14] Automatizar exportacao analitica (CSV)
  [ 0] Sair
-------------------------------------------------------
```

## Testes Automatizados

A suite conta com 14 testes unitarios que utilizam um banco SQLite em memoria (`:memory:`) para validar todas as consultas, KPIs e Window Functions sem alterar o banco local:

```bash
pytest -v
```

## Autora

Nayane Araujo
