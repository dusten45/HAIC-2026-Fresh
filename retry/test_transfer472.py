"""472 current-own-reference/native authority fixtures; all integration forbidden."""
import ast,copy,inspect,json,pickle,random,tempfile,unittest
from contextlib import ExitStack,contextmanager,nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop,TechnicalStop

R=Path('/workspace/haic-private-retry-20261009')

def sources472(old):
 sources=dict(old['semantic_sources']);code=Path(__file__).resolve().parent
 for name in ('query472.py','law468.py'):
  path=code/name;sources[str(path)]=sha(path)
 return sources

@contextmanager
def current472():
 from retry.receipt421_io import load_receipt,save_receipt
 from retry.fixture438 import stored_env
 from retry.actual437_boundary import live_proxy
 from retry.paired417_common import SourceC
 from retry.planner419 import GoalLedger
 from retry.query472 import Query472,inject_p4_nodes472
 from retry.law468 import profile_inputs468
 old=read(R/'stage453/plan.json');fixed=read(old['fixed_plan']);pace=np.asarray(read(old['pace_path'])['frozen268']);bundle=load_receipt(R/'stage463-native/actual_SecantOnce/SecantOnce_step126-before-native-private.json');full=bundle['full_pre_before_nominal'];env=stored_env(copy.deepcopy(full));ctrl=SourceC(fixed,pace,copy.deepcopy(full['controller']));_,nodes,path=profile_inputs468(R,fixed,pace);inject_p4_nodes472(ctrl,nodes)
 before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(live_proxy(env));ledger=GoalLedger(**bundle['actual_ledger_before']);history=SimpleNamespace(env=env,obs=np.zeros((4,84,84),np.float32),ctrl=ctrl,ledger=ledger,initial=SimpleNamespace(actual_root_digest=ledger.digest()),native=SimpleNamespace(global_step=126),require_live=lambda:None)
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);meter=SimpleNamespace(d=d,p=dict(fixed_plan=old['fixed_plan'],semantic_sources=sources472(old)),queries=[],model=lambda label:nullcontext())
  def capture(state,memory,view,label,**kw):
   value=dict(state=state,memory=memory,ledger=view.__dict__,policy_digest=kw['context'].policy_digest,gate=kw['gate']);descriptor=d/(label+'-fixture-proof.json');save_receipt(descriptor,value);return dict(path=str(descriptor),sha256=sha(descriptor))
  meter.capture_inputs=capture;query=Query472(R,meter,fixed,pace)
  yield query,history,before,nominal

