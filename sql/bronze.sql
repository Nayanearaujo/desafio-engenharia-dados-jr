-- Camada Bronze: ingestao bruta dos arquivos CSV sem transformacao de tipos

DROP TABLE IF EXISTS bronze_itens_pedido;
DROP TABLE IF EXISTS bronze_pedidos;
DROP TABLE IF EXISTS bronze_produtos;
DROP TABLE IF EXISTS bronze_clientes;

CREATE TABLE bronze_clientes (
    id              TEXT,
    nome            TEXT,
    email           TEXT,
    cidade          TEXT,
    criado_em       TEXT,
    _ingested_at    TEXT NOT NULL,
    _source_file    TEXT NOT NULL
);

CREATE TABLE bronze_produtos (
    id              TEXT,
    nome            TEXT,
    categoria       TEXT,
    preco           TEXT,
    estoque         TEXT,
    _ingested_at    TEXT NOT NULL,
    _source_file    TEXT NOT NULL
);

CREATE TABLE bronze_pedidos (
    id              TEXT,
    cliente_id      TEXT,
    data_pedido     TEXT,
    status          TEXT,
    _ingested_at    TEXT NOT NULL,
    _source_file    TEXT NOT NULL
);

CREATE TABLE bronze_itens_pedido (
    id              TEXT,
    pedido_id       TEXT,
    produto_id      TEXT,
    quantidade      TEXT,
    preco_unit      TEXT,
    _ingested_at    TEXT NOT NULL,
    _source_file    TEXT NOT NULL
);
