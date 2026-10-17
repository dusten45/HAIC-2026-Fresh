"""485 native-prefix root bindings and unchanged finite history: pure fixtures only."""
import ast,copy,hashlib,inspect
import unittest
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from retry import history485 as h
from retry.planner419 import GoalLedger,ActualObservation
from retry.planner419_model_ledger import ForecastLedger

class History485Tests(unittest.TestCase):
    def fixture(self):
        slot='D485-A';memory={'C':{'phase':'FIRST_LAP'}}
        initial=GoalLedger.start(0.,0);root_actual=initial.advance_actual(ActualObservation(20.,4,False))
        root=dict(physical=dict(actual_time=.08,hull=dict(position=[20.,0.],velocity=[0.,1.]),source_world_contacts=2),finish_tracker=dict(candidate_crossing_time_s=None,finish_time_s=None))
        rng=b'static-485-no-random-draw';rd=hashlib.sha256(rng).hexdigest()
        projected=[0.,20.,20.,20.,20.];nd=h.digest(projected);policy='c'*64;case='d'*64
        context=dict(state=root,before=memory,ledger=asdict(ForecastLedger.fork(root_actual)),actual_ledger=asdict(root_actual),RNG=dict(global_pickle=rng,digest=rd),slot=slot,case_identity_digest=case,nodes_digest=nd,policy_digest=policy)
        def row(step,pre,post,before,after,p0,g0,p1,hit):
            return dict(step=step,pre=dict(pos=pre,vel=[0.,1.],time=(step-1)*.08),post=dict(pos=post,vel=[0.,1.],time=step*.08),memory_before=before,nominal_memory_after=after,raw_ticks=4,completed=False,ended=False,truncated=False,command=[0.,1.,0.],nominal=[0.,1.,0.],safety=[],progress_before=p0,goal_before=g0,progress_after=p1,goal_hit_actual_step=hit)
        rows=[row(1,[0.,0.],[20.,0.],{'C':{'phase':'LAUNCH'}},memory,0.,3.24,20.,True),row(2,[20.,0.],[20.,1.],memory,memory,20.,root_actual.goal_m,21.,False)]
        after=root_actual.advance_actual(ActualObservation(21.,8,False))
        payloads={
          'context':context,'full':{'native':'full'},
          'fixed':dict(line=[[0.,0.],[20.,0.],[20.,20.],[0.,20.]],free_profile=dict(ds=[20.]*4)),
          'nodes':dict(projected_nodes=projected,nodes_digest=nd,policy_digest=policy),
          'trace':dict(rows=rows,initial_actual_ledger=asdict(initial),root_actual_ledger=asdict(root_actual),witness_index=2),
          'witness':dict(row=rows[-1],posts=[],full_pre={'native':'full'},full_post={},ledger_before=asdict(root_actual),ledger_after=asdict(after),nominal=[0.,1.,0.],own_native_fact=True),
        }
        counts=dict(slot_actions=0,slot_resets=0,slot_reset_raw=0,slot_action_raw=0);events=[]
        for kind in ['reset']+['reset_raw']*51+['action']+['action_raw']*4+['action']+['action_raw']*4:
            key=dict(reset='slot_resets',reset_raw='slot_reset_raw',action='slot_actions',action_raw='slot_action_raw')[kind];counts[key]+=1
            events.append(dict(kind=kind,sequence=len(events)+1,charged_before_call=True,**counts))
        payloads['journal']=dict(slot=slot,case_identity_digest=case,events=events,counts=counts)
        proof=dict(schema=h.PREFIX_SCHEMA485,stage=485,passed=True,slot=slot,case_identity_digest=case,p4_nodes_digest=nd,profile_sha256='a'*64,actions=1,native_actions_including_witness=2,initial_actual_ledger=asdict(initial),root_actual_ledger=asdict(root_actual),root_state_digest=h.digest(root),root_memory_digest=h.digest(memory),root_RNG_digest=rd,policy_digest=policy)
        for stem,path in [('root_context','context'),('native_trace','trace'),('native_charge_journal','journal'),('witness','witness'),('root_full','full'),('fixed_plan','fixed'),('nodes','nodes')]:proof[stem+'_path']=path;proof[stem+'_sha256']='a'*64
        payloads['gate']=dict(passed=True,slot=slot,case_identity_digest=case,p4_nodes_digest=nd,root_context_sha256='a'*64,root_state_digest=h.digest(root))
        return proof,payloads,root,memory

    def checked(self,payloads):
        return patch.object(h,'checked',side_effect=lambda path,sha:copy.deepcopy(payloads[str(path)]))

    def authenticate(self,proof,payloads,root,memory):
        with self.checked(payloads),patch('retry.terminal410_model.from_actual_full',return_value=copy.deepcopy(root)):
            final=h.finish_root_proof(proof,'gate','b'*64)
            return h.authenticate_root485(final,root,payloads['context']['ledger'],memory)

    def test_generic_non121_native_prefix_and_fresh_gate_bind(self):
        proof,payloads,root,memory=self.fixture()
        result=self.authenticate(proof,payloads,root,memory)
        self.assertEqual(result['stage'],485);self.assertEqual(result['actions'],1)
        self.assertFalse(result['actual_execution_allowed']);self.assertFalse(result['actual_DONE_allowed'])

    def test_success_path_constructs_or_integrates_no_world(self):
        from retry.source_vehicle_transition import SourceVehicleTransition
        from retry.terminal410_model import TerminalVehicleTransition
        from retry import diagnose
        import Box2D
        proof,payloads,root,memory=self.fixture()
        with ExitStack() as stack:
            forbidden=[]
            for cls in (SourceVehicleTransition,TerminalVehicleTransition):
                for name in ('__init__','step'):
                    forbidden.append(stack.enter_context(patch.object(cls,name,side_effect=AssertionError('485_FORBIDDEN_PHYSICS'))))
            forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('485_FORBIDDEN_NATIVE'))))
            forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('485_FORBIDDEN_WORLD'))))
            self.authenticate(proof,payloads,root,memory)
            for guard in forbidden:guard.assert_not_called()

    def test_foreign_case_line_and_profile_file_hash_are_rejected(self):
        proof,payloads,root,memory=self.fixture()
        with self.checked(payloads),patch('retry.terminal410_model.from_actual_full',return_value=copy.deepcopy(root)):
            final=h.finish_root_proof(proof,'gate','b'*64)
            with self.assertRaises(h.HistoryStop485):
                h.authenticate_root485(final,root,payloads['context']['ledger'],memory,[[0.,0.],[1.,0.],[1.,1.]])
            final['profile_sha256']='c'*64
            with self.assertRaises(h.HistoryStop485):
                h.authenticate_root485(final,root,payloads['context']['ledger'],memory)

    def test_bootstrap_alone_and_legacy121_cannot_authorize_model_history(self):
        proof,_,_,_=self.fixture()
        with self.assertRaises(h.HistoryStop485):h.NativePrefix485.parse(proof,qualified=True)
        for key,value in [('schema','legacy483'),('stage',483),('actions',128),('native_actions_including_witness',3),('slot','D484-A'),('passed',False)]:
            bad=copy.deepcopy(proof);bad[key]=value
            with self.assertRaises(h.HistoryStop485):h.NativePrefix485.parse(bad)

    def test_gate_cannot_be_cached_from_another_case_or_root(self):
        for key in ['passed','slot','case_identity_digest','p4_nodes_digest','root_context_sha256','root_state_digest']:
            proof,payloads,root,memory=self.fixture();payloads['gate'][key]=False if key=='passed' else 'other'
            with self.assertRaises(h.HistoryStop485):self.authenticate(proof,payloads,root,memory)

    def test_complete_prefix_actual_ledger_and_witness_are_required(self):
        for mutate in [lambda p:p['trace']['rows'].pop(),lambda p:p['trace']['rows'][0].update(progress_after=19.),lambda p:p['witness'].update(own_native_fact=False),lambda p:p['context']['actual_ledger'].update(goal_m=99.),lambda p:p['context']['ledger'].update(actual_root_digest='0'*64),lambda p:p['nodes']['projected_nodes'].__setitem__(1,21.),lambda p:p['context']['RNG'].update(global_pickle=b'tamper')]:
            proof,payloads,root,memory=self.fixture();mutate(payloads)
            with self.assertRaises((h.HistoryStop485,ValueError)):self.authenticate(proof,payloads,root,memory)

    def test_journal_before_call_counts_and_witness_charge_cannot_be_forged(self):
        for mutate in [lambda j:j['events'][-1].update(charged_before_call=False),lambda j:j['events'][-1].update(slot_action_raw=7),lambda j:j['counts'].update(slot_actions=1),lambda j:j.update(slot='D485-B')]:
            proof,payloads,root,memory=self.fixture();mutate(payloads['journal'])
            with self.assertRaises(h.HistoryStop485):self.authenticate(proof,payloads,root,memory)

    def test_old_finite_ranking_raw_and_ledger_validator_algebra_unchanged(self):
        from retry import history483 as old
        for name in ['_finite','rank_key','raw_max_guard_path_error','_join_snapshot','_historical','_replay_observed']:
            self.assertEqual(ast.dump(ast.parse(inspect.getsource(getattr(old,name))),include_attributes=False),ast.dump(ast.parse(inspect.getsource(getattr(h,name))),include_attributes=False),name)
        source=inspect.getsource(old.validate_history)
        start=source.index("                require(root_proof['stage']==483")
        end=source.index('            require(proof_identity==root_proof_identity',start)
        source=source[:start]+"                authenticate_root485(root_proof,root_state,initial_ledger,actions[0]['memory_before'],line)\n"+source[end:]
        source=source.replace('return dict(stage=483,scope=','return dict(stage=485,scope=')
        self.assertEqual(ast.dump(ast.parse(source),include_attributes=False),ast.dump(ast.parse(inspect.getsource(h.validate_history)),include_attributes=False))

if __name__=='__main__':unittest.main()
