"""One stored-model float32 repair, then at most one strict source candidate."""
import copy,datetime,inspect,json,signal,textwrap,time,traceback
from pathlib import Path
import numpy as np
import retry.reference572_model as m
from retry.rounding573 import solve,check
from retry.durable568 import Journal,inspect as inspect_journal
from retry.clip561_core import atomic_write,plain

G=m.G;OLD=m.D;D=Path('/workspace/haic-response573-private');rd=m.rd;sha=m.sha;base=m.base;d=m.d

def load_stored():
    o=object.__new__(m.Study);o.static=rd(base.INPUTS[1]);o.paths=rd(base.INPUTS[2]);o.tape=rd(base.INPUTS[0]);o.ledger=rd(base.INPUTS[3]);r=o.tape['rows'][527];visited=set(o.ledger['initial_visited'])
    for row in o.tape['rows'][:528]:
        for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
    o.start=dict(root=d.load_root(dict(r['root_without_roads'],roads=o.static['root']['roads'])),progress=r['progress'],tracking=r['proposed_history'].copy(),launch=r['launch_history_before'].copy(),tracker=d.FinishLineTracker(**r['tracker']),elapsed=r['episode_after_s'],global_raw=528,visited=visited)
    assert o.start['tracking']==[64,1728] and o.start['launch']==[55,384]
    o.s900=base.station_point(o.paths['candidate'],900.);saved=rd(OLD/'proposal-2-0-diagnostic-private.json');center=o.metric(saved['rows']);center.update(x=np.asarray(saved['x']),rows=saved['rows'],label='572finalsafe');o.seed_x=np.asarray(rd(m.OLD/'proposal-4-0-diagnostic-private.json')['x']);o.frozen_segments(center);support=rd(OLD/'proposal-3-0-support-private.json')
    o.support_model=lambda *args:tuple(np.asarray(support[k]) for k in ['seed_slacks','Jacobian','error_coefficients'])
    linear={k:np.asarray(v) for k,v in rd(OLD/'linear-4-private.json')['linear'].items()};env=rd(OLD/'envelope-4-private.json')
    source=textwrap.dedent(inspect.getsource(m.Study.solve));marker='    for cut in range(8):';assert source.count(marker)==1
    source=source.split(marker)[0]+"    return dict(A=A0,b=b0,bounds=np.asarray(bounds),objective=T,path=dict(center=center['P'],J=P,L=lp,a=self.segA,b=self.segB),x0=center['x'],scale=SCALE),pre,ids\n"
    source=source.replace("atomic_write(D/(tag+'-precheck-private.json'),pre)",'self.precheck=pre');ns=dict(m.__dict__);exec(compile(source,'<573-fixed-572-matrix-extraction-no-solve>','exec'),ns);problem,pre,ids=ns['solve'](o,center,linear,env,.05,'unused')
    assert pre==rd(OLD/'proposal-3-0-precheck-private.json');return o,center,problem,support,ids

class SourceStudy(m.Study):
    def __init__(self,stored,contract,cpu,wall):
        self.__dict__.update(stored.__dict__);self.contract=contract;self.cpu=cpu;self.wall=wall;self.phases=[];self.evaluations=0;self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.journal=Journal(D/'raw-journal-private.jsonl')
    def cost(self):
        value=base.Study.cost(self);value.pop('prior567_separate',None);value['test_and_prestart_CPU_wall_budget_charge_s']=2.;return value
    def save_cost(self):atomic_write(G/'retry/quant573_cost.json',self.cost(),True)
    def strict_finish(self,x,label):
        assert self.evaluations==0
        return super().strict_finish(x,label)

