# Catálogo de dados

## Origem e campos Bronze

Fonte comum: ANP/LPC, ZIP do primeiro semestre de 2026, coletado em 04/11/2026. URL, hash e contagens em `resultados/auditoria.json`. Todos os campos passam por remoção de espaços externos; string vazia vira nulo. A tabela abaixo distingue domínio esperado de valores efetivamente observados.

| Campo | Tipo conceitual | Significado | Domínio esperado | Admite nulo |
|---|---|---|---|---|
| regiao | categórico | Região da revenda | CO | não |
| uf | categórico | Unidade federativa | DF ou GO | não |
| municipio | categórico | Município conforme grafia ANP | Lista observada abaixo; não vazio | não |
| revenda | texto | Nome empresarial do posto | Texto não vazio; mudanças não são tratadas como novo CNPJ | não |
| cnpj | texto | Identificador empresarial; preservar zeros iniciais | 14 dígitos após normalização; sem validação cadastral externa | não |
| logradouro | texto | Nome da via do estabelecimento | Texto; preservado como publicado | sim, se ausente na fonte |
| numero | texto | Número do endereço | Texto: admite S/N e combinações; não é medida numérica | sim |
| complemento | texto | Complemento do endereço | Texto livre; ausência não invalida preço | sim |
| bairro | texto | Bairro do estabelecimento | Texto livre | sim |
| cep | texto | Código postal do estabelecimento | Formato esperado 00000-000; validação descritiva | sim |
| produto | categórico | Combustível pesquisado | DIESEL S10 | não |
| data_coleta | data | Dia da pesquisa de preço | 2026-01-01 a 2026-06-30; origem dd/mm/aaaa | não |
| preco_venda | numérico decimal | Preço ao consumidor, em R$/litro | Maior que zero; máximo não imposto. Faixa de alerta 2–15 | não |
| preco_compra | numérico decimal na origem | Preço de distribuição; série encerrada em agosto de 2020 | Não disponível em 2026; não modelado como zero | sim, estrutural |
| unidade | categórico | Unidade de preço | R$ / litro | não |
| bandeira | categórico | Marca comercial declarada pelo posto | Categorias observadas abaixo; mudanças preservadas por versão | sim |

## Categorias e faixas observadas

- **regiao:** CO.
- **uf:** DF, GO.
- **municipio:** AGUAS LINDAS DE GOIAS, ANAPOLIS, APARECIDA DE GOIANIA, BRASILIA, CALDAS NOVAS, CATALAO, FORMOSA, GOIANIA, GOIATUBA, ITUMBIARA, LUZIANIA, MINEIROS, MORRINHOS, PORANGATU, RIO VERDE, TRINDADE, VALPARAISO DE GOIAS.
- **produto:** DIESEL S10.
- **unidade:** R$ / litro.
- **bandeira:** ALE, BRANCA, CIAPETRO, IPIRANGA, LARCO, MASUT DISTRIBUIDORA, NEXTA, RAIZEN, VIBRA.
- **Preço de venda:** R$ 5,39 a R$ 8,73/litro. A faixa observada não substitui o domínio esperado.
- **Datas de coleta:** 02/01/2026 a 30/06/2026.

Os valores categóricos de município e bandeira são o domínio observado desta versão. Novas categorias futuras devem ser registradas, não eliminadas por desconhecimento. Perfil de todos os atributos em `resultados/qualidade_atributos.csv`.

## Atributos do modelo estrela

