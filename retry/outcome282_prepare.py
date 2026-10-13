"""Freeze24TRAIN boundaries, reuse16stage281 outcomes, collect80new interventions."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha
ROADS=['O0','O2','N0','N1','N2','N3'];MACROS=['gas_upper','brake_lower','steer_plus','steer_minus']
def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage282';assert not D.exists();D.mkdir(mode=0o700)
 prior=R/'project-effective-budget-v286.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==927800 and v['research_remaining']==6200
 save(D/'budget-extension.json',dict(stage=282,explicit_research_grant=46000,B_operating_cap=1064000,research_remaining=52200,reserve=84000));v.update(version=287,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=46000,B_operating_cap=1064000,research_remaining=52200,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'),budget_reason='Explicit282grant46000;80newactual outcomes,16reused;24states one fixedtree recipe+LORO, no new policy runs.');save(R/'project-effective-budget-v287.json',v)
 old=read(R/'stage251/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/outcome281_worker.py'),worker_sha256=sha(G/'retry/outcome281_worker.py'));anchors={};reused=[];total=0
 for road in ROADS:
  A=D/road;A.mkdir(mode=0o700);folder=R/'stage251/training'/road;m=read(folder/'materialized.json');n=m['native_actions'];qs=[min(map(int,m['snapshots']),key=lambda q:(abs(q-f*n),q)) for f in [.125,.25,.5,.75]];assert len(set(qs))==4;anchors[road]=qs
  oldqs=read(R/'stage281'/road/'plan.json')['anchors'] if road in ['N0','N2'] else []
  assert not oldqs or oldqs==qs[1:3]
  for q in oldqs:
   for macro in MACROS:
    receipt=R/'stage281'/road/(str(q)+'_'+macro)/'result.json';r=read(receipt);assert r['comparable'] and r['memory_history_verified'];reused.append(dict(road=road,anchor=q,macro=macro,result_path=str(receipt),sha256=sha(receipt)))
  jobs=[dict(anchor=q,macro=macro) for q in qs if q not in oldqs for macro in MACROS];total+=len(jobs)
  p=dict(stage=282,road=road,anchors=qs,anchor_fractions=[.125,.25,.5,.75],anchor_rule='Closest validquery to fraction*baselineactionlength, lowerquery wins ties, before outcomes',jobs=jobs,macros=['gas_upper','brake_lower','steer_plus','steer_minus'],macro_actions=3,base=base,scales=old['scales'],case=old['roads'][road],cache=str(folder/'cache-private.npz'),materialized=str(folder/'materialized.json'),baseline_lap_ms=old['references'][road]['lap_ms'],sandbox_path=old['sandbox_path'],deadline_utc='2026-10-16T10:01:55+00:00',shard_native_cap=len(jobs)*650,per_run_cap=650,no_classifier_during_collection=True,no_model_predictions=True,baseline_replayed=False)
  sources=[G/'retry/outcome282_prepare.py',G/'retry/outcome282_run.py',G/'retry/outcome282_tree.py',G/'retry/outcome281_worker.py',Path(base['archive_path']),folder/'cache-private.npz',folder/'materialized.json',R/'project-effective-budget-v287.json'];p['hashes']={str(q):sha(q) for q in sources};save(A/'plan.json',p);(A/'plan.sha256').write_text(sha(A/'plan.json')+'\n');(A/'plan.sha256').chmod(0o600);save(A/'budget.json',dict(actions=0,phases={}))
 assert total==80 and len(reused)==16
 save(D/'plan.json',dict(stage=282,anchors=anchors,new_runs=80,reused_runs=reused,total_outcomes=120,baseline_outcomes=24,new_native_cap=52000,per_run_cap=650,parallel_shards=ROADS,tree_recipe=dict(max_depth=2,min_samples_leaf=3,features=16,criterion='Gini',ties='classorderbaseline,gas_upper,brake_lower,steer_plus,steer_minus; featurethenascendingthreshold',seed='No RNG'),validation='6leave-one-road-out fits of same fixed recipe; one final24-state fit; no tuning',selection='Strict smaller official integer lap_ms among comparable completed outcomes; ties with baseline abstain; incomplete/incomparable/censored excluded from labels; preservealloutcomes',evaluation_scope='One intervention at existing snapshots, not repeated policy',stop='All registered runs unless deadline or technical failure; no automatic replay',no_promotion=True,TRAIN_only=True));print(str(anchors),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
