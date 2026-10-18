"""Full498 preparation poison and saved-only own-path fixtures."""
import ast,copy,types
from contextlib import contextmanager,ExitStack
from pathlib import Path
from unittest.mock import patch

@contextmanager
def preparation_poison(Graph):
 """Cover imports, setup, source/receipt gates and pure fixtures; never integrate."""
 import Box2D
 from core.vendor.car_racing import CarRacing
 from core.vendor.car_dynamics import Car
 hits=[];classes=set();original_world=Box2D.b2World;original_exec=Graph.exec_module
 def forbidden(*a,**k):hits.append('physics');raise AssertionError('498_PREFLIGHT_PHYSICS_FORBIDDEN')
 with ExitStack() as stack:
  stack.enter_context(patch.object(Box2D,'b2World',forbidden))
  def guard_class(cls):
   if cls in classes:return
   classes.add(cls)
   for name in ('__init__','reset','step'):
    if hasattr(cls,name):stack.enter_context(patch.object(cls,name,forbidden))
  guard_class(CarRacing);guard_class(Car)
  def guarded_exec(graph,module):
   original_exec(graph,module)
   for name,value in list(vars(module).items()):
    if isinstance(value,type) and name in ('TerminalVehicleTransition','SourceVehicleTransition'):guard_class(value)
    if name=='make_env':stack.enter_context(patch.object(module,name,forbidden))
  stack.enter_context(patch.object(Graph,'exec_module',guarded_exec))
  try:yield hits
  finally:
   # Imports may bind the temporarily poisoned world symbol by value. Restore
   # only that exact symbol; no controller or physics logic is rewritten.
   import sys
   for name,module in list(sys.modules.items()):
    if name.startswith('retry492.') and module is not None:
     for key,value in list(vars(module).items()):
      if value is forbidden and key!='make_env':setattr(module,key,original_world)

def compiled_reference(module_name,qualname):
 """Compile the WHOLE frozen module, preserving Python import optimization.

 No module body is executed. Use the sanctioned namespace-only AST transform
 for cloned sources; select nested code by its original qualified function name.
 """
 from retry.runtime492 import Rewrite
 root=Path(__file__).resolve().parent
 tree=Rewrite().visit(ast.parse((root/(module_name+'.py')).read_text()));ast.fix_missing_locations(tree)
 compiled=compile(tree,'498-full-module-reference-'+module_name,'exec')
 def walk(code):
  yield code
  for value in code.co_consts:
   if isinstance(value,types.CodeType):yield from walk(value)
 matches=[code for code in walk(compiled) if code.co_qualname==qualname]
 if len(matches)!=1:raise AssertionError('498_UNIQUE_REFERENCE:'+qualname)
 return matches[0]

def reference_functions(runtime):
 controller=runtime.import_module('terminal410_run');paired=runtime.import_module('paired417_common');refs={}
 for name in ('__init__','act','memory','phase'):
  code=compiled_reference('terminal410_run','Controller.'+name);refs['Controller.'+name]=types.FunctionType(code,dict(vars(controller)),name)
 code=compiled_reference('paired417_common','SourceC.__init__')
 def cell(value):
  def f():return value
  return f.__closure__[0]
 refs['SourceC.__init__']=types.FunctionType(code,dict(vars(paired)),'__init__',None,(cell(paired.SourceC),))
 return refs

def saved_own_fixture(runtime,mods,checked,model_dir,history,project):
 """Exercise new own validator on original saved nominal prefix, no new world."""
 from retry.history498 import authenticate_own
 from dataclasses import asdict
 from types import SimpleNamespace as NS
 contexts=[checked(model_dir/f'context-{i:03d}-private.json') for i in (1,2,3,4)]
 parent=checked(model_dir/'D495-A_control_1-private.json');obs=parent['observer_records495']['observer-private'];root=contexts[0];policy='a'*64;transitions=[]
 for i in range(3):
  a,b=contexts[i:i+2];row=parent['rows'][i]
  transitions.append(dict(index=i+1,policy_digest=policy,state_before=a['state'],memory_before=a['before'],ledger_before=a['ledger'],state_after=b['state'],memory_after=b['before'],ledger_after=b['ledger'],row_digest=mods['io481'].canonical(row),RNG_digest=a['RNG']['digest']))
 stream=NS(root_memory=root['before'],root_ledger=root['ledger'],root_state=root['state'],root_rng=root['RNG'],actions=obs['actions'][:3],posts=obs['posts'][:12])
 fake=NS(rows=parent['rows'][:3],stream=stream,capture_holds495=parent['direct_holds495'][:3],L=float(sum(runtime.fixed['free_profile']['ds'])),line=runtime.fixed['line'],ctrl=NS(memory=lambda:contexts[3]['before']),ledger=mods['planner419_model_ledger'].ForecastLedger(**contexts[3]['ledger']),m=object())
 backend=mods['pilot420_backend'];fake_backend=NS(**vars(backend));fake_backend.snapshot=lambda _:contexts[3]['state'];fixturemods=dict(mods,pilot420_backend=fake_backend)
 proof=authenticate_own(fake,root,transitions,policy,history,project,fixturemods)
 checks=[]
 for name,mutate in [('ledger',lambda t:t[0]['ledger_after'].update(age_actions=999)),('policy',lambda t:t[0].update(policy_digest='b'*64)),('row',lambda t:t[0].update(row_digest='f'*64))]:
  bad=copy.deepcopy(transitions);mutate(bad)
  try:authenticate_own(fake,root,bad,policy,history,project,fixturemods)
  except Exception:checks.append(name)
  else:raise AssertionError('498_OWN_TAMPER_ACCEPTED:'+name)
 return dict(passed=True,saved_actions=3,nominal_only_own_path=proof,negative_fixtures=checks,snapshot_dependency='explicit saved-state stub only in fake-only fixture',new_worlds=0,new_ticks=0)

