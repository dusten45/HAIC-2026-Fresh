"""432 caps plus private pre-constructor and pre-integration receipts."""
import copy,random,pickle,time
from dataclasses import asdict
from retry.pilot428_meter import Meter as PreviousMeter
from retry.pilot420_backend import snapshot,rnghash,TechnicalStop
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.loss389_analyze import sha

class Meter(PreviousMeter):
 def __init__(self,d):
  super().__init__(d);self.inputs=None;self.auth={};self.sequence=0;self.active_step=False;self.qualification_passed=False
 def capture_inputs(self,state,memory,ledger,label,context=None,gate=None):
  import numpy as np
  payload=dict(label=label,state=copy.deepcopy(state),memory=copy.deepcopy(memory),ledger=asdict(ledger),global_RNG_pickle=pickle.dumps((random.getstate(),np.random.get_state())),RNG_digest=rnghash(),context=None if context is None else asdict(context),gate=gate,qualification_passed=self.qualification_passed,qualification_scope='Saved423/427 physical calibration only. New model states not actual-qualified.',actual_execution_allowed=False)
  path=self.d/(label+'-before-integration-private.json');h=save_receipt(path,payload)
  if receipt_digest(load_receipt(path))!=h:raise TechnicalStop('before_integration_receipt_roundtrip')
  self.inputs=dict(path=str(path),sha256=sha(path),receipt_digest=h,RNG_digest=rnghash(),label=label)
  return copy.deepcopy(self.inputs)
 def world(self,state,tag):
  if self.inputs is None:raise TechnicalStop('missing_preconstructor_input_proof')
  self.sequence+=1;number=self.sequence
  proof=dict(sequence=number,tag=tag,input_proof=self.inputs,state=copy.deepcopy(state),global_RNG_digest=rnghash(),restore_gate='NOT_YET_CONSTRUCTED',new_actual_actions=0)
  path=self.d/('world'+str(number)+'-before-constructor-private.json');save_receipt(path,proof)
  m=super().world(state,tag)
  if rnghash()!=proof['global_RNG_digest']:raise TechnicalStop('world_constructor_global_RNG_mutation')
  gates=dict(bodies=m.initial_bodies_exact,tiles=m.initial_tiles_exact,progress=m.initial_progress_exact,finish=m.initial_finish_exact)
  if not all(gates.values()):raise TechnicalStop('world_restore_gate')
  self.auth[id(m)]=dict(number=number,input_proof=self.inputs,constructor_proof_sha256=sha(path),restore_gates=gates,first_step=False)
  return m
 def step(self,m,act,tag):
  if self.active_step:raise TechnicalStop('concurrent_integration_forbidden')
  if id(m) not in self.auth:raise TechnicalStop('unregistered_model_world')
  auth=self.auth[id(m)]
  # Complete restore snapshot and gate record is durably written before this
  # world's first integration. Query context/root/RNG were already sealed.
  if not auth['first_step']:
   save_receipt(self.d/('world'+str(auth['number'])+'-before-first-step-private.json'),dict(**auth,model_root=snapshot(m),global_RNG_digest=rnghash(),first_command=[float(x) for x in act],tag=tag,qualification_passed=self.qualification_passed,actual_execution_allowed=False))
   auth['first_step']=True
  before=rnghash();self.active_step=True
  try:return super().step(m,act,tag)
  finally:
   self.active_step=False
   if rnghash()!=before:raise TechnicalStop('integration_global_RNG_mutation')
