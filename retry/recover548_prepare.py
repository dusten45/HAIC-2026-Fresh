"""Freeze exact reusable547 evaluations/Jacobian and precharge original work."""
from pathlib import Path
import hashlib,json,datetime,time

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response547-private');O=Path('/workspace/haic-response548-private');O.mkdir(mode=0o700,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for name in ('entry-private.json','gate-private.json','frozen-paths-private.json','fresh-feasible541-baseline-private.json','prior546-local-model-private.json','prior546-direction-check-private.json','prior546-warmstart-private.json'):
  p=O/name
  with p.open('xb') as f:f.write((D/name).read_bytes())
  p.chmod(0o600)
 records=[]
 for p in sorted(D.glob('pointwise-*-private.json')):
  q=json.loads(p.read_text());records.append(dict(path=str(p),sha256=sha(p),rollout=q['summary']['rollout']))
 assert len(records)==20
 manifest=dict(prior_pointwise=records,prior_first_model=dict(path=str(D/'local-model-0-private.json'),sha256=sha(D/'local-model-0-private.json')),prior_547_result=dict(path=str(G/'retry/filter547_pilot_result.json'),sha256=sha(G/'retry/filter547_pilot_result.json')))
 with (O/'reuse-manifest-private.json').open('x') as f:json.dump(manifest,f,indent=2)
 prior=json.loads((G/'retry/filter547_pilot_result.json').read_text());out=dict(status='FROZEN548_NO_NEW_PHYSICS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original547preserved=True,prior_core_windows=20,prior_model_ticks=prior['model_integrator_ticks'],prior_CPU_s=prior['CPU_s'],original_safety_and_terminal_limits_unchanged=True,reusable_pointwise_records=20,remaining_core_windows=44,remaining_model_ticks=46000-prior['model_integrator_ticks'],remaining_CPU_s=900-prior['CPU_s'],source_propagation_functions_unchanged=True,private_inputs_sha256={str(p):sha(p) for p in O.glob('*private.json')},prior_cache_sha256={r['path']:r['sha256'] for r in records},new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/recover548_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
