"""Read-only audit of the preparation stop; does not import the evaluator."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

CPU = time.process_time()
G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response609-private')


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def main():
    r = read(G/'retry/early609_result.json')
    raw = read(D/'as-executed-result-private.json')
    closed = read(D/'CLOSED-private.json')
    diagnosis = read(D/'PREPARATION_DIAGNOSIS-private.json')
    checks = dict(technical_stop=r['status']=='TECHNICAL_STOP_NO_RETRY',
        no_source_cost=not r['cost'], no_arms=not r['arms'], no_replay=r['replay'] is None,
        no_registration=not (D/'REGISTERED-private.json').exists(),
        no_frozen_contract=not (G/'retry/early609_contract.json').exists(),
        no_full_preflight_record=not (G/'retry/early609_tests.json').exists(),
        no_telemetry_or_pair_execution=not list(D.glob('*-telemetry-private.json')) and not list(D.glob('C-pairs-*-private.json')),
        public_result_pinned=sha(G/'retry/early609_result.json')==closed['result_sha256'],
        private_result_pinned=sha(D/'as-executed-result-private.json')==closed['raw_sha256'],
        all_private_pins=all(sha(D/p)==h for p,h in raw['private_sha256'].items()),
        checkpoint_intact=all(diagnosis['checks'][k] for k in ['prefix_count96','last_checkpoint_digest','last_root','last_visited']),
        exact_guard_error_identified=not diagnosis['checks']['row_proposed_history_matches_tracking'] and diagnosis['checks']['row_proposed_history_matches_launch'],
        no_forbidden_work=all(r[k]==0 for k in ['native','worlds','resets','new_seed','carry','HOLDOUT','SEALED']),
        original_ledger=r['research_remaining']==22211 and r['reserve']==84000 and r['reserve_used']==0,
        original_main=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31',
        participants_unchanged=not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip())
    journal=[json.loads(s) for s in (D/'applied-journal-private.jsonl').read_text().splitlines()]
    head='0'*64
    for i,e in enumerate(journal):
        h=e.pop('sha256'); assert e['previous']==head and e['sequence']==i and digest(e)==h; head=h
    checks['only_durable_study_end']=len(journal)==1 and journal[0]['kind']=='STUDY_END'
    task=read(D/'TASK_STARTED-private.json')
    elapsed=time.time()-task['start_epoch']+task['prior_preparation_wall_s']
    audit_cpu=time.process_time()-CPU
    checks['budget_including_cleanup_reserve']=elapsed+120<6600 and r['time']['CPU_s']+audit_cpu+90<5400
    out=dict(study=609,status='PREPARATION_STOP_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',
        checks=checks,source_model=0,force=0,geometry=0,native=0,new_evaluations=0,
        audit_CPU_s=audit_cpu,whole_task_wall_through_audit_s=elapsed,
        source_sha256={p:sha(G/p) for p in ['retry/early609.py','retry/early609_core.py']},
        result_sha256=sha(G/'retry/early609_result.json'),
        cause='Guard compared raw96 launch proposed_history with tracking history. Saved full checkpoint and prefix are intact. Source registration and actual clone/budget preflight were not reached. No retry or correction executed.')
    (G/'retry/early609_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); assert all(checks.values())


if __name__=='__main__': main()
