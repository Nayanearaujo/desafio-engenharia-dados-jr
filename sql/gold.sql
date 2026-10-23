-- Camada Gold: visoes analiticas e indicadores de negocio prontos para consumo

DROP VIEW IF EXISTS gold_resumo_pedidos;
DROP VIEW IF EXISTS gold_kpis_executivos;
DROP VIEW IF EXISTS gold_faturamento_categoria;
DROP VIEW IF EXISTS gold_pareto_produtos;
DROP VIEW IF EXISTS gold_receita_mensal;
DROP VIEW IF EXISTS gold_rfm_clientes;
DROP VIEW IF EXISTS gold_coorte_retencao;
DROP VIEW IF EXISTS gold_taxa_recompra;
DROP VIEW IF EXISTS gold_cancelamento_categoria_mes;
DROP VIEW IF EXISTS gold_receita_diaria;
DROP VIEW IF EXISTS gold_qualidade_resumo;

-- 1. Resumo de pedidos (espelho Gold da view original resumo_pedidos)
CREATE VIEW gold_resumo_pedidos AS
    SELECT
        pedido_id,
        cliente,
        email_cliente,
        data_pedido,
        status,
        total_itens,
        valor_total
    FROM resumo_pedidos;

-- 2. KPIs executivos globais
CREATE VIEW gold_kpis_executivos AS
    WITH totais_pedidos AS (
        SELECT
            p.id AS pedido_id,
            p.cliente_id,
            p.status,
            SUM(ip.quantidade * ip.preco_unit) AS valor_pedido
        FROM pedidos p
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        GROUP BY p.id, p.cliente_id, p.status
    )
    SELECT
        COUNT(pedido_id) AS total_pedidos,
        SUM(CASE WHEN status = 'pago' THEN 1 ELSE 0 END) AS pedidos_pagos,
        ROUND(COALESCE(SUM(CASE WHEN status = 'pago' THEN valor_pedido ELSE 0 END), 0), 2) AS receita_paga,
        ROUND(COALESCE(SUM(CASE WHEN status = 'pendente' THEN valor_pedido ELSE 0 END), 0), 2) AS receita_pendente,
        ROUND(COALESCE(AVG(CASE WHEN status = 'pago' THEN valor_pedido END), 0), 2) AS ticket_medio_pedido,
        ROUND(
            COALESCE(
                SUM(CASE WHEN status = 'pago' THEN valor_pedido ELSE 0 END)
                / NULLIF(COUNT(DISTINCT CASE WHEN status = 'pago' THEN cliente_id END), 0),
                0
            ),
            2
        ) AS ltv_medio_cliente,
        ROUND(
            COALESCE(100.0 * SUM(CASE WHEN status = 'pago' THEN 1 ELSE 0 END) / NULLIF(COUNT(pedido_id), 0), 0),
            1
        ) AS taxa_conversao_pct,
        ROUND(
            COALESCE(100.0 * SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) / NULLIF(COUNT(pedido_id), 0), 0),
            1
        ) AS taxa_cancelamento_pct
    FROM totais_pedidos;

-- 3. Faturamento por categoria (receita confirmada paga)
CREATE VIEW gold_faturamento_categoria AS
    SELECT
        pr.categoria,
        COUNT(DISTINCT pr.id) AS produtos_distintos,
        SUM(ip.quantidade) AS unidades_vendidas,
        ROUND(AVG(ip.preco_unit), 2) AS ticket_medio,
        ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_total
    FROM produtos pr
    JOIN itens_pedido ip ON ip.produto_id = pr.id
    JOIN pedidos p ON p.id = ip.pedido_id
    WHERE p.status = 'pago'
    GROUP BY pr.categoria
    ORDER BY receita_total DESC;