@contextmanager
def pending472():
 from retry.test_parent436 import stored_parent
 from retry.parent436 import decode
 from retry.fixture438 import stored_env
 from retry.actual437_boundary import live_proxy
 from retry.paired417_common import SourceC
 from retry.planner419 import GoalLedger
 from retry.routing442 import ObservedHistory442,ObservedRouteValues442
 from retry.query472 import Query472,inject_p4_nodes472
 from retry.law468 import profile_inputs468
 from retry.receipt421_io import save_receipt
 p=stored_parent();state=decode(p.snapshot_bytes);full=read(R/'stage437/actual_C0/final-private.json');full['physical']=copy.deepcopy(state['physical']);full['wrapper'].update(finish_tracker=copy.deepcopy(state['finish_tracker']),elapsed_raw_steps=state['elapsed_raw_steps'],finish_time_s=None,finish_qualified_time_s=state['finish_tracker']['qualified_time_s']);env=stored_env(full)
 old=read(R/'stage453/plan.json');fixed=read(old['fixed_plan']);pace=np.asarray(read(old['pace_path'])['frozen268']);ctrl=SourceC(fixed,pace,decode(p.memory_before_bytes));_,nodes,path=profile_inputs468(R,fixed,pace);inject_p4_nodes472(ctrl,nodes);before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(live_proxy(env))
 initial=ObservedRouteValues442(**decode(p.history_initial_ledger_bytes));values=ObservedRouteValues442(**decode(p.forecast_ledger_bytes));ledger=GoalLedger(values.progress_m,values.goal_m,values.age_actions,values.last_clock_tick,values.deadline_missed,values.done);actions=decode(p.history_actions_bytes);native=SimpleNamespace(env=env,ctrl=ctrl,obs=np.zeros((4,84,84),np.float32),ledger=ledger,halted=False,awaiting_verification=False,dispatcher=SimpleNamespace(calls=len(actions)),global_step=127)
 h=ObservedHistory442.__new__(ObservedHistory442);h.native=native;h.fixed=fixed;h.bound_env=env;h.bound_ctrl=ctrl;h.token='SYNTHETIC_P4_NATIVE472';h.root=decode(p.history_root_bytes);h.initial=initial;h.values=values;h.posts=decode(p.history_posts_bytes);h.actions=actions;h.root_dispatch=0;h.verified=len(actions)
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);meter=SimpleNamespace(d=d,p=dict(fixed_plan=old['fixed_plan'],semantic_sources=sources472(old)),queries=[],model=lambda label:nullcontext())
  def capture(state,memory,view,label,**kw):
   path=d/(label+'-fixture-proof.json');save_receipt(path,dict(state=state,memory=memory,ledger=view.__dict__,policy_digest=kw['context'].policy_digest,gate=kw['gate']));return dict(path=str(path),sha256=sha(path))
  meter.capture_inputs=capture;query=Query472(R,meter,fixed,pace);yield query,h,before,nominal

