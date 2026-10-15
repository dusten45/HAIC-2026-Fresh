"""Read-only expiry schema adapter; never repeat completed actor diagnostics."""
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
from retry.diagnosis364_stage import G
import retry.diagnosis364_audit as audit

def recover(R):
    D=R/'stage364';p=read(D/'plan.json');assert not (D/'audit-private.json').exists() and not (D/'cost.json').exists();assert read(D/'run-result.json')['passed']
    assert all(sha(f)==h for f,h in p['source_hashes'].items());before=read(D/'call-budget.json')
    save(D/'readonly-schema-recovery-registration.json',dict(original_error="KeyError: 'item' in expiry report extraction; lineage339.track emits flat expiry dictionaries, not nested item.",frozen_audit_sha256=sha(G/'retry/diagnosis364_audit.py'),adapter_sha256=sha(Path(__file__)),completed_actor_diagnostics_preserved=True,new_actor_calls=0,new_clone_calls=0,new_native=0,no_policy_or_metric_change=True))
    original=audit.track
    def with_nested_expiry_alias(records):
        result=original(records)
        for row in result['records']:row['expiries']=[dict(e,item=dict(e)) for e in row['expiries']]
        return result
    audit.track=with_nested_expiry_alias
    try:audit.run(R)
    finally:audit.track=original
    assert read(D/'call-budget.json')==before
if __name__=='__main__':recover(Path(sys.argv[1]).resolve())
