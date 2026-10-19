"""Boundary-aware diagnostic sensitivities and strictly safe policy admission."""
import copy,datetime,json,math,signal,time,traceback
from contextlib import contextmanager
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from retry.clip561_core import atomic_write,plain,prefix_slacks
from retry.durable568 import Journal,digest,evaluate_force,guarded_tick,inspect
import retry.handoff562_model as d
import retry.structure537_control as policy
from retry.diagnose566 import station_point

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response568-private')
INPUTS=[Path('/workspace/haic-response565-private/final-tape-private.json'),Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response519-private/model-ledger-private.json'),G/'retry/late567_calibration_result.json',G/'retry/late567_baseline_result.json']
SOURCES=['retry/late568_model.py','retry/durable568.py','tests/test_durable568.py',*d.SOURCES]
rd=d.rd;sha=d.sha;SCALE=np.tile([.003,.03],20)
CAPS={'local':dict(ticks=30000,force=130000,geometry=35000,CPU_s=600,wall_s=900),'feedback':dict(ticks=90000,force=500000,geometry=120000,CPU_s=1100,wall_s=1400),'verification':dict(ticks=1200,force=5000,geometry=1300,CPU_s=35,wall_s=50)}
TOTAL=dict(ticks=121200,force=635000,geometry=156300,CPU_s=1800,wall_s=2400)
CASE=dict(ticks=20000,force=100000,geometry=25000,CPU_s=250,wall_s=350)

def body(root):
    return max(math.hypot(*d.hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels))
def physical_key(root):
    z=d.short(root);z['planar'].pop('steer');return digest(z)
def checkpoint(state):return d.Study.checkpoint(None,state)

class Phase:
    def __init__(self,s,bucket):
        self.s=s;self.bucket=bucket;self.limit=CASE if bucket=='feedback' else CAPS[bucket];self.counter=[0];self.force_seen=0;self.active=False;self.label='';self.cpu_s=self.wall_s=0.
        self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,body_checks=0,max_body=0.);self.histories={};self.pending=None;s.phases.append(self)
    def values(self):
        return dict(ticks=self.counter[0],force=self.force_seen,geometry=self.cost['geometry_checks'],CPU_s=self.cpu_s+(time.process_time()-self.cpu if self.active else 0),wall_s=self.wall_s+(time.perf_counter()-self.wall if self.active else 0),body_checks=self.cost['body_checks'],max_body=self.cost['max_body'])
    @contextmanager
    def session(self,label):
        assert not self.active;self.label=label;self.cpu=time.process_time();self.wall=time.perf_counter();self.active=True
        self.s.journal.append('CASE_STARTED',label=label,bucket=self.bucket,cost=self.s.cost())
        try:self.guard();yield self
        finally:
            self.cpu_s+=time.process_time()-self.cpu;self.wall_s+=time.perf_counter()-self.wall;self.active=False;self.s.save_cost();self.s.journal.append('CASE_FINISHED',label=label,cost=self.values())
    def guard(self,reserve=0):
        v=self.values()
        for k,cap in self.limit.items():
            if v[k]+(reserve if k=='force' else 0)>cap:raise RuntimeError('CASE_CAP:'+self.label+':'+k)
        self.s.guard(reserve)
    def evaluate(self,root,action,history,context,peak=1.059,clip=.1,check_clip=True):
        self.guard(reserve=4)
        def compute():self.force_seen+=4;return d.force_rows(root,action)
        result=evaluate_force(self.s.journal,d.short(root),action.tolist(),history,dict(label=self.label,bucket=self.bucket,**context),compute,peak,clip,check_clip)
        self.pending=dict(result,root_id=digest(d.short(root)),context=context,action=action.tolist());return result
    def seed_forecast(self,root,history,global_raw):
        linear=root.planar.linear;self.histories={id(linear):(linear,list(history))};self.forecast_base=list(history);self.forecast_raw=global_raw
    def force(self,root,action):
        key=id(root.planar.linear)
        if key not in self.histories:raise RuntimeError('FORECAST_HISTORY_LINEAGE_MISSING')
        linear,h=self.histories[key]
        if linear is not root.planar.linear:raise RuntimeError('FORECAST_HISTORY_OBJECT_ALIAS')
        result=self.evaluate(root,action,h,dict(mode='forecast',base_global_raw=self.forecast_raw,forecast_raw=(h[1]-self.forecast_base[1])//4))
        return result['forces']
    def tick(self,root,gas,brake,index,counter):
        self.guard()
        if counter is not self.counter or counter[0]>=self.limit['ticks']:raise RuntimeError('TICK_COUNTER_CAP_OR_ALIAS')
        p=self.pending
        if p is None or p['root_id']!=digest(d.short(root)) or [gas,brake]!=p['action'][1:]:raise RuntimeError('TICK_WITHOUT_EXACT_DURABLE_VERDICT')
        after=guarded_tick(self.s.journal,p,dict(label=self.label,**p['context']),lambda:d.source_tick(root,gas,brake,index,counter),body,d.short)
        self.cost['body_checks']+=1;self.cost['max_body']=max(self.cost['max_body'],body(after));linear=after.planar.linear;self.histories[id(linear)]=(linear,p['history']);return after
    def geometry(self,root):
        self.guard()
        if self.cost['geometry_checks']>=self.limit['geometry']:raise RuntimeError('GEOMETRY_CAP')
        self.cost['geometry_checks']+=1;return d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])

