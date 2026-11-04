# Evidências de execução

## Estado verificável

A execução local está documentada em `resultados/auditoria.json` e nos CSVs e gráficos do repositório. **Isso não comprova execução na nuvem.** A pasta ainda não contém capturas de execução Databricks.

## Após executar o notebook

1. Capture a saída da célula de persistência: lista de tabelas e respectivas contagens, com o ambiente Databricks visível.
2. Capture `DESCRIBE DETAIL` da tabela fato, mostrando formato Delta e localização.
3. Reinicie a sessão e execute a última célula; capture a contagem da fato e `SHOW TABLES`.
4. Capture resultados de perguntas e gráficos com legendas legíveis.
5. Baixe `evidencia_execucao.json` do Volume. Ele registra catálogo/schema, contagens, hash e data da execução.

Publicar somente capturas reais, revisadas para não expor tokens ou dados pessoais desnecessários. Referenciar cada captura junto à afirmação correspondente no README. Atualizar o estado da entrega somente depois da verificação.
