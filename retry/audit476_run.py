"""Registered, bounded saved arithmetic/search validation. No physics imports."""
import ctypes,datetime,hashlib,json,math,os,shutil,signal,sys,time
from pathlib import Path
from retry.audit474_traces import NoPhysics,RUNS
from retry.audit475_forces import read,sha,put,G
RAW=Path('/tmp/haic-retry-stage476-private');MIB=1024**2

def before_path(root,label,wi):
 if label=='473_P4':return root/'stage473/world43-before-first-step-private.json' if wi==1 else None
 if label=='473_Original':return root/'stage473/world42-before-first-step-private.json' if wi==1 else None
 rel=RUNS[label][0];folder=root/Path(rel).parent;prefix='Projected4ReferenceCommonPulse' if label=='472_nativeP4' else 'C0' if label=='442_nativeC0' else 'P'
 return folder/f'{prefix}_step{wi}-before-native-private.json'
def loadrows(root,label):
 rel,obs=RUNS[label];return read(root/rel)['rows'] if obs else [json.loads(s) for s in (root/rel).read_text().splitlines() if s]
def prepare(root):
 old=read(root/'stage475-plan-durable-private.json');assert not RAW.exists() and not(root/'stage476').exists();assert read(root/'research-deadline-current.json')['deadline_utc']=='2026-10-20T10:01:55Z'
 sources=dict(old['sources']);reps={};counts={}
 for label in RUNS:
  rows=loadrows(root,label);n=len(rows);reps[label]=sorted({1,2,3,n//4+1,n//2+1,3*n//4+1,n-1,n});counts[label]=n
  for wi in range(1,n+1):
   f=before_path(root,label,wi)
   if f is not None:assert f.is_file();sources[str(f)]=sha(f)
 for name in ['allocator476.py','audit476_run.py','audit476_verify.py']:
  p=G/'retry'/name;sources[str(p)]=sha(p)
 sources[str(root/'research-deadline-current.json')]=sha(root/'research-deadline-current.json')
 free={s:shutil.disk_usage(s).free for s in ['/tmp','/workspace']};required=(16+32+512)*MIB;assert free['/tmp']>=required and free['/workspace']>=576*MIB
 p=dict(stage=476,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=sources,protected=old['protected'],original408_preserve=old['original408_preserve'],deadline_utc=old['deadline_utc'],mode='PURE_ARITHMETIC_SEARCH_NO_INTEGRATION',CPU_cap_s=600,wall_cap_s=900,new_physics=0,new_native=0,new_world=0,new_reset=0,new_actor=0,raw_hard_bytes=16*MIB,proof_hard_bytes_each=8192,reserve_bytes_each=512*MIB,temp_allowance_bytes=32*MIB,free_bytes=free,tmp_required_bytes=required,workspace_metadata_and_reserve_bytes=576*MIB,representatives=reps,stored_counts=counts,before_state_coverage='all533 native wrappers plus2 model root snapshots; remaining130 model decisions telemetry-fed only',predeclared_checks=['all available before-state q0 vs first raw, independent vs telemetry separately','exact q0 identity, q0 inclusion and nonworsening objective','independent source evaluator witness and predecessor/next boundary audit','small finite rank intervals exhaustive oracle','gas plateau, brake general/zero/lock, damage and unsupported fixtures'],stops='source/hash/schema/operation/time/output/mismatch => technical stop; preserve partial; no physics or search retuning. Unsupported numeric domains recorded separately from infeasibility',search_scope='Exactly8 registered first-raw decisions per run,40 total; no trajectory propagation; actual stored command, guards included',output='Proofs compact bounded perquery, no perprobe logs; no archive/copy/delete oldraw',authorization_extension_path=old['sources'] and str(root/'stage441/authorization-correction-private.json'),authorization_extension_sha256=sha(root/'stage441/authorization-correction-private.json'))
 RAW.mkdir(mode=0o700);(root/'stage476').symlink_to(RAW,target_is_directory=True);put(RAW/'plan.json',p);put(root/'stage476-plan-durable-private.json',p);print(json.dumps(dict(plan_sha256=sha(RAW/'plan.json'),representatives=reps,storage=dict(free=free,required=required))))
def physical(root,label,wi):
 p=before_path(root,label,wi)
 if p is None:return None
 d=read(p);return d['model_root']['physical'] if label.startswith('473') else d['full_pre_before_nominal']['physical']
def independently_build(p):
 # libm pure arithmetic, not Box2D. Validate this angle->rotation reconstruction
 # against saved first-raw vf/vs, never assume cached transform identity.
 lib=ctypes.CDLL('libm.so.6');lib.sinf.argtypes=[ctypes.c_float];lib.sinf.restype=ctypes.c_float;lib.cosf.argtypes=[ctypes.c_float];lib.cosf.restype=ctypes.c_float
 damage=p['damage'];engine=max(.8,1.-damage*.25);grip=max(.6,1.-damage*.5);roads={t['idx']:t['friction'] for t in p['roads']};out=[]
 for j,w in enumerate(p['wheels']):
  a=w['body']['angle'];s=float(lib.sinf(a));c=float(lib.cosf(a));vx,vy=w['body']['velocity'];vf=(-s)*vx+c*vy;vs=c*vx+s*vy;lim=400.*p['grass_friction_multiplier']
  for tile in w['tiles']:lim=max(lim,400.*roads[tile])
  lim*=grip
  out.append(dict(wheel=j,omega=float(w['dynamics']['omega']),gas=float(w['dynamics']['gas']),vf=float(vf),vs=float(vs),limit=float(lim),engine=float(engine),radius=.54))
 return out

def run(root,directory_name='stage476'):
 guard=NoPhysics();sys.meta_path.insert(0,guard)
 import numpy as np
 from retry.allocator476 import force,solve,Unsupported
 from retry.audit476_verify import verify,fixtures
 d=root/directory_name;p=read(d/'plan.json');start=time.perf_counter();cpu=time.process_time();signal.setitimer(signal.ITIMER_PROF,599);signal.setitimer(signal.ITIMER_REAL,899)
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 put(d/'opening-private.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(d/'plan.json'),new_physics=0))
 def guardbudget():
  if time.process_time()-cpu>=598 or time.perf_counter()-start>=898:raise RuntimeError('resource_cap')
  if sum(f.stat().st_size for f in d.iterdir() if f.is_file())>=p['raw_hard_bytes']:raise RuntimeError('output_cap')
  if shutil.disk_usage('/tmp').free<512*MIB or shutil.disk_usage('/workspace').free<512*MIB:raise RuntimeError('reserve')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')):raise RuntimeError('deadline')
 fixture_result=fixtures();put(d/'fixtures-private.json',fixture_result)
 before_checks=[];queries=[];identity={};interventions={};q0_metrics={}
 for label in RUNS:
  rows=loadrows(root,label);model=label.startswith('473');dtype='model64' if model else 'native32';initial=physical(root,label,1);prev=[dict(omega=w['dynamics']['omega'],gas=w['dynamics']['gas']) for w in initial['wheels']];ident=0;num=0
  for wi,row in enumerate(rows,1):
   guardbudget();cmd=row['command'];assert not(cmd[1]>0 and cmd[2]>0);branch='gas' if cmd[1]>0 else 'brake' if cmd[2]>0 else 'none';q0=float(cmd[1] if branch=='gas' else cmd[2] if branch=='brake' else 0.);tires=row['tires'] if model else row['raw_tire_samples'];first=[t for t in tires if t['raw_tick']==1];snapshot=physical(root,label,wi);ind=None
   conditional=[dict(wheel=t['wheel'],omega=float(prev[t['wheel']]['omega']),gas=float(prev[t['wheel']]['gas']),vf=t['forward_speed_m_s'],vs=t['lateral_slip_m_s'],limit=t['friction_limit'],engine=1.,radius=.54) for t in first]
   for w,t in zip(conditional,first):
    r=force(w,q0,branch,dtype);es={k:abs(r[f]-t[k]) for k,f in [('omega','omega'),('gas','gas'),('brake','brake'),('raw_long_N','long'),('raw_lat_N','lat')]};assert max(es.values())==0,(label,wi,es);ident+=1;num+=1
   if snapshot is not None:
    ind=independently_build(snapshot);errors=[]
    for w,t in zip(ind,first):
     r=force(w,q0,branch,dtype);es=dict(vf=w['vf']-t['forward_speed_m_s'],vs=w['vs']-t['lateral_slip_m_s'],limit=w['limit']-t['friction_limit'],gas=r['gas']-t['gas'],omega=r['omega']-t['omega'],long=r['long']-t['raw_long_N'],lat=r['lat']-t['raw_lat_N']);errors.append(es)
    before_checks.append(dict(run=label,wrapper=wi,errors=errors,all_exact=all(v==0 for es in errors for v in es.values()),damage=snapshot['damage'],inputs='wheel stored angle/COM linearVelocity, tile friction, damage multiplier; libm sinf/cosf reconstruction'))
   if wi in p['representatives'][label]:
    # A mismatch is not repaired with telemetry: native independent runs stop.
    if ind is not None and not before_checks[-1]['all_exact']:raise RuntimeError('independent_before_state_mismatch:'+label+':'+str(wi))
    wheels=ind if ind is not None else conditional;cc=time.process_time();ww=time.perf_counter();proof=solve(wheels,q0,branch,dtype);elapsed=time.process_time()-cc;welapsed=time.perf_counter()-ww;vc=time.process_time();verify(wheels,q0,branch,dtype,proof);verifycpu=time.process_time()-vc
    packet=dict(run=label,wrapper=wi,input_kind='independent_before_state' if ind is not None else 'telemetry_conditional',branch=branch,dtype=dtype,CPU_s=elapsed,wall_s=welapsed,verification_CPU_s=verifycpu,proof=proof)
    b=json.dumps(packet,allow_nan=False).encode();assert len(b)<=p['proof_hard_bytes_each'];packet['compact_proof_bytes']=len(b);queries.append(packet)
   # Source reaction from saved local observations only. No state integration.
   for k in range(1,len(row['raw_hull'])+1):
    for t in [t for t in tires if t['raw_tick']==k]:
     ff=t['raw_long_N'];f=np.sqrt(np.square(ff)+np.square(t['raw_lat_N']))
     if f>t['friction_limit']:ff/=f;ff*=t['friction_limit']
     prev[t['wheel']]=dict(omega=t['omega']-.02*ff*.54/1.6,gas=t['gas'])
  identity[label]=dict(wheel_first_samples=num,exact=ident)
 put(d/'before-checks-private.json',before_checks);put(d/'queries-private.json',queries)
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 out=dict(stage=476,status='PURE_SEARCH_VALIDATION_COMPLETE',plan_sha256=sha(d/'plan.json'),numpy_version=np.__version__,q0_telemetry_identity=identity,before_state=dict(available=len(before_checks),all_exact=sum(x['all_exact'] for x in before_checks),nonzero_damage=sum(x['damage']>0 for x in before_checks),max_abs_error=max(abs(v) for q in before_checks for e in q['errors'] for v in e.values())),fixtures=fixture_result,query_count=len(queries),query_summary={label:dict(n=len(qs),changed=sum(q['proof']['q']!=q['proof']['q0'] for q in qs),objective_strictly_lower=sum(q['proof']['objective']<q['proof']['objective_q0'] for q in qs),objective_still_positive=sum(q['proof']['objective']>0 for q in qs),max_search_CPU_s=max(q['CPU_s'] for q in qs),mean_search_CPU_s=sum(q['CPU_s'] for q in qs)/len(qs),max_search_wall_s=max(q['wall_s'] for q in qs),max_proof_bytes=max(q['compact_proof_bytes'] for q in qs),max_wheel_evaluations=max(q['proof']['wheel_evaluations'] for q in qs)) for label in RUNS for qs in [[q for q in queries if q['run']==label]]},total_search_CPU_s=sum(q['CPU_s'] for q in queries),total_verification_CPU_s=sum(q['verification_CPU_s'] for q in queries),max_query_CPU_s=max(q['CPU_s'] for q in queries),max_query_wall_s=max(q['wall_s'] for q in queries),max_proof_bytes=max(q['compact_proof_bytes'] for q in queries),new_physics=0,new_native=0,new_world=0,new_reset=0,new_actor=0,import_guard_attempts=guard.attempts,whole_analysis_CPU_s=time.process_time()-cpu,whole_analysis_wall_s=time.perf_counter()-start,protection_verified=True,caveat='Saved arithmetic interventions only; no fresh dynamics or80ms safety effect',CPU_and_IO_include='read all535 full snapshots, hash manifests, fixtures,40searches and independent validation; preparation/report not fully measured')
 guardbudget();put(d/'result.json',out);put(G/'retry/audit476_result.json',out);print(json.dumps(out));signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else 'stage476')
