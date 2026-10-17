"""Post-stop representation counterexample using saved state; zero new worlds."""
import copy,json,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from retry.terminal410_model import snapshot,from_actual_full
from retry.pedal331_run import plain
from retry.loss389_analyze import read,save,sha

def run(root):
 d=root/'stage437';assert read(d/'result.json')['status']=='ACTUAL_PAIR_CENSORED_STOP';assert not(d/'snapshot-diagnosis.json').exists();cpu=time.process_time();wall=time.perf_counter();full=read(d/'actual_C0/final-private.json');expected=from_actual_full(full);tracker=copy.deepcopy(expected['finish_tracker'])
 # Actual racing constructor uses tuples, update never changes these fields.
 # complete_state serializes them through plain() to JSON lists. Reproduce that
 # exact representation distinction, without restoring or stepping any world.
 tracker['center']=tuple(tracker['center']);tracker['forward']=tuple(tracker['forward']);proxy=SimpleNamespace(car=None,world=None,roads=None,obstacles=None,track=None,tile_visited_count=None,t=expected['physical']['actual_time'],damage=None,off_track_counter=None,finish_line_tracker=SimpleNamespace(**tracker),elapsed_raw_steps=expected['elapsed_raw_steps'])
 with patch('retry.terminal410_model.capture',return_value=copy.deepcopy(expected['physical'])) as capture:
  raw=snapshot(proxy)
 assert capture.call_count==1 and raw!=expected and plain(raw)==expected
 keys=[k for k in raw['finish_tracker'] if raw['finish_tracker'][k]!=expected['finish_tracker'][k]];assert keys==['center','forward']
 altered=copy.deepcopy(raw);altered['physical']['hull']['position'][0]+=.001;assert plain(altered)!=expected
 q=dict(stage=437,diagnosis='RAW_TUPLE_VS_PLAIN_JSON_LIST_COMPARISON',snapshot_direct_runtime_value_saved=False,source_guaranteed_type_distinction_fields=['finish_tracker.center','finish_tracker.forward'],saved_state_counterexample_raw_equality=False,canonical_plain_equality=True,physical_change_after_canonicalization_still_rejected=True,new_model_ticks=0,new_worlds=0,new_actual_actions=0,new_resets=0,source_unchanged_since_model_start=True,fix_applied=False,actual_retry=False,scope='Source-backed pure representation counterexample using saved actual state and mocked physical capture; not a fresh runtime proxy capture or actual/model fidelity certification. Other unrecorded proxy differences not excluded.',inputs={str(d/'actual_C0/final-private.json'):sha(d/'actual_C0/final-private.json')},diagnostic_source_sha256=sha(Path(__file__)),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'snapshot-diagnosis.json',q);print(json.dumps({k:q[k] for k in ['diagnosis','canonical_plain_equality','physical_change_after_canonicalization_still_rejected','new_worlds','actual_retry','CPU_s']}))
if __name__=='__main__':run(Path(sys.argv[1]))
