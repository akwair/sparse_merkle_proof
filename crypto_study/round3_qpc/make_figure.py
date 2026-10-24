from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'AUDIT.json').read_text())['comparisons']
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'pdf.fonttype':42,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
fig,axes=plt.subplots(1,2,figsize=(7.2,3.4),sharey=True)
groups=[('reference','bitmap','Reference: JSON bitmap\n12 cells','#5879a2'),('reference','binary-bitmap','Reference: binary bitmap\n12 cells','#388577'),('external','compact','External: compact\n24 cells','#b5773b')]
for y,(host,mode,label,color) in enumerate(groups):
    points=sorted([x for x in data if x['host']==host],key=lambda x:(x['domain'],x['cell']))
    for i,x in enumerate(points):
        pos=y+(i/(len(points)-1)-.5)*.44
        marker='o' if x['domain']=='dev' else '^'
        for ax,metric in zip(axes,['byte_ratio','time_ratio']):
            ax.scatter(x['comparisons'][mode][metric],pos,s=18,marker=marker,color=color,alpha=.85,linewidths=.35,edgecolors='white',zorder=3)
for ax in axes:
    ax.axvline(1,color='#666666',lw=.8,ls='--',zorder=1)
    ax.grid(axis='x',color='#e7e7e7',lw=.5)
    ax.set_ylim(2.55,-.55)
axes[0].set_yticks(range(3),[x[2] for x in groups]);axes[0].set_xscale('log');axes[0].set_xlim(.02,1.15)
axes[0].set_xticks([.03,.1,.3,1],['0.03','0.1','0.3','1'])
axes[0].set_xlabel('Complete bytes / native full (log scale)')
axes[1].set_xlim(.85,1.41);axes[1].set_xlabel('Paired local total time / native full')
axes[0].set_title('A  Wire size',loc='left',fontweight='bold');axes[1].set_title('B  Local processing',loc='left',fontweight='bold')
fig.legend(handles=[Line2D([],[],color='#666666',marker='o',linestyle='',markersize=4,label='Domain 1'),Line2D([],[],color='#666666',marker='^',linestyle='',markersize=4,label='Domain 2')],loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.6,.01))
fig.subplots_adjust(left=.27,right=.98,top=.88,bottom=.23,wspace=.17)
out=ROOT/'analysis';out.mkdir(exist_ok=True)
for ext in ('pdf','svg','png'):fig.savefig(out/('baseline_sensitivity.'+ext),dpi=300)
plt.close(fig)
print('Figure saved from audited cell summaries.')
