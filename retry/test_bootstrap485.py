"""485 bootstrap fixtures: fake native only; every real physics entry is forbidden."""
import contextlib,copy,hashlib,json,tempfile,unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch,Mock
import numpy as np
from retry import bootstrap485 as b
from retry.planner419 import ActualObservation
from retry.receipt421_io import save_receipt,load_receipt

class FakeMeter:
    def __init__(self):self.events=[];self.active=False
    def begin_actual(self):self.active=True
    def end_actual(self):self.active=False
    def guard(self):pass
    def checkpoint(self,*args,**kwargs):pass
    def charge(self,kind,slot):self.events.append(kind)
    @contextlib.contextmanager
    def geometry(self,slot):yield

class FakeQuota:
    def __init__(self,path):self.native_dir=Path(path)
    def save_receipt(self,path,value):return save_receipt(path,value)
    save=save_receipt

class FakeEnv:
    def __init__(self,meter,*,reset_ticks=2,action_ticks=4,rereset=False):
        self.unwrapped=self;self.meter=meter;self.t=0.;self.calls=[];self.progress=0.;self.reset_ticks=reset_ticks;self.action_ticks=action_ticks;self.rereset=rereset;self.closed=False
        self.finish_line_tracker=NS(candidate_crossing_time_s=None,finish_time_s=None)
        self.world=NS(bodies=[object()],joints=[object()])
        self.world.DestroyBody=lambda x:self.world.bodies.remove(x)
        self.world.DestroyJoint=lambda x:self.world.joints.remove(x)
    def reset(self,**kwargs):
        assert self.meter.events[-1]=='reset';self.calls.append('reset')
        if self.rereset:return self.reset(**kwargs)
        for _ in range(self.reset_ticks):self.step(None)
        return {},{}
    def step(self,command):
        expected='reset_raw' if command is None else 'action_raw'
        assert self.meter.events[-1]==expected;self.calls.append(expected);self.t+=.02
        return {},0.,False,False,{'collision':False}
    def wrapper_action(self,command):
        assert self.meter.events[-1]=='action';self.calls.append('action')
        for _ in range(self.action_ticks):self.step(command)
        self.progress+=4.
        return {},0.,False,False,{'collision':False}
    def close(self):self.closed=True

class FakeController:
    terminal_at=None
    def __init__(self,env,fixed,pace):self.env=env;self.policy=NS(nodes=np.asarray([0.,5.,5.,5.,5.]));self.n=0;self.current='LAUNCH'
    def phase(self):return self.current
    def memory(self):return {'C':{'phase':self.current},'calls':self.n}
    def act(self,env):
        self.n+=1
        if self.n>=2:self.current='FIRST_LAP'
        if self.terminal_at==self.n:self.current='FINISH_CONFIRM'
        return np.asarray([.01,.6,0.],np.float32)

class FakeNative:
    def __init__(self,env,ctrl,ledger,fixed,charge_native):self.env=env;self.ctrl=ctrl;self.ledger=ledger;self.rows=[];self.charge=charge_native;self.prepared=None;self.ticket=None
    def prepare_before_nominal(self):self.prepared=copy.deepcopy(self.ctrl.memory())
    def dispatch(self,command,trace):
        self.charge();result=self.env.wrapper_action(command)
        self.ticket=NS(posts=[{'tick':j} for j in range(self.env.action_ticks)],native_tires=[],native_hulls=[],success=True,command=np.asarray(command,np.float32).tolist())
        return result
    def commit_prefix_fact485(self):
        before=self.ledger;self.ledger=before.advance_actual(ActualObservation(self.env.progress,round(self.env.t*50),False))
        row=dict(step=self.global_step,command=self.ticket.command,nominal=self.nominal,memory_before=self.prepared,nominal_memory_after=self.ctrl.memory(),safety=[],ended=False,truncated=False,raw_ticks=self.env.action_ticks,progress_after=self.env.progress)
        self.rows.append(row);return dict(row=row,ledger_before=asdict(before),ledger_after=asdict(self.ledger))

