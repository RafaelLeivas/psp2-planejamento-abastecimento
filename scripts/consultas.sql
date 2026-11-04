-- Escolha seu catálogo antes de executar; o notebook usa current_catalog().
USE SCHEMA psp2_abastecimento;

-- Q1: evolução temporal; não ponderada por volume vendido.
SELECT uf, municipio, semana, n_postos, mediana, p25, p75
FROM indicadores_semanais WHERE analise ORDER BY municipio, semana;

-- Q2: dispersão, somente localidades com cobertura suficiente.
SELECT uf, municipio, semanas, iqr_medio, gap_pct_medio
FROM resumo_localidades WHERE cobertura_suficiente ORDER BY iqr_medio DESC;

-- Q3: candidatos para cotação. Não equivale a recomendação de contratação.
SELECT uf, municipio, cnpj, semanas_observadas, cobertura,
       fracao_abaixo, desconto_medio_pct
FROM ranking_postos WHERE elegivel
ORDER BY fracao_abaixo DESC, desconto_medio_pct DESC;

-- Q4: economia potencial simulada, não realizada.
SELECT uf, municipio, litros_semanais, COUNT(*) AS semanas,
       AVG(custo_referencia) AS custo_referencia_semanal,
       AVG(custo_cenario) AS custo_cenario_semanal,
       AVG(economia_potencial) AS diferenca_simulada_semanal
FROM cenarios GROUP BY uf, municipio, litros_semanais
ORDER BY municipio, litros_semanais;

-- Avaliação da hipótese: manter as localidades inconclusivas identificadas.
SELECT uf, municipio, semanas, fracao_semanas_gap3,
       CASE WHEN NOT cobertura_suficiente THEN 'Inconclusiva por cobertura'
            WHEN hipotese_atendida THEN 'Critério atendido'
            ELSE 'Critério não atendido' END AS avaliacao
FROM resumo_localidades ORDER BY uf, municipio;

-- Qualidade e comprovação de persistência.
SELECT * FROM qualidade_atributos ORDER BY atributo;
SELECT COUNT(*) AS observacoes FROM fato_preco;
DESCRIBE DETAIL fato_preco;
