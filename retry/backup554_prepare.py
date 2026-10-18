"""Reuse exactly553 frozen segment and551 baseline, no source ticks."""
import hashlib,json,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response554-private')
def run():
 cpu=time.process_time();wall=time.perf_counter();S=Path('/workspace/haic-response553-private');D.mkdir(mode=0o700,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=json.loads((G/'retry/dynamic553_preparation.json').read_text())
 for name in ['entry-private.json','baseline-prefix-private.json','frozen-paths-private.json']:
  p=D/name
  with p.open('xb') as f:f.write((S/name).read_bytes())
  p.chmod(0o600)
 assert sha(D/'entry-private.json')==old['entry_sha256'] and sha(D/'baseline-prefix-private.json')==old['baseline_prefix_sha256'] and sha(D/'frozen-paths-private.json')==old['fixed_path_sha256'];out=dict(passed=True,same553_fixed_segment=True,same552root26=True,baseline551_performance_reused=True,baseline_gate=old['baseline_gate'],baseline_return=old['baseline_return'],entry_sha256=sha(D/'entry-private.json'),fixed_path_sha256=sha(D/'frozen-paths-private.json'),new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/backup554_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
