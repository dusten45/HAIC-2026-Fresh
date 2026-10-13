"""Freeze lambda-only pairedlearning from275checkpoint2; no new screen."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha

def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage278';D.mkdir(mode=0o700);assert not (D/'plan.json').exists()
    prior=read(R/'project-effective-budget-v280.json');assert prior['actual_cumulative_wrapper_actions']==904931 and prior['research_remaining']==5069
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();grant=dict(stage=278,at_utc=now,explicit_research_increment=15000,B_before=994000,B_after=1009000,cumulative=904931,research_after=20069,reserve=84000,reserve_used=0,source='278delegated user authorization')
    save(D/'budget-extension.json',grant);new=dict(prior);new.update(version=281,at_utc=now,prior_budget_path=str(R/'project-effective-budget-v280.json'),prior_budget_sha256=sha(R/'project-effective-budget-v280.json'),B_operating_cap=1009000,B_increment=15000,research_remaining=20069,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'),budget_reason='Explicit278researchgrant15000; two8kvalid PPO lambda arms;904931+20069+84000=1009000.')
    save(R/'project-effective-budget-v281.json',new)
    old=read(R/'stage275/plan.json');base=dict(old['base']);base['worker_sha256']=sha(Path(base['worker_path']))
    sources=[G/'retry'/n for n in ['ppo278_prepare.py','ppo278_train.py','ppo278_finalize.py','ppo278_eval.py','ppo275_model.py','ppo275_worker.py','ppo275_build.py','frozen_composite_runtime.py','diagnose.py']]
    sources += [R/'stage275/checkpoint2.pt',R/'stage275/updates-private.json',R/'stage231/single-head.npz',Path(base['archive_path']),R/'project-effective-budget-v281.json']
    hashes={str(q):sha(q) for q in sources};common=dict(stage=278,deadline_utc='2026-10-16T10:01:55+00:00',native_cap=9492,valid_new_samples=8192,new_updates=8,start_batch=3,last_batch=10,noise_seed=27801,shuffle_seed=27802,
        base=base,initial_checkpoint=str(R/'stage275/checkpoint2.pt'),initial_updates=str(R/'stage275/updates-private.json'),normalization=old['normalization'],cases=old['cases'],initial_observations=old['initial_observations'],sandbox_path=old['sandbox_path'],hashes=hashes,
        recipe='Exact275architecture/input/reward/bounds/1024rollout/4epoch/LR/clip/KL, onlyGAElambda differs. Fresh identicalnoise/shuffle seeds; checkpoint2actor/critic/Adam identical.',no_screen=True,
        cut_semantics='lambda1 cutoff uses prefixreward + criticbootstrap, not actualunobservedterminal MC.',stop='Technical/nonfinite/statehistory errors recovered without physics replay. ActualDNF is data. No recipe/modelselection.')
    arms={}
    for name,value in [('control',.95),('lambda1',1.)]:
        A=D/name;A.mkdir(mode=0o700);p=dict(common,arm=name,GAE_lambda=value);save(A/'training-plan.json',p);(A/'training-plan.sha256').write_text(sha(A/'training-plan.json')+'\n');(A/'training-plan.sha256').chmod(0o600);save(A/'budget.json',dict(actions=0,training=0,evaluation=0));arms[name]=str(A/'training-plan.json')
    plan=dict(stage=278,at_utc=now,arms=arms,total_native_cap=18984,planned_training_native=16384,evaluation_native_cap=2600,eval_roads=['N0','N2'],eval_per_case_cap=650,initial_checkpoint_sha256=sha(R/'stage275/checkpoint2.pt'),noise_seed=27801,shuffle_seed=27802,only_GAE_lambda_changed=True,
        seeds_fresh_common_not_276_replay=True,TRAIN_diagnostic_not_independent_confirmation=True,champion_change=False,history277_small_positive_gain_preserved=True,no_new_screen_HOLDOUT_SEALED=True)
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    print('278frozen:.95vs1.0, samecheckpoint2/freshseeds,8192valid+8updates each,18984totalcap',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);prepare(a.parse_args().private_root.resolve())
