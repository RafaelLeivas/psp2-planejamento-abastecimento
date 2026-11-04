# Executar o projeto no Databricks

1. Baixe `notebooks/PSP2_Abastecimento.ipynb` deste repositório (abra o arquivo e use Download raw file).
2. No Databricks, abra Workspace e sua pasta de usuário. No menu da pasta, escolha Import → File; selecione o notebook.
3. Abra o notebook importado. Se for necessário escolher compute, selecione Serverless.
4. Clique em Run all. A primeira célula cria o schema `psp2_abastecimento` e o volume `arquivos` no catálogo atual. Anote o caminho exibido.
5. Se a coleta falhar por bloqueio de rede, baixe o [ZIP oficial](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip), sem descompactar.
6. Abra Catalog → catálogo exibido na primeira célula → psp2_abastecimento → arquivos → Upload. Envie `ca-2026-01.zip` à raiz do volume, mantendo esse nome.
7. Volte ao notebook e execute Run all novamente. O pipeline detecta o arquivo existente e não precisa baixá-lo.
8. A célula de persistência deve mostrar 3.789 linhas na fato para a versão da fonte com SHA-256 `a2c95e5dfa324a9d7253d4e8d53022e0c08dcc5eb6f18551527ee9f29305c54c`.
9. Confirme a mensagem de persistência e integridade. Salve as evidências descritas em `evidencias/README.md`.
10. Reinicie a sessão de execução e rode apenas a última célula: ela deve consultar as tabelas sem recriar os dados.

## Erros comuns

- **Acesso de rede negado à ANP:** execute o envio manual descrito acima; não desative controles de segurança.
- **Catálogo hive_metastore ou system:** edite a variável CATALOGO para um catálogo Unity Catalog em que você tenha permissão, por exemplo workspace, se ele existir.
- **Arquivo ZIP inválido:** confira se o download não salvou uma página HTML e se o nome é `ca-2026-01.zip`.
- **Quota Serverless:** aguarde a disponibilidade indicada pelo Databricks; não contratar plano pago automaticamente.
- **Conflitos de chave ou esquema diferente:** preserve os arquivos gerados e revise a fonte; o pipeline não deve ocultar essas falhas.

O notebook não requer token. As tabelas de projeto são sobrescritas em reexecuções; não altere SCHEMA para um schema de produção.
