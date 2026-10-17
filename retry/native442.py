"""Durable442 binding of NativeAuthority439; no model argument to fact commit."""
import copy,pickle
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.authority439 import NativeAuthority439
from retry.ledger439 import require
from retry.canonical438 import require_equal,compare
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.receipt421_io import save_receipt,load_receipt
from retry.loss389_analyze import sha
from retry.paired417_common import shapecheck

class Native442(NativeAuthority439):
 def __init__(self,*args,obs,directory,arm,**kwargs):
  super().__init__(*args,**kwargs);self.obs=obs;self.directory=Path(directory);self.arm=arm;self.global_step=0;self.nominal=None;self.last_bundle=None;self.trace_file=(self.directory/'trace-private.jsonl').open('x');self.verified=0
 def label(self):return self.arm+'_step'+str(self.global_step)
 def prepare_step(self,step):
  root=super().prepare_before_nominal();self.global_step=step;self.nominal=None;full=complete_state(self.env,self.obs,self.ctrl.memory());self.prepared['full_native_pre']=copy.deepcopy(full);return root
 def bind_nominal(self,nominal):
  require(self.prepared is not None and self.nominal is None,'ONE_ACTUAL_NOMINAL_PREPARE');self.nominal=np.asarray(nominal,np.float32).tolist();self.prepared['nominal_actual']=copy.deepcopy(self.nominal)
 def _dispatch_checked(self,command,trace):
  require(self.nominal is not None and not self.awaiting_verification,'ACTUAL_NOMINAL_OR_VERIFICATION_NOT_READY');before=self.prepared['full_native_pre'];now=complete_state(self.env,self.obs,self.ctrl.memory());select=lambda x:{k:v for k,v in x.items() if k!='controller'};require_equal(select(before),select(now),self.directory,self.label()+'_pre_dispatch')
  prepath=self.directory/(self.label()+'-before-native-private.json');save_receipt(prepath,dict(full_pre_before_nominal=before,full_pre_after_nominal=now,actual_ledger_before=asdict(self.ledger),command=np.asarray(command,np.float32).tolist(),prepared_nominal=self.nominal,actual_calls_in_this_env_before=self.dispatcher.calls,authority='EXPLICIT442_CHARGE_THEN_OWN_NATIVE_STEP',forecast_is_not_fact_input=True))
  out=super()._dispatch_checked(command,trace);self.obs=out[0];ticket=self.ticket;full=complete_state(self.env,self.obs,self.ctrl.memory());raw=len(ticket.posts);clock_ok=full['wrapper']['elapsed_raw_steps']-before['wrapper']['elapsed_raw_steps']==raw and round((full['physical']['actual_time']-before['physical']['actual_time'])*50)==raw;self.last_bundle=dict(native_sequence=ticket.number,step=self.global_step,full_pre=copy.deepcopy(before),full_post=full,posts=copy.deepcopy(ticket.posts),nominal=self.nominal,ledger_before=asdict(self.ledger),native_out_flags=dict(ended=bool(out[2]),truncated=bool(out[3])),pre_proof_sha256=sha(prepath))
  save_receipt(self.directory/(self.label()+'-after-native-private.json'),dict(**self.last_bundle,ticket_success=ticket.success,command=ticket.command,memory_after_nominal=ticket.nominal_memory,tires=ticket.native_tires,raw_hull=ticket.native_hulls,actual_ledger_not_yet_committed=True,native_full_clock_verified=clock_ok));require(clock_ok,'NATIVE_FULL_CLOCK_ELAPSED');return out
 def observed_row(self):
  row,candidate=super().observed_row();row.update(step=self.global_step,nominal=copy.deepcopy(self.nominal),deadline_before=self.global_step-1+13-self.ledger.age_actions);return row,candidate
 def commit_native_observation(self):
  fact=super().commit_native_observation();row=self.rows[-1];save_receipt(self.directory/(self.label()+'-actual-fact-private.json'),dict(fact=fact,row=row,ledger_before=self.last_bundle['ledger_before'],full_native_post_sha256=sha(self.directory/(self.label()+'-after-native-private.json')),forecast_not_read=True));import json;self.trace_file.write(json.dumps(row,allow_nan=False)+'\n');self.trace_file.flush();return fact
 def verify_forecast(self,frame):
  try:
   report=super().verify_forecast(frame);self.verified+=1;save_receipt(self.directory/(self.label()+'-verification-private.json'),dict(passed=True,report=report,actual_fact_retained=True));return report
  except BaseException as e:
   row=self.rows[-1] if self.rows else None;save_receipt(self.directory/(self.label()+'-forecast-mismatch-private.json'),dict(model_original_pickle=pickle.dumps(frame,protocol=5),native_original_pickle=pickle.dumps(row,protocol=5),ledger_fact_original_pickle=pickle.dumps(asdict(self.ledger),protocol=5),canonical_field_diff=compare(dict(progress=frame.get('model_progress'),goal=frame.get('model_goal'),age=frame.get('model_age'),clock=self.last_bundle['ledger_before']['last_clock_tick']+frame['predicted']['raw_ticks'],done=frame['predicted']['finished'],position=frame['predicted']['position'],memory_before=frame['memory_before'],memory_after=frame['memory_after']),dict(progress=self.ledger.progress_m,goal=self.ledger.goal_m,age=self.ledger.age_actions,clock=self.ledger.last_clock_tick,done=self.ledger.done,position=row['post']['pos'],memory_before=row['memory_before'],memory_after=row['nominal_memory_after'])),error=type(e).__name__+': '+str(e),authority_halted=self.halted,actual_fact_retained=True));raise
 def verify_prefix(self,reference,source_frame):
  try:
   require(self.awaiting_verification and not self.halted,'PREFIX_NATIVE_FACT_REQUIRED');row=self.rows[-1];keys=['pre','post','nominal','command','memory_before','nominal_memory_after','raw_ticks','raw_tire_samples','raw_hull','collision','damage','completed','finish_time_s','ended','truncated','progress_before','progress_after','goal_before','deadline_before','goal_hit_actual_step'];require_equal({k:row[k] for k in keys},{k:reference[k] for k in keys},self.directory,self.label()+'_prefix');fidelity=shapecheck(source_frame,row);require(fidelity['passed'] and fidelity['wheel']['clipped_flag_mismatches']==0 and not row['safety'] and not self.ledger.deadline_missed,'PREFIX_UNCHANGED_FIDELITY_OR_SAFETY');self.last_verification=dict(passed=True,scope='EXACT_STORED_ACTUAL_PREFIX_AND_EXISTING_SOURCE_PHYSICS_ONLY');self.awaiting_verification=False;self._observation_record=None;self.verified+=1;save_receipt(self.directory/(self.label()+'-prefix-verification-private.json'),dict(passed=True,fidelity=fidelity,actual_fact_retained=True,no_new_model_query=True));return fidelity
  except BaseException as e:self.halted=True;self.failure=type(e).__name__+': '+str(e);raise
 def close_log(self):
  if not self.trace_file.closed:self.trace_file.close()
