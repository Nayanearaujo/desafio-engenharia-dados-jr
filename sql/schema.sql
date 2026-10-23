-- Camada Silver: tabelas tipadas, deduplicadas, validadas e quarentena de rejeitados

DROP VIEW IF EXISTS resumo_pedidos;
DROP TABLE IF EXISTS silver_rejeitados;
DROP TABLE IF EXISTS itens_pedido;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS clientes;

CREATE TABLE clientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    cidade      TEXT    NOT NULL,
    criado_em   TEXT    NOT NULL DEFAULT (date('now'))
);

CREATE TABLE produtos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    categoria   TEXT    NOT NULL,
    preco       REAL    NOT NULL CHECK (preco >= 0),
    estoque     INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0)
);

CREATE TABLE pedidos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,
    data_pedido     TEXT    NOT NULL DEFAULT (date('now')),
    status          TEXT    NOT NULL DEFAULT 'pendente',
    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
);

CREATE TABLE itens_pedido (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id   INTEGER NOT NULL,
    produto_id  INTEGER NOT NULL,
    quantidade  INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unit  REAL    NOT NULL CHECK (preco_unit >= 0),
    FOREIGN KEY (pedido_id)  REFERENCES pedidos  (id),
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
);

CREATE TABLE silver_rejeitados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tabela_origem   TEXT    NOT NULL,
    motivo          TEXT    NOT NULL,
    registro_raw    TEXT    NOT NULL,
    rejeitado_em    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE VIEW IF NOT EXISTS resumo_pedidos AS
    SELECT
        p.id                                         AS pedido_id,
        c.nome                                       AS cliente,
        c.email                                      AS email_cliente,
        p.data_pedido,
        p.status,
        COUNT(ip.id)                                 AS total_itens,
        ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS valor_total
    FROM pedidos p
    JOIN clientes c      ON c.id = p.cliente_id
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    GROUP BY p.id, c.nome, c.email, p.data_pedido, p.status;
