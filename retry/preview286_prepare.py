"""Freeze wholepixelpath preview steering, sourcekinematic dimensions, no sweep."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage286';assert not D.exists();D.mkdir(mode=0o700);old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/preview286_worker.py'),worker_sha256=sha(G/'retry/preview286_worker.py'))
 p=dict(stage=286,hypothesis='One-lookahead circle discards currentpixel pathshape and upcomingsteering actuation; wholepath finitepreview may improve tracking/time',candidate='Legal HUDv,ownprevioussteer,current240pixelroute only; H<=8 and observedarc length; sourceL3.24,50steererror rateclipped3rad/s,dt.02;2GaussNewton updates; objectivepathpositionsquared+L^2steerrate squared; boundedsteer±.4; keepcurrent240pedals',differences='Not GTsourceworld macro ranking, no frozenfuturesteering teacher, no learnedselector, no twoframepath fusion, no gain/residual sweep',pilot=['O0','N0'],extension_if_pass=['O2','N1','N2','N3'],gate='Pilotbothcomplete and eachstrictlyfaster than cached240; no minimumgain; failure stopsfixedcandidate',pilot_native_cap=4000,extension_native_cap=8000,total_native_cap=12000,research_available=30903,cases=old['roads'],baseline_lap_ms={r:old['references'][r]['lap_ms'] for r in old['roads']},base=base,sandbox_path=old['sandbox_path'],deadline_utc='2026-10-16T10:01:55+00:00',GT_control=False,baseline_replay=False,no_learning=True,no_HOLDOUT_SEALED=True,no_reserve=True,no_promotion=True)
 sources=[G/'retry/preview286_prepare.py',G/'retry/preview286_run.py',G/'retry/preview286_control.py',G/'retry/preview286_worker.py',Path(base['archive_path']),R/'project-effective-budget-v291.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));print('286 fixedlegal wholepathpreview; pilotcap4000, gatedextension8000',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
