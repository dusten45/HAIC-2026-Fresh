"""Frozen early-feedback experiment interfaces; no integration or geometry."""
import ast
import inspect
import numpy as np
from unittest.mock import patch
from retry.corner608_core import make_pairs, signature


def proposal(root, high, progress, nominal):
    a = nominal(root, high, progress)
    assert a.dtype == np.float32 and a.shape == (3,) and np.isfinite(a).all()
    return a.copy()


def require_equal(actual, expected, digest):
    assert digest(actual) == digest(expected), '609_ZERO_IDENTITY'


def select(entries):
    safe = [q for q in entries if q['report']['ok']]
    if not safe:
        return None
    return min(safe, key=lambda q: (-q['end_progress'], -q['first4_progress'], q['index']))


def batch(nominal, modified, certify, reserve, record):
    pairs, grid = make_pairs(nominal, modified)
    entries = []
    for i, q in enumerate(pairs):
        reserve(len(pairs) - i)
        a = q['action'].copy()
        report, end, first = certify(a)
        assert a.tobytes() == q['action'].tobytes()
        e = dict(q, report=report, end_progress=end, first4_progress=first)
        entries.append(e)
        record(e)
    best = select(entries)
    if best is None:
        return None, None, entries
    reserve(0)
    a = best['action'].copy()
    final, end, first = certify(a)
    assert final['ok'] and a.tobytes() == best['action'].tobytes()
    assert (end, first) == (best['end_progress'], best['first4_progress'])
    return a, final, entries


def pure_checks(tracking, clones, budgets):
    # The actual original537 function is executed only with synthetic providers.
    tree = ast.parse(inspect.getsource(tracking.choose))
    first = tree.body[0].body[0]
    assert isinstance(first, ast.Assign) and isinstance(first.value, ast.Call)
    assert first.value.func.id == 'nominal'
    a = np.asarray([.1, .54321, 0], np.float32)
    b = np.asarray([.11, .65432, 0], np.float32)
    nominal_calls = []
    def nominal(*args):
        nominal_calls.append(args)
        return a.copy()
    with patch.object(tracking, 'nominal', nominal), patch.object(tracking, 'backup', lambda *a: np.zeros(3, np.float32)), patch.object(tracking, 'certifier', lambda *a, **k: lambda action: {'ok': True}):
        proposed = proposal('root', 'high', 1., tracking.nominal)
        chosen, report = tracking.choose('root', 'high', 'low', 1., [0], {'forecast_calls': 0}, geometry={})
        assert proposed[0].tobytes() == chosen[0].tobytes() and len(nominal_calls) == 2
    with patch.object(tracking, 'nominal', nominal), patch.object(tracking, 'backup', lambda *a: np.zeros(3, np.float32)), patch.object(tracking, 'certifier', lambda *a, **k: lambda action: {'ok': False}):
        chosen, report = tracking.choose('root', 'high', 'low', 1., [0], {'forecast_calls': 0}, geometry={})
        assert chosen is None
    seen = []
    def certify(x):
        seen.append(x.tobytes())
        return {'ok': x[0].tobytes() == b[0].tobytes()}, 2., 1.
    chosen, final, entries = batch(a, b, certify, lambda n: None, lambda q: None)
    assert chosen is not None and final['ok'] and len(seen) == 43
    assert len(make_pairs(a, a)[0]) == 20  # current nominal pedal + original19
    chosen, final, entries = batch(a, a, lambda x: ({'ok': True}, float(x[1]-x[2]), 0.), lambda n: None, lambda q: None)
    assert chosen[1] == 1.  # zero lateral residual still uses time-oriented grid
    tie = [dict(index=3, report={'ok': True}, end_progress=2., first4_progress=1.),
           dict(index=2, report={'ok': True}, end_progress=2., first4_progress=2.),
           dict(index=1, report={'ok': True}, end_progress=2., first4_progress=2.)]
    assert select(tie)['index'] == 1 and select([]) is None
    try:
        batch(a, b, lambda x: (_ for _ in ()).throw(IOError('stub')), lambda n: None, lambda q: None)
    except IOError:
        pass
    else:
        raise AssertionError('TECHNICAL_ERROR_SWALLOWED')
    require_equal({'history': [1, 2]}, {'history': [1, 2]}, lambda x: x)
    try:
        require_equal({'history': [1, 2]}, {'history': [1, 3]}, lambda x: x)
    except AssertionError:
        pass
    else:
        raise AssertionError('ZERO_MISMATCH_NOT_REJECTED')
    clones(); budgets()
    return dict(passed=True, checks=['nominal_original537_AST_and_synthetic_call_parity',
        'original537_no_safe_does_not_gate_C', 'same_dynamic_grid_dedup_and_order608',
        'end48_then_first4_then_fixed_index', 'fresh_FINAL_selected_pair',
        'zero_residual_still_time_pedal_grid', 'independent_clones',
        'zero_arm_stored_identity_comparator', 'full_budget_reservation',
        'technical_IO_whole_stop_no_retry'], model=0, force=0, geometry=0, native=0)
