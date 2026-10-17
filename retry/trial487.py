"""Single feasibility-first AST clone; no simulator or condition generation."""
import time
START=time.perf_counter()
import ast,copy,datetime,hashlib,json,math,signal,sys,traceback,unittest,io
from pathlib import Path
import numpy as np
import retry.racing258_plan as original
import retry.racing258_feasibility as repair_source
from retry.quota487 import Quota
G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage487-private')
DEV_CPU=5.;DEV_WALL=5.
EXTRA_FILES=9;EXTRA_BYTES=128*1024
DEADLINE='2026-10-20T10:01:55Z'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def plain(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x
def digest(x):return hashlib.sha256(json.dumps(plain(x),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def arrayhash(a):return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes()).hexdigest()
def key(V,T,rough):return V,T+rough

def transformed():
    source=ast.parse((G/'retry/racing258_plan.py').read_text())
    fn=copy.deepcopy(next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='solve'))
    evaluate=next(n for n in fn.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate')
    score=next(n for n in evaluate.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='score' for t in n.targets))
    # Strip only the original1000*violation term. Preserve original source
    # evaluation order for T+rough and all feasibility arithmetic.
    old=copy.deepcopy(score.value);assert ast.unparse(old).startswith("p['estimated_time_s'] + 1000 * violation +")
    score.value=ast.Tuple(elts=[ast.Name(id='violation',ctx=ast.Load()),ast.BinOp(left=copy.deepcopy(old.left.left),op=ast.Add(),right=copy.deepcopy(old.right))],ctx=ast.Load())
    semantic=ast.dump(fn,include_attributes=False)
    evaluate.body.insert(-1,ast.parse('capture_evaluation(theta,score,path,p,clear,violation,calls,offset)').body[0])
    outer=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step')
    inner=next(n for n in outer.body if isinstance(n,ast.For))
    assignment=next(i for i,n in enumerate(inner.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Tuple))
    inner.body.insert(assignment+1,ast.parse('capture_accepted(step,j,coeff,best[0],calls)').body[0])
    first_index=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='first' for t in n.targets))
    fn.body.insert(first_index,ast.parse('capture_initial(coeff)').body[0])
    module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
    return module,semantic,ast.dump(next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='profile'),include_attributes=False)

def transformed_repair():
    tree=ast.parse((G/'retry/racing258_feasibility.py').read_text())
    fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='project'))
    original_ast=ast.dump(fn,include_attributes=False)
    ix=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assert))
    fn.body.insert(ix,ast.parse('capture_repair(theta,line,c,p,calls,old)').body[0])
    return ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),original_ast

def static():
    from retry.test_quota487 import Quota487Tests
    out=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Quota487Tests)
    result=unittest.TextTestRunner(stream=out).run(suite);assert result.wasSuccessful(),out.getvalue()
    assert key(.01,1e9,1)>key(0,1e100,1)
    assert key(0,3,1)==key(0,2,2) and not key(0,3,1)<key(0,2,2)
    assert key(0,3,.1)<key(0,4,.1)
    module,semantic,profile_ast=transformed()
    # Remove instrumentation and compare with an independently constructed
    # expected original tree with exactly one score expression replaced.
    clean=copy.deepcopy(module.body[0])
    for node in ast.walk(clean):
        if hasattr(node,'body') and isinstance(node.body,list):node.body[:]=[n for n in node.body if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id in ('capture_evaluation','capture_accepted','capture_initial'))]
    assert ast.dump(clean,include_attributes=False)==semantic
    original_solve=ast.parse((G/'retry/racing258_plan.py').read_text())
    expected=copy.deepcopy(next(n for n in original_solve.body if isinstance(n,ast.FunctionDef) and n.name=='solve'))
    ev=next(n for n in expected.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate')
    target=next(n for n in ev.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='score' for t in n.targets))
    target.value=ast.parse("(violation,p['estimated_time_s']+.001*np.sum((np.roll(theta,-1)-theta)**2))",mode='eval').body
    assert ast.dump(expected,include_attributes=False)==semantic
    rm,ra=transformed_repair();clean_repair=copy.deepcopy(rm.body[0]);clean_repair.body=[n for n in clean_repair.body if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='capture_repair')];assert ast.dump(clean_repair,include_attributes=False)==ra
    assert not any(n.startswith(('Box2D','env_wrapper','core.vendor.car_racing')) for n in sys.modules)
    return dict(passed=True,quota_tests=result.testsRun,structural_checks=['only score semantics changed','unchanged profile AST','all194 capture location','strict tuple/tie/time-rough ordering','no physics imports'],tests=result.testsRun+6,profile_ast_sha256=hashlib.sha256(profile_ast.encode()).hexdigest(),candidate_semantic_ast_sha256=hashlib.sha256(semantic.encode()).hexdigest())

