"""Freeze unit-gain GTyaw feedback, twoTRAIN roads, no gain/smoothing search."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage284';assert not D.exists();D.mkdir(mode=0o700);old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/outcome281_worker.py'),worker_sha256=sha(G/'retry/outcome281_worker.py'))
 p=dict(stage=284,cases={r:old['roads'][r] for r in ['O0','N0']},baseline_lap_ms=dict(O0=23660,N0=23620),base=base,sandbox_path=old['sandbox_path'],formula='k_command=tan(final240steer)/3.24; k_error=k_command-(-hull.angularVelocity)/currentHUDfeedbackspeed; returnedsteer=clip(atan(3.24*(k_command+k_error)),-.4,.4)',unit_gain=1,wheelbase_m=3.24,gain_is_fixed_diagnostic_not_source_optimal=True,fallback='No target/forward<=0/v<=0/nonfinite => exact240',extra_GT_control='angularVelocity only; lateral velocity logged but never in command',pedals='Exact same-call final240 gas/brake, base.act once; commit actualsteer with establishedprecision rule',native_cap=4000,per_run_max=2000,deadline_utc='2026-10-16T10:01:55+00:00',no_learning=True,no_model_physics=True,no_baseline_replay=True,no_promotion=True)
 sources=[G/'retry/yaw284_prepare.py',G/'retry/yaw284_run.py',G/'retry/outcome281_worker.py',G/'core/vendor/car_dynamics.py',Path(base['archive_path']),R/'project-effective-budget-v289.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));print('284 fixed GTyaw unitgain, O0/N0 once, cap4000',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
