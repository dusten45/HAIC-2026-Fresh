"""Bounded six-basis full-source pattern search. Surrogates never veto points."""
import datetime,json,signal,time,traceback
from pathlib import Path
import numpy as np
import retry.face576_model as shared
from retry.algebra575_isolate import load
from retry.direct577_math import bases,propose,choose
from retry.wide574_math import SCALE,metric
from retry.checkpoints574 import same
from retry.clip561_core import atomic_write,plain
from retry.durable568 import inspect

ROOT=shared.ROOT;PRIVATE=Path('/workspace/haic-response577-private');OLD=shared.OLD;base=shared.base;d=shared.d;rd=d.rd;sha=d.sha

class Source(shared.Source):
    def __init__(self,*args):
        shared.PRIVATE=PRIVATE;super().__init__(*args);self.evaluations=0;self.replays=0;self.events=[];self.round=0
    def cost(self):
        v=base.Study.cost(self);v.pop('prior567_separate',None);v.update(preflight_test_CPU_wall_charge_s=5.,source_candidates=self.evaluations,independent_replays=self.replays,round=self.round);return v
    def save_cost(self):atomic_write(ROOT/'retry/direct577_cost.json',self.cost(),True)
    def guard(self,reserve=0):
        c=self.cost();active=next((p.bucket for p in self.phases if p.active),None)
        for key,limit in dict(ticks=16550,force=66200,geometry=16550,CPU_s=600,wall_s=720).items():
            if c['total'][key]+(reserve if key=='force' else 0)>limit:raise RuntimeError('577_TOTAL_CAP:'+key)
        for bucket in ['evaluation','verification']:
            for key,limit in self.contract['budgets'][bucket].items():
                used=sum(v[key] for v in c['phases'] if v['bucket']==bucket)
                if used+(reserve if key=='force' and active==bucket else 0)>limit:raise RuntimeError('577_BUCKET_CAP:'+bucket+':'+key)
        for p in self.phases:
            if p.active:
                v=p.values()
                if v['CPU_s']>25 or v['wall_s']>35:raise RuntimeError('577_CASE_TIME_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('577_DEADLINE')
    def can_evaluate(self):
        c=self.cost();ev=[p for p in c['phases'] if p['bucket']=='evaluation'];ec=sum(p['CPU_s'] for p in ev);ew=sum(p['wall_s'] for p in ev)
        return self.evaluations<24 and c['total']['ticks']+1324<=16550 and c['total']['CPU_s']+25+30+15<=600 and c['total']['wall_s']+35+45+20<=720 and ec+25<=480 and ew+35<=600

def compare(a,b):
    keys=['before_root_without_roads','root_without_roads','forces','proposed_history','tracker','episode_before_s','episode_after_s','global_raw_after','tracking_history_before','launch_history_before','visited_count']
    return bool(a['safe'] and b['safe'] and len(a['rows'])==len(b['rows']) and all(same(x[k],y[k]) for x,y in zip(a['rows'],b['rows']) for k in keys) and same(base.checkpoint(a['state']),base.checkpoint(b['state'])))

def main():
    PRIVATE.mkdir(mode=0o700,exist_ok=False);contract=rd(ROOT/'retry/direct577_contract.json');tests=rd(ROOT/'retry/direct577_tests.json');assert tests['passed']==3
    sources=['retry/direct577_model.py','retry/direct577_math.py','tests/test_direct577.py','retry/face576_model.py','retry/late568_model.py','retry/wide574_math.py','retry/checkpoints574.py','retry/durable568.py',*d.SOURCES]
    inputs=[Path('/workspace/haic-response575-private/model-private.npz'),OLD/'initial-center-private.json',OLD/'linear-1-private.npz',OLD/'initial-checkpoints-private.json',Path('/workspace/haic-response573-private/final-independent-tape-private.json'),ROOT/'retry/quant573_result.json',*base.INPUTS[1:4]]
    contract.update(implementation_frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256={s:sha(ROOT/s) for s in sources},input_sha256={str(p):sha(p) for p in inputs},tests_sha256=sha(ROOT/'retry/direct577_tests.json'));atomic_write(ROOT/'retry/direct577_contract.json',contract,True);atomic_write(PRIVATE/'STARTED.json',dict(contract_sha256=sha(ROOT/'retry/direct577_contract.json')))
    cpu=time.process_time()-5.;wall=time.perf_counter()-5.;study=None;selected=None;events=[];rounds=[];error=None;stop=None;verified=None;accepts=0;seed_hull=13.19360251036074;working_hull=seed_hull;working_raw=660;seen=set();skips=[]
    tick,force=d.source_tick,d.force_rows
    def forbidden(*a,**kw):raise RuntimeError('577_SOURCE_BEFORE_BASIS_FREEZE')
    d.source_tick=d.force_rows=forbidden;signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('577_CPU_CAP')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('577_WALL_CAP')));signal.setitimer(signal.ITIMER_PROF,595);signal.setitimer(signal.ITIMER_REAL,715)
    try:
        pc,pw=time.process_time(),time.perf_counter();base.CAPS={k:contract['budgets'][k] for k in ['evaluation','verification']};study=Source(cpu,wall,contract);p=load();seed=p['x0'].copy();working=seed.copy();center=rd(OLD/'initial-center-private.json');linear=dict(np.load(OLD/'linear-1-private.npz'));m=metric(study,center['rows']);assert m['physical_safe'] and m['times']['hull_finish']==seed_hull;B,details=bases(p,linear,m['g']);assert B.shape==(6,264) and np.linalg.matrix_rank(B)==6
        np.savez(PRIVATE/'frozen-bases-private.npz',B=B,seed=seed);atomic_write(ROOT/'retry/direct577_basis.json',dict(bases=details,rank=6,private_basis_sha256=sha(PRIVATE/'frozen-bases-private.npz'),CPU_s=time.process_time()-pc,wall_s=time.perf_counter()-pw,source_ticks=0,empirical_L_used=False,rounding_tube_used=False));
        if time.process_time()-pc>10 or time.perf_counter()-pw>15:raise RuntimeError('577_PREPARATION_CAP')
        d.source_tick,d.force_rows=tick,force;seen.add(seed.tobytes());step=.004;stagnant=0
        for round_index in range(2):
            study.round=round_index+1;before_accepts=accepts
            for k in range(6):
                anchor=working.copy();anchor_hull=working_hull;anchor_raw=working_raw;cases=[];records=[]
                for sign in [1,-1]:
                    label=f'round-{round_index+1}-basis-{k}-'+('plus' if sign>0 else 'minus');x,proposal=propose(seed,anchor,B[k],step,sign)
                    if x.tobytes() in seen:
                        skips.append(dict(label=label,reason='DUPLICATE_OR_QUANTIZED_ZERO'));continue
                    if not study.can_evaluate():stop='FINAL_REPLAY_RESERVE';break
                    seen.add(x.tobytes());study.evaluations+=1;study.save_cost();delta=x-seed;pred=m['g']+linear['J']@delta;labels=np.asarray(m['labels']);predicted={v:float(min(pred[labels==v])) for v in sorted(set(labels))}
                    plan=dict(label=label,x=x,proposal=proposal,step=step,sign=sign,basis=k,anchor_hull=anchor_hull,predicted_gain_over_anchor_s=-float(p['objective']@((x-anchor)/SCALE)),predicted_minimum_slack_by_group=predicted);atomic_write(PRIVATE/(label+'-planned-private.json'),plan)
                    case=study.full(x,label,'evaluation');record=dict(label=label,evaluation=study.evaluations,basis=k,round=round_index+1,sign=sign,step=step,proposal=proposal,predicted_gain_over_anchor_ms=1000*plan['predicted_gain_over_anchor_s'],predicted_minimum_slack_by_group=predicted,strict_safe_finish=case['safe'],strict_failure=case['failure'],source_ticks=sum(p.values()['ticks'] for p in study.phases if p.label==label),selected_incumbent=False)
                    score=dict(safe=False)
                    if case['safe']:
                        actual=metric(study,case['rows'][136:]);raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);score=dict(safe=actual['physical_safe'],raw=raw,hull=actual['times']['hull_finish']);record.update(actual_times=actual['times'],actual_gain_over_anchor_ms=1000*(anchor_hull-score['hull']),official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'])
                    else:
                        row=case['rows'][-1];record['first_failure_raw']=row['global_raw_before']+1;record['first_failure_values']={key:row[key] for key in ['margin','path_error','reference_overspeed','body'] if key in row}
                    case.update(x=x,score=score);cases.append(case);records.append(record);events.append(record);atomic_write(ROOT/'retry/direct577_events.json',events,True);atomic_write(PRIVATE/(label+'-decision-private.json'),record);print(json.dumps(plain(dict(stage='CASE',**record,cost=study.cost()['total']))),flush=True)
                winner=choose(anchor_hull,anchor_raw,[c['score'] for c in cases])
                if winner is not None:
                    selected=cases[winner];working=selected['x'].copy();working_hull=selected['score']['hull'];working_raw=selected['score']['raw'];accepts+=1;records[winner]['selected_incumbent']=True;atomic_write(PRIVATE/'working-incumbent-private.json',dict(x=working,hull=working_hull,raw=working_raw,label=records[winner]['label'],checkpoint=base.checkpoint(selected['state'])) ,True);atomic_write(ROOT/'retry/direct577_events.json',events,True);atomic_write(PRIVATE/(records[winner]['label']+'-decision-private.json'),records[winner],True);print(json.dumps(dict(stage='ACCEPT',label=records[winner]['label'],hull=working_hull,raw=working_raw,accepts=accepts)),flush=True)
                if stop:break
            made=accepts-before_accepts
            if not stop:stagnant=stagnant+1 if made==0 else 0
            rounds.append(dict(round=round_index+1,complete=stop is None,step=step,accepts=made,consecutive_no_gain_rounds=stagnant));atomic_write(ROOT/'retry/direct577_rounds.json',rounds,True)
            if stop:break
            if stagnant>=2:stop='TWO_NO_GAIN_ROUNDS';break
            if round_index==0 and made==0:step=.002
        stop=stop or 'TWO_ROUNDS_COMPLETE'
        if selected is not None:
            study.replays=1;study.save_cost();again=study.full(working,'final-independent-new-full-tape','verification');exact=compare(selected,again);verified=dict(exact=exact,checkpoint_exact=same(base.checkpoint(selected['state']),base.checkpoint(again['state'])),raw=len(again['rows']),official_candidate_raw=working_raw)
            if not exact:raise RuntimeError('577_INDEPENDENT_REPLAY_MISMATCH')
            atomic_write(PRIVATE/'final-independent-tape-private.json',dict(rows=again['rows'],commands=[dict(index=h,action=a) for h,a in sorted(again['commands'].items())],checkpoint=base.checkpoint(again['state']),exact=True,checkpoint_exact=verified['checkpoint_exact']))
    except BaseException as e:
        error=type(e).__name__+':'+str(e);atomic_write(PRIVATE/'ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),events=events,cost=study.cost() if study else None),True)
    finally:
        d.source_tick,d.force_rows=tick,force;journal=None
        if study is not None:
            study.save_cost();study.journal.close();ac,aw=time.process_time(),time.perf_counter()
            try:
                journal=inspect(PRIVATE/'raw-journal-private.jsonl')
                if time.process_time()-ac>15 or time.perf_counter()-aw>20:raise RuntimeError('577_AUDIT_CAP')
            except BaseException as e:error=error or 'AUDIT:'+str(e)
            study.save_cost();cost=study.cost()
        else:cost=dict(total=dict(ticks=0,force=0,geometry=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall))
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);valid=verified is not None and verified['exact'] and error is None
        result=dict(completed=error is None,error=error,stop_reason=stop,method='bounded6basisfullsourcepatternsearch',source_candidates=study.evaluations if study else 0,independent_replays=study.replays if study else 0,safe_working_accepts=accepts,seed_hull_s=seed_hull,final_working_hull_s=working_hull,actual_gain_ms=1000*(seed_hull-working_hull),new_plan_independently_verified=valid,independent_verification=verified,official_promotion=bool(valid and working_raw<660),official_incumbent_raw=working_raw if valid else 660,official_incumbent_s=selected['state']['tracker'].finish_time_s-1.02 if valid else 13.20,events=events,rounds=rounds,skips=skips,cost=cost,journal=journal,source_hashes_match=all(sha(ROOT/s)==h for s,h in contract['source_sha256'].items()),input_hashes_match=all(sha(Path(s))==h for s,h in contract['input_sha256'].items()),actual_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,new_FD=0,new_calibrations=0,LP_solves=0,scope='Actualwholecommand-sourceonly;Native/pixel/feedback/robustnessnotproven. Surrogatepredictionsdiagnosticonly.');atomic_write(ROOT/'retry/direct577_result.json',result,True);print(json.dumps(plain(result),indent=2),flush=True)

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**k):raise RuntimeError('NATIVE_FORBIDDEN577')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    main()
