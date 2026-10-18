"""Pin fixed549 profile and reuse identity-verified541 whole-model records."""
import datetime,hashlib,json,time
from pathlib import Path
from retry.structure537_control import choose
from retry.launch540_control import tracking_choose
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response551-private')
def run():
 cpu=time.process_time();wall=time.perf_counter();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();D.mkdir(mode=0o700,exist_ok=False);prior=read(G/'retry/joint541_contract.json');old=Path('/workspace/haic-response541-private');paths=read(Path('/workspace/haic-response549-private/frozen-paths-private.json'));baseline=read(old/'frozen-paths-private.json');ledger=read(Path('/workspace/haic-response519-private/model-ledger-private.json'));checks=dict(source_pins=all(sha(G/p)==h for p,h in prior['source_sha256'].items()),input_pins=all(sha(Path(p))==h for p,h in prior['private_inputs_sha256'].items()),same_tracking_function=choose is tracking_choose,baseline_profile_exact=paths['baseline']==baseline['candidate'],backup_exact=paths['backup']==baseline['backup'],candidate549_frozen_sha=sha(Path('/workspace/haic-response549-private/frozen-paths-private.json'))==read(G/'retry/retime549_design_result.json')['frozen_paths_sha256'],legacy_carry_completed46=ledger['completed_actions']==46,prior541_audit_passed=read(G/'retry/joint541_audit.json')['status']=='SAVED_RECORD_AUDIT_PASS');cases={};pins={}
 for kind,first in [('cold',1),('carry',47)]:
  p=old/(kind+'-candidate-private.json');data=read(p);r=read(G/('retry/joint541_'+kind+'_result.json'));checks[kind+'_summary_exact']=data['summary']==r['case'];checks[kind+'_first_action']=data['commands'][0]['index']==first;checks[kind+'_source_finish']=r['passed'] and r['case']['pass_safety'] and r['case']['stop']=='MODEL_SOURCE_STYLE_FINISH';checks[kind+'_unchanged_global_limits']=r['case']['min_margin_m']>=.5 and r['case']['force_groups']['running']['peak']<=1.059 and r['case']['max_reference_overspeed_m_s']<=4.85 and r['case']['max_body_speed_m_s']<100 and r['case']['max_cumulative_clipping_fraction']<=.1;cases[kind]=dict(source_finish_s=r['case']['model_finish_episode_s'],raw_ticks=len(data['trace']),saved_actions=len(data['commands']),model_ticks_reused=r['model_integrator_ticks'],recomputed_model_ticks=0);pins[str(p)]=sha(p)
 assert all(checks.values());p=D/'frozen-paths-private.json'
 with p.open('xb') as f:f.write(Path('/workspace/haic-response549-private/frozen-paths-private.json').read_bytes())
 p.chmod(0o600);out=dict(passed=True,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,baseline_reuse=cases,baseline_private_record_sha256=pins,frozen_paths_sha256=sha(p),new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/whole551_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
