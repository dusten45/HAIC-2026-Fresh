"""Freeze categorical3action policy and2freshscreens before16update training."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha
from retry.macro290_model import RECIPE

def run(R):
 from retry.dev243_register import register
 G=Path(__file__).resolve().parent.parent;D=R/'stage290';assert not D.exists();D.mkdir(mode=0o700);prior=read(R/'project-effective-budget-v295.json');assert prior['research_remaining']==28449
 exclusions=read(R/'stage276/exclusion-snapshot.json');mapping={'seed':'excluded_seeds','road_geometry_sha256':'excluded_road_geometry_sha256','obstacle_spec_sha256':'excluded_obstacle_spec_sha256','expected_physical_obstacles_sha256':'excluded_physical_obstacles_sha256','obstacle_rng_entropy':'excluded_obstacle_rng_entropy'};metadata=read(R/'stage276/registration/split.json')
 for case in metadata['cases']:
  for source,key in mapping.items():
   if source in case and case[source] not in exclusions[key]:exclusions[key].append(case[source])
 if metadata['family_entropy'] not in exclusions['excluded_parent_entropy_vectors']:exclusions['excluded_parent_entropy_vectors'].append(metadata['family_entropy'])
 exclusions['stage']=290;save(D/'exclusion-snapshot.json',exclusions);reg=D/'registration';reg.mkdir(mode=0o700);contract=read(R/'stage276/registration/selection-contract.json');contract.update(stage=290,frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization='290twofreshDEVsourceonly beforetraining, no policy/performance lookup until frozencheckpoint16',declared_split='DEV_SCREEN_290',exclusion_snapshot_path=str(D/'exclusion-snapshot.json'),exclusion_snapshot_sha256=sha(D/'exclusion-snapshot.json'));save(reg/'selection-contract.json',contract);(reg/'selection-contract.sha256').write_text(sha(reg/'selection-contract.json')+'\n');(reg/'selection-contract.sha256').chmod(0o600);register(R/'stage125/prepare_selection.py',reg/'selection-contract.json',reg)
 save(D/'screen-seal.json',dict(registered_before_training=True,registration_sha256=sha(reg/'split.json'),opened_for_policy_evaluation=False,training_or_selection_use=False,new_screens=2))
 old=read(R/'stage275/plan.json');base=dict(old['base']);base.update(worker_path=str(G/'retry/outcome281_worker.py'),worker_sha256=sha(G/'retry/outcome281_worker.py'))
 names=['macro290_model.py','macro290_train.py','macro290_prepare.py','macro290_finalize.py','macro290_build.py','macro290_worker.py','macro290_eval.py','outcome281_worker.py'];sources=[G/'retry'/n for n in names]+[Path(base['archive_path']),Path(old['normalization']),R/'project-effective-budget-v295.json']
 plan=dict(stage=290,deadline_utc='2026-10-16T10:01:55+00:00',native_cap=22884,training_native_cap=16384,evaluation_native_cap=6500,recipe=dict(RECIPE,rollout_cut='Onlywholecompletedmacro boundary; remaining1/2native in1024windowunused; terminal may shortenmacro',technical_recovery='Atomiccheckpoint+completedmacrodecision journals, discardunfinishedmacro, chargedloss included; no native replay'),base=base,cases=old['cases'],initial_observations=old['initial_observations'],normalization=old['normalization'],sandbox_path=old['sandbox_path'],screen_registration=str(reg/'split.json'),screen_registration_sha256=sha(reg/'split.json'),hashes={str(q):sha(q) for q in sources},no_intermediate_model_selection=True,final_checkpoint=16,no_hyperparameter_changes=True,GT_policy_or_critic_inputs=False,training_road_count=6,screen_cases_not_in_training_plan=True)
 save(D/'training-plan.json',plan);(D/'training-plan.sha256').write_text(sha(D/'training-plan.json')+'\n');(D/'training-plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,training=0,evaluation=0));print('290ready:2screens sealed beforetrain;categoricalrecipe16updates, caps16384+6500',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
