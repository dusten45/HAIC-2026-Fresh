"""Research grant and two source-only freshDEV registrations before training."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha

def prepare(R):
    from retry.dev243_register import register
    G=Path(__file__).resolve().parent.parent;D=R/'stage276';D.mkdir(mode=0o700);assert not (D/'training-plan.json').exists()
    prior=read(R/'project-effective-budget-v277.json');assert prior['B_operating_cap']==924000 and prior['actual_cumulative_wrapper_actions']==839085 and prior['research_remaining']==915
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    grant=dict(stage=276,at_utc=now,explicit_user_authorized_research_increment=70000,B_before=924000,B_after=994000,cumulative=839085,research_after=70915,reserve=84000,reserve_used=0,source='276delegated user authorization; no paidresources or automaticextension')
    save(D/'budget-extension.json',grant)
    budget=dict(prior);budget.update(version=278,at_utc=now,prior_budget_path=str(R/'project-effective-budget-v277.json'),prior_budget_sha256=sha(R/'project-effective-budget-v277.json'),B_operating_cap=994000,B_increment=70000,research_remaining=70915,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'),budget_reason='Explicit276researchgrant70000:839085+70915+84000=994000; exact275recipe continuation only.')
    save(R/'project-effective-budget-v278.json',budget)
    # Reuse already composed identity exclusions; no protected outcomes opened.
    exclusions=read(R/'stage247/exclusion-snapshot.json');exclusions['stage']=276
    mapping={'seed':'excluded_seeds','road_geometry_sha256':'excluded_road_geometry_sha256','obstacle_spec_sha256':'excluded_obstacle_spec_sha256','expected_physical_obstacles_sha256':'excluded_physical_obstacles_sha256','obstacle_rng_entropy':'excluded_obstacle_rng_entropy'}
    for split in [R/'stage243/registration/split.json',R/'stage247/registration/split.json']:
        metadata=read(split)
        for case in metadata['cases']:
            for source,key in mapping.items():
                if source in case and case[source] not in exclusions[key]:exclusions[key].append(case[source])
        if metadata['family_entropy'] not in exclusions['excluded_parent_entropy_vectors']:exclusions['excluded_parent_entropy_vectors'].append(metadata['family_entropy'])
    exclusions['scope']='Existing247metadata exclusions plus243/247registeredDEVidentities. No protectedperformance/rawscene reads.'
    save(D/'exclusion-snapshot.json',exclusions)
    registration=D/'registration';registration.mkdir(mode=0o700)
    contract=read(R/'stage247/registration/selection-contract.json');contract.update(stage=276,frozen_at_utc=now,authorization='276two freshDEVscreen source-only registration before275checkpoint continuation; no screenperformance access until finalcheckpoint64.',exclusion_snapshot_path=str(D/'exclusion-snapshot.json'),exclusion_snapshot_sha256=sha(D/'exclusion-snapshot.json'),declared_split='DEV_SCREEN_276',prior_input_sha256={str(R/'stage247/exclusion-snapshot.json'):sha(R/'stage247/exclusion-snapshot.json')})
    save(registration/'selection-contract.json',contract);(registration/'selection-contract.sha256').write_text(sha(registration/'selection-contract.json')+'\n');(registration/'selection-contract.sha256').chmod(0o600)
    selector=R/'stage125/prepare_selection.py';register(selector,registration/'selection-contract.json',registration)
    save(D/'screen-seal.json',dict(registered_before_training=True,registration_sha256=sha(registration/'split.json'),opened_for_policy_evaluation=False,training_or_selection_use=False,split='DEV_SCREEN_276',new_screens=2))
    old=read(R/'stage275/plan.json');base=dict(old['base']);base['worker_sha256']=sha(Path(base['worker_path']))
    sources=[G/'retry'/n for n in ['ppo276_prepare.py','ppo276_train.py','ppo276_eval.py','ppo275_model.py','ppo275_worker.py','ppo275_build.py','frozen_composite_runtime.py','diagnose.py']]
    sources += [R/'stage275/checkpoint2.pt',R/'stage275/updates-private.json',R/'stage231/single-head.npz',Path(base['archive_path']),R/'project-effective-budget-v278.json']
    plan=dict(stage=276,deadline_utc='2026-10-16T10:01:55+00:00',native_cap=69988,planned_additional_training_native=63488,final_eval_cap=6500,initial_valid_samples=2048,target_total_valid_samples=65536,start_batch=3,last_batch=64,base=base,
        initial_checkpoint=str(R/'stage275/checkpoint2.pt'),initial_updates=str(R/'stage275/updates-private.json'),normalization=old['normalization'],cases=old['cases'],initial_observations=old['initial_observations'],
        sandbox_path=old['sandbox_path'],screen_registration=str(registration/'split.json'),screen_registration_sha256=sha(registration/'split.json'),hashes={str(q):sha(q) for q in sources},recipe=read(R/'stage275/followup-recipe-private.json')['recipe'],
        no_intermediate_model_selection=True,final_checkpoint_only=True,GT_policy_or_critic_inputs=False,screen_inputs_not_in_training_plan=True,
        stop='Technical/nonfinite/actionhistory/logprob errors,authorization or global69988native limit. ActualDNF is trainingdata. No native replay; durable completedsamples/checkpoints recover. No recipechange or intermediate screen.')
    save(D/'training-plan.json',plan);(D/'training-plan.sha256').write_text(sha(D/'training-plan.json')+'\n');(D/'training-plan.sha256').chmod(0o600)
    save(D/'budget.json',dict(actions=0,training=0,evaluation=0))
    print('276ready:registeredsealed2freshDEVscreens,native0;grant70000;continuecheckpoint2to64updates',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);prepare(a.parse_args().private_root.resolve())
