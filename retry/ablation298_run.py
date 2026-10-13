"""Sixonecoordinate screen; freezeonecandidate, extend15, eligible12DEV only."""
import argparse,time,json,os,subprocess,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose,key
from retry.reliability296_run import judge

def jobs(D,p,entries,phase):
 remaining=p['phase_caps'][phase]-read(D/'budget.json')[phase];out=[];pending=[]
 if len(entries)>1 and remaining<2000*len(entries):
  for e in entries:
   rr=jobs(D,p,[e],phase);out+=rr
   if not rr or any(r['censored'] or r['technical_error'] for r in rr):break
  return out
 for e in entries:
  F=Path(e['folder'])
  if (F/'result.json').exists():out.append(read(F/'result.json'));continue
  if F.exists():raise RuntimeError('Incompleteepisode preserved; no automaticnative replay:'+str(F))
  cap=min(2000,remaining);remaining-=cap
  if cap<=0:break
  F.mkdir(parents=True,mode=0o700);save(F/'job.json',dict(private_stage=str(D),phase=phase,native_cap=cap,**{k:v for k,v in e.items() if k!='folder'}));log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600);proc=subprocess.Popen([sys.executable,'-m','retry.ablation298_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'));pending.append((F,proc,log))
 for F,proc,log in pending:
  rc=proc.wait();log.close();assert (F/'result.json').exists(),f'Childexit{rc}:no endpoint';out.append(read(F/'result.json'))
 return out

def evaluate(D,p,c,roads,phase):
 F=D/'evaluations'/phase/c['label'];F.mkdir(parents=True,exist_ok=True,mode=0o700);cached={}
 for a in read(D/'TRAIN-cache-private.json'):
  if key(a['theta'])==key(c['theta']):cached.update({r['road']:r for r in a['results']})
 rr=[];reused=0
 for i in range(0,len(roads),2):
  batch=roads[i:i+2];entries=[dict(folder=str(F/r),road=r,case=p['cases'][r],config=c['config'],initial_observation_sha256=p['initial_observations'].get(r),ceiling=float(45*np.exp(c['theta'][5])),steering_gain=float(np.exp(c['theta'][2]))) for r in batch if r not in cached];fresh=jobs(D,p,entries,phase) if entries else [];mapped={r['road']:r for r in fresh}
  for r in batch:
   if r in cached:rr.append(cached[r]);reused+=1
   elif r in mapped:rr.append(mapped[r])
  save(F/'partial.json',rr)
  if len(fresh)<len(entries) or any(r['censored'] for r in fresh):break
 complete=len(rr)==len(roads) and not any(r['technical_error'] or r['censored'] for r in rr);baseline=[r for r in p['baseline296']['results'] if r['road'] in roads];e=dict(label=c['label'],results=rr,fully_observed=complete,reused_roads=reused,unexecuted=[r for r in roads if not any(x['road']==r for x in rr)],**metrics(rr),against296=diagnose(rr,baseline) if complete else None);save(F/'evaluation.json',e);return e

def rank_screen(a):return (-a['completions'],a['own_complete_mean_ms'] if a['own_complete_mean_ms'] is not None else float('inf'),0 if a['label']=='296' else 1,a['ordinal'])
def run(R):
 D=R/'stage298';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 if not (D/'opening.json').exists():save(D/'opening.json',dict(epoch=time.time()))
 screen=[];selected=None;full=None;dev=[];judgment=None;error=None;eligible=False
 try:
  base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']];screen=[dict(p['candidates'][0],**metrics(base),results=base,fully_observed=True,cached=True)]
  for c in p['candidates'][1:]:
   e=evaluate(D,p,c,p['screen'],'screen');screen.append(dict(c,**{k:e[k] for k in ['results','fully_observed','completions','own_complete_mean_ms','against296','reused_roads']}));save(D/'screen-results-private.json',screen);print(json.dumps(dict(candidate=c['label'],fully_observed=e['fully_observed'],completions=e['completions'],own_complete_mean_ms=e['own_complete_mean_ms'],native=read(D/'budget.json')['screen'])),flush=True)
   if not e['fully_observed']:raise RuntimeError('Screenincomplete/technical/budget; no forcedselection')
  selected=min(screen,key=rank_screen);frozen=D/'screen-winner-frozen.json'
  if not frozen.exists():save(frozen,dict(winner=selected,all18screen_outcomes_verified=True,frozen_epoch=time.time(),no_alternate_selection=True))
  assert read(frozen)['winner']==selected
  if selected['label']!='296':
   e=evaluate(D,p,selected,p['extension'],'extension');rr=selected['results']+e['results'];fully=e['fully_observed'] and len(rr)==18;full=dict(label=selected['label'],fully_observed=fully,results=rr,**metrics(rr),against296=diagnose(rr,p['baseline296']['results']) if fully else None);save(D/'full-TRAIN-private.json',full)
   if not fully:raise RuntimeError('Extensionincomplete/technical/budget; no promotion')
   bcount=sum(r['completed'] for r in p['baseline296']['results']);d=full['against296'];eligible=full['completions']>bcount or (full['completions']==bcount and d['common_mean_delta_ms'] is not None and d['common_mean_delta_ms']<0);save(D/'full-TRAIN-gate.json',dict(eligible=bool(eligible),baseline296_completions=bcount,candidate_completions=full['completions'],against296=d));print(json.dumps(dict(fullTRAINwinner=selected['label'],completions=full['completions'],eligible=bool(eligible),diagnostic=d)),flush=True)
   if eligible:
    if not (D/'screen-opening.json').exists():save(D/'screen-opening.json',dict(winner_sha256=sha(frozen),fullTRAIN_sha256=sha(D/'full-TRAIN-private.json'),single_candidate=True))
    for case in p['fresh_DEV']:
     pair={}
     for arm in case['arm_order']:
      c=p['baseline296'] if arm=='A' else selected;t=c['theta'];rr=jobs(D,p,[dict(folder=str(D/'DEV'/case['public_label']/arm),road=case['public_label'],case=case,config=c['config'],ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))],'evaluation')
      if rr:pair[arm]=rr[0]
     dev.append(dict(road=case['public_label'],arm_order=case['arm_order'],results=pair));save(D/'DEV-records-private.json',dev);print(json.dumps(dict(DEVroad=case['public_label'],results={a:{k:r.get(k) for k in ['completed','actual_DNF','censored','technical_error','lap_ms']} for a,r in pair.items()},native=read(D/'budget.json')['evaluation'])),flush=True)
     if set(pair)!={'A','B'} or any(r['censored'] or r['technical_error'] for r in pair.values()):raise RuntimeError('DEVincomplete/technical/budget; preserve296')
    judgment=judge([x['results'] for x in dev]);judgment['winner']=selected['label'] if judgment['candidate_outranks'] else '296'
 except BaseException as ex:error=type(ex).__name__+': '+str(ex);print(error,flush=True)
 save(D/'outcome-private.json',dict(stage=298,screen=screen,selected=selected,full_TRAIN=full,eligible=bool(eligible),DEV=dev,judgment=judgment,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch']))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
