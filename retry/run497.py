"""Exactly one authorized C4 saved-root smoothing ablation; no native interface."""
import time
START=time.perf_counter()
import ast,copy,datetime,hashlib,json,marshal,os,pickle,random,resource,shutil,signal,sys,traceback,types,subprocess
from pathlib import Path
from dataclasses import asdict
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');D=R/'stage497';M=Path('/tmp/haic-retry-stage495-qualified-private/model');INPUT=Path('/tmp/haic-retry-stage490-private/input-manifest-private.json')
DEADLINE='2026-10-20T10:01:55Z'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(v,s):
 if not v:raise RuntimeError('497_'+s)
def rawsave(p,v):
 from retry.pilot420_json import json_ready
 data=(json.dumps(json_ready(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();p=Path(p);check(not p.exists(),'IMMUTABLE:'+p.name)
 with p.open('xb') as f:os.chmod(p,0o600);f.write(data);f.flush();os.fsync(f.fileno())
 return sha(p)
def stop(*_):raise RuntimeError('497_WHOLE_RESOURCE_STOP')
def whole_guard():
 check(time.process_time()<180 and time.perf_counter()-START<240,'WHOLE_CAP')
 check(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'DEADLINE')

def smoothing_code():
 """Return original extracted controller and one-AST-expression replacement."""
 source=(G/'retry/pace269_run.py').read_text();tree=ast.parse(source);loop=next(x for x in ast.walk(tree) if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='step')
 start=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='raw' for z in x.targets));end=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='action' for z in x.targets))
 control=ast.Module(body=loop.body[start:end+1],type_ignores=[]);variant=copy.deepcopy(control)
 target=ast.parse('steer=.8*steer+.2*laststeer').body[0];matches=[x for x in ast.walk(variant) if ast.dump(x,include_attributes=False)==ast.dump(target,include_attributes=False)]
 check(len(matches)==1,'SINGLE_SMOOTHING_ASSIGNMENT');matches[0].value=ast.Name(id='steer',ctx=ast.Load());ast.fix_missing_locations(variant)
 undo=copy.deepcopy(variant);changed=[x for x in ast.walk(undo) if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='steer' and isinstance(x.value,ast.Name) and x.value.id=='steer'];check(len(changed)==1,'ONE_REMOVAL');changed[0].value=copy.deepcopy(target.value)
 check(ast.dump(undo,include_attributes=False)==ast.dump(control,include_attributes=False),'ONLY_AST_DIFFERENCE')
 return compile(control,str(G/'retry/pace269_run.py'),'exec'),compile(variant,str(G/'retry/pace269_run.py')+'#497-no-smoothing','exec'),dict(original_AST_sha256=hashlib.sha256(ast.dump(control,include_attributes=False).encode()).hexdigest(),variant_AST_sha256=hashlib.sha256(ast.dump(variant,include_attributes=False).encode()).hexdigest(),single_change='steer=.8*steer+.2*laststeer -> steer=steer; laststeer=steer unchanged')

