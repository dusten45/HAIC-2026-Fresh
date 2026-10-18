"""Complete ONLY never-executed candidate arm;550 baseline/test failure preserved.

Same frozen boundary/criteria, precharge entire earlier cost against same total cap.
"""
import datetime,hashlib,json,signal,time,traceback
from pathlib import Path
import retry.yaw550_continuation as original
from retry.yaw550_continuation import G,D,policy,bounds,boundary_index

class Completion(original.Stage):
 def __init__(self):
  self.phase='candidate-completion';self.cpu=time.process_time();self.wall=time.perf_counter();self.c=json.loads((G/'retry/yaw550_contract.json').read_text());self.prior=json.loads((G/'retry/yaw550_continuation_result.json').read_text());self.completion_contract=json.loads((G/'retry/yaw550_completion_contract.json').read_text());assert len(self.prior['cases'])==1 and self.prior['cases'][0]['arm']=='baseline' and not self.prior['passed'];assert not (D/'candidate-continuation-private.json').exists() and not (D/'candidate-interrupted-private.json').exists();self.counter=[self.prior['model_ticks']];self.cost=self.prior['cost'].copy();self.outcomes=self.prior['cases'].copy();self.current=None;self.safety_state=None;self.arm='candidate';self.probe_gate=None;self.cpu_precharged=self.prior['CPU_s'];self.wall_precharged=self.prior['wall_s'];lim=self.c['caps'];self.tick_cap=lim['model_ticks'];self.force_cap=lim['force'];self.cpu_cap=lim['CPU_s'];self.wall_cap=lim['wall_s']
  for p,h in {**self.c['source_sha256'],**self.completion_contract['source_sha256']}.items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
  for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
  self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads((D/'frozen-paths-private.json').read_text());self.inputs=json.loads((D/'continuation-input-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.geometry=policy.geometry_context(self.static,lim['geometry']);self.save(D/'candidate-completion-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/yaw550_completion_contract.json').read_bytes()).hexdigest(),precharged_model_ticks=self.counter[0],precharged_CPU_s=self.cpu_precharged))
 def guard(self,reserve=0):
  super().guard(reserve)
  if self.cpu_precharged+time.process_time()-self.cpu>=self.cpu_cap or self.wall_precharged+time.perf_counter()-self.wall>=self.wall_cap:raise RuntimeError('COMBINED550_COST_CAP')
 def run(self):
  from core.vendor.car_racing import CarRacing
  def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_550')
  CarRacing.__init__=CarRacing.reset=CarRacing.step=poison;policy.tick=self.checked_tick
  def interrupt(*a):raise RuntimeError('COMBINED550_TIMER_CAP')
  signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,self.cpu_cap-self.cpu_precharged);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,self.wall_cap-self.wall_precharged);out={}
  try:
   candidate=self.one_arm('candidate',self.paths['candidate']);both=len(self.outcomes)==2 and all(x['crossing'] is not None and x['first_failure'] is None for x in self.outcomes);gain=self.outcomes[0]['crossing']['lower_s']-candidate['crossing']['upper_s'] if both else None;interp=self.outcomes[0]['crossing']['time_s']-candidate['crossing']['time_s'] if both else None;out=dict(passed=False,original550_future_witness_gate_failed=True,original549_gate_passed=False,both_arms_raw_safe_to_next_boundary=both,registered_future_witness_gate_passed=all(x['fresh12hold_witness_passed'] for x in self.outcomes),conservative_gain_from549_entry_s=gain,interpolated_gain_from549_entry_s=interp,sustained_time_gain_observed=bool(both and gain>=.02-1e-12),whole_lap_or_native_promotion=False,new_native_actions=0,new_resets=0,replayed_saved549_ticks=0)
  except BaseException as exc:
   out=dict(passed=False,technical_error=type(exc).__name__+':'+str(exc),new_native_actions=0,new_resets=0);self.save(D/'candidate-completion-error-private.json',dict(error=out['technical_error'],traceback=traceback.format_exc(),cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint();out.update(cases=self.outcomes,cost=self.cost,model_ticks=self.counter[0],new_candidate_model_ticks=self.counter[0]-self.prior['model_ticks'],integrator_wheel_force_evaluations=4*self.counter[0],CPU_s=self.cpu_precharged+time.process_time()-self.cpu,wall_s=self.wall_precharged+time.perf_counter()-self.wall,research_remaining=22758,reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0);self.save(G/'retry/yaw550_completion_result.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':Completion().run()
