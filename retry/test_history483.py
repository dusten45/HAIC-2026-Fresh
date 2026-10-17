"""Pure arm-ranking/receipt regressions. Parent runs these in its static gate."""
import copy
import unittest
from unittest.mock import patch
from retry.history483 import HistoryStop483,_finite,bits,rank_key,raw_max_guard_path_error

LINE=[[0.,0.],[20.,0.],[20.,20.],[0.,20.]]

class History483Tests(unittest.TestCase):
    def fixture(self,arm='control',selected=0):
        nominal=[0.,1.,0.];qstar=[0.,.5,0.];zero=[0.,0.,0.]
        commands={bits(v):v for v in (nominal,qstar,zero)};keys=list(commands)
        memory={'C':{'phase':'FIRST_LAP'}};traces={};options={}
        for i,(k,v) in enumerate(commands.items()):
            path='/tmp/static483-candidate-'+str(i)
            row=dict(command=v,memory_before=memory,memory_after=memory,safety=[],
                     raw_hull=[dict(origin_position=[5.,.2],origin_linear_velocity=[1.,0.])],
                     predicted=dict(position=[6.,[1.,.5,.8][i]],velocity=[1.,0.],raw_ticks=1,terminal=False,finished=False),
                     tires=[{'force_ratio':1.+[0.,.25,.5][i]} for _ in range(4)])
            traces[path]=dict(rows=[row],model_ledger={'deadline_missed':False},final_state={},controller_memory=memory,status='ACTIVE',error=None)
            options[k]=dict(command=v,aliases=[('nominal','qstar','zero')[i]],valid=True,M80=[0.,.25,.5][i],
                            max_guard_path_error_m=[1.,.5,.8][i],active_pedal=v[1],first_path=path,first_sha256='a'*64)
        selected_key=keys[selected];first=options[selected_key]['first_path'];repeat='/tmp/static483-selected-repeat'
        traces[repeat]=copy.deepcopy(traces[first])
        auth=dict(mode='online',ranking_arm=arm,command=commands[selected_key],nominal=nominal,qstar=qstar,
                  commands=commands,selected_key=selected_key,selected_repeat_exact=True,repeat_path=repeat,repeat_sha256='b'*64)
        action=dict(command=auth['command'],nominal=nominal,memory_before=memory,memory_after=memory)
        decision=dict(options=options,selected_repeat_proof=dict(first_path=first,first_sha256='a'*64,repeat_path=repeat,repeat_sha256='b'*64,full_trace_exact=True))
        return auth,action,decision,traces

    def validate(self,auth,action,decision,traces):
        with patch('retry.history483.checked',side_effect=lambda path,sha:traces[str(path)]),patch('retry.history483.metrics',return_value=({},[])):
            return _finite(auth,action,decision,LINE)

    def test_control_and_variant_choose_different_eligible_commands(self):
        self.assertEqual(self.validate(*self.fixture('control',0)),'online')
        self.assertEqual(self.validate(*self.fixture('variant',1)),'online')
        with self.assertRaises(HistoryStop483):self.validate(*self.fixture('variant',0))
        with self.assertRaises(HistoryStop483):self.validate(*self.fixture('control',1))

    def test_raw_root_is_included_instead_of_endpoint_only(self):
        _,_,_,traces=self.fixture();row=copy.deepcopy(next(iter(traces.values()))['rows'][0])
        row['raw_hull'][0]['origin_position']=[5.,2.]
        self.assertEqual(raw_max_guard_path_error(row,LINE),2.)

    def test_metric_tampering_is_rejected_in_both_arms(self):
        for arm,selected in [('control',0),('variant',1)]:
            for field in ('M80','max_guard_path_error_m'):
                auth,action,decision,traces=self.fixture(arm,selected)
                decision['options'][auth['selected_key']][field]+=.001
                with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)

    def test_candidate_eligibility_is_replayed(self):
        auth,action,decision,traces=self.fixture('variant',1)
        first=decision['options'][auth['selected_key']]['first_path'];traces[first]['model_ledger']['deadline_missed']=True
        with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)

    def test_all_invalid_cannot_authorize_own_action(self):
        auth,action,decision,traces=self.fixture()
        for option in decision['options'].values():
            option['valid']=False;traces[option['first_path']]['status']='STOP'
        with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)

    def test_repeat_and_alias_domain_cannot_be_forged(self):
        auth,action,decision,traces=self.fixture()
        decision['options'][auth['selected_key']]['aliases']=['qstar']
        with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)
        auth,action,decision,traces=self.fixture()
        traces[auth['repeat_path']]['final_state']={'different':True}
        with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)

    def test_exact_lexicographic_ranking_without_epsilon(self):
        self.assertLess(rank_key('variant',100.,1.,0.),rank_key('variant',0.,1.+1e-12,1.))
        self.assertLess(rank_key('variant',.1,1.,.2),rank_key('variant',.2,1.,1.))
        self.assertLess(rank_key('control',.1,2.,.8),rank_key('control',.1,0.,.2))
        self.assertLess(rank_key('variant',.1,1.,.8),rank_key('variant',.1,1.,.2))

    def test_baseline_is_not_new_arm_authority(self):
        auth,action,decision,traces=self.fixture();auth['mode']='baseline'
        with self.assertRaises(HistoryStop483):self.validate(auth,action,decision,traces)

    def test_signed_zero_identity_is_preserved(self):
        self.assertNotEqual(bits([0.,0.,0.]),bits([0.,-0.,0.]))

if __name__=='__main__':unittest.main()
