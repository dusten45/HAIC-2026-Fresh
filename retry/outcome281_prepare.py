"""Freeze four TRAIN boundaries and four fixed3action macros before outcomes."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage281';assert not D.exists();D.mkdir(mode=0o700)
 prior=R/'project-effective-budget-v284.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==923208 and v['research_remaining']==1792
 extension=dict(stage=281,explicit_grant=9000,B_operating_cap=1018000,research_remaining=10792,reserve=84000);save(D/'budget-extension.json',extension)
 v.update(version=285,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),B_increment=9000,B_operating_cap=1018000,research_remaining=10792,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'),budget_reason='Explicit281 grant9000; four boundaries/four actual3-action macro outcomes, max10400native, no learning.')
 save(R/'project-effective-budget-v285.json',v)
 old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/outcome281_worker.py'),worker_sha256=sha(G/'retry/outcome281_worker.py'));anchors={}
 for road in ['N0','N2']:
  A=D/road;A.mkdir(mode=0o700);folder=R/'stage251/training'/road;m=read(folder/'materialized.json');n=m['native_actions'];qs=[min(map(int,m['snapshots']),key=lambda q:(abs(q-f*n),q)) for f in [.25,.5]];anchors[road]=qs
  p=dict(stage=281,road=road,anchors=qs,anchor_rule='Closest valid stored pre-action query to25%/50% baseline action length; lower boundary wins ties; frozen before outcomes',jobs=[dict(anchor=q,macro=macro) for q in qs for macro in ['gas_upper','brake_lower','steer_plus','steer_minus']],macros=dict(gas_upper='clip(clip(current_nominal_gas+.5,0,1)*fixed240gas_scale,0,1)',brake_lower='clip(clip(current_nominal_brake-.5,0,1)*fixed240brake_scale,0,1)',steer_plus='clip(current240steer+.015,-.4,.4)',steer_minus='clip(current240steer-.015,-.4,.4)'),macro_actions=3,base=base,scales=old['scales'],case=old['roads'][road],cache=str(folder/'cache-private.npz'),materialized=str(folder/'materialized.json'),baseline_lap_ms=old['references'][road]['lap_ms'],sandbox_path=old['sandbox_path'],deadline_utc='2026-10-16T10:01:55+00:00',shard_native_cap=5200,per_run_cap=650,no_model_predictions=True,no_classifier=True,baseline_replayed=False)
  sources=[G/'retry/outcome281_prepare.py',G/'retry/outcome281_worker.py',G/'retry/outcome281_run.py',Path(base['archive_path']),folder/'cache-private.npz',folder/'materialized.json',R/'project-effective-budget-v285.json'];p['hashes']={str(q):sha(q) for q in sources};save(A/'plan.json',p);(A/'plan.sha256').write_text(sha(A/'plan.json')+'\n');(A/'plan.sha256').chmod(0o600);save(A/'budget.json',dict(actions=0,phases={}))
 save(D/'plan.json',dict(stage=281,anchors=anchors,total_jobs=16,native_cap=10400,per_run_cap=650,research_grant=9000,parallel_shards='N0/N2 separate5200 caps; no shared budget writes',no_promotion=True,TRAIN_only=True));print(str(anchors),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
