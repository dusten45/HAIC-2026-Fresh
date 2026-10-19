"""Read-only593 technical-stop audit and pure dataclass serialization regression."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import ast,hashlib,json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from retry.brake502_response import State
from retry.clip561_core import plain
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response593-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 r=read(G/'retry/cold593_result.json');c=read(G/'retry/cold593_contract.json');a=r['arms'][0];failure=read(D/'failure-baseline-private.json');n=Counter();head='0'*64;events=[]
 for seq,line in enumerate((D/'journal-private.jsonl').read_text().splitlines()):
  row=json.loads(line);h=row.pop('sha256');assert row['sequence']==seq and row['previous']==head and hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==h;head=h;n[row['kind']]+=1;events.append(row)
 tree=ast.parse((G/'retry/cold593_native.py').read_text());inputs={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INPUTS' for t in node.targets):
   for kw in node.value.keywords:inputs[kw.arg]=Path(kw.value.args[0].value) if isinstance(kw.value,ast.Call) else G/kw.value.right.value
 toy=State(velocity=(0.,0.),wheels=(),mass=1.,engine_multiplier=1.);observed=None
 try:plain(toy)
 except TypeError as exc:observed=str(exc)
 encoded=plain(asdict(toy));safe_json=json.loads(json.dumps(encoded,allow_nan=False))==encoded
 checks=dict(original_contract_registered=(D/'REGISTERED-private.json').exists() and read(D/'REGISTERED-private.json')['contract_sha256']==sha(G/'retry/cold593_contract.json'),native_started_marker=(D/'NATIVE_STARTED-private.json').exists(),original_code_dependency_pins=all(sha(Path(p) if Path(p).is_absolute() else G/p)==h for p,h in {**c['implementation_sha256'],**c['dependency_sha256']}.items()),all_input_pins=set(inputs)==set(c['input_sha256']) and all(sha(p)==c['input_sha256'][k] for k,p in inputs.items()),journal_exact=dict(n)==r['journal']['kinds'] and head==r['journal']['head'] and len(events)==r['journal']['events']==4,technical_stop=r['status']=='BASELINE_TECHNICAL_FAILURE_CANDIDATE_NOT_STARTED' and a['error']=='TypeError:UNSUPPORTED_JSON:State',root_cause_trace='before_state=plain(before)' in failure['traceback'] and 'UNSUPPORTED_JSON:State' in failure['traceback'],pure_regression=observed=='UNSUPPORTED_JSON:State' and safe_json,no_raw_call_or_kernel=n['BEFORE_NATIVE_RAW']==n['AFTER_NATIVE_RAW']==n['BEFORE_NATIVE_ORACLE']==n['BEFORE_MODEL_FORCE']==n['BEFORE_MODEL_TICK']==0 and r['cost'].get('raw_completed',0)==r['cost'].get('native_wheel_observed',0)==r['cost'].get('model_attempted',0)==r['cost'].get('model_completed',0)==r['cost'].get('external_force',0)==r['cost'].get('internal_force',0)==0,precharge_preserved=r['cost']['raw_attempts']==1 and r['cost']['native_wheel_reserved']==4 and r['cost']['worlds']==r['cost']['resets']==1,no_actions_or_candidate=r['cost'].get('actions',0)==0 and len(r['arms'])==1 and n['ACTION_CHARGED']==0,cleanup=a['cleanup']==dict(body=0,joint=0) and r['cost']['closed']==1,ledger_preserved=(r['research_remaining'],r['reserve'],r['reserve_used'])==(22758,84000,0),no_retry=len([q for q in events if q['kind']=='WORLD_CHARGED'])==1,combined_carry_closed=not r['combined_promotion'] and not r['general_policy_promotion'] and not read(G/'retry/carry592_result.json')['combined_source_gate'],no_claimed_performance=r['cold_native_gain_raw'] is None and r['cold_native_gain_s'] is None and a['official_finish_raw'] is None and not a['initial_identity'],protected_zero=all(r[k]==0 for k in ['carry_actions','new_conditions','HOLDOUT','SEALED','new_profiles','new_FD','new_solver','paid_compute']))
 out=dict(study=593,status='TECHNICAL_STOP_PRESERVED_READ_ONLY_AUDIT',checks=checks,cause='plain() rejects dataclass State; before_state must first be converted using asdict. Frozen failed runner was not edited or rerun.',recovery_allowed_in_this_run=False,recovery_reason='NATIVE_STARTED exists and world/reset began, so import-only zero-world exception does not apply.',source0_regression=dict(input='Synthetic State with zero velocity,emptywheels,mass1;no world/force/tick',observed_error=observed,asdict_then_plain_json_roundtrip=safe_json,proposed_serialization_change_only='before_state=plain(asdict(before))',applied_to_frozen_runner=False),operation_counts=dict(world_attempted=1,world_closed=1,reset_attempted=1,reset_completed=0,native_raw_precharged=1,native_raw_original_step_invocations=0,native_raw_completed=0,native_wheel_reserved=4,native_wheel_observed=0,env_step_attempts=0,model_attempted=0,model_completed=0,external_model_force=0,internal_model_force=0,geometry=0),new_audit_source_ticks=0,new_audit_native_calls=0,new_audit_force_calls=0,new_audit_geometry_queries=0,sha256=dict(result=sha(G/'retry/cold593_result.json'),contract=sha(G/'retry/cold593_contract.json'),journal_private=sha(D/'journal-private.jsonl'),failure_private=sha(D/'failure-baseline-private.json'),audit_code=sha(Path(__file__))))
 out['read_only_CPU_s']=time.process_time()-CPU;out['read_only_wall_s']=time.perf_counter()-WALL;out['auxiliary_CPU_wall_charge_s']=2.;out['aggregate_time']={k:v+out['read_only_CPU_s']+2 if 'CPU' in k and not k.startswith('science') else v+out['read_only_wall_s']+2 if 'wall' in k and not k.startswith('science') else v for k,v in r['time'].items()};checks['time_caps']=all(out['aggregate_time'][k]<cap for k,cap in dict(science_CPU_s=3000,science_wall_s=3300,preparation_audit_CPU_s=120,preparation_audit_wall_s=180,total_CPU_s=3120,total_wall_s=3480).items())
 with (G/'retry/cold593_closeout.json').open('x') as f:json.dump(out,f,indent=2)
 assert all(checks.values()),[k for k,v in checks.items() if not v];print(json.dumps(out,indent=2))
if __name__=='__main__':run()
