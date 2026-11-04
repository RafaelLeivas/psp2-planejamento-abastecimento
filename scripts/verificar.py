"""Verifica integridade dos resultados e gera o resumo público do ranking.
Execute após pipeline.py: python scripts/verificar.py
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import json
import platform
import pandas as pd
import numpy as np

root=Path(__file__).resolve().parents[1]
out=root/'resultados'
f=pd.read_csv(out/'fato_preco.csv')
assert f.observacao_id.is_unique and f.observacao_id.notna().all()
contagens={'fato_preco':len(f)}
for name,key in [('dim_data','data_id'),('dim_posto','posto_id'),('dim_localidade','localidade_id'),('dim_produto','produto_id')]:
    d=pd.read_csv(out/(name+'.csv'))
    assert d[key].is_unique and d[key].notna().all(),name
    assert f[key].isin(d[key]).all(),key
    assert len(f.merge(d,on=key,validate='many_to_one'))==len(f),name
    contagens[name]=len(d)
w=pd.read_csv(out/'indicadores_semanais.csv')
assert not w.duplicated(['uf','municipio','semana']).any()
assert ((w.minimo<=w.p25)&(w.p25<=w.mediana)&(w.mediana<=w.p75)&(w.p75<=w.maximo)).all()
assert w.loc[w.analise].n_postos.ge(5).all()
c=pd.read_csv(out/'cenarios.csv')
assert np.allclose(c.custo_referencia-c.custo_cenario,c.economia_potencial)
assert np.allclose(c.litros_semanais*c.gap_litro,c.economia_potencial)
assert len(c)==3*int(w.analise.sum())
r=pd.read_csv(out/'ranking_postos.csv',dtype={'cnpj':str})
assert r.cobertura.between(0,1).all()
assert r.fracao_abaixo.between(0,1).all()
assert r.loc[r.elegivel].semanas_observadas.ge(12).all()
assert r.loc[r.elegivel].cobertura.ge(.75).all()
r.loc[r.elegivel].groupby(['uf','municipio'],as_index=False).agg(postos_elegiveis=('cnpj','nunique'),maior_fracao_abaixo=('fracao_abaixo','max'),maior_desconto_medio_pct=('desconto_medio_pct','max')).to_csv(out/'resumo_ranking.csv',index=False)
nb=json.loads((root/'notebooks/PSP2_Abastecimento.ipynb').read_text(encoding='utf-8'))
for cell in nb['cells']:
    if cell['cell_type']=='code':ast.parse(''.join(cell['source']))
report={'status':'aprovado','ambiente':'local_python','verificado_em_utc':datetime.now(timezone.utc).isoformat(),
        'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,
        'contagens':contagens,'municipio_semanas_analise':int(w.analise.sum()),'cenarios':len(c),'postos_ranking_elegiveis':int(r.elegivel.sum()),
        'verificacoes':['unicidade de PK','FK sem órfãos','joins sem multiplicação da fato','ordem dos quantis','filtros de cobertura','aritmética dos cenários','sintaxe das células Python do notebook'],
        'limite':'Não comprova execução Spark/Delta ou persistência no Databricks.'}
(out/'validacao_local.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
