"""Read completed cold cases; reference exposure is descriptive, not causal."""
import json,math,time,signal
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('ACCOUNT_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];rows=[]
 for stage in (536,538):
  q=json.loads(Path(f'/workspace/haic-response{stage}-private/cold-candidate-private.json').read_text());t=q['trace'];z=[r for r in t if r['index']>24];v=lambda r:math.hypot(*r['root_without_roads']['planar']['linear']['velocity']);rows.append(dict(stage=stage,finish_s=q['summary']['model_finish_episode_s'],post_launch_s=.02*len(z),above_reference_s=.02*sum(v(r)>r['target'] for r in z),mean_positive_reference_deficit_m_s=sum(max(0.,r['target']-v(r)) for r in z)/len(z),mean_positive_reference_surplus_m_s=sum(max(0.,v(r)-r['target']) for r in z)/len(z),mean_peak_force=sum(max(f['ratio'] for f in r['forces']) for r in z)/len(z),sampled_body_chord_distance_m=sum(math.dist(a['root_without_roads']['center'],b['root_without_roads']['center']) for a,b in zip(t,t[1:]))))
 out=dict(rows=rows,interpretation='Same frozen reference/profile; candidate exploits allowed reference deviation as well as reducing some deficit. Exposure changes and fixed-clock differences are not recoverable or causal time gains; only official fresh actual pair can establish actual performance.',native_actions=0,model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/transfer538_accounting.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
