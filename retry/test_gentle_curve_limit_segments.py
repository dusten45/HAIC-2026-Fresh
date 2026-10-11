"""Synthetic saved rows; no environment or policy execution."""
import math
import unittest

from retry.gentle_curve_limit_segments import summarize


def row(step, start, *, k=0., coef=14, near=False, distance=None, fallback=False, speed=0.):
    telemetry = {'actual_fallback_called': fallback}
    if fallback:
        response = {'route_telemetry': telemetry, 'curve_diagnostic': None}
    else:
        y = 6.
        x = k*y*y/(1+math.sqrt(1-k*k*y*y))
        actual_k = 2*x/(x*x+y*y)
        gate = not near and .015<=abs(actual_k)<=.05
        base = 5. if near else 7.
        target = lambda a: min(28., math.sqrt(a/(abs(actual_k)+.003)), distance or math.inf)
        telemetry.update(controller_target=[x,y], speed_estimate=speed)
        response = {'route_telemetry': telemetry,
            'cap_diagnostic': {'cap_input_scope':'age_zero', 'radial_clearances':[] if distance is None else [distance*distance/10]},
            'curve_diagnostic': {'curvature':actual_k,'near':near,'gate':gate,'coefficient':coef,
                'existing_smoothed_steer':0.,'baseline_final_target':target(base),
                'applied_final_target':target(coef if gate else base)}}
    return {'step':step,'truth_before':{'time':start},'policy_response':response}


class LimitSegmentsTests(unittest.TestCase):
    def test_conceptual_global_ties_safe_subtype_and_endpoint_weighting(self):
        rows = [row(1,0.),row(2,.1),row(3,.3,k=.03,near=True),
                row(4,.4,k=.03,distance=4.),row(5,.6,fallback=True),
                row(6,.7,distance=28.)]
        out = summarize(rows,[.1,.2,.1,.2,.1,.05])
        self.assertAlmostEqual(out['elapsed_s'],.75)
        self.assertAlmostEqual(out['interval_dwell_s']['global28'],.3)
        self.assertAlmostEqual(out['interval_dwell_s']['age0distance'],.2)
        self.assertAlmostEqual(out['interval_dwell_s']['tie:global28+age0distance'],.05)
        self.assertAlmostEqual(out['curvature_subtype_dwell_s']['safe5'],.1)
        self.assertAlmostEqual(sum(out['interval_dwell_share'].values()),1.)
        self.assertEqual(out['transition_count'],4)
        self.assertEqual(out['segments'][0]['start_step'],1)
        self.assertEqual(out['segments'][0]['end_step'],2)
        self.assertAlmostEqual(out['segments'][-1]['end_time_s'],.75)

    def test_own_input_shadow_distinguishes_target_and_pedal_masking(self):
        # Artificial D masking validates min algebra, not a claim that the
        # frozen source can produce D<28 with a genuinely near-false gate.
        rows=[row(1,0.,k=.03,coef=7),row(2,.1,k=.03,coef=14,distance=10.),
              row(3,.3,k=.03,coef=14,speed=0.)]
        out=summarize(rows,[.1,.2,.1]);shadow=out['own_input_7_vs_14']
        self.assertEqual(shadow['gate_intervals'],3)
        self.assertAlmostEqual(shadow['dwell_s']['target_raised'],.2)
        self.assertAlmostEqual(shadow['dwell_s']['target_fully_masked'],.2)
        self.assertAlmostEqual(shadow['dwell_s']['pedals_equal_despite_target_raise'],.2)
        self.assertAlmostEqual(shadow['mask_dwell_s']['age0distance'],.2)
        self.assertGreater(shadow['target_delta_max_m_s'],0.)
        self.assertEqual(out['segments'][0]['curvature_subtype'],'fast7')
        self.assertFalse(out['trajectory_comparison_performed'])
        with self.assertRaises(ValueError): summarize(rows,[.1])
        with self.assertRaises(ValueError): summarize(rows,[.1,-.1,.1])


if __name__ == '__main__':
    unittest.main()
