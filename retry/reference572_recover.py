"""Resume the interrupted 572 contract without repeating completed source ticks."""
import copy,datetime,json,math,os,signal,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.reference572_model as original
from retry.reference572_model import G,D,OLD,base,d,rd,sha,SCALE,CAPS,TOTAL,vertices,layout
from retry.durable568 import Journal,digest,inspect
from retry.clip561_core import atomic_write,plain

class Study(original.Study):
    def __init__(self):
        assert D.is_dir() and (G/'retry/reference572_diagnosis.json').exists()
        self.tape,self.static,self.paths,self.ledger=map(rd,base.INPUTS[:4]);self.cpu=time.process_time();self.wall=time.perf_counter();self.phases=[];self.events=[];self.accepts=[];self.proposals=0;self.linears=0;self.fd_completed=0;self.calibrations=0;self.evaluations=0;self.restorations=0;self.geometry_queries=0
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};r=self.tape['rows'][527];visited=set(self.ledger['initial_visited'])
        for row in self.tape['rows'][:528]:
            for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**r['tracker']),elapsed=r['episode_after_s'],global_raw=528,progress=r['progress'],launch=r['launch_history_before'].copy(),tracking=r['proposed_history'].copy());self.s900=base.station_point(self.paths['candidate'],900.)
        self.incumbent=rd(OLD/'proposal-4-0-diagnostic-private.json');self.seed_x=np.asarray(self.incumbent['x']);roots=[d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads'])) for row in self.incumbent['rows']];self.initialV=np.stack([vertices(root) for root in roots]);self.vertex_layout=layout(roots[0]);self.start_id=digest(dict(root=r['root_without_roads'],tracker=r['tracker'],progress=r['progress'],tracking=self.start['tracking'],visited=sorted(visited)));assert self.start_id==rd(G/'retry/late567_baseline_result.json')['start_checkpoint_sha256']
        self.floor={};self.known_components=set();self.observations=[];self.features=[];self.sensitivity_summaries=[]
        for path in sorted(OLD.glob('*-support-private.json')):
            value=rd(path)
            for k,v in zip(value['keys'],value['error_coefficients']):self.floor[k]=max(self.floor.get(k,0),v)
            for f in value['features']:self.known_components.add((f['raw'],f['kind'],f['polygon'],f['feature']))
        self.diagnosis=rd(G/'retry/reference572_diagnosis.json');None

        self.contract=rd(G/'retry/reference572_contract.json');assert all(sha(G/p)==h for p,h in self.contract['source_sha256'].items())
        assert not (D/'RECOVERY_STARTED.json').exists()
        self.old_audit=inspect(D/'raw-journal-private.jsonl');self.cache_events={};label=None
        for line in (D/'raw-journal-private.jsonl').open():
            row=json.loads(line)
            if row['kind']=='CASE_STARTED':label=row['label']
            if row['kind'] in ['BEFORE_FORCE','FORCE_VERDICT','AFTER_TICK','RAW_VERDICT']:
                self.cache_events.setdefault(label,[]).append(row)
        prior=rd(G/'retry/reference572_cost.json');atomic_write(D/'pre-recovery-cost-private.json',prior)
        self.cpu=time.process_time()-500.;self.wall=time.perf_counter()-500.
        for entry in prior['phases']+[dict(bucket='verification',label='interrupted-independent-prefix',ticks=489,force=1956,geometry=489,body_checks=489,max_body=0,CPU_s=25.,wall_s=25.)]:
            ph=base.Phase(self,entry['bucket']);ph.label=entry['label'];ph.counter[0]=entry['ticks'];ph.force_seen=entry['force'];ph.cost.update(geometry_checks=entry['geometry'],body_checks=entry['body_checks'],max_body=entry['max_body']);ph.cpu_s=entry['CPU_s'];ph.wall_s=entry['wall_s']
        self.journal=Journal(D/'recovery-raw-journal-private.jsonl');self.localphase=base.Phase(self,'local')
        self.linears=1;self.fd_completed=68;self.calibrations=2;self.proposals=1;self.evaluations=1;self.geometry_queries=prior['primitive_geometry_queries']
        event=rd(D/'proposal-0-0-decision-private.json');self.events=[event];case=rd(D/'proposal-0-0-strict-finish-private.json');case['state']=self.load_checkpoint(case['checkpoint']);case['x']=np.asarray(case['x']);case['metrics']=self.metric(case['rows']);self.accepts=[case];self.sensitivity_summaries=[rd(D/'sensitivity-1-private.json')]
        for f in rd(D/'proposal-0-0-support-private.json')['features']:self.known_components.add((f['raw'],f['kind'],f['polygon'],f['feature']))
        sup=rd(D/'proposal-0-0-support-private.json');self.floor.update(dict(zip(sup['keys'],sup['error_coefficients'])))
        atomic_write(D/'RECOVERY_STARTED.json',dict(original_contract_sha256=sha(G/'retry/reference572_contract.json'),recovery_source_sha256=sha(G/'retry/reference572_recover.py'),old_audit=self.old_audit,actual_native=0,CPU_wall_historical_charge=500.,verification_historical_charge=25.,exact_prior_CPU_unknown=True,prior_CPU_lower=prior['total']['CPU_s'],note='Conservative budget charges, not recovered measurements. Historical verification last journal timestamp minus error timestamp 13.923s;25s charged with extra termination allowance. Original aggregate and bucket ceilings unchanged.'))
    def load_checkpoint(self,cp):
        return dict(root=d.load_root(dict(cp['root_without_roads'],roads=self.static['root']['roads'])),visited=set(cp['visited']),tracker=d.FinishLineTracker(**cp['tracker']),elapsed=cp['elapsed'],global_raw=cp['global_raw'],progress=cp['progress'],launch=cp['launch'].copy(),tracking=cp['tracking'].copy())
    def recover_rows(self,label,state):
        rows=[];pending={}
        for ev in self.cache_events.get(label,[]):
            kind=ev['kind']
            if kind=='BEFORE_FORCE':pending=dict(before=ev)
            elif kind=='FORCE_VERDICT':pending['force']=ev
            elif kind=='AFTER_TICK':pending['after']=ev
            elif kind=='RAW_VERDICT':
                self.hydrate_row(state,pending,rows,ev);pending={}
        if 'after' in pending:self.hydrate_row(state,pending,rows,None)
        return rows
    def hydrate_row(self,state,p,rows,saved):
        before=p['before'];f=p['force'];after=d.load_root(dict(p['after']['root'],roads=self.static['root']['roads']));ctx=before['context'];index=ctx['index'];group='launch' if index<=24 else 'tracking';previous=state['progress'];q=d.project(after.center,self.paths['candidate'],previous);gap=saved['margin'] if saved else self.localphase.geometry(after);over=saved['reference_overspeed'] if saved else math.hypot(*after.planar.linear.velocity)-d.reference(q['s'],self.paths['candidate'])[0];delta=q['s']-previous;lim=max(5.,2*math.dist(state['root'].center,after.center));row=dict(index=index,raw=ctx['raw'],action=before['action'],global_raw_before=state['global_raw'],episode_before_s=state['elapsed'],before_root_without_roads=before['root'],forces=f['forces'],tracking_history_before=state['tracking'].copy(),launch_history_before=state['launch'].copy(),proposed_history=f['proposed_history'],pre_failure=f['gate'],diagnostic_probe=ctx['mode']=='diagnostic-probe')
        state['root']=after;state[group]=f['proposed_history'];state['elapsed']+=.02;state['global_raw']+=1;state['progress']=q['s']
        for ids in after.current_contacts:state['visited'].update(ids)
        pose,velocity=d.hull_pose(after);state['tracker'].update(pose,velocity,len(state['visited'])/len(self.static['track']),1.02+state['elapsed'])
        failures=saved['failures'] if saved else [name for bad,name in [(bool(f['gate']),f['gate']),(gap<.5,'FOOTPRINT'),(q['distance']>3,'PATH'),(group=='tracking' and over>4.85,'REFERENCE'),(delta<-.5 or delta>lim,'PROJECTION')] if bad]
        row.update(root_without_roads=p['after']['root'],episode_after_s=state['elapsed'],global_raw_after=state['global_raw'],progress=q['s'],progress_delta=delta,projection_limit=lim,margin=gap,path_error=q['distance'],reference_overspeed=over,body=p['after']['body'],visited_count=len(state['visited']),tracker=asdict(state['tracker']),post_failure=failures[0] if failures else None,all_failures=failures);rows.append(row)
    def cached_local(self,label):
        saved=rd(D/(label+'-private.json'));state=copy.deepcopy(self.start);rows=self.recover_rows(label,state) if saved['rows'] is None else saved['rows']
        if saved['rows'] is not None:state=self.load_checkpoint(saved['checkpoint'])
        value=self.metric(rows);value.update(x=np.asarray(saved['x']),rows=rows,state=state,label=label)
        if 'g' in saved:
            for k in ['g','ratios','order']:assert np.array_equal(value[k],np.asarray(saved[k]))
            assert value['times']==saved['times'];assert d.canonical(base.checkpoint(state))==d.canonical(saved['checkpoint'])
        return value
    def local(self,x,label):
        if label in self.cache_events:
            saved=rd(D/(label+'-private.json'));assert np.array_equal(x,np.asarray(saved['x']));value=self.cached_local(label)
            if len(value['rows'])==134:return value
            state=value['state'];rows=value['rows'];commands=self.actions(x)
            with self.localphase.session(label+'-resume'):
                for offset in range(len(rows),134):
                    i,k=divmod(528+offset,4);row,_=self.raw(state,commands[i+1],i+1,k+1,self.localphase,True);rows.append(row)
            value=self.metric(rows);value.update(x=x.copy(),rows=rows,state=state,label=label);atomic_write(D/(label+'-recovered-private.json'),dict(x=x,rows=rows,checkpoint=base.checkpoint(state),cost=self.cost()));return value
        return super().local(x,label)
    def verify_plan(self,case):
        state=d.Study.initial(self);actual=self.recover_rows('final-independent-full-tape',state);commands={i:a for i,a in self.commands.items() if i<=132};commands.update(self.actions(case['x']));expected=self.tape['rows'][:528]+case['rows']
        for a,b in zip(actual,expected):assert d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker'])
        phase=base.Phase(self,'verification')
        with phase.session('final-independent-full-tape-resume'):
            for offset in range(len(actual),len(expected)):
                i,k=divmod(offset,4);row,reason=self.raw(state,commands[i+1],i+1,k+1,phase);actual.append(row)
                if reason:raise RuntimeError('REPLAY_SAFETY:'+reason)
        same=len(expected)==len(actual) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(actual,expected));cp=d.canonical(base.checkpoint(state))==d.canonical(base.checkpoint(case['state']));assert same and cp
        atomic_write(D/'final-independent-tape-private.json',dict(rows=actual,checkpoint=base.checkpoint(state),exact=same,checkpoint_exact=cp,reused_independent_prefix=489))
        return dict(raw=len(actual),new_ticks=len(actual)-489,reused_independent_prefix=489,fullstate_force_history_tracker_exact=same,checkpoint_exact=cp,official_candidate_raw=round((state['tracker'].finish_time_s-1.02)/.02),confirmation_raw=state['global_raw'])
    def cost(self):
        value=super().cost();value['CPU_wall_are_budget_charges']=True;value['historical_CPU_wall_charge']=500.;value['historical_measured_CPU_lower']=396.682209993;return value

    def run(self):
        result={};error=None;stop=None;whole=None;selected=None;verification=None;working=None;working_raw=660;safe_stale=0;repair_stale=0;last_bad=None;seen=set()
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP572')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP572')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']-500.);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s']-500.)
        try:
            seed=self.metric(self.incumbent['rows']);seed.update(x=self.seed_x.copy(),rows=self.incumbent['rows'],label='571final-safe-working');center=self.cached_local('proposal-0-0-diagnostic');working=self.accepts[0]['metrics'];selected=self.accepts[0]
            for n in range(1,4):
                if time.process_time()-self.cpu>=1200 or time.perf_counter()-self.wall>=1680:stop='OPTIMIZATION_TIME_RESERVE';break
                if n and self.localphase.counter[0]+68*134+4*134>CAPS['local']['ticks']:stop='LOCAL_RESERVE';break
                self.prepare_features(center);self.frozen_segments(center);linear,env=self.linearize(center,first=n==0);accepted=False;rho=.05
                for attempt in range(3):
                    if self.proposals>=10:stop='PROPOSAL_LIMIT10';break
                    label=f'proposal-{n}-{attempt}';x,meta=self.solve(center,linear,env,rho,label)
                    if x is None:self.events.append(dict(label=label,source_evaluated=False,model=meta));stop=meta['reason'];break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,label+'-diagnostic');case=self.strict_finish(x,label+'-strict-finish');event=dict(label=label,source_evaluated=True,model=meta,diagnostic_physical_safe=probe['physical_safe'],diagnostic_violations=probe['violation_counts'],strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],working_accept=False,official_promotion=False);self.events.append(event)
                    if case['safe_finish']:
                        exact=len(case['rows'])<=len(probe['rows']) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(case['rows'],probe['rows']));actual=self.metric(case['rows']);matched=actual['times']['hull_finish']==probe['times']['hull_finish'];assert exact and matched
                        raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-actual['times']['hull_finish'];event.update(strict_diagnostic_prefix_exact=exact,objective_same_command_time_exact=matched,actual_times=actual['times'],diagnostic_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],official_finish_s=case['state']['tracker'].finish_time_s-1.02)
                        if actual['physical_safe'] and gain>=1e-6 and raw<=working_raw:
                            case['metrics']=actual;self.accepts.append(case);selected=case;working=actual;working_raw=raw;accepted=True;safe_stale=0;repair_stale=0;last_bad=None;event['working_accept']=True
                            if raw<660 and (whole is None or raw<round((whole['state']['tracker'].finish_time_s-1.02)/.02) or (raw==round((whole['state']['tracker'].finish_time_s-1.02)/.02) and actual['times']['hull_finish']<whole['metrics']['times']['hull_finish'])):whole=case;event['official_promotion']=True
                            center=probe
                            if not center['physical_safe']:stop='POSTFINISH_DIAGNOSTIC_CENTER_UNSAFE'
                        else:safe_stale+=1
                    else:
                        scales=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in probe['labels']]);bad=max(0.,float(max(-probe['g']/scales)),float(max(-probe['order']/.01)));event['measured_normalized_violation']=bad
                        if last_bad is not None:
                            repair_stale=repair_stale+1 if bad>=.9*last_bad else 0
                        last_bad=bad
                        if attempt<2 and self.restorations<3:event['measured_error_recovery']=self.recover(center,linear,env,probe,case)
                        else:stop='RECOVERY_ATTEMPT_OR_GLOBAL_LIMIT'
                    atomic_write(D/(label+'-decision-private.json'),event)
                    if accepted or stop:break
                    if safe_stale>=2:stop='TWO_SAFE_WHOLE_NONIMPROVEMENTS';break
                    if repair_stale>=2:stop='TWO_REPAIR_STAGNATIONS';break
                    if attempt>=1 or case['safe_finish']:rho*=.5
                if stop or not accepted:stop=stop or 'THREE_BOUNDED_ATTEMPTS_WITHOUT_ACCEPT';break
                recent=[e['diagnostic_gain_ms'] for e in self.events if e.get('working_accept')][-3:]
                if len(recent)==3 and sum(recent)<.10 and all(g<.05 for g in recent[-2:]):stop='OBSERVED_SMALL_PROGRESS_WINDOW';break
                if len(self.accepts)>=4:stop='ACCEPT_LIMIT4';break
            stop=stop or 'LINEARIZATION_LIMIT4'
        except BaseException as e:
            error=type(e).__name__+':'+str(e);atomic_write(D/'ERROR-recovery-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            try:
                selected=whole or selected
                if selected is not None:verification=self.verify_plan(selected)
            except BaseException as e:
                error=(error+';' if error else '')+'VERIFY:'+type(e).__name__+':'+str(e);atomic_write(D/'VERIFY_ERROR-recovery-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
            self.save_cost();self.journal.close()
            try:audit=inspect(D/'recovery-raw-journal-private.jsonl')
            except BaseException as e:audit=dict(valid=False,error=str(e))
            atomic_write(G/'retry/reference572_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/reference572_contract.json'),private_raw_uploaded=False,source_hashes_match=all(sha(G/p)==h for p,h in self.contract['source_sha256'].items()),primitive_unit_tests_reused=4))
            promoted=whole is not None and verification is not None and error is None
            result.update(completed=error is None,error=error,stop_reason=stop,scope='Same full68 source openloop plan;native/feedbacktransition/robustness unproven',seed_times=seed['times'] if 'seed' in locals() else None,final_working_times=working['times'] if working is not None else None,safe_working_accepts=len(self.accepts),official_whole_promotion=promoted,official_incumbent_candidate_raw=round((whole['state']['tracker'].finish_time_s-1.02)/.02) if promoted else 660,official_incumbent_finish_s=whole['state']['tracker'].finish_time_s-1.02 if promoted else 13.199999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events,cost=self.cost(),linearizations=self.linears,reused_FD_columns=0,local_sensitivity_summaries=self.sensitivity_summaries,new_FD_columns=self.fd_completed,new_calibrations=self.calibrations,source_proposals=self.proposals,strict_full_finish_cases=self.evaluations,measured_error_recoveries=self.restorations,feedback_calls=0,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/reference572_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()
