"""Bounded 264-control whole-finish optimization with certified prefix reuse."""
import datetime,json,os,signal,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.late568_model as base
import retry.handoff562_model as d
from retry.checkpoints574 import START,END,HORIZON,FIRST,LAST,clone,checkpoint_map,fd_ticks,same
from retry.wide574_math import SCALE,metric,empirical,signed,matrix,prefix_radii
from retry.causal574_rounding import solve,check,actual_aux
from retry.clip561_core import atomic_write,prefix_slacks,plain
from retry.durable568 import Journal,digest,inspect
from retry.geometry571 import active_component,component,layout
from retry.path569_design import project_all,capsule

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response574-private');PREV=Path('/workspace/haic-response573-private');rd=d.rd;sha=d.sha
class ReserveStop(Exception):pass

def load_checkpoint(cp,static):
    return dict(root=d.load_root(dict(cp['root_without_roads'],roads=static['root']['roads'])),visited=set(cp['visited']),tracker=d.FinishLineTracker(**cp['tracker']),elapsed=cp['elapsed'],global_raw=cp['global_raw'],progress=cp['progress'],launch=cp['launch'].copy(),tracking=cp['tracking'].copy())

class Study:
    def __init__(self):
        if (D/'STARTED.json').exists():raise RuntimeError('574_ALREADY_STARTED')
        self.contract=rd(G/'retry/wide574_contract.json');self.tests=rd(G/'retry/wide574_tests.json');self.design=rd(G/'retry/wide574_design.json');assert self.design['passed'] and self.tests['passed']==9 and self.tests['failed']==0
        sources=['retry/wide574_model.py','retry/wide574_math.py','retry/checkpoints574.py','retry/causal574_rounding.py','retry/wide574_design.py','tests/test_wide574.py','retry/rounding573.py','retry/geometry571.py','retry/path569_design.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES]
        self.contract.update(implementation_frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={p:sha(G/p) for p in sources},tests_sha256=sha(G/'retry/wide574_tests.json'),design_sha256=sha(G/'retry/wide574_design.json'),LP_time_limit_wall_s=30,BLAS_OMP_threads=1,preflight_and_test_CPU_wall_charge_s=5.)
        assert all(sha(G/p)==h for p,h in self.tests['source_sha256'].items());assert all(sha(Path(p))==h for p,h in self.contract['input_sha256'].items());atomic_write(G/'retry/wide574_contract.json',self.contract,True);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/wide574_contract.json')))
        self.cpu=time.process_time()-5.;self.wall=time.perf_counter()-5.;self.phases=[];self.linears=0;self.fd_completed=0;self.calibrations=0;self.proposals=0;self.restorations=0;self.geometry_queries=0;self.events=[];self.accepts=[];self.comparisons=[];self.checkpoint_checks=[];self.reuse=True;self.center_limit=2;self.known_components=set();self.observations=[];self.features=[]
        self.static=rd(base.INPUTS[1]);self.paths=rd(base.INPUTS[2]);self.ledger=rd(base.INPUTS[3]);self.tape=rd(PREV/'final-independent-tape-private.json');assert self.tape['exact'] and self.tape['checkpoint_exact'];self.commands={v['index']:np.asarray(v['action'],np.float32) for v in self.tape['commands']};self.fixed_rows=self.tape['rows'][:START];cached=rd(D/'initial-checkpoints-private.json');self.start=load_checkpoint(cached['35'],self.static);assert self.start['global_raw']==136 and self.start['tracking']==[3,160] and self.start['launch']==[55,384]
        self.seed_x=np.asarray([v for h in range(FIRST,LAST+1) for v in [float(self.commands[h][0]),float(self.commands[h][1]-self.commands[h][2])]]);assert len(self.seed_x)==264 and np.array_equal(self.seed_x,self.seed_x.astype(np.float32).astype(float));assert all(np.array_equal(self.actions(self.seed_x)[h],self.commands[h]) for h in range(FIRST,LAST+1))
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.journal=Journal(D/'raw-journal-private.jsonl');base.CAPS=self.contract['budgets'];base.TOTAL=self.contract['aggregate'];self.localphase=base.Phase(self,'local');self.checkphase=base.Phase(self,'checkpoint');self.initial= None
    def actions(self,x):
        assert len(x)==264
        return {FIRST+j:np.asarray([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(132)}
    def cost(self):
        v=base.Study.cost(self);v.pop('prior567_separate',None);v.update(linearizations=self.linears,FD_columns_completed=self.fd_completed,calibrations=self.calibrations,source_proposals=self.proposals,measured_error_recoveries=self.restorations,primitive_queries=self.geometry_queries,preflight_and_test_CPU_wall_charge_s=5.);return v
    def save_cost(self):atomic_write(G/'retry/wide574_cost.json',self.cost(),True)
    def guard(self,reserve=0):
        c=self.cost();active=next((p.bucket for p in self.phases if p.active),None)
        for k,limit in self.contract['aggregate'].items():
            if c['total'][k]+(reserve if k=='force' else 0)>limit:raise RuntimeError('AGGREGATE_CAP:'+k)
        for bucket,limits in self.contract['budgets'].items():
            for k,limit in limits.items():
                value=sum(r[k] for r in c['phases'] if r['bucket']==bucket)
                if value+(reserve if k=='force' and bucket==active else 0)>limit:raise RuntimeError('BUCKET_CAP:'+bucket+':'+k)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
    def reserve_guard(self):
        self.guard();c=self.cost()['total']
        if c['CPU_s']>4600 or c['wall_s']>5750:raise ReserveStop('FINAL_REPLAY_AND_AUDIT_RESERVE')
    def raw(self,state,a,index,k,phase,diagnostic=False):
        previous=state['progress'];row,reason=base.Study.raw(self,state,a,index,k,phase,diagnostic);phase.histories.clear()
        i=state['global_raw']-START-1
        if 'root_without_roads' in row and hasattr(self,'segIdx') and 0<=i<HORIZON:
            q=d.project(state['root'].center,self.paths['candidate'],previous);j=int(self.segIdx[i]);distance,_,u,_=capsule(np.asarray(state['root'].center),self.segA[i],self.segB[i]);s=self.paths['candidate']['arcs'][j]+float(np.clip(u,0,1))*self.paths['candidate']['ds'][j];s+=round((previous-s)/self.paths['candidate']['length'])*self.paths['candidate']['length'];row.update(active_segment=q['i'],frozen_segment_eligible=previous-5<=s<=previous+30,frozen_segment_distance=float(distance));self.journal.append('SOURCE_PATH_RECHECK',label=phase.label,global_raw=state['global_raw'],diagnostic=diagnostic,exact_path_distance=q['distance'],frozen_segment_eligible=row['frozen_segment_eligible'],frozen_segment_distance=float(distance))
        return row,reason
    def metric(self,rows):return metric(self,rows)
    def initial_center(self):
        state=load_checkpoint(self.tape['checkpoint'],self.static);rows=self.tape['rows'][START:].copy()
        with self.localphase.session('seed-single-postfinish-extension'):
            row,_=self.raw(state,self.commands[166],166,2,self.localphase,True);rows.append(row)
        assert state['global_raw']==END and len(rows)==HORIZON;center=self.metric(rows);center.update(x=self.seed_x.copy(),rows=rows,state=state,label='573independently-safe-plus-one-diagnostic-tick');assert center['physical_safe'] and center['times']['hull_finish']==rd(G/'retry/quant573_result.json')['actual_times']['hull_finish'];atomic_write(D/'initial-center-private.json',dict(x=center['x'],rows=rows,checkpoint=base.checkpoint(state),times=center['times']));self.initial=center;return center
    def frozen(self,center):
        previous=np.asarray([self.start['progress']]+[v['progress'] for v in center['rows'][:-1]]);idx,dist,*_=project_all(center['P'],previous,self.paths['candidate']);pts=np.asarray(self.paths['candidate']['points']);self.segIdx=idx;self.segA=pts[idx];self.segB=np.roll(pts,-1,axis=0)[idx];assert max(abs(dist-np.asarray([v['path_error'] for v in center['rows']])))<1e-8
    def prove_checkpoints(self,center):
        full=self.fixed_rows+center['rows']
        try:self.checkpoints,checks=checkpoint_map(self,full,base.checkpoint(center['state']))
        except NotImplementedError:
            if self.linears:raise ReserveStop('UNSUPPORTED_REUSE_NO_SECOND_CENTER')
            self.reuse=False;self.center_limit=1;self.checkpoints={35:clone(self.start)};checks=dict(prehold_checkpoints=1,unsupported_cache_proof=True,validated_common_start_only=True)
        with self.checkphase.session(f'checkpoint-proof-{self.linears+1}'):
            for hold,point in self.checkpoints.items():
                state=clone(point);identity=digest(base.checkpoint(point));self.journal.append('RESTORED_CHECKPOINT',hold=hold,center=center['label'],checkpoint_sha256=identity)
                row,reason=self.raw(state,self.actions(center['x'])[hold],hold,1,self.checkphase,True);expected=center['rows'][4*(hold-FIRST)]
                assert reason is None
                for key in ['before_root_without_roads','root_without_roads','forces','tracker','proposed_history','episode_before_s','episode_after_s','progress','margin','path_error','reference_overspeed','body','visited_count']:
                    if not same(row[key],expected[key]):raise RuntimeError('CHECKPOINT_NEXT_TICK_MISMATCH:'+str(hold)+':'+key)
                assert digest(base.checkpoint(point))==identity
        checks.update(source_next_tick_exact=True,reuse_enabled=self.reuse);self.checkpoint_checks.append(checks);atomic_write(D/f'checkpoints-{self.linears+1}-private.json',{str(h):base.checkpoint(s) for h,s in self.checkpoints.items()});return checks
    def geometry_query(self):
        self.geometry_queries+=1
        if self.geometry_queries>1200:raise RuntimeError('PRIMITIVE_QUERY_CAP1200')
    def prepare_features(self,center):
        self.features=[];self.vertex_layout=layout(d.load_root(dict(center['rows'][0]['root_without_roads'],roads=self.static['root']['roads'])))
        for i,row in enumerate(center['rows']):
            self.geometry_query();root=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));f=active_component(root,self.static);assert abs(f['gap']-row['margin'])<1e-8;f['raw']=i;self.features.append(f)
        for i,kind,poly,feature in sorted(self.known_components):
            if any(all(f[k]==v for k,v in [('raw',i),('kind',kind),('polygon',poly),('feature',feature)]) for f in self.features):continue
            self.geometry_query();root=d.load_root(dict(center['rows'][i]['root_without_roads'],roads=self.static['root']['roads']));f=component(root,self.static,kind,poly,feature);f['raw']=i;self.features.append(f)
    def local(self,x,label,center=None,start_hold=FIRST):
        offset=4*(start_hold-FIRST) if self.reuse else 0;state=clone(self.checkpoints[start_hold] if offset else self.start);rows=center['rows'][:offset].copy() if offset else [];commands=self.actions(x);start_id=digest(base.checkpoint(state));result=None
        with self.localphase.session(label):
            try:
                for raw_before in range(state['global_raw'],END):
                    h,k=divmod(raw_before,4);row,_=self.raw(state,commands[h+1],h+1,k+1,self.localphase,True);rows.append(row)
                result=self.metric(rows);result.update(x=x.copy(),rows=rows,state=state,label=label);return result
            finally:
                payload=dict(x=x,label=label,source_start_raw=START+offset,start_checkpoint_sha256=start_id,rows=rows if not label.startswith('FD-') else None,checkpoint=base.checkpoint(state),cost=self.cost())
                if result is not None:payload.update(times=result['times'],physical_safe=result['physical_safe'],violation_counts=result['violation_counts'])
                atomic_write(D/(label+'-private.json'),payload)
    def linearize(self,center):
        self.linears+=1;assert self.linears<=self.center_limit;N=264;H=HORIZON;V=center['V'].shape[1];linear=dict(J=np.zeros((10*H,N)),R=np.zeros((4*H,N)),O=np.zeros((H,N)),T=np.zeros(N),P=np.zeros((H,2,N)),V=np.zeros((H,V,2,N)));steps=[];unsafe=[];before_ticks=self.localphase.counter[0];before_cpu=time.process_time()
        for j,value in enumerate(center['x']):
            self.reserve_guard();hold=FIRST+j//2;h=1e-5 if j%2==0 else 1e-4;hi=float(np.float32(.4)) if j%2==0 else 1.;x=center['x'].copy();x[j]=float(np.float32(value+(h if value+h<=hi else -h)));delta=x[j]-value
            if delta==0:raise RuntimeError('FLOAT32_ZERO_FD')
            ev=self.local(x,f'FD-{self.linears}-{j:03d}',center,hold);self.fd_completed+=1;steps.append(delta);offset=4*(hold-FIRST)
            if ev['times']['hull_finish'] is None:raise RuntimeError('FD_FINISH_UNBRACKETED')
            fields=[('J','g',10),('R','ratios',4),('O','order',1),('P','P',1),('V','V',1)]
            column={}
            for key,field,mult in fields:
                if not np.array_equal(ev[field][:offset*mult],center[field][:offset*mult]):raise RuntimeError('FD_PREFIX_CAUSALITY_MISMATCH:'+key)
                derivative=(ev[field]-center[field])/delta;linear[key][...,j]=derivative;column[key]=derivative
            linear['T'][j]=(ev['times']['hull_finish']-center['times']['hull_finish'])/delta;column['T']=linear['T'][j]
            np.savez_compressed(D/f'FD-{self.linears}-{j:03d}-derivative-private.npz',**column,step=delta);os.chmod(D/f'FD-{self.linears}-{j:03d}-derivative-private.npz',0o600)
            if not ev['physical_safe']:unsafe.append(j)
            if (j+1)%8==0 or j==N-1:print(json.dumps(dict(stage='FD',center=self.linears,columns=j+1,source_ticks=self.localphase.counter[0]-before_ticks,CPU_s=time.process_time()-before_cpu,total=self.cost()['total'])),flush=True)
        actual_ticks=self.localphase.counter[0]-before_ticks;expected=fd_ticks() if self.reuse else N*H
        if actual_ticks!=expected:raise RuntimeError('FD_COST_ARITHMETIC_MISMATCH')
        self.last_fd_CPU=time.process_time()-before_cpu;np.savez(D/f'linear-{self.linears}-private.npz',**linear,steps=steps);os.chmod(D/f'linear-{self.linears}-private.npz',0o600);atomic_write(D/f'linear-{self.linears}-summary-private.json',dict(FD_source_ticks=actual_ticks,expected_ticks=expected,unsafe_probe_columns=unsafe,all_prefix_derivatives_exact_zero=True,CPU_s=self.last_fd_CPU))
        patterns=[]
        for n,sign in enumerate([1.,-1.]):
            x=center['x'].copy()
            for j,value in enumerate(x):
                delta=sign*(1 if j%2==0 else -1)*.05*SCALE[j];lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.)
                if not lo<=value+delta<=hi:delta=-delta
                x[j]=float(np.float32(value+delta))
            patterns.append(self.local(x,f'cal-{self.linears}-{n}'));self.calibrations+=1
        self.observations=patterns;env=empirical(center,linear,patterns);atomic_write(D/f'envelope-{self.linears}-private.json',env);return linear,env
    def problem(self,center,linear,env,rho,label):
        self.reserve_guard();p,detail=matrix(self,center,linear,env,self.features,self.vertex_layout,self.observations,rho);p['budget_guard']=self.reserve_guard;atomic_write(D/(label+'-matrix-summary-private.json'),detail)
        return p,detail
    def validate_nominal_counts(self,p,x,center,linear,env):
        z=(x-center['x'])/SCALE;groups=actual_aux(z,p['groups']);R=linear['R']*SCALE;pred=center['ratios']+R@z;ids=np.asarray([i-sum(np.asarray(center['labels'])!='path') for i in p['ratio_rows']],int);upper=pred[ids]+np.asarray(env['ratio'])[ids]*groups[(ids//4)//4];order=prefix_slacks(pred,*self.start['tracking'])
        return dict(exact_predicted_prefix_pass=bool(min(order)>=0),exact_predicted_nonexempt_upper_pass=bool(np.all(upper<=1.)),minimum_predicted_order_slack=float(min(order)),maximum_nonexempt_upper=float(max(upper)))
    def recover(self,center,linear,env,probe,case):
        self.restorations+=1;assert self.restorations<=4;self.observations.append(probe);new=empirical(center,linear,self.observations)
        for key in ['g','ratio','order','position']:env[key]=np.maximum(env[key],new[key])
        detail=dict(recovery=self.restorations,source_failure=case['failure'],added_component=False)
        if case['failure']=='FOOTPRINT':
            row=case['rows'][-1];i=row['global_raw_after']-START-1
            if row['margin']<=0:raise RuntimeError('UNSUPPORTED_NONPOSITIVE_GEOMETRY')
            root=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();f=active_component(root,self.static);assert abs(f['gap']-row['margin'])<1e-8;safe=d.load_root(dict(center['rows'][i]['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();feature=component(safe,self.static,f['kind'],f['polygon'],f['feature']);feature['raw']=i
            if not any(all(v[k]==feature[k] for k in ['raw','kind','polygon','feature']) for v in self.features):self.features.append(feature);detail['added_component']=True
            self.known_components.add((i,f['kind'],f['polygon'],f['feature']));detail.update(raw=row['global_raw_after'],kind=f['kind'],polygon=f['polygon'],feature=f['feature'],actual_margin=row['margin'])
        atomic_write(D/f'recovery-{self.restorations}-private.json',dict(detail=detail,envelope=env));return detail
    def strict_finish(self,x,label):
        state=clone(self.start);phase=base.Phase(self,'evaluation');rows=[];failure=None;commands=self.actions(x)
        with phase.session(label):
            try:
                for before in range(START,END):
                    h,k=divmod(before,4);row,reason=self.raw(state,commands[h+1],h+1,k+1,phase);rows.append(row)
                    if reason:failure=reason;break
                    if state['tracker'].finish_time_s is not None:break
                safe=failure is None and state['tracker'].finish_time_s is not None
                return dict(x=x.copy(),rows=rows,state=state,label=label,safe_finish=safe,failure=failure or (None if safe else 'NO_FINISH_IN_HORIZON'))
            finally:atomic_write(D/(label+'-private.json'),dict(x=x,rows=rows,checkpoint=base.checkpoint(state),failure=failure,cost=self.cost()))
    def verify_plan(self,case):
        state=d.Study.initial(self);phase=base.Phase(self,'verification');commands={h:a for h,a in self.commands.items() if h<FIRST};commands.update(self.actions(case['x']));expected=self.fixed_rows+case['rows'];actual=[]
        with phase.session('final-independent-new-full-tape'):
            for index in sorted(commands):
                for k in range(1,5):
                    row,reason=self.raw(state,commands[index],index,k,phase);actual.append(row)
                    if reason:raise RuntimeError('REPLAY_SAFETY:'+reason)
                    if state['tracker'].finish_time_s is not None:break
                if state['tracker'].finish_time_s is not None:break
        exact=len(actual)==len(expected) and all(same(a['root_without_roads'],b['root_without_roads']) and same(a['forces'],b['forces']) and a['proposed_history']==b['proposed_history'] and same(a['tracker'],b['tracker']) and a['episode_before_s']==b['episode_before_s'] and a['episode_after_s']==b['episode_after_s'] and a['global_raw_after']==b['global_raw_after'] and a['tracking_history_before']==b['tracking_history_before'] and a['launch_history_before']==b['launch_history_before'] for a,b in zip(actual,expected));cp=same(base.checkpoint(state),base.checkpoint(case['state']));atomic_write(D/'final-independent-tape-private.json',dict(rows=actual,commands=[dict(index=h,action=a) for h,a in sorted(commands.items())],checkpoint=base.checkpoint(state),exact=exact,checkpoint_exact=cp))
        if not exact or not cp:raise RuntimeError('FINAL_REPLAY_INTEGRITY')
        return dict(raw=len(actual),fullstate_force_history_tracker_exact=exact,checkpoint_exact=cp,official_candidate_raw=round((state['tracker'].finish_time_s-1.02)/.02),confirmation_raw=state['global_raw'])
    def run(self):
        result={};selected=None;working=None;verification=None;error=None;stop=None;seen=set();hard_float=False
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP574')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP574')));signal.setitimer(signal.ITIMER_PROF,4795);signal.setitimer(signal.ITIMER_REAL,5995)
        try:
            center=self.initial_center();working=center;working_raw=660
            for n in range(2):
                self.reserve_guard()
                if n>=self.center_limit:stop='SINGLE_CENTER_FALLBACK_COMPLETE';break
                required=(fd_ticks() if self.reuse else 264*HORIZON)+2*HORIZON+6*HORIZON+662
                if self.cost()['total']['ticks']+required>160000:stop='NEXT_CENTER_TICK_RESERVE';break
                if n and self.cost()['total']['CPU_s']+self.last_fd_CPU+300>4770:stop='NEXT_CENTER_CPU_RESERVE';break
                self.frozen(center);self.prove_checkpoints(center);self.prepare_features(center);linear,env=self.linearize(center);rho=.05;accepted=False;repair_stale=0;last_bad=None
                p,detail=self.problem(center,linear,env,rho,f'center-{self.linears}-conditional');tail=dict(p,bounds=p['bounds'].copy());tail['bounds'][:196]=0.;_,tail_meta=solve(tail);self.comparisons.append(dict(center=self.linears,tail_only=tail_meta,scope='Same fresh264 Jacobian/error model/control trust;tail-only holds133..166 free. Conditional model opportunities,not source gains/global bounds. Fixed controls have q=0;expanded uncertainty tubes need not be nested.'))
                for attempt in range(3):
                    if self.proposals>=6:stop='SOURCE_PAIR_LIMIT6';break
                    label=f'proposal-{self.linears}-{attempt}';p,detail=self.problem(center,linear,env,rho,label);x,meta=solve(p);self.comparisons[-1].setdefault('expanded',meta)
                    if x is None:
                        self.events.append(dict(label=label,source_evaluated=False,model=meta));stop=meta['stop'];hard_float=stop in ['QUANTIZED_JOINT_CHECK_FAILED','ROUNDING_OUTSIDE_CERTIFICATE','INVALID_QUANTIZER_OUTPUT','NONFINITE_SOLVER_OUTPUT'];break
                    counts=self.validate_nominal_counts(p,x,center,linear,env);meta['exact_predicted_counts']=counts
                    if not counts['exact_predicted_prefix_pass'] or not counts['exact_predicted_nonexempt_upper_pass']:stop='UNRESOLVED_EXACT_CLIP_ALGEBRA';hard_float=True;break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,label+'-diagnostic');case=self.strict_finish(x,label+'-strict');event=dict(label=label,source_evaluated=True,model=meta,strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],diagnostic_safe=probe['physical_safe'],diagnostic_violations=probe['violation_counts'],working_accept=False);self.events.append(event)
                    if case['safe_finish']:
                        exact=len(case['rows'])<=len(probe['rows']) and all(same(a['root_without_roads'],b['root_without_roads']) and same(a['forces'],b['forces']) and a['proposed_history']==b['proposed_history'] and same(a['tracker'],b['tracker']) and a['episode_after_s']==b['episode_after_s'] and a['global_raw_after']==b['global_raw_after'] and a['tracking_history_before']==b['tracking_history_before'] and a['launch_history_before']==b['launch_history_before'] for a,b in zip(case['rows'],probe['rows']));actual=self.metric(case['rows']);matched=actual['times']['hull_finish']==probe['times']['hull_finish'];assert exact and matched
                        raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-actual['times']['hull_finish'];event.update(actual_times=actual['times'],actual_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],official_finish_s=case['state']['tracker'].finish_time_s-1.02,strict_diagnostic_exact=exact,objective_same_command_exact=matched)
                        if actual['physical_safe'] and gain>=1e-6 and raw<=working_raw:
                            accepted=True;event['working_accept']=True;case['metrics']=actual;self.accepts.append(case);selected=case;working=actual;working_raw=raw;center=probe
                            if not center['physical_safe']:stop='POSTFINISH_DIAGNOSTIC_UNSAFE_STOP'
                        else:stop='SAFE_WHOLE_NONIMPROVEMENT'
                    else:
                        scales=np.asarray([.01 if v=='force' else 10. if v=='body' else 1. if v=='reference' else .1 for v in probe['labels']]);bad=max(0.,float(max(-probe['g']/scales)),float(max(-probe['order']/.01)));event['normalized_violation']=bad
                        if last_bad is not None:repair_stale=repair_stale+1 if bad>=.9*last_bad else 0
                        last_bad=bad
                        if attempt<2 and self.restorations<4:event['measured_error_recovery']=self.recover(center,linear,env,probe,case)
                        else:stop='BOUNDED_RECOVERY_COMPLETE'
                    atomic_write(D/(label+'-decision-private.json'),event);print(json.dumps(dict(stage='DECISION',**{k:v for k,v in event.items() if k not in ['model']})),flush=True)
                    if accepted or stop:break
                    if repair_stale>=2:stop='TWO_MEASURED_REPAIR_STAGNATIONS';break
                    if attempt>=1:rho=.025
                if stop or not accepted:stop=stop or 'THREE_ATTEMPTS_NO_ACCEPT';break
                del linear,env,p,tail
            stop=stop or 'TWO_CENTERS_COMPLETE'
        except ReserveStop as e:stop=str(e)
        except BaseException as e:
            error=type(e).__name__+':'+str(e);atomic_write(D/'ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
        finally:
            # No replay after unresolved quantization/integrity/domain error.
            if selected is not None and error is None and not hard_float:
                try:verification=self.verify_plan(selected)
                except BaseException as e:error='VERIFY:'+type(e).__name__+':'+str(e);atomic_write(D/'VERIFY_ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
            self.save_cost();self.journal.close();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            try:audit=inspect(D/'raw-journal-private.jsonl')
            except BaseException as e:audit=dict(valid=False,error=str(e))
            result.update(completed=error is None,error=error,stop_reason=stop,unresolved_float=hard_float,seed_times=self.initial['times'] if self.initial else None,final_working_times=working['times'] if working else None,safe_working_accepts=len(self.accepts),new_plan_independently_verified=verification is not None and error is None,official_promotion=bool(verification and error is None and verification['official_candidate_raw']<660),official_incumbent_candidate_raw=verification['official_candidate_raw'] if verification and error is None else 660,official_incumbent_finish_s=selected['state']['tracker'].finish_time_s-1.02 if verification and error is None else 13.199999999999807,independent_verification=verification,linearizations=self.linears,FD_columns=self.fd_completed,calibration_rollouts=self.calibrations,source_candidate_pairs=self.proposals,measured_error_recoveries=self.restorations,checkpoint_reuse=self.reuse,checkpoint_proofs=self.checkpoint_checks,conditional_comparisons=self.comparisons,events=self.events,cost=self.cost(),journal=audit,source_hashes_match=all(sha(G/p)==h for p,h in self.contract['source_sha256'].items()),source_and_actual_scope='Source command-plan only;Native/pixel/feedbacktransition/robustness unproven',new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0);atomic_write(G/'retry/wide574_result.json',result);print(json.dumps(plain(result),indent=2),flush=True)

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN574')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()
