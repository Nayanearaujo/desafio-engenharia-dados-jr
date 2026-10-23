# 🛒 Loja Digital — Painel de Relatórios

Projeto final da **Trilha de Engenharia de Dados JR** da [DIO](https://dio.me).

Aplicação de terminal que combina um banco de dados **SQLite** com **Python**, gerando relatórios interativos sobre uma loja de produtos digitais (cursos, e-books e templates).

---

## 📁 Estrutura do Projeto

```
desafio-engenharia-dados-jr/
├── sql/
│   ├── schema.sql        # Criação das tabelas + VIEW
│   └── seed.sql          # Dados de exemplo (insert)
├── src/
│   ├── main.py           # Ponto de entrada — menu interativo
│   ├── database.py       # Conexão e criação do banco SQLite
│   ├── queries.py        # Todas as consultas SQL (JOIN, WHERE, GROUP BY…)
│   └── relatorios.py     # Formatação e exibição no terminal
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗃️ Banco de Dados

O banco **não fica no repositório** — ele é gerado automaticamente ao rodar o projeto.

### Tabelas

| Tabela         | Descrição                                        |
|----------------|--------------------------------------------------|
| `clientes`     | Dados dos clientes (nome, e-mail, cidade)        |
| `produtos`     | Catálogo de produtos (nome, categoria, preço)    |
| `pedidos`      | Pedidos realizados, com status                   |
| `itens_pedido` | Itens de cada pedido (produto, quantidade, preço)|

### Relacionamentos
- `pedidos.cliente_id` → `clientes.id` (FK)
- `itens_pedido.pedido_id` → `pedidos.id` (FK)
- `itens_pedido.produto_id` → `produtos.id` (FK)

### Conceitos SQL utilizados
- ✅ `JOIN` (INNER JOIN entre 3+ tabelas)
- ✅ `WHERE` com parâmetro (evita SQL injection)
- ✅ `GROUP BY` + `COUNT`, `SUM`, `AVG`
- ✅ `VIEW` (`resumo_pedidos`) com JOIN e agregação

---

## ▶️ Como Rodar

**Pré-requisito:** Python 3.8 ou superior. Nenhuma dependência externa.

```bash
# Clone o repositório
git clone <URL-do-seu-repositorio>
cd desafio-engenharia-dados-jr

# Rode o projeto
python src/main.py
```

O banco será criado automaticamente na primeira execução.

---

## 📋 Menu Disponível

```
[1] 📦 Listar todos os produtos
[2] 🔍 Filtrar produtos por categoria
[3] 👥 Listar clientes cadastrados
[4] 🧾 Pedidos detalhados (via View SQL)
[5] 🏆 Ranking: produtos mais vendidos
[6] 💰 Faturamento por categoria
[7] ⭐ Clientes por volume de compras
[0] Sair
```

---

## 🛡️ Boas Práticas Implementadas

- **Tratamento de erros** com `try/except` em conexão, leitura de scripts SQL e execução de queries
- **Separação de responsabilidades**: cada módulo tem uma função clara
- **Parâmetros SQL** para evitar SQL injection
- **`.gitignore`** excluindo o arquivo `.db`, cache Python e ambiente virtual

---

## 🧰 Tecnologias

- Python 3.x (biblioteca padrão: `sqlite3`, `os`, `sys`)
- SQLite 3

---

## 👩‍💻 Autora

Desenvolvido por **Nayane Araújo** como projeto final da Trilha de Engenharia de Dados JR — [DIO](https://dio.me).