def main():
    if (D/'STARTED.json').exists():raise RuntimeError('573_ALREADY_STARTED')
    contract=rd(G/'retry/quant573_contract.json');tests=rd(G/'retry/quant573_tests.json');assert tests['passed']==7 and tests['failed']==0
    sources=['retry/rounding573.py','retry/quant573_model.py','tests/test_rounding573.py','retry/reference572_model.py','retry/repair571_model.py','retry/tail570_model.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES]
    contract.update(implementation_frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={p:sha(G/p) for p in sources},tests_sha256=sha(G/'retry/quant573_tests.json'))
    assert all(sha(G/p)==h for p,h in tests['source_sha256'].items());assert all(sha(Path(p))==h for p,h in contract['input_sha256'].items());atomic_write(G/'retry/quant573_contract.json',contract,True);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/quant573_contract.json')))
    cpu=time.process_time()-2.;wall=time.perf_counter()-2.;study=None;result=dict(completed=False,new_native_actions=0,new_resets=0,new_worlds=0,HOLDOUT=0,SEALED=0,new_seeds=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,source_proposals=0,independent_replays=0);saved_force,saved_tick=d.force_rows,d.source_tick
    def forbidden(*a,**kw):raise RuntimeError('SOURCE_FORBIDDEN_BEFORE_ALGEBRA_GATE')
    d.force_rows=d.source_tick=forbidden
    signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP573')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP573')));signal.setitimer(signal.ITIMER_PROF,63);signal.setitimer(signal.ITIMER_REAL,108)
    try:
        stagecpu,stagewall=time.process_time(),time.perf_counter();stored,center,problem,support,ids=load_stored();x,algebra=solve(problem,max_solves=8)
        algebra.update(CPU_s=time.process_time()-stagecpu,wall_s=time.perf_counter()-stagewall,source_ticks=0,old_precheck_exact=True)
        if algebra['CPU_s']>15 or algebra['wall_s']>25:raise RuntimeError('ALGEBRA_BUDGET')
        if x is not None:
            z=(x-problem['x0'])/problem['scale'];t=float(max(abs(z)));res=problem['A']@np.r_[z,t]-problem['b'];keep=np.asarray(center['labels'])!='path';mapping=np.flatnonzero(keep);M=len(mapping);K=len(support['seed_slacks']);labels=np.asarray(center['labels'])[mapping]
            algebra['joint_group_violations']=dict(force=max(0.,float(max(res[:M][labels=='force']))),reference=max(0.,float(max(res[:M][labels=='reference']))),signed_road_support=max(0.,float(max(res[M+len(ids):M+len(ids)+K]))),trust_bounds=algebra['verdict']['bound_violation'],capsule=algebra['verdict']['path_violation'])
            atomic_write(D/'quantized-candidate-private.json',dict(x=x,algebra=algebra,seed=problem['x0']))
        atomic_write(G/'retry/quant573_algebra.json',algebra);result['algebra']=algebra
        if x is None:result.update(completed=True,stop_reason=algebra['stop'],safe_working_accept=False);return
        assert algebra['accepted'] and check(problem,x)['pass_all'];d.force_rows,d.source_tick=saved_force,saved_tick
        caps={k:contract['budgets'][k] for k in ['evaluation','verification']};base.CAPS=caps;base.TOTAL=contract['aggregate'];base.D=D;m.D=D;m.parent.D=D;m.parent.parent.D=D
        study=SourceStudy(stored,contract,cpu,wall);result['source_proposals']=1;case=study.strict_finish(x,'one-quantized-strict-finish');result.update(strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],strict_raw_count=len(case['rows']),safe_working_accept=False)
        if case['safe_finish']:
            actual=study.metric(case['rows']);raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=center['times']['hull_finish']-actual['times']['hull_finish'];result.update(actual_times=actual['times'],actual_gain_ms=1000*gain,official_candidate_raw=raw,official_finish_s=case['state']['tracker'].finish_time_s-1.02,confirmation_raw=case['state']['global_raw'])
            accepted=bool(actual['physical_safe'] and gain>=1e-6 and raw<=660);result['safe_working_accept']=accepted
            if accepted:result['independent_replays']=1;result['independent_verification']=study.verify_plan(case)
        result.update(completed=True,stop_reason='ONE_SOURCE_CANDIDATE_DONE',official_promotion=bool(result['safe_working_accept'] and result['official_candidate_raw']<660))
    except BaseException as e:
        result.update(error=type(e).__name__+':'+str(e),stop_reason='ERROR');atomic_write(D/'ERROR-private.json',dict(error=result['error'],traceback=traceback.format_exc()))
    finally:
        d.force_rows,d.source_tick=saved_force,saved_tick;signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        if study is not None:
            study.save_cost();result['cost']=study.cost();study.journal.close();result['journal']=inspect_journal(D/'raw-journal-private.jsonl')
        else:result['cost']=dict(total=dict(ticks=0,force=0,geometry=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall),test_and_prestart_CPU_wall_budget_charge_s=2.)
        result['source_hashes_match']=all(sha(G/p)==h for p,h in contract['source_sha256'].items());atomic_write(G/'retry/quant573_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def native_forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN573')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=native_forbidden
    main()
