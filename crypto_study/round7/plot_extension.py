"""Publication plots from sealed/audited evidence, Python only."""
from pathlib import Path
import json,statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'manuscript/figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
 'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.right':False,'axes.spines.top':False,
 'legend.frameon':False,'axes.linewidth':.7,'lines.linewidth':1.3,'xtick.labelsize':8,'ytick.labelsize':8})
BLUE='#276987';ORANGE='#AE6635';GRAY='#666666'

def read(p):return json.loads(p.read_text(encoding='utf8'))

def save(fig,name,data):
    for suffix in ('pdf','svg','png'):fig.savefig(OUT/f'{name}.{suffix}',dpi=300,bbox_inches='tight',pad_inches=.04)
    (OUT/f'{name}_source.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf8')
    plt.close(fig)

def application():
    ds=read(ROOT/'runs/app_001/measurements/diagnostics.json');source=[]
    fig,axes=plt.subplots(2,2,figsize=(6.69,3.94),sharex=True,sharey=True,layout='constrained')
    for ax,(n,v),letter in zip(axes.flat,[(4096,32),(4096,1000),(16384,32),(16384,1000)],'abcd'):
        for dist,color,marker,offset in [('uniform',BLUE,'o',-.04),('zipf',ORANGE,'s',.04)]:
            xx=np.arange(4,dtype=float)+offset;med=[];lo=[];hi=[]
            for j,q in enumerate((1,8,32,128)):
                selected=sorted((d for d in ds if (d['domain'],d['n'],d['value_bytes'],d['q'],d['distribution'])==('confirm',n,v,q,dist)),key=lambda x:x['batch'])
                assert len(selected)==3
                yy=[d['sizes']['dictionary']/d['sizes']['ordinary'] for d in selected]
                m=st.median(yy);med.append(m);lo.append(m-min(yy));hi.append(max(yy)-m)
                ax.scatter([xx[j]]*3,yy,color=color,s=10,alpha=.35,zorder=2)
                source.append(dict(n=n,value_bytes=v,q=q,distribution=dist,domain='confirm',bundle_ratios=yy,median=m))
            ax.errorbar(xx,med,yerr=[lo,hi],color=color,marker=marker,ms=3.5,capsize=2,label='Uniform' if dist=='uniform' else 'Finite Zipf (0.99)')
        ax.axhline(1,color=GRAY,lw=.7,ls=':');ax.set_title(f'{letter}   N = {n:,}; value = {v} B',loc='left')
        ax.set_xticks(range(4),['1','8','32','128']);ax.set_ylim(.42,1.14);ax.grid(axis='y',color='#e8e8e8',lw=.5)
    axes[0,0].legend(loc='lower left',fontsize=7)
    for ax in axes[:,0]:ax.set_ylabel('Dictionary / ordinary bytes')
    for ax in axes[-1,:]:ax.set_xlabel('Queries per response, q')
    save(fig,'application_bytes',source)

def spread():
    r=read(ROOT/'REPETITIONS.json');source={}
    fig,ax=plt.subplots(figsize=(6.69,2.83),layout='constrained')
    for key,color,label in [('application_cells',BLUE,'Application service path'),('frozen_cells',ORANGE,'Controlled-corpus codec path')]:
        xs=sorted(s['absolute_spread'] for c in r[key] for s in c['modes'].values());assert len(xs)==576
        source[key]=xs
        ax.step(xs,np.arange(1,577)/576,where='post',color=color,label=f'{label} ({sum(x>1.2 for x in xs)}/576 > 1.20)')
    ax.axvline(1.2,color=GRAY,ls=':',lw=1);ax.set_xlim(1,2.68);ax.set_ylim(0,1.02)
    ax.set_xlabel('Largest / smallest absolute cell median across five processes')
    ax.set_ylabel('Fraction of cell-mode summaries');ax.legend(loc='lower right',fontsize=7.5)
    ax.grid(axis='y',color='#e8e8e8',lw=.5)
    save(fig,'process_spread',source)

def allocations():
    e=read(ROOT/'diagnostics/runs/allocation_001/eval.json')
    cases=[f'dev_n16384_q{q}_v32_member_{d}_b0' for d in ('uniform','zipf') for q in (1,128)]
    fig,axes=plt.subplots(2,2,figsize=(6.69,3.94),sharey=True,layout='constrained');source=[]
    for ax,case,letter in zip(axes.flat,cases,'abcd'):
        for reset,color,offset,label in [(False,BLUE,-.12,'Fresh writer'),(True,ORANGE,.12,'Primed reset')]:
            for j,mode in enumerate(('zlib-ordinary','zlib-compact','zlib-dictionary')):
                m=('reset-' if reset else '')+mode;c=next(c for c in e['cells'] if(c['id'],c['stage'],c['mode'])==(case,'encode',m))
                b=c['bytes_per_operation'];yy=np.array(b['values'])/1024;assert np.all(yy>0)
                ax.scatter(j+offset+np.linspace(-.025,.025,5),yy,s=9,alpha=.5,color=color)
                ax.errorbar(j+offset,b['median']/1024,yerr=[[(b['median']-b['min'])/1024],[(b['max']-b['median'])/1024]],color=color,fmt='o',ms=4,capsize=2,label=label if j==0 else None)
                source.append(c)
        q=128 if '_q128_' in case else 1;dist='Uniform' if '_uniform_' in case else 'Finite Zipf'
        ax.set_title(f'{letter}   {dist}; q = {q}',loc='left');ax.set_xticks(range(3),['Ordinary','Compact','Dictionary'])
        ax.set_yscale('log');ax.grid(axis='y',color='#e8e8e8',lw=.5)
    axes[0,0].legend(fontsize=7,loc='lower right')
    for ax in axes[:,0]:ax.set_ylabel('Encoding allocation (KiB/op)')
    for ax in axes[-1,:]:ax.set_xlabel('Representation before zlib')
    save(fig,'stage_allocations',source)

if __name__=='__main__':
    import sys
    OUT.mkdir(exist_ok=True)
    if len(sys.argv)>1 and sys.argv[1]=='allocation':allocations()
    else:application();spread()
