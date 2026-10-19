import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from retry.durable568 import Journal,evaluate_force,guarded_tick,inspect

class Durable568Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'events.jsonl';self.j=Journal(self.path);self.calls=0
    def tearDown(self):self.j.close();self.tmp.cleanup()
    def force(self,ratio=.8):
        self.calls+=1;return [dict(ratio=ratio,clipped=ratio>1.) for _ in range(4)]
    def evaluate(self,ratio=.8,history=(0,100),inject=None):
        return evaluate_force(self.j,dict(test_state=1),[0.,.1,0.],history,dict(mode='diagnostic-probe'),lambda:self.force(ratio),inject=inject)
    def events(self):return [json.loads(x) for x in self.path.read_text().splitlines()]
    def test_input_survives_injected_failure_before_evaluator(self):
        def boom(point):
            if point=='after_input':raise RuntimeError('INJECTED')
        with self.assertRaisesRegex(RuntimeError,'INJECTED'):self.evaluate(inject=boom)
        self.assertEqual(self.calls,0);self.assertEqual(self.events()[-1]['kind'],'BEFORE_FORCE');self.assertTrue(inspect(self.path)['valid'])
    def test_force_and_clip_failure_preserved_before_any_tick(self):
        v=self.evaluate(1.06);self.assertEqual(v['gate'],'FORCE')
        v=self.evaluate(1.01,(10,100));self.assertEqual(v['gate'],'CLIP_HISTORY')
        self.assertEqual(self.events()[-1]['proposed_history'],[14,104]);self.assertTrue(inspect(self.path)['valid'])
    def test_verdict_survives_injected_failure(self):
        def boom(point):
            if point=='after_verdict':raise RuntimeError('INJECTED')
        with self.assertRaisesRegex(RuntimeError,'INJECTED'):self.evaluate(inject=boom)
        self.assertEqual(self.events()[-1]['kind'],'FORCE_VERDICT');self.assertEqual(self.calls,1)
    def test_fsync_failure_prevents_evaluation(self):
        with patch('retry.durable568.os.fsync',side_effect=OSError('INJECTED_FSYNC')):
            with self.assertRaisesRegex(OSError,'INJECTED_FSYNC'):self.evaluate()
        self.assertEqual(self.calls,0)
    def test_body_domain_failure_is_durable(self):
        v=self.evaluate()
        with self.assertRaisesRegex(RuntimeError,'MODEL_BODY_DOMAIN'):
            guarded_tick(self.j,v,dict(mode='diagnostic-probe'),lambda:dict(result=1),lambda _:100.,lambda x:x)
        self.assertFalse(self.events()[-1]['body_domain_pass']);self.assertTrue(inspect(self.path)['valid'])
    def test_exact_one_is_unclipped(self):
        v=self.evaluate(1.);self.assertEqual(v['history'],[0,104]);self.assertIsNone(v['gate'])

if __name__=='__main__':unittest.main()
