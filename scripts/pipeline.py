"""PSP2: pipeline ANP reproduzível. Python 3.10+, pandas 2.x/3.x.

Uso: python scripts/pipeline.py --zip caminho/ca-2026-01.zip --out resultados
O download oficial é realizado quando --zip não aponta para arquivo existente.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
import pandas as pd

SOURCE = 'https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip'
COLS = ['regiao','uf','municipio','revenda','cnpj','logradouro','numero','complemento','bairro','cep','produto','data_coleta','preco_venda','preco_compra','unidade','bandeira']

def stable_id(s):
    return hashlib.sha256(str(s).encode()).hexdigest()[:20]

def run(zip_path, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    zip_path = Path(zip_path)
    if not zip_path.exists():
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SOURCE, zip_path)
    blob = zip_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith('.csv'))
        raw = pd.read_csv(archive.open(member), sep=';', dtype=str, encoding='utf-8-sig')
    original_columns = list(raw.columns)
    assert len(raw.columns) == len(COLS), 'Esquema da fonte mudou; revisar mapeamento.'
    raw.columns = COLS
    for c in COLS:
        raw[c] = raw[c].str.strip().replace('', pd.NA)
    scope = raw.loc[raw.uf.isin(['DF','GO']) & raw.produto.eq('DIESEL S10')].copy()
    assert not scope.empty, 'Recorte vazio.'
    scope.to_csv(out/'bronze_recorte.csv',index=False)
    profile = []
    for c in COLS:
        s = scope[c]
        profile.append({'atributo':c,'linhas':len(s),'nulos':int(s.isna().sum()),'pct_nulos':round(s.isna().mean()*100,4),'distintos':int(s.nunique()),'exemplos':' | '.join(s.dropna().unique()[:8])})
    pd.DataFrame(profile).to_csv(out/'qualidade_atributos.csv',index=False)
    n_exact = int(scope.duplicated().sum())
    df = scope.drop_duplicates().copy()
    df['data_coleta'] = pd.to_datetime(df.data_coleta,format='%d/%m/%Y',errors='coerce')
    df['preco_venda'] = pd.to_numeric(df.preco_venda.str.replace(',','.',regex=False),errors='coerce')
    df['cnpj'] = df.cnpj.str.replace(r'\D','',regex=True)
    checks = pd.DataFrame({
        'data_invalida':df.data_coleta.isna() | ~df.data_coleta.between('2026-01-01','2026-06-30'),
        'preco_invalido':df.preco_venda.isna() | df.preco_venda.le(0),
        'cnpj_invalido':~df.cnpj.str.fullmatch(r'\d{14}',na=False),
        'localidade_ausente':df.municipio.isna(),
        'unidade_invalida':~df.unidade.eq('R$ / litro'),
        'regiao_inconsistente':~df.regiao.eq('CO'),
    })
    invalid = checks.any(axis=1)
    quarantine = df.loc[invalid].copy()
    quarantine['motivos'] = [';'.join(checks.columns[row.to_numpy(dtype=bool)]) for _,row in checks.loc[invalid].iterrows()]
    quarantine.to_csv(out/'quarentena.csv',index=False)
    df = df.loc[~invalid].copy()
    keys = ['cnpj','produto','data_coleta']
    conflict = df.duplicated(keys, keep=False)
    df.loc[conflict].to_csv(out/'conflitos_chave.csv',index=False)
    assert not conflict.any(), 'Chaves conflitantes: resolver antes de analisar; arquivo conflitos_chave.csv.'
    assert not df.empty
    df['semana'] = df.data_coleta - pd.to_timedelta(df.data_coleta.dt.weekday,unit='D')
    df['localidade_id'] = (df.uf+'|'+df.municipio).map(stable_id)
    # Versão de posto inclui atributos descritivos; preserva mudanças históricas sem escolher arbitrariamente o último nome.
    df['posto_id'] = df[['cnpj','revenda','bandeira','logradouro','numero','bairro','cep']].fillna('').agg('|'.join,axis=1).map(stable_id)
    df['data_id'] = df.data_coleta.dt.strftime('%Y%m%d').astype(int)
    df['produto_id'] = 'diesel_s10'
    df['observacao_id'] = df[keys].astype(str).agg('|'.join,axis=1).map(stable_id)
    dates = df[['data_id','data_coleta','semana']].drop_duplicates().sort_values('data_id')
    dates['mes'] = dates.data_coleta.dt.month
    loc = df[['localidade_id','uf','municipio','regiao']].drop_duplicates()
    posts = df[['posto_id','cnpj','revenda','bandeira','logradouro','numero','bairro','cep']].drop_duplicates()
    prod = pd.DataFrame([{'produto_id':'diesel_s10','produto':'DIESEL S10','unidade':'R$ / litro'}])
    fact = df[['observacao_id','data_id','localidade_id','posto_id','produto_id','preco_venda']]
    tables = {'dim_data':dates,'dim_localidade':loc,'dim_posto':posts,'dim_produto':prod,'fato_preco':fact}
    for name, table in tables.items(): table.to_csv(out/(name+'.csv'),index=False)
    # Um voto por posto por semana; múltiplas coletas do mesmo posto são resumidas pela mediana.
    pw = df.groupby(['uf','municipio','localidade_id','semana','cnpj'],as_index=False).agg(preco=('preco_venda','median'),n_coletas=('preco_venda','size'))
    group = ['uf','municipio','localidade_id','semana']
    weekly = pw.groupby(group).agg(n_postos=('cnpj','nunique'),media=('preco','mean'),mediana=('preco','median'),minimo=('preco','min'),maximo=('preco','max'),desvio=('preco','std')).reset_index()
    qs = pw.groupby(group).preco.quantile([.25,.75]).unstack().reset_index().rename(columns={.25:'p25',.75:'p75'})
    weekly = weekly.merge(qs,on=group,validate='one_to_one')
    weekly['elegivel'] = weekly.n_postos.ge(5)
    weekly['semana_completa'] = weekly.semana.between('2026-01-05','2026-06-22')
    weekly['analise'] = weekly.elegivel & weekly.semana_completa
    weekly['iqr'] = weekly.p75-weekly.p25
    weekly['gap_litro'] = weekly.mediana-weekly.p25
    weekly['gap_pct'] = 100*weekly.gap_litro/weekly.mediana
    weekly['cv_pct'] = 100*weekly.desvio/weekly.media
    weekly.to_csv(out/'indicadores_semanais.csv',index=False)
    valid = weekly.loc[weekly.analise].copy()
    assert not valid.empty
    summary = valid.groupby(['uf','municipio'],as_index=False).agg(semanas=('semana','nunique'),postos_medios=('n_postos','mean'),mediana_media=('mediana','mean'),iqr_medio=('iqr','mean'),gap_medio=('gap_litro','mean'),gap_pct_medio=('gap_pct','mean'),fracao_semanas_gap3=('gap_pct',lambda s:float(s.ge(3).mean())))
    summary['hipotese_atendida'] = (summary.fracao_semanas_gap3.ge(.5) & summary.semanas.ge(12))
    summary['cobertura_suficiente'] = summary.semanas.ge(12)
    summary.to_csv(out/'resumo_localidades.csv',index=False)
    ref = valid[group+['mediana']]
    ranked = pw.merge(ref,on=group,how='inner',validate='many_to_one')
    ranked['abaixo'] = ranked.preco.lt(ranked.mediana)
    ranked['desconto_pct'] = 100*(ranked.mediana-ranked.preco)/ranked.mediana
    ranks = ranked.groupby(['uf','municipio','cnpj'],as_index=False).agg(semanas_observadas=('semana','nunique'),fracao_abaixo=('abaixo','mean'),desconto_medio_pct=('desconto_pct','mean'))
    available = valid.groupby(['uf','municipio']).semana.nunique().rename('semanas_localidade').reset_index()
    ranks = ranks.merge(available,on=['uf','municipio'],validate='many_to_one')
    ranks['cobertura'] = ranks.semanas_observadas/ranks.semanas_localidade
    ranks['elegivel'] = ranks.semanas_observadas.ge(12) & ranks.cobertura.ge(.75)
    ranks = ranks.sort_values(['elegivel','fracao_abaixo','desconto_medio_pct'],ascending=False)
    ranks.to_csv(out/'ranking_postos.csv',index=False)
    scenarios = pd.concat([valid.assign(litros_semanais=v,custo_referencia=valid.mediana*v,custo_cenario=valid.p25*v,economia_potencial=valid.gap_litro*v) for v in [1000,5000,10000]],ignore_index=True)
    scenarios.to_csv(out/'cenarios.csv',index=False)
    # Sinalização de extremos: não excluir preços válidos somente por serem extremos.
    unusual = int((df.preco_venda.lt(2) | df.preco_venda.gt(15)).sum())
    audit = {'source_url':SOURCE,'arquivo_interno':member,'sha256_zip':hashlib.sha256(blob).hexdigest(),'bytes_zip':len(blob),'executado_em_utc':datetime.now(timezone.utc).isoformat(),'ambiente':'local_python','linhas_fonte':len(raw),'linhas_recorte':len(scope),'duplicatas_exatas_removidas':n_exact,'linhas_quarentena':int(invalid.sum()),'linhas_finais':len(df),'problemas':{c:int(checks[c].sum()) for c in checks},'precos_fora_faixa_alerta_2_15':unusual,'data_min':str(df.data_coleta.min().date()),'data_max':str(df.data_coleta.max().date()),'postos':int(df.cnpj.nunique()),'localidades':len(loc),'semanas_elegiveis':len(valid),'colunas_originais':original_columns}
    (out/'auditoria.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))
    return tables, weekly, summary, ranks, scenarios, audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--zip',default='data/ca-2026-01.zip'); parser.add_argument('--out',default='resultados')
    args = parser.parse_args(); run(args.zip,args.out)
