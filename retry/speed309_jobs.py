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
  F.mkdir(parents=True,mode=0o700);save(F/'job.json',dict(private_stage=str(D),phase=phase,native_cap=cap,**{k:v for k,v in e.items() if k!='folder'}));log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600);proc=subprocess.Popen([sys.executable,'-m','retry.speed309_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'));pending.append((F,proc,log))
 for F,proc,log in pending:
  rc=proc.wait();log.close();assert (F/'result.json').exists(),f'Childexit{rc}:no endpoint';out.append(read(F/'result.json'))
 return out
