from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
W=ROOT/'runs/conditions_001'
E=json.loads((W/'eval.json').read_text());D=json.loads((W/'measurements/diagnostics.json').read_text())
OUT=ROOT/'manuscript/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.labelsize':8,'legend.fontsize':7.5})
def save(fig,name):
 for ext in ('pdf','svg','png'):fig.savefig(OUT/f'{name}.{ext}',dpi=300,bbox_inches='tight')
 plt.close(fig)
qs=[1,8,32,128];records=[]
fig,axes=plt.subplots(2,2,figsize=(6.7,5.5),sharex=True,sharey=True)
colors={'dictionary':'#2B6A98','zlib-ordinary':'#BE7026','zlib-dictionary':'#775992'}
labels={'dictionary':'Dictionary','zlib-ordinary':'zlib ordinary','zlib-dictionary':'zlib dictionary'}
for ni,n in enumerate((4096,16384)):
 for ki,kind in enumerate(('member','absent')):
  ax=axes[ki,ni]
  for m,color in colors.items():
   for pattern,ls,marker in [('dispersed','--','o'),('clustered','-','s')]:
    vals=[];lo=[];hi=[]
    for q in qs:
     v=[d['sizes'][m]/d['sizes']['ordinary'] for d in D if (d['domain'],d['n'],d['q'],d['kind'],d['pattern'])==('confirm',n,q,kind,pattern)]
     med=statistics.median(v);vals.append(med);lo.append(med-min(v));hi.append(max(v)-med)
     records.append(dict(n=n,kind=kind,q=q,mode=m,pattern=pattern,ratios=v))
    ax.errorbar(qs,vals,yerr=[lo,hi],color=color,linestyle=ls,marker=marker,markersize=3,linewidth=1,elinewidth=.6,capsize=1.5,label=f'{labels[m]}, {pattern}')
  ax.axhline(1,color='.7',linewidth=.7);ax.set_xscale('log',base=2);ax.set_xticks(qs,labels=qs);ax.set_ylim(0,1.15);ax.set_title(f"{'ABCD'[ki*2+ni]}  N = {n:,}, {kind}",loc='left',fontweight='bold');ax.grid(axis='y',alpha=.15)
  if ni==0:ax.set_ylabel('Frame bytes / ordinary')
  if ki==1:ax.set_xlabel('Queries per bundle, q')
handles,labels_=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels_,loc='lower center',ncol=2,bbox_to_anchor=(.5,-.015),frameon=False)
fig.subplots_adjust(wspace=.12,hspace=.26,bottom=.20);save(fig,'locality')
(OUT/'locality_source.json').write_text(json.dumps(records,indent=2))

fig,axes=plt.subplots(1,3,figsize=(6.7,2.65),sharey=True)
records=[]
for ax,base,letter in zip(axes,('ordinary','compact','dictionary'),'ABC'):
 for domain,marker,color in [('dev','o','#2B6A98'),('confirm','^','#BE7026')]:
  for qi,q in enumerate(qs):
   cells=[c for c in E['cells'] if c['domain']==domain and c['q']==q]
   for j,c in enumerate(cells):
    v=c['modes']['reset-zlib-'+base]['reset_fresh_ratio'];x=qi+(j-3.5)*.035+(-.045 if domain=='dev' else .045)
    ax.scatter(x,v,s=12,marker=marker,facecolors='none',edgecolors=color,linewidth=.7,label=domain if qi==0 and j==0 else None)
    records.append(dict(domain=domain,cell=c['cell'],representation=base,ratio=v))
 ax.axhline(1,color='.35',linewidth=.8);ax.axhline(.9,color='.6',linestyle=':',linewidth=.8)
 ax.set_title(f'{letter}  {base.capitalize()}',loc='left',fontweight='bold');ax.set_xticks(range(4),labels=qs);ax.set_xlabel('Queries per bundle, q');ax.set_xlim(-.4,3.4);ax.set_ylim(.25,1.13);ax.grid(axis='y',alpha=.15)
axes[0].set_ylabel('Reset / fresh paired local-time ratio');handles,labels_=axes[0].get_legend_handles_labels();fig.legend(handles,['Development','Confirmation'],loc='lower center',bbox_to_anchor=(.5,-.06),ncol=2,frameon=False)
fig.subplots_adjust(wspace=.12,bottom=.24);save(fig,'lifecycle')
(OUT/'lifecycle_source.json').write_text(json.dumps(records,indent=2))
print('Two figures exported with source summaries.')
