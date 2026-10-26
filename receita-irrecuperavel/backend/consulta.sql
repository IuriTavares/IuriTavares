-- ORACLE: inadimplência histórica por fechamento e safra de vencimento.
-- Altere somente as duas datas no CTE entrada (meses inicial e final inclusivos).
-- Padrão: janeiro/2025, para uma primeira conferência com volume reduzido.
-- Para todos os meses encerrados desde janeiro/2025, use SYSDATE como mes_final.
-- Não altera dados. A janela 49_60M implementa a regra informada pelo usuário.
-- Datas de pagamento são ftcd_dt_sit_fatura para situações PAGA/PAGR.
-- Alterações manuais posteriores não podem ser reconstruídas sem histórico.
-- Recortes cadastrais refletem os dados disponíveis hoje.
-- Percentuais não devem ser somados nem calculados por média simples.
-- Recalcule totais como 100 * SUM(saldo_pendente) / SUM(faturamento).
-- Faça isso separadamente por fechamento e visão.
-- Ausência de faturas não gera linha; não significa inadimplência zero.
-- Havendo inconsistências, o percentual fica NULL e os valores exigem conferência.
-- Execução e desempenho ainda precisam ser validados no Oracle de destino.
WITH
entrada AS (
    SELECT :mes_inicial AS mes_inicial,
           :mes_final AS mes_final
    FROM dual
),
parametros AS (
    SELECT TRUNC(e.mes_inicial, 'MM') AS mes_inicial,
           LEAST(ADD_MONTHS(TRUNC(e.mes_final, 'MM'), 1),
                 TRUNC(SYSDATE, 'MM')) AS mes_final
    FROM entrada e
),
fechamentos AS (
    SELECT ADD_MONTHS(p.mes_inicial, LEVEL - 1) AS mes_fechamento,
           ADD_MONTHS(p.mes_inicial, LEVEL) AS corte_exclusivo
    FROM parametros p
    WHERE p.mes_inicial < p.mes_final
    CONNECT BY LEVEL <= MONTHS_BETWEEN(p.mes_final, p.mes_inicial)
),
visoes AS (
    SELECT '1M' AS visao, 1 AS idade_min, 1 AS idade_max FROM dual UNION ALL
    SELECT '3M', 3, 3 FROM dual UNION ALL
    SELECT '6M', 6, 6 FROM dual UNION ALL
    SELECT '12M', 12, 12 FROM dual UNION ALL
    SELECT '60M', 60, 60 FROM dual UNION ALL
    SELECT '49_60M', 49, 60 FROM dual
),
janelas AS (
    SELECT f.mes_fechamento, f.corte_exclusivo, v.visao,
           ADD_MONTHS(f.mes_fechamento, -v.idade_max) AS inicio_vencimento,
           ADD_MONTHS(f.mes_fechamento, 1-v.idade_min) AS fim_vencimento_exclusivo
    FROM fechamentos f CROSS JOIN visoes v
),
base AS (
    SELECT
    unid.seto_setor               AS setor,
    ftcd.ftcd_corrida_fatmto      AS Corrida,
    muni.muni_nome_municipio      AS nome_municipio,
    bair.bair_nome_bairro         AS bairro_nome,
    unid.rota_rota                AS Rota,

    unid.unid_compl_endereco_uc   AS Compl,

    REGEXP_SUBSTR(unid.unid_compl_endereco_uc, '^[^ ]+') || ' - ' || REGEXP_SUBSTR(unid.unid_compl_endereco_uc, '[^-]+$') AS bloco_residencial,
    REGEXP_SUBSTR(unid.unid_compl_endereco_uc, '^[^ ]+') AS bloco,
    REGEXP_SUBSTR(unid.unid_compl_endereco_uc, '[^-]+$') AS residencial,
    CASE
        WHEN ftcd.ftcd_local = 1 THEN 'Capital'
        ELSE 'Interior'
    END AS cap_int,

    ftcd.ftcd_mes_ano_fatmto AS mes_ano,

    CASE
        WHEN ftcd.ftcd_optante = 1
         AND ftcd.ftcd_tipo_ligacao <> 4
        THEN 'Optante'

        WHEN NVL(ftcd.ftcd_optante, 0) = 0
         AND ftcd.ftcd_tipo_ligacao <> 4
        THEN 'BT'

        ELSE 'MT'
    END AS tensao,

    CASE
        WHEN ftcd.ftcd_classe IN (1,2,3,4,8,10,11)
        THEN 'Privada'
        ELSE 'Pública'
    END AS tipo_classe,

    CASE
        WHEN ftcd.ftcd_classe = 1 AND ftcd.ftcd_subclasse >= 4 THEN '1-Bx. Renda'
        WHEN ftcd.ftcd_classe = 1 AND ftcd.ftcd_subclasse < 4 THEN '1 -Residencial'
        WHEN ftcd.ftcd_classe = 2 THEN '2-Industrial'
        WHEN ftcd.ftcd_classe = 3 THEN '3-Comercial'
        WHEN ftcd.ftcd_classe = 4 THEN '4-Rural'
        WHEN ftcd.ftcd_classe = 5 AND ftcd.ftcd_subclasse = 1 THEN '5.1-Municipal'
        WHEN ftcd.ftcd_classe = 5 AND ftcd.ftcd_subclasse = 2 THEN '5.2-Estadual'
        WHEN ftcd.ftcd_classe = 5 AND ftcd.ftcd_subclasse = 3 THEN '5.3-Federal'
        WHEN ftcd.ftcd_classe = 6 THEN '6-IP'
        WHEN ftcd.ftcd_classe = 7 THEN '7-SP'
        WHEN ftcd.ftcd_classe = 8 THEN '8-CP'
        WHEN ftcd.ftcd_classe = 10 THEN '10-Suprimento'
        WHEN ftcd.ftcd_classe = 11 THEN '11-Livre'
        ELSE 'xxx'
    END AS classe,

    CASE
        WHEN ftcd.ftcd_tipo_motivo_fd IN (70, 71, 72, 73)
        THEN 'TOI'
        ELSE 'Regular'
    END AS toi,
    ftcd.ftcd_tipo_entrega AS tipo_entrega,
    ftcd.ftcd_dt_vencto AS dt_vencimento,
    ftcd.ftcd_dt_sit_fatura AS dt_pagamento,
    ftcd.ftcd_sit_fatura AS situacao_atual,
    ftcd.ftcd_total_fatura AS valor_fatura
FROM ajuri.fatura_cadastro     ftcd,
     ajuri.unidade_consumidora unid,
     ajuri.local               locl,
     ajuri.municipio           muni,
     ajuri.logradouro          logr,
     ajuri.bairro              bair,
     parametros p

WHERE ftcd.ftcd_sit_fatura IN ('ABER', 'REAV', 'TRAN', 'PAGA', 'PAGR')
  AND ftcd.ftcd_dt_vencto >= ADD_MONTHS(p.mes_inicial, -60)
  AND ftcd.ftcd_dt_vencto < p.mes_final


  AND ftcd.ftcd_ident_uc                                = unid.unid_ident_uc

  AND unid.locl_local                                   = locl.locl_local
  AND locl.muni_cod_municipio                           = muni.muni_cod_municipio

  AND unid.locl_local                                   = logr.locl_local
  AND unid.locl_local                                   = bair.locl_local
  AND logr.bair_cod_bairro                              = bair.bair_cod_bairro
  AND unid.logr_cod_logradouro                          = logr.logr_cod_logradouro


),
classificada AS (
    SELECT j.mes_fechamento, j.corte_exclusivo, j.visao,
           j.inicio_vencimento, j.fim_vencimento_exclusivo,
           b.*,
           CASE WHEN b.situacao_atual IN ('PAGA', 'PAGR')
                      AND b.dt_pagamento < j.corte_exclusivo
                THEN 1 ELSE 0 END AS paga_no_corte,
           CASE WHEN b.valor_fatura IS NULL
                       OR (b.situacao_atual IN ('PAGA', 'PAGR') AND b.dt_pagamento IS NULL)
                THEN 1 ELSE 0 END AS dado_inconsistente
    FROM janelas j
    JOIN base b ON b.dt_vencimento >= j.inicio_vencimento
               AND b.dt_vencimento < j.fim_vencimento_exclusivo
),
resumo AS (
    SELECT mes_fechamento, corte_exclusivo, visao,
           inicio_vencimento, fim_vencimento_exclusivo,
           setor, Corrida, nome_municipio, bairro_nome, Rota, Compl, bloco_residencial, bloco, residencial, cap_int, mes_ano, tensao, tipo_classe, classe, toi, tipo_entrega,
           COUNT(*) AS qtd_faturas,
           SUM(paga_no_corte) AS qtd_pagas_no_corte,
           SUM(1-paga_no_corte) AS qtd_pendentes_no_corte,
           SUM(dado_inconsistente) AS qtd_inconsistentes,
           SUM(valor_fatura) AS faturamento,
           SUM(CASE WHEN paga_no_corte=1 THEN valor_fatura ELSE 0 END) AS pago_ate_fechamento,
           SUM(CASE WHEN paga_no_corte=0 THEN valor_fatura ELSE 0 END) AS saldo_pendente
    FROM classificada
    GROUP BY mes_fechamento, corte_exclusivo, visao,
             inicio_vencimento, fim_vencimento_exclusivo,
             setor, Corrida, nome_municipio, bairro_nome, Rota, Compl, bloco_residencial, bloco, residencial, cap_int, mes_ano, tensao, tipo_classe, classe, toi, tipo_entrega
)
SELECT r.*,
       LAST_DAY(mes_fechamento) AS data_fechamento,
       fim_vencimento_exclusivo - 1 AS ultimo_dia_vencimento,
       CASE WHEN qtd_inconsistentes=0 THEN
           ROUND(100 * saldo_pendente / NULLIF(faturamento, 0), 6)
       END AS inadimplencia_pct
FROM resumo r
ORDER BY mes_fechamento, visao, setor, nome_municipio, bairro_nome;
