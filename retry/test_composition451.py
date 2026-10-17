"""Recorded guardian rejection and policy-segment fixtures, no integrator."""
import copy,tempfile,unittest
from dataclasses import asdict,replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from retry.guard451 import classify451
from retry.segment451 import Parent451,Segment451Error
from retry.composition451 import Study451
from retry.root449 import load_root449
from retry.loss389_analyze import read
from retry.receipt421_io import load_receipt
from retry.planner419 import GoalLedger
from retry.planner419_model_ledger import ForecastLedger
from retry.boundary434 import TailRecord
from retry.test_query445 import fixture as query_fixture
R=Path('/workspace/haic-private-retry-20261009')

class Composition451Tests(unittest.TestCase):
    def recorded_shadow(self,decision):
        label='B1_decision'+str(decision)+'_nominal1';value=read(R/'stage445'/(label+'-private.json'))
        payload=load_receipt(R/'stage445'/(label+'_inputs-before-integration-private.json'))
        fixed=read(Path(read(R/'stage445/plan.json')['fixed_plan']))
        return SimpleNamespace(rows=copy.deepcopy(value['rows']),status=value['status'],error=value['error'],ledger=ForecastLedger(**value['model_ledger']),root_ledger=GoalLedger(**payload['ledger']),line=np.asarray(fixed['line']),L=sum(fixed['free_profile']['ds']),initial_ok=value['initial_actions']==13,initial_safe=not any(r['safety'] for r in value['rows']),initial_progress=ForecastLedger(**value['model_ledger']).progress_qualified())
    def segment_parent(self):
        data=read(R/'stage450/nominal1-private.json');actual=load_root449(R,'nominal')['ledger']
        c=Parent451.__new__(Parent451);c.segment451=None;c.label='fixture451_parent';c._selected451=False;c.rows=copy.deepcopy(data['rows']);c.status='ACTIVE';c.recipe='nominal';c.ledger=ForecastLedger(**data['model_ledger']);c.root_ledger=actual
        c.m=SimpleNamespace(t=data['final_state']['physical']['actual_time'],native_ticks=4*len(c.rows));c.ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(data['controller_memory']))
        tail=TailRecord(**load_receipt(R/'stage450/nominal1-same-live-tail-private.json')['tail'])
        c.stream=SimpleNamespace(tail_record=lambda:tail,require_owner=lambda owner:self.assertIs(owner,c))
        return c,actual,data
    def test_recorded_safe_H13_is_eligible(self):
        self.assertEqual(classify451(self.recorded_shadow(1))['kind'],'SAFE_PROGRESS_H13')
    def test_recorded_physical_rejection_is_expected_alternative_only(self):
        c=self.recorded_shadow(2);z=classify451(c)
        self.assertFalse(z['valid']);self.assertEqual(z['kind'],'REGISTERED_PHYSICAL_INELIGIBILITY');self.assertIn('path_error_over3m',z['reasons'])
    def test_unknown_or_reverse_or_technical_rejection_is_global_error(self):
        for reason in ['reverse','domain_error','path_error_over3m,reverse']:
            c=self.recorded_shadow(2);c.rows[-1]['safety']=[reason];c.error=reason
            with self.assertRaises(Exception):classify451(c)
        c=self.recorded_shadow(1);c.status='TECHNICAL_STOP'
        with self.assertRaises(Exception):classify451(c)
    def test_fabricated_deadline_or_model_progress_is_rejected(self):
        c=self.recorded_shadow(1);c.status='INFEASIBLE';c.error='predicted_progress_deadline';c.ledger=replace(c.ledger,deadline_missed=True)
        with self.assertRaises(Exception):classify451(c)
        c=self.recorded_shadow(1);c.rows[0]['model_progress']+=.001
        with self.assertRaises(Exception):classify451(c)
    def test_segment_blocks_nominal_tail_ranking_and_unselected_step(self):
        c,actual,data=self.segment_parent()
        with tempfile.TemporaryDirectory() as td,patch('retry.segment451.snapshot',return_value=data['final_state']):
            token=c.begin_guarded(actual,Path(td));token.validate(c,actual)
            for call in [lambda:c.stream.tail_record(),lambda:c.evidence(None),lambda:c.continue_tail('forbidden'),lambda:c.one('unselected')]:
                with self.assertRaises(Segment451Error):call()
    def test_segment_rejects_other_owner_prefix_or_native_root(self):
        c,actual,data=self.segment_parent()
        with tempfile.TemporaryDirectory() as td,patch('retry.segment451.snapshot',return_value=data['final_state']):
            token=c.begin_guarded(actual,Path(td))
            with self.assertRaises(Exception):token.validate(copy.copy(c),actual)
            with self.assertRaises(Exception):token.validate(c,replace(actual))
            c.rows[0]['model_progress']+=.001
            with self.assertRaises(Exception):token.validate(c,actual)
    def test_production_model_query_spawns_new_guardian_factory_without_step(self):
        with query_fixture() as(ex,parent,actual,query,step):
            study=Study451.__new__(Study451);study.d=ex.d;study.meter=ex.meter;study.fixed=ex.fixed;study.pace=ex.pace;study.children=[]
            c=query.spawn(study,parent,actual,'fixture451_shadow','nominal')
            try:
                self.assertIs(type(c.ledger),ForecastLedger);self.assertEqual(c.ledger.actual_root_digest,query.context.ledger.digest());self.assertFalse(query.actual_DONE_allowed);self.assertEqual(step.call_count,0)
            finally:c.close()

    def recorded_parent_step(self,decision,recipe):
        from retry.audit439 import root_ledger
        from retry.planner419_model_ledger import ModelPrediction
        import json
        data=read(R/'stage445/B1-private.json');own=data['rows'][decision-1]
        rootrow=json.loads((R/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()[89]);actual=root_ledger(rootrow)
        parent=Parent451.__new__(Parent451);parent.rows=copy.deepcopy(data['rows'][:decision-1]);parent.status='ACTIVE';parent._selected451=False
        parent.ledger=ForecastLedger.fork(actual)
        for row in parent.rows:parent.ledger=parent.ledger.advance_prediction(ModelPrediction(row['model_progress'],round(row['predicted']['time']*50),False))
        parent.segment451=SimpleNamespace(prefix_actions=0,validate=lambda p,a:None)
        parent.fixed=read(Path(read(R/'stage445/plan.json')['fixed_plan']))
        root=load_receipt(R/'stage445'/('B1_decision'+str(decision)+'-query-root-private.json'))
        query=SimpleNamespace(context=SimpleNamespace(ledger=GoalLedger(**root['context']['ledger'])),validate=lambda p,a:None)
        selected=read(R/'stage445'/('B1_decision'+str(decision)+'_'+recipe+'1-private.json'))['rows'][0]
        def recorded_step(*args,**kwargs):
            self.assertEqual(kwargs['first_override'],own['command']);parent.rows.append(copy.deepcopy(own))
            parent.ledger=parent.ledger.advance_prediction(ModelPrediction(own['model_progress'],round(own['predicted']['time']*50),False))
        parent.one=recorded_step
        report=parent.guarded_one(query,actual,dict(recipe=recipe,first=selected),root['context']['nominal'],own['memory_before'],'fixture_recorded_only')
        self.assertTrue(report['physical']['passed']);self.assertTrue(report['ledger']['goal_hit_exact']);self.assertFalse(report['model_native_authority'])
    def test_recorded_selected_nominal_runs_new_parent_first_fidelity_path(self):
        self.recorded_parent_step(1,'nominal')
    def test_recorded_selected_neutral_runs_new_parent_first_fidelity_path(self):
        self.recorded_parent_step(2,'neutralbrake')
