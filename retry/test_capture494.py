"""Exercise production callback/tap/Dispatch with fake env/controller only."""
import copy,json
from types import SimpleNamespace as NS
from retry.capture494 import *

class FakeController:
    def __init__(self,phase='FIRST_LAP'):self.value=phase;self.act_calls=0
    def phase(self):return self.value
    def memory(self):return {'index':0,'laststeer':0.,'C':{'phase':self.value}}
    def act(self,*a):self.act_calls+=1;raise AssertionError('NO_ACT_IN_CALLBACK_TEST')

class FakeEnv:
    def __init__(self,tracker_type,n=4,collision=False,damage=.0,terminal=False):
        tracker=tracker_type(center=(0.,0.),forward=(1.,0.),half_width=1.,half_depth=1.)
        self.damage=NS(damage=0.)
        self.unwrapped=NS(t=0.,finish_line_tracker=tracker,damage=self.damage,contacts=set(),_collision_this_step=False,car=NS(hull=NS(position=[0.,0.],linearVelocity=[1.,0.],angle=0.,angularVelocity=0.),wheels=[NS(tiles=[NS(idx=j)]) for j in range(4)]))
        self.n=n;self.collision=collision;self.final_damage=damage;self.terminal=terminal;self.bad_clock=False;self.fake_dispatches=0
    def step(self,command):
        self.fake_dispatches+=1;r=self.unwrapped
        for i in range(1,self.n+1):
            r.t=i/50;r.car.hull.position=[i/10,0.];r._collision_this_step=bool(self.collision and i==2)
            if r._collision_this_step:r.contacts.add(1)
            r.finish_line_tracker.update(tuple(r.car.hull.position),tuple(r.car.hull.linearVelocity),0.,r.t+.02 if self.bad_clock else r.t)
        self.damage.damage=self.final_damage
        return None,0.,self.terminal,False,{'collision':self.collision}

class FakeTrace:
    def __init__(self):self.enabled=False
    def reset(self):pass
    def enable(self):self.enabled=True
    def disable(self):self.enabled=False