class Transfer472Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage472';d.mkdir();native=root/'stage472-native';native.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]});before=root/'project-effective-budget-v475.json';save(before,dict(version=475,research_remaining=26346,actual_cumulative_wrapper_actions=1321718,final_reserved_actions=84000,final_reserve_used=0))
  p=dict(stage=472,deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),scope=dict(ticks=8738,worlds=181),caps=dict(ticks=9216,worlds=185,CPU_s=900,wall_s=1200,actual_actions=195,resets=1,max_parallel=1),sources={},semantic_sources={},protected={},original408_preserve={},budget_before_path=str(before),budget_before_sha256=sha(before),ledger_path=str(root/'project-effective-budget-v476.json'),native_directory=str(native))
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')));return d,p

 def test_real_runner_one_meter_fresh41_before_only_candidate_native_entry(self):
  from retry import transfer472 as r,diagnose
  from retry.meter472 import Meter472
  from retry.planner419 import GoalLedger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen={}
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d,p=self.fixture_plan(root);c=r.contract();p.update(execution=c,caps=c['runtime_caps'],budget_fixture=r.cost_fixture(),world_audit=r.world_audit());save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr));stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state));stack.enter_context(patch.object(r,'check_storage',return_value={}));stack.enter_context(patch.object(Meter472,'check_storage'))
   realcreate=r.create_meter
   def create(path):
    meter=realcreate(path);seen['meter']=meter;self.assertIs(type(meter),Meter472);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def qualify(_root,meter,*args):self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35)
   def h13(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(meter.qualification_passed);self.assertIsNotNone(meter.active);self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1137,35));meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41);return dict(passed=True,cohorts=[])
   def native(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNone(meter.active);self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1353,41));self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0));self.assertFalse(Path(p['ledger_path']).exists());return [dict(completed=True,arm='Projected4ReferenceCommonPulse')]
   stack.enter_context(patch.object(r,'qualify',side_effect=qualify));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));h13mock=stack.enter_context(patch.object(r,'root_h13',side_effect=h13));nativemock=stack.enter_context(patch.object(r,'actual472',side_effect=native));timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);h13mock.assert_called_once();nativemock.assert_called_once();result=read(d/'result.json');self.assertEqual(result['status'],'NATIVE_P4_TRANSFER_COMPLETE');self.assertIsNone(result['error']);self.assertFalse(Path(p['ledger_path']).exists());self.assertEqual(sha(p['budget_before_path']),p['budget_before_sha256'])
   for kind,seconds in [call.args for call in timers.call_args_list if call.args[1]>0]:self.assertLessEqual(seconds,900 if kind==r.signal.ITIMER_PROF else 1200)
   for guard in forbidden:guard.assert_not_called()
  self.assertEqual(random.getstate(),py);current=np.random.get_state();self.assertEqual(current[0],npr[0]);np.testing.assert_array_equal(current[1],npr[1]);self.assertEqual(current[2:],npr[2:])

 def test_budget_journal_is_charged_before_fake_native_attempt_and_caps_never_refund(self):
  from retry.meter472 import Meter472
  from retry.budget472 import ARM
  with tempfile.TemporaryDirectory() as td,patch('retry.meter472.signal.setitimer'):
   d,p=self.fixture_plan(Path(td));meter=Meter472(d);meter.begin_actual()
   try:
    meter.charge('reset',ARM);meter.charge('action',ARM);self.assertEqual(read(p['ledger_path'])['research_remaining'],26345);self.assertEqual(read(Path(p['native_directory'])/'charge472-0002-private.json')['status'],'CHARGED_BEFORE_CALL_CONSERVATIVE_NO_REFUND')
    with self.assertRaisesRegex(RuntimeError,'synthetic-call-failed'):raise RuntimeError('synthetic-call-failed')
    self.assertEqual(read(p['ledger_path'])['research_remaining'],26345);meter.nb['actions']=195
    with self.assertRaises(ResourceStop):meter.charge('action',ARM)
    with self.assertRaises(ResourceStop):meter.charge('reset',ARM)
   finally:meter.end_actual()
   with patch.object(meter,'guard'):
    meter.active=(0.,0.);meter.b['reserved_ticks']=8738
    with self.assertRaises(ResourceStop):meter.step(object(),[],'scope')
    meter.b['worlds']=181
    with self.assertRaises(ResourceStop):meter.world({},'scope')

 def test_native_profile_injected_only_after125_prefix_and_only_one_native_arm(self):
  from retry.native472 import actual472
  tree=ast.parse(inspect.getsource(actual472));loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step');self.assertEqual(ast.unparse(loop.iter),'range(1, 196)')
  root=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=='step == 126');self.assertIn('ctrl.policy.nodes = projected_nodes.copy()',ast.unparse(root))
  prefix=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=='step <= 125');self.assertNotIn('query.query_policy',ast.unparse(ast.Module(body=prefix.body,type_ignores=[])));self.assertIn('step - 125',ast.unparse(ast.Module(body=prefix.orelse,type_ignores=[])))
  arm=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='arm');self.assertEqual(ast.unparse(arm.iter),'[PROJECTED]')
 def run_real_pair(self,q,h,b,n,decision):
  """Real query + pair + P4 driver, synthetic ticks/rows, never a solver."""
  from retry import query472 as module
  from retry.fixture438 import stored_env
  from retry.actual437_boundary import live_proxy
  from retry.paired417_common import SourceC
  from retry.terminal410_model import snapshot
  from retry.fork394_run import complete_state
  from retry.test_parent436 import synthetic_guard
  from retry.parent436 import decode,legacy_digest
  from retry.planner419_model_ledger import ForecastLedger
  from retry.loss389_analyze import save
  created=[];full=complete_state(h.env,h.obs,h.ctrl.memory())
  class FakeGuardian:
   def __init__(self,meter,state,memory,ledger,fixed,pace,label,recipe,tag,confirmation_phase=None):
    self.label=label;self.recipe=recipe;self.closed=False;self.error=None;self.status='ACTIVE';self.rows=[];self.initial_count=0;self.tail_count=0;self.guardian_certificate=None;self.root_ledger=ledger;self.root_state_digest=legacy_digest(state);self.root_memory_digest=legacy_digest(memory)
    childfull=copy.deepcopy(full);childfull['physical']=copy.deepcopy(state['physical']);childfull['wrapper'].update(finish_tracker=copy.deepcopy(state['finish_tracker']),elapsed_raw_steps=state['elapsed_raw_steps']);self.m=live_proxy(stored_env(childfull));self.ctrl=SourceC(fixed,pace,copy.deepcopy(memory));self.ledger=SimpleNamespace(progress_qualified=lambda:True,deadline_missed=False)
    pending=q.active_pending
    if pending:
     proof=synthetic_guard(pending);self.synthetic=proof;self.stream=SimpleNamespace(child_id=label,require_owner=lambda child:None,root_rng=dict(digest=proof.root_RNG_digest),authority=pending.authority,posts=decode(proof.posts_bytes))
    created.append(self)
   def one(self,tag,**kw):
    row=dict(command=kw['first_override'].tolist(),memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(self.ctrl.memory()),safety=[])
    if q.active_pending:
     proof=self.synthetic;row.update(decode(proof.rows_bytes)[0]);row.update(command=kw['first_override'].tolist(),memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(self.ctrl.memory()));self.guardian_certificate=decode(proof.certificate_bytes);self.status='FINISHED'
     state=decode(proof.final_snapshot_bytes) if hasattr(proof,'final_snapshot_bytes') else decode(proof.snapshot_bytes)
     childfull=copy.deepcopy(full);childfull['physical']=state['physical'];childfull['wrapper'].update(finish_tracker=state['finish_tracker'],elapsed_raw_steps=state['elapsed_raw_steps']);self.m=live_proxy(stored_env(childfull))
    else:self.m.t+=.08
    self.rows.append(row)
   def _end_vector(self):return None
   def signature(self):return copy.deepcopy(self.rows)
   def dump(self,d):save(Path(d)/(self.label+'-private.json'),dict(rows=self.rows,status=self.status))
   def close(self):self.closed=True
  with patch.object(module,'GuardianChild',side_effect=FakeGuardian),patch.object(q,'validate_child'):
   first,record,pending=q.query_policy(h,b,n,module.PROJECTED,decision)
  self.assertEqual(len(created),2);self.assertTrue(all(c.closed for c in created));self.assertTrue(record['pair_independent_repeat_exact']);self.assertTrue(record['all_future_actions_use_P4']);self.assertFalse(h.ledger.done)
  for child in created:self.assertFalse(child.ctrl.policy.nodes.flags.writeable);np.testing.assert_array_equal(child.ctrl.policy.nodes,q.nodes)
  return first,record,pending,created

 def test_real_first_current_pair_executes13_P4_boundaries_twice_without_old_future(self):
  with current472() as(q,h,b,n):
   first,record,pending,children=self.run_real_pair(q,h,b,n,1);self.assertIsNone(pending);self.assertEqual([len(c.rows) for c in children],[13,13]);self.assertEqual(record['pair_observed_actions'],13)

 def test_real_pending_pair_uses_ownP4_FINISH_CONFIRM_and_validates_two_guardian_proofs(self):
  with pending472() as(q,h,b,n):
   first,record,pending,children=self.run_real_pair(q,h,b,n,2);self.assertIsNotNone(pending);self.assertEqual(record['route'],'REGISTERED_PENDING_GUARDIAN_ONLY');self.assertEqual(record['phase'],'FINISH_CONFIRM');self.assertEqual([len(c.rows) for c in children],[1,1]);self.assertEqual(len(list(q.d.glob('*-pending-policy-proof-private.json'))),2);self.assertFalse(record['model_authorizes_actual_DONE'])
 def test_all_current_independent_pairs_costed_with_no_auxiliary_fixture_world(self):
  self.assertEqual((1458+70*2*13*4,41+70*2),(8738,181));self.assertLessEqual(8738,9216);self.assertLessEqual(181,185)
  self.assertEqual((125+70,1),(195,1))

 def test_own_FINISH_CONFIRM_reference_is_not_legacy_nominal_future(self):
  from retry.signed417_executor import CoherentExecutor
  fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,speed=[0.,20.,30.,20.,20.]),model=dict(rear_traction_accel=100.,brake_accel=100.,effective_mass=10.))
  finish=dict(finish_time_s=None,candidate_crossing_time_s=1.9,qualified_time_s=1.9,crossing_from_back=True,center=[0.,0.],forward=[1.,0.],half_width=4.,half_depth=1.)
  state=dict(pos=[.5,0.],vel=[10.,0.],speed=10.,time=2.);out=[]
  for nodes in ([0.,20.,30.,20.,20.],[0.,18.,24.,18.,9.]):
   ctrl=CoherentExecutor(fixed);ctrl.nodes=np.asarray(nodes);ctrl.nodes.setflags(write=False);ctrl.phase='FINISH_CONFIRM'
   command,detail=ctrl.act(state,np.asarray([.2,.5,0],np.float32),finish);self.assertEqual(detail['r'],nodes[-1]);self.assertEqual(ctrl.phase,'FINISH_CONFIRM');out.append(command)
  self.assertFalse(np.array_equal(*out));self.assertGreater(out[1][2],0.)

 def test_native_fact_precedes_forecast_comparison_and_phantom_DONE_is_blocked(self):
  from retry.test_native442 import bind_case
  from retry.step442 import suffix_step
  with tempfile.TemporaryDirectory() as td:
   native,history,frame,row,trace,charges=bind_case(td,'pending')
   try:
    self.assertTrue(frame['predicted']['finished']);self.assertFalse(native.ledger.done);self.assertEqual(native.env.recorded_steps,0)
    events=[];dispatch=native.dispatch;commit=native.commit_native_observation;verify=native.verify_forecast
    def dispatched(*args,**kw):events.append('dispatch');return dispatch(*args,**kw)
    def committed():
     events.append('own_fact');return commit()
    def compared(forecast):
     events.append('compare');self.assertTrue(native.ledger.done);self.assertEqual(len(native.rows),1);self.assertTrue(read(Path(td)/(native.label()+'-actual-fact-private.json'))['forecast_not_read']);return verify(forecast)
    with patch.object(native,'dispatch',side_effect=dispatched),patch.object(native,'commit_native_observation',side_effect=committed),patch.object(native,'verify_forecast',side_effect=compared):suffix_step(native,history,frame,trace)
    self.assertEqual(events,['dispatch','own_fact','compare']);self.assertEqual(charges,[0]);self.assertEqual(native.env.recorded_steps,1)
   finally:native.close_log()

 def test_current_native_context_binds_P4_source_nodes_clock_memory_and_readback(self):
  from retry.query472 import PROJECTED
  from retry.receipt421_io import load_receipt
  from retry.planner419 import GoalLedger
  with current472() as(q,h,b,n):
   original=h.ledger.digest();calls=[];frame=dict(command=np.asarray(n,np.float32).tolist(),memory_before=b,memory_after=h.ctrl.memory())
   def pair(parent,ctx,before,label,force):
    calls.append(force);self.assertIs(type(ctx.ledger),GoalLedger);self.assertEqual(ctx.ledger,h.ledger);self.assertEqual(ctx.parent.raw_clock_tick,h.ledger.last_clock_tick);self.assertEqual(ctx.parent.fork_inputs()[1],b);self.assertEqual(ctx.policy_digest,q.policy_digest);self.assertFalse(parent.ctrl.policy.nodes.flags.writeable);np.testing.assert_array_equal(parent.ctrl.policy.nodes,q.nodes)
    return dict(valid=True,first=frame,certificate=None,status='ACTIVE',observed_actions=13,independent_repeat_exact=True,all_future_actions_use_P4=True)
   with patch.object(q,'p4_pair',side_effect=pair):first,record,pending=q.query_policy(h,b,n,PROJECTED,1)
   self.assertEqual(calls,[True]);self.assertEqual(first,frame);self.assertIsNone(pending);self.assertEqual(h.ledger.digest(),original);self.assertFalse(record['model_authorizes_actual_DONE']);self.assertTrue(record['all_future_actions_use_P4'])
   receipt=load_receipt(q.d/(PROJECTED+'_decision1-before-actual-dispatch-private.json'));self.assertEqual(receipt['record']['nodes_digest'],q.nodes_digest);self.assertEqual(receipt['context']['policy_digest'],q.policy_digest);self.assertFalse(receipt['record']['planner_ranking_receipt'])

 def test_wrong_nodes_or_forecast_authority_stop_before_current_pair(self):
  from retry.query472 import PROJECTED
  from retry.planner419_model_ledger import ForecastLedger
  for failure in ('nodes','ledger','policy'):
   with current472() as(q,h,b,n):
    if failure=='nodes':h.ctrl.policy.nodes=q.nodes.copy()
    elif failure=='ledger':h.ledger=ForecastLedger.fork(h.ledger)
    else:q.policy_digest='forged'
    with patch.object(q,'p4_pair') as pair:
     with self.assertRaises(Exception):q.query_policy(h,b,n,PROJECTED,1)
     pair.assert_not_called()

 def test_global126_override_once_pending_and_horizon_modes(self):
  from retry.query472 import mode472,PROJECTED
  self.assertEqual(mode472(PROJECTED,1,'FIRST_LAP',False),('P4_CURRENT',True))
  for decision in range(2,71):
   self.assertEqual(mode472(PROJECTED,decision,'FIRST_LAP',False),('P4_CURRENT',False));self.assertEqual(mode472(PROJECTED,decision,'FINISH_CONFIRM',True),('P4_REGISTERED_PENDING',False))
  for decision in (0,71,82):
   with self.assertRaises(Exception):mode472(PROJECTED,decision,'FIRST_LAP',False)
  with self.assertRaises(Exception):mode472(PROJECTED,1,'FINISH_CONFIRM',True)

 def test_every_shadow_action_uses_P4_prepared_nominal_once_and_rejects_old_nodes(self):
  from retry.query472 import p4_one472,inject_p4_nodes472
  from retry.pilot420_backend import fingerprint
  memory=dict(C=dict(phase='FIRST_LAP'),calls=0);nodes=np.asarray([0.,9.]);ctrl=SimpleNamespace(policy=SimpleNamespace(nodes=np.asarray([0.,20.])),memory=lambda:copy.deepcopy(memory),phase=lambda:memory['C']['phase'])
  digest=inject_p4_nodes472(ctrl,nodes);nominals=[np.asarray([.2,1.,0.],np.float32),np.asarray([.2,0.,.1],np.float32)]
  def act(model):
   command=nominals[memory['calls']];memory['calls']+=1
   if memory['calls']==2:memory['C']['phase']='FINISH_CONFIRM'
   return command
  ctrl.act=Mock(side_effect=act);child=SimpleNamespace(ctrl=ctrl,m=object(),rows=[],status='ACTIVE')
  def one(tag,**kw):child.rows.append(dict(command=kw['first_override'].tolist(),memory_before=kw['prepared_before'],memory_after=copy.deepcopy(memory)))
  child.one=Mock(side_effect=one)
  p4_one472(child,nodes,digest,True,'first');p4_one472(child,nodes,digest,False,'pending')
  self.assertEqual(ctrl.act.call_count,2);self.assertEqual(memory['calls'],2)
  for index,call in enumerate(child.one.call_args_list):self.assertIs(call.kwargs['prepared_nominal'],nominals[index]);self.assertEqual(call.kwargs['prepared_before']['calls'],index);np.testing.assert_array_equal(call.kwargs['first_override'],nominals[index])
  ctrl.policy.nodes=np.asarray([0.,20.]);ctrl.policy.nodes.setflags(write=False)
  with self.assertRaises(Exception):p4_one472(child,nodes,digest,False,'old-nominal-future')
  self.assertEqual(ctrl.act.call_count,2)
