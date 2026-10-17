"""Zero-world finite/history boundary regressions for the parent static suite."""
import copy,unittest
from retry.history481 import bits,_finite,_historical,HistoryStop481

class HistoryFinite481Tests(unittest.TestCase):
    def fixture(self):
        nominal=[0.,1.,0.];qstar=[0.,.5,0.];key=bits(qstar)
        auth=dict(mode='baseline',command=qstar,nominal=nominal,qstar=qstar,commands={key:qstar},selected_key=key)
        return auth,dict(command=qstar,nominal=nominal)
    def test_baseline_requires_exact_registered_qstar(self):
        auth,action=self.fixture();self.assertEqual(_finite(auth,action,{}),'baseline')
        auth['command']=[0.,.25,0.];action['command']=auth['command'];auth['selected_key']=bits(auth['command'])
        with self.assertRaises(HistoryStop481):_finite(auth,action,{})
    def test_online_cannot_omit_original_or_zero_candidate(self):
        auth,action=self.fixture();auth.update(mode='online',selected_repeat_exact=True)
        with self.assertRaises(HistoryStop481):_finite(auth,action,{})
    def test_complete_command_bits_preserve_signed_zero(self):
        self.assertNotEqual(bits([0.,.5,0.]),bits([-0.,.5,0.]))
    def test_inactive_pedal_negative_zero_is_not_registered_positive_zero(self):
        auth,action=self.fixture();auth['nominal']=[0.,1.,-0.];auth['qstar']=[0.,.5,-0.]
        auth['command']=auth['qstar'];action.update(command=auth['qstar'],nominal=auth['nominal'])
        key=bits(auth['qstar']);auth.update(commands={key:auth['qstar']},selected_key=key)
        with self.assertRaises(HistoryStop481):_finite(auth,action,{})
    def test_qstar_cannot_change_nominal_steering(self):
        auth,action=self.fixture();auth['nominal']=[.125,1.,0.];action['nominal']=auth['nominal']
        with self.assertRaises(HistoryStop481):_finite(auth,action,{})
    def test_live_marker_is_not_frozen435_authority(self):
        with self.assertRaises(HistoryStop481):_historical({}, {}, [], [], {}, {}, {},[{'mode':'online'}])

if __name__=='__main__':unittest.main()
