"""Whole fixed60run diversity comparison, frozen18road winner, single4DEV."""
import argparse,time,json,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.cem294_search import episode_jobs

def entry(D,p,case,c,phase):
 theta=c['theta'];F=D/('TRAIN' if phase=='training' else 'DEV')/case['public_label']/c['label'];return dict(folder=str(F),road=case['public_label'],case=case,config=c['config'],ceiling=float(45*np.exp(theta[5])),steering_gain=float(np.exp(theta[2])))

def select(p,records):
 cs=p['candidates'];labels=p['candidate_order'];roads=p['old_TRAIN_roads']+[c['public_label'] for c in p['new_TRAIN']];sets={};metrics={};allby={}
 for c in cs:
  rr={x['road']:x for x in c['old_results']};rr.update({x['road']:x for x in records if x['candidate']==c['label']});assert set(rr)==set(roads);assert all(not x['technical_error'] and not x['censored'] for x in rr.values());allby[c['label']]=rr;sets[c['label']]={r for r,x in rr.items() if x['completed']}
 base=sets['240'];eligible=[c for c in cs if base<=sets[c['label']]];maxcount=max(len(sets[c['label']]) for c in eligible);top=[c for c in eligible if len(sets[c['label']])==maxcount];common=set.intersection(*(sets[c['label']] for c in top));assert common
 def ranking(c):return (float(np.mean([allby[c['label']][r]['lap_ms'] for r in sorted(common)])),float(np.linalg.norm(c['theta'])),c['ordinal'])
 winner=min(top,key=ranking);wl=winner['label'];paired=base&sets[wl];delta=float(np.mean([allby[wl][r]['lap_ms']-allby['240'][r]['lap_ms'] for r in sorted(paired)]));strict=(len(sets[wl])>len(base)) or (sets[wl]==base and delta<0)
 for c in cs:
  label=c['label'];cc=base&sets[label];metrics[label]=dict(completions=len(sets[label]),baseline_completions_preserved=base<=sets[label],baseline_completion_losses=sorted(base-sets[label]),additional_completions=sorted(sets[label]-base),common_baseline_completions=len(cc),common_baseline_mean_delta_ms=float(np.mean([allby[label][r]['lap_ms']-allby['240'][r]['lap_ms'] for r in sorted(cc)])) if cc else None,eligible=c in eligible)
 return dict(winner=winner,strict_improvement_over240=bool(strict),baseline_completions=len(base),metrics=metrics,common_selection_roads=sorted(common),equal_topcount_completion_sets=all(sets[c['label']]==sets[top[0]['label']] for c in top),completion_first=True)

def run(R):
 D=R/'stage295';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 if not (D/'opening.json').exists():save(D/'opening.json',dict(epoch=time.time(),TRAIN_cap=24000,DEV_cap=8000))
 records=[];technical=None;dev=[];selection=None
 try:
  for case in p['new_TRAIN']:
   for offset in range(0,5,2):
    candidates=p['candidates'][offset:offset+2];jobs=[entry(D,p,case,c,'training') for c in candidates];rr=episode_jobs(D,p,jobs,'training')
    for c,x in zip(candidates,rr):records.append(dict(x,candidate=c['label']))
    save(D/'TRAIN-records-private.json',records)
    if len(rr)<len(candidates) or any(x['censored'] for x in rr):raise RuntimeError('TRAINbudget censor or unexecuted jobs; no incomplete selection')
   closed=[x for x in records if x['road']==case['public_label']];print(json.dumps(dict(road=case['public_label'],results=[{k:x.get(k) for k in ['candidate','completed','actual_DNF','censored','technical_error','lap_ms']} for x in closed],native=read(D/'budget.json')['training'])),flush=True)
  if len(records)!=60 or any(x['technical_error'] or x['censored'] for x in records):raise RuntimeError('TRAINtechnicalunknown/incomplete; no forced selection/DEV')
  selection=select(p,records);save(D/'selection-private.json',selection);frozen=D/'winner-frozen.json'
  if not frozen.exists():save(frozen,dict(selection=selection,all60newTRAIN_outcomes_verified=True,frozen_epoch=time.time(),DEV_used_for_selection=False))
  assert read(frozen)['selection']==selection
  if selection['strict_improvement_over240']:
   save(D/'screen-opening.json',dict(winner_sha256=sha(frozen),opened_epoch=time.time(),no_retune=True)) if not (D/'screen-opening.json').exists() else None
   for case in p['fresh_DEV']:
    pair=[]
    for arm in case['arm_order']:
     c=p['candidates'][0] if arm=='A' else selection['winner'];rr=episode_jobs(D,p,[entry(D,p,case,c,'evaluation')],'evaluation');pair += [dict(x,arm=arm,candidate=c['label']) for x in rr]
    dev.append(dict(road=case['public_label'],arm_order=case['arm_order'],results=pair));save(D/'DEV-records-private.json',dev);print(json.dumps(dict(DEVroad=case['public_label'],results=[{k:x.get(k) for k in ['arm','completed','actual_DNF','censored','technical_error','lap_ms']} for x in pair],native=read(D/'budget.json')['evaluation'])),flush=True)
    if len(pair)!=2 or any(x['censored'] or x['technical_error'] for x in pair):raise RuntimeError('DEVbudget/technicalunknown; no alternatewinner/replacement')
 except BaseException as e:technical=type(e).__name__+': '+str(e);print(technical,flush=True)
 save(D/'outcome-private.json',dict(stage=295,TRAIN=records,selection=selection,DEV=dev,technical_error=technical,training_fully_observed=len(records)==60 and not any(x['technical_error'] or x['censored'] for x in records),budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],champion_changed=False,no_294_DEV_reuse=True))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
