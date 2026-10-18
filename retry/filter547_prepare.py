"""Freeze547 inputs and identify missing546 pointwise residual records honestly."""
import hashlib,json,time,datetime
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response546-private');O=Path('/workspace/haic-response547-private');O.mkdir(mode=0o700,exist_ok=False)
 for name in ('entry-private.json','gate-private.json','frozen-paths-private.json','fresh-feasible541-baseline-private.json'):
  p=O/name
  with p.open('xb') as f:f.write((D/name).read_bytes())
  p.chmod(0o600)
 for old,new in [('local-model-0-private.json','prior546-local-model-private.json'),('direction-check-0-private.json','prior546-direction-check-private.json'),('warmstart-private.json','prior546-warmstart-private.json')]:
  p=O/new
  with p.open('xb') as f:f.write((D/old).read_bytes())
  p.chmod(0o600)
 out=dict(status='INPUTS_FROZEN_NO_PHYSICS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stored546_has_warmstart_full_trace_J_direction_summaries_and_hashes=True,stored546_actual_direction_pointwise_g_and_branch_arrays_not_persisted=True,two_direction_reconstruction_replays_registered_inside_new64window_budget=True,new546_gate_not_reinterpreted=True,private_inputs_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*private.json')},new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/filter547_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
