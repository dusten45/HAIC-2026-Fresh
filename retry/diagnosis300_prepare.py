"""Registerminimum4signalaugmentation runs; archive/log digests immutable."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage300';assert not D.exists();D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v307.json');assert v['research_remaining']==10506
 p295=read(R/'stage295/plan.json');p298=read(R/'stage298/plan.json');p299=read(R/'stage299/plan.json');roadset=['T2950','T2954','T2955','T29510','T29511'];stored=[]
 for road in roadset:
  for label,stage,folder in [('240',295,R/'stage295/TRAIN'/road/'240'),('296',295,R/'stage295/TRAIN'/road/'g1p4'),('298',298,R/'stage298/evaluations'/('screen' if road in p298['screen'] else 'extension')/'revert_steering'/road),('299',299,R/'stage299/evaluations/training/steering_log_midpoint'/road)]:
   assert (folder/'result.json').exists();stored.append(dict(road=road,policy=label,result=str(folder/'result.json'),trace=str(folder/'trace-private.jsonl')))
 chosen=[('T2950','240'),('T2950','296'),('T2954','296'),('T2954','298')];cfgs={'240':p295['candidates'][0]['config'],'296':p298['baseline296']['config'],'298':next(c for c in p298['candidates'] if c['label']=='revert_steering')['config'],'299':p299['candidate']['config']};runs=[]
 for road,label in chosen:
  item=next(s for s in stored if s['road']==road and s['policy']==label);cfg=dict(cfgs[label]);cfg.update(worker_path=str(G/'retry/diagnosis300_worker.py'),worker_sha256=sha(G/'retry/diagnosis300_worker.py'));runs.append(dict(label=road+'_'+label,road=road,policy=label,config=cfg,case=p298['cases'][road],old_trace=item['trace'],old_result=item['result']))
 sources=[G/'retry'/n for n in ['diagnosis300_prepare.py','diagnosis300_collect.py','diagnosis300_worker.py']]+[Path(x[k]) for x in stored for k in ['result','trace']]+[R/'project-effective-budget-v307.json']+[Path(c['archive_path']) for c in cfgs.values()]
 plan=dict(stage=300,deadline_utc='2026-10-16T10:01:55+00:00',missing_signals=['Storedtrace lacksGTposition/progress, fullpixelpath, wheeljoint/motor/contact. Cannot spatiallyalign orisolatelag vsroadpathsupport from features alone.'],stored=stored,runs=runs,native_cap=2500,max_new_official_runs=4,research_available=10506,sandbox_path=p295['sandbox_path'],signal_goal='T2950 matched240/296 failure contrast;T2954 matched296/298 commonloss contrast; all4neednewGTspatial/path/actuator signals, no outcome-only confirmation',signals='PRE/POST GTposition/velocity/arc,lateral; actualpixelpath/detectedobstacles; roadpolygon support; rawtickwheeljoint/motor/contacts; nativecollision/damage; noGT policyinput',alignment='Connectedadjacentsegment projection, signedarc decreasesonreverse; nearestfirstforwardarc5mbins/tolerance2.5m; no equal-timestep-as-equal-state',diagnostic_thresholds=dict(first_observable_lateral_divergence_m=1,arc_bin_m=5,arc_match_tolerance_m=2.5,first_roadcontact_loss_after_arc_m=20,actuator_lag_rad=.03),policy_code_changed=False,raw_step_observer_only=True,no_reconstruction_of_missing_old_positions=True,no_297DEV_HOLDOUT_SEALED=True,no_control_intervention=True,hashes={str(q):sha(q) for q in sources});save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));print('300newsignals exactly4runs/T2950pair+T2954pair, cap2500; originalarchives preserved',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
