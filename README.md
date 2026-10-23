# 🛒 Loja Digital — Painel de Relatórios

Projeto final da **Trilha de Engenharia de Dados JR** da [DIO](https://dio.me).

Aplicação de linha de comando que integra **SQLite** e **Python** para gerenciar e analisar dados de uma loja de produtos digitais e criativos (cursos, e-books e templates).

---

## 📁 Estrutura do Projeto

```
desafio-engenharia-dados-jr/
├── sql/
│   ├── schema.sql        # Criação das 4 tabelas (PK/FK) + VIEW resumo_pedidos
│   └── seed.sql          # Carga inicial de dados (clientes, produtos, pedidos, itens)
├── src/
│   ├── main.py           # Ponto de entrada — menu interativo no terminal
│   ├── database.py       # Conexão SQLite e criação/reset automático do banco
│   ├── queries.py        # Consultas SQL organizadas em funções
│   └── relatorios.py     # Formatação tabular e exibição no terminal
├── tests/
│   └── test_queries.py   # Testes automatizados com pytest (banco em memória)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗃️ Modelo de Dados e Cobertura da Trilha SQL

O arquivo `.db` não é versionado no Git — ele é recriado automaticamente sempre que a aplicação é iniciada a partir de `sql/schema.sql` e `sql/seed.sql`.

### Tabelas Relacionadas

```
clientes (1) ──< pedidos (1) ──< itens_pedido >── (1) produtos
```

| Tabela         | Descrição                                                   |
|----------------|-------------------------------------------------------------|
| `clientes`     | Cadastro de clientes (`id`, `nome`, `email`, `cidade`, `criado_em`) |
| `produtos`     | Catálogo digital (`id`, `nome`, `categoria`, `preco`, `estoque`) |
| `pedidos`      | Cabeçalho do pedido com FK para `clientes` e `status`       |
| `itens_pedido` | Itens vendidos com FKs para `pedidos` e `produtos`          |

### Conceitos SQL Implementados

- ✅ **DDL & DML**: `CREATE TABLE`, `DROP TABLE`, `INSERT INTO`, constraints `CHECK`, `NOT NULL`, `UNIQUE`, `PRIMARY KEY` e `FOREIGN KEY`
- ✅ **Filtros e Strings**: `WHERE`, `LOWER()` e parâmetros `?` contra SQL Injection
- ✅ **Junções (`JOIN`)**: `INNER JOIN` entre 3 tabelas e `LEFT JOIN` para produtos sem vendas
- ✅ **Agregações e Agrupamento**: `GROUP BY`, `COUNT`, `SUM`, `AVG`, `ROUND`
- ✅ **Filtro Pós-Agregação (`HAVING`)**: clientes que superaram uma meta financeira
- ✅ **Subconsulta (`Subquery`)**: produtos com preço acima da média geral do catálogo
- ✅ **CTE (`WITH`) + `CASE WHEN` + `COALESCE`**: classificação de desempenho de vendas por faixa de receita
- ✅ **`VIEW` (`resumo_pedidos`)**: visão consolidada de pedidos com total de itens e valor total

---

## ▶️ Como Configurar e Rodar

### 1. Clonar o repositório e criar o ambiente virtual

```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd desafio-engenharia-dados-jr

# Criar e ativar o ambiente virtual (.venv)
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

### 2. Instalar dependências de desenvolvimento (opcional para testes/lint)

```bash
pip install -r requirements.txt
```

### 3. Executar a aplicação

```bash
python src/main.py
```

---

## 📋 Menu Interativo no Terminal

```text
═══════════════════════════════════════════════════════
  🛒  LOJA DIGITAL — PAINEL DE RELATÓRIOS
═══════════════════════════════════════════════════════
  [1] 📦 Listar todos os produtos
  [2] 🔍 Filtrar produtos por categoria
  [3] 👥 Listar clientes cadastrados
  [4] 🧾 Pedidos detalhados (via View SQL)
  [5] 🏆 Ranking: produtos mais vendidos
  [6] 💰 Faturamento por categoria
  [7] ⭐ Clientes por volume de compras
  [8] 🎯 Clientes acima de meta   [HAVING]
  [9] 📊 Produtos acima da média  [Subquery]
  [A] 🧠 Desempenho dos produtos  [CTE + CASE WHEN]
  [0] Sair
```

---

## 🧪 Testes Automatizados e Qualidade de Código (Bônus)

Os testes utilizam um banco SQLite em memória (`:memory:`), garantindo rapidez e isolamento sem alterar o arquivo `loja_digital.db`:

```bash
# Executar os 10 testes unitários
pytest -v

# Verificar padronização PEP8 com Ruff
ruff check src/ tests/
```

---

## 🛡️ Boas Práticas de Engenharia de Dados

- **Modularização**: separação clara entre persistência (`database.py`), consultas (`queries.py`), visualização (`relatorios.py`) e orquestração (`main.py`).
- **Tratamento de Erros (`try/except`)**: proteção na abertura de conexão, leitura de scripts `.sql`, entradas do usuário e interrupção via teclado (`Ctrl+C`).
- **Segurança**: todas as entradas de usuário utilizam queries parametrizadas (`?`).
- **Git Workflow**: desenvolvimento em branch dedicada (`feature/loja-digital`) com histórico de commits semânticos e progressivos.

---

## 👩‍💻 Autora

Desenvolvido por **Nayane Araújo** como projeto final da Trilha de Engenharia de Dados JR.