def binding_gate(runtime,np_expected):
 """Independent binding anchors survive mutations made BEFORE reference build."""
 import hashlib,math
 from retry.codegate498 import verify_code,verify_function,CodeGate498Error
 from retry.projection491 import CoherentExecutor491
 from retry.signed417_executor import ExecutorDomainError
 root=Path(__file__).resolve().parent;controller=runtime.import_module('terminal410_run');paired=runtime.import_module('paired417_common');cross=runtime.import_module('cross404_common');probe=runtime.import_module('probe390_run');factorial=runtime.import_module('factorial401_run')
 original_controller=controller.Controller;original_source=paired.SourceC;original_policy=paired.policy
 anchors={'Controller.__init__':dict(control_code=probe.control_code,G=cross.G,scope_for=cross.scope_for,executor=cross.executor),'Controller.act':dict(SimpleNamespace=types.SimpleNamespace,np=np_expected,copy=copy,sensor=factorial.sensor,ExecutorDomainError=ExecutorDomainError),'Controller.memory':{},'Controller.phase':{},'SourceC.__init__':dict(Controller=original_controller,policy=original_policy)}
 if cross.G.resolve()!=root.parent.resolve():raise AssertionError('498_CONTROLLER_G_PATH')
 if original_source.__mro__[1] is not original_controller:raise AssertionError('498_SOURCE_BASE_OWNER')
 def independent(module_name,name):
  return types.FunctionType(compiled_reference(module_name,name),{},name)
 auxiliary=[]
 for actual,modname,name,expected in [(probe.control_code,'probe390_run','control_code',dict(ast=ast,Path=Path,hashlib=hashlib)),(cross.scope_for,'cross404_common','scope_for',dict(np=np_expected)),(cross.executor,'cross404_common','executor',dict(np=np_expected,CoherentExecutor=CoherentExecutor491)),(factorial.sensor,'factorial401_run','sensor',dict(math=math)),(runtime.policy_original,'paired417_common','policy',dict(np=np_expected,CoherentExecutor=CoherentExecutor491))]:
  auxiliary.append(verify_function(actual,independent(modname,name),globals_expected=expected,label='dependency.'+name))
 # The sanctioned491 wrapper is independently matched to the pinned normal
 # Graph source code and its actual original-policy/runtime closure identities.
 code=compile(ast.parse((root/'runtime492.py').read_text()),'498-graph-reference','exec')
 def descend(c):
  yield c
  for value in c.co_consts:
   if isinstance(value,types.CodeType):yield from descend(value)
 policycodes=[c for c in descend(code) if c.co_name=='policy']
 if len(policycodes)!=1:raise AssertionError('498_POLICY_WRAPPER_REFERENCE')
 auxiliary.append(verify_code(original_policy.__code__,policycodes[0],label='sanctioned491.policy_wrapper'))
 cells=dict(zip(original_policy.__code__.co_freevars,original_policy.__closure__ or ()))
 if set(cells)!={'old','self'} or cells['old'].cell_contents is not runtime.policy_original or cells['self'].cell_contents is not runtime:raise AssertionError('498_POLICY_WRAPPER_CLOSURE')
 def validate():
  references=reference_functions(runtime);proofs=[]
  for name,reference in references.items():
   owner=original_source if name.startswith('SourceC.') else original_controller;actual=getattr(owner,name.split('.')[1]);closure={'__class__':original_source} if name.startswith('SourceC.') else None
   proofs.append(verify_function(actual,reference,globals_expected=anchors[name],closure_expected=closure,label=name))
  return proofs
 proofs=validate();negative=[]
 # Mutation precedes independent reference generation, so copying the polluted
 # globals cannot accidentally make the replacement acceptable.
 for label,namespace,key,replacement in [('np',original_controller.act.__globals__,'np',object()),('copy',original_controller.act.__globals__,'copy',object()),('sensor',original_controller.act.__globals__,'sensor',object()),('policy',original_source.__init__.__globals__,'policy',lambda *a:None),('Controller',original_source.__init__.__globals__,'Controller',type('WrongController',(),{}))]:
  old=namespace[key];namespace[key]=replacement
  try:
   try:validate()
   except CodeGate498Error as exc:
    if 'global_identity:'+key not in str(exc):raise AssertionError('498_WRONG_BINDING_REJECTION:'+str(exc))
    negative.append(label)
   else:raise AssertionError('498_PRE_REFERENCE_GLOBAL_TAMPER_ACCEPTED:'+label)
  finally:namespace[key]=old
 validate()
 return dict(passed=True,functions=proofs,dependencies=auxiliary,pre_reference_global_tamper_rejected=negative,independent_standard_and_frozen_dependency_anchors=True,policy_wrapper_closure=True)
