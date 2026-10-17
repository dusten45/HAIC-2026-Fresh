"""Pure policy/protocol fixtures for the parent's zero-world gate; no test runs here."""
import copy
import struct
import unittest
from retry.online485 import decision,opportunity,rank

def option(pedal,M80,error,valid=True):
    command=[0.,pedal,0.]
    return struct.pack('<3f',*command).hex(),dict(command=command,valid=valid,
        M80=M80,max_guard_path_error_m=error,active_pedal=pedal)

def parent(status='H6_SAFE_CENSORED',actions=6,margin=1.,*,partial=False):
    lengths=[4]*actions
    if partial and lengths:lengths[-1]=2
    return dict(status=status,actions=actions,raw_lengths=lengths,raw_ticks=sum(lengths),
        margins_m=[margin]*actions,safe_own_actions=actions-(status=='UNSAFE'),
        progress_deadline_missed=status=='INFEASIBLE',
        admissible_query_raw_times=[4*i for i in range(actions)])

class Policy485Tests(unittest.TestCase):
    def test_disagreement_uses_same_eligible_context(self):
        a=option(1.,.2,.7);b=option(0.,.1,1.1);invalid=option(.5,0.,0.,False)
        query={'options':dict([a,b,invalid])};frozen=copy.deepcopy(query)
        proof=opportunity([query])[0]
        self.assertEqual(proof['control_key'],b[0]);self.assertEqual(proof['variant_key'],a[0])
        self.assertTrue(proof['disagreement']);self.assertTrue(proof['same_context'])
        self.assertEqual(query,frozen)

    def test_different_commands_at_different_contexts_are_not_disagreement(self):
        queries=[{'options':dict([option(1.,.1,.2)])},{'options':dict([option(0.,.2,.1)])}]
        self.assertFalse(any(p['disagreement'] for p in opportunity(queries)))

    def test_invalid_and_empty_domains_cannot_create_opportunity(self):
        self.assertEqual(opportunity([{'options':{}},{'options':dict([option(1.,0.,0.,False)])}]),[])

    def test_exact_lexicographic_margin_then_force_then_pedal(self):
        a=option(0.,100.,1.)[1];b=option(1.,0.,1.+1e-12)[1]
        self.assertLess(rank(a,'variant'),rank(b,'variant'))
        self.assertGreater(rank(a,'control'),rank(b,'control'))
        self.assertLess(rank(option(1.,.1,1.)[1],'variant'),rank(option(0.,.1,1.)[1],'variant'))

    def test_both_safe_can_pass_new_independent_criterion(self):
        c=parent(margin=1.);v=parent(margin=1.3)
        proof=decision(c,v,True,3.)
        self.assertTrue(proof['success']);self.assertFalse(proof['reject'])
        self.assertEqual(proof['common_executed_own_actions'],6)

    def test_threshold_and_opportunity_are_strict(self):
        self.assertFalse(decision(parent(margin=1.),parent(margin=1.25),True,3.)['success'])
        self.assertFalse(decision(parent(margin=1.),parent(margin=1.5),False,3.)['success'])
        self.assertFalse(decision(parent(margin=1.),parent(margin=.75),True,3.)['reject'])
        self.assertTrue(decision(parent(margin=1.),parent(margin=.74),True,3.)['reject'])

    def test_partial_timing_and_early_finish_are_not_success(self):
        self.assertFalse(decision(parent(actions=4,partial=True),parent(margin=1.5),True,3.)['success'])
        self.assertFalse(decision(parent(actions=4),parent('FINISHED',3,1.5),True,3.)['success'])

    def test_adverse_evidence_precedes_root_domination(self):
        proof=decision(parent(margin=1.),parent('UNSAFE',3,1.1),True,1.2)
        self.assertTrue(proof['root_dominates_identifiability']);self.assertTrue(proof['reject'])
        self.assertEqual(proof['verdict'],'REJECT')

    def test_empty_earlier_than_later_empty_control_is_a_falsifier(self):
        # Control safely executes two additional holds before its own empty
        # domain; its later final status must not erase matched-time evidence.
        proof=decision(parent('EMPTY_FINITE_CANDIDATE_DOMAIN',4,1.),
                       parent('EMPTY_FINITE_CANDIDATE_DOMAIN',2,1.1),True,3.)
        self.assertTrue(proof['reject'])

    def test_simultaneous_nonadmissible_control_is_not_empty_falsifier(self):
        proof=decision(parent('INFEASIBLE',2,1.),
                       parent('EMPTY_FINITE_CANDIDATE_DOMAIN',2,1.1),True,3.)
        self.assertFalse(proof['reject'])

    def test_progress_deadline_adverse_is_preserved(self):
        self.assertTrue(decision(parent(margin=1.),parent('INFEASIBLE',2,1.1),True,3.)['reject'])

if __name__=='__main__':unittest.main()
