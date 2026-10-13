"""Freeze wholepixelpath preview steering, sourcekinematic dimensions, no sweep."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage293';assert not D.exists();D.mkdir(mode=0o700);old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/preview286_worker.py'),worker_sha256=sha(G/'retry/preview286_worker.py'))
 p=dict(stage=293,hypothesis='Memoryless learned pedals may leave persistent speed error against nominal goal; integral gas feedback tests that mismatch',candidate='IntegralGas: I+=.08*.08*(feature6-feature4), gas=clip(basegas+I,0,1); I bounded[-1,1]; conditional antiwindup at gas bounds; missingtarget resetsI; steering/brake/path/head unchanged',differences='One new longitudinal error memory, no scaling sweep, PPO, selector, yaw/traction/preview objective or pixel refit',pilot=['O0','N0'],extension_if_pass=['O2','N1','N2','N3'],gate='Bothpilot complete and eachstrictly faster than cached240; failure stops, no coefficientchange',pilot_per_road_cap=1000,extension_per_road_cap=917,total_native_cap=5668,research_available=5669,cases=old['roads'],baseline_lap_ms={r:old['references'][r]['lap_ms'] for r in old['roads']},base=base,sandbox_path=old['sandbox_path'],deadline_utc='2026-10-16T10:01:55+00:00',GT_control=False,baseline_replay=False,no_learning=True,no_HOLDOUT_SEALED=True,no_reserve=True,no_promotion=True)
 sources=[G/'retry/integral293_prepare.py',G/'retry/integral293_run.py',G/'retry/integral293_control.py',G/'retry/preview286_worker.py',Path(base['archive_path']),R/'project-effective-budget-v298.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));print('293 fixed integral gas; pilot2x1000, extension4x917, total5668',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
