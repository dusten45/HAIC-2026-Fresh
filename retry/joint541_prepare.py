"""Freeze the sole specified combination; no controller or physics calls."""
import hashlib,json,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');D.mkdir(mode=0o700,exist_ok=False);read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();launch=read(G/'retry/launch540_contract.json');cap=read(G/'retry/profile539_contract.json')
 assert sha(G/'retry/launch540_control.py')==launch['source_sha256']['retry/launch540_control.py'];assert sha(G/'retry/profile539_profile.py')==cap['source_sha256']['retry/profile539_profile.py']
 S=Path('/workspace/haic-response539-private')
 for name in ('frozen-paths-private.json','approved-case-private.json'):
  with (D/name).open('xb') as f:f.write((S/name).read_bytes())
  (D/name).chmod(0o600)
 old=read('/workspace/haic-response538-private/frozen-paths-private.json');new=read(D/'frozen-paths-private.json');assert old['candidate']==new['baseline'];assert all(old['candidate'][k]==new['candidate'][k] for k in ('points','arcs','ds','curvature','length'));assert old['backup']==new['backup']
 # A predeclared fixed80hold window covers launch, firstcorner, and prior538 longesttop80run53..73.
 b=read('/workspace/haic-response538-private/cold-candidate-private.json');milestone=next(r['progress'] for r in reversed(b['trace']) if r['index']==73)
 with (D/'pilot-coverage-private.json').open('x') as f:json.dump({'fixed_holds':80,'must_reach_baseline73_station':milestone},f)
 assert not (G/'retry/profile539_carry_result.json').exists()
 out=dict(candidate='Exactly540source-launch+539primarycap90; other538geometry/tracking/steering/backup/safety unchanged. No new parameter or sweep.',component_sha256={'launch540_control':sha(G/'retry/launch540_control.py'),'profile539_profile':sha(G/'retry/profile539_profile.py'),'tracking537_control':sha(G/'retry/structure537_control.py')},frozen_paths_sha256=sha(D/'frozen-paths-private.json'),case_sha256=sha(D/'approved-case-private.json'),pilot='Onefreshresetmodel80holds throughnewlaunch/firstcorner/highspeed. Allsafety/body<100 andcoveragepastbaseline538action73; no local500ms proxy. Saved538first80prefix reusedfor descriptive comparison only.',carry='539carrywasNOTobserved. New541carry fromsamelegacybefore47/history0,352 usescap90 andunchangedtracking; launchbranchunreachable. Verifyidentitywith539cap90function/inputs. Requirewhole safety/finish and nonworsening vs538carry14.70; no500mscarryeffectgate,no539cold240msimputation.',known_component_cold_results_s={'cap539':13.98,'launch540':13.90},component_results_not_added_to_predict_joint_gain=True,new_model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/joint541_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
