"""One predeclared friction-circle traction candidate, pairedTRAIN pilot gate."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage285';assert not D.exists();D.mkdir(mode=0o700);old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/outcome281_worker.py'),worker_sha256=sha(G/'retry/outcome281_worker.py'))
 p=dict(stage=285,hypothesis='Excess rear wheelspin consumes source shared longitudinal/lateral friction budget; firsttick gas inverse may preserve traction and pixel steering',fixed_method='Largestgas<=final240gas under eachrear wheel firsttick positive longitudinal friction-circle remainder, usecommonmin; preserve steering/brake; no gain/smoothing/search',scope='GT wheel dynamics diagnostic, not legalparticipant',pilot=['O0','N0'],extension_if_pass=['O2','N1','N2','N3'],gate='Both pilot roads officiallycomplete and each lap strictlysmaller than cached240; otherwise stop thisfixedcandidate, no retuning',pilot_native_cap=4000,whole_stage_native_cap=12000,per_road_cap=2000,research_available=31508,cases=old['roads'],baseline_lap_ms={r:old['references'][r]['lap_ms'] for r in old['roads']},base=base,sandbox_path=old['sandbox_path'],deadline_utc='2026-10-16T10:01:55+00:00',no_baseline_replay=True,no_training=True,no_model_physics=True,no_DEV_HOLDOUT_SEALED=True,no_reserve=True,no_promotion=True)
 sources=[G/'retry/traction285_prepare.py',G/'retry/traction285_control.py',G/'retry/traction285_run.py',G/'retry/outcome281_worker.py',G/'core/vendor/car_dynamics.py',Path(base['archive_path']),R/'project-effective-budget-v290.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));print('285 tractionfirsttick inverse frozen; pilotO0/N0 bothstrictgain gate',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
