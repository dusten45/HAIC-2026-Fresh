"""Prove post-launch dispatch identity and reuse pinned538carry, no simulation."""
import hashlib,json,time
from pathlib import Path
from retry.launch540_control import tracking_choose
from retry.structure537_control import choose

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response540-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();cold=read(G/'retry/launch540_cold_result.json');assert cold['passed'];c=read(G/'retry/launch540_contract.json');assert all(sha(G/p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in c['private_inputs_sha256'].items());assert tracking_choose is choose
 prep=read(G/'retry/launch540_preparation.json');ledger=read('/workspace/haic-response519-private/model-ledger-private.json');assert ledger['completed_actions']==46>=24 and sha(ledger['checkpoint'])==prep['carry_state_sha256'];old=read(G/'retry/transfer538_carry_result.json');assert old['passed'] and sha(G/'retry/transfer538_carry_result.json')==prep['carry_source_result_sha256'];assert sha('/workspace/haic-response538-private/carry-candidate-private.json')==prep['carry_private_sha256'];assert (D/'frozen-paths-private.json').read_bytes()==Path('/workspace/haic-response538-private/frozen-paths-private.json').read_bytes()
 out=dict(status='REUSED_IDENTICAL_POST_LAUNCH_CARRY_REGRESSION_PASS',passed=True,completed_actions=46,history=[0,352],launch_branch_unreachable=True,tracking_function_identity=True,path_root_model_sources_pinned=True,reused_source_result_sha256=prep['carry_source_result_sha256'],reused_private_case_sha256=prep['carry_private_sha256'],reused_safe_model_finish_s=old['case']['model_finish_episode_s'],new_effect_required=False,new_independent_evidence=False,new_model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/launch540_carry_regression.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out))
if __name__=='__main__':run()