-- 4. Curva de Pareto 80/20 por produto (sobre receita paga)
CREATE VIEW gold_pareto_produtos AS
    WITH receita_produtos AS (
        SELECT
            pr.id AS produto_id,
            pr.nome AS produto,
            pr.categoria,
            COALESCE(SUM(CASE WHEN p.status = 'pago' THEN ip.quantidade ELSE 0 END), 0) AS unidades,
            ROUND(COALESCE(SUM(CASE WHEN p.status = 'pago' THEN ip.quantidade * ip.preco_unit ELSE 0 END), 0), 2) AS receita
        FROM produtos pr
        LEFT JOIN itens_pedido ip ON ip.produto_id = pr.id
        LEFT JOIN pedidos p ON p.id = ip.pedido_id
        GROUP BY pr.id, pr.nome, pr.categoria
    ),
    pareto_calc AS (
        SELECT
            RANK() OVER (ORDER BY receita DESC) AS posicao_ranking,
            produto_id,
            produto,
            categoria,
            unidades,
            receita,
            ROUND(100.0 * receita / NULLIF(SUM(receita) OVER (), 0), 1) AS share_receita_pct,
            ROUND(
                100.0 * SUM(receita) OVER (ORDER BY receita DESC, produto_id ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                / NULLIF(SUM(receita) OVER (), 0),
                1
            ) AS pareto_acumulado_pct
        FROM receita_produtos
    )
    SELECT
        posicao_ranking,
        produto_id,
        produto,
        categoria,
        unidades,
        receita,
        share_receita_pct,
        pareto_acumulado_pct,
        CASE
            WHEN pareto_acumulado_pct <= 80.0 OR posicao_ranking = 1 THEN 'Classe A (Top 80%)'
            WHEN pareto_acumulado_pct <= 95.0 THEN 'Classe B (15%)'
            ELSE 'Classe C (5%)'
        END AS classe_abc
    FROM pareto_calc
    ORDER BY posicao_ranking, produto_id;

-- 5. Receita mensal paga com crescimento MoM (LAG) e media movel de 3 meses
CREATE VIEW gold_receita_mensal AS
    WITH vendas_mensais AS (
        SELECT
            substr(p.data_pedido, 1, 7) AS mes,
            COUNT(DISTINCT p.id) AS total_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS receita_liquida
        FROM pedidos p
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        WHERE p.status = 'pago'
        GROUP BY substr(p.data_pedido, 1, 7)
    ),
    com_lag AS (
        SELECT
            mes,
            total_pedidos,
            receita_liquida,
            LAG(receita_liquida) OVER (ORDER BY mes) AS receita_mes_anterior,
            ROUND(
                AVG(receita_liquida) OVER (ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),
                2
            ) AS media_movel_3m
        FROM vendas_mensais
    )
    SELECT
        mes,
        total_pedidos,
        receita_liquida,
        receita_mes_anterior,
        ROUND(
            CASE
                WHEN receita_mes_anterior IS NULL OR receita_mes_anterior = 0 THEN NULL
                ELSE 100.0 * (receita_liquida - receita_mes_anterior) / receita_mes_anterior
            END,
            1
        ) AS variacao_mom_pct,
        media_movel_3m
    FROM com_lag
    ORDER BY mes;

-- 6. Segmentacao RFM (Recencia, Frequencia, Valor Monetario sobre pedidos pagos)
CREATE VIEW gold_rfm_clientes AS
    WITH ref_date AS (
        SELECT MAX(data_pedido) AS data_max FROM pedidos WHERE status = 'pago'
    ),
    base_rfm AS (
        SELECT
            c.id AS cliente_id,
            c.nome AS cliente,
            c.cidade,
            CAST(
                julianday((SELECT data_max FROM ref_date)) - julianday(MAX(p.data_pedido))
                AS INTEGER
            ) AS recencia_dias,
            COUNT(DISTINCT p.id) AS frequencia_pedidos,
            ROUND(SUM(ip.quantidade * ip.preco_unit), 2) AS valor_monetario
        FROM clientes c
        JOIN pedidos p ON p.cliente_id = c.id
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        WHERE p.status = 'pago'
        GROUP BY c.id, c.nome, c.cidade
    ),
    quartis AS (
        SELECT
            cliente_id,
            cliente,
            cidade,
            recencia_dias,
            frequencia_pedidos,
            valor_monetario,
            NTILE(4) OVER (ORDER BY recencia_dias DESC) AS r_score,
            NTILE(4) OVER (ORDER BY frequencia_pedidos ASC, valor_monetario ASC) AS f_score,
            NTILE(4) OVER (ORDER BY valor_monetario ASC) AS m_score
        FROM base_rfm
    )
    SELECT
        cliente_id,
        cliente,
        cidade,
        recencia_dias,
        frequencia_pedidos,
        valor_monetario,
        r_score,
        f_score,
        m_score,
        CASE
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Campeoes'
            WHEN r_score >= 2 AND f_score >= 3 THEN 'Leais'
            WHEN r_score <= 2 AND (f_score >= 3 OR m_score >= 3) THEN 'Em risco'
            ELSE 'Inativos'
        END AS segmento_rfm
    FROM quartis
    ORDER BY valor_monetario DESC;

-- 7. Retencao por coorte (mes do primeiro pedido pago)
CREATE VIEW gold_coorte_retencao AS
    WITH primeira_compra AS (
        SELECT
            cliente_id,
             MIN(substr(data_pedido, 1, 7)) AS coorte_mes
        FROM pedidos
        WHERE status = 'pago'
        GROUP BY cliente_id
    ),
    atividade_mensal AS (
        SELECT DISTINCT
            p.cliente_id,
            pc.coorte_mes,
            substr(p.data_pedido, 1, 7) AS mes_pedido,
            (CAST(substr(p.data_pedido, 1, 4) AS INTEGER) - CAST(substr(pc.coorte_mes, 1, 4) AS INTEGER)) * 12
            + (CAST(substr(p.data_pedido, 6, 2) AS INTEGER) - CAST(substr(pc.coorte_mes, 6, 2) AS INTEGER)) AS indice_mes
        FROM pedidos p
        JOIN primeira_compra pc ON pc.cliente_id = p.cliente_id
        WHERE p.status = 'pago'
    ),
    tamanho_coortes AS (
        SELECT
            coorte_mes,
            COUNT(DISTINCT cliente_id) AS clientes_iniciais
        FROM primeira_compra
        GROUP BY coorte_mes
    )
    SELECT
        a.coorte_mes,
        a.mes_pedido,
        a.indice_mes,
        COUNT(DISTINCT a.cliente_id) AS clientes_ativos,
        t.clientes_iniciais,
        ROUND(100.0 * COUNT(DISTINCT a.cliente_id) / t.clientes_iniciais, 1) AS taxa_retencao_pct
    FROM atividade_mensal a
    JOIN tamanho_coortes t ON t.coorte_mes = a.coorte_mes
    GROUP BY a.coorte_mes, a.mes_pedido, a.indice_mes, t.clientes_iniciais
    ORDER BY a.coorte_mes, a.indice_mes;

-- 8. Taxa global de recompra (sobre clientes pagantes)
CREATE VIEW gold_taxa_recompra AS
    WITH pedidos_por_cliente AS (
        SELECT
            cliente_id,
            COUNT(DISTINCT id) AS qtd_pedidos
        FROM pedidos
        WHERE status = 'pago'
        GROUP BY cliente_id
    )
    SELECT
        COUNT(cliente_id) AS clientes_compradores,
        SUM(CASE WHEN qtd_pedidos >= 2 THEN 1 ELSE 0 END) AS clientes_recorrentes,
        ROUND(
            100.0 * SUM(CASE WHEN qtd_pedidos >= 2 THEN 1 ELSE 0 END) / NULLIF(COUNT(cliente_id), 0),
            1
        ) AS taxa_recompra_pct,
        ROUND(AVG(qtd_pedidos), 2) AS media_pedidos_por_cliente
    FROM pedidos_por_cliente;

-- 9. Cancelamento por categoria e por mes
CREATE VIEW gold_cancelamento_categoria_mes AS
    SELECT
        substr(p.data_pedido, 1, 7) AS mes,
        pr.categoria,
        COUNT(DISTINCT p.id) AS total_pedidos,
        COUNT(DISTINCT CASE WHEN p.status = 'cancelado' THEN p.id END) AS pedidos_cancelados,
        ROUND(
            100.0 * COUNT(DISTINCT CASE WHEN p.status = 'cancelado' THEN p.id END)
            / NULLIF(COUNT(DISTINCT p.id), 0),
            1
        ) AS taxa_cancelamento_pct,
        ROUND(
            SUM(CASE WHEN p.status = 'cancelado' THEN ip.quantidade * ip.preco_unit ELSE 0 END),
            2
        ) AS receita_cancelada
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
    GROUP BY substr(p.data_pedido, 1, 7), pr.categoria
    ORDER BY mes DESC, taxa_cancelamento_pct DESC;

-- 10. Receita paga e cancelamento diario (base para Carta de Controle I-MR Lean Six Sigma)
CREATE VIEW gold_receita_diaria AS
    WITH pedidos_dia AS (
        SELECT
            p.data_pedido,
            p.id AS pedido_id,
            p.status,
            SUM(ip.quantidade * ip.preco_unit) AS valor_pedido
        FROM pedidos p
        JOIN itens_pedido ip ON ip.pedido_id = p.id
        GROUP BY p.data_pedido, p.id, p.status
    )
    SELECT
        data_pedido,
        COUNT(pedido_id) AS total_pedidos,
        SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS pedidos_cancelados,
        ROUND(
            100.0 * SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) / NULLIF(COUNT(pedido_id), 0),
            2
        ) AS taxa_cancelamento_pct,
        ROUND(
            SUM(CASE WHEN status = 'pago' THEN valor_pedido ELSE 0 END),
            2
        ) AS receita_liquida_dia
    FROM pedidos_dia
    GROUP BY data_pedido
    ORDER BY data_pedido;

-- 11. Resumo de qualidade dos dados rejeitados na camada Silver
CREATE VIEW gold_qualidade_resumo AS
    SELECT
        tabela_origem,
        motivo,
        COUNT(*) AS total_rejeitados
    FROM silver_rejeitados
    GROUP BY tabela_origem, motivo
    ORDER BY total_rejeitados DESC, tabela_origem;
