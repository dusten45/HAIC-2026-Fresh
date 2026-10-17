"""495 pure finite launch/seam, opt-in wiring, codec and quota pre-gates.

The caller supplies frozen inputs and the old485 snapshot. No file inputs are
opened here except controller source. All physics entry points are poisoned.
"""
import copy
import contextlib
import json
import time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np


def run(runtime,quota,Meter,initial,fixed,pace,nodes):
    cpu=time.process_time();wall=time.perf_counter();tests=[]
    require=runtime.require
    common=runtime.import_module('paired417_common')
    codec=runtime.import_module('io481')
    jsoncodec=runtime.import_module('pilot420_json')
    terminal=runtime.import_module('terminal410_model')
    source=runtime.import_module('source_vehicle_transition')
    import Box2D
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    def poison(*args,**kwargs):raise AssertionError('495_STATIC_PHYSICS_ENTRY_FORBIDDEN')
    def case(label,check):
        check();tests.append(label)
    def fake(physical,tracker):
        h=physical['hull']
        hull=NS(position=list(h['position']),linearVelocity=list(h['velocity']),angle=h['angle'],angularVelocity=h['angular_velocity'])
        wheels=[NS(joint=NS(angle=w['joint']['angle']),tiles=list(w['tiles']),**{k:w['dynamics'][k] for k in ('gas','brake','omega')}) for w in physical['wheels']]
        raw=NS(car=NS(hull=hull,wheels=wheels),t=physical['actual_time'],finish_line_tracker=NS(**copy.deepcopy(tracker)),tile_visited_count=physical['unique_tiles'],finished=False)
        env=NS(unwrapped=raw,off_track_counter=physical['off_track_counter'])
        return env,raw
    def same_launch():
        env,model=fake(initial['physical'],initial['wrapper']['finish_tracker'])
        actual=runtime.ActualC(env,fixed,np.asarray(pace))
        memory=actual.memory();src=common.SourceC(fixed,np.asarray(pace),copy.deepcopy(memory))
        require(actual.policy.nodes.tobytes()==np.asarray(nodes).tobytes() and src.policy.nodes.tobytes()==np.asarray(nodes).tobytes(),'495_STATIC_P4_BINDING')
        a=actual.act(env);b=src.act(model)
        require(np.array_equal(a,b) and actual.memory()==src.memory(),'495_STATIC_LAUNCH_ACTUAL_SOURCE')
        require(actual.phase()=='LAUNCH','495_STATIC_LAUNCH_PHASE')
    def seam():
        line=np.asarray(fixed['line']);velocity=line[1]-line[0];L=float(np.cumsum(np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1))[-1])
        for phase in ('LAUNCH','FIRST_LAP','FINISH_CONFIRM'):
            q=runtime.canonical_projection(line,line[0],velocity,phase)
            require(q['path_error_m']==0 and q['arc']==(0. if phase=='LAUNCH' else L),'495_STATIC_SEAM_PHASE')
    def finite_policy(phase):
        env,model=fake(initial['physical'],initial['wrapper']['finish_tracker'])
        line=np.asarray(fixed['line']);edge=line[1]-line[0];direction=edge/np.linalg.norm(edge)
        model.car.hull.position=((line[0]+line[1])*.5).tolist() if phase=='FIRST_LAP' else line[0].tolist()
        model.car.hull.linearVelocity=direction.tolist();model.t=1.
        if phase=='FINISH_CONFIRM':
            model.finish_line_tracker=NS(candidate_crossing_time_s=.5,qualified_time_s=.4,crossing_from_back=True,finish_time_s=None,center=line[0].tolist(),forward=direction.tolist(),half_depth=1.,half_width=1.)
        actual=runtime.ActualC(env,fixed,np.asarray(pace));actual.policy.phase=phase
        memory=actual.memory();src=common.SourceC(fixed,np.asarray(pace),copy.deepcopy(memory))
        a=actual.act(env);b=src.act(model)
        require(np.array_equal(a,b) and actual.memory()==src.memory() and np.isfinite(a).all(),'495_STATIC_FINITE_'+phase)
        require(actual.phase()==phase,'495_STATIC_FINITE_PHASE')
    def codec_roundtrip():
        payload=dict(snapshot=copy.deepcopy(initial),binary=b'\x00\xff495\x80')
        packed={codec.CODEC_KEY:1,'payload':jsoncodec.json_ready(payload),'decoded_sha256':codec.canonical(payload)}
        wire=json.loads(json.dumps(packed,allow_nan=False))
        with patch.object(codec,'ORIGINAL_READ',return_value=wire):
            got=codec.read(Path(quota.native_dir)/'unwritten-codec-fixture.json')
        require(codec.canonical(got)==codec.canonical(payload) and got['binary']==payload['binary'],'495_STATIC_CODEC_ROUNDTRIP')
        altered=copy.deepcopy(wire);altered['payload']['binary']=jsoncodec.json_ready(b'tampered')
        rejected=False
        with patch.object(codec,'ORIGINAL_READ',return_value=altered):
            try:codec.read(Path(quota.native_dir)/'unwritten-codec-fixture.json')
            except runtime.TechnicalStop:rejected=True
        require(rejected,'495_STATIC_CODEC_TAMPER_REJECT')
        # Preflight the very scalar converter used by every new native writer.
        json.dumps(jsoncodec.json_ready(dict(ok=True,count=int(np.int64(2)),value=float(np.float64(1.)),binary=b'x')),allow_nan=False)
    def quota_before_write():
        from retry.quota495 import QuotaStop
        before=quota.summary();rejected=False
        try:quota.reserve(Path(quota.native_dir)/'unwritten-oversize-fixture.json',2*1024*1024+1)
        except QuotaStop:rejected=True
        require(rejected and quota.summary()==before and not quota.pending,'495_STATIC_QUOTA_PREWRITE')
    def meter_caps():
        # Exercise real charge method on a memory-only counter, no journal hook.
        m=object.__new__(Meter);m.actual_start=(1.,1.);m.active=None
        m.nb=dict(actions=129,resets=1,arm_actions={'D495-A':129},arm_resets={'D495-A':1})
        m.raw_counts={'D495-A':dict(reset_raw=64,action_raw=516)}
        m.guard=lambda:None;m.persist=lambda:None
        calls=[];m.native_charge_hook=lambda *args:calls.append(args)
        for kind in ('action','reset','reset_raw','action_raw'):
            rejected=False
            try:m.charge(kind,'D495-A')
            except runtime.ResourceStop:rejected=True
            require(rejected and not calls,'495_STATIC_CHARGE_CAP_BEFORE_HOOK_'+kind)
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(Box2D,'b2World',poison))
        for cls,names in ((CarRacing,('__init__','reset','step')),(Car,('__init__','step'))):
            for name in names:stack.enter_context(patch.object(cls,name,poison))
        for module in (terminal,source):
            for name in ('TerminalVehicleTransition','SourceVehicleTransition'):
                if hasattr(module,name):stack.enter_context(patch.object(module,name,poison))
        # Constructor aliases in already loaded private graph are also blocked.
        graph=getattr(runtime,'graph',None)
        modules=[] if graph is None else list(graph.modules.values())
        for module in modules:
            if module in (terminal,source):continue
            for name in ('TerminalVehicleTransition','SourceVehicleTransition','make_env'):
                if hasattr(module,name):stack.enter_context(patch.object(module,name,poison))
        case('canonical_phase_aware_exact_seam',seam)
        case('bound_actual_source_finite_launch',same_launch)
        case('bound_actual_source_finite_first_lap',lambda:finite_policy('FIRST_LAP'))
        case('bound_actual_source_finite_finish_confirm',lambda:finite_policy('FINISH_CONFIRM'))
        case('full_snapshot_bytes_codec_and_tamper',codec_roundtrip)
        case('native_output_oversize_rejected_before_write',quota_before_write)
        case('all_four_native_caps_reject_before_hook',meter_caps)
    result=dict(stage=495,passed=True,tests=tests,test_count=len(tests),no_physics=True,worlds=0,resets=0,steps=0,profile_calls=0,P4_recomputations=0,finite_only=True,whole_tube_continuity_claim=False,binding=copy.deepcopy(runtime.binding),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    return result