class Bootstrap485Tests(unittest.TestCase):
    def run_fake(self,*,reset_ticks=2,action_ticks=4,rereset=False,terminal_at=None,quarter=10.):
        temporary=tempfile.TemporaryDirectory(prefix='haic485-bootstrap-pure-');self.addCleanup(temporary.cleanup);directory=Path(temporary.name)
        meter=FakeMeter();env=FakeEnv(meter,reset_ticks=reset_ticks,action_ticks=action_ticks,rereset=rereset)
        coeff=directory/'coeff.json';coeff.write_text(json.dumps({'coefficients':[0.,0.,0.]}))
        original_sha=b.sha
        fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[quarter]*4,speed=[0.,5.,5.,5.,5.]))
        def full(env,obs,memory):return dict(physical={'progress':env.progress,'time':env.t},memory=copy.deepcopy(memory))
        patches=[patch('retry.diagnose.make_env',return_value=env),patch.object(b,'sha',side_effect=lambda p:b.COEFFICIENT_SHA if Path(p)==coeff else original_sha(p)),patch.object(b,'complete_state',side_effect=full),patch.object(b,'from_actual_full',side_effect=lambda value:value['physical']),patch.object(b,'native_model485',return_value={'mass':10.}),patch.object(b,'geometry485',return_value=(fixed,np.ones(5),np.asarray([0.,5.,5.,5.,5.]))),patch.object(b,'ActualC',FakeController),patch.object(FakeController,'terminal_at',terminal_at),patch.object(b,'NativePrefix485',FakeNative),patch.object(b,'Trace',return_value=NS(disable=lambda:None)),patch.object(b,'sensor',side_effect=lambda env:dict(pos=[0.,0.],vel=[0.,1.],time=env.t)),patch.object(b,'canonical_projection',return_value={'arc':0.})]
        with contextlib.ExitStack() as stack:
            mocks=[stack.enter_context(p) for p in patches]
            try:out=b.prepare_case(dict(slot='D485-A',case_identity_digest='a'*64,seed='ASSIGNED_ONLY',track_id='assigned'),meter,FakeQuota(directory),directory,coefficients_path=coeff,identity_check=lambda case,actual: {'same_env':actual is env})
            except BaseException as exc:out=exc
        return out,env,meter,directory,mocks

    def test_natural_launch_then_first_root_before_next_witness_and_teardown(self):
        out,env,meter,directory,mocks=self.run_fake()
        self.assertIsInstance(out,dict);self.assertEqual(out['status'],'NATIVE_ROOT_AND_WITNESS_OBSERVED')
        self.assertEqual(out['prefixproof']['actions'],3);self.assertEqual(out['counts'],dict(slot_actions=4,slot_resets=1,slot_reset_raw=2,slot_action_raw=16))
        self.assertEqual(out['state']['progress'],12.);self.assertEqual(out['before']['calls'],3)
        self.assertEqual(out['witness_row']['step'],4);self.assertEqual(out['witness_row']['memory_before'],out['before'])
        self.assertTrue(out['native_closed']);self.assertTrue(env.closed);self.assertFalse(env.world.bodies or env.world.joints or meter.active)
        trace=load_receipt(directory/'D485-A/native-trace-private.json')
        self.assertEqual(trace['rows'][0]['memory_before']['C']['phase'],'LAUNCH')
        self.assertEqual(trace['rows'][0]['nominal_memory_after']['C']['phase'],'LAUNCH')
        self.assertEqual(trace['rows'][1]['nominal_memory_after']['C']['phase'],'FIRST_LAP')
        for row in trace['rows']:self.assertEqual(row['command'],row['nominal'])
        journal=load_receipt(directory/'D485-A/native-charge-journal-private.json')
        self.assertEqual([e['kind'] for e in journal['events']],meter.events)
        self.assertTrue(all(e['charged_before_call'] for e in journal['events']))
        mocks[0].assert_called_once();mocks[5].assert_called_once()

    def test_action128_is_only_allowed_for_root127_witness(self):
        out,env,meter,directory,_=self.run_fake(quarter=508.)
        self.assertEqual(out['prefixproof']['actions'],127)
        self.assertEqual(out['counts']['slot_actions'],128)
        self.assertEqual(out['counts']['slot_action_raw'],512)
        self.assertEqual(out['witness_row']['step'],128)
        self.assertTrue(env.closed)

    def test_no_root_by127_closes_before_action128_no_replacement(self):
        out,env,meter,directory,_=self.run_fake(quarter=512.)
        self.assertEqual(out['status'],'PREPARATION_INELIGIBLE')
        self.assertEqual(meter.events.count('action'),127)
        self.assertFalse((directory/'D485-A/witness-private.json').exists())
        self.assertEqual(meter.events.count('reset'),1);self.assertTrue(env.closed)

    def test_internal_second_reset_is_blocked_before_charge_and_call(self):
        out,env,meter,directory,_=self.run_fake(rereset=True)
        self.assertIsInstance(out,b.TechnicalStop);self.assertIn('SECOND_RESET',str(out))
        self.assertEqual(env.calls,['reset']);self.assertEqual(meter.events,['reset']);self.assertTrue(env.closed)
        self.assertFalse(meter.active)

    def test_reset_raw65_cannot_enter_native_function(self):
        out,env,meter,directory,_=self.run_fake(reset_ticks=65)
        self.assertIsInstance(out,b.ResourceStop);self.assertIn('reset_raw',str(out))
        self.assertEqual(env.calls.count('reset_raw'),64);self.assertEqual(meter.events.count('reset_raw'),64)
        self.assertFalse(env.world.bodies or env.world.joints or meter.active)

    def test_action_raw513_cannot_enter_native_function(self):
        out,env,meter,directory,_=self.run_fake(action_ticks=513)
        self.assertIsInstance(out,b.ResourceStop);self.assertIn('action_raw',str(out))
        self.assertEqual(env.calls.count('action_raw'),512);self.assertEqual(meter.events.count('action_raw'),512)
        self.assertEqual(env.calls.count('action'),1);self.assertTrue(env.closed)

    def test_terminal_prefix_is_ineligible_no_witness_no_rescue(self):
        out,env,meter,directory,_=self.run_fake(terminal_at=2)
        self.assertEqual(out['status'],'PREPARATION_INELIGIBLE');self.assertEqual(meter.events.count('action'),2)
        self.assertFalse((directory/'D485-A/witness-private.json').exists());self.assertTrue(env.closed)

    def test_mass_comes_from_existing_native_bodies_without_probe(self):
        env=NS(unwrapped=NS(car=NS(hull=NS(mass=10.),wheels=[NS(mass=2.)]*4)))
        with patch('retry.diagnose.make_env',side_effect=AssertionError('NO_WORLD')) as guard:
            model=b.native_model485(env)
        self.assertEqual(model['mass'],18.);self.assertEqual(model['effective_mass'],18.+4*1.6/.54**2);guard.assert_not_called()

    def geometry_fixture(self,feasible=True,clearance=0.):
        return dict(model_calls=194,free_feasible=feasible,free_clearance=[clearance],line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,curvature=[0.]*4,speed=[0.,5.,5.,5.,5.],max_abs_curvature=0.))

    def test_geometry_one_solve_no_unnecessary_repair_four_projection(self):
        fixed=self.geometry_fixture();model={'mass':10.};nodes=np.asarray([0.,4.,4.,4.,4.])
        with patch.object(b,'solve',return_value=fixed) as solve,patch.object(b,'project') as repair,patch.object(b,'project_four',return_value=nodes) as projection:
            out,pace,result=b.geometry485({},model,[0.,0.,0.])
        solve.assert_called_once();repair.assert_not_called();projection.assert_called_once()
        self.assertFalse(result.flags.writeable);self.assertEqual( len(pace),5)

    def test_geometry_single_old_numerical_repair_and_hard_eval_bound(self):
        for evaluations,accepted in [(100,True),(101,False)]:
            with self.subTest(evaluations=evaluations):
                fixed=self.geometry_fixture(False,-.0005);repaired=dict(geometry_evaluations=evaluations,line=fixed['line'],coefficients=[0.],profile=fixed['free_profile'],clearance=[0.])
                with patch.object(b,'solve',return_value=fixed) as solve,patch.object(b,'project',return_value=repaired) as repair,patch.object(b,'project_four',return_value=np.asarray([0.,4.,4.,4.,4.])):
                    if accepted:b.geometry485({}, {'mass':10.},[0.,0.,0.])
                    else:
                        with self.assertRaises(b.LedgerStop439):b.geometry485({}, {'mass':10.},[0.,0.,0.])
                solve.assert_called_once();repair.assert_called_once()

    def test_geometry_unsupported_has_no_retry_or_repair(self):
        with patch.object(b,'solve',return_value=self.geometry_fixture(False,-.1)) as solve,patch.object(b,'project') as repair,patch.object(b,'project_four') as projection:
            with self.assertRaises(b.PreparationIneligible485):b.geometry485({}, {'mass':10.},[0.,0.,0.])
        solve.assert_called_once();repair.assert_not_called();projection.assert_not_called()

    def test_actual_prepare_launch_uses_safety_clock_not_first_only_gate(self):
        from retry.authority439 import NativeAuthority439
        from retry.planner419 import GoalLedger
        authority=NativeAuthority439.__new__(NativeAuthority439);env=NS(damage=NS(damage=0.),unwrapped=NS(finish_line_tracker=NS()));ctrl=NS(memory=lambda:{'C':{'phase':'LAUNCH'}},phase=lambda:'LAUNCH')
        authority.env=authority._bound_env=env;authority.ctrl=authority._bound_ctrl=ctrl;authority.halted=False;authority.ticket=authority.prepared=None;authority.awaiting_verification=False;authority._ledger=GoalLedger.start(0.,0);authority.fixed={'line':[]}
        with patch('retry.authority439.sensor',return_value={'time':0.,'pos':[0.,0.],'vel':[0.,0.]}),patch('retry.authority439.canonical'),patch('retry.authority439.canonical_projection',return_value={}),patch('retry.authority439.safety_flags',return_value=[]) as safety,patch('retry.authority439.raw_capture_pairs',return_value=[]),patch('retry.authority439.rng',return_value={}):
            prepared=authority.prepare_before_nominal()
        self.assertEqual(prepared['phase'],'LAUNCH');safety.assert_called_once()

    def test_pure_p4_executor_natural_launch_first_and_own_terminal_node(self):
        from retry.signed417_executor import CoherentExecutor
        fixed=self.geometry_fixture();fixed['model']={'mass':18.,'effective_mass':40.,'rear_traction_accel':8.,'brake_accel':5.,'lateral_accel':10.}
        policy=CoherentExecutor(fixed);policy.nodes=np.asarray([0.,4.,5.,6.,7.]);policy.nodes.setflags(write=False)
        nominal=np.asarray([.02,.37,0.],np.float32)
        state=dict(time=0.,speed=0.,pos=[0.,0.],vel=[0.,0.])
        launch,record=policy.act(state,nominal,{})
        np.testing.assert_array_equal(launch,nominal);self.assertEqual(policy.phase,'LAUNCH')
        first,record=policy.act(dict(time=.08,speed=1.,pos=[1.,0.],vel=[1.,0.]),nominal,{})
        self.assertEqual(policy.phase,'FIRST_LAP');self.assertEqual(record['r'],np.sqrt(.1*16))
        finish=dict(candidate_crossing_time_s=.1,qualified_time_s=.09,crossing_from_back=True,forward=[0.,1.],center=np.asarray([0.,0.]),half_depth=2.,half_width=2.)
        terminal,record=policy.act(dict(time=.16,speed=1.,pos=[0.,1.],vel=[0.,1.]),nominal,finish)
        self.assertEqual(policy.phase,'FINISH_CONFIRM');self.assertEqual(record['r'],7.);self.assertEqual(record['f'],0.)
        self.assertIsNone(finish.get('finish_time_s'));self.assertFalse(policy.nodes.flags.writeable)

if __name__=='__main__':unittest.main()
