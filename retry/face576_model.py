"""One saved-model active face; at most one full-source candidate and replay."""
import datetime,json,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.late568_model as base
import retry.handoff562_model as d
from retry.algebra575_isolate import load
from retry.face576_math import active_face,enclosures
from retry.causal575_rounding import solve,check
from retry.wide574_model import load_checkpoint
from retry.wide574_math import metric
from retry.checkpoints574 import same
from retry.clip561_core import atomic_write,plain,prefix_slacks
from retry.durable568 import Journal,inspect,digest

ROOT=Path(__file__).resolve().parents[1];PRIVATE=Path('/workspace/haic-response576-recovery-private');OLD=Path('/workspace/haic-response574-private')
rd=d.rd;sha=d.sha

class Source:
    def __init__(self,cpu,wall,contract):
        self.cpu=cpu;self.wall=wall;self.contract=contract;self.phases=[];self.static=rd(base.INPUTS[1]);self.paths=rd(base.INPUTS[2]);self.ledger=rd(base.INPUTS[3]);self.tape=rd(Path('/workspace/haic-response573-private/final-independent-tape-private.json'));self.commands={v['index']:np.asarray(v['action'],np.float32) for v in self.tape['commands']};self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.start=load_checkpoint(rd(OLD/'initial-checkpoints-private.json')['35'],self.static);self.journal=Journal(PRIVATE/'raw-journal-private.jsonl')
    def cost(self):
        v=base.Study.cost(self);v.pop('prior567_separate',None);v['preflight_test_CPU_wall_charge_s']=7.;return v
    def save_cost(self):atomic_write(ROOT/'retry/face576_cost.json',self.cost(),True)
    def guard(self,reserve=0):
        cost=self.cost();active=next((p.bucket for p in self.phases if p.active),None)
        for key,limit in dict(ticks=1324,force=5296,geometry=1324,CPU_s=120,wall_s=180).items():
            if cost['total'][key]+(reserve if key=='force' else 0)>limit:raise RuntimeError('576_AGGREGATE_CAP:'+key)
        for bucket in ['evaluation','verification']:
            for key,limit in self.contract['budgets'][bucket].items():
                v=sum(p[key] for p in cost['phases'] if p['bucket']==bucket)
                if v+(reserve if key=='force' and active==bucket else 0)>limit:raise RuntimeError('576_BUCKET_CAP:'+bucket+':'+key)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('576_DEADLINE')
    def raw(self,*args):
        row,reason=base.Study.raw(self,*args)
        args[4].histories.clear()
        return row,reason
    def full(self,x,label,bucket):
        state=d.Study.initial(self);rows=[];failure=None;phase=base.Phase(self,bucket);commands={h:a for h,a in self.commands.items() if h<35}
        for j in range(132):commands[35+j]=np.asarray([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32)
        with phase.session(label):
            try:
                for before in range(662):
                    h,k=divmod(before,4);row,reason=self.raw(state,commands[h+1],h+1,k+1,phase);rows.append(row)
                    if reason:failure=reason;break
                    if state['tracker'].finish_time_s is not None:break
                safe=failure is None and state['tracker'].finish_time_s is not None
                if not safe and failure is None:failure='NO_FINISH_IN_HORIZON'
                if safe:
                    if len(rows)<136:raise RuntimeError('576_PREMATURE_FINISH')
                    prefix_exact=all(same(a['root_without_roads'],b['root_without_roads']) and same(a['forces'],b['forces']) and same(a['tracker'],b['tracker']) and a['episode_after_s']==b['episode_after_s'] and a['proposed_history']==b['proposed_history'] and a['visited_count']==b['visited_count'] for a,b in zip(rows[:136],self.tape['rows'][:136]))
                    if not prefix_exact:raise RuntimeError('576_FIXED_PREFIX_MISMATCH')
                return dict(state=state,rows=rows,safe=safe,failure=failure,commands=commands)
            finally:atomic_write(PRIVATE/(label+'-private.json'),dict(rows=rows,checkpoint=base.checkpoint(state),failure=failure,commands=[dict(index=h,action=a) for h,a in sorted(commands.items())],cost=self.cost()))

def main():
    PRIVATE.mkdir(mode=0o700,exist_ok=False);contract=rd(ROOT/'retry/face576_contract.json');tests=rd(ROOT/'retry/face576_tests.json');assert tests['passed']==4
    inputs=[Path('/workspace/haic-response575-private/model-private.npz'),ROOT/'retry/algebra575_result.json',OLD/'initial-center-private.json',OLD/'initial-checkpoints-private.json',OLD/'linear-1-private.npz',Path('/workspace/haic-response573-private/final-independent-tape-private.json'),Path('/workspace/haic-response575-private/expanded-tube-private.npz')]
    sources=['retry/face576_model.py','retry/face576_math.py','tests/test_face576.py','retry/causal575_rounding.py','retry/rounding573.py','retry/wide574_math.py','retry/checkpoints574.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES]
    contract.update(implementation_frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={s:sha(ROOT/s) for s in sources},input_sha256={str(p):sha(p) for p in inputs},tests_sha256=sha(ROOT/'retry/face576_tests.json'));atomic_write(ROOT/'retry/face576_contract.json',contract,True);atomic_write(PRIVATE/'STARTED.json',dict(contract_sha256=sha(ROOT/'retry/face576_contract.json')))
    assert sha(inputs[0])==rd(inputs[1])['private_model_sha256']
    cpu=time.process_time()-7.;wall=time.perf_counter()-7.;study=None;count=0;result=dict(completed=False,source_candidates=0,independent_replays=0,safe_working_accept=False,official_promotion=False,official_incumbent_candidate_raw=660,official_incumbent_finish_s=13.20,actual_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,new_FD=0,new_calibrations=0,active_face_count=1)
    tick,force=d.source_tick,d.force_rows
    def forbidden(*a,**kw):raise RuntimeError('SOURCE_FORBIDDEN_BEFORE_576_GATE')
    d.source_tick=d.force_rows=forbidden
    signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('576_CPU_CAP')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('576_WALL_CAP')));signal.setitimer(signal.ITIMER_PROF,113);signal.setitimer(signal.ITIMER_REAL,173)
    try:
        ac,aw=time.process_time(),time.perf_counter();p,fixed,q,inward=active_face(load());savedbox=np.load(inputs[-1])['bounds'];assert np.array_equal(fixed,(savedbox[:264,0]>0)|(savedbox[:264,1]<0));checks=enclosures(p,fixed,q,inward);checks['same_predetermined_575_mask_exact']=True;atomic_write(ROOT/'retry/face576_preflight.json',checks)
        def bounded(c,A_ub,b_ub,bounds,**unused):
            nonlocal count
            if count>=8:raise RuntimeError('576_SOLVE_CAP')
            if time.process_time()-ac>35 or time.perf_counter()-aw>50:raise RuntimeError('576_ALGEBRA_CAP')
            count+=1
            return linprog(c,A_ub=A_ub,b_ub=b_ub,bounds=bounds,method='highs',options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9,time_limit=5.))
        x,meta=solve(p,solve_fn=bounded,max_solves=8);meta.update(CPU_s=time.process_time()-ac,wall_s=time.perf_counter()-aw)
        if meta['CPU_s']>35 or meta['wall_s']>50:raise RuntimeError('576_ALGEBRA_CAP')
        result['algebra']=meta
        if x is None:result.update(completed=True,stop_reason=meta['stop'],failure_class='RESTRICTED_MODEL_CERTIFICATE_NO_OPPORTUNITY');return
        assert np.array_equal(x[fixed],p['x0'][fixed]) and check(p,x)['pass_all']
        center=rd(OLD/'initial-center-private.json');R=np.load(OLD/'linear-1-private.npz')['R'];ratios=np.asarray([f['ratio'] for row in center['rows'] for f in row['forces']])+R@(x-p['x0']);slack=prefix_slacks(ratios,3,160)
        result['predicted_exact_prefix_pass']=bool(min(slack)>=0)
        if not result['predicted_exact_prefix_pass']:raise RuntimeError('576_EXACT_PREFIX_GATE')
        atomic_write(PRIVATE/'algebra-candidate-private.json',dict(x=x,face_fixed=fixed,verdict=check(p,x)));d.source_tick,d.force_rows=tick,force;base.CAPS={k:contract['budgets'][k] for k in ['evaluation','verification']};base.TOTAL=dict(ticks=1324,force=5296,geometry=1324,CPU_s=120,wall_s=180)
        study=Source(cpu,wall,contract);result['source_candidates']=1;case=study.full(x,'one-full-strict','evaluation');result.update(strict_safe_finish=case['safe'],strict_failure=case['failure'])
        if not case['safe']:result.update(completed=True,stop_reason='STRICT_SOURCE_FAILURE',failure_class='TRUE_SOURCE_SAFETY_OR_FINISH_FAILURE');return
        actual=metric(study,case['rows'][136:]);raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=13.19360251036074-actual['times']['hull_finish'];accepted=actual['physical_safe'] and gain>=1e-6 and raw<=660;result.update(actual_times=actual['times'],actual_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],safe_working_accept=bool(accepted))
        if accepted:
            result['independent_replays']=1;again=study.full(x,'independent-new-full-tape','verification');keys=['before_root_without_roads','root_without_roads','forces','proposed_history','tracker','episode_before_s','episode_after_s','global_raw_after','tracking_history_before','launch_history_before','visited_count'];exact=again['safe'] and len(again['rows'])==len(case['rows']) and all(same(a[k],b[k]) for a,b in zip(again['rows'],case['rows']) for k in keys);cp=same(base.checkpoint(again['state']),base.checkpoint(case['state']));result['independent_verification']=dict(raw=len(again['rows']),full_state_force_history_tracker_clock_visited_exact=exact,checkpoint_exact=cp)
            if not exact or not cp:raise RuntimeError('576_INDEPENDENT_REPLAY_MISMATCH')
            atomic_write(PRIVATE/'final-independent-tape-private.json',dict(rows=again['rows'],commands=[dict(index=h,action=a) for h,a in sorted(again['commands'].items())],checkpoint=base.checkpoint(again['state']),exact=exact,checkpoint_exact=cp));result.update(official_incumbent_candidate_raw=raw,official_incumbent_finish_s=case['state']['tracker'].finish_time_s-1.02,official_promotion=raw<660)
        result.update(completed=True,stop_reason='ONE_CANDIDATE_DONE',failure_class=None if accepted else 'SOURCE_SAFE_NO_ACCEPTABLE_GAIN')
    except BaseException as e:
        result.update(error=type(e).__name__+':'+str(e),stop_reason='ERROR',safe_working_accept=False,official_promotion=False);atomic_write(PRIVATE/'ERROR-private.json',dict(error=result['error'],traceback=traceback.format_exc()))
    finally:
        d.source_tick,d.force_rows=tick,force
        if study is not None:
            study.save_cost();study.journal.close();jc,jw=time.process_time(),time.perf_counter()
            try:result['journal']=inspect(PRIVATE/'raw-journal-private.jsonl')
            except BaseException as e:result.update(completed=False,error='576_JOURNAL:'+str(e),journal=dict(valid=False))
            result['journal_audit_CPU_s']=time.process_time()-jc;result['journal_audit_wall_s']=time.perf_counter()-jw
            if result['journal_audit_CPU_s']>10 or result['journal_audit_wall_s']>15:result.update(completed=False,error='576_AUDIT_CAP')
            study.save_cost();result['cost']=study.cost()
        else:result['cost']=dict(total=dict(ticks=0,force=0,geometry=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall),preflight_test_CPU_wall_charge_s=7.);atomic_write(ROOT/'retry/face576_cost.json',result['cost'],True)
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        if result.get('error'):result.update(safe_working_accept=False,official_promotion=False,official_incumbent_candidate_raw=660,official_incumbent_finish_s=13.20)
        result.update(LP_solves=count,source_hashes_match=all(sha(ROOT/s)==h for s,h in contract['source_sha256'].items()),input_hashes_match=all(sha(Path(p))==h for p,h in contract['input_sha256'].items()),scope='One predetermined575fixed40face:33exactdomainendpoints+7adjacentfloat32values. Not wholefeasible-set search orphysicalrobustness/globaloptimum. Native/pixel/feedback untested.');atomic_write(ROOT/'retry/face576_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def native_forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN576')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=native_forbidden
    main()
