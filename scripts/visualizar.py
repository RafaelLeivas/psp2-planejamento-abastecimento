"""Gráficos reproduzíveis a partir dos resultados agregados."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def plot(root):
    root=Path(root); dest=root/'figuras'; dest.mkdir(exist_ok=True)
    weekly=pd.read_csv(root/'resultados/indicadores_semanais.csv',parse_dates=['semana'])
    summary=pd.read_csv(root/'resultados/resumo_localidades.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f5f7fa','axes.facecolor':'#f5f7fa','axes.titleweight':'bold'})
    palette=['#066b79','#eb8b23','#6555a3']
    fig,ax=plt.subplots(figsize=(11,5.5))
    for city,color in zip(['BRASILIA','GOIANIA','ANAPOLIS'],palette):
        x=weekly.loc[weekly.municipio.eq(city)&weekly.analise].sort_values('semana')
        ax.plot(x.semana,x.mediana,marker='o',markersize=3,label=city.title(),color=color,linewidth=2)
    ax.set(title='O orçamento precisa acompanhar a variação semanal',ylabel='Mediana do diesel S10 (R$/litro)',xlabel='Semana de coleta | jan–jun/2026')
    ax.legend(frameon=False,ncol=3); ax.grid(axis='y',alpha=.2)
    fig.text(.02,.015,'Fonte: ANP/LPC. Cálculos próprios. Um preço por posto-semana; mínimo de 5 postos. Semanas de borda excluídas.',fontsize=8,color='#52606d')
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(dest/'01_evolucao.png',dpi=180);plt.close(fig)
    x=summary.loc[summary.cobertura_suficiente].sort_values('gap_pct_medio')
    fig,ax=plt.subplots(figsize=(10,7))
    ax.barh(x.municipio.str.title(),x.gap_pct_medio,color='#066b79')
    ax.set(title='Diferença entre mediana e P25: oportunidade histórica',xlabel='Média das diferenças relativas semanais (%)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:.1f}%'))
    for i,v in enumerate(x.gap_pct_medio):ax.text(v+.025,i,f'{v:.2f}%',va='center',fontsize=9)
    ax.set_xlim(0,3.2);ax.grid(axis='x',alpha=.2)
    fig.text(.02,.015,'Fonte: ANP/LPC. Localidades com ≥12 semanas elegíveis. Não representa economia obtida nem cotação atual.',fontsize=8,color='#52606d')
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(dest/'02_oportunidade.png',dpi=180);plt.close(fig)
    x=summary.loc[summary.municipio.isin(['BRASILIA','GOIANIA','ANAPOLIS'])].sort_values('gap_medio')
    fig,ax=plt.subplots(figsize=(10,4.8))
    ax.barh(x.municipio.str.title(),x.gap_medio*5000,color=palette)
    for i,v in enumerate(x.gap_medio*5000):ax.text(v+12,i,f'R$ {v:,.2f}',va='center')
    ax.set(title='Cenário: 5.000 litros por semana',xlabel='Diferença média semanal de gasto (R$) | mediana versus P25',xlim=(0,1100))
    ax.grid(axis='x',alpha=.2)
    fig.text(.02,.015,'Simulação com volume hipotético. Sem custos de desvio, negociação ou disponibilidade. Fonte dos preços: ANP.',fontsize=8,color='#52606d')
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(dest/'03_cenario.png',dpi=180);plt.close(fig)

if __name__=='__main__': plot(Path(__file__).resolve().parents[1])
