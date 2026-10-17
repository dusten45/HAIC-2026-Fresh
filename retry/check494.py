"""494 once-only physics-poisoned callback checkpoint. Does not authorize runs."""
import time
START=time.perf_counter()
import contextlib,datetime,hashlib,json,os,resource,shutil,signal,subprocess,traceback,sys
from pathlib import Path
from unittest.mock import patch
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');D=R/'stage494'
if len(sys.argv)>1:
    check_name=sys.argv[1]
    if check_name!='validation2':raise ValueError('494_only_registered_static_repair')
    D=D/check_name
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(v,msg):
    if not v:raise RuntimeError('494_'+msg)
def save(p,v):
    check(not p.exists(),'OUTPUT_EXISTS');data=(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();check(len(data)<2*1024**2,'OUTPUT_SIZE')
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(p,0o600);check(p.read_bytes()==data,'OUTPUT_READBACK')
def run():
    check(not D.exists(),'ONCE');check(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'),'DEADLINE')
    for volume in ('/tmp','/workspace'):check(shutil.disk_usage(volume).free>512*1024**2,'FREE_RESERVE')
    preserved={}
    for stage in (492,493):
        manifest=R/f'stage{stage}-retention-final-private.json'
        for e in json.loads(manifest.read_text())['files']:preserved[e['path']]=e['sha256']
        for p in (manifest,R/f'stage{stage}-publication-private.json'):preserved[str(p)]=sha(p)
    for p in (R/'project-effective-budget-v492.json',R/'research-deadline-current.json'):preserved[str(p)]=sha(p)
    previous=json.loads((R/'stage493/plan-private.json').read_text())
    preserved.update(previous['preserved']);preserved.update(previous['sources'])
    for p,h in preserved.items():check(sha(p)==h,'PRESERVATION:'+p)
    paths=[G/'retry'/n for n in ('capture494.py','test_capture494.py','check494.py','capture494_contract.json')]
    sources={str(p):sha(p) for p in paths}
    D.mkdir(mode=0o700)
    save(D/'plan-private.json',dict(stage=494,sources=sources,preserved=preserved,physics_allowed=False,registered_before_fixtures=True,deadline_utc='2026-10-20T10:01:55Z',caps=dict(CPU_s=90,wall_s=120,RSS_bytes=268435456,new_files=160,new_bytes=16*1024**2,worlds=0,resets=0,steps=0),no_followup=True))
    def timeout(*_):raise RuntimeError('494_CPU90_WALL120')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_PROF,max(.001,90-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,120-(time.perf_counter()-START)))
    from retry.runtime492 import Graph
    graph=Graph({},dict(line=[[0.,0.],[1.,0.],[0.,1.]],free_profile=dict(ds=[1.,1.,1.],speed=[0.,1.,1.,1.],curvature=[0.,0.,0.]),model={}),[1.,1.,1.,1.],[0.,1.,1.,1.]).install()
    for name in ('actual437_boundary','observer435','capture434','authority439','planner419'):graph.import_module(name)
    from retry.test_capture494 import run as tests
    from retry.capture494 import BINDING_KEYS
    binding={key:sha(G/'retry/capture494.py') if key=='capture494_sha256' else 'a'*64 for key in BINDING_KEYS}
    import Box2D
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    forbidden_hits=[]
    def forbidden(*a,**k):forbidden_hits.append('physical_entry');raise AssertionError('494_PHYSICS_POISON')
    with contextlib.ExitStack() as stack:
        original=Box2D.b2World;stack.enter_context(patch.object(Box2D,'b2World',forbidden));classes={CarRacing,Car}
        for m in graph.modules.values():
            for key,value in list(vars(m).items()):
                if isinstance(value,type) and key in ('TerminalVehicleTransition','SourceVehicleTransition'):classes.add(value)
                if value is original or key=='make_env':stack.enter_context(patch.object(m,key,forbidden))
        for cls in classes:
            for name in ('__init__','reset','step'):
                if hasattr(cls,name):stack.enter_context(patch.object(cls,name,forbidden))
        result=tests(graph,D/'synthetic-receipts',binding)
    check(not forbidden_hits,'PHYSICS_ENTRY_ATTEMPT');result.update(stage=494,status='STATIC_CALLBACK_CHECKPOINT_PASSED_NO_PHYSICS',physics_poison_attempts=len(forbidden_hits),synthetic_binding_only=True,real_execution_source_qualified=False,real_ObserveMixin_one_not_executed=True,native_callsite='isolated Dispatch437.call on fake env',model_callsite='isolated ObserveMixin PostTrackerTap alias on fake model/controller',CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,research_remaining=26101,reserve=84000,reserve_used=0,best_s=13.640,deadline_utc='2026-10-20T10:01:55Z',checkpoint_review_required_before_any_physics=True,no_auto_followup=True)
    for p,h in {**preserved,**sources}.items():check(sha(p)==h,'FINAL_PRESERVATION:'+p)
    save(D/'result-private.json',result)
    files=[p for p in D.rglob('*') if p.is_file()]
    check(len(files)<160 and sum(p.stat().st_size for p in files)<16*1024**2,'FINAL_QUOTA')
    for p in files:json.loads(p.read_text());check(sha(p)==hashlib.sha256(p.read_bytes()).hexdigest(),'DOUBLE_READBACK')
    save(D/'retention-private.json',dict(stage=494,files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files],physics=0))
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({k:result[k] for k in ('stage','status','test_count','positive_holds','receipt_files','receipt_bytes','physical_worlds','physical_resets','physical_steps','physics_poison_attempts','CPU_s','wall_s')}),flush=True)
if __name__=='__main__':run()