| Campo / tabela | Tipo | Significado e domínio | Nulo | Linhagem / transformação |
|---|---|---|---|---|
| observacao_id / fato_preco | texto | 20 caracteres hexadecimais; chave única | não | SHA-256 truncado de CNPJ + produto + data |
| data_id / fato e dim_data | inteiro | 20260101 a 20260630, somente datas válidas | não | Data convertida para aaaammdd |
| data_coleta / dim_data | timestamp | Datas dentro do semestre; hora 00:00 | não | Parse estrito dd/mm/aaaa |
| semana / dim_data | timestamp | Segunda-feira, 2025-12-29 a 2026-06-29 | não | Subtração do número do dia da semana |
| mes / dim_data | inteiro | 1 a 6 | não | Mês da data_coleta |
| localidade_id / fato e dim_localidade | texto | 20 caracteres hexadecimais; chave de localidade | não | SHA-256 truncado de UF + município |
| uf, municipio, regiao / dim_localidade | texto | Domínios listados acima | não | Campos da origem após padronização |
| posto_id / fato e dim_posto | texto | 20 caracteres hexadecimais; versão descritiva do posto | não | Hash de CNPJ/nome/bandeira/logradouro/número/bairro/CEP |
| cnpj / dim_posto | texto | 14 dígitos, sem pontuação | não | Remoção de caracteres não numéricos |
| revenda, bandeira, logradouro, numero, bairro, cep / dim_posto | texto | Domínios descritos na tabela de origem | conforme origem | Atributos preservados por versão; não representa histórico fora do recorte |
| produto_id / fato e dim_produto | texto | diesel_s10 | não | Chave fixa para o produto do recorte |
| produto, unidade / dim_produto | texto | DIESEL S10; R$ / litro | não | Valores da origem filtrada |
| preco_venda / fato_preco | double | >0; alerta se <2 ou >15; observado 5,39–8,73 | não | Vírgula decimal convertida; valores inválidos vão à quarentena |

## Indicadores, rankings e cenários

| Campo | Domínio e unidade | Cálculo / significado |
|---|---|---|
| n_postos | Inteiro ≥1 | CNPJs distintos na localidade-semana |
| media, mediana, minimo, maximo, p25, p75 | R$/litro, positivos | Estatísticas sobre um preço mediano por posto-semana; quantis lineares |
| desvio | R$/litro ≥0; nulo se menos de 2 postos | Desvio-padrão amostral dos preços por posto-semana |
| elegivel | true ou false | Indicadores: ≥5 postos. Ranking: ≥12 semanas e ≥75% de cobertura |
| semana_completa | true ou false | Segunda-feira de 05/01 a 22/06/2026 |
| analise | true ou false | elegivel E semana_completa |
| iqr | R$/litro ≥0 | P75 − P25 |
| gap_litro | R$/litro ≥0 | mediana − P25 |
| gap_pct | Percentual de 0 a 100 | 100 × gap_litro / mediana |
| cv_pct | Percentual ≥0; sem máximo imposto | 100 × desvio / média |
| semanas, semanas_observadas, semanas_localidade | Inteiro de 1 a 25 nas análises principais | Semanas elegíveis distintas |
| postos_medios | Número real ≥5 | Média semanal de n_postos |
| mediana_media, iqr_medio, gap_medio, gap_pct_medio | Mesmas unidades dos indicadores-base | Médias não ponderadas entre semanas elegíveis |
| fracao_semanas_gap3 | Número de 0 a 1 | Proporção de semanas com gap_pct ≥3 |
| cobertura_suficiente | true ou false | Localidade com ≥12 semanas elegíveis |
| hipotese_atendida | true ou false | fracao_semanas_gap3 ≥0,5 e cobertura_suficiente; baixa cobertura deve ser interpretada como inconclusiva |
| fracao_abaixo | Número de 0 a 1 | Semanas do posto com preço estritamente inferior à mediana local / semanas observadas |
| desconto_medio_pct | Percentual; pode ser negativo; máximo ≤100 | Média de 100 × (mediana local − preço do posto) / mediana local |
| cobertura | Número de 0 a 1 | Semanas observadas / semanas elegíveis da localidade |
| litros_semanais | 1.000, 5.000 ou 10.000 litros | Volume hipotético de cenário; não medido |
| custo_referencia, custo_cenario | R$ >0 | Litros × mediana; litros × P25, respectivamente |
| economia_potencial | R$ ≥0 | custo_referencia − custo_cenario; simulação sem custos adicionais |

## Rastreabilidade dos arquivos auxiliares

`qualidade_atributos`: atributo (nome), linhas/nulos/distintos (inteiros ≥0), pct_nulos (0–100) e exemplos (texto, até oito categorias). `auditoria.json`: fonte e arquivo (texto), sha256_zip (64 caracteres hexadecimais), bytes/contagens (inteiros ≥0), horário UTC (ISO-8601), problemas (contagens por regra), datas mínima/máxima e ambiente. `resumo_ranking`: contagem de postos elegíveis por localidade e máximos de frequência/desconto, sem identificação de estabelecimentos.
