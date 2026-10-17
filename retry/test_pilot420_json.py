"""Static serialization correction tests; never instantiate a physics world."""
import json,unittest
from dataclasses import asdict
from retry.planner419 import Parent,Current,GoalLedger
from retry.pilot420_json import json_ready,restore_bytes
class ReceiptCodec(unittest.TestCase):
 def test_original_immutable_context_reproduces_typeerror(self):
  parent=Parent.current({'speed':2.},{'memory':'before'},{'RNG':[1,2]},100)
  with self.assertRaises(TypeError):json.dumps(asdict(parent))
 def test_bytes_roundtrip_and_parent_stamp_preserved(self):
  parent=Parent.current({'speed':2.},{'memory':'before'},{'RNG':[1,2]},100);ctx=Current(parent,GoalLedger.start(0.,100),'signedC',(0.,0.,0.),'FIRST_LAP',2.,2.,2.,20.);before=parent.stamp();encoded=json.dumps(json_ready(ctx),allow_nan=False);back=restore_bytes(json.loads(encoded));restored=Parent(**back['parent']);self.assertEqual(restored.stamp(),before);self.assertEqual(parent.stamp(),before)
 def test_arbitrary_bytes_and_no_silent_string_coercion(self):
  self.assertEqual(restore_bytes(json.loads(json.dumps(json_ready({'x':b'\x00\xff'})))),{'x':b'\x00\xff'})
  with self.assertRaises(TypeError):json_ready(object())
 def test_nonfinite_numerical_problem_not_masked(self):
  for x in [float('nan'),float('inf'),float('-inf')]:
   with self.assertRaises(ValueError):json_ready({'x':x})
if __name__=='__main__':unittest.main()
