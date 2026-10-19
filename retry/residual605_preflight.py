"""Pure production-path stubs: no real force, tick, world, chooser or geometry.

Exercise the actual605 constructor/choose/evaluate/context/run entry points.
"""
import json
import io
from contextlib import redirect_stdout
from collections import Counter, namedtuple
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np


def run_checks(Study):
    import sys
    m=sys.modules[Study.__module__]
    checks=[];writes={};selector_calls=[];contexts=[];reserves=[]
    root_type=namedtuple('StubRoot','center planar')
    planar_type=namedtuple('StubPlanar','angle levers linear')
    linear_type=namedtuple('StubLinear','velocity wheels')
    wheel_type=namedtuple('StubWheel','heading')
    root=root_type((0.,0.),planar_type(0.,((0.,1.),),linear_type((0.,10.),(wheel_type(0.),))))
    action=np.array([-.0,.3,-.0],np.float32)
    report=dict(mode='STUB',final_recertified=True,reports=[dict(mode='FINAL',ok=True)])
    class FakeDir:
        def mkdir(self,**kw): pass
        def __truediv__(self,name): return Path('/tmp/605-pure-unused')/name
        def glob(self,pattern): return []
    class FakeJournal:
        def __init__(self,*a):self.rows=[]
        def append(self,*a,**k):self.rows.append((a,k));return '0'*64
        def close(self):pass
    def write(path,value,*a):writes[str(path)]=value
    static=dict(roads=[[[[0.,0.],[1.,0.]],1.]],boundary=[[[0.,0.],[1.,0.]]],obstacles=[])
    def read(path,*a,**kw):
        if path==m.base.old.INPUTS['static']:return json.dumps(static)
        if path==m.base.old.INPUTS['candidate_paths']:return json.dumps(dict(candidate={'stub':'PRIMARY551'},backup={'stub':'BACKUP551'}))
        if path==m.base.old.INPUTS['ledger']:return json.dumps(dict(initial_visited=[0]))
        raise AssertionError('UNEXPECTED_READ_IN_PURE_STUB')
    def init(o,st,previous):
        o.static=st;o.source_index=((0.,1.,0.,0.),);o.source_edges=[(0.,1.,0.,0.)]
        o.counts=Counter();o.model=[0];o.planner=dict(forecast_calls=0,geometry_checks=0,forecast_ticks=0,force_evaluations=0)
        o.originals={};o.trial_summaries=[];o.journal=SimpleNamespace(rows=[]);o.raw_kernels=[]
        o.active_trial=None;o.pending=None;o.original_margin=lambda *a:1.25
        o.last_model_before=o.last_model_after=None;o.diag=None
    def geometry_context(st,limit):
        q=dict(roads=st['roads'],boundary=st['boundary'],obstacles=st['obstacles'],max_checks=limit,owner_token=object())
        contexts.append(q);return q
    def selector(r,high,low,progress,counter,cost,max_ticks,**kw):
        selector_calls.append((r,high,low,progress,counter,cost,max_ticks,kw))
        return action.copy(),report
    def forbidden(*a,**kw):raise AssertionError('REAL_SCIENTIFIC_EVALUATION_FORBIDDEN_IN_STUB')
    with patch.object(m,'D',FakeDir()),patch.object(Path,'read_text',read), \
         patch.object(m,'Journal',FakeJournal),patch.object(m,'atomic_write',write), \
         patch.object(m.prior.Meter,'__init__',init), \
         patch.object(m.base.old.tracking,'geometry_context',geometry_context), \
         patch.object(m.base.old.tracking,'choose',selector), \
         patch.object(m.d,'source_tick',forbidden),patch.object(m.d,'force_rows',forbidden), \
         patch.object(m.base.old.wheel,'wheel_response',forbidden),patch.object(m.base.old.planar,'wheel_response',forbidden):
        q=Study();other=Study()
        assert len(contexts)==2 and q.geometry_context is contexts[0] and other.geometry_context is contexts[1]
        assert q.geometry_context is not other.geometry_context and q.static is not other.static
        assert q.geometry_context['roads'] is q.static['roads'] and q.geometry_context['max_checks']==600000
        checks.append('production_constructor_creates_private_instance_geometry_context_before_source')
        def configure(o):
            tracker=m.d.FinishLineTracker(center=(0.,0.),forward=(1.,0.),half_width=1.,half_depth=1.)
            o.prefix=dict(root=root,progress=110.,visited={0},tracker=tracker,elapsed=1.92,global_raw=96,launch=[0,384],tracking=[0,0])
            o.short=lambda r:dict(center=r.center,angle=r.planar.angle)
            o.prefix_hash=m.digest(o.checkpoint(o.prefix));o.state=m.clone(o.prefix)
            o.fixed={h:action.copy() for h in range(1,40)}
            o.old_choices={40:dict(action=action.tolist(),detail=report)}
            o.reserve=lambda feedback,replay_tail=True:reserves.append((o.next_hold,feedback,replay_tail))
            o.begin_context=lambda:None;o.end_context=lambda:None;o.flush=lambda *a,**k:None
            o.project=lambda *a:{'s':110.}
            o.same_saved=lambda row:None
            def raw(a,h,k):
                before=o.state['global_raw'];o.state['global_raw']+=1;o.state['elapsed']+=.02
                o.state['tracking'][1]+=4;o.state['visited'].add(h);o.state['tracker'].previous_longitudinal+=.1
                return dict(index=h,raw=k,action=a.tolist(),global_raw_before=before,global_raw_after=before+1,tick_executed=True),None
            o.raw=raw
            o.tape=dict(rows=[dict(index=i//4+1,raw=i%4+1,global_raw_after=i+1) for i in range(160)])
        class FakeCrossing:
            def __init__(self,owner):self.hits={}
            def add(self,row):
                if row['global_raw_after']==160:self.hits['400']=dict(time_s=3.19,hold=40,whole_hold_safe=False)
            def finish_hold(self,rows):
                if self.hits and len(rows)==4:self.hits['400']['whole_hold_safe']=True
            def passed(self,key):return key in self.hits and self.hits[key]['whole_hold_safe']
        configure(q)
        with patch.object(m,'Crossing',FakeCrossing),patch.object(m.residual,'target',lambda *a:((0.,10.),(-1.,0.))):
            zero=q.evaluate('zero',[0.]*6)
            nonzero=q.evaluate('H0',m.residual.family()[1][1])
        assert zero['safe_s400'] and nonzero['safe_s400'] and len(selector_calls)==2
        for args in selector_calls:
            assert args[0] is root and args[1] is q.paths['candidate'] and args[2] is q.paths['backup']
            assert args[3]==110. and args[4] is q.model and args[5] is q.planner and args[6]==180000
            assert args[7]['geometry'] is q.geometry_context and args[7]['history']==(0,240)
        assert all(feedback==(h>=40) and tail for h,feedback,tail in reserves)
        checks.append('real_evaluate_fixed25to39_then_feedback40_passes_all_original537_args_budget_history_context')
        a0=q.records['zero']['commands'][-1]['action'];a1=q.records['H0']['commands'][-1]['action']
        assert np.asarray(a0,np.float32).tobytes()==action.tobytes() and np.asarray(a1,np.float32).tobytes()!=action.tobytes()
        checks.append('zero_and_nonzero_real_residual_paths_exercised_with_stub_raw_and_selector')
        for s in (80.,220.,400.):
            q.state['progress']=s
            with patch.object(q,'project',forbidden),patch.object(m.residual,'target',forbidden):
                outside,_=q.residual_action(action,m.residual.family()[1][1])
            assert outside.tobytes()==action.tobytes()
        checks.append('outside_support_residual_zero_bytes_and_no_geometry_dispatch')
        m.isolated(q.state,[q.prefix]);m.immutable(q.prefix['root'])
        a=m.clone(q.prefix);b=m.clone(q.prefix);m.isolated(a,[b,q.prefix])
        a['tracking'][0]+=1;a['launch'][0]+=1;a['visited'].add(99);a['tracker'].previous_longitudinal=999.
        assert b['tracking']==q.prefix['tracking']==[0,0] and b['launch']==q.prefix['launch']==[0,384]
        assert 99 not in b['visited'] and b['tracker'].previous_longitudinal==q.prefix['tracker'].previous_longitudinal==0.
        checks.append('candidate_mutable_state_history_visited_tracker_isolation_and_frozen_shared_root')
        # Real begin_context uses the same601cache and602Road wiring; numeric
        # callbacks below are pure sentinels, never a real geometry evaluator.
        helper=other;helper.original_margin=lambda *a:m.compiled_geometry.distance('A','AE','B','BE')
        helper.original_plain_road=lambda *a:1.25
        old_margin=helper.original_margin;old_road=m.compiled_geometry.full.road_margin
        with patch.object(m.compiled_geometry,'distance',lambda *a:1.25), \
             patch.object(m.compiled_geometry.full,'obstacle_margin',lambda *a:2.), \
             patch.object(m.compiled_geometry.original,'polygons',lambda *a:()):
            helper.begin_context()
            assert isinstance(m.compiled_geometry.full.road_margin,m.compiled_geometry.Road)
            assert helper.original_margin(root,*helper.context.args)==1.25
            assert helper.original_margin(root,*helper.context.args)==1.25
            assert helper.context.hits==1 and helper.counts['helper_original_comparisons']==1
            helper.end_context()
        assert helper.original_margin is old_margin and m.compiled_geometry.full.road_margin is old_road and helper.context is None
        checks.append('real_cache_preparedRoad_compiled_distance_original_comparison_wiring_and_cleanup')
        # Exercise real top-level whole-stop handler, with all disk/timer calls
        # stubbed so it cannot alter the outer study's timers or artifacts.
        fatal=Study();called=[]
        def failure():called.append('prepare');raise RuntimeError('PURE_STUB_INTEGRITY_FAILURE')
        fatal.prepare=failure;fatal.prefix96=lambda:called.append('PREFIX_FORBIDDEN')
        fatal.evaluate=lambda *a:called.append('CANDIDATE_FORBIDDEN')
        fatal.replay=lambda *a:called.append('REPLAY_FORBIDDEN')
        with patch.object(m.signal,'signal',lambda *a:None),patch.object(m.signal,'setitimer',lambda *a:None), \
             patch.object(m.base,'sha',lambda *a:'0'*64),redirect_stdout(io.StringIO()):
            fatal.run()
        end=next(value for key,value in writes.items() if key.endswith('residual605_result.json'))
        assert called==['prepare'] and end['status']=='TECHNICAL_OR_POSITIVE_CONTROL_STOP'
        assert not end['candidates'] and not end['replay']
        checks.append('production_top_level_integrity_failure_aborts_all_candidates_and_replay_without_retry')
    return dict(passed=True,checks=checks,stub_original_selector_calls=len(selector_calls),
                actual_choose=0,physics_ticks=0,force_evaluator=0,geometry_evaluator=0,native=0)
