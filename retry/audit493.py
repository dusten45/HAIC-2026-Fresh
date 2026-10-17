"""493 pure saved-data audit with prospective registration and physics poison."""
import time
START=time.perf_counter()
import ast,contextlib,copy,datetime,hashlib,json,os,resource,shutil,signal,subprocess,sys,traceback
from pathlib import Path
from unittest.mock import patch
from retry.schema493 import receipt,adapt_hold,complete493,MissingEvidence493,SchemaError493,digest,source_ref,clock

G=Path(__file__).resolve().parents[1]
R=Path('/workspace/haic-private-retry-20261009');D=R/'stage493'
RAW=Path('/tmp/haic-retry-stage492-private');N=RAW/'native/D492-A';M=RAW/'model'
DEADLINE='2026-10-20T10:01:55Z'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
    if not x:raise RuntimeError('493_'+msg)
def plain(v):
    if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    if type(v).__module__.startswith('numpy') and hasattr(v,'item'):return plain(v.item())
    return v

def guard():
    require(time.process_time()<90 and time.perf_counter()-START<120,'CPU90_WALL120')
    require(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'DEADLINE')
    for p in ('/tmp','/workspace'):require(shutil.disk_usage(p).free>=512*1024**2,'STORAGE_RESERVE')

class Store:
    def __init__(self):self.records={}
    def save(self,p,value):
        guard();p=Path(p);data=(json.dumps(plain(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        require(len(data)<=2*1024**2,'PERFILE2MIB')
        proposed={**self.records,str(p):len(data)}
        require(len(proposed)<=64 and sum(proposed.values())<=8*1024**2,'OUTPUT8MIB_64FILES')
        require(not p.exists() or str(p) in self.records,'EXISTING_OUTPUT_FORBIDDEN')
        temp=p.with_name(p.name+'.tmp');require(not temp.exists(),'TEMP_EXISTS')
        with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,p);fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        require(p.read_bytes()==data,'WRITE_READBACK');self.records=proposed

def poison_graph(graph):
    import Box2D
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    stack=contextlib.ExitStack()
    def forbidden(*a,**k):raise AssertionError('493_PHYSICS_ENTRY_FORBIDDEN')
    original=Box2D.b2World
    stack.enter_context(patch.object(Box2D,'b2World',forbidden))
    classes={CarRacing,Car}
    for m in graph.modules.values():
        for k,v in list(vars(m).items()):
            if isinstance(v,type) and k in ('TerminalVehicleTransition','SourceVehicleTransition'):classes.add(v)
            if v is original or k=='make_env':stack.enter_context(patch.object(m,k,forbidden))
    for cls in classes:
        for name in ('__init__','reset','step'):
            if hasattr(cls,name):stack.enter_context(patch.object(cls,name,forbidden))
    return stack

def saved_first_compare():
    import numpy as np
    from retry.executor490_input import load,array_sha
    from retry.runtime492 import Graph
    manifest=Path('/tmp/haic-retry-stage490-private/input-manifest-private.json')
    fixed,pace,nodes=load(manifest)
    def lists(v):
        if isinstance(v,np.ndarray):return v.tolist()
        if isinstance(v,dict):return {k:lists(x) for k,x in v.items()}
        return v
    fixed=lists(fixed);binding=receipt(M/'result.json')['binding']
    require(sha(manifest)==binding['input_manifest_sha256'] and array_sha(fixed['line'])==binding['line_sha256'] and array_sha(nodes)==binding['nodes_sha256'],'FROZEN490_INPUT')
    graph=Graph(binding,fixed,pace,nodes).install()
    ledger=graph.import_module('ledger439');Goal=graph.import_module('planner419').GoalLedger
    witness=receipt(N/'witness-1-private.json')
    observer_path=next(M.glob('*-D492-A_source_1-observer-final-private.json'))
    observer=receipt(observer_path);frame=observer['actions'][0]['frozen_row']
    with poison_graph(graph):
        old=Goal(**witness['ledger_before'])
        actual,report=ledger.compare_first(old,frame,witness['row'],fixed)
        require(actual.__dict__==witness['ledger_after'],'SAVED_ACTUAL_LEDGER_JOIN')
        alias=graph.audit()
    return dict(stage=493,status='SAVED_FIRST_COLD_NUMERIC_AND_LEDGER_SUBGATE_PASSED',report=plain(report),source_alias_modules=alias['modules'],native_witness_ref=source_ref(N/'witness-1-private.json','/row'),model_frame_ref=source_ref(observer_path,'/actions/0/frozen_row'),full_raw_gate_passed=False,missing_raw_evidence_not_repaired=True,worlds=0,ticks=0,resets=0,original492_status_unchanged=True)

def native_hold(step):
    before_path=N/f'action-{step}-before-native-private.json';after_path=N/f'action-{step}-after-native-private.json';fact_path=N/f'action-{step}-fact-private.json'
    b=receipt(before_path);a=receipt(after_path);f=receipt(fact_path);row=f['row']
    require(row['step']==step,'NATIVE_STEP')
    pre=b['full_pre_before_nominal'];prepared=b['full_pre_after_nominal'];post=a['full_post']
    require(pre['physical']['actual_time']==prepared['physical']['actual_time']==row['pre']['time'] and post['physical']['actual_time']==row['post']['time'],'FULL_BOUNDARY_CLOCK')
    require(pre['controller']==row['memory_before'] and prepared['controller']==post['controller']==row['nominal_memory_after'],'FULL_CONTROLLER_BOUNDARIES')
    require(post['physical']['damage']==row['damage'] and post['physical']['hull']['position']==row['post']['pos'],'FULL_BOUNDARY_DAMAGE_BODY')
    out=adapt_hold(owner='D492-A',post_rows=a['posts'],tires=row['raw_tire_samples'],hulls=row['raw_hull'],ledger_before=f['ledger_before'],ledger_after=f['ledger_after'],nominal_phase=row['nominal_memory_after']['C']['phase'],hold_end_damage=post['physical']['damage'],hold_end_time=post['physical']['actual_time'],provenance=source_ref(after_path,'/posts'),collision_kind='RAW_STEP_EVENT')
    require(a['posts'][-1]['time']==post['physical']['actual_time'] and a['posts'][-1]['position']==post['physical']['hull']['position'],'LAST_POST_BOUNDARY_JOIN')
    return out,f,a,b

def run():
    require(not D.exists(),'ONCE_NEW_OUTPUT');guard()
    require(receipt(R/'research-deadline-current.json')['deadline_utc']==DEADLINE,'CURRENT_DEADLINE')
    pins={}
    previous=receipt(R/'stage492-retention-final-private.json')
    for entry in previous['files']:pins[entry['path']]=entry['sha256']
    for p in [R/'stage492-publication-private.json',R/'stage492-retention-final-private.json',R/'project-effective-budget-v492.json']:pins[str(p)]=sha(p)
    for path,h in pins.items():require(sha(path)==h,'PRIOR_PIN:'+path)
    old=receipt(R/'stage485/plan-private.json')
    for group in ('sources','protected','original408_preserve'):
        pins.update(old[group])
    for path,h in pins.items():require(sha(path)==h,'PRESERVATION:'+path)
    ledger=receipt(R/'project-effective-budget-v492.json');require(ledger['research_remaining']==26101 and ledger['final_reserved_actions']==84000 and ledger['final_reserve_used']==0,'BALANCE')
    paths=[G/'retry'/n for n in ('schema493.py','test_schema493.py','audit493.py','schema493_contract.json')]
    # Source timings from original492 semantic closure and stage493 registrations.
    sourcepaths=[G/'env_wrapper.py',G/'damage.py',G/'core/vendor/car_racing.py',G/'core/vendor/car_dynamics.py',G/'retry/authority439.py',G/'retry/actual437_boundary.py',G/'retry/observer435.py',G/'retry/capture434.py',G/'retry/fork394_run.py',G/'retry/headroom413_run.py',G/'retry/terminal410_model.py',G/'retry/planner419.py']
    sourcepins={str(p):sha(p) for p in paths+sourcepaths}
    D.mkdir(mode=0o700);store=Store()
    plan=dict(stage=493,deadline_utc=DEADLINE,contract_sha256=sha(G/'retry/schema493_contract.json'),sources=sourcepins,preserved=pins,no_physics=True,new_actions=0,new_resets=0,new_model_ticks=0,strict_same_tick_and_microphase=True,registered_before_fixtures=True)
    store.save(D/'plan-private.json',plan)
    def timeout(*_):raise RuntimeError('493_RESOURCE_OR_DEADLINE')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_PROF,max(.001,90-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,120-(time.perf_counter()-START)))
    from retry.test_schema493 import run as synthetic
    tests=synthetic();store.save(D/'synthetic-private.json',tests)
    # All old raw bytes and codec payloads, including state objects and journals.
    schema_counts={};count=0;rawbytes=0
    for path in sorted(RAW.rglob('*')):
        if not path.is_file():continue
        guard();require(str(path) in pins and sha(path)==pins[str(path)],'RAW_UNPINNED_OR_CHANGED')
        if path.suffix=='.json':
            value=receipt(path);key=('list' if isinstance(value,list) else value.get('schema','dictionary'))
        elif path.suffix=='.jsonl':
            lines=[json.loads(line) for line in path.read_text().splitlines()];key='charge_jsonl'
            require([x['sequence'] for x in lines]==list(range(1,len(lines)+1)),'CHARGE_SEQUENCE')
        else:raise RuntimeError('493_UNKNOWN_RAW_SUFFIX')
        schema_counts[key]=schema_counts.get(key,0)+1;count+=1;rawbytes+=path.stat().st_size
    native=[];last=None;missing_native=0;tickcount=0
    for step in range(1,75):
        guard();out,f,a,b=native_hold(step)
        if last is not None:require(last==f['ledger_before'],'GOALLEDGER_CHAIN')
        last=f['ledger_after'];tickcount+=len(out['rows']);missing_native+=out['missing_count']
        try:complete493(out)
        except MissingEvidence493:pass
        else:raise RuntimeError('493_UNEXPECTED_RAW_AUTHORITY')
        native.append(dict(step=step,ticks=len(out['rows']),missing=[dict(raw_clock=p['raw_clock'],fields=p['missing']) for p in out['rows']],pre_force_grass_available=True,nominal_phase_available=True,wrapper_end_damage_available=True,raw_post_collision_contact_available=True,provenance=out['rows'][0]['provenance']))
    proof=receipt(N/'prefix-root-proof-private.json');require(proof['actions']==72 and proof['witness_count']==2,'ROOT_SCOPE')
    w1=receipt(N/'witness-1-private.json');w2=receipt(N/'witness-2-private.json')
    root=receipt(N/'root-full-private.json');root.pop('binding',None)
    require(root==w1['full_pre'] and w1['full_post']==w2['full_pre'] and w1['ledger_after']==w2['ledger_before'],'ROOT_TWO_WITNESS_EXACT_CHAIN')
    for i,w in enumerate((w1,w2),1):
        out,f,a,b=native_hold(72+i)
        require(w['row']==f['row'] and w['posts']==a['posts'] and w['full_pre']==b['full_pre_before_nominal'] and w['full_post']==a['full_post'],'WITNESS_SAVED_JOIN')
    op=next(M.glob('*-D492-A_source_1-observer-final-private.json'));observer=receipt(op)
    require(len(observer['actions'])==1 and len(observer['posts'])==4,'EXISTING_COLD_ONCE')
    action=observer['actions'][0];frame=action['frozen_row'];snap=observer['snapshot']
    model=adapt_hold(owner=observer['link']['child_id'],post_rows=observer['posts'],tires=frame['tires'],hulls=frame['raw_hull'],ledger_before=observer['link']['model_ledger'],ledger_after=action['ledger_after'],nominal_phase=frame['memory_after']['C']['phase'],hold_end_damage=snap['physical']['damage'],hold_end_time=snap['physical']['actual_time'],provenance=source_ref(op,'/posts'),collision_kind='RAW_STEP_EVENT_OR_CONTACTS_LATCH')
    require(all(p['damage']==frame['predicted']['damage']==snap['physical']['damage'] for p in observer['posts']),'MODEL_POST_DAMAGE_WRAPPER_BROADCAST')
    store.save(D/'native-schema-audit-private.json',dict(stage=493,holds=native,raw_ticks=tickcount,missing_native_fields=missing_native,all_native_holds_incomplete=True))
    store.save(D/'first-cold-schema-audit-private.json',model)
    first=saved_first_compare();store.save(D/'saved-first-cold-subgate-private.json',first)
    for path,h in {**pins,**sourcepins}.items():require(sha(path)==h,'FINAL_IMMUTABILITY:'+path)
    result=dict(stage=493,status='INSUFFICIENT_DIRECT_RAW_TICK_EVIDENCE',synthetic=tests,saved492_raw_files=count,saved492_raw_bytes=rawbytes,saved492_schema_counts=schema_counts,native_holds=74,native_raw_action_ticks=tickcount,native_complete_holds=0,native_missing_damage_ticks=tickcount,native_missing_direct_phase_ticks=tickcount,native_grass_pre_world_ticks=tickcount,native_collision_and_contact_post_ticks=tickcount,native_goal_ledger_chain_passed=True,root_and_two_witnesses_chain_passed=True,witness_raw_ticks=8,witness_missing_damage_ticks=8,witness_missing_direct_phase_ticks=8,existing_first_cold_ticks=4,first_cold_partial_numeric_and_ledger_passed=True,first_cold_full_raw_gate_passed=False,model_damage_provenance='WRAPPER_END_VALUE_BROADCAST_TO_RAW_ROWS_NOT_DIRECT_TRACKER_POST',collision_schema_note='Native RAW_STEP_EVENT; model RAW_STEP_EVENT_OR_CONTACTS_LATCH. No guessing event decomposition from aggregate.',source_gate_passed=False,root_source_authority_qualified=False,model_only_resume_contract_proposed=False,minimum_missing_measurements=dict(native_witness_tracker_posts=8,direct_damage_values=8,direct_controller_phase_values=8,model_direct_tracker_posts_needed_for_full_source_gate=True),native_world_closed_in492=True,recollection_transport_note='492 native world was destroyed. New direct native measurements cannot be added to old ticks. Same-case exact prefix reproduction would require a new reset and72prefix+2witness actions; separate authorization and reset identity/root gates required. No such execution in493.',new_actual_actions=0,new_resets=0,new_model_worlds=0,new_model_ticks=0,new_profile_P4_seed_conditions_HOLDOUT_SEALED=0,research_remaining=26101,reserve=84000,reserve_used=0,best_s=13.640,original492_failure_cost_immutable=True,preserved_entries=len(pins),CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,no_auto_followup=True,deadline_utc=DEADLINE)
    store.save(D/'result-private.json',result)
    # Every493 output has complete readback; no raw state/pose copies are saved.
    inv=[dict(path=path,bytes=n,sha256=sha(path)) for path,n in store.records.items()]
    store.save(D/'retention-private.json',dict(stage=493,files=inv,original492_files_unchanged=True,no_raw_copies=True))
    guard();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({k:result[k] for k in ('stage','status','saved492_raw_files','native_holds','native_raw_action_ticks','witness_missing_damage_ticks','first_cold_partial_numeric_and_ledger_passed','new_actual_actions','new_model_ticks','CPU_s','wall_s')}),flush=True)

if __name__=='__main__':run()
