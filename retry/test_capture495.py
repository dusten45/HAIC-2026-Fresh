"""Registered fake-only FULL ObserveMixin lifecycle; no physical constructor.

Parent calls run(graph, new_directory, binding) inside its static worker. This
file never runs tests on import. Only the BaseChild dependency is replaced;
the actual Stream and full ObserveMixin.__init__/one/dump/close execute.
"""
import copy
from contextlib import ExitStack
from dataclasses import asdict
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
from retry.capture494 import ImmutableWriter494,CaptureError494
from retry.capture495 import (Registry495,install_model495,authenticate_hold495,
    compare_flags495,compare_repeat495,read_ref,encoded,BUNDLE_BYTES495)


def run(graph,root,binding,writer=None):
    observer=graph.import_module('observer435');backend=graph.import_module('pilot420_backend')
    native_module=graph.import_module('actual437_boundary');capture=graph.import_module('capture434')
    tracker_type=capture.FinishLineTracker;original_update=tracker_type.update;original_tap=capture.PostTrackerTap
    Goal=graph.import_module('planner419').GoalLedger
    writer=writer or ImmutableWriter494(root,max_files=256,max_bytes=8*1024**2)
    registry=Registry495();hooks=registry.install(graph);tests=[];counter=[0];poisoned=[0]
    def poison(*args,**kwargs):poisoned[0]+=1;raise AssertionError('495_PHYSICS_FORBIDDEN')
    def expect(name,fn,error=Exception):
        try:fn()
        except error:tests.append(name);return
        raise AssertionError('495_EXPECTED_FAILURE:'+name)
    class Controller:
        def __init__(self,phase):self.value=phase;self.act_calls=0
        def phase(self):return self.value
        def memory(self):return dict(index=0,laststeer=0.,C=dict(phase=self.value))
        def act(self,world):self.act_calls+=1;return np.asarray([0.,.25,0.],np.float32)
    class Env:
        def __init__(self,n=4,terminal=False,done=False,collision=False,damage=0.):
            tracker=tracker_type(center=(100.,100.),forward=(1.,0.),half_width=1.,half_depth=1.)
            self.damage=NS(damage=0.);self.n=n;self.terminal=terminal;self.done=done
            self.collision=collision;self.final_damage=damage;self.bad_clock=False
            self.raw_hulls=[];self.raw_tires=[];self.calls=0
            self.unwrapped=NS(t=0.,finish_line_tracker=tracker,damage=self.damage,contacts=set(),_collision_this_step=False,
                car=NS(hull=NS(position=[0.,0.],linearVelocity=[1.,0.],angle=0.,angularVelocity=0.),
                       wheels=[NS(tiles=[NS(idx=j)]) for j in range(4)]))
        def step(self,command):
            self.calls+=1;r=self.unwrapped;self.raw_hulls=[];self.raw_tires=[]
            for i in range(1,self.n+1):
                self.raw_hulls.append(dict(raw_tick=i,time=r.t,origin_position=list(r.car.hull.position),
                    origin_linear_velocity=[1.,0.],COM_linear_velocity=[1.,0.],angle=0.,yaw=0.,extra_hull=7.))
                self.raw_tires.extend(dict(raw_tick=i,wheel=j,grass=False,force_ratio=.25,clipped=False,
                    omega=2.,extra_tire=.125) for j in range(4))
                r.t+=1/50;r.car.hull.position=[r.car.hull.position[0]+.1,0.]
                r._collision_this_step=bool(self.collision and i==2)
                if r._collision_this_step:r.contacts.add(1)
                if self.done and i==self.n:
                    r.finish_line_tracker.qualified_time_s=r.t;r.finish_line_tracker.finish_time_s=r.t
                r.finish_line_tracker.update(tuple(r.car.hull.position),tuple(r.car.hull.linearVelocity),0.,r.t+.02 if self.bad_clock else r.t)
            self.damage.damage=self.final_damage
            return None,0.,self.terminal,False,dict(collision=self.collision)
    class Trace:
        def __init__(self):self.enabled=False
        def reset(self):pass
        def enable(self):self.enabled=True
        def disable(self):self.enabled=False
    def snapshot(world):return dict(finish_tracker=asdict(world.finish_line_tracker))
    def save_receipt(path,value):return writer(path.name,value)['sha256']
    def save(path,value):writer(path.name,value)
    def base_init(self,env,label,phase='FIRST_LAP'):
        counter[0]+=1;self.env495=env;self.m=env.unwrapped;self.ctrl=Controller(phase);self.label=label
        self.rows=[];self.status='ACTIVE';self.closed=False;self.error=None;self.initial_count=0;self.tail_count=0
        self.ledger=Goal.start(0.,0);self.fixed=dict(line=[],free_profile=dict(ds=[1.,1.,1.,1.]));self.line=[]
        self.meter=NS(d=root,p=dict(semantic_sources={}),plan_sha='a'*64,auth={id(self.m):dict(number=counter[0],constructor_proof_sha256='b'*64)},streams={})
        self.base_dump_calls=0;self.base_close_calls=0
    def base_one(self,tag,first_override=None,prepared_nominal=None,prepared_before=None):
        before=copy.deepcopy(self.ctrl.memory() if prepared_before is None else prepared_before)
        nominal=self.ctrl.act(self.m) if prepared_nominal is None else prepared_nominal
        command=np.asarray(nominal if first_override is None else first_override,np.float32)
        memory_after=copy.deepcopy(self.ctrl.memory());self.env495.step(command)
        n=self.env495.n;r=self.m;self.ledger=Goal.start(0.,round(r.t*50))
        q=dict(raw_ticks=n,position=list(r.car.hull.position),velocity=list(r.car.hull.linearVelocity),time=r.t,
            damage=self.env495.damage.damage,terminal=self.env495.terminal,terminated=self.env495.terminal,
            truncated=False,finished=self.env495.done)
        safety=[]
        if q['damage']>0:safety.append('damage_increase')
        if self.env495.collision:safety.append('collision_or_obstacle')
        self.rows.append(dict(predicted=q,command=command.tolist(),memory_before=before,memory_after=memory_after,
            raw_hull=copy.deepcopy(self.env495.raw_hulls),tires=copy.deepcopy(self.env495.raw_tires),safety=safety,model_progress=0.))
        if self.env495.done:self.ctrl.value='DONE';self.status='FINISHED'
    def base_dump(self,d):self.base_dump_calls+=1;save(d/(self.label+'-private.json'),dict(rows=self.rows))
    def base_close(self):self.base_close_calls+=1;self.closed=True
    def metrics(q,tires,hulls,line,phase):
        flags=[]
        if q['damage']>0:flags.append('damage_increase')
        if any(t['raw_tick']==2 for t in tires) and getattr(metrics,'collision',False):flags.append('collision_or_obstacle')
        return dict(path_error_m=0.),flags
    def make(label,*,shadow=False,n=4,terminal=False,done=False):
        env=Env(n,terminal,done);phase='FINISH_CONFIRM' if done else 'FIRST_LAP'
        if shadow:
            c=observer.Child.__new__(observer.Child);base_init(c,env,label,phase);c.stream=observer.Stream(c)
        else:c=observer.Child(env,label,phase)
        return c
    with ExitStack() as stack:
        # A fake gate must not leave its registry/writer closures installed in a
        # graph that a parent might inspect or explicitly reuse afterwards.
        stack.callback(setattr,hooks['native'],'PostTrackerTap',original_tap)
        stack.callback(setattr,hooks['model'],'PostTrackerTap',original_tap)
        for name,value in [('__init__',base_init),('one',base_one),('dump',base_dump),('close',base_close)]:stack.enter_context(patch.object(observer.BaseChild,name,value))
        for name,value in [('snapshot',snapshot),('save_receipt',save_receipt),('metrics',metrics),('canonical_projection',lambda *a:dict(path_error_m=0.))]:stack.enter_context(patch.object(observer,name,value))
        stack.enter_context(patch.object(graph.import_module('loss389_analyze'),'save',save))
        stack.enter_context(patch.object(backend.TerminalVehicleTransition,'__init__',poison))
        stack.enter_context(patch.object(backend.Meter,'world',poison))
        info=install_model495(graph,registry,lambda c:writer,binding)
        stack.callback(setattr,observer.ObserveMixin,'__init__',info['original_init'])
        stack.callback(setattr,observer.ObserveMixin,'one',info['original_one'])
        stack.callback(delattr,observer.ObserveMixin,'_capture495_installed')
        a=make('fullA');a.one('fake_full_original');b=make('fullB');b.one('fake_full_original')
        ah=a.capture_holds495[0];bh=b.capture_holds495[0]
        authenticate_hold495(ah,binding);assert compare_repeat495(ah,bh,binding)['passed']
        assert a.ctrl.act_calls==b.ctrl.act_calls==1 and a.stream.calls==b.stream.calls==1
        assert len(a.stream.posts)==4 and len(a.stream.actions)==1 and len(a.capture_holds495)==1
        tests.append('FULL_original_ObserveMixin_init_Stream_one_nominal_once_and_cold_repeat')
        assert len([p for p in writer.files if 'fullA-h1-' in p])==5
        tests.append('exactly_four_16KiB_tick_receipts_plus_one_64KiB_bundle_no_outerseal')
        shadow=make('shadowBypass',shadow=True);assert not hasattr(shadow,'capture_session495')
        shadow.one('fake_shadow');assert shadow.ctrl.act_calls==1 and len(shadow.capture_holds495)==1
        tests.append('Shadow_bypasses_ObserveMixin_init_lazy_registration_before_FULL_one')
        a.one('fake_second');assert a.ctrl.act_calls==2 and a.stream.calls==2 and len(a.capture_holds495)==2
        tests.append('same_session_second_warm_hold_clock_and_ledger_lifecycle')
        done=make('partialDone',n=2,terminal=True,done=True);done.one('fake_terminal')
        dh=done.capture_holds495[0];authenticate_hold495(dh,binding)
        assert dh['wrapper_return']['controller_phase']=='DONE' and all(p['direct_tracker_capture']['controller_phase']=='FINISH_CONFIRM' for p in dh['common']['rows'])
        tests.append('FULL_one_terminal_partial_preserves_afteract_phase_before_return_DONE')
        damage=make('fullDamage');damage.env495.final_damage=.2;damage.one('fake_damage_return')
        damage_hold=damage.capture_holds495[0]
        assert all(p['direct_tracker_capture']['damage']==0 for p in damage_hold['common']['rows'])
        assert damage_hold['wrapper_return']['damage']==.2 and not compare_flags495(damage_hold,damage_hold,binding)['safe']
        tests.append('FULL_one_raw_damage0_wrapper_damage_point2_preserved_and_unsafe')
        a.dump(root);a.close();assert a.base_dump_calls==1 and a.base_close_calls==1 and a.stream.final_saved
        tests.append('FULL_original_dump_close_Stream_final_save_no_world_teardown_call')
        for label,mutator in [('common_post',lambda h:h['common']['rows'][0]['tracker_post'].update(collision=True)),
                              ('common_force',lambda h:h['common']['rows'][0]['pre_force'].update(grass=True)),
                              ('common_phase',lambda h:h['common']['rows'][0]['nominal'].update(controller_phase='LAUNCH')),
                              ('bool_clock',lambda h:h['common']['rows'][0].update(raw_clock=True)),
                              ('wrapper_damage',lambda h:h['wrapper_return'].update(damage=.2))]:
            bad=copy.deepcopy(bh);mutator(bad);expect('tamper_'+label,lambda bad=bad:authenticate_hold495(bad,binding))
        wrong=dict(binding);wrong['line_sha256']='f'*64
        expect('external_binding_mismatch',lambda:authenticate_hold495(bh,wrong))
        expect('bundle_oversize_typedstop',lambda:writer('oversize.json',{'x':'z'*(1024**2+1)}))
        oversized=copy.deepcopy(read_ref(bh['bundle_ref']));oversized['extra']='z'*BUNDLE_BYTES495
        oversized_ref=writer('over64KiB-bundle.json',oversized)
        oversized_hold=copy.deepcopy(bh);oversized_hold['bundle_ref']=oversized_ref
        expect('actual_64KiB_bundle_auth_cap',lambda:authenticate_hold495(oversized_hold,binding),CaptureError494)
        for field in ('pre_force','wrapper_return'):
            boolean=copy.deepcopy(read_ref(bh['bundle_ref']));boolean[field]['hold_id']=True
            boolean_ref=writer('bool-'+field+'-bundle.json',boolean)
            boolean_hold=copy.deepcopy(bh);boolean_hold['bundle_ref']=boolean_ref
            expect('bool_'+field+'_hold_id_rejected',lambda h=boolean_hold:authenticate_hold495(h,binding),CaptureError494)
        bad=make('badClock');bad.env495.bad_clock=True
        expect('FULL_one_callback_clock_error',lambda:bad.one('must_fail'))
        assert bad.capture_session495.failed and tracker_type.update is original_update and not original_tap._active
        tests.append('callback_exception_restores_tracker_FULL_one_spy_and_no_final_hold')
        assert len(bad.capture_holds495)==0 and 'act' not in bad.ctrl.__dict__
        bad=make('wrongOwner');bad.m=NS()
        expect('owner_changed_before_original_one',lambda:bad.one('must_fail'))
        # Genuine native Dispatch437 uses the same isolated production tap.
        env=Env();ctrl=Controller('FIRST_LAP');authority=NS(env=env,ctrl=ctrl,_bound_env=env,_bound_ctrl=ctrl,ledger=Goal.start(0.,0))
        session=registry.native(authority,owner='native',writer=writer,binding=binding)
        dispatch=native_module.Dispatch437(env,'FAKE495');dispatch.call([0.,.25,0.],Trace())
        kwargs=dict(tires=env.raw_tires,hulls=env.raw_hulls,nominal_phase='FIRST_LAP',ledger_after=dict(last_clock_tick=4),terminal=False,terminated=False,truncated=False,wrapper_return_phase='FIRST_LAP')
        payload=session.build_payload(**kwargs);outer=writer('existing-native-after.json',dict(direct_bundle495=payload))
        ref={**outer,'pointer':'/direct_bundle495'};native=session.finalize_payload(payload,ref)
        assert compare_flags495(native,bh,binding)['safe'] and ctrl.act_calls==0
        factref=writer('existing-native-fact.json',dict(capture_hold495=native))
        native['sealed_hold_ref']={**factref,'pointer':'/capture_hold495'};authenticate_hold495(native,binding)
        tests.append('production_Dispatch437_native_bundle_existing_after_and_optional_fact_pointer')
        check=copy.deepcopy(read_ref(bh['bundle_ref']));check['pre_force']['tires'][0]['extra_tire']=.5
        # Build a second, internally valid immutable bundle; repeat must compare
        # fields beyond the summarized grass/clip metrics as well.
        forged_ref=writer('altered-full-tire-bundle.json',check)
        from retry.capture495 import _rebuild
        forged=copy.deepcopy(bh);forged['bundle_ref']=forged_ref;forged['common']=_rebuild(check,forged_ref,binding)
        authenticate_hold495(forged,binding)
        expect('repeat_checks_ALL_full_tire_fields',lambda:compare_repeat495(bh,forged,binding))
        assert poisoned[0]==0 and tracker_type.update is original_update and capture.PostTrackerTap is original_tap
        tests.append('poisoned_physics_constructor_world_calls_zero_original_capture_global_unchanged')
    return dict(passed=True,test_count=len(tests),tests=tests,full_ObserveMixin_one_executed=True,
                physical_worlds=0,physical_resets=0,physical_steps=0,poison_calls=poisoned[0],
                fake_dispatches_only=True,receipt_files=len(writer.files),receipt_bytes=sum(writer.files.values()),
                tick_cap_bytes=16*1024,bundle_cap_bytes=BUNDLE_BYTES495,
                private_fixtures495=dict(first=ah,repeat=bh,native=native,unsafe=damage_hold))
