"""One fixed AB/BA pair on each12DEV; countfirst judgment afterall24only."""
import argparse,time,json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.cem294_search import episode_jobs

def judge(pairs):
 assert len(pairs)==12
 base=sum(x['A']['completed'] for x in pairs);cand=sum(x['B']['completed'] for x in pairs);common=[x for x in pairs if x['A']['completed'] and x['B']['completed']];delta=float(np.mean([x['B']['lap_ms']-x['A']['lap_ms'] for x in common])) if common else None;win=cand>base or (cand==base and delta is not None and delta<0)
 return dict(base_completions=base,candidate_completions=cand,common_completions=len(common),common_mean_delta_ms=delta,paired_additional_completions=sum(not x['A']['completed'] and x['B']['completed'] for x in pairs),paired_lost_completions=sum(x['A']['completed'] and not x['B']['completed'] for x in pairs),winner='g1p4' if win else '240',candidate_outranks=bool(win),completion_count_primary=True)

def run(R):
 D=R/'stage296';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 if not (D/'opening.json').exists():save(D/'opening.json',dict(epoch=time.time(),judgment_fixed_before_results=True))
 records=[];error=None;judgment=None
 try:
  for case in p['cases']:
   pair={}
   for arm in case['arm_order']:
    c=p['candidates'][0] if arm=='A' else p['candidates'][1];t=c['theta'];F=D/'DEV'/case['public_label']/arm;entry=dict(folder=str(F),road=case['public_label'],case=case,config=c['config'],ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])));rr=episode_jobs(D,p,[entry],'evaluation')
    if rr:pair[arm]=rr[0]
   records.append(dict(road=case['public_label'],group=case['group'],arm_order=case['arm_order'],results=pair));save(D/'records-private.json',records);print(json.dumps(dict(road=case['public_label'],group=case['group'],results={a:{k:r.get(k) for k in ['completed','actual_DNF','censored','technical_error','lap_ms']} for a,r in pair.items()},native=read(D/'budget.json')['evaluation'])),flush=True)
   if set(pair)!=set(['A','B']) or any(r['censored'] or r['technical_error'] for r in pair.values()):raise RuntimeError('Incomplete/technical/budget pair; no DNF conversion or promotion')
  assert len(records)==12;judgment=judge([r['results'] for r in records]);save(D/'judgment-private.json',judgment)
 except BaseException as e:error=type(e).__name__+': '+str(e);print(error,flush=True)
 save(D/'outcome-private.json',dict(stage=296,records=records,judgment=judgment,technical_error=error,fully_observed=len(records)==12 and all(set(r['results'])=={'A','B'} and not any(x['technical_error'] or x['censored'] for x in r['results'].values()) for r in records),budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch']))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
