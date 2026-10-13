"""Fixed294 archive4+240; register12newTRAIN and4sealedDEV beforeperformance."""
import argparse,datetime
from pathlib import Path
from retry.path271_run import read,save,sha

def add_cases(ex,meta):
 mapping={'seed':'excluded_seeds','road_geometry_sha256':'excluded_road_geometry_sha256','obstacle_spec_sha256':'excluded_obstacle_spec_sha256','expected_physical_obstacles_sha256':'excluded_physical_obstacles_sha256','obstacle_rng_entropy':'excluded_obstacle_rng_entropy'}
 for case in meta['cases']:
  for src,key in mapping.items():
   if src in case and case[src] not in ex[key]:ex[key].append(case[src])
 if meta['family_entropy'] not in ex['excluded_parent_entropy_vectors']:ex['excluded_parent_entropy_vectors'].append(meta['family_entropy'])

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage295';assert not D.exists();D.mkdir(mode=0o700);prior=R/'project-effective-budget-v301.json';v=read(prior);assert v['research_remaining']==32564 and v['actual_cumulative_wrapper_actions']==1023436
 old=read(R/'stage294/plan.json');cp=read(R/'stage294/checkpoint.json');fixed=sorted([a for a in cp['archive'] if a['label']!='240'],key=lambda a:a['ordinal']);assert len(fixed)==4 and all(a['complete6'] and a['fully_observed'] for a in fixed);candidates=[dict(label='240',ordinal=0,theta=[0.]*6,config=old['base'],old_results=[dict(road=r,completed=True,actual_DNF=False,censored=False,technical_error=None,lap_ms=old['baseline'][r]['lap_ms']) for r in old['roads']])]
 for a in fixed:
  e=read(R/'stage294/policies'/a['label']/'evaluation.json');candidates.append(dict(label=a['label'],ordinal=a['ordinal'],theta=a['theta'],config=a['config'],old_results=e['results']))
 assert [c['label'] for c in candidates]==['240','g1p4','g2p1','g3p4','g4p7'];save(D/'fixed-candidates-private.json',candidates)
 ex=read(R/'stage294/exclusion-snapshot.json');add_cases(ex,read(R/'stage294/registration/split.json'));ex['stage']=295;template=read(R/'stage294/registration/selection-contract.json');selector=R/'stage125/prepare_selection.py';registrations=[];training=[];dev=[]
 for batch,role in [(0,'TRAIN'),(1,'TRAIN'),(2,'TRAIN'),(3,'DEV_SCREEN')]:
  F=D/'registration'/f'{role}-{batch}';F.mkdir(parents=True,mode=0o700);save(F/'exclusion-snapshot.json',ex);c=dict(template);c.update(stage=295,declared_split=role+'_295',authorization='295 unfiltered12newTRAIN+4distinctsealedDEV before new performance; fixed294fourcandidates+240 only',frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exclusion_snapshot_path=str(F/'exclusion-snapshot.json'),exclusion_snapshot_sha256=sha(F/'exclusion-snapshot.json'));save(F/'selection-contract.json',c);(F/'selection-contract.sha256').write_text(sha(F/'selection-contract.json')+'\n');(F/'selection-contract.sha256').chmod(0o600)
  s=selector.read_text();oldid='f\'holdout{contract["stage"]}-{index}\'';oldsplit='f\'HOLDOUT_{contract["stage"]}\'';assert s.count(oldid)==s.count(oldsplit)==1;s=s.replace(oldid,'f\''+role.lower()+'{contract["stage"]}-'+str(batch)+'-{index}\'').replace(oldsplit,'f\''+role+'_{contract["stage"]}\'');ns={'__name__':'identity295','__file__':str(selector)};exec(compile(s,str(selector),'exec'),ns);ns['register'](F/'selection-contract.json',F);m=read(F/'split.json');add_cases(ex,m);registrations.append(dict(role=role,batch=batch,path=str(F/'split.json'),sha256=sha(F/'split.json')))
  for case in m['cases']:
   dst=training if role=='TRAIN' else dev;dst.append(dict(case,public_label=('T295' if role=='TRAIN' else 'S295')+str(len(dst))))
 save(D/'exclusion-final.json',ex);save(D/'new-TRAIN-identities-private.json',training);save(D/'new-DEV-identities-private.json',dev);assert len(training)==12 and len(dev)==4;assert len(set(c['seed'] for c in training+dev))==16;assert len(set(c['road_geometry_sha256'] for c in training+dev))==16
 sources=[G/'retry'/n for n in ['diversity295_prepare.py','diversity295_run.py','cem294_episode.py','cem294_search.py','preview286_worker.py']]+[prior,D/'fixed-candidates-private.json',D/'new-TRAIN-identities-private.json',D/'new-DEV-identities-private.json']+[Path(c['config']['archive_path']) for c in candidates]
 p=dict(stage=295,deadline_utc='2026-10-16T10:01:55+00:00',candidates=candidates,candidate_order=[c['label'] for c in candidates],old_TRAIN_roads=old['roads'],new_TRAIN=training,fresh_DEV=dev,registrations=registrations,sandbox_path=old['sandbox_path'],training_cap=24000,evaluation_cap=8000,research_available=32564,no_parameter_draw=True,no_294_DEV_reuse=True,selection='Requireall60newTRAIN outcomes andcached6TRAIN perpolicy; preserve every240 completedroad; additionalcompletions first; samecompletioncount rankequallyweightedcommoncomplete roads among topcount candidates; thenlogparamnorm andoriginalordinal',DEV_gate='Onlystrictlybetter eligiblewinner over240, frozenonce;4freshAB/BA; preservebaseline completions andimprovecommonmean; no retune or alternatecandidate',hashes={str(q):sha(q) for q in sources});save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,training=0,evaluation=0));save(D/'screen-seal.json',dict(registered_before_TRAIN_performance=True,new_TRAIN_count=12,separate_fresh_DEV_count=4,opened_for_performance=False,no_294_DEV_reuse=True,registrations=registrations));print('295 fixed5policies;12newTRAIN+4sealedDEV registered; caps24000+8000, R32564',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
