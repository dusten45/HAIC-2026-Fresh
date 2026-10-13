"""One fixedgasguard,2TRAIN pilot andconditionalremaining16, noDEV/adoption."""
import argparse,time,json,os,subprocess,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose

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
  F.mkdir(parents=True,mode=0o700);save(F/'job.json',dict(private_stage=str(D),phase=phase,native_cap=cap,**{k:v for k,v in e.items() if k!='folder'}));log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600);proc=subprocess.Popen([sys.executable,'-m','retry.guard301_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'));pending.append((F,proc,log))
 for F,proc,log in pending:
  rc=proc.wait();log.close();assert (F/'result.json').exists(),f'Childexit{rc}:no endpoint';out.append(read(F/'result.json'))
 return out

def evaluate(D,p,roads):
 rr=[]
 for i in range(0,len(roads),2):
  batch=roads[i:i+2];c=p['candidate'];t=c['theta'];entries=[dict(folder=str(D/'TRAIN'/r),road=r,case=p['cases'][r],config=c['config'],initial_observation_sha256=p['initial_observations'].get(r),ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2]))) for r in batch];out=jobs(D,p,entries,'training');rr+=out;save(D/('pilot-private.json' if len(roads)==2 else 'extension-private.json'),rr)
  if len(out)<len(entries) or any(x['technical_error'] or x['censored'] for x in out):break
 return rr

def run(R):
 D=R/'stage301';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 if not (D/'opening.json').exists():save(D/'opening.json',dict(epoch=time.time()))
 pilot=[];extension=[];gate=False;error=None
 try:
  pilot=evaluate(D,p,p['pilot']);assert len(pilot)==2 and not any(x['technical_error'] or x['censored'] for x in pilot),'Pilotincomplete/technical/cap; noforcedextension';base=p['pilot_baseline'];m=metrics(pilot);bc=sum(x['completed'] for x in base);d=diagnose(pilot,base);gate=m['completions']>bc or (m['completions']==bc and d['common_mean_delta_ms'] is not None and d['common_mean_delta_ms']<0);save(D/'pilot-gate.json',dict(passed=bool(gate),baseline_completions=bc,candidate_completions=m['completions'],diagnostic=d));print(json.dumps(dict(pilot_results=[{k:x[k] for k in ['road','completed','actual_DNF','censored','lap_ms','native_actions']} for x in pilot],gate=bool(gate),diagnostic=d)),flush=True)
  if gate:extension=evaluate(D,p,p['extension']);assert len(extension)==16 and not any(x['technical_error'] or x['censored'] for x in extension),'Extensionincomplete/technical/cap; no DNFconversion'
 except BaseException as e:error=type(e).__name__+': '+str(e);print(error,flush=True)
 full=pilot+extension;fullmetric=dict(**metrics(full),against296=diagnose(full,p['baseline296']['results'])) if len(full)==18 and not any(x['technical_error'] or x['censored'] for x in full) else None;save(D/'outcome-private.json',dict(pilot=pilot,extension=extension,pilot_gate=bool(gate),full18=fullmetric,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],champion_changed=False,DEV_opened=False));print('301 closed',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
