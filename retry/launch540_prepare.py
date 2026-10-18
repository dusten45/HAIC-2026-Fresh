"""Frozen baseline inputs; baseline data only, no launch policy evaluations."""
import json,hashlib,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response540-private');S=Path('/workspace/haic-response538-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 for name in ('frozen-paths-private.json','approved-case-private.json'):
  with (D/name).open('xb') as f:f.write((S/name).read_bytes())
  (D/name).chmod(0o600)
 static=read('/workspace/haic-response515-private/collected-map-state-private.json');ledger=read('/workspace/haic-response519-private/model-ledger-private.json');carry=read(G/'retry/transfer538_carry_result.json');assert carry['passed'] and ledger['completed_actions']==46
 out=dict(unchanged_path_sha256=sha(D/'frozen-paths-private.json'),case_sha256=sha(D/'approved-case-private.json'),pilot='Tworesetmodelprefixes48holds192raw each; baseline24gas.32then538tracking versuscandidate540launchthenidentical538tracking. Allsafety; launchendprogressgain>=5m/speed>=5m/s; 48holdendprogressgain>=1m. End24and48metrics includegasdelay; no80ms effectthreshold.',carry_regression='Samelegacyactual518before47 state/history0/352/visited means launch branch unreachable. Aftercoldgate verify dispatch directly references identical537tracking function and pinned path/root/model. Reuse538safe carry14.70 withfullsourcehashreceipt, not new gain/newindependentevidence; no duplicatewholecarrysimulation.',carry_source_result_sha256=sha(G/'retry/transfer538_carry_result.json'),carry_private_sha256=sha(S/'carry-candidate-private.json'),carry_state_sha256=sha(ledger['checkpoint']),baseline_actual_s=14.22,new_model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/launch540_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
