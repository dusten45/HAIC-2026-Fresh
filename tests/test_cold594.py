"""World-free regression of the actual State/NumPy and fsync log boundary."""
import importlib.util,json,os,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.brake502_response import State,Wheel
from retry.cold594_logging import native_input_fields
from retry.durable568 import Journal
# Retain all four unchanged593 policy/phase/clock pure tests.
spec=importlib.util.spec_from_file_location('old593_tests',Path(__file__).with_name('test_cold593.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);PureTests=old.PureTests
class SerializationTests(unittest.TestCase):
 def state(self):return State(velocity=np.asarray([1.25,-2.5],np.float32),wheels=tuple(Wheel(np.float64(2+i),np.float32(.25),np.float64(.1),np.float64(400),np.asarray([.5,-.5],np.float32)) for i in range(4)),mass=np.float64(7.),engine_multiplier=np.float32(1.))
 def test_actual_state_nested_numpy_roundtrip(self):
  state=self.state();before=state.velocity.tobytes();record=native_input_fields(state,np.asarray([.25,.5,0],np.float32));out=json.loads(json.dumps(record,allow_nan=False));self.assertEqual(out,record);self.assertEqual(out['before_state']['wheels'][0]['offset'],[.5,-.5]);self.assertEqual(state.velocity.tobytes(),before)
 def test_reset_none_and_action_journal_roundtrip(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'journal.jsonl';j=Journal(p)
   for action in [None,np.asarray([-.25,.5,0],np.float32),np.asarray([.25,0,.5],np.float64)]:
    j.append('BEFORE_NATIVE_RAW',phase='reset' if action is None else 'action',counts={'raw_attempts':1,'raw_completed':0},**native_input_fields(self.state(),action))
   j.close();rows=[json.loads(line) for line in p.read_text().splitlines()];self.assertIsNone(rows[0]['payload']);self.assertEqual(rows[1]['payload'],[-.25,.5,0.]);self.assertEqual(rows[2]['payload'],[.25,0.,.5])
 def test_exception_before_fsync_blocks_physics_and_keeps_reservation(self):
  counts=Counter(raw_attempts=0,raw_completed=0,physics_calls=0);counts['raw_attempts']+=1
  with tempfile.TemporaryDirectory() as folder:
   j=Journal(Path(folder)/'journal.jsonl');bad=State(velocity=(object(),0.),wheels=(),mass=1.,engine_multiplier=1.)
   with patch('retry.durable568.os.fsync') as fsync:
    with self.assertRaises(TypeError):
     j.append('BEFORE_NATIVE_RAW',**native_input_fields(bad,None));counts['physics_calls']+=1;counts['raw_completed']+=1
    fsync.assert_not_called()
   j.close()
  self.assertEqual((counts['raw_attempts'],counts['physics_calls'],counts['raw_completed']),(1,0,0))
 def test_fsync_failure_blocks_physics_no_retry(self):
  counts=Counter(raw_attempts=1,raw_completed=0,physics_calls=0)
  with tempfile.TemporaryDirectory() as folder:
   j=Journal(Path(folder)/'journal.jsonl')
   with patch('retry.durable568.os.fsync',side_effect=OSError('synthetic fsync failure')):
    with self.assertRaises(OSError):
     j.append('BEFORE_NATIVE_RAW',**native_input_fields(self.state(),None));counts['physics_calls']+=1;counts['raw_completed']+=1
   j.close()
  self.assertEqual((counts['raw_attempts'],counts['physics_calls'],counts['raw_completed']),(1,0,0))
 def test_durable_log_precedes_stub_physics_completion(self):
  counts=Counter(raw_attempts=1,raw_completed=0);order=[];real_fsync=os.fsync
  with tempfile.TemporaryDirectory() as folder:
   j=Journal(Path(folder)/'journal.jsonl')
   def fsync(fd):order.append('fsync');return real_fsync(fd)
   with patch('retry.durable568.os.fsync',side_effect=fsync):
    j.append('BEFORE_NATIVE_RAW',**native_input_fields(self.state(),np.asarray([.25,.5,0],np.float32)));order.append('stub_physics');counts['raw_completed']+=1
   j.close()
  self.assertEqual(order,['fsync','stub_physics']);self.assertEqual((counts['raw_attempts'],counts['raw_completed']),(1,1))
