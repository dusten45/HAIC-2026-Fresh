"""Saved public aggregates only; no model imports or new experiment."""
import time
START=time.perf_counter()
import hashlib,json,os,sys
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/haic-stage483-matplotlib-cache')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/haic-stage483-render-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
G=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
    source=G/'retry/diagnostic483_result.json';public=json.loads(source.read_text());out=public['outcome'];parents={r['arm']:r for r in out['parents'] if r['repetition']==1}
    assert out['common_executed_own_actions']==4 and out['same_elapsed_common_prefix']
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for arm,color in [('control','#b04a3e'),('variant','#216e96')]:
        r=parents[arm];n=r['actions'];xs=list(range(1,n+1));common=4
        for ax,field in zip(axes,('margins_m','own_M80')):
            ax.plot(xs[:common],r[field][:common],'-o',color=color,label=arm)
            if n>common:ax.plot(xs[common-1:],r[field][common-1:],'--o',color=color,label='variant beyond common prefix')
    axes[0].axhline(out['root_inclusive_margin_upper_bound_m'],color='grey',ls=':',label='common root ceiling')
    axes[0].axhline(0,color='black',lw=.8);axes[0].set_ylabel('remaining 3 m raw path margin, m')
    axes[0].set_title('Own hold margin (root and all raw poses included)')
    axes[1].set_ylabel('M80 = max(force ratio - 1, 0)');axes[1].set_title('Own observed force objective')
    for ax in axes:
        ax.axvspan(4.5,6.4,color='grey',alpha=.08);ax.axvline(4.5,color='grey',ls=':');ax.set_xticks(range(1,7));ax.set_xlim(.7,6.3);ax.set_xlabel('local own hold; control stops before hold 5');ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('483: common-prefix margin gain +0.552502 m; registered cut >0.25 m\nSame posthoc cold root, two repeated branches per arm; no finish/generalization claim',fontsize=10)
    fig.tight_layout(rect=(0,0,1,.86));target=G/'retry/diagnostic483_comparison.png';assert not target.exists();fig.savefig(target,dpi=150);plt.close(fig)
    cost=dict(stage=483,scope='SAVED_AGGREGATE_RENDER_NO_PHYSICS',CPU_s=time.process_time(),wall_s=time.perf_counter()-START,input_sha256=sha(source),source_code_sha256=sha(__file__),image_sha256=sha(target),image_bytes=target.stat().st_size,new_worlds=0,new_ticks=0)
    p=root/'stage483-render-cost-private.json'
    with p.open('x') as f:json.dump(cost,f,indent=2);f.write('\n')
    print(json.dumps(cost))
if __name__=='__main__':run(Path(sys.argv[1]))
