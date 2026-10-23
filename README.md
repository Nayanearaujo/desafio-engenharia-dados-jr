# Loja Digital - Painel de Relatorios

Projeto final desenvolvido para a Trilha de Engenharia de Dados Junior.

Aplicacao de terminal que utiliza Python e SQLite para gerenciar e gerar relatorios de vendas de uma loja de produtos digitais (cursos, e-books e templates).

## Estrutura do Projeto

```text
desafio-engenharia-dados-jr/
├── sql/
│   ├── schema.sql        # Criacao das tabelas, relacionamentos e view
│   └── seed.sql          # Dados de exemplo para testes
├── src/
│   ├── main.py           # Menu principal no terminal
│   ├── database.py       # Conexao com o SQLite e criacao do banco
│   ├── queries.py        # Consultas SQL organizadas em funcoes
│   └── relatorios.py     # Formatacao e exibicao das tabelas no terminal
├── tests/
│   └── test_queries.py   # Testes unitarios com pytest
├── .gitignore
├── requirements.txt
└── README.md
```

## Banco de Dados

O arquivo `.db` nao fica salvo no repositorio. Sempre que o `main.py` e executado, o sistema le os arquivos `sql/schema.sql` e `sql/seed.sql` e recria o banco automaticamente.

### Tabelas e Relacionamentos

- `clientes`: dados cadastrais dos clientes (`id`, `nome`, `email`, `cidade`, `criado_em`)
- `produtos`: catalogo de itens digitais (`id`, `nome`, `categoria`, `preco`, `estoque`)
- `pedidos`: registro dos pedidos com chave estrangeira para `clientes`
- `itens_pedido`: itens de cada pedido com chaves estrangeiras para `pedidos` e `produtos`

### Recursos SQL Utilizados

- Criacao de tabelas com `PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, `UNIQUE` e `CHECK`
- Consultas com `INNER JOIN` e `LEFT JOIN`
- Filtros com `WHERE` parametrizado e `LOWER()`
- Agrupamentos com `GROUP BY` e funcoes `COUNT`, `SUM`, `AVG` e `ROUND`
- Filtro pos-agrupamento com `HAVING`
- Subconsulta (`Subquery`) para comparar precos com a media geral
- `CTE (WITH)` combinada com `CASE WHEN` e `COALESCE` para classificar desempenho de vendas
- `VIEW` (`resumo_pedidos`) para consolidar o total de itens e valor de cada pedido

## Como Executar

### 1. Clonar o repositorio e ativar o ambiente virtual

```bash
git clone <URL_DO_REPOSITORIO>
cd desafio-engenharia-dados-jr

python3 -m venv .venv
source .venv/bin/activate
```

No Windows, ative com:
```bash
.venv\Scripts\activate
```

### 2. Instalar dependencias (opcional, usado para rodar os testes)

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
  [ 0] Sair
-------------------------------------------------------
```

## Testes Automatizados

Os testes utilizam um banco SQLite em memoria (`:memory:`) para validar todas as consultas do modulo `queries.py` sem alterar o banco local:

```bash
pytest -v
```

## Autora

Nayane Araujo
