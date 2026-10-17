"""No-physics connection tests for selected/own/history and lossless packing."""
import copy
from contextlib import contextmanager,ExitStack
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from retry.capture494 import CaptureError494
from retry.schema493 import receipt,digest
from retry.quota495 import PackedObservers495

@contextmanager
def physics_poison(graph):
    import Box2D
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    hits=[]
    def forbidden(*a,**k):hits.append('physical_entry');raise AssertionError('495_FULL_STATIC_PHYSICS_FORBIDDEN')
    with ExitStack() as stack:
        original=Box2D.b2World;stack.enter_context(patch.object(Box2D,'b2World',forbidden));classes={CarRacing,Car}
        for m in graph.modules.values():
            for name,value in list(vars(m).items()):
                if isinstance(value,type) and name in ('TerminalVehicleTransition','SourceVehicleTransition'):classes.add(value)
                if value is original or name=='make_env':stack.enter_context(patch.object(m,name,forbidden))
        for cls in classes:
            for name in ('__init__','reset','step'):
                if hasattr(cls,name):stack.enter_context(patch.object(cls,name,forbidden))
        yield hits

def run(runtime,meter,quota,packing,fixtures,folder):
    from retry.runtime495 import install
    base=runtime.import_module('online481');online=runtime.import_module('online485')
    observer=runtime.import_module('observer435');native=runtime.import_module('actual437_boundary')
    cls=observer.ObserveMixin
    original=(cls.__init__,cls.one,getattr(cls,'_capture495_installed',None),native.PostTrackerTap,observer.PostTrackerTap)
    methods=(base.closed,base.own,online.select,online.history);tests=[]
    def child(label,hold):return NS(label=label,rows=[{'safety':[]}],capture_holds495=[copy.deepcopy(hold)])
    first=child('first',fixtures['first']);repeat=child('repeat',fixtures['repeat'])
    def fake_closed(c):return '/virtual/'+c.label,'a'*64
    def fake_select(*args):return dict(auth={'repeat_path':'/virtual/repeat'}),dict(selected='chosen',options={'chosen':dict(first_path='/virtual/first')})
    def fake_own(*args):return {},{}
    def fake_history(*args):return {'full_original_history_dependency':'stubbed_for_no_physics_connection_test'}
    try:
        base.closed=fake_closed;base.own=fake_own;online.select=fake_select;online.history=fake_history
        hook=install(runtime,meter,quota,packing)
        base.closed(first);base.closed(repeat)
        selected,_=online.select(first,{},None)
        assert selected['direct_hold495']['kind']=='model'
        tests.append('candidate_and_selected_cold_capture_auth_and_all_measurement_repeat')
        row,join=base.own(repeat,{},selected)
        assert join['direct_capture495']['safe']
        tests.append('own_direct_flags_and_wrapper_return_safety_after_original_own_dependency')
        assert online.history(first)['full_original_history_dependency']
        tests.append('history_wrapper_requires_capture_for_every_own_row')
        bad=child('unsafe',fixtures['unsafe'])
        try:online.history(bad)
        except Exception:pass
        else:raise AssertionError('direct wrapper damage missing from row must stop')
        tests.append('unreported_direct_return_damage_stops_history_path')
        bad=child('missing',fixtures['first']);bad.capture_holds495=[]
        try:online.history(bad)
        except Exception:pass
        else:raise AssertionError('capture coverage must stop')
        tests.append('missing_capture_in_history_path_rejected')
    finally:
        base.closed,base.own,online.select,online.history=methods
        cls.__init__,cls.one=original[:2]
        if original[2] is None:
            if '_capture495_installed' in cls.__dict__:delattr(cls,'_capture495_installed')
        else:cls._capture495_installed=original[2]
        native.PostTrackerTap=original[3];observer.PostTrackerTap=original[4]
        if hasattr(packing,'owner_extra'):del packing.owner_extra
        if hasattr(runtime,'capture_registry495'):del runtime.capture_registry495
    # Exercise actual packing functions with central prospective quota IO. All
    # logical fields survive in the existing child payload; no observer file.
    folder=Path(folder);folder.mkdir(mode=0o700)
    path=folder/'D495-A_source_1-private.json';quota.register_workspace(path)
    class FakeCodec:
        def save(self,p,v):quota.save(p,v)
        def save_receipt(self,p,v):return quota.save_receipt(p,v)
    codec=FakeCodec();codec_module=NS(load_receipt=receipt,canonical=digest)
    pack=PackedObservers495(runtime,codec,codec_module)
    pack.owner_extra=lambda label:dict(direct_holds495=[copy.deepcopy(fixtures['first'])])
    body=dict(rows=[{'all':'fields'}],final_state={'whole':'fixture'},controller_memory={'phase':'FIRST_LAP'})
    pack.save(path,body)
    private=dict(posts=[{'damage':0.,'extra':[1,2]}],actions=[{'all':'preserved'}],failure=None)
    final=dict(snapshot={'all':'fields'},memory={'all':'fields'},RNG={'all':'fields'},ledger={'all':'fields'},posts=private['posts'],actions=private['actions'])
    logical1=folder/'D495-A_source_1-observer-private.json';logical2=folder/'abc-world1-D495-A_source_1-observer-final-private.json'
    pack.save(logical1,private);pack.save_receipt(logical2,final)
    restored=receipt(path)
    assert restored['observer_records495']=={'observer-private':private,'observer-final':final}
    assert restored['rows']==body['rows'] and restored['final_state']==body['final_state'] and restored['direct_holds495']
    assert not logical1.exists() and not logical2.exists()
    tests.append('full_logical_observer_private_final_and_direct_holds_losslessly_packed')
    return dict(passed=True,tests=tests,test_count=len(tests),physics=0,selected_own_history_original_dependencies_stubbed=True,all_wrapper_code_and_provenance_real=True)