class Study:
    def __init__(self):
        D.mkdir(mode=0o700,exist_ok=False);self.tape,self.static,self.paths,self.ledger,old567,oldbaseline=map(rd,INPUTS);self.phases=[];self.cpu=time.process_time();self.wall=time.perf_counter();self.events=[];self.feedback_calls=0;self.proposals=0;self.linears=0;self.restorations=0;self.accepts=[]
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands']}
        row=self.tape['rows'][527];assert row['global_raw_after']==528
        visited=set(self.ledger['initial_visited'])
        for r in self.tape['rows'][:528]:
            for ids in r['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**row['tracker']),elapsed=row['episode_after_s'],global_raw=528,progress=row['progress'],launch=row['launch_history_before'].copy(),tracking=row['proposed_history'].copy())
        verifyid=digest(dict(root=row['root_without_roads'],tracker=row['tracker'],progress=row['progress'],tracking=self.start['tracking'],visited=sorted(visited)))
        assert verifyid==oldbaseline['start_checkpoint_sha256'] and self.start['tracking']==[64,1728]
        self.seed_x=np.array([v for i in range(133,153) for v in [float(self.commands[i][0]),float(self.commands[i][1]-self.commands[i][2])]])
        self.s900=station_point(self.paths['candidate'],900.);self.start_id=verifyid;self.fd_completed=0
        self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',question='Improve late s800-s900 recovery through unchanged feedback official finish. Preserve failed567 without rerun.',start='Reuse exact565raw528root/tracker/visited/clock,launch55/384,tracking64/1728;565seed variableholds133..152;fixed local134raw horizon529..662. Reuse saved baseline,no seed integration or selector replay.',instrumentation='Every raw including forecasts: fsynced hash-chained complete pre-force state/action/history identifiers,then fsynced force vectors/exact ratio>1 clipping counts/gate before any tick;fsynced pendingtick and aftertick body/domain;policyraw geometry/verdict durable. Six injected unit tests passed before source execution. Raw private,no transfers.',sensitivity='Fresh40float32one-sidedFD steer1e-5/pedal1e-4;flip sign only at declared control domain edge. Separate diagnostic rollouts record force/clip/geometry/reference/projection violations and continue ONLY within finite physical state/body<100/actiondomain. Unsafe probes cannot be policy incumbent. No FD shrink sweeps;no conclusion of directional infeasibility from a probe safety violation.',calibration='Two fixed opposite alternating-sign patterns normalized .05 (inward flip at control domain edges). Once:physical,ratio andprefix margins=2*(maxpositive predictionoptimism overtwo checks+propagatedfullfloat32ULP+4binary64eps). Empiricaltargets only;all exactpolicythresholds unchanged.',method='Frozen incumbent suffix derivative surrogate to134raw;after new safe feedback use actual suffix commands,fill only missing postfinish commands from original565. LP physical interior plus recomputed per-prefix rank-exemption branch (exact initial64/1728),scales steer.003/pedal.03,radius.5,range.125..5;total displacement<=1 normalized from seed. Elastic restoration permits bounded diagnostic numerical centers only if measured fixed-interior violation falls>=10%;otherwise halve radius;two nondecreasing restorations stop. RecomputeFD at each center. Time objective:continuous hull-origin official-center-plane interpolant;root-centerplane and fixedspatial900 diagnostics separate.',caps=dict(linearizations=4,FD_columns=160,calibration_checks=2,source_proposals=6,restoration_steps=4,actual_feedback_calls=4,safe_working_accepts=2),acceptance='Program and fresh unchanged537feedback globallysafe to official confirmation. Safe working update requires hullplane diagnostic gain>=1microsecond and no later officialcandidate raw. Wholepolicy promotion REQUIRES strictly earlier officialtracker candidate raw AND safefinish;rawties never called official gains. Two safe nonimprovements or two accepted prediction sign mismatches stop. No arbitrary s900-only promotion.',finish='Exact unchanged FinishLineTracker qualification/contacts/departure/forward/width/halfdepth;officialcandidate raw=round((finish_time-1.02)/.02);confirmationraw separately. Original551reference/exactclipcounts;force<=1.059,footprint>=.5,path<=3,referenceoverspeed<=4.85,projection;all model/forecastsbody<100. SourceTimeLimit1224 includes50warmup.',verification='Only NEW selected safe working/whole trajectory:one independent full command-tape replay from initialsource state,including exact565prefix528raw,compare all states/forces/contacts/history/tracker and finalcheckpoint. No new acceptedcandidate means no whole seed replay.',budgets=CAPS,aggregate=TOTAL,feedback_case=CASE,stop='Body/domain/integrity/durableIO/budget errors terminate study,with finallycostFIRST. Probe ordinary safetyviolations do not terminate derivative calculations. Duplicate/quantizedzero,no bracket,minradius,linearization/proposal/feedback/acceptance/stagnationcaps stop. No automatic retry after technical errors.',actual_cap=0,HOLDOUT=0,SEALED=0,new_seed_paid_other_environment=0,research_remaining=22758,reserve=84000,reserve_used=0,source_kernel_cap_unchanged=200000,private_inputs_sha256={str(p):sha(p) for p in INPUTS},source_sha256={p:sha(G/p) for p in SOURCES})
        atomic_write(G/'retry/late568_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/late568_contract.json'),source_ticks=0));self.journal=Journal(D/'raw-journal-private.jsonl');self.localphase=Phase(self,'local')
    def cost(self):
        rows=[dict(bucket=p.bucket,label=p.label,**p.values()) for p in self.phases]
        sums={k:sum(x[k] for x in rows) for k in ['ticks','force','geometry','body_checks']};sums.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall)
        return dict(total=sums,phases=rows,prior567_separate=dict(ticks=1224,CPU_s=14.497968429),research_remaining=22758,reserve=84000,reserve_used=0)
    def save_cost(self):atomic_write(G/'retry/late568_cost.json',self.cost(),True)
    def guard(self,reserve=0):
        c=self.cost()
        for k,limit in TOTAL.items():
            if c['total'][k]+(reserve if k=='force' else 0)>limit:raise RuntimeError('AGGREGATE_CAP:'+k)
        for name,limits in CAPS.items():
            vals={k:sum(x[k] for x in c['phases'] if x['bucket']==name) for k in limits}
            for k,limit in limits.items():
                if vals[k]+(reserve if k=='force' and self.phases[-1].bucket==name else 0)>limit:raise RuntimeError('BUCKET_CAP:'+name+':'+k)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
    def actions(self,x):
        return {133+j:np.asarray([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(20)}
    def raw(self,state,a,index,k,phase,diagnostic=False):
        if abs(float(a[0]))>float(np.float32(.4)) or any(not 0<=float(v)<=1 for v in a[1:]) or a[1]*a[2]!=0:raise RuntimeError('CONTROL_DOMAIN')
        root=replace(state['root'],planar=replace(state['root'].planar,steer=-float(a[0])));group='launch' if index<=24 else 'tracking';context=dict(mode='diagnostic-probe' if diagnostic else 'strict-policy',global_raw=state['global_raw'],index=index,raw=k)
        verdict=phase.evaluate(root,a,state[group],context,2.5 if group=='launch' else 1.059,.15 if group=='launch' else .1,group!='launch' or index>=24);phase.cost['force_evaluations']+=4
        row=dict(index=index,raw=k,action=a.tolist(),global_raw_before=state['global_raw'],episode_before_s=state['elapsed'],before_root_without_roads=d.short(root),forces=verdict['forces'],tracking_history_before=state['tracking'].copy(),launch_history_before=state['launch'].copy(),proposed_history=verdict['history'],pre_failure=verdict['gate'],diagnostic_probe=diagnostic)
        if verdict['gate'] and not diagnostic:return row,verdict['gate']
        after=phase.tick(root,float(a[1]),float(a[2]),self.index,phase.counter);state['root']=after;state[group]=verdict['history'];state['elapsed']+=.02;state['global_raw']+=1;previous=state['progress'];q=d.project(after.center,self.paths['candidate'],previous);state['progress']=q['s'];gap=phase.geometry(after);over=math.hypot(*after.planar.linear.velocity)-d.reference(state['progress'],self.paths['candidate'])[0];delta=state['progress']-previous;projection_limit=max(5.,2*math.dist(root.center,after.center))
        for ids in after.current_contacts:state['visited'].update(ids)
        pose,velocity=d.hull_pose(after);state['tracker'].update(pose,velocity,len(state['visited'])/len(self.static['track']),1.02+state['elapsed'])
        failures=[]
        if verdict['gate']:failures.append(verdict['gate'])
        for bad,name in [(gap<.5,'FOOTPRINT'),(q['distance']>3,'PATH'),(group=='tracking' and over>4.85,'REFERENCE'),(delta<-.5 or delta>projection_limit,'PROJECTION')]:
            if bad:failures.append(name)
        row.update(root_without_roads=d.short(after),episode_after_s=state['elapsed'],global_raw_after=state['global_raw'],progress=state['progress'],progress_delta=delta,projection_limit=projection_limit,margin=gap,path_error=q['distance'],reference_overspeed=over,body=body(after),visited_count=len(state['visited']),tracker=asdict(state['tracker']),post_failure=failures[0] if failures else None,all_failures=failures)
        self.journal.append('RAW_VERDICT',context=context,force_event=verdict['event'],history_after=state[group],failures=failures,policy_eligible=not diagnostic and not failures,progress=state['progress'],margin=gap,path_error=q['distance'],reference_overspeed=over)
        return row,failures[0] if failures else None
    def metric(self,rows):
        g=[];labels=[];ratios=[];roots=[self.start['root']];progress=self.start['progress']
        for row in rows:
            root=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));delta=row['progress']-progress;lim=max(5.,2*math.dist(roots[-1].center,root.center));roots.append(root);progress=row['progress']
            vals=[row['margin']-.5,3-row['path_error'],4.85-row['reference_overspeed'],*[1.059-f['ratio'] for f in row['forces']],100-row['body'],delta+.5,lim-delta]
            g.extend(vals);labels.extend(['footprint','path','reference']+['force']*4+['body','projection','projection']);ratios.extend(f['ratio'] for f in row['forces'])
        order=prefix_slacks(ratios,*self.start['tracking']);times={};tracker=self.start['tracker']
        for name,point,normal,use_hull in [('hull_finish',tracker.center,tracker.forward,True),('center_finish',tracker.center,tracker.forward,False),('s900',*self.s900,False)]:
            signed=[sum((p[j]-point[j])*normal[j] for j in range(2)) for p in [d.hull_pose(r)[0] if use_hull else r.center for r in roots]];hit=None
            for k in range(1,len(roots)):
                if signed[k-1]<0<=signed[k]:
                    f=-signed[k-1]/(signed[k]-signed[k-1]);hit=.02*(528+k-1+f);break
            times[name]=hit
        safe=all(not r.get('pre_failure') and not r.get('post_failure') for r in rows) and min(g)>=0 and min(order)>=0
        return dict(g=np.array(g),labels=labels,ratios=np.array(ratios),order=order,times=times,physical_safe=bool(safe),violation_counts={key:sum(key in r.get('all_failures',[r.get('pre_failure'),r.get('post_failure')]) for r in rows) for key in ['FORCE','CLIP_HISTORY','FOOTPRINT','PATH','REFERENCE','PROJECTION']})
    def local(self,x,label,tail):
        state=copy.deepcopy(self.start);rows=[];tape={**tail,**self.actions(x)}
        with self.localphase.session(label) as phase:
            try:
                for offset in range(134):
                    index,k=divmod(528+offset,4);row,_=self.raw(state,tape[index+1],index+1,k+1,phase,True);rows.append(row)
                metrics=self.metric(rows);metrics.update(x=x.copy(),label=label,rows=rows,state=state);return metrics
            finally:
                value=dict(label=label,x=x,rows=rows if not label.startswith('FD') else None,checkpoint=checkpoint(state),cost=self.cost())
                if 'metrics' in locals():value.update({key:metrics[key] for key in ['g','labels','ratios','order','times','physical_safe','violation_counts']})
                atomic_write(D/(label+'-private.json'),value)
    def strict_program(self,x,label):
        state=copy.deepcopy(self.start);rows=[];acts=self.actions(x)
        with self.localphase.session(label) as phase:
            for index in range(133,153):
                for k in range(1,5):
                    row,reason=self.raw(state,acts[index],index,k,phase);rows.append(row)
                    if reason:return dict(safe=False,reason=reason,rows=rows,state=state)
        return dict(safe=True,rows=rows,state=state)
    def feedback(self,program,label):
        self.feedback_calls+=1;assert self.feedback_calls<=4;state=copy.deepcopy(program['state']);phase=Phase(self,'feedback');rows=[];commands=[];failure=None;ot,of=policy.tick,policy.force_rows
        with phase.session(label):
            try:
                for index in range(153,368):
                    phase.seed_forecast(state['root'],state['tracking'],state['global_raw']);geometry=policy.geometry_context(self.static,CASE['geometry']);policy.tick=phase.tick;policy.force_rows=phase.force
                    try:action,detail=policy.choose(state['root'],self.paths['candidate'],self.paths['backup'],state['progress'],phase.counter,phase.cost,CASE['ticks'],history=tuple(state['tracking']),geometry=geometry)
                    finally:policy.tick,policy.force_rows=ot,of
                    if action is None:failure='NO_ADMISSIBLE_ACTION';break
                    if not detail['final_recertified'] or not next(r for r in detail['reports'] if r['mode']=='FINAL')['ok']:raise RuntimeError('FINAL_CERTIFICATION_INTEGRITY')
                    commands.append(dict(index=index,action=action.tolist(),detail=detail))
                    for k in range(1,5):
                        row,reason=self.raw(state,action,index,k,phase);rows.append(row)
                        if reason:failure=reason;break
                        if state['tracker'].finish_time_s is not None:break
                        if 50+state['global_raw']>=1224:failure='SOURCE_TIME_LIMIT';break
                    self.save_cost()
                    if failure or state['tracker'].finish_time_s is not None:break
                safe=failure is None and state['tracker'].finish_time_s is not None
                return dict(safe_finish=safe,failure=failure or (None if safe else 'POLICY_LIMIT'),state=state,rows=rows,commands=commands,label=label)
            finally:atomic_write(D/(label+'-private.json'),dict(checkpoint=checkpoint(state),rows=rows,commands=commands,failure=failure,cost=self.cost()))
    def violation(self,r):
        scale=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in r['labels']]);return max(0.,float(max((self.gmargin-r['g'])/scale)),float(max((self.omargin-r['order'])/.01)))
    def linearize(self,center,tail):
        self.linears+=1;assert self.linears<=4;J=[];R=[];O=[];T=[];steps=[];unsafe=[]
        for j,v in enumerate(center['x']):
            h=1e-5 if j%2==0 else 1e-4;upper=float(np.float32(.4)) if j%2==0 else 1.;h=h if v+h<=upper else -h;x=center['x'].copy();x[j]=float(np.float32(v+h));step=x[j]-v
            if step==0:raise RuntimeError('FLOAT32_ZERO_FD')
            ev=self.local(x,f'FD-{self.linears:02d}-{j:02d}',tail)
            self.fd_completed+=1
            if ev['times']['hull_finish'] is None:raise RuntimeError('DIAGNOSTIC_FINISH_PLANE_UNBRACKETED')
            J.append((ev['g']-center['g'])/step);R.append((ev['ratios']-center['ratios'])/step);O.append((ev['order']-center['order'])/step);T.append((ev['times']['hull_finish']-center['times']['hull_finish'])/step);steps.append(step)
            if not ev['physical_safe']:unsafe.append(j)
        result=dict(J=np.array(J).T,R=np.array(R).T,O=np.array(O).T,T=np.array(T),steps=steps,unsafe_probe_columns=unsafe)
        atomic_write(D/f'linearization-{self.linears:02d}-private.json',result);return result
    def calibrate(self,seed,linear,tail):
        errors=[];oerrors=[];rerrors=[];details=[]
        for n,sign in enumerate([1.,-1.]):
            x=seed['x'].copy()
            for j,v in enumerate(x):
                delta=sign*(1 if j%2==0 else -1)*.05*SCALE[j];lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.)
                if not lo<=v+delta<=hi:delta=-delta
                x[j]=float(np.float32(v+delta))
            ev=self.local(x,'calibration-'+str(n),tail);dx=x-seed['x'];errors.append(np.maximum(0,seed['g']+linear['J']@dx-ev['g']));oerrors.append(np.maximum(0,seed['order']+linear['O']@dx-ev['order']));rerrors.append(np.maximum(0,ev['ratios']-seed['ratios']-linear['R']@dx));details.append(dict(label=ev['label'],physical_safe=ev['physical_safe'],violations=ev['violation_counts'],times=ev['times']))
        ulp=np.array([abs(float(np.spacing(np.float32(v)))) for v in seed['x']]);floor=4*np.finfo(float).eps
        self.gmargin=2*(np.max(errors,axis=0)+abs(linear['J'])@ulp+floor);self.omargin=2*(np.max(oerrors,axis=0)+abs(linear['O'])@ulp+floor);self.rmargin=2*(np.max(rerrors,axis=0)+abs(linear['R'])@ulp+floor)
        atomic_write(D/'frozen-interior-private.json',dict(physical=self.gmargin,prefix=self.omargin,ratio=self.rmargin,details=details));return dict(details=details,physical_max_by_label={label:float(max(self.gmargin[np.array(seed['labels'])==label])) for label in set(seed['labels'])},prefix_max=float(max(self.omargin)),ratio_max=float(max(self.rmargin)),sha256=sha(D/'frozen-interior-private.json'))
    def solve(self,center,linear,rho,restore,working):
        J=linear['J']*SCALE;R=linear['R']*SCALE;T=linear['T']*SCALE;cm={}
        for raw,m in enumerate(self.omargin):
            n=4*(raw+1);k=(1728+n)//10-64;rank=np.argsort(-center['ratios'][:n],kind='stable')
            for i in rank[max(0,k):]:cm[int(i)]=max(cm.get(int(i),0),float(m))
        ids=np.array(sorted(cm),int);A=np.vstack([-J,R[ids]]);b=np.r_[center['g']-self.gmargin,1-np.array([cm[int(i)] for i in ids])-center['ratios'][ids]];elastic=np.r_[[.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in center['labels']],np.full(len(ids),.01)]
        bounds=[]
        for j,v in enumerate(center['x']):
            lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(v-self.seed_x[j])/SCALE[j];radius=rho*.5 if restore else rho;bounds.append((max(-radius,-1-offset,(lo-v)/SCALE[j]),min(radius,1-offset,(hi-v)/SCALE[j])))
        if any(lo>hi for lo,hi in bounds):return None,dict(reason='EMPTY_TRUST_INTERSECTION')
        el=linprog(np.r_[np.zeros(40),1.],A_ub=np.c_[A,-elastic],b_ub=b,bounds=bounds+[(0.,None)],method='highs')
        if not el.success:return None,dict(reason='ELASTIC_LP_FAILED',status=int(el.status))
        eta=float(el.x[-1]);meta=dict(eta=eta,restoration=restore,rank_constrained_samples=len(ids))
        if eta>1e-8:
            # A bounded numerical restoration probe, never a policy admission.
            z=el.x[:40];meta['elastic_diagnostic_only']=True
        else:
            lp=linprog(T,A_ub=A,b_ub=b,bounds=bounds,method='highs')
            if not lp.success:return None,dict(meta,reason='TIME_LP_FAILED')
            z=lp.x;meta['elastic_diagnostic_only']=False
        x=(center['x']+SCALE*z).astype(np.float32).astype(float);meta.update(predicted_hull_finish=center['times']['hull_finish']+float(T@((x-center['x'])/SCALE)),normalized_step=float(max(abs((x-center['x'])/SCALE))));return x,meta
    def verify(self,case):
        phase=Phase(self,'verification');initial=d.Study.initial(self);tape={i:a for i,a in self.commands.items() if i<=132};tape.update(self.actions(case['x']));tape.update({q['index']:np.asarray(q['action'],np.float32) for q in case['feedback']['commands']});expected=self.tape['rows'][:528]+case['program']['rows']+case['feedback']['rows'];actual=[]
        with phase.session('independent-full-tape'):
            for index in sorted(tape):
                for k in range(1,5):
                    row,reason=self.raw(initial,tape[index],index,k,phase);actual.append(row)
                    if reason:raise RuntimeError('INDEPENDENT_REPLAY_SAFETY:'+reason)
                    if initial['tracker'].finish_time_s is not None:break
                if initial['tracker'].finish_time_s is not None:break
        same=len(expected)==len(actual) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(actual,expected));cp=d.canonical(checkpoint(initial))==d.canonical(checkpoint(case['feedback']['state']))
        atomic_write(D/'verified-final-tape-private.json',dict(rows=actual,commands=[dict(index=i,action=a.tolist()) for i,a in sorted(tape.items())],checkpoint=checkpoint(initial),same=same,checkpoint_exact=cp))
        if not same or not cp:raise RuntimeError('INDEPENDENT_REPLAY_INTEGRITY')
        return dict(raw=len(actual),fullstate_force_history_tracker_exact=same,checkpoint_exact=cp,official_candidate_raw=round((initial['tracker'].finish_time_s-1.02)/.02),confirmation_raw=initial['global_raw'])
    def run(self):
        result={};error=None;stop=None;working=None;whole=None;cal=None;verification=None;rho=.5;stale=nonimproving=mismatch=0;seen=set()
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP568')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP568')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s'])
        try:
            tail={i:a for i,a in self.commands.items() if i>=153};seed=self.metric(self.tape['rows'][528:]);seed.update(x=self.seed_x.copy(),label='saved565seed',rows=self.tape['rows'][528:]);assert seed['physical_safe'] and all(seed['times'].values());center=working=seed;working_raw=661;restore=False;linear=self.linearize(center,tail);cal=self.calibrate(seed,linear,tail)
            for iteration in range(4):
                if iteration:linear=self.linearize(center,tail)
                restore=self.violation(center)>1e-8
                if restore:self.restorations+=1
                if self.restorations>4:stop='RESTORATION_LIMIT';break
                x,meta=self.solve(center,linear,rho,restore,working)
                if x is None:stop=meta['reason'];self.events.append(meta);break
                if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_QUANTIZED_ZERO';break
                seen.add(x.tobytes());self.proposals+=1;trial=self.local(x,f'proposal-{iteration:02d}',tail);oldvi=self.violation(center);newvi=self.violation(trial);event=dict(iteration=iteration,LP=meta,old_interior_violation=oldvi,new_interior_violation=newvi,local_physical_safe=trial['physical_safe'],local_times=trial['times'],probe_violations=trial['violation_counts'],feedback_called=False,working_accept=False,whole_promotion=False)
                if trial['physical_safe'] and newvi<=1e-8 and not meta['elastic_diagnostic_only']:
                    program=self.strict_program(x,f'candidate-{iteration:02d}-program')
                    if program['safe']:
                        fb=self.feedback(program,f'candidate-{iteration:02d}-feedback');event['feedback_called']=True;event['safe_finish']=fb['safe_finish'];event['feedback_failure']=fb['failure']
                        if fb['safe_finish']:
                            actual=self.metric(program['rows']+fb['rows']);candidate_raw=round((fb['state']['tracker'].finish_time_s-1.02)/.02);event.update(actual_times=actual['times'],official_candidate_raw=candidate_raw,confirmation_raw=fb['state']['global_raw'],official_finish_s=fb['state']['tracker'].finish_time_s-1.02)
                            gain=working['times']['hull_finish']-actual['times']['hull_finish'];accepted=actual['physical_safe'] and candidate_raw<=working_raw and gain>=1e-6
                            if accepted:
                                case=dict(x=x.copy(),program=program,feedback=fb,metrics=actual);working=actual;working.update(x=x.copy(),label=f'accepted-{iteration:02d}');working_raw=candidate_raw;self.accepts.append(case);event['working_accept']=True;event['diagnostic_gain_ms']=1000*gain;nonimproving=0;mismatch+=int(meta['predicted_hull_finish']>=center['times']['hull_finish'])
                                if candidate_raw<661 and (whole is None or candidate_raw<round((whole['feedback']['state']['tracker'].finish_time_s-1.02)/.02)):whole=case;event['whole_promotion']=True
                                tail={i:a for i,a in self.commands.items() if i>=153};tail.update({q['index']:np.asarray(q['action'],np.float32) for q in fb['commands']});center=self.local(x,f'refresh-{iteration:02d}',tail);stale=0
                            else:nonimproving+=1
                        else:nonimproving+=1
                    else:event['program_failure']=program['reason'];nonimproving+=1
                self.events.append(event);atomic_write(D/f'decision-{iteration:02d}-private.json',event)
                if len(self.accepts)>=2:stop='TWO_SAFE_WORKING_ACCEPTS';break
                if nonimproving>=2:stop='TWO_POLICY_NONIMPROVEMENTS';break
                if mismatch>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES';break
                if self.feedback_calls>=4:stop='FEEDBACK_LIMIT';break
                if event['working_accept']:continue
                if newvi<oldvi*.9 or (oldvi==0 and newvi==0):center=trial;stale=0
                else:
                    stale+=1;rho*=.5
                    if stale>=2:stop='TWO_NONDECREASING_RESTORATIONS';break
                    if rho<.125:stop='MIN_TRUST_RADIUS';break
            if stop is None:stop='LINEARIZATION_LIMIT4'
            selected=whole or (self.accepts[-1] if self.accepts else None)
            if selected is not None:verification=self.verify(selected)
            result.update(completed=True,stop_reason=stop,calibration=cal,seed_times=seed['times'],final_working_times=working['times'],safe_working_accepts=len(self.accepts),official_whole_promotion=whole is not None,official_incumbent_candidate_raw=round((whole['feedback']['state']['tracker'].finish_time_s-1.02)/.02) if whole else 661,official_incumbent_finish_s=whole['feedback']['state']['tracker'].finish_time_s-1.02 if whole else 13.219999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events)
        except BaseException as e:
            error=type(e).__name__+':'+str(e);atomic_write(D/'ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True);result.update(completed=False,error=error,stop_reason=stop,events=self.events,calibration=cal,safe_working_accepts=len(self.accepts))
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.save_cost();self.journal.close()
            try:audit=inspect(D/'raw-journal-private.jsonl')
            except BaseException as audit_error:audit=dict(valid=False,error=str(audit_error))
            atomic_write(G/'retry/late568_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/late568_contract.json'),private_raw_uploaded=False,tests=dict(failure_injection_passed=6,source_ticks=0)),True)
            result.update(error=error,cost=self.cost(),linearizations=self.linears,FD_columns=self.fd_completed,source_proposals=self.proposals,restoration_steps=self.restorations,actual_feedback_calls=self.feedback_calls,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/late568_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**k):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()
