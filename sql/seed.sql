-- Carga inicial de dados da Loja Digital

INSERT INTO clientes (nome, email, cidade) VALUES
    ('Ana Lima',       'ana.lima@email.com',       'São Paulo'),
    ('Bruno Costa',    'bruno.costa@email.com',    'Rio de Janeiro'),
    ('Carla Mendes',   'carla.mendes@email.com',   'Belo Horizonte'),
    ('Diego Rocha',    'diego.rocha@email.com',    'Curitiba'),
    ('Elena Ferreira', 'elena.ferreira@email.com', 'Recife'),
    ('Felipe Araújo',  'felipe.araujo@email.com',  'Salvador'),
    ('Gabi Nunes',     'gabi.nunes@email.com',     'Fortaleza');

INSERT INTO produtos (nome, categoria, preco, estoque) VALUES
    ('Python do Zero ao Avançado',    'Curso',    197.00, 100),
    ('SQL para Engenheiros de Dados', 'Curso',    147.00, 100),
    ('Git & GitHub na Prática',       'Curso',     97.00, 100),
    ('Guia de Boas Práticas Python',  'E-book',    37.00, 999),
    ('Template de Dashboard SQL',     'Template',  27.00, 999),
    ('Fundamentos de IA com Python',  'Curso',    247.00, 100),
    ('Pack de Prompts para Devs',     'E-book',    47.00, 999);

INSERT INTO pedidos (cliente_id, data_pedido, status) VALUES
    (1, '2026-10-01', 'pago'),
    (2, '2026-10-03', 'pago'),
    (3, '2026-10-05', 'pendente'),
    (4, '2026-10-07', 'pago'),
    (5, '2026-10-10', 'cancelado'),
    (6, '2026-10-12', 'pago'),
    (7, '2026-10-15', 'pendente'),
    (1, '2026-10-18', 'pago');

INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unit) VALUES
    (1, 1, 1, 197.00),
    (1, 4, 1,  37.00),
    (2, 2, 1, 147.00),
    (2, 3, 1,  97.00),
    (3, 6, 1, 247.00),
    (4, 5, 2,  27.00),
    (4, 7, 1,  47.00),
    (5, 1, 1, 197.00),
    (6, 2, 1, 147.00),
    (6, 4, 2,  37.00),
    (7, 3, 1,  97.00),
    (7, 5, 3,  27.00),
    (8, 6, 1, 247.00),
    (8, 7, 2,  47.00);
