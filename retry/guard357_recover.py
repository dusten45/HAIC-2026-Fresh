"""Before-first-actor repair: normalize host record paths, preserve frozen study."""
import datetime
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
import retry.guard357_run as job


def run(R):
    D=R/'stage357';b=read(D/'call-budget.json');assert b['actor_act_calls']==b['actor_resets']==b.get('actor_commit_calls',0)==0
    failed=read(D/'run-result.json');assert not failed['passed'] and failed['error']=="AttributeError: 'str' object has no attribute 'read_text'" and not failed['receipts']
    assert not any((D/c['key']).exists() for c in read(D/'plan.json')['cases'])
    F=D/'technical-parser-failure0';assert not F.exists();F.mkdir(mode=0o700)
    for name in ['opening.json','run-result.json','failure-private.json']:(D/name).rename(F/name)
    save(D/'parser-repair-registration.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),before_any_actor_reset_or_native=True,failed_attempt_preserved=str(F),scope='Only hostrows(path) convertsstrtoPath. Policyarchive/passiveworker/cases/GTgate/callbudgets/loop/control untouched; no extraexperimentalarm.',original_registered_runner_sha256=sha(Path(job.__file__)),recovery_adapter_sha256=sha(Path(__file__)),actor_cap=3342,reset_cap=12,native_cap=0))
    strict_rows=job.rows
    job.rows=lambda path:strict_rows(Path(path))
    job.run(R)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
