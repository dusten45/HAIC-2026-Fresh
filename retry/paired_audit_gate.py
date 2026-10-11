"""Publish and consume a one-use paired-audit readiness receipt, failing closed.

Plan creation and process launch are separate operations. A plan by itself never
permits launch, including when an outer shell continues after a failed command.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()


def _time_gate(plan, receipt, now):
    assert receipt['status'] == 'PASS' and receipt['native_execution_authorized'] is True
    assert receipt['native_deadline_utc'] == plan['simulation_deadline_utc']
    assert receipt['overall_deadline_utc'] == plan['deadline_utc']
    native_end = dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
    end = dt.datetime.fromisoformat(plan['deadline_utc'])
    assert native_end.tzinfo is not None and end.tzinfo is not None
    assert now < native_end <= end
    required = receipt['required_native_window_s']
    assert isinstance(required, (int, float)) and required > 0
    assert (native_end - now).total_seconds() >= required, 'Insufficient native time window'


def _write_once(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
    path.chmod(0o600)


def publish_ready_plan(plan_path, plan, receipt, *, now=None):
    """Check all time gates before publishing; readiness is written last.

    Caller must already have frozen and checked candidate, split, source/runtime
    hashes and qualification. Interrupted publication leaves no launchable batch.
    """
    plan_path = Path(plan_path)
    now = now or dt.datetime.now(dt.timezone.utc)
    receipt = dict(receipt)
    _time_gate(plan, receipt, now)
    assert receipt['qualification_sha256'] == plan['qualification_sha256']
    assert receipt['qualification_sha256'] == _hash(Path(plan['qualification_path']).read_bytes())
    assert json.loads(Path(plan['qualification_path']).read_bytes())['status'] == 'PASS'
    for group in ('source_sha256', 'runtime_sha256'):
        for name, wanted in plan[group].items():
            assert _hash(Path(name).read_bytes()) == wanted
    data = _json(plan)
    receipt['plan_sha256'] = _hash(data)
    receipt['published_at_utc'] = now.isoformat()
    _write_once(plan_path, data)
    _write_once(plan_path.with_suffix('.sha256'), (receipt['plan_sha256']+'  '+plan_path.name+'\n').encode())
    receipt_path = plan_path.parent.parent/'paired-protocol-receipt.json'
    _write_once(receipt_path, _json(receipt))
    return receipt_path


def verify_readiness(plan_path, *, now=None):
    """Read-only check immediately before any worker/environment creation."""
    plan_path = Path(plan_path)
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    receipt_path = plan_path.parent.parent/'paired-protocol-receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['plan_sha256'] == _hash(plan_bytes), 'Readiness/plan mismatch'
    assert receipt['qualification_sha256'] == plan['qualification_sha256']
    assert receipt['qualification_sha256'] == _hash(Path(plan['qualification_path']).read_bytes())
    assert json.loads(Path(plan['qualification_path']).read_bytes())['status'] == 'PASS'
    assert not (plan_path.parent/'opening-receipt.json').exists(), 'One-use audit already claimed'
    _time_gate(plan, receipt, now or dt.datetime.now(dt.timezone.utc))
    return receipt


def claim_once(plan_path):
    """Recheck the time gate, then claim once with exclusive creation."""
    plan_path = Path(plan_path)
    receipt = verify_readiness(plan_path)
    value = {'claimed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'plan_sha256': receipt['plan_sha256'],
             'readiness_sha256': _hash((plan_path.parent.parent/'paired-protocol-receipt.json').read_bytes()),
             'one_use': True}
    _write_once(plan_path.parent/'opening-receipt.json', _json(value))
    return value
