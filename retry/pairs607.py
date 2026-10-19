"""One saved-state zero and fixed joint-pair experiment; no prefix or native."""
import time
CPU=time.process_time()
import datetime,importlib.util,json,math,signal,subprocess,traceback,os
from collections import Counter
from pathlib import Path
from dataclasses import asdict
import numpy as np
import retry.residual605 as old
import retry.pairs607_core as core
from retry.clip561_core import atomic_write
base=old.base;G=old.G;D=Path('/workspace/haic-response607-private')
CAPS=dict(model_attempted=4096,model_completed=4096,external_force=16384,internal_force=16384,total_force=32768,geometry=20000)
FULL=dict(model_attempted=3900,model_completed=3900,external_force=15600,internal_force=15600,total_force=31200,geometry=15518)
def strip_label(value):
    if isinstance(value,dict):return {k:strip_label(v) for k,v in value.items() if k!='label'}
    if isinstance(value,list):return [strip_label(v) for v in value]
    return value
def final_frames(events,wheels):
    at=0;current=[];last=None;frame=None
    for e in events:
        if e['kind']=='TRACKING_TRIAL_START':current=[]
        elif e['kind']=='BEFORE_MODEL_FORCE':
            p=wheels[at:at+4];at+=4;assert all(q[0]=='external_force' for q in p)
            frame=dict(before=e,external=[q[1] for q in p]);current.append(frame)
        elif e['kind']=='MODEL_FORCE_VERDICT':frame['verdict']=e
        elif e['kind']=='BEFORE_MODEL_TICK':
            p=wheels[at:at+4];at+=4;assert all(q[0]=='internal_force' for q in p)
        elif e['kind']=='AFTER_MODEL_TICK':frame['after']=e
        elif e['kind']=='SOURCE_GEOMETRY_DIAGNOSTIC':frame['geometry']=e
        elif e['kind']=='TRACKING_TRIAL_END':last=list(current)
    assert last and len(last)>=4
    return last[:4]