def run():
 whole_guard();check(not D.exists(),'ONCE_NO_RETRY');check(subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31','PROTECTED_MAIN');check(json.loads((R/'research-deadline-current.json').read_text())['deadline_utc']==DEADLINE,'LATEST_DEADLINE');D.mkdir(mode=0o700)
 signal.signal(signal.SIGPROF,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_PROF,max(.001,180-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,240-(time.perf_counter()-START)))
 from retry.schema493 import receipt,digest,source_ref
 from retry.pilot420_json import json_ready
 import numpy as np
 from retry.runtime492 import Graph,canonical_projection
 from retry.executor490_input import load as inputs
 from retry.history495 import install as history_install
 from retry.test_runtime495 import physics_poison
 from retry.capture495 import Registry495,install_model495,authenticate_hold495,compare_repeat495,compare_flags495
 from retry.capture494 import encoded
 old_manifest=receipt(R/'stage495-retention-final-private.json');pins={x['path']:x['sha256'] for x in old_manifest['files']};accessed={}
 def checked(p):
  p=Path(p);check(str(p) in pins and sha(p)==pins[str(p)],'SAVED_PIN:'+p.name);accessed[str(p)]=pins[str(p)];return receipt(p)
 fixed,pace,nodes=inputs(INPUT)
 def plain(v):
  if isinstance(v,np.ndarray):return plain(v.tolist())
  if isinstance(v,np.generic):return v.item()
  if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
  if isinstance(v,(tuple,list)):return [plain(x) for x in v]
  return v
 frozen=fixed;fixed=plain(fixed)
 for key in ('speed','ds','curvature'):check(np.asarray(fixed['free_profile'][key],dtype='<f8').tobytes()==np.asarray(frozen['free_profile'][key],dtype='<f8').tobytes(),'PLAIN_BYTES')
 check(np.asarray(fixed['line'],dtype='<f8').tobytes()==np.asarray(frozen['line'],dtype='<f8').tobytes(),'PLAIN_LINE_BYTES')
 oldresult=checked(M/'result.json');binding=oldresult['binding'];check(binding['input_manifest_sha256']==sha(INPUT),'INPUT_BINDING')
 runtime=Graph(binding,fixed,pace,nodes).install();runtime.input_manifest_path=str(INPUT);history=history_install(runtime)
 names=('online481','online485','observer435','pilot420_backend','planner419_model_ledger','planner419','meter453','paired442_meter','pilot433_meter','paired417_common','io481','loss389_analyze','receipt421_io','ledger439','mechanism479','live477','live479','live481','live485','executor490_input')
 mods={n:runtime.import_module(n) for n in names};runtime.audit()
 io=mods['io481'];original_save=mods['loss389_analyze'].save;original_receipt=mods['receipt421_io'].save_receipt
 class Codec(io.Quota):
  STATE_MAX=512*1024;STATES_MAX=32;NONSTATE_MODEL_MAX=48*1024**2
  def __init__(self):
   super().__init__(D,64*1024**2,0,0);self.original_save=self.oldsave;self.original_receipt=self.oldreceipt;self.oldsave=lambda p,v:self.publish(p,v,False);self.oldreceipt=lambda p,v:self.publish(p,v,True)
  def before(self,path,value):
   p,n=super().before(path,value);fresh=p not in self.used
   check(len(self.used)+fresh<=504 and sum(self.used.values())-self.used.get(p,0)+n<=64*1024**2-256*1024,'STORAGE_WITH_CLOSING_RESERVE')
   if p.name.startswith('direct497-'):check(n<=(64*1024 if 'bundle' in p.name else 16*1024),'DIRECT_FORMAT')
   return p,n
  def cap(self,p):return self.STATE_MAX if p.name.startswith('state-') else 4*1024**2
  def publish(self,p,v,is_receipt):
   data=(json.dumps(json_ready(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();p=Path(p)
   # before() has reserved final size; temp overhead also fits total/free cap.
   check(sum(self.used.values())+len(data)<=64*1024**2,'TEMP_STORAGE');check(not is_receipt or not p.exists(),'RECEIPT_OVERWRITE')
   temp=p.with_name(p.name+'.tmp497');check(not temp.exists(),'STALE_TEMP')
   with temp.open('xb') as f:os.chmod(temp,0o600);f.write(data);f.flush();os.fsync(f.fileno())
   temp.replace(p);check(p.read_bytes()==data,'WRITE_READBACK')
   return io.canonical(v)
  def install(self):
   pairs=[(original_save,self.save),(original_receipt,self.save_receipt),(io.ORIGINAL_READ,io.read),(io.ORIGINAL_LOAD,io.load_receipt)]
   for mod in runtime.modules.values():
    if mod is io:continue
    for k,v in list(vars(mod).items()):
     for before,after in pairs:
      if v is before:setattr(mod,k,after);break
   return self
 codec=Codec();codec.install();runtime.codec=codec
 # All source namespaces are loaded before pinning; new code changes only the
 # local per-controller compiled operation, never historical module sources.
 original_code,variant_code,astproof=smoothing_code()
 ctx=checked(M/'context-004-private.json');coldroot=checked(M/'context-001-private.json');quarter=checked(M/'D495-A-root-authority-private.json');rootctx=checked(quarter['root_context_path']);parent=checked(M/'D495-A_control_1-private.json');obs=parent['observer_records495']['observer-private'];decisions=[checked(M/f'decision-{i:03d}-private.json') for i in (1,2,3)];auths=[v['authorization']|{'decision_path':str(M/f'decision-{i:03d}-private.json'),'decision_sha256':sha(M/f'decision-{i:03d}-private.json')} for i,v in zip((1,2,3),decisions)]
 # Existing saved authorizations already include all policy proof references;
 # decision_path/hash are the only outer additions used by history485.
 semantic={row['path']:row['source_sha256'] for row in runtime.records.values()};semantic.update({str(G/'retry'/n):sha(G/'retry'/n) for n in ('run497.py','history497.py','pace269_run.py','history495.py','runtime492.py','executor490_input.py','capture494.py','capture495.py','schema493.py','test_runtime495.py','pilot420_json.py','signed417_executor.py','projection491.py','diagnostic497_proposal.json','diagnostic497_contract.json')})
 plan=dict(budget_path=str(R/'project-effective-budget-v495.json'),budget_sha256=sha(R/'project-effective-budget-v495.json'),stage=497,deadline_utc=DEADLINE,semantic_sources=semantic,binding=binding,contract_sha256=sha(G/'retry/diagnostic497_contract.json'),root_context_path=str(M/'context-004-private.json'),root_context_sha256=sha(M/'context-004-private.json'),root_context_digest=io.canonical(ctx),ast=astproof,caps=dict(worlds=6,holds=26,charged_ticks=104,CPU_s=180,wall_s=240,bytes=64*1024**2,files=512,states=32,state_bytes=512*1024),actual_actions=0,resets=0,allocator=0,new_seeds=0,once=True)
 oldplan=checked(M/'plan.json')
 for path,h in semantic.items():
  if path in oldplan['semantic_sources']:check(h==oldplan['semantic_sources'][path],'ORIGINAL495_SOURCE_CHANGED:'+path)
 codec.save(D/'plan.json',plan)
 class Meter(mods['meter453'].Meter453):
  def __init__(self):
   super().__init__(D);self.charged_ticks=0;self.wrapper_slots=0;self.closed_worlds=0;self.integrating_worlds=0;self.peak_live=0;self.allocator_calls=0
  def persist(self):
   if hasattr(self,'nb'):codec.save(D/'budget.json',dict(stage=497,model=self.b,charged_ticks=getattr(self,'charged_ticks',0),holds=getattr(self,'wrapper_slots',0),live=len(self.live),closed=getattr(self,'closed_worlds',0),actual=self.nb,CPU_s=time.process_time(),wall_s=time.perf_counter()-START))
  def guard(self):whole_guard();check(time.process_time()<165 and time.perf_counter()-START<220,'CLEANUP_TIME_RESERVE');check(self.nb['actions']==self.nb['resets']==self.allocator_calls==0,'NO_NATIVE_ALLOCATOR')
  def timers(self):pass # whole-worker timers were installed before imports.
  def world(self,state,tag):
   self.guard();check(self.b['worlds']<6 and not self.live,'WORLD6_SINGLE_LIVE');m=super().world(state,tag);self.peak_live=max(self.peak_live,len(self.live));return m
  def step(self,m,a,tag):
   self.guard();check(self.charged_ticks+4<=104 and self.wrapper_slots<26 and m in self.live,'CHARGE_CAP');self.charged_ticks+=4;self.wrapper_slots+=1;self.persist();return mods['paired442_meter'].Meter.step(self,m,a,tag)
  def charge(self,*a):raise RuntimeError('497_NATIVE_FORBIDDEN')
  def begin_actual(self):raise RuntimeError('497_NATIVE_FORBIDDEN')
  def close(self,m):
   if m not in self.live:return
   stream=self.streams.get(id(m));child=None if stream is None else stream.child;m.close();world=m.world
   for body in list(world.bodies):world.DestroyBody(body)
   check(len(world.bodies)==len(world.joints)==0,'TEARDOWN');self.live.remove(m);self.auth.pop(id(m),None);self.streams.pop(id(m),None);self.closed_worlds+=1
   if stream:stream.world=stream.ctrl=stream.child=None
   if child is not None:child.m=None
   m.__dict__.clear();m.closed497=True;self.persist()
 meter=Meter();result=None;error=None;branches=[];live=None;status='TECHNICAL_STOP';static={};model_region=None
 def writer(child):
  def put(name,value):
   check(Path(name).name==name,'DIRECT_NAME');p=D/('direct497-'+name);codec.save_receipt(p,value);return source_ref(p,'')
  return put
 registry=Registry495();registry.install(runtime);install_model495(runtime,registry,writer,binding)
 # Native constructors/factories and allocators are permanently forbidden.
 def forbidden(*a,**k):raise RuntimeError('497_FORBIDDEN_NATIVE_OR_ALLOCATOR')
 for n in ('online485','online481','live485','live481','live477','live479'):
  mod=runtime.import_module(n)
  if hasattr(mod,'allocate_current'):mod.allocate_current=forbidden
 codec.install()
 try:
  with physics_poison(runtime) as poison:
   # Original qualified-quarter certificate and finite prefix are revalidated;
   # only the old prefix uses its genuine allocator receipts.
   history.authenticate_root495(quarter,rootctx['state'],rootctx['ledger'],rootctx['before'],fixed['line'])
   check(mods['pilot420_backend'].fingerprint(coldroot['state'])==obs['link']['root_state_digest'],'OLD_STREAM_ROOT_PIN')
   check(mods['online481'].physical_identity(coldroot['state'])==mods['online481'].physical_identity(rootctx['state']),'OLD_NATIVE_COLD_ROOT_JOIN')
   oldproof=history.validate_history(coldroot['state'],rootctx['ledger'],obs['posts'][:12],obs['actions'][:3],auths,ctx['state'],ctx['before'],ctx['ledger'],fixed['line'],auths[0]['policy_digest'])
   check(oldproof['actions']==3 and ctx['before']==obs['actions'][2]['memory_after'],'C4_BEFORE_NOMINAL_JOIN')
   check(sha(G/'retry/pace269_run.py')==semantic[str(G/'retry/pace269_run.py')],'ORIGINAL_LAW_PIN')
   py,npr=pickle.loads(ctx['RNG']['global_pickle']);check(hashlib.sha256(ctx['RNG']['global_pickle']).hexdigest()==ctx['RNG']['digest'],'RNG_BYTES')
   # Pure controller calls on a fake model test smoothing & coherent memory.
   from types import SimpleNamespace as NS
   h=ctx['state']['physical']['hull'];fake=NS(car=NS(hull=NS(position=h['position'],linearVelocity=h['velocity'],angle=h['angle'],angularVelocity=h['angular_velocity']),wheels=[NS(joint=NS(angle=w['joint']['angle']),tiles=w['tiles']) for w in ctx['state']['physical']['wheels']]),t=ctx['state']['physical']['actual_time'],finish_line_tracker=NS(**ctx['state']['finish_tracker']))
   ctrls=[];acts=[]
   for code in (original_code,variant_code):
    ctrl=mods['paired417_common'].SourceC(fixed,pace,copy.deepcopy(ctx['before']));check(marshal.dumps(ctrl.code)==marshal.dumps(original_code),'ORIGINAL_CODE_EXACT');ctrl.code=code;acts.append(ctrl.act(fake));ctrls.append(ctrl)
   check(acts[0].tolist()==ctx['nominal'] and ctrls[0].memory()==ctx['after'],'STATIC_CONTROL_ONCE')
   check(abs(ctrls[1].scope['laststeer']-(ctrls[0].scope['laststeer']-.2*ctx['before']['laststeer'])/.8)<1e-14,'UNFILTERED_LASTSTEER')
   check(np.array_equal(acts[0][1:],acts[1][1:]),'STATIC_PEDAL_LAW_UNCHANGED')
   check(not poison,'STATIC_PHYSICS_HIT');static=dict(passed=True,old_prefix=oldproof,ast=astproof,pure_control_once=True,variant_memory_coherent=True,physics_hits=0)
  for record in runtime.records.values():check(semantic.get(record['path'])==record['source_sha256'],'FINAL_NAMESPACE_SOURCE_PIN:'+record['path'])
  for path,h in semantic.items():check(sha(path)==h,'PREPHYSICS_SOURCE_PIN:'+path)
  # Preflight reserves physical output bytes and room for atomic writers.
  for volume in ('/tmp','/workspace'):check(shutil.disk_usage(volume).free>=512*1024**2+64*1024**2,'DISK_RESERVE')
  check(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<1024**3,'RSS_PREFLIGHT')
  codec.save(D/'static-private.json',static);meter.qualification_passed=True
  expected=checked(next(o['first_path'] for q in checked(M/'query-details-private.json')[0]['queries'] if q['local_query']==4 for o in q['options'].values() if 'nominal' in o['aliases']))
  expectedrow=expected['rows'][0];expectedhold=expected['direct_holds495'][0]
  # Separate non-finite-policy own authority below: no fake allocation receipts.
  model_region=meter.model('497_C4_FILTER_REMOVAL_ONLY');model_region.__enter__()
  for arm in ('control','variant'):
   arm_branches=[]
   for rep,limit in ((1,6),(2,6),('held',1)):
    random.setstate(py);np.random.set_state(npr);label=f'D497_{arm}_{rep}';full=mods['planner419_model_ledger'].ForecastLedger(**copy.deepcopy(ctx['ledger']))
    meter.capture_inputs(ctx['state'],ctx['before'],full,label+'_inputs',gate='497_AUTHENTICATED_C4_NOMINAL_ONLY')
    c=mods['online481'].Shadow(meter,copy.deepcopy(ctx['state']),copy.deepcopy(ctx['before']),mods['pilot420_backend'].model_ledger_view(full),fixed,pace,label,'nominal',world_tag='497_parent',full_ledger=ctx['ledger'],confirmation_phase='FIRST_LAP');live=c
    check(mods['online481'].physical_identity(mods['pilot420_backend'].snapshot(c.m))==mods['online481'].physical_identity(ctx['state']) and c.ctrl.memory()==ctx['before'] and asdict(c.ledger)==ctx['ledger'] and mods['pilot420_backend'].rnghash()==ctx['RNG']['digest'],'ROOT_RESTORE')
    c.ctrl.code=original_code if arm=='control' else variant_code
    policy_digest=io.canonical(dict(stage=497,arm=arm,root=plan['root_context_digest'],contract=plan['contract_sha256'],AST=astproof['original_AST_sha256' if arm=='control' else 'variant_AST_sha256']))
    transitions=[];first=None
    for index in range(limit):
     if c.status!='ACTIVE':break
     before=copy.deepcopy(c.ctrl.memory());state=mods['pilot420_backend'].snapshot(c.m);beforeledger=asdict(c.ledger);rng=mods['pilot420_backend'].rnghash();n=len(c.rows)
     c.one('497_nominal_only')
     if len(c.rows)==n:break
     row=c.rows[-1];hold=c.capture_holds495[-1];authenticate_hold495(hold,binding);flags=compare_flags495(hold,hold,binding)
     check(flags['safe'] or bool(row['safety']),'DIRECT_UNREPORTED_UNSAFE');check(row['memory_before']==before and row['command']==c.stream.actions[-1]['nominal'],'NOMINAL_ONCE');check(mods['pilot420_backend'].rnghash()==rng==ctx['RNG']['digest'],'RNG_CHANGED')
     check(c.ctrl.scope['laststeer']==row['memory_after']['laststeer'],'ACTUAL_MEMORY_JOIN')
     # Nominal-only own authority includes every state/memory/ledger boundary.
     transitions.append(dict(index=index+1,policy_digest=policy_digest,state_before=state,memory_before=before,ledger_before=beforeledger,state_after=mods['pilot420_backend'].snapshot(c.m),memory_after=c.ctrl.memory(),ledger_after=asdict(c.ledger),row_digest=io.canonical(row),RNG_digest=rng))
     if index==0:
      first=dict(row=copy.deepcopy(row),posts=copy.deepcopy(c.stream.posts),state=mods['pilot420_backend'].snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),RNG=rng)
      if arm=='control' and rep==1:
       check(row['command']==expectedrow['command'] and row['memory_before']==expectedrow['memory_before'] and row['memory_after']==expectedrow['memory_after'],'SOURCE_COMMAND_MEMORY');fidelity=mods['mechanism479'].fidelity(row,expectedrow);direct=compare_flags495(expectedhold,hold,binding);check(direct['passed'] and direct['safe'],'SOURCE_DIRECT_FLAGS');codec.save(D/'first-control-source-private.json',dict(passed=True,fidelity=fidelity,direct=direct,existing_native_qualification=False))
    # Replay every own tracker/ledger/physical join, separately from old finite history.
    from retry.history497 import authenticate_own,secondary
    own=authenticate_own(c,ctx,transitions,policy_digest,history,canonical_projection,mods)
    packet=dict(arm=arm,rep=rep,status=c.status,error=c.error,actions=len(c.rows),raw_ticks=sum(z['predicted']['raw_ticks'] for z in c.rows),raw_lengths=[z['predicted']['raw_ticks'] for z in c.rows],secondary=secondary(c.rows,fixed['line'],canonical_projection),safe_actions=sum(not z['safety'] for z in c.rows),progress_m=[z['model_progress']-ctx['ledger']['progress_m'] for z in c.rows],margins_m=[3-mods['online485'].max_guard_error(z,fixed['line']) for z in c.rows],signature=c.signature(),post_signature=io.canonical(c.stream.posts),first=first,history=own,policy_digest=policy_digest)
    if rep==2:
     check(packet['signature']==arm_branches[0]['signature'] and packet['post_signature']==arm_branches[0]['post_signature'],'COLD_REPEAT');check(len(c.capture_holds495)==len(arm_branches[0]['holds']),'REPEAT_HOLD_COUNT')
     for a,b in zip(c.capture_holds495,arm_branches[0]['holds']):compare_repeat495(a,b,binding)
    if rep=='held':check(first==arm_branches[0]['first'],'HELD_FIRST');compare_repeat495(c.capture_holds495[0],arm_branches[0]['holds'][0],binding)
    packet['holds']=copy.deepcopy(c.capture_holds495);arm_branches.append(packet);branches.append(packet)
    # All complete logical observer records remain separate, unmodified.
    c.dump(D);codec.save(D/(label+'-nominal-authority-private.json'),dict(policy_digest=policy_digest,transitions=transitions,history=own,holds=c.capture_holds495));c.close();live=None
    codec.save(D/'branches-private.json',branches);print(json.dumps(dict(stage=497,arm=arm,rep=rep,actions=packet['actions'],status=packet['status'],worlds=meter.b['worlds'],ticks=meter.charged_ticks)),flush=True)
  a=next(x for x in branches if x['arm']=='control' and x['rep']==1);b=next(x for x in branches if x['arm']=='variant' and x['rep']==1);n=min(a['actions'],b['actions']);check(n>0 and a['raw_lengths'][:n]==b['raw_lengths'][:n] and all(x==4 for x in a['raw_lengths'][:n]),'NO_EQUAL_ELAPSED_COMMON_HOLD');pg=b['progress_m'][n-1]-a['progress_m'][n-1];mg=min(b['margins_m'][:n])-min(a['margins_m'][:n]);fullsafe=b['actions']==b['safe_actions']==6 and b['status']=='ACTIVE';earlierunsafe=b['status']=='UNSAFE' and (a['status']!='UNSAFE' or b['raw_ticks']<a['raw_ticks']);success=fullsafe and pg>=.25 and mg>=-.25;reject=earlierunsafe or (pg<=-.25 and mg<.25);status='LOCAL_SUPPORT' if success and not reject else 'LOCAL_FALSIFICATION' if reject else 'NO_INFORMATION';result=dict(verdict=status,success=success and not reject,reject=reject,common_holds=n,common_time_s=n*.08,progress_gain_m=pg,margin_gain_m=mg,control_common_min_margin_m=min(a['margins_m'][:n]),variant_common_min_margin_m=min(b['margins_m'][:n]),control_status=a['status'],variant_status=b['status'],variant_H6_safe=fullsafe,exact_cold_repeats=True,held_first_passed=True,posthoc_root=True,native_promotion=False,whole_lap_improvement=None)
 except BaseException as exc:
  status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc);codec.save(D/'stop-private.json',dict(error=error,traceback=traceback.format_exc(),no_retry=True));print(error,flush=True)
 finally:
  if live is not None and not live.closed:
   try:live.dump(D)
   finally:live.close()
  meter.closeall()
  if model_region is not None:model_region.__exit__(None,None,None)
 whole_guard();check(not meter.live and meter.closed_worlds==meter.b['confirmed_worlds'],'CLOSED_ALL');check(len(codec.objects)<=32,'STATE_COUNT')
 # Two complete codec/raw readbacks, including source pins and original files.
 for _ in range(2):
  for p in D.iterdir():
   if p.is_file():receipt(p)
 for p,h in accessed.items():check(sha(p)==h,'SAVED_IMMUTABLE')
 for p,h in semantic.items():check(sha(p)==h,'SOURCE_IMMUTABLE')
 check(sha(plan['budget_path'])==plan['budget_sha256'],'BUDGET_IMMUTABLE')
 whole_guard();final=dict(stage=497,status=status,error=error,outcome=result,static_passed=static.get('passed',False),worlds=meter.b['worlds'],closed_worlds=meter.closed_worlds,live_worlds=len(meter.live),actual_ticks=meter.b['ticks'],charged_ticks=meter.charged_ticks,holds=meter.wrapper_slots,actual_actions=0,resets=0,new_seeds=0,allocator_calls=0,CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,state_objects=len(codec.objects),files=len(codec.used),bytes=sum(codec.used.values()),research_remaining=26027,reserve=84000,reserve_used=0,no_retry=True,no_followup=True,deadline_utc=DEADLINE)
 codec.save(D/'result-private.json',final);codec.save(D/'read-inputs-private.json',accessed);whole_guard();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(final),flush=True)
if __name__=='__main__':run()
