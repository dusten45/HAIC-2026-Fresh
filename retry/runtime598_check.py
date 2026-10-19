"""Private saved598 numerical/time unit checks; NOT observation/Agent testing."""
import time
CPU=time.process_time()
import ast
import datetime
import hashlib
import json
from pathlib import Path
import resource
import signal
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
D=Path('/workspace/haic-runtime-port-private')
START=json.loads((D/'started-private.json').read_text())
DEADLINE=datetime.datetime(2026,10,20,14,59,tzinfo=datetime.timezone.utc)
PHASE=sys.argv[1] if len(sys.argv)>1 else 'baseline'
assert PHASE in {'baseline','optimized'}
PREVIOUS=json.loads((D/'baseline-result-private.json').read_text()) if PHASE=='optimized' else None
PRIOR_TICKS=PREVIOUS['total_model_attempted'] if PREVIOUS else 0
import_start=time.perf_counter()
from submit_core import runtime598 as core
IMPORT_S=time.perf_counter()-import_start


def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def bits(x):return struct.pack('!d',x)
def strip_hashes(x):
    if isinstance(x,dict):return {k:strip_hashes(v) for k,v in x.items() if not k.endswith('sha256')}
    if isinstance(x,list):return [strip_hashes(v) for v in x]
    return x


def run():
    if datetime.datetime.now(datetime.timezone.utc)>=DEADLINE:raise RuntimeError('AUTHORIZATION_EXPIRED')
    marker=D/(PHASE+'-UNIT_STARTED-private.json')
    if marker.exists():raise RuntimeError('NO_DUPLICATE_NUMERICAL_RUN')
    marker.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
    fixture=json.loads((D/'fixtures-private.json').read_text());before=digest(fixture)
    source=ROOT/'submit_core/runtime598.py';tree=ast.parse(source.read_text())
    banned={'ctypes','importlib','multiprocessing','os','pathlib','resource','shutil','signal','socket','subprocess','sys'}
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[q.name for q in n.names] if isinstance(n,ast.Import) else [n.module]
            assert not any(s.split('.')[0] in banned or s.startswith(('retry','core')) for s in names)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):assert n.func.id not in {'compile','eval','exec','__import__','open'}
    static=fixture['static'];high=fixture['paths']['candidate'];low=fixture['paths']['backup']
    scene=core.Scene(static['roads'],static['boundary'],static['obstacles'],array_distance=PHASE=='baseline')
    # Use actual stored polygons/segments only. Compare independent array
    # operations with original scalar expressions before any model integration.
    kernel_cases=0;array_mismatches=0;margin_checks=0
    for case in ([] if PREVIOUS else fixture['cases'].values()):
        root=core.load_required_root(dict(case['root'],roads=static['root']['roads']))
        for poly in core.polygons(root):
            edges=scene.boundary[::max(1,len(scene.boundary)//12)]
            for edge in edges:
                a=core.polygon_distance(poly,edge);b=core.polygon_distance_array(poly,edge)
                kernel_cases+=1;array_mismatches+=bits(a)!=bits(b)
    if array_mismatches:scene.array_distance=False
    for case in fixture['cases'].values():
        root=core.load_required_root(dict(case['root'],roads=static['root']['roads']))
        scalar=min(core.scalar_road_margin(root,scene.roads,scene.index,scene.boundary,scene.edges),core.obstacle_margin(core.polygons(root),scene.obstacles))
        fast=scene.margin(root);margin_checks+=1
        if bits(scalar)!=bits(fast):
            scene.array_distance=False;scene.clear();fast=scene.margin(root)
            assert bits(scalar)==bits(fast),'CONSERVATIVE_MARGIN_FALLBACK_DIFFERS'
    model_attempted=model_completed=0
    original_tick=core.tick
    def guarded_tick(*args):
        nonlocal model_attempted,model_completed
        if model_attempted+PRIOR_TICKS>=20000:raise RuntimeError('TOTAL_MODEL_TICK_20000')
        if datetime.datetime.now(datetime.timezone.utc)>=DEADLINE:raise RuntimeError('AUTHORIZATION_EXPIRED')
        if time.process_time()-CPU+10>=1740 or time.time()-START['start_epoch']>=3480:raise RuntimeError('TOTAL_TIME_RESERVE')
        model_attempted+=1
        after=original_tick(*args);model_completed+=1;return after
    core.tick=guarded_tick
    results=[];status='PASS';error=None
    try:
        for name,case in fixture['cases'].items():
            root=core.load_required_root(dict(case['root'],roads=static['root']['roads']))
            controller=core.Controller(high,low,scene,{int(h):a for h,a in fixture['commands'].items()},len(static['track']))
            begin=time.perf_counter();cpu=time.process_time();count=model_attempted
            action,report=controller.select(root,case['progress'],case['hold'],case['groups']['launch'],case['groups']['running'],
                core.FinishLineTracker(**case['tracker']),set(case['visited']),case['clock'])
            wall=time.perf_counter()-begin;used=time.process_time()-cpu
            parity=dict(action_bytes=action is not None and action.tobytes().hex()==case['expected_bits'],
                full_safety_selection_report_without_passive_hashes=digest(strip_hashes(report))==digest(strip_hashes(case['expected_report'])))
            record=dict(case=name,hold=case['hold'],parity=parity,model_ticks=model_attempted-count,CPU_s=used,wall_s=wall,
                        cache_hits=scene.hits,cache_misses=scene.misses)
            results.append(record)
            (D/f'{PHASE}-{name}-output-private.json').write_text(json.dumps(dict(action=action.tolist() if action is not None else None,report=report,summary=record),indent=2))
            if not all(parity.values()):raise AssertionError('SAVED598_NUMERIC_OR_SELECTION_MISMATCH_'+name)
    except BaseException as exc:
        status='NUMERICAL_OR_TECHNICAL_STOP';error=type(exc).__name__+':'+str(exc)
        import traceback
        (D/'error-private.txt').write_text(traceback.format_exc())
    finally:core.tick=original_tick
    assert digest(fixture)==before,'PRIVATE_INPUT_MUTATED'
    result=dict(status=status,error=error,phase=PHASE,scope='Research-only saved privileged598 unit inputs. NOT Agent/observation/native/complete decision coverage or official submission admission.',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),static_import_scan=True,
        original_kernel_hardcap=core.MAX_MODEL_TICKS,horizon=core.HORIZON,
        array_geometry_checks=kernel_cases,array_geometry_mismatches=array_mismatches,
        scalar_fullmargin_checks=margin_checks,array_geometry_used=scene.array_distance,
        cases=results,total_model_attempted=model_attempted,total_model_completed=model_completed,
        cumulative_model_attempted=model_attempted+PRIOR_TICKS,
        import_wall_s=IMPORT_S,total_CPU_s=time.process_time()-CPU+10+(PREVIOUS['total_CPU_s'] if PREVIOUS else 0),total_wall_s=time.time()-START['start_epoch'],
        external_harness_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        immutable_cache_max_entries=scene.max_entries,inputs_unchanged=True,
        native=0,DEV_actions=0,HOLDOUT=0,SEALED=0,research_remaining=20745,reserve=84000,reserve_used=0,
        observation_connection_complete=False,original13_22s_maintained=False,whole_Agent_act_pass=False)
    if PREVIOUS:result['first_port_before_exact_bound_preparation']={k:PREVIOUS[k] for k in ['cases','total_model_attempted','total_CPU_s','source_sha256','array_geometry_checks','array_geometry_mismatches']}
    (ROOT/'retry/runtime598_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    def stop(*a):raise RuntimeError('UNIT_TIME_CAP')
    signal.signal(signal.SIGPROF,stop);signal.signal(signal.SIGALRM,stop)
    signal.setitimer(signal.ITIMER_PROF,1740)
    signal.setitimer(signal.ITIMER_REAL,max(.1,3480-(time.time()-START['start_epoch'])))
    run()
