"""Validate durable fixed-PI traces and charge actual native cost once."""
import argparse,json,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save
from retry.integral293_control import IntegralGas

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage293';p=read(D/'plan.json');o=read(D/'outcome-private.json');assert not (D/'cost.json').exists()
 for q,h in p['hashes'].items():assert sha(q)==h
 verified=0
 for result in o['results']:
  c=IntegralGas();rows=[json.loads(x) for x in (D/result['road']/'trace-journal-private.jsonl').read_text().splitlines()];assert len(rows)==result['native_actions']
  for row in rows:
   b=np.array(row['base'],np.float32);a,d=c.control(b,row['features']);assert np.array_equal(a,np.array(row['action'],np.float32));assert d==row['audit'];assert np.float32(row['memory']['previous_steer'])==a[0];verified+=1
  assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
 n=read(D/'budget.json')['actions'];assert n==sum(x['native_actions'] for x in o['results']);assert n<=p['total_native_cap']<=p['research_available']
 prior=R/'project-effective-budget-v298.json';v=read(prior)
 cost=dict(stage=293,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=n,new_source_physics_ticks=0,new_policy_training_native=0,new_paid_resources=0,raw_step_ticks=sum(x['raw_step_ticks'] for x in o['results']),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in o['results']),runner_wall_s=o['wall_s'],runner_CPU_s=o['CPU_s'],actor_CPU_s=sum(x['actor_CPU_s'] for x in o['results']),B_operating_cap=v['B_operating_cap'],actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+n,research_remaining=v['research_remaining']-n,final_reserved_actions=84000,final_reserve_used=0);save(D/'cost.json',cost)
 v.update(version=299,at_utc=cost['at_utc'],prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage293_new_wrapper_actions=n,budget_reason='293 fixed legal integral gas candidate paired TRAIN; actual native charged, no reserve/policy/physics model.');assert not (R/'project-effective-budget-v299.json').exists();save(R/'project-effective-budget-v299.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(x).get('stage')==293 for x in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 public=dict(stage=293,candidate=p['candidate'],differences=p['differences'],gate=p['gate'],total_native_cap=p['total_native_cap'],results=o['results'],technical_error=o['technical_error'],gate_passed=o['gate_passed'],extension_executed=len(o['results'])>2,unexecuted_roads=[r for r in p['extension_if_pass'] if r not in [x['road'] for x in o['results']]],legal_input_only=True,official_package_qualification=False,baseline_replay=False,verified_trace_actions=verified,cost=cost,decision='Reject this fixed integral gas candidate; no gain sweep or extension. No claim against integral control or the task in general.')
 # Evaluator process ids are private operational details.
 for x in public['results']:x['reaping']={k:x['reaping'][k] for k in ['process_reaped','actor_pids_absent','actor_count']}
 save(G/'retry/integral293_result.json',public);print(json.dumps(dict(results=[{k:r[k] for k in ['road','completed','actual_DNF','censored','lap_ms','lap_delta_ms','native_actions']} for r in o['results']],cost=cost,verified=verified),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