def run(root):
    root=Path(root);assert not RAW.exists();RAW.mkdir(mode=0o700);q=Quota(RAW);q.MAX_FILES=32-EXTRA_FILES;q.MAX_BYTES=8*1024**2-EXTRA_BYTES
    counts=dict(road_solver=0,objectives=0,profiles=0,repair_calls=0,repair_clearance=0)
    def guard():
        if not(time.process_time()+DEV_CPU<60 and time.perf_counter()-START+DEV_WALL<90):raise RuntimeError('487_WHOLE_CAP')
        if not(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))):raise RuntimeError('487_DEADLINE')
        q.diskpreflight()
    def timeout(*_):raise RuntimeError('487_CPU_WALL_OR_DEADLINE')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_PROF,max(.001,60-time.process_time()-DEV_CPU));signal.setitimer(signal.ITIMER_REAL,max(.001,min(90-(time.perf_counter()-START)-DEV_WALL,(datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
    status='PREPARING';error=None;candidate=None;plan=None;audited=None;chunks={};accepted=[]
    try:
        gate=static();guard();q.diskpreflight(additional_bytes=10*1024**2)
        cpath=G/'retry/geometry486_contract.json';contract=read(cpath);assert contract['status']=='DESIGN_ONLY_NO_OPTIMIZATION_OR_EXECUTION_AUTHORIZATION'
        snapshot=Path('/tmp/haic-retry-stage485-private/native/D485-A/initial-full-private.json');baseline=snapshot.with_name('unsupported-geometry-private.json')
        assert sha(snapshot)==contract['inputs']['snapshot_sha256'] and sha(baseline)==contract['inputs']['baseline_final_sha256']
        initial=root/'stage486-initial-reconstruction-private.json';assert sha(initial)==contract['inputs']['initial_material_sha256']
        old=read(root/'stage485/plan-private.json')
        for group in ('sources','protected','original408_preserve'):
            for p,h in old[group].items():assert sha(p)==h,p
        assert sha(old['ledger_path'])==old['ledger_sha256']
        ledger=root/'project-effective-budget-v485.json';assert read(ledger)['research_remaining']==26175 and read(ledger)['final_reserved_actions']==84000 and read(ledger)['final_reserve_used']==0
        source_names=['trial487.py','quota487.py','test_quota487.py','audit487.py','racing258_plan.py','racing258_feasibility.py']
        pins={str(G/'retry'/n):sha(G/'retry'/n) for n in source_names}
        plan=dict(stage=487,authorization='EXPLICIT_ONE_FEASIBILITY_FIRST194_NO_NATIVE',contract_sha256=sha(cpath),snapshot_path=str(snapshot),snapshot_sha256=sha(snapshot),baseline_path=str(baseline),baseline_sha256=sha(baseline),initial_theta_sha=contract['inputs']['initial_coefficients_sha256'],source_pins=pins,profile_ast_sha256=gate['profile_ast_sha256'],candidate_semantic_ast_sha256=gate['candidate_semantic_ast_sha256'],old_485_plan_path=str(root/'stage485/plan-private.json'),old_485_plan_sha256=sha(root/'stage485/plan-private.json'),ledger_path=str(ledger),ledger_sha256=sha(ledger),deadline_utc=DEADLINE,static=gate,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),caps=contract['hard_caps'],outside_raw_reserved_files=EXTRA_FILES,outside_raw_reserved_bytes=EXTRA_BYTES,raw_enforced_files=q.MAX_FILES,raw_enforced_bytes=q.MAX_BYTES,development_conservative_CPU_s=DEV_CPU,development_conservative_wall_s=DEV_WALL,allowance_is_not_measurement=True,runtime=dict(python=sys.version,numpy=np.__version__))
        q.write_json('plan-private.json',plan,exclusive=True)
        module,semantic,profile_ast=transformed();rm_registered,ra_registered=transformed_repair();q.write_json('source-transform-private.json',dict(source=sha(G/'retry/racing258_plan.py'),transformed_source=ast.unparse(module),repair_transformed_source=ast.unparse(rm_registered),repair_original_ast_sha256=hashlib.sha256(ra_registered.encode()).hexdigest(),semantic_sha256=hashlib.sha256(semantic.encode()).hexdigest(),profile_ast_sha256=hashlib.sha256(profile_ast.encode()).hexdigest()),exclusive=True)
        q.write_json('opening-private.json',dict(stage=487,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),counts=counts.copy(),CPU_s=time.process_time(),wall_s=time.perf_counter()-START),exclusive=True)
        snapshot_value=read(snapshot)['physical'];model=read(baseline)['model'];bound=40/6-1.4-.35
        def capture_initial(theta):
            guard();assert counts['objectives']==counts['profiles']==0 and arrayhash(theta)==plan['initial_theta_sha']
            q.write_json('initialization-private.json',dict(theta=plain(theta),sha256=arrayhash(theta),source_expression_unchanged=True,before_first_objective=True),exclusive=True)
        original_profile=original.profile
        def profile(*args,**kwargs):
            guard();assert counts['profiles']<196;counts['profiles']+=1
            return original_profile(*args,**kwargs)
        def capture_evaluation(theta,score,path,p,clear,V,number,offset):
            guard();assert number==counts['objectives']+1<=194;counts['objectives']=number
            if number==1:assert arrayhash(theta)==plan['initial_theta_sha']
            components=dict(obstacle_squared=float(np.sum(np.maximum(-clear,0)**2)),curvature_weighted_squared=float(np.sum(np.maximum(abs(p['curvature'])-np.tan(.4)/3.24,0)**2)*100),offset_squared=float(np.sum(np.maximum(abs(offset)-bound,0)**2)))
            rough=float(.001*np.sum((np.roll(theta,-1)-theta)**2));assert tuple(score)==key(V,p['estimated_time_s'],rough)
            record=dict(number=number,theta=plain(theta),key=plain(score),components=components,clearance=plain(clear),violation=V,profile=plain(p),path_sha256=arrayhash(path),profile_sha256=digest(p),time_term=p['estimated_time_s'],roughness=rough)
            chunk=(number-1)//20;chunks.setdefault(chunk,[]).append(record);q.write_json(f'evaluations-{chunk:02d}-private.json',dict(evaluations=chunks[chunk]))
        def capture_accepted(step,j,theta,score,calls):
            accepted.append(dict(calls=calls,step=step,coordinate=j,theta=plain(theta),key=plain(score)));q.write_json('accepted-private.json',dict(accepted=accepted))
        namespace={**vars(original),'profile':profile,'capture_evaluation':capture_evaluation,'capture_accepted':capture_accepted,'capture_initial':capture_initial}
        exec(compile(module,str(G/'retry/racing258_plan.py')+'#registered487-score-only','exec'),namespace)
        guard();assert counts['road_solver']==0;counts['road_solver']=1
        def baseline_forbidden(*a,**k):raise RuntimeError('487_BASELINE_REOPTIMIZATION_FORBIDDEN')
        original.solve=baseline_forbidden
        candidate=namespace['solve'](snapshot_value,model)
        assert counts['objectives']==194 and len(accepted)==96 and counts['profiles']==195
        q.write_json('pre-repair-private.json',plain(candidate),exclusive=True)
        repair=None
        if not candidate['free_feasible'] and min(candidate['free_clearance'])>=-.001 and candidate['free_profile']['max_abs_curvature']<=np.tan(.4)/3.24:
            counts['repair_calls']+=1;assert counts['repair_calls']==1
            original_clear=repair_source.obstacle_clearance;repair_observation=None;repair_clear_trace=[]
            def counted_clear(*a,**k):
                guard()
                if counts['repair_clearance']>=100:raise RuntimeError('487_REPAIR_CLEARANCE100')
                counts['repair_clearance']+=1;return original_clear(*a,**k)
            def capture_repair(theta,line,c,p,calls,oldtheta):
                nonlocal repair_observation
                repair_observation=plain(dict(line=line,coefficients=theta,clearance=c,profile=p,geometry_evaluations=calls,max_coefficient_change=float(abs(theta-oldtheta).max())))
                q.write_json('repair-observation-private.json',repair_observation,exclusive=True)
            rm,ra=transformed_repair();rns={**vars(repair_source),'obstacle_clearance':counted_clear,'profile':profile,'capture_repair':capture_repair}
            exec(compile(rm,str(G/'retry/racing258_feasibility.py')+'#observer-only','exec'),rns)
            try:
                candidate['model']=model;repaired=rns['project'](snapshot_value,candidate);assert repaired['geometry_evaluations']==counts['repair_clearance']
                repair=plain(repaired);candidate.update(line=repaired['line'],coefficients=repaired['coefficients'],free_profile=repaired['profile'],free_clearance=repaired['clearance'],free_feasible=True)
            except AssertionError:
                if repair_observation is None:raise
                repair=dict(failed=True,geometric_exit_assertion_failed=True,observation_path=str(RAW/'repair-observation-private.json'),observation_sha256=sha(RAW/'repair-observation-private.json'),geometry_evaluations=counts['repair_clearance'])
            q.write_json('repair-private.json',repair,exclusive=True)
        candidate['model']=model;candidate['numerical_projection']=repair
        q.write_json('candidate-final-private.json',plain(candidate),exclusive=True)
        from retry.audit487 import audit
        audited=audit(RAW,{**plan,'profile_calls':counts['profiles'],'counts':counts.copy()},q);assert audited['passed']
        status='GEOMETRY_INPUT_CANDIDATE_ONLY' if candidate['free_feasible'] else 'ORDERING_ALONE_SUFFICIENCY_REJECTED'
    except BaseException as e:
        status='TECHNICAL_INCONCLUSIVE';error=type(e).__name__+': '+str(e)
        q.write_json('stop.json',dict(error=error,traceback=traceback.format_exc(),counts=counts,no_retry=True),control=True)
    finally:
        guard()
        result=dict(stage=487,status=status,error=error,counts=counts,CPU_s=time.process_time()+DEV_CPU,wall_s=time.perf_counter()-START+DEV_WALL,measured_CPU_s=time.process_time(),measured_wall_s=time.perf_counter()-START,development_conservative_CPU_s=DEV_CPU,development_conservative_wall_s=DEV_WALL,allowance_is_not_measurement=True,static=None if plan is None else plan['static'],audit=audited,min_clearance_m=None if candidate is None else float(min(candidate['free_clearance'])),geometry_feasible=None if candidate is None else bool(candidate['free_feasible']),new_actual=0,new_resets=0,new_worlds=0,new_ticks=0,new_seed=0,new_P4=0,new_prefix=0,second_condition_used=False,research_remaining=26175,reserve=84000,reserve_used=0,no_followup=True)
        q.write_json('result.json',result,control=True)
        # Each file is fully reopened/decoded twice; no controls are rewritten
        # after this manifest is sealed.
        inventory=q.inventory()
        for rec in inventory['files']:
            p=Path(rec['path']);data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==rec['sha256'] and data==p.read_bytes();json.loads(data);json.loads(p.read_bytes());rec['decoded_sha256']=digest(json.loads(data));rec['readbacks']=2
        q.write_json('retention-private.json',dict(stage=487,files=inventory['files'],plan_sha256=sha(RAW/'plan-private.json') if (RAW/'plan-private.json').exists() else None),exclusive=True)
        guard();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        print(json.dumps(dict(stage=487,status=status,error=error,counts=counts,min_clearance=result['min_clearance_m'],CPU_s=time.process_time()+DEV_CPU,wall_s=time.perf_counter()-START+DEV_WALL,retained=q.inventory()['bytes'])),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]))
