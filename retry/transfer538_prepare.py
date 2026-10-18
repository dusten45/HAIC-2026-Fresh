"""Select a new normal root from frozen536 only; no model/policy execution."""
import hashlib,json,math,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];S=Path('/workspace/haic-response536-private');P=Path('/workspace/haic-response537-private');D=Path('/workspace/haic-response538-private');D.mkdir(mode=0o700,exist_ok=False)
 read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 rows=read(P/'accounting-corrected-rows-private.json');eligible=[]
 for f in sorted(S.glob('action-candidate-*.json')):
  a=read(f);r=a['record'];i=r['index'];v=math.hypot(*a['before_root_without_roads']['planar']['linear']['velocity']);cap=min(1.,29.249793766661764*35.0188778925416*(v+2.7)/80000);window=[q for q in rows if q['index']==i]
  if 49<=i<=165 and i not in (40,166) and r['governor_mode']=='HIGH' and abs(r['action'][1]-cap)<1e-6 and max(q['force'] for q in window)<.9:eligible.append(i)
 runs=[]
 for i in eligible:
  if not runs or i!=runs[-1][-1]+1:runs.append([i])
  else:runs[-1].append(i)
 assert runs;run=min(runs,key=lambda x:(-len(x),x[0]));chosen=run[0];a=read(S/('action-candidate-%03d.json'%chosen));native_raw=[read(f) for f in sorted(S.glob('raw-*.json'))][1022:];history=[r for r in native_raw if 24<r['action']<chosen]
 normal=dict(label='normal-acceleration',index=chosen,holds=24,completed=chosen-1,root_without_roads=a['before_root_without_roads'],history=dict(samples=4*len(history),clipped=sum(z['ratio']>1 for r in history for z in r['forces'])))
 risk=[c for c in read(P/'pilot-roots-private.json') if c['label'] in ('curvature','footprint')];assert [c['index'] for c in risk]==[40,166]
 assert not any((P/(c['label']+'-'+arm+'-private.json')).exists() for c in risk for arm in ('baseline','candidate'))
 for name in ('frozen-paths-private.json','approved-case-private.json'):
  (D/name).write_bytes((P/name).read_bytes());(D/name).chmod(0o600)
 with (D/'pilot-roots-private.json').open('x') as f:json.dump(risk+[normal],f)
 prior=read(G/'retry/structure537_pilot_result.json');pair=prior['pairs'][0];assert not prior['passed'] and pair['both_safe']
 out=dict(selection='536savedHIGH exactlyequalsto steadyceiling and maxactualforce<.9, indices49..165 excludingprior25..48 window and40/166; longestconsecutiveeligible run, tieearliest, choosefirst. No537candidate result used.',new_normal_index=chosen,eligible_run_length=len(run),risk_roots=[40,166],normal_holds=24,reused_observed_root25_pair=pair,reuse_is_independent_evidence=False,old537_failure_preserved=True,source537_policy_sha256=sha(G/'retry/structure537_control.py'),pilot_roots_sha256=sha(D/'pilot-roots-private.json'),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,model_ticks=0)
 with (G/'retry/transfer538_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
