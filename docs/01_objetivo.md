# PSP2 — Planejamento de abastecimento de frotas

Professor: André Luiz Marques Serrano. Universidade de Brasília, Engenharia de Produção.

## Registro anterior à coleta

Escopo definido em 04/11/2026, antes do processamento: diesel S10, Distrito Federal e Goiás, janeiro a junho de 2026. Público-alvo: gestores de operações e compras de pequenas frotas. Estudo com dados secundários; não representa consultoria contratada por empresa real.

## Problema e objetivo

Como apoiar o orçamento de combustível e a seleção de postos para cotação usando referências históricas locais de preços? Construir um pipeline reproduzível em nuvem que transforme observações da ANP em indicadores semanais e cenários explícitos de custo.

## Perguntas preservadas

1. Como os preços variaram semanalmente nas localidades analisadas?
2. Onde houve maior dispersão de preços entre os postos pesquisados?
3. Quais postos apresentaram preços abaixo da mediana local com maior frequência e cobertura suficiente de observações?
4. Qual seria a diferença de gasto em cenários de consumo, comparando a mediana com uma referência de preço inferior?
5. Que regras de acompanhamento e revisão do orçamento podem ser propostas a partir dos resultados?

## Hipótese e critério de avaliação definidos previamente

Hipótese exploratória: existem diferenças recorrentes entre a mediana e o primeiro quartil dos preços locais que justificam pesquisar fornecedores antes de abastecer. Métrica: diferença relativa (mediana - P25) / mediana por município-semana. Critério de interesse gerencial, escolhido para este experimento e não como padrão universal: diferença de pelo menos 3% em ao menos metade das semanas elegíveis de uma localidade. Cada semana elegível exige pelo menos cinco postos distintos. A hipótese pode ser refutada ou permanecer inconclusiva.

## Limites

Sem dados de rotas, contratos, qualidade do serviço ou consumo real, não será possível otimizar rotas nem comprovar economia realizada. Os cenários usarão volumes hipotéticos de 1.000, 5.000 e 10.000 litros por semana, sem representar compras efetivas. Preços históricos não são cotações atuais. A desejabilidade será discutida como hipótese, sem alegar validação com usuários.
