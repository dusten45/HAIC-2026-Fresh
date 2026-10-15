"""Keep coverage completeness distinct from support-gate success at lastcase."""
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
from retry.evaluation363_close import close
from retry.evaluation363_stage import G

def finish(R):
    D=R/'stage363';p=read(D/'plan.json');status=read(D/'batch-status.json');assert status['evaluated']==p['order'] and status['stop_reason']=='supported_point_loss'
    # Frozenclose conflates successful loop-exhaustion with complete measurement.
    # Preserve it byte-for-byte and correct only the reporting metadata afterward.
    save(D/'report-completeness-correction-registration.json',dict(readonly_accounting_only=True,reason='Last13thcasefailedsupportgate, soforloopdidnotexhaustnormally;all18actualrecordsnonethelesspresent. Tablecoverageandcandidategateareseparate.',frozen_close_sha256=sha(G/'retry/evaluation363_close.py'),adapter_sha256=sha(Path(__file__)),new_native=0,new_actor=0,new_simulation=0))
    close(R);r=read(D/'summary-private.json');save(D/'summary-before-completeness-correction-private.json',r);a=r['aggregate'];assert a['measured_conditions']==18 and len(r['table'])==18 and not a['unmeasured'] and not a['table_complete']
    a.update(table_complete=True,frozen357_completion_fraction_of18=a['frozen357_completed']/18)
    r['batch_status']['all13_evaluated']=True;r['batch_status']['all13_support_gates_passed']=False
    r['report_metadata_correction']=dict(coverage_completeness_separated_from_lastcase_gate_failure=True,no_outcome_gate_budget_or_cost_changed=True,no_experiment_recovery=True)
    save(D/'summary-private.json',r);save(G/'retry/evaluation363_result.json',r)
    v=read(D/'final-report-verification.json');v.update(table_complete=True,all13_evaluated=True,support_gate_all=False,bookkeeping_verification_not_candidate_pass=True);save(D/'final-report-verification.json',v)
    print('All18recordstablecomplete; supportgatefailedremainsfailed; no outcomes/cost/native changed.',flush=True)
if __name__=='__main__':finish(Path(sys.argv[1]).resolve())
