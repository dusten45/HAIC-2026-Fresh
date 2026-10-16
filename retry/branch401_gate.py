"""Qualified source-model snapshot branches; no challenge env or actor."""
import datetime,hashlib,json,sys,time,traceback,signal
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.numeric401_audit import read,save,sha
from retry.source_vehicle_transition import SourceVehicleTransition,capture
G=Path(__file__).resolve().parent.parent

def snapshot(model,t):
 raw=SimpleNamespace(car=model.car,world=model.world,road=model.roads,obstacles=model.obstacles,track=model.track,tile_visited_count=model.tile_visited_count,t=t)
 return capture(SimpleNamespace(unwrapped=raw,damage=model.damage,off_track_counter=model.off_track_counter))
def fingerprint(x):return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()
class Meter:
 def __init__(self,d):
  self.d=d;self.b=read(d/'model-budget.json');self.cpu=time.process_time();self.wall=time.perf_counter();self.basecpu=self.b.get('CPU_s',0.)
 def guard(self):
  assert self.basecpu+time.process_time()-self.cpu<180
  assert time.time()-self.b['started_epoch']<300
  assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(read(self.d/'plan.json')['deadline_utc'])
 def persist(self):
  self.b['CPU_s']=self.basecpu+time.process_time()-self.cpu;save(self.d/'model-budget.json',self.b)
 def step(self,m,a):
  self.guard();assert self.b['reserved']+4<=12288;self.b['reserved']+=4;self.persist();before=m.native_ticks
  try:return m.step(a)
  finally:self.b['ticks']+=m.native_ticks-before;self.persist()
 def world(self,s):
  self.guard();self.b['worlds']+=1;self.persist();return SourceVehicleTransition(s)
def errors(q,r):return dict(speed_m_s=abs(q['speed_m_s']-r['speed_m_s']),yaw_rate_rad_s=abs(q['angular_velocity']-r['angular_velocity']),position_m=float(np.linalg.norm(np.asarray(q['position'])-r['position'])))
def compare(q,r):
 e=errors(q,r);dis={k:q[k]==r[k] for k in ['collision','damage','wheel_road_contacts']};return dict(errors=e,discrete=dis,passed=e['speed_m_s']<=.5 and e['yaw_rate_rad_s']<=.05 and e['position_m']<=.1 and all(dis.values()))
def prepare(root):
 d=root/'stage401';assert read(d/'numeric-result.json')['numeric_passed'];assert not(d/'branch-plan.json').exists();p=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),fork_case='N1',fork_step=94,prefix_actions=93,reference='Stored39894command; parentcontinuousvsfreshbranch391criteria. Snapshotcaptureandcandidatebranchesmustnotmutateparent/input. Sixbranches repeatreverseorder exactreproducibility; bothreferencefreshbranches exactrepeat.',candidates='pursuitrequest stored39894,holdnegativecurrentfrontmeanjoint,neutral0 x nominal39894pedals,coast0/0; listedorder. Candidatequalificationnotpolicyperformance.',stop='Anyinitialbody/tile/progress mismatch,sourcehash,reference391mismatch,mutation/nonindependence ->stopall,factorial0. No tolerancechange/retry.',sources={str(f):sha(f) for f in [Path(__file__),d/'plan.json',d/'numeric-result.json',root/'stage398/N1/initial-private.json',root/'stage398/N1/trace-private.jsonl',G/'retry/source_vehicle_transition.py']})
 save(d/'branch-plan.json',p);print('Branch gate preregistered, no positive-time calls yet')
def run(root):
 d=root/'stage401';p=read(d/'branch-plan.json');assert not(d/'branch-opening.json').exists()
 for f,h in p['sources'].items():assert sha(f)==h,f
 assert not(d/'model-budget.json').exists();save(d/'model-budget.json',dict(ticks=0,reserved=0,worlds=0,CPU_s=read(d/'numeric-result.json')['CPU_s'],started_epoch=time.time()));save(d/'branch-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter(d);active=[];error=None;failure=None;records=[];status='RUNNING'
 def timeout(*args):raise TimeoutError('401CPU180')
 oldsig=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,179)
 try:
  actual=[json.loads(s) for s in (root/'stage398/N1/trace-private.jsonl').read_text().splitlines()];parent=meter.world(read(root/'stage398/N1/initial-private.json')['physical']);active.append(parent);assert parent.initial_bodies_exact and parent.initial_tiles_exact and parent.initial_progress_exact
  for r in actual[:93]:meter.step(parent,np.asarray(r['command'],np.float32))
  row=actual[93];s=snapshot(parent,row['pre']['time']);saved=fingerprint(s);parent_before=fingerprint(snapshot(parent,row['pre']['time']));parentQ=meter.step(parent,np.asarray(row['command'],np.float32));parent_after=fingerprint(snapshot(parent,row['post']['time']))
  refs=[]
  def evaluate(action,label):
   nonlocal failure
   before=fingerprint(s);m=meter.world(s);active.append(m);ini=dict(bodies=m.initial_bodies_exact,tiles=m.initial_tiles_exact,progress=m.initial_progress_exact)
   if not all(ini.values()):failure=dict(kind='initialization',label=label,initial=ini);return None
   q=meter.step(m,np.asarray(action,np.float32));m.close();active.remove(m)
   if fingerprint(s)!=before or fingerprint(snapshot(parent,row['post']['time']))!=parent_after:failure=dict(kind='state_mutation',label=label)
   return q
  q=evaluate(row['command'],'reference_before')
  if failure is None:
   z=compare(q,parentQ);records.append(dict(label='parent_vs_fresh',**z))
   if not z['passed']:failure=dict(kind='restoration_mismatch',record=z)
  if failure is None:
   joint=float(np.mean([w['joint']['angle'] for w in s['wheels'][:2]]));candidates=[np.asarray([a,*b],np.float32).tolist() for a in [row['command'][0],float(np.clip(-joint,-.4,.4)),0.] for b in [row['command'][1:],[0.,0.]]];outs={}
   for idx in list(range(6))+list(range(5,-1,-1)):
    q2=evaluate(candidates[idx],f'candidate{idx}')
    if failure:break
    if idx in outs and q2!=outs[idx]:failure=dict(kind='candidate_order_dependence',index=idx);break
    outs[idx]=q2
   if failure is None:
    q3=evaluate(row['command'],'reference_after')
    if failure is None and q3!=q:failure=dict(kind='reference_repeat_mismatch')
   records.append(dict(label='candidate_independence',passed=failure is None,candidates=6,orders=['forward','reverse'],snapshot_unchanged=fingerprint(s)==saved,parent_unchanged=fingerprint(snapshot(parent,row['post']['time']))==parent_after))
  status='BRANCH_QUALIFIED' if failure is None else 'BRANCH_UNQUALIFIED'
 except BaseException as e:error=type(e).__name__+': '+str(e);status='TECHNICAL_STOP';save(d/'branch-error-private.json',dict(error=error,traceback=traceback.format_exc()))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig)
  for m in active:m.close()
  meter.persist()
 x=dict(status=status,passed=status=='BRANCH_QUALIFIED',failure=failure,technical_error=error,records=records,budget=meter.b,factorial_executed=False);save(d/'branch-result.json',x);print(json.dumps(x,ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
