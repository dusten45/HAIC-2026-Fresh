"""Stored-only diagnosis. No change to guardian/419 law and no model/native call."""
import json,math,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.paired417_common import policy
from retry.planner419 import TickBracket,ContractError

def event_relation(root_time,event_time):
 if not(math.isfinite(root_time) and math.isfinite(event_time)):raise ValueError('nonfinite_event')
 return 'BEFORE_ROOT' if event_time<root_time else 'AT_ROOT' if event_time==root_time else 'AFTER_ROOT'

def prepare(root):
 d=root/'stage425';assert not(d/'boundary-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'budget.json',d/'actual_P/final-private.json',d/'actual_P/result.json',d/'actual_P/trace-private.jsonl',d/'actual_P/stop-private.json',d/'actual_P/actual_P_177_nominal_1-private.json',Path(p['fixed_plan']),root/'stage404/profiles-private.json',Path(__file__).with_name('pilot420_backend.py'),Path(__file__).with_name('signed417_executor.py'),Path(__file__).with_name('planner419.py')];save(d/'boundary-plan.json',dict(scope='Purestoredrecordcomparison+existingexecutorconfirmationpredicate+strictbracketrejection; nonewmodel/nativecalls, noexecutioncodefix/retry.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']));(d/'boundary-plan.sha256').write_text(sha(d/'boundary-plan.json')+'\n')

def run(root):
 d=root/'stage425';p=read(d/'boundary-plan.json');assert not(d/'boundary-result.json').exists();cpu=time.process_time();wall=time.perf_counter()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 final=read(d/'actual_P/final-private.json');failed=read(d/'actual_P/actual_P_177_nominal_1-private.json');rr=read(d/'actual_P/result.json');last=json.loads((d/'actual_P/trace-private.jsonl').read_text().splitlines()[-1]);frame=failed['rows'][0];pred=frame['predicted'];current=float(final['physical']['actual_time']);event=float(pred['finish_time_s']);tracker=final['wrapper']['finish_tracker'];checks=[]
 def check(name,value):
  if not value:raise AssertionError(name)
  checks.append(name)
 check('actual_world_clock_unchanged_after_last_native',current==last['post']['time']==frame['raw_hull'][0]['time'])
 check('actual_official_finish_unobserved',final['wrapper']['finish_time_s'] is None and not last['completed'])
 check('actual_pending_confirmation_phase',final['controller']['C']['phase']=='FINISH_CONFIRM' and tracker['candidate_crossing_time_s']==current and tracker['crossing_from_back'])
 plan=read(d/'plan.json');ctrl=policy(read(Path(plan['fixed_plan'])),np.asarray(read(root/'stage404/profiles-private.json')['frozen268']));ctrl._confirm_valid(last['post'],tracker);checks.append('existing_confirmation_corridor_predicate_passed')
 check('model_finish_event_at_root',event_relation(current,event)=='AT_ROOT')
 check('only_model_advanced_one_raw_tick',pred['raw_ticks']==1 and pred['finished'] and abs(pred['time']-current-.02)<1e-8)
 relative=round((event-current)*50);check('strict_positive_future_guard_rejects_zero',relative==0 and rr['error']=='TechnicalStop: official_finish_not_after_root')
 try:TickBracket(relative-1,relative)
 except ContractError:checks.append('419_negative_lower_bracket_remains_rejected')
 else:raise AssertionError('changed419timecontract')
 check('actual177_not_dispatched',rr['native_actions']==rr['confirmed_rows']==176 and last['step']==176)
 check('computational_cap_not_reached',rr['native_actions']<plan['per_arm_actual_cap'] and read(d/'budget.json')['model']['ticks']<plan['model_caps']['ticks'])
 q=dict(status='STORED_BOUNDARY_DIAGNOSED_NO_RETRY',tests=len(checks),checks=checks,actual_root_time_s=current,model_event_time_s=event,model_confirmation_post_time_s=pred['time'],event_relation='AT_ROOT',model_raw_ticks_charged=1,new_actual177_dispatched=False,actual_official_finish_observed=False,diagnosis='ShortguardianforecastreusesChildstrictfuturefinishcertificate. ExistingpendingcrossingcanbeAT_ROOTwhileactualofficialfinishisNone; nextMODELconfirmationisnotanactualfinish.',execution_code_changed=False,proposal='Separateguardianconfirmationqualificationfromplannerfuturefinishranking. Preserve419strictpositivefuturegaincontract; donotturncandidate/modelcompletionintoactualDONE. Requirestoredroot/eventboundarytestsbeforeanynewintegration. Newactualexecutionnotauthorizedbythisdiagnosis.',new_model_ticks=0,new_wrapper_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'boundary-result.json',q);print(json.dumps(q))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
