"""One bounded reachable beam pilot. Native and optimizer execution forbidden."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import sys,json,math,signal,datetime,traceback,copy,hashlib
from pathlib import Path
from dataclasses import fields,is_dataclass,asdict
from contextlib import contextmanager
from collections import Counter
import numpy as np
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,evaluate_force,guarded_tick,inspect
import retry.late568_model as base
import retry.handoff562_model as d
import retry.brake502_response as wheel
import retry.brake504_planar as planar
from retry.beam579_math import clone,immutable,actions,crossing,passes,terminal_key,rank_key,isolated
from core.vendor.car_racing import CarRacing

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response579-private');CONTRACT=G/'retry/beam579_contract.json'
INPUTS={'tape':Path('/workspace/haic-response577-private/final-independent-tape-private.json'),'static':Path('/workspace/haic-response515-private/collected-map-state-private.json'),'paths':Path('/workspace/haic-response551-private/frozen-paths-private.json'),'ledger':Path('/workspace/haic-response519-private/model-ledger-private.json')}
KEYS=['action','before_root_without_roads','root_without_roads','forces','proposed_history','tracker','episode_before_s','episode_after_s','global_raw_before','global_raw_after','tracking_history_before','launch_history_before','visited_count','progress','margin','path_error','reference_overspeed','body']
def forbidden(*a,**k):raise RuntimeError('NATIVE_OR_OPTIMIZER_FORBIDDEN')
CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
base.linprog=forbidden


def manifest():
    files={}
    for name,module in sorted(sys.modules.items()):
        file=getattr(module,'__file__',None)
        if file and Path(file).is_file():
            path=Path(file).resolve();key=str(path.relative_to(G)) if path.is_relative_to(G) else str(path)
            files[key]=d.sha(path)
    return files


def register():
    contract=d.rd(G/'retry/reframe578_next_contract.json');contract.update(study=579,status='FROZEN_BEFORE_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit='498c7ae0293ad6a18c6c74e74da85a65bbdcd05c',parent_contract_sha256=d.sha(G/'retry/reframe578_next_contract.json'))
    contract['beam']['deduplication']='NO_MERGE for states. Exact action byte dedup only, first enumeration ID retained. Factual tag is byte identity independent of retained ID.'
    contract['beam']['stageA']='Expand every live parent INCLUDING protected factual parent over up to13 actions. Exactly its factual byte-identical successor is protected; its modified children compete with all other parents for3 slots. Rejection or any stored row mismatch of protected successor hard stops. Once factual crosses, freeze its slot; never replace by fourth competitive slot.'
    contract['gates']['A'].update(baseline_before_raw=192,minimum_raw_gain=5,candidate_after_raw_max=187)
    contract['gates']['B'].update(baseline_before_raw=247,minimum_raw_gain=4,candidate_after_raw_max=243)
    contract['gates']['integer_rule']='Raw integer comparisons only, no float epsilon. Keep absolute original clocks. First forward crossing fixed before terminal recognition; recognize only after complete4raw strict-safe hold. Preserve terminals before live pruning. B starts actual completed selected A checkpoint and absolute hold index.'
    contract['budgets']['aggregate'].pop('force_evaluations');contract['budgets']['aggregate'].update(external_force=44000,internal_force=44000,total_force=88000)
    contract['budgets']['force_definition']='Count actual wheel_response invocations separately: external force_rows checks vs internal brake504_planar.step calls. Before each attempted raw reserve4 external/4 internal; preforce rejections count an attempt and4 external but0 internal. No hidden rollout.'
    contract['integrity']='Clone visited/tracker/launch/tracking per branch; recursively frozen root/roads only shared after proof. Full mutable parent/sibling fingerprints before/after every expansion. No successor cache. Independent identity probe remains a fresh separate hold from cloned prefix checkpoint, not reused as search successor. NO_MERGE.'
    contract['censoring']='Cost/time/deadline=>budget-censored; technical/body/domain/integrity/IO=>technical failure. Neither is scientific A/B falsification. B fail only selected A continuation; finite width/progress ranking failure only this finite method.'
    contract['input_sha256']={k:d.sha(p) for k,p in INPUTS.items()};contract['initial_visited_sha256']=digest(d.rd(INPUTS['ledger'])['initial_visited']);contract['dependency_file_sha256']=manifest();contract['implementation_sha256']={str(p.relative_to(G)):d.sha(p) for p in [Path(__file__),G/'retry/beam579_math.py',G/'tests/test_beam579.py']};contract['tests']=d.rd(G/'retry/beam579_tests.json');contract['preparation_prior_charge']={'CPU_s':contract['tests']['CPU_s']+1.,'wall_s':contract['tests']['wall_s']+1.,'meaning':'Measured tests plus conservative1s registration/hash preparation; runtime imports/preparation separately included.'}
    atomic_write(CONTRACT,contract)
    print(json.dumps({'registered':True,'dependency_files':len(contract['dependency_file_sha256']),'source_ticks':0}))


class BudgetStop(RuntimeError):pass
class Phase:
    def __init__(self,s,name):self.s=s;self.name=name;self.counter=[0];self.cost={'body_checks':0,'max_body':0.,'force_evaluations':0};self.pending=None
    def evaluate(self,root,action,history,context,peak,clip,check_clip):
        self.s.guard(attempts=1,external=4,internal=4);self.s.count('attempted_raw',1)
        result=evaluate_force(self.s.journal,d.short(root),action.tolist(),history,dict(bucket=self.name,**context),lambda:d.force_rows(root,action),peak,clip,check_clip)
        self.pending=dict(result,root_id=digest(d.short(root)),context=context,action=action.tolist());return result
    def tick(self,root,gas,brake,index,counter):
        p=self.pending
        if p is None or p['root_id']!=digest(d.short(root)) or [gas,brake]!=p['action'][1:]:raise RuntimeError('EXACT_FORCE_TICK_IDENTITY')
        completed=[False]
        def compute():
            after=d.source_tick(root,gas,brake,index,counter);completed[0]=True;return after
        try:
            after=guarded_tick(self.s.journal,p,p['context'],compute,base.body,d.short)
        finally:
            if completed[0]:self.s.count('completed_model_ticks',1)
        self.pending=None;self.cost['body_checks']+=1;self.cost['max_body']=max(self.cost['max_body'],base.body(after));return after
    def geometry(self,root):
        self.s.guard();self.s.count('geometry_checks',1);return d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])


class Study:
    raw=base.Study.raw
    def __init__(self):
        self.contract=d.rd(CONTRACT);self.prior=self.contract['preparation_prior_charge'];self.bucket='preparation';self.stage_start_cpu=START_CPU;self.stage_start_wall=START_WALL;self.phases={};self.phases['preparation']=dict(CPU_s=self.prior['CPU_s'],wall_s=self.prior['wall_s']);self.counts=Counter();self.stage_counts={};self.journal=None;self.error=None;self.events=[];self.best=None;self.best_prefix=None;self.root_ids={};self.root_refs={};self.result={};self.isolation_checks=0
        D.mkdir(mode=0o700,exist_ok=False);self.journal=Journal(D/'raw-journal-private.jsonl')
        self.guard()
        if any(d.sha(INPUTS[k])!=v for k,v in self.contract['input_sha256'].items()):raise RuntimeError('INPUT_HASH_MISMATCH')
        for f,v in self.contract['dependency_file_sha256'].items():
            p=G/f if not Path(f).is_absolute() else Path(f)
            if d.sha(p)!=v:raise RuntimeError('DEPENDENCY_HASH_MISMATCH:'+f)
        for f,v in self.contract['implementation_sha256'].items():
            if d.sha(G/f)!=v:raise RuntimeError('IMPLEMENTATION_HASH_MISMATCH:'+f)
        current=manifest()
        if any(f not in self.contract['dependency_file_sha256'] for f in current):raise RuntimeError('UNMANIFESTED_RUNTIME_IMPORT')
        self.tape,self.static,self.paths,self.ledger=[d.rd(INPUTS[k]) for k in ['tape','static','paths','ledger']]
        if digest(self.ledger['initial_visited'])!=self.contract['initial_visited_sha256']:raise RuntimeError('INITIAL_VISITED_HASH')
        self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.path=self.paths['candidate'];self.orig_external=wheel.wheel_response;self.orig_internal=planar.wheel_response
        immutable(d.load_root(self.static['root']))
        atomic_write(D/'STARTED.json',{'contract_sha256':d.sha(CONTRACT),'source_ticks':0,'initial_state_input_sha256':self.contract['input_sha256']})
    def count(self,key,n):self.counts[key]+=n;self.stage_counts.setdefault(self.bucket,Counter())[key]+=n
    def elapsed(self):return {'CPU_s':time.process_time()-START_CPU+self.prior['CPU_s'],'wall_s':time.perf_counter()-START_WALL+self.prior['wall_s']}
    def phase_times(self):
        out=copy.deepcopy(self.phases);active=out.setdefault(self.bucket,{});active['CPU_s']=active.get('CPU_s',0)+time.process_time()-self.stage_start_cpu;active['wall_s']=active.get('wall_s',0)+time.perf_counter()-self.stage_start_wall;return out
    def cost(self):return dict(total=dict(self.counts,**self.elapsed()),phases={k:dict(self.stage_counts.get(k,{}),**v) for k,v in self.phase_times().items()},external_force=self.counts['external_force'],internal_force=self.counts['internal_force'],total_force=self.counts['external_force']+self.counts['internal_force'])
    def guard(self,attempts=0,external=0,internal=0,child=False):
        caps=self.contract['budgets']['aggregate'];counts=self.counts;reserve=288 if child else 0
        for key,add,cap in [('attempted_raw',attempts+reserve,11000),('completed_model_ticks',reserve,11000),('external_force',external+4*reserve,44000),('internal_force',internal+4*reserve,44000),('geometry_checks',reserve,11000)]:
            if counts[key]+add>cap:raise BudgetStop('AGGREGATE_'+key)
        if counts['external_force']+counts['internal_force']+external+internal+8*reserve>88000:raise BudgetStop('AGGREGATE_total_force')
        times=self.elapsed();phase=self.phase_times()[self.bucket];limit=self.contract['budgets']['stage_caps'][self.bucket]
        for key in ['CPU_s','wall_s']:
            extra=(30 if key=='CPU_s' else 45) if child else 0
            if times[key]+extra>=caps[key] or phase[key]>=limit[key]:raise BudgetStop('TIME_'+self.bucket+'_'+key)
        if 'attempted_raw' in limit and self.stage_counts.get(self.bucket,{}).get('attempted_raw',0)+attempts>limit['attempted_raw']:raise BudgetStop('PHASE_ATTEMPTS_'+self.bucket)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc'].replace('Z','+00:00')):raise BudgetStop('DEADLINE')
    def switch(self,name):
        if name!='audit':self.guard()
        self.phases=self.phase_times();self.bucket=name;self.stage_start_cpu=time.process_time();self.stage_start_wall=time.perf_counter();self.phases.setdefault(name,{'CPU_s':0.,'wall_s':0.});self.guard()
    def wheel_call(self,kind,fn,*args,**kwargs):
        self.guard(external=1 if kind=='external_force' else 0,internal=1 if kind=='internal_force' else 0);self.count(kind,1);return fn(*args,**kwargs)
    def fingerprint(self,state):
        root=state['root'];key=id(root)
        if key not in self.root_ids:
            # Shared roots consist entirely of frozen dataclasses and tuples.
            # roads were recursively proven once; all successors retain that tuple.
            def fast(x):
                if is_dataclass(x):
                    if not x.__dataclass_params__.frozen:raise RuntimeError('MUTABLE_ROOT_DATACLASS')
                    return {f.name:fast(getattr(x,f.name)) for f in fields(x) if f.name!='roads'}
                if isinstance(x,tuple):return [fast(v) for v in x]
                if x is not None and not isinstance(x,(str,bool,int,float)):raise RuntimeError('MUTABLE_ROOT_FIELD')
                return x
            self.root_ids[key]=digest(fast(root));self.root_refs[key]=root
        return digest(dict(root=self.root_ids[key],roads_id=id(root.roads),visited=sorted(state['visited']),tracker=asdict(state['tracker']),launch=state['launch'],tracking=state['tracking'],elapsed=state['elapsed'],global_raw=state['global_raw'],progress=state['progress']))
    def factual_equal(self,row):
        old=self.tape['rows'][row['global_raw_before']]
        if not all(d.canonical(row.get(k))==d.canonical(old.get(k)) for k in KEYS):raise RuntimeError('FACTUAL_ROW_INTEGRITY')
    def hold(self,parent,action,index,phase,plane=None,factual=False):
        if not np.all(np.isfinite(action)):raise RuntimeError('CONTROL_DOMAIN_NONFINITE')
        state=clone(parent);isolated(state,[parent]);rows=[];hit=None
        for k in range(1,5):
            row,reason=self.raw(state,action,index,k,phase);rows.append(row)
            if reason:
                if factual:raise RuntimeError('FACTUAL_REJECTED:'+reason)
                return {'state':state,'rows':rows,'failure':reason,'crossing':None}
            if state['root'].roads is not parent['root'].roads:raise RuntimeError('ROOT_ROADS_IDENTITY')
            if factual:self.factual_equal(row)
            if hit is None and plane is not None:hit=crossing(row,plane)
            if self.best_prefix is None or state['progress']>self.best_prefix['state']['progress']:self.best_prefix={'state':clone(state),'row':row,'partial_hold_raw':k}
        return {'state':state,'rows':rows,'failure':None,'crossing':hit}
    def node_summary(self,node):
        state=node['state'];return dict(global_raw=state['global_raw'],hold=state['global_raw']//4,elapsed_s=state['elapsed'],progress_m=state['progress'],COM_speed_m_s=math.hypot(*state['root'].planar.linear.velocity),crossing=node.get('crossing'),factual=node.get('factual',False),checkpoint_sha256=self.fingerprint(state))
    def stage(self,name,start):
        spec=self.contract['gates'][name];plane=self.contract['gates']['planes'][0 if name=='A' else 1];phase=Phase(self,'search');live=[start];terminals=[];pruning=Counter();depths=[];factual_frozen=False
        for depth in range(1,(spec['max_holds'] if name=='A' else spec['max_additional_holds'])+1):
            if not live:break
            children=[];protected=None
            for parent in live:
                index=parent['state']['global_raw']//4+1
                for proposal in actions(parent['state'],self.path,self.commands[index]):
                    self.guard(attempts=4,external=16,internal=16,child=True)
                    guards=[n['state'] for n in live+children];before=[self.fingerprint(s) for s in guards]
                    isfact=name=='A' and parent.get('factual',False) and proposal['factual_action']
                    try:edge=self.hold(parent['state'],proposal['action'],index,phase,plane,isfact)
                    finally:
                        if before!=[self.fingerprint(s) for s in guards]:raise RuntimeError('PARENT_SIBLING_MUTATED')
                        self.isolation_checks+=len(guards)
                    isolated(edge['state'],guards)
                    if edge['failure']:pruning[edge['failure']]+=1;continue
                    node=dict(state=edge['state'],rows=parent['rows']+edge['rows'],commands=parent['commands']+[(index,proposal['action'].tolist())],ids=parent['ids']+[proposal['id']],factual=isfact,crossing=edge['crossing'])
                    if self.best is None or node['state']['progress']>self.best['state']['progress']:self.best=node
                    if node['crossing'] is not None:
                        # Save terminal before any live pruning. Never replace its first crossing.
                        terminals.append(node)
                        if isfact:factual_frozen=True
                        if not node['crossing']['eligible']:pruning['PLANE_OUTSIDE_WINDOW']+=1
                        elif not passes(node['crossing'],spec):pruning['TERMINAL_GATE']+=1
                        continue
                    if isfact:protected=node
                    else:children.append(node)
            children.sort(key=lambda n:rank_key(n,self.path));slots=3 if name=='A' else 4
            pruning['BEAM_WIDTH']+=max(0,len(children)-slots);live=children[:slots]
            if protected is not None:live.append(protected)
            if name=='A' and not factual_frozen and protected is None:raise RuntimeError('FACTUAL_SLOT_LOST')
            detail={'depth':depth,'live':len(live),'terminals':len(terminals),'factual_frozen':factual_frozen,'best_progress_m':max((n['state']['progress'] for n in live),default=None),'cost':self.cost()};depths.append(detail)
            self.journal.append('BEAM_DEPTH',stage=name,**detail);atomic_write(D/(name+'-latest-private.json'),{'depth':depth,'live':[dict(checkpoint=d.Study.checkpoint(self,n['state']),ids=n['ids']) for n in live],'cost':self.cost()},True)
        passing=[n for n in terminals if passes(n['crossing'],spec)];passing.sort(key=terminal_key);selected=passing[0] if passing else None
        summary=dict(completed_depths=len(depths),pruning=dict(pruning),terminal_count=len(terminals),passing_terminals=len(passing),selected=self.node_summary(selected) if selected else None,best_terminal=min((self.node_summary(n) for n in terminals),key=lambda s:(s['crossing']['after_raw'],-s['crossing']['COM_speed_m_s']),default=None),depths=depths)
        atomic_write(D/(name+'-terminals-private.json'),{'terminals':[dict(checkpoint=d.Study.checkpoint(self,n['state']),crossing=n['crossing'],ids=n['ids'],commands=n['commands']) for n in terminals],'summary':summary})
        self.result[name]=summary
        return selected
    def run(self):
        selected=None;prefix=[];replay=None;status=None
        wheel.wheel_response=lambda *a,**k:self.wheel_call('external_force',self.orig_external,*a,**k)
        planar.wheel_response=lambda *a,**k:self.wheel_call('internal_force',self.orig_internal,*a,**k)
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(BudgetStop('CPU_SIGNAL')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(BudgetStop('WALL_SIGNAL')));signal.setitimer(signal.ITIMER_PROF,max(.01,400-self.elapsed()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,540-self.elapsed()['wall_s']))
        try:
            self.switch('prefix_identity');phase=Phase(self,'prefix_identity');state=d.Study.initial(self);immutable(state['root'])
            for index in range(1,25):
                edge=self.hold(state,self.commands[index],index,phase,factual=True);prefix+=edge['rows'];state=edge['state']
            before=self.fingerprint(state);probe=self.hold(state,self.commands[25],25,phase,factual=True)
            if self.fingerprint(state)!=before:raise RuntimeError('IDENTITY_PROBE_MUTATED_PREFIX')
            self.result['prefix_identity']={'prefix_raw':96,'independent_probe_raw':4,'all_stored_fields_exact':True,'probe_not_reused':True,'start_checkpoint_sha256':before}
            atomic_write(D/'prefix-checkpoint-private.json',d.Study.checkpoint(self,state))
            start={'state':clone(state),'rows':prefix,'commands':[(i,self.commands[i].tolist()) for i in range(1,25)],'ids':[],'factual':True,'crossing':None}
            self.switch('search');A=self.stage('A',start)
            if A is None:status='A_FINITE_SEARCH_NO_PASS'
            else:
                B=self.stage('B',dict(A,factual=False,crossing=None))
                if B is None:status='SELECTED_A_B_CONTINUATION_NO_PASS'
                else:
                    selected=B;self.switch('verification');phase=Phase(self,'verification');verify=d.Study.initial(self);immutable(verify['root']);actual=[]
                    for index,action in B['commands']:
                        edge=self.hold(verify,np.asarray(action,np.float32),index,phase);actual+=edge['rows'];verify=edge['state']
                        if edge['failure']:raise RuntimeError('INDEPENDENT_REPLAY_REJECTED:'+edge['failure'])
                    exact=len(actual)==len(B['rows']) and all(all(d.canonical(a.get(k))==d.canonical(b.get(k)) for k in KEYS) for a,b in zip(actual,B['rows']));cp=d.canonical(d.Study.checkpoint(self,verify))==d.canonical(d.Study.checkpoint(self,B['state']))
                    if not exact or not cp:raise RuntimeError('INDEPENDENT_REPLAY_MISMATCH')
                    hits=[]
                    for plane in self.contract['gates']['planes']:
                        hit=next((h for r in actual if (h:=crossing(r,plane)) is not None),None);hits.append(hit)
                    if hits!=[A['crossing'],B['crossing']]:raise RuntimeError('REPLAY_CROSSING_MISMATCH')
                    replay={'raw':len(actual),'all_state_force_history_visited_tracker_clock_exact':exact,'checkpoint_exact':cp,'crossings_exact':True};atomic_write(D/'verified-tape-private.json',{'rows':actual,'commands':B['commands'],'checkpoint':d.Study.checkpoint(self,verify)});status='LOCAL_A_B_PASS_EXACT_REPLAY'
        except BaseException as exc:
            self.error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'TECHNICAL_FAILURE'
            atomic_write(D/'failure-private.json',{'error':self.error,'traceback':traceback.format_exc(),'cost':self.cost(),'result':self.result},True)
        finally:
            # Cost first; preserve partial result and no restart even after failure.
            atomic_write(G/'retry/beam579_cost.json',self.cost(),True)
            wheel.wheel_response=self.orig_external;planar.wheel_response=self.orig_internal
            try:
                self.switch('audit');self.journal.close();audit=inspect(D/'raw-journal-private.jsonl');self.guard()
                if self.best:atomic_write(D/'best-safe-complete-private.json',{'summary':self.node_summary(self.best),'checkpoint':d.Study.checkpoint(self,self.best['state']),'commands':self.best['commands']})
                if self.best_prefix:atomic_write(D/'best-safe-prefix-private.json',{'checkpoint':d.Study.checkpoint(self,self.best_prefix['state']),'partial_hold_raw':self.best_prefix['partial_hold_raw']})
                closure_ok=all(d.sha(G/f if not Path(f).is_absolute() else Path(f))==v for f,v in self.contract['dependency_file_sha256'].items())
                if not closure_ok:raise RuntimeError('FINAL_DEPENDENCY_HASH_MISMATCH')
                if any(f not in self.contract['dependency_file_sha256'] for f in manifest()):raise RuntimeError('FINAL_UNMANIFESTED_RUNTIME_IMPORT')
                self.guard()
            except BaseException as exc:
                audit={'valid':False,'error':type(exc).__name__+':'+str(exc)};status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'TECHNICAL_FAILURE';self.error=(self.error or '')+';AUDIT:'+str(exc)
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            self.result.update(status=status,error=self.error,independent_replay=replay,journal=audit,cost=self.cost(),best_safe_completed=self.node_summary(self.best) if self.best else None,best_safe_partial_prefix=self.node_summary(self.best_prefix) if self.best_prefix else None,parent_sibling_fingerprints_checked=self.isolation_checks,source_native_scope='Source DEV only; no whole finish or policy promotion',native_actions=0,HOLDOUT=0,SEALED=0,LP_solves=0,nonlinear_solves=0,new_FD=0,new_calibration=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0)
            atomic_write(G/'retry/beam579_cost.json',self.cost(),True);atomic_write(G/'retry/beam579_result.json',self.result);print(json.dumps(plain(self.result),indent=2))

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=Study();study.run()
        except BaseException as exc:
            # Preparation failures cannot silently rerun or enter source.
            failure={'status':'PREPARATION_TECHNICAL_FAILURE','error':type(exc).__name__+':'+str(exc),'traceback':traceback.format_exc(),'cost':study.cost() if study else {'CPU_s':time.process_time()-START_CPU,'wall_s':time.perf_counter()-START_WALL},'source_execution_started':bool(study and study.counts['attempted_raw']), 'actual_counts':dict(study.counts) if study else {}}
            if D.exists():atomic_write(D/'preparation-failure-private.json',failure,True)
            atomic_write(G/'retry/beam579_preparation_failure.json',dict(failure,traceback='private'));raise
