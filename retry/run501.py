"""One registered501 factual-first screen; no native interface or automatic retry."""
import time
START=time.perf_counter()
import copy,datetime,hashlib,json,math,os,pickle,random,resource,shutil,signal,sys,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');CONTROL=R/'stage501'
ATTEMPT=int(os.environ.get('HAIC501_ATTEMPT','0'));check_attempt=0<=ATTEMPT<=3
if not check_attempt:raise ValueError('501_ATTEMPT_RANGE')
D=Path('/tmp/haic-retry-stage501'+('' if ATTEMPT==0 else '-prep'+str(ATTEMPT))+'-private')
DEADLINE='2026-10-20T10:01:55Z'
PRE_CPU=float(os.environ.get('HAIC501_PRIOR_CPU','12'));PRE_WALL=float(os.environ.get('HAIC501_PRIOR_WALL','20')) # source1.883 + IOtest bounds + preparation/closing allowance

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(v,s):
    if not v:raise RuntimeError('501_'+s)
def cpu():return time.process_time()+PRE_CPU
def wall():return time.perf_counter()-START+PRE_WALL
def guard(*args):
    check(cpu()<600 and wall()<900,'WHOLE_RESOURCE_CAP')
    check(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'DEADLINE')
def timed_stop(*a):raise RuntimeError('501_RESOURCE_TIMER')


def own_history(c,root,transitions,mods,stop_before=None):
    check(len(transitions)==len(c.rows)==len(c.stream.actions)==len(c.capture_holds495),'OWN_COVERAGE')
    ledger=mods['planner419_model_ledger'].ForecastLedger.fork(root['ledger'])
    tracker=mods['capture434'].FinishLineTracker(**copy.deepcopy(root['state']['finish_tracker']))
    previous=copy.deepcopy(root['state']);memory=copy.deepcopy(root['before']);offset=0
    project=mods['signed417_executor'].canonical_projection;L=c.L
    arc=project(c.fixed['line'],previous['physical']['hull']['position'],previous['physical']['hull']['velocity'],memory['C']['phase'])['arc']
    for i,(t,f,action) in enumerate(zip(transitions,c.rows,c.stream.actions),1):
        guard();n=f['predicted']['raw_ticks'];q=f['predicted'];posts=c.stream.posts[offset:offset+n]
        check(t['state_before']==previous and t['memory_before']==memory==f['memory_before'] and t['ledger_before']==asdict(ledger),'OWN_BEFORE_CHAIN')
        check(t['row_digest']==mods['io481'].canonical(f) and f['command']==action['command'],'OWN_ROW_COMMAND')
        check(t['memory_after']==c.stream.actions[i-1]['memory_after'] or q['finished'],'OWN_AFTER_MEMORY')
        h=t['state_before']['physical']['hull'];raw=f['raw_hull'][0]
        check(raw['origin_position']==h['position'] and raw['COM_linear_velocity']==h['velocity'] and raw['time']==t['state_before']['physical']['actual_time'],'OWN_RAW_PRE_JOIN')
        check(n==len(posts)==len(f['raw_hull']) and len(f['tires'])==4*n,'OWN_RAW_COVERAGE')
        for j,p in enumerate(posts):
            check(p['raw_clock']==ledger.last_clock_tick+j+1,'OWN_RAW_CLOCK')
            tracker.update(tuple(p['position']),tuple(p['velocity']),p['progress'],p['time'])
            check(asdict(tracker)==p['tracker_after'],'OWN_TRACKER_REPLAY')
        projected,flags=mods['pilot420_backend'].metrics(q,f['tires'],f['raw_hull'],c.fixed['line'],f['memory_after']['C']['phase'])
        check(set(flags)==set(f['safety']),'OWN_SAFETY_REPLAY')
        progress=ledger.progress_m+(projected['arc']-arc+L/2)%L-L/2;arc=projected['arc']
        ledger=ledger.advance_prediction(mods['planner419_model_ledger'].ModelPrediction(progress,ledger.last_clock_tick+n,q['finished']))
        check(progress==f['model_progress'] and asdict(ledger)==t['ledger_after']==action['ledger_after'],'OWN_LEDGER_REPLAY')
        post=t['state_after'];check(post['finish_tracker']==asdict(tracker) and post['physical']['hull']['position']==q['position'] and post['physical']['hull']['velocity']==q['velocity'] and post['physical']['actual_time']==q['time'],'OWN_RETURN_JOIN')
        check(post['elapsed_raw_steps']==previous['elapsed_raw_steps']+n,'OWN_ELAPSED')
        check(not flags or i==len(c.rows),'OWN_CONTINUED_UNSAFE');check(not q['terminal'] or i==len(c.rows),'OWN_CONTINUED_TERMINAL')
        previous=post;memory=t['memory_after'];offset+=n
    check(asdict(ledger)==asdict(c.ledger) and previous==mods['pilot420_backend'].snapshot(c.m) and memory==(c.ctrl.memory() if stop_before is None else stop_before),'OWN_FINAL')
    return dict(passed=True,actions=len(c.rows),ticks=offset,own_tracker_ledger_state_memory_replayed=True,actual_authority=False)


