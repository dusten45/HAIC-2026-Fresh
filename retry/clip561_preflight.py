"""Synthetic exactness/storage checks and saved560 classification; NO physics."""
import itertools,json,math,tempfile,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.clip561_core import atomic_write,order_slack,count_pass,source_fraction_pass,prefix_slacks,nonexempt_branch

def run(private):
 cpu,wall=time.process_time(),time.perf_counter();checks={};count=0
 with tempfile.TemporaryDirectory(dir='/tmp',prefix='clip561-private-') as folder:
  p=Path(folder)/'record.json';atomic_write(p,dict(a=np.int64(7),nested=[np.float32(.5),np.bool_(True)],array=np.array([1,2],np.int32)));checks['numpy_basic_roundtrip']=json.loads(p.read_text())==dict(a=7,nested=[.5,True],array=[1,2])
  original=p.read_bytes()
  try:atomic_write(p,dict(bad=float('nan')),True)
  except ValueError:pass
  checks['nonfinite_preserves_old']=p.read_bytes()==original
  try:
   with patch('retry.clip561_core.os.replace',side_effect=OSError('INJECTED_BEFORE_COMMIT')):atomic_write(p,dict(new=np.int64(9)),True)
  except OSError:pass
  checks['atomic_replace_failure_preserves_old']=p.read_bytes()==original and len(list(Path(folder).iterdir()))==1
  try:atomic_write(p,dict(replace=False))
  except FileExistsError:pass
  checks['exclusive_preserves_old']=p.read_bytes()==original
  ledger=Path(folder)/'finally.json';start=time.process_time()
  try:raise RuntimeError('INJECTED_WORK_ERROR')
  except RuntimeError:pass
  finally:atomic_write(ledger,dict(cost=dict(model_ticks=np.int64(0),CPU_s=time.process_time()-start,wall_s=.0),failed=np.bool_(True)))
  z=json.loads(ledger.read_text());checks['finally_numpy_cost_survives_exception']=z['failed'] and isinstance(z['cost']['CPU_s'],float) and z['cost']['model_ticks']==0
 values=[.5,float(np.nextafter(1.,0.)),1.,float(np.nextafter(1.,2.)),float(np.nextafter(np.float32(1.),np.float32(0.))),float(np.nextafter(np.float32(1.),np.float32(2.))),1.2]
 histories=[]
 for n0 in [0,1,9,10,11,19,20,160,1000000]:
  for c0 in sorted(set([0,min(n0,1),min(n0,2),n0//10,min(n0,n0//10+1)])):histories.append((c0,n0))
 for n in range(5):
  for r in itertools.product(values,repeat=n):
   for c0,n0 in histories:
    slack,_=order_slack(r,c0,n0);actual=source_fraction_pass(r,c0,n0);assert (slack>=0)==count_pass(r,c0,n0)==actual;count+=1
   if time.process_time()-cpu>20 or time.perf_counter()-wall>30:raise RuntimeError('PREFLIGHT_CAP')
 checks['strict_ties_f32_history_denominator_equivalence']=True
 checks['exact1_unclipped']=(order_slack([1.]*4,0,0)[0]==0 and count_pass([1.]*4,0,0))
 checks['nextafter_above1_clipped']=not count_pass([np.nextafter(1.,2.)],0,0) and not count_pass([np.nextafter(np.float32(1.),np.float32(2.))],0,0)
 a=np.array([1.01,.8,.8,.8]);b=np.array([.8,1.01,.8,.8]);checks['active_identity_can_swap']=count_pass(a,0,6) and count_pass(b,0,6) and np.array_equal(nonexempt_branch(a,0,6),[1,2,3]) and np.array_equal(nonexempt_branch(b,0,6),[0,2,3])
 cases=[]
 for label in ['baseline','trial-00-00','trial-00-01','trial-00-02']:
  data=json.loads((Path('/workspace/haic-response560-private')/(label+'-private.json')).read_text());ratios=np.array([f['ratio'] for r in data['rows'] for f in r['forces']]);assert all((f['ratio']>1)==f['clipped'] for r in data['rows'] for f in r['forces']);slacks=prefix_slacks(ratios,3,160);actual=[source_fraction_pass(ratios[:n],3,160) for n in range(4,len(ratios)+1,4)];assert list(slacks>=0)==actual
  cases.append(dict(label=label,prefixes=len(slacks),order_all_pass=bool(np.all(slacks>=0)),count_all_pass=all(actual),first_bad_raw=next((i+1 for i,v in enumerate(actual) if not v),None),minimum_order_slack=float(min(slacks))))
 checks['saved560_exact_four_case_classification']=cases[0]['order_all_pass'] and all(not x['order_all_pass'] for x in cases[1:])
 out=dict(passed=all(checks.values()),checks=checks,synthetic_equivalence_cases=count,saved_cases=cases,model_ticks=0,force_calls=0,geometry_calls=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,domain='Finite ratios, integer source counts,10% budget; synthetic histories up to1e6 so source float fraction agrees with exact integer floor. No claim beyond tested floating denominator domain.')
 atomic_write(private/'preflight-private.json',out);return out