def run(graph,root,binding):
    from retry.capture494 import Registry494,ImmutableWriter494
    native=graph.import_module('actual437_boundary');model=graph.import_module('observer435');authority=graph.import_module('authority439')
    Goal=graph.import_module('planner419').GoalLedger
    tracker_type=graph.import_module('capture434').FinishLineTracker
    original_update=tracker_type.update;original_tap=graph.import_module('capture434').PostTrackerTap
    writer=ImmutableWriter494(root);registry=Registry494();hooks=registry.install(graph);tests=[]
    def expect(name,fn,error=SchemaError493):
        try:fn()
        except error:tests.append(name);return
        raise AssertionError('MUST_FAIL:'+name)
    def setup(owner,kind='model',n=4,collision=False,damage=0.,terminal=False,phase='FIRST_LAP'):
        env=FakeEnv(tracker_type,n,collision,damage,terminal);ctrl=FakeController(phase)
        if kind=='native':
            obj=authority.NativeAuthority439(env,ctrl,Goal.start(0.,0),{'line':[]},charge_native=lambda:(_ for _ in ()).throw(AssertionError('NO_CHARGE')))
            session=registry.native(obj,owner=owner,writer=writer,binding=binding)
        else:
            obj=NS(m=env.unwrapped,ctrl=ctrl,ledger=Goal.start(0.,0));session=registry.model(obj,owner=owner,writer=writer,binding=binding)
        return env,ctrl,obj,session
    def emit(parts,kind='model',legacy=None):
        env,ctrl,obj,session=parts
        if kind=='native':
            tr=FakeTrace();obj.dispatcher.call([0.,0.,0.],tr);assert not tr.enabled
        else:
            callback=legacy or (lambda p:None)
            with hooks['model'].PostTrackerTap(env.unwrapped.finish_line_tracker,callback):env.step([0.,0.,0.])
        assert tracker_type.update is original_update and not original_tap._active
        return parts
    def finish(parts,done=False,tires=None,hulls=None):
        env,ctrl,obj,s=parts;n=env.n
        if done:ctrl.value='DONE'
        return s.finish_hold(tires=tires if tires is not None else [dict(raw_tick=i,wheel=j,grass=False,force_ratio=.25) for i in range(1,n+1) for j in range(4)],hulls=hulls if hulls is not None else [dict(raw_tick=i,time=(i-1)/50,origin_position=[(i-1)/10,0.]) for i in range(1,n+1)],nominal_phase='FINISH_CONFIRM' if done else 'FIRST_LAP',ledger_after={'last_clock_tick':n},terminal=env.terminal,terminated=env.terminal,truncated=False,wrapper_return_phase=ctrl.phase())
    a=finish(emit(setup('nativeA','native'),'native'));b=finish(emit(setup('modelA')))
    assert compare_flags494(a,b,binding)['safe'];tests.append('production_native_Dispatch_and_model_tap_direct_capture')
    b2=finish(emit(setup('modelB')));assert compare_repeat494(b,b2,binding)['passed'];tests.append('different_owner_receipt_paths_all_measurements_exact')
    assert a['common']['rows'][0]['direct_tracker_capture']['observed_ref']['path']!=b['common']['rows'][0]['direct_tracker_capture']['observed_ref']['path']
    def mutation(p):p.update(damage=999,phase='DONE',collision=True);p['position'][0]=999
    stable=finish(emit(setup('mutableLegacy'),legacy=mutation));assert compare_flags494(a,stable,binding)['safe'];tests.append('sidecar_precedes_mutable_legacy_post_rewrite')
    ca=finish(emit(setup('collisionN','native',collision=True,damage=.2),'native'));cb=finish(emit(setup('collisionM',collision=True,damage=.2)))
    assert all(p['direct_tracker_capture']['damage']==0 for p in ca['common']['rows']) and ca['wrapper_return']['damage']==.2
    assert compare_flags494(ca,cb,binding)['safe'] is False;tests.append('raw_damage0_wrapper_return_point2_kept_separate')
    cc=cb['common']['rows'];assert cc[2]['direct_tracker_capture']['collision_raw_event'] is False and cc[2]['direct_tracker_capture']['begin_contact_latch_ids']==[1];tests.append('BeginContact_hold_latch_is_not_tick_event_or_touch')
    da=finish(emit(setup('damageOnlyN','native',damage=.2),'native'));db=finish(emit(setup('damageOnlyM',damage=.2)))
    assert not compare_flags494(da,db,binding)['safe'];tests.append('wrapper_return_damage_alone_retained_in_safety')
    p=setup('partialTerminal',n=2,terminal=True,phase='FINISH_CONFIRM');partial=finish(emit(p),done=True)
    assert all(x['direct_tracker_capture']['controller_phase']=='FINISH_CONFIRM' for x in partial['common']['rows']) and partial['wrapper_return']['controller_phase']=='DONE'
    authenticate_hold494(partial,binding);tests.append('partial_terminal2_callbacks_phase_before_DONE_after_return')
    expect('partial_nonterminal_rejected',lambda:finish(emit(setup('partialBad',n=2))))
    expect('missing_all_callbacks_rejected',lambda:finish(emit(setup('missingAll',n=0))))
    expect('fifth_callback_rejected',lambda:emit(setup('tooMany',n=5)))
    p=setup('wrongClock');p[0].bad_clock=True;expect('same_tick_before_post_clock_mix_rejected',lambda:emit(p))
    p=setup('wrongOwner');p[2].ctrl=FakeController();expect('native_or_model_owner_change_rejected',lambda:emit(p))
    p=setup('badLedger');p[2].ledger=NS(last_clock_tick=False);expect('bool_ledger_clock_rejected',lambda:emit(p))
    p=setup('badWheel');p[0].unwrapped.car.wheels[0].tiles[0].idx=True;expect('bool_tile_index_rejected',lambda:emit(p))
    p=setup('badTire');emit(p);t=[dict(raw_tick=i,wheel=j,grass=False) for i in range(1,5) for j in range(4)];t[0]['wheel']=False
    expect('bool_wheel_index_rejected',lambda:finish(p,tires=t))
    for field in ('raw_clock','wheel_road_contacts'):
        forged=copy.deepcopy(b);forged['common']['rows'][0]['direct_tracker_capture'][field]=True
        expect('bool_capture_'+field+'_rejected',lambda forged=forged:authenticate_hold494(forged,binding))
    for name,path,value in [('common_clock',['common','rows',0,'raw_clock'],True),('common_contact',['common','rows',0,'tracker_post','wheel_road_contacts'],True),('common_phase',['common','rows',0,'nominal','controller_phase'],'LAUNCH'),('common_position',['common','rows',0,'tracker_post','position'],[99.,0.]),('pre_force_grass',['common','rows',0,'pre_force','wheel_grass'],[True]*4),('wrapper_return',['wrapper_return','damage'],9.)]:
        forged=copy.deepcopy(b);v=forged
        for key in path[:-1]:v=v[key]
        v[path[-1]]=value
        expect('sealed_'+name+'_tamper_rejected',lambda forged=forged:authenticate_hold494(forged,binding))
    wrong=dict(binding);wrong['line_sha256']='f'*64
    expect('external_source_input_binding_mismatch_rejected',lambda:authenticate_hold494(b,wrong))
    expect('immutable_receipt_overwrite_rejected',lambda:writer('modelA-h1-t1.json',{}))
    expect('nonfinite_serializer_rejected_before_publish',lambda:writer('nan.json',{'x':float('nan')}),ValueError)
    class Boom(Exception):pass
    p=setup('callbackRaises')
    try:emit(p,legacy=lambda row:(_ for _ in ()).throw(Boom('legacy callback failure')))
    except Boom:pass
    else:raise AssertionError('callback exception swallowed')
    assert tracker_type.update is original_update and not original_tap._active and p[3].failed
    expect('failed_callback_session_cannot_finish',lambda:finish(p));tests.append('callback_exception_restores_original_tracker_and_stops_session')
    p=setup('nativeRaises','native');p[3].writer=lambda *a:(_ for _ in ()).throw(Boom('writer failure'))
    try:emit(p,'native')
    except Boom:pass
    else:raise AssertionError('native exception swallowed')
    assert tracker_type.update is original_update and not original_tap._active and p[3].failed and not p[2].dispatcher.ticket.success
    tests.append('native_writer_exception_restores_tracker_no_success_ticket')
    refs=[a,b,b2,stable,ca,cb,da,db,partial]
    for h in refs:authenticate_hold494(json.loads(json.dumps(h,allow_nan=False)),binding)
    tests.append('real_immutable_serializer_read_ref_JSON_roundtrip')
    assert all(s.controller.act_calls==0 for s in registry.sessions)
    assert graph.import_module('capture434').PostTrackerTap is original_tap
    tests.append('no_extra_nominal_act_and_original_capture_class_unchanged')
    return dict(passed=True,test_count=len(tests),tests=tests,positive_holds=len(refs),receipt_files=len(writer.files),receipt_bytes=sum(writer.files.values()),physical_worlds=0,physical_resets=0,physical_steps=0,fake_dispatches_only=True,full_ObserveMixin_one_not_executed=True,measured_capture_provenance_real_files=True)