def run():
    guard();check(CONTROL.is_dir() and not D.exists(),'ONCE_RAW_DIRECTORY')
    check(not (CONTROL/'PHYSICS_STARTED-private.json').exists(),'NO_RETRY_AFTER_PHYSICS')
    signal.signal(signal.SIGPROF,timed_stop);signal.signal(signal.SIGALRM,timed_stop)
    signal.setitimer(signal.ITIMER_PROF,max(.001,600-cpu()));signal.setitimer(signal.ITIMER_REAL,max(.001,900-wall()))
    from retry.runtime501 import Graph501
    from retry.preflight498 import preparation_poison
    from retry.storage500 import Store500
    from retry.io501 import Adapter501
    from retry.schema493 import receipt
    from retry.static501 import binding_gate,control_gate,capture_lifecycle,own_saved_gate
    from retry.law501 import FactualGate501,candidate_one
    from retry.capture495 import Registry495,install_model495,authenticate_hold495,compare_repeat495,compare_flags495
    from retry.capture494 import encoded
    check(sha(G/'retry/envelope500.py')==json.loads((G/'retry/envelope500_contract.json').read_text())['code_pins']['retry/envelope500.py'],'FROZEN500_LAW')
    source=json.loads((R/'stage501-source-private/source-schema-manifest-private.json').read_text())
    for row in source['native_receipts']:
        check(Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256'],'ORIGINAL472_RECEIPT_PIN')
    fixedpath=R/'stage269/N1-plan-private.json';pacepath=R/'stage404/profiles-private.json';p4path=R/'stage466-numeric-recovery1/projection-and-segments-private.json'
    fixed=json.loads(fixedpath.read_text());pace=np.asarray(json.loads(pacepath.read_text())['frozen268']);nodes=np.asarray(json.loads(p4path.read_text())['projected_nodes'])
    original=np.asarray(fixed['free_profile']['speed'])*pace
    check(sha(p4path)=='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f','P4_SOURCE')
    arcs=np.r_[0.,np.cumsum(fixed['free_profile']['ds'])].tolist()
    inputpins={str(p):sha(p) for p in [fixedpath,pacepath,p4path,R/'project-effective-budget-v495.json',R/'stage501-source-private/source-schema-manifest-private.json']}
    binding=dict(input_manifest_sha256=hashlib.sha256(json.dumps(inputpins,sort_keys=True).encode()).hexdigest(),projection491_sha256=sha(G/'retry/projection491.py'),runtime492_sha256=sha(G/'retry/runtime492.py'),line_sha256=hashlib.sha256(np.asarray(fixed['line'],dtype='<f8').tobytes()).hexdigest(),nodes_sha256=hashlib.sha256(nodes.astype('<f8').tobytes()).hexdigest(),capture494_sha256=sha(G/'retry/capture494.py'))
    prep=preparation_poison(Graph501);poison=prep.__enter__();runtime=None;codec=None;meter=None;live=None;region=None;physical_started=False;outcome=None;error=None;static={};branches=[];status='TECHNICAL_STOP';pending_authority=None
    try:
        runtime=Graph501(binding,fixed,pace,nodes).install()
        names=('law473','meter453','paired442_meter','pilot420_backend','pilot433_meter','pilot436_meter','observer435','planner419','planner419_model_ledger','geometry439','ledger439','paired417_common','terminal410_run','signed417_executor','capture434','io481','loss389_analyze','receipt421_io','canonical438','audit439','mechanism479')
        mods={n:runtime.import_module(n) for n in names}
        store=Store500(D);codec=Adapter501(runtime,store,logical_root=D).install();runtime.codec=codec
        # Prepaid bounded console/control and external source/preparation files.
        # No old input/raw files are copied or charged as new output.
        for folder in [CONTROL,R/'stage501-source-private']:
            for p in folder.rglob('*'):
                if p.is_file() and not p.name.endswith('.log'):codec.account_external(p)
        # Any earlier attempt must have stopped before a physical marker; its
        # complete outputs remain and count against the SAME total quotas.
        for prior in sorted(Path('/tmp').glob('haic-retry-stage501*-private')):
            if prior==D:continue
            for priorfile in prior.rglob('*'):
                if priorfile.is_file():
                    category='state' if priorfile.name.startswith('state-') else 'tick' if 'direct501-' in priorfile.name and '-bundle' not in priorfile.name else 'bundle' if '-bundle' in priorfile.name else 'other'
                    store.record('prior-'+sha(priorfile)+'-'+hashlib.sha256(str(priorfile).encode()).hexdigest()[:16],category,priorfile.stat().st_size,sha(priorfile))
        store.record('reserved501-console-stream','other',64*1024,'PREPAID_BOUNDED_STREAM')
        store.record('reserved501-physics-marker','other',16*1024,'PREPAID_CONTROL_MARKER')
        state,before,ledger,rng,blob,expected=mods['law473'].root_inputs473(R)
        root=dict(state=state,before=before,ledger=ledger,RNG_digest=hashlib.sha256(blob).hexdigest())
        check(root['RNG_digest']==source['root_binding']['RNG_pickle_sha256'],'ROOT_RNG_PIN')
        tracepath=Path(source['trace']['path']);check(sha(tracepath)==source['trace']['sha256'],'472_TRACE_PIN')
        actual=[json.loads(s) for s in tracepath.read_text().splitlines()][22:]
        check(len(actual)==149 and sum(z['raw_ticks'] for z in actual)==594,'FACTUAL_SCOPE')
        afterpaths={x['step']:x['path'] for x in source['native_receipts'] if x['phase']=='after'}
        # All namespaces and source bindings are pinned before physics.
        graphproof=runtime.audit();functionproof=binding_gate(runtime)
        ctrlproof=control_gate(runtime,fixed,pace,state,before,actual[0],nodes.tolist())
        lifecycle=capture_lifecycle(runtime,D,binding)
        ownfixture=own_saved_gate(runtime,mods,ledger,fixed,own_history,R)
        # Full capture lifecycle restores its fake patch points; install once
        # for the real original ObserveMixin, no495 root/history qualification.
        registry=Registry495();registry.install(runtime)
        def writer(c):
            def put(name,value):
                check(Path(name).name==name,'DIRECT_NAME')
                return codec.writer(D/('direct501-'+name),value,kind='bundle' if '-bundle' in name else 'tick')
            return put
        install_model495(runtime,registry,writer,binding);codec.install()
        # Exercise actual graph aliases and full state/bytes codec under poison.
        sample=dict(state=copy.deepcopy(state),RNG_blob=blob,scalar=-0.,all_fields=['fixture'])
        mods['loss389_analyze'].save(D/'io501-pure-fixture.json',sample)
        check(mods['io481'].canonical(codec.read(D/'io501-pure-fixture.json'))==mods['io481'].canonical(sample),'REAL_GRAPH_CODEC_ROUNDTRIP')
        aliasproof=codec.audit();check(not poison,'PREFLIGHT_PHYSICS_CALL')
        semantic={v['path']:v['source_sha256'] for v in runtime.records.values()}
        oldsource=json.loads((R/'stage473/plan.json').read_text())
        for path,h in list(semantic.items()):
            if path in oldsource['semantic_sources']:check(h==oldsource['semantic_sources'][path],'ORIGINAL473_SOURCE_CHANGED:'+path)
        for path in list((G/'core').rglob('*.py'))+[G/'damage.py',G/'env_wrapper.py']:
            current=sha(path)
            if str(path) in oldsource['sources']:check(current==oldsource['sources'][str(path)],'ORIGINAL473_PHYSICS_SOURCE_CHANGED:'+str(path))
            semantic[str(path)]=current
        for f in ('run501.py','runtime501.py','static501.py','law501.py','io501.py','test_io501.py','envelope500.py','storage500.py','envelope500_contract.json','capture494.py','capture495.py','schema493.py','codegate498.py','preflight498.py'):
            semantic[str(G/'retry'/f)]=sha(G/'retry'/f)
        plan=dict(stage=501,deadline_utc=DEADLINE,semantic_sources=semantic,input_pins=inputpins,binding=binding,source_schema_manifest_sha256=inputpins[str(R/'stage501-source-private/source-schema-manifest-private.json')],caps=dict(worlds=4,holds=448,ticks=1792,CPU_s=600,wall_s=900,bytes=256*1024**2,files=2688,states=320),reservation='All1792ticks/448holds upper reserved before first world; no process resume/retry after marker. Per-call counters charge in RAM before dispatch; sparse immutable gate snapshots only, no uncapped budget rewrite stream.',source_scope='Original473 source preserved;435 factual future-memory drift remains diagnostic.417 projection,495 capture format only; no495C4 qualification.',root_RNG_digest=root['RNG_digest'],budget_path=str(R/'project-effective-budget-v495.json'),budget_sha256=inputpins[str(R/'project-effective-budget-v495.json')],prior_workload_charge_CPU_s=PRE_CPU,prior_workload_charge_wall_s=PRE_WALL)
        codec.save_receipt(D/'plan.json',plan)
        class Meter(mods['meter453'].Meter453):
            def __init__(self):
                self.charged_ticks=0;self.wrapper_slots=0;self.closed_worlds=0;self.allocator_calls=0;self.flushed=0;self.latest={};self.constructing=False;self.created_worlds=[]
                super().__init__(D)
            def persist(self):
                self.latest=dict(model=copy.deepcopy(self.b),holds=self.wrapper_slots,charged_ticks=self.charged_ticks,closed=self.closed_worlds,CPU_s=cpu(),wall_s=wall(),actual_actions=0,resets=0)
            def flush(self,tag):
                self.persist();self.flushed+=1;codec.save_receipt(D/f'budget501-{self.flushed}-{tag}.json',self.latest)
            def guard(self):
                guard();check(cpu()<580 and wall()<870,'CLEANUP_TIME_RESERVE');check(not self.nb['actions'] and not self.nb['resets'] and not self.allocator_calls,'NATIVE_ALLOCATOR_FORBIDDEN')
            def timers(self):pass
            def world(self,state,tag):
                self.guard();check(physical_started and self.b['worlds']<4 and not self.live,'WORLD_AUTH_CAP')
                self.constructing=True
                try:return super().world(state,tag)
                finally:self.constructing=False
            def step(self,m,a,tag):
                self.guard();check(self.charged_ticks+4<=1792 and self.wrapper_slots<448 and m in self.live,'HOLD_TICK_CAP')
                self.charged_ticks+=4;self.wrapper_slots+=1;self.persist()
                return mods['paired442_meter'].Meter.step(self,m,a,tag)
            def charge(self,*a):raise RuntimeError('501_NATIVE_FORBIDDEN')
            def begin_actual(self):raise RuntimeError('501_NATIVE_FORBIDDEN')
            def close(self,m):
                if m not in self.live:return
                stream=self.streams.get(id(m));m.close();w=m.world
                for body in list(w.bodies):w.DestroyBody(body)
                check(not w.bodies and not w.joints,'TEARDOWN_ZERO')
                self.live.remove(m);self.auth.pop(id(m),None);self.streams.pop(id(m),None);self.closed_worlds+=1
                if stream:stream.world=stream.ctrl=stream.child=None
                m.__dict__.clear();m.closed501=True;self.persist()
        meter=Meter();meter.qualification_passed=True
        # Permanently forbid native factories/allocators, not model Car physics.
        def forbidden(*a,**k):raise RuntimeError('501_NATIVE_OR_ALLOCATOR_FORBIDDEN')
        for module in runtime.modules.values():
            for key in ('make_env','allocate_current'):
                if hasattr(module,key):setattr(module,key,forbidden)
        static=dict(passed=True,graph=graphproof,functions=functionproof,control=ctrlproof,lifecycle=lifecycle,alias=aliasproof,own_fixture=ownfixture,physics_hits=0,source298_verified=True)
        codec.save_receipt(D/'static-private.json',static)
        for p,h in semantic.items():check(sha(p)==h,'PREPHYSICS_SOURCE_CHANGED')
        for p,h in inputpins.items():check(sha(p)==h,'PREPHYSICS_INPUT_CHANGED')
        check(shutil.disk_usage('/tmp').free>=768*1024**2 and shutil.disk_usage('/workspace').free>=528*1024**2,'DISK_PREFLIGHT')
        check(not poison,'ENTIRE_PREPARATION_PHYSICS_HIT');prep.__exit__(None,None,None);prep=None
        # Marker is pre-reserved16KiB, written once before ANY real allocation.
        marker=CONTROL/'PHYSICS_STARTED-private.json';data=json.dumps(dict(stage=501,once=True,plan=codec.physical_ref(D/'plan.json'),reserved_ticks=1792,reserved_holds=448,worlds=4,CPU_s=cpu(),wall_s=wall())).encode()
        check(len(data)<=16*1024 and not marker.exists(),'PHYSICS_MARKER')
        with marker.open('xb') as f:os.chmod(marker,0o600);f.write(data);f.flush();os.fsync(f.fileno())
        physical_started=True
        # Monitor every Box2D allocation, including constructor-failure cleanup.
        import Box2D
        original_world=Box2D.b2World
        def counted_world(*a,**k):
            check(meter.constructing and len(meter.created_worlds)<4,'UNDECLARED_WORLD_ALLOCATION')
            w=original_world(*a,**k);meter.created_worlds.append(w);return w
        Box2D.b2World=counted_world
        random_state,numpy_state=pickle.loads(blob)
        region=meter.model('501_SINGLE_FACTUAL_FIRST_SCREEN');region.__enter__()
        def branch(label,mode,limit):
            nonlocal live,pending_authority
            random.setstate(random_state);np.random.set_state(numpy_state)
            meter.capture_inputs(state,before,ledger,label+'_inputs',gate='501_REGISTERED_PRE23_'+mode)
            c=mods['observer435'].Child(meter,copy.deepcopy(state),copy.deepcopy(before),ledger,fixed,pace,label,'nominal',world_tag='501_'+mode);live=c
            check(mods['mechanism479'].physical_identity(mods['pilot420_backend'].snapshot(c.m))==mods['mechanism479'].physical_identity(state) and c.ctrl.memory()==before and mods['pilot420_backend'].rnghash()==root['RNG_digest'],'ROOT_RESTORE_EXACT')
            if mode!='factual':c.ctrl.policy.nodes=nodes.copy();c.ctrl.policy.nodes.setflags(write=False)
            else:c.ctrl.policy.nodes=original.copy();c.ctrl.policy.nodes.setflags(write=False)
            initial=mods['pilot420_backend'].snapshot(c.m);ownroot={**root,'state':initial};transitions=[];pending_authority={'label':label,'transitions':transitions};first=None;factual=FactualGate501(mods,fixed,ledger) if mode=='factual' else None
            scalar_stop=None;stop_before=None
            for index in range(limit):
                guard()
                if c.status!='ACTIVE':break
                sb=mods['pilot420_backend'].snapshot(c.m);mb=copy.deepcopy(c.ctrl.memory());lb=asdict(c.ledger);rh=mods['pilot420_backend'].rnghash()
                try:
                    if mode=='factual':
                        a=actual[index]
                        if a['step']==126:c.ctrl.policy.nodes=nodes.copy();c.ctrl.policy.nodes.setflags(write=False)
                        nominal=c.ctrl.act(c.m)
                        c.one('501_FACTUAL472_CALIBRATION',first_override=a['command'],prepared_nominal=nominal,prepared_before=mb)
                        check(len(c.rows)==index+1,'FACTUAL_ZERO_ROW')
                        details={'scope':'STORED_COMMAND_CALIBRATION_ONLY'}
                    else:details=candidate_one(c,arcs,nodes.tolist(),mods['signed417_executor'].canonical_projection)
                except Exception as exc:
                    from retry.envelope500 import EnvelopeStop
                    if isinstance(exc,EnvelopeStop) and str(exc)=='EMPTY_SET':
                        scalar_stop='EXACT_EMPTY_SET';stop_before=mb;pending_authority['unexecuted_nominal_stop']={'state':sb,'before':mb,'after':c.ctrl.memory(),'ledger':lb,'reason':scalar_stop};break
                    raise
                row=c.rows[-1];hold=c.capture_holds495[-1]
                transitions.append(dict(index=index+1,state_before=sb,memory_before=mb,ledger_before=lb,state_after=mods['pilot420_backend'].snapshot(c.m),memory_after=c.ctrl.memory(),ledger_after=asdict(c.ledger),row_digest=mods['io481'].canonical(row),scalar=details,RNG_digest=rh))
                authenticate_hold495(hold,binding);flags=compare_flags495(hold,hold,binding)
                check(flags['safe'] or bool(row['safety']),'DIRECT_UNREPORTED_UNSAFE')
                check(mods['pilot420_backend'].rnghash()==rh==root['RNG_digest'],'RNG_CHANGED')
                if mode=='factual':factual.one(c,a,receipt(afterpaths[a['step']]),nominal)
                if first is None:first=dict(row=copy.deepcopy(row),posts=copy.deepcopy(c.stream.posts),state=mods['pilot420_backend'].snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),RNG=rh)
                if (index+1)%32==0:print(json.dumps(dict(stage=501,label=label,holds=index+1,ticks=meter.charged_ticks,status=c.status,CPU_s=cpu(),wall_s=wall())),flush=True)
                if mode=='factual' and c.status!='ACTIVE' and index!=148:raise RuntimeError('501_FACTUAL_ENDED_EARLY')
                if scalar_stop:break
            own=own_history(c,ownroot,transitions,mods,stop_before=stop_before)
            packet=dict(label=label,mode=mode,status=c.status,error=c.error,scalar_stop=scalar_stop,actions=len(c.rows),raw_ticks=sum(f['predicted']['raw_ticks'] for f in c.rows),signature=c.signature(),post_signature=mods['io481'].canonical(c.stream.posts),first=first,holds=copy.deepcopy(c.capture_holds495),own=own,finish=None if c.finish_ticks is None else asdict(c.finish_ticks),safe=not any(f['safety'] for f in c.rows))
            if factual:
                check(c.status=='FINISHED' and c.ledger.done and len(c.rows)==149,'FACTUAL_FULL_OFFICIAL_FINISH')
                packet['factual']=factual.result();check(packet['factual']['passed'],'FACTUAL_GATE')
            c.dump(D);codec.save_receipt(D/(label+'-own-authority-private.json'),dict(transitions=transitions,own=own,scalar_stop=scalar_stop,unexecuted_nominal_stop=pending_authority.get('unexecuted_nominal_stop')))
            c.close();live=None;meter.flush(label);branches.append(packet)
            persisted={k:v for k,v in packet.items() if k!='holds'}
            persisted['capture_refs']=[dict(bundle_ref=h['bundle_ref'],decoded_hold_digest=mods['io481'].canonical(h)) for h in packet['holds']]
            persisted['capture_reconstruction']='CAPTURED_HOLD495_V1 original495._rebuild from authenticated bundle, immutable binding/header/wrapper; original exact logical digest above. No measurement omitted.'
            codec.save_receipt(D/(label+'-result-private.json'),persisted);pending_authority=None
            return packet
        fact=branch('D501_factual','factual',149)
        check(fact['factual']['passed'],'FACTUAL_GATE_BEFORE_CANDIDATE')
        # Isolate actual future objects from the candidate input/function globals.
        actual=None;afterpaths=None
        a=branch('D501_candidate_1','candidate',149)
        if a['scalar_stop'] or a['status']!='FINISHED' or not a['safe']:
            status='PACKAGE_REJECTED';outcome=dict(reason=a['scalar_stop'] or a['status'],candidate_actions=a['actions'],no_repeat_after_failed_candidate=True)
        else:
            b=branch('D501_candidate_2','candidate',149)
            check(a['signature']==b['signature'] and a['post_signature']==b['post_signature'],'COLD_REPEAT_MISMATCH')
            check(len(a['holds'])==len(b['holds']),'COLD_HOLD_COUNT')
            for x,y in zip(a['holds'],b['holds']):compare_repeat495(x,y,binding)
            held=branch('D501_candidate_held','held',1)
            check(held['first']==a['first'],'HELD_FIRST_MISMATCH');compare_repeat495(held['holds'][0],a['holds'][0],binding)
            upper_ticks=88+a['finish']['hi'] if 'hi' in a['finish'] else 88+a['finish']['upper']
            status='MODEL_SCREEN_PASS' if upper_ticks<=657 else 'NO_INFORMATION'
            outcome=dict(episode_upper_s=upper_ticks/50,required_upper_s=13.14,cold_exact=True,held_first_exact=True,model_only=True,actual_record_updated=False,target11_99_claimed=False)
        Box2D.b2World=original_world
    except BaseException as exc:
        status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc)
        if codec is not None and not codec.store.failed:
            try:
                if pending_authority is not None:codec.save_receipt(D/'incomplete-own-authority-private.json',pending_authority)
                codec.save_receipt(D/'stop-private.json',dict(error=error,traceback=traceback.format_exc(),physics_started=physical_started,no_retry_after_physics=True))
            except BaseException:pass
        print(json.dumps(dict(stage=501,status=status,error=error,physics_started=physical_started)),flush=True)
    finally:
        if prep is not None:prep.__exit__(None,None,None)
        if meter is not None:
            if live is not None and not live.closed:
                try:
                    if codec is not None and not codec.store.failed:live.dump(D)
                except BaseException:pass
                try:live.close()
                except BaseException as e:
                    error=(error or '')+';close:'+str(e)
            # Includes any partially failed constructor's captured Box2D world.
            for m in list(meter.live):
                try:meter.close(m)
                except BaseException as e:error=(error or '')+';teardown:'+str(e)
            for w in meter.created_worlds:
                for body in list(w.bodies):w.DestroyBody(body)
                check(not w.bodies and not w.joints,'ALL_CREATED_WORLD_TEARDOWN')
            if region is not None:region.__exit__(None,None,None)
        if 'original_world' in locals():Box2D.b2World=original_world
    guard()
    if codec is not None:
        codec.store.closing=True
        for p,h in inputpins.items():check(sha(p)==h,'INPUT_IMMUTABLE')
        if 'semantic' in locals():
            for p,h in semantic.items():check(sha(p)==h,'SOURCE_IMMUTABLE')
        if not codec.store.failed:
            # One full readback plus authenticated content/state references.
            try:
                for logical in list(codec.aliases):codec.read(logical)
                codec.audit()
            except BaseException as exc:
                status='TECHNICAL_STOP';error=(error or '')+';closing_readback:'+type(exc).__name__+':'+str(exc)
    final=dict(stage=501,status=status,error=error,outcome=outcome,static_passed=static.get('passed',False),physics_started=physical_started,worlds=0 if meter is None else meter.b['worlds'],confirmed_worlds=0 if meter is None else meter.b['confirmed_worlds'],closed_worlds=0 if meter is None else meter.closed_worlds,live_worlds=0 if meter is None else len(meter.live),actual_ticks=0 if meter is None else meter.b['ticks'],charged_ticks=0 if meter is None else meter.charged_ticks,holds=0 if meter is None else meter.wrapper_slots,created_Box2D_worlds=0 if meter is None else len(meter.created_worlds),branches=[{k:v for k,v in b.items() if k not in ('first','holds','factual')} for b in branches],factual_passed=bool(branches and branches[0].get('factual',{}).get('passed')),actual_action_reset_seed_allocator_HOLDOUT_SEALED=0,CPU_s=cpu(),wall_s=wall(),preparation_charge_CPU_s=PRE_CPU,preparation_charge_wall_s=PRE_WALL,storage={} if codec is None else codec.summary(),research_remaining=26027,reserve=84000,reserve_used=0,no_retry_after_physics=True)
    if codec is not None and not codec.store.failed:codec.save_receipt(D/'result-private.json',final)
    print(json.dumps(final),flush=True)
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':run()
