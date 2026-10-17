"""Saved first-raw endpoint diagnostics only; no allocator or physics execution."""
import json,sys,time
from pathlib import Path
from retry.audit474_traces import NoPhysics,RUNS
from retry.audit475_forces import read,sha,put,G

def run(root):
 guard=NoPhysics();sys.meta_path.insert(0,guard)
 import numpy as np
 d=root/'stage475';put(root/'stage475-domain-recovery1-plan-private.json',dict(stage=475,source_sha256=sha(Path(__file__)),input_plan_sha256=sha(d/'plan.json'),scope='saved first wrapper raw q=0 endpoint only, no search, no action dispatch',new_physics=0,new_native=0))
 result={};records=[]
 for label,(rel,observer) in RUNS.items():
  model=observer is not None;rows=read(root/rel)['rows'] if model else [json.loads(s) for s in (root/rel).read_text().splitlines() if s]
  s=read(root/('stage473/world43-before-first-step-private.json' if label=='473_P4' else 'stage473/world42-before-first-step-private.json'))['model_root']['physical'] if model else read(root/rel.replace('trace-private.jsonl','initial-private.json'))['physical']
  prev=[w['dynamics']['omega'] for w in s['wheels']];rr=[]
  for wi,row in enumerate(rows,1):
   ts=row['tires'] if model else row['raw_tire_samples'];cmd=row['command']
   for k in range(1,len(row['raw_hull'])+1):
    group=[t for t in ts if t['raw_tick']==k]
    if k==1:
     wheels=[]
     for t in group:
      # q=0 gives gas0 and brake0 on either mutually-exclusive active branch.
      # Front gas invariant0 verified by reconstruction; no drive term is added.
      omega=prev[t['wheel']];long=(-t['forward_speed_m_s']+omega*.54)*(205000*.02*.02);lat=t['raw_lat_N'];ratio=float(np.sqrt(np.square(long)+np.square(lat))/t['friction_limit'])
      wheels.append(dict(wheel=t['wheel'],qzero_long_N=float(long),qzero_ratio=ratio,lat_alone_excess=abs(lat)>t['friction_limit'],qzero_long_alone_excess=bool(abs(long)>t['friction_limit']),qzero_long_lat_combined_only=bool(abs(long)<=t['friction_limit'] and abs(lat)<=t['friction_limit'] and ratio>1)))
     lateral=any(t['lat_alone_excess'] for t in wheels);front=cmd[1]>0 and cmd[2]==0 and any(t['wheel']<2 and t['clipped'] for t in group);zfail=any(t['qzero_ratio']>1 for t in wheels)
     q=dict(run=label,wrapper=wi,lateral_alone_proves_empty=lateral,pedal_invariant_front_proves_empty=front,qzero_fails=zfail,qzero_fails_without_known_empty_proof=zfail and not(lateral or front),qzero_feasible_witness=not zfail,full_empty_classification='PROVEN_EMPTY_LATERAL' if lateral else 'PROVEN_EMPTY_INVARIANT_FRONT' if front else 'NONEMPTY_QZERO_WITNESS' if not zfail else 'UNRESOLVED_QZERO_FAILURE_NOT_EMPTY_PROOF',wheels=wheels)
     rr.append(q);records.append(q)
    for t in group:
     ff=t['raw_long_N'];force=np.sqrt(np.square(ff)+np.square(t['raw_lat_N']))
     if force>t['friction_limit']:ff/=force;ff*=t['friction_limit']
     prev[t['wheel']]=t['omega']-.02*ff*.54/(4000*.02*.02)
  result[label]=dict(wrappers=len(rr),**{key:sum(bool(q[key]) for q in rr) for key in ['lateral_alone_proves_empty','pedal_invariant_front_proves_empty','qzero_fails','qzero_fails_without_known_empty_proof','qzero_feasible_witness']},categories={key:sum(q['full_empty_classification']==key for q in rr) for key in sorted({q['full_empty_classification'] for q in rr})})
 put(d/'domain-recovery1-private.json',dict(runs=result,records=records,new_physics=0,new_native=0,import_guard_attempts=guard.attempts));put(G/'retry/audit475_domain.json',dict(stage=475,runs=result,new_physics=0,new_native=0,exactness='conditional on saved vf/vs/limit and preceding saved reaction identity; not independently regenerated state',qzero_failure_is_not_empty_proof=True,allocator_search_executed=False));print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