class Study(old.Study):
    def __init__(self):
        self.task=old.d.rd(D/'TASK_STARTED-private.json')
        if (D/'PROCESS_STARTED-private.json').exists():raise RuntimeError('607_NO_AUTOMATIC_RETRY')
        atomic_write(D/'PROCESS_STARTED-private.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        static=old.d.rd(base.old.INPUTS['static']);old.prior.Meter.__init__(self,static,{})
        self.index=self.source_index;self.edge=self.source_edges;self.paths=old.d.rd(base.old.INPUTS['candidate_paths'])
        self.geometry_context=base.old.tracking.geometry_context(self.static,20000)
        self.applied_journal=old.Journal(D/'applied-journal-private.jsonl')
        self.context=None;self.state=None;self.label='preparation';self.results=[];self.saved=[]
        self.orig_geometry_margin=old.compiled_geometry.full.road_margin
        self.original_plain_road=old.compiled_geometry.original.margin;self.original_distance=old.compiled_geometry.distance
        self.result=dict(study=607,status='PREPARATION',zero_pass=False,grid_evaluated=0,shifted_feasible=0,
                         fresh_FINAL=0,applied_raw=0,original_choose_calls=0,independent_replay=False)
    def times(self):return dict(CPU_s=time.process_time()-CPU+10.,wall_s=time.time()-self.task['start_epoch'])
    def guard(self,*a):
        t=self.times()
        if t['CPU_s']>=540 or t['wall_s']>=810 or t['wall_s']<0:raise old.BudgetStop('607_CLEANUP_RESERVE')
        if datetime.datetime.now(datetime.timezone.utc)>=base.DEADLINE:raise old.BudgetStop('DEADLINE')
    def capacity(self,req):
        self.guard()
        for k,n in req.items():
            if k in CAPS and self.counts[k]+n>CAPS[k]:raise old.BudgetStop('607_'+k)
    def initial(self):raise RuntimeError('NEW_INITIAL_STATE_FORBIDDEN607')
    def prefix96(self):raise RuntimeError('PREFIX_FORBIDDEN607')
    def flush(self,label,hold=41,detail=None):
        atomic_write(D/(label+'-telemetry-private.json'),dict(events=old.prior.materialize(self.journal.rows),
            wheel_results=old.prior.materialize(self.raw_kernels),detail=detail,cost=dict(self.counts),time=self.times()))
        self.journal.rows.clear();self.raw_kernels.clear();self.trial_summaries.clear()
    def reserve_full(self):
        self.capacity(FULL);t=self.times()
        if t['CPU_s']+180+60>=600 or t['wall_s']+240+90>=900:raise old.BudgetStop('607_WHOLE_STUDY_AND_CLEANUP_RESERVE')
        self.applied_journal.append('FULL_STUDY_RESERVE',requests=FULL,CPU_s=180,wall_s=240,cleanup_CPU_s=60,cleanup_wall_s=90,time=t)
    def reserve_remaining(self,n):
        raw=(n+1)*48+8;geo=(n+1)*190+88
        req=dict(model_attempted=raw,model_completed=raw,external_force=raw*4,internal_force=raw*4,total_force=raw*8,geometry=geo)
        self.capacity(req);self.applied_journal.append('REMAINING_RESERVE',grid_remaining=n,requests=req,time=self.times())
    def certify(self,a):
        before=old.digest(self.checkpoint(self.state));bits=a.tobytes();self.model_mode='joint_forecast'
        report=self.joint_certify(a)
        assert bits==a.tobytes() and old.digest(self.checkpoint(self.state))==before
        return report
    def apply_four(self,label,a,frames):
        self.label=label;self.state=old.clone(self.start);old.isolated(self.state,[self.start])
        assert old.digest(self.checkpoint(self.state))==self.start_hash
        rows=[]
        for k in range(1,5):
            self.capacity(dict(model_attempted=1,model_completed=1,external_force=4,internal_force=4,total_force=8,geometry=3))
            row,why=old.Study.raw(self,a,41,k);self.result['applied_raw']+=1
            if why:raise RuntimeError('607_APPLIED_STRICT_FAILURE_'+why)
            frame=frames[k-1];expected_forces=[dict(wheel=i,ratio=frame['verdict']['ratios'][i],clipped=bool(frame['external'][i][2]['clipped']),vector=frame['external'][i][1]) for i in range(4)]
            assert old.digest(row['root_without_roads'])==old.digest(frame['after']['root']),'FINAL_ROOT_PARITY'
            assert old.digest(row['forces'])==old.digest(expected_forces),'FINAL_FORCE_PARITY'
            assert row['proposed_history']==frame['verdict']['prefix_history'],'FINAL_HISTORY_PARITY'
            assert row['margin']==frame['geometry']['footprint'],'FINAL_MARGIN_PARITY'
            rows.append(row)
        atomic_write(D/(label+'-rows-private.json'),dict(rows=rows,checkpoint=self.checkpoint(self.state)))
        return rows,self.checkpoint(self.state)
    def zero(self):
        self.reserve_full();self.label='zero';self.state=old.clone(self.start);old.isolated(self.state,[self.start])
        self.begin_context();before=self.counts.copy()
        try:
            self.result['original_choose_calls']+=1
            a,report=old.Study.choose(self,41)
            assert a is not None and a.tobytes().hex()==self.packet['stored_hold41_detail']['incumbent_bits']
            assert old.digest(report)==old.digest(self.packet['stored_hold41_detail']['original_FINAL'])
            work={k:self.counts[k]-before[k] for k in self.expected_work}
            assert work==self.expected_work,('ZERO_WORK_DELTA',work,self.expected_work)
            events=old.prior.materialize(self.journal.rows);wheels=old.prior.materialize(self.raw_kernels)
            assert old.digest(strip_label(events))==old.digest(strip_label(self.expected_events)),'ZERO_PRIMITIVE_PARITY'
            assert old.digest(wheels)==old.digest(self.expected_wheels),'ZERO_WHEEL_PARITY'
            frames=final_frames(self.expected_events,self.expected_wheels)
            self.apply_four('zero-apply',a,frames)
            self.result.update(zero_pass=True,zero_work_delta=work,zero_full_report_primitive_FINAL_first4_exact=True)
        finally:self.end_context();self.flush('zero',detail=dict(zero_pass=self.result['zero_pass']))
    def joint(self):
        assert self.result['zero_pass'];self.label='joint';self.state=old.clone(self.start);self.begin_context()
        try:
            self.joint_certify=base.old.tracking.certifier(self.state['root'],self.paths['candidate'],self.paths['backup'],
                self.state['progress'],self.model,self.planner,self.geometry_context,180000,tuple(self.state['tracking']))
            def record(q):
                self.result['grid_evaluated']+=1
                self.applied_journal.append('PAIR_VERDICT',index=q['index'],row=q['row'],action_bits=q['action'].tobytes().hex(),report=q['report'])
            entries,best,final=core.search(self.pairs,core.net(self.modified),self.certify,self.reserve_remaining,record)
            atomic_write(D/'all-pairs-private.json',[dict(index=q['index'],row=q['row'],u=q['u'],action_bits=q['action'].tobytes().hex(),report=q['report']) for q in entries])
            self.result['row_results']={row:dict(evaluated=sum(q['row']==row for q in entries),feasible=sum(q['row']==row and q['report']['ok'] for q in entries),
                reasons=dict(Counter(q['report']['reason'] for q in entries if q['row']==row))) for row in ['base','shifted']}
            self.result['shifted_feasible']=self.result['row_results']['shifted']['feasible']
            if best is None:self.result['status']='NO_FEASIBLE_SHIFTED_PAIR_IN_FIXED_GRID';return
            self.result['fresh_FINAL']=1
            frames=final_frames(old.prior.materialize(self.journal.rows),old.prior.materialize(self.raw_kernels))
            rows,cp=self.apply_four('shifted-apply',best['action'],frames)
            self.result['selected']=dict(index=best['index'],netpedal_change_vs_recorded_modified=best['u']-core.net(self.modified),
                netpedal_change_vs_original_base=best['u']-core.net(self.base_action),original_FINAL_reused=False,
                progress_gain_diagnostic=rows[-1]['progress']-self.start['progress'],min_margin=min(q['margin'] for q in rows),
                force_peak=max(f['ratio'] for q in rows for f in q['forces']))
            self.end_context();self.flush('joint')
            self.state=old.clone(self.start);self.begin_context()
            replay,rcp=self.apply_four('shifted-replay',best['action'],frames)
            assert old.digest(replay)==old.digest(rows) and old.digest(rcp)==old.digest(cp),'INDEPENDENT_REPLAY_PARITY'
            self.result.update(independent_replay=True,status='LOCAL_SHIFTED_PAIR_SAFE_EXACT_REPLAY')
        finally:
            self.end_context()
            if self.journal.rows:self.flush('final')
    def prepare(self):
        c603=old.d.rd(G/'retry/scalar603_contract.json');r603=old.d.rd(G/'retry/scalar603_result.json')
        for p,h in c603['compiler_runtime_sha256'].items():assert base.sha(Path(p))==h
        self.packet=old.d.rd(Path('/workspace/haic-response606-private/proposed-input-private.json'))
        analysis=old.d.rd(G/'retry/forensic606_analysis.json')
        assert base.sha(Path('/workspace/haic-response606-private/proposed-input-private.json'))==analysis['proposed_private_input_sha256']
        saved605=old.d.rd(Path('/workspace/haic-response605-private/as-executed-result-private.json'))
        assert base.sha(Path('/workspace/haic-response605-private/as-executed-result-private.json'))==self.packet['source605_sha256']
        c605=old.d.rd(G/'retry/residual605_contract.json')
        for k,p in [('static',base.old.INPUTS['static']),('paths',base.old.INPUTS['candidate_paths'])]:assert base.sha(p)==c605['input_sha256'][k]
        cp=self.packet['checkpoint'];h1=old.d.rd(Path('/workspace/haic-response605-private/H1-result-private.json'))
        assert old.digest(cp)==old.digest(h1['checkpoint']) and cp['global_raw']==160
        row=next(q for q in h1['rows'] if q.get('global_raw_after')==160)
        assert old.digest(cp)==row['checkpoint_sha256'] and cp['visited']==row['visited'] and cp['tracking']==row['proposed_history']
        assert cp['tracker']==row['tracker'] and cp['elapsed']==row['episode_after_s'] and cp['launch']==row['launch_history_before']
        root=old.d.load_root(dict(cp['root'],roads=self.static['root']['roads']));old.immutable(root)
        self.start=dict(root=root,progress=cp['progress'],tracker=old.d.FinishLineTracker(**cp['tracker']),visited=set(cp['visited']),
                        launch=list(cp['launch']),tracking=list(cp['tracking']),elapsed=cp['elapsed'],global_raw=cp['global_raw'])
        assert old.digest(self.checkpoint(self.start))==old.digest(cp),'FULL_CHECKPOINT_AND_STEER_LATCH_PARITY'
        self.start_hash=old.digest(cp)
        a=old.clone(self.start);b=old.clone(self.start);old.isolated(a,[b,self.start])
        a['tracking'][0]+=1;assert b['tracking']==self.start['tracking'];a['tracker'].previous_lateral+=1
        assert b['tracker'].previous_lateral==self.start['tracker'].previous_lateral
        self.base_action=np.frombuffer(bytes.fromhex(self.packet['stored_hold41_detail']['incumbent_bits']),np.float32).copy()
        self.modified=np.frombuffer(bytes.fromhex(self.packet['stored_hold41_detail']['action_bits']),np.float32).copy()
        self.pairs,self.grid=core.fixed_pairs(self.base_action,self.modified)
        p=Path('/workspace/haic-response605-private/H1-hold-041-private.json');beforep=Path('/workspace/haic-response605-private/H1-hold-040-private.json')
        assert base.sha(p)==saved605['private_sha256'][p.name] and base.sha(beforep)==saved605['private_sha256'][beforep.name]
        expected=old.d.rd(p);prev=old.d.rd(beforep)
        self.expected_events=[q for q in expected['events'] if q.get('mode')=='incumbent_forecast']
        assert sum(q['kind']=='BEFORE_MODEL_FORCE' and q['mode']=='applied' for q in expected['events'])==1
        assert all(q[0]=='external_force' for q in expected['wheel_results'][-4:])
        self.expected_wheels=expected['wheel_results'][:-4]
        keys=['model_attempted','model_completed','external_force','internal_force','total_force','geometry','geometry_source_footprint',
              'helper_original_comparisons','geometry_internal_nominal_steering','geometry_tracking_forecast','chooser_calls']
        self.expected_work={k:expected['counts'].get(k,0)-prev['counts'].get(k,0) for k in keys}
        self.expected_work['model_attempted']-=1;self.expected_work['external_force']-=4;self.expected_work['total_force']-=4
        self.expected_work['geometry']-=2
        assert expected['counts']['geometry_residual_projection']-prev['counts']['geometry_residual_projection']==1
        binary=Path(c603['command'][-1]);assert base.sha(binary)==r603['binary_sha256']
        spec=importlib.util.spec_from_file_location('_scalar603',binary);ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
        env=ext.environment();assert env.pop('original_math_hypot') is math.hypot and env['rounding_mode']==env['FE_TONEAREST']
        def forbidden(*a,**kw):raise RuntimeError('607_NATIVE_PREFIX_INITIAL_FORBIDDEN')
        base.old.CarRacing.__init__=base.old.CarRacing.reset=base.old.CarRacing.step=forbidden
        base.old.Car.__init__=base.old.Car.step=forbidden
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS==200000
        assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
        contract=dict(study=607,status='FROZEN_BEFORE_PURE_TESTS_AND_ANY_EVALUATOR',task_start=self.task,caps=CAPS,full_reserve=FULL,
            time_caps=dict(total_CPU_s=600,total_wall_s=900,cleanup_CPU_s=60,cleanup_wall_s=90),
            input_packet_sha256=analysis['proposed_private_input_sha256'],checkpoint_sha256=self.start_hash,
            source_sha256={s:base.sha(G/s) for s in ['retry/pairs607.py','retry/pairs607_core.py','retry/residual605.py','retry/structure537_control.py','retry/cold598_support.py']},
            runtime_manifest603_sha256=base.sha(G/'retry/scalar603_contract.json'),binary_sha256=base.sha(binary),
            expected_zero_work_delta=self.expected_work,grid_points=len(self.grid),pairs=len(self.pairs),
            ordering='Steering rows ascending storedfloat32steer,then netpedal descending. Same fixedgrid for both rows;all pairs beforeselection. Min abs(u-recordedmodifiedu),tiehigheru,thenindex.',
            certificate='Original537certifier12holds,current ACTUALfinalpair followedby11unchangedbackupholds. OriginalpositiveFINAL not reused. Atmost48grid+ONEfreshselectedFINAL. No residualaftercertification.',
            applied='Zero base4raw matchesstoredFINALfirst4,then selectedshifted4rawmatchesfreshFINAL,thenoneindependent4rawcommandreplay fromSAMEsavedraw160checkpoint. Allstrictnumeric gates inherited605;no fullcold/prefix/newroot/s400/lap/native.',
            budget='Onlyper-calloriginal537workdeltaandprimitivevaluesmatch605;neverabsoluteoldglobalcounter. Global4096strongerthanoriginalkernel200000;choosemax_ticks180000unchanged. Every603memo miss extra originalPythonmargin charged. Fullreservationbeforezero andremainingbeforeeachcert;allprep/audit/cleanupwall measuredsinceTASK_STARTED.',
            physics_domain='Strictpreforce1.059/clip.10;footprint.50/path3/reference4.85/body<100/projection[-.5,max(5,2COMstep)];finitefloat32control/exclusivepedals. No gate relaxations.',
            stops='Firsttechnical/IO/integrity/domain/budget/deadline failure endsALL,no retry. Ordinarygridcertificate failures retained;nofeasiblenonzero=>FINITE_GRID_ONLY_FAILURE. No slowerprogresspruning.',
            prior606_overtime_preserved=base.sha(G/'retry/forensic606_closeout.json'),research_remaining=22211,reserve=84000,reserve_used=0)
        atomic_write(G/'retry/pairs607_contract.json',contract)
        atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=base.sha(G/'retry/pairs607_contract.json'),counts=dict(self.counts),time=self.times()))
        def reserve_stub():
            fake=Study.__new__(Study);fake.counts=Counter();fake.guard=lambda:None;fake.times=lambda:dict(CPU_s=0,wall_s=0)
            fake.applied_journal=type('J',(),{'append':lambda *a,**k:None})();fake.reserve_full()
            fake.counts['model_attempted']=CAPS['model_attempted']
            try:fake.reserve_full()
            except old.BudgetStop:pass
            else:raise AssertionError('FULL_BUDGET_NOT_RESERVED')
        tests=core.pure_checks(reserve_stub)
        atomic_write(G/'retry/pairs607_tests.json',tests)
        self.install_meters();old.compiled_geometry.distance=ext.distance
    def run(self):
        error=None
        def timer(*a):raise old.BudgetStop('607_TIMER')
        signal.signal(signal.SIGPROF,timer);signal.signal(signal.SIGALRM,timer)
        signal.setitimer(signal.ITIMER_PROF,max(.01,540-self.times()['CPU_s']))
        signal.setitimer(signal.ITIMER_REAL,max(.01,810-self.times()['wall_s']))
        try:
            self.prepare();core.pipeline(self.zero,self.joint)
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);self.result['status']='TECHNICAL_OR_BUDGET_STOP_NO_RETRY'
            atomic_write(D/'error-private.json',dict(error=error,traceback=traceback.format_exc(),time=self.times()))
        finally:
            self.end_context();self.restore();old.compiled_geometry.distance=self.original_distance
            old.compiled_geometry.full.road_margin=self.orig_geometry_margin
            self.applied_journal.append('STUDY_END',error=error,result=self.result,cost=dict(self.counts),time=self.times());self.applied_journal.close()
            if self.journal.rows:self.flush('partial')
            self.result.update(error=error,cost=dict(self.counts),time=self.times(),model_counter=self.model[0],kernel_hardcap=200000,
                native=0,worlds=0,resets=0,actions=0,new_seed=0,HOLDOUT=0,SEALED=0,carry=0,FD=0,solver=0,
                scope='ONE_STORED_STATE_LOCAL_FEASIBILITY_ONLY',native_admission=False,whole_lap_claim=False,
                native_incumbent_s=13.22,research_remaining=22211,reserve=84000,reserve_used=0,
                private_sha256={p.name:base.sha(p) for p in D.glob('*.json*')})
            atomic_write(G/'retry/pairs607_result.json',self.result)
            atomic_write(D/'CLOSED-private.json',dict(time=self.times(),result_sha256=base.sha(G/'retry/pairs607_result.json')))
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            print(json.dumps(self.result,indent=2))
if __name__=='__main__':Study().run()
