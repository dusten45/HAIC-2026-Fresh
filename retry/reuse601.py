"""One candidate: memoize the pure full-vehicle margin on immutable geometry.

No controller/dynamics/report/gate edits. Every logical geometry query is still
charged by the original source_geometry/check wrappers before this function.
"""
from dataclasses import replace
from types import SimpleNamespace
import struct
import retry.timing600 as base

DESIGN = dict(target='Repeated full body/road/obstacle margin; dominant instrumented geometry family',
              evidence='919 corner515.margin calls cumulative16.288s, road margin15.770s; point_segment4485256 calls cumulative4.974s. These are overlapping profiled times, not normal latency.',
              change='One fresh per-choose memo of exact full margin. Key contains every input used by plan513.polygons: center, planar.angle, levers and each wheel.heading, preserving finite binary64 type/signedzero. Geometry context is recursively immutable and privately owned. All other root fields are unused by polygons/margin. On miss call the original margin with unchanged arithmetic/control-flow order; on hit reuse that exact immutable float. All original logical query counters/admission/body/force gates execute.',
              boundaries='Cache only one choose, maximum5000 keys, no history/action/report/control state in entries, clear on exit. Other geometry projection/contact/physics functions unchanged. Geometry budget counts logical queries including cache hits.')


def freeze(value):
    if isinstance(value, (tuple, list)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, (int, float, bool, str)) or value is None:
        return value
    raise TypeError('MARGIN_CONTEXT_NOT_RECURSIVELY_IMMUTABLE')


def geometry_key(root):
    # Exact dependency set of the unchanged plan513_model.polygons.
    p = root.planar
    return base.exact_key((root.center, p.angle, p.levers,
                           tuple(w.heading for w in p.linear.wheels)))


class Cache:
    def __init__(self, meter):
        self.meter = meter
        self.original = meter.original_margin
        self.old_static = meter.static
        self.old_edges = meter.source_edges
        meter.static = dict(meter.static,
                            roads=freeze(meter.static['roads']),
                            boundary=freeze(meter.static['boundary']),
                            obstacles=freeze(meter.static['obstacles']))
        meter.source_edges = freeze(meter.source_edges)
        self.args = (meter.static['roads'], meter.source_index,
                     meter.static['boundary'], meter.source_edges,
                     meter.static['obstacles'])
        assert all(freeze(v) == v for v in self.args)
        self.entries = {}
        self.hits = self.misses = 0
        meter.original_margin = self.margin

    def margin(self, root, *args):
        if len(args) != len(self.args) or any(a is not b for a, b in zip(args, self.args)):
            raise ValueError('MARGIN_CONTEXT_CHANGED')
        key = geometry_key(root)
        if key in self.entries:
            self.hits += 1
            return self.entries[key]
        if len(self.entries) >= 5000:
            raise base.old.CostStop('IMMUTABLE_MARGIN_CACHE5000')
        self.misses += 1
        result = self.original(root, *args)
        if not isinstance(result, float):
            raise TypeError('MARGIN_RESULT_NOT_IMMUTABLE_FLOAT')
        self.entries[key] = result
        return result

    def statistics(self):
        return dict(hits=self.hits, misses=self.misses, entries=len(self.entries),
                    logical_queries=self.hits + self.misses,
                    cache_lifetime='ONE_CHOOSE_ONLY', result_values='IMMUTABLE_FLOAT',
                    geometry_context='OWNED_RECURSIVE_TUPLES')

    def restore(self):
        self.meter.original_margin = self.original
        self.meter.static = self.old_static
        self.meter.source_edges = self.old_edges
        self.entries.clear()


def install():
    # install_meters has already bound this exact call's source_geometry.
    meter = base.old.tracking.margin.__self__
    return Cache(meter)


def pure_checks():
    """Pure synthetic function stand-ins only, no geometry/model evaluator."""
    checks = []
    calls = []
    def owner():
        def original(root, *args):
            calls.append((root.center, args))
            return root.center[0]
        return SimpleNamespace(original_margin=original,
            static=dict(roads=[[[[0., 0.], [1., 0.]], 1.]],
                        boundary=[[[0., 0.], [1., 0.]]], obstacles=[[[2., 2.], 1.]]),
            source_index=((0., 1., 0., 0.),), source_edges=[[0., 1., 0., 0.]])
    root = SimpleNamespace(center=(1., 2.), planar=SimpleNamespace(angle=.1,
        levers=((0., 1.),), linear=SimpleNamespace(wheels=(SimpleNamespace(heading=.2),))))
    a = owner()
    c = Cache(a)
    assert c.margin(root, *c.args) == 1.
    assert c.margin(root, *c.args) == 1. and len(calls) == 1 and c.hits == 1
    checks.append('identical_geometry_reuses_exact_original_float')
    source_roads = c.old_static['roads']
    source_roads[0][0][0][0] = 999.
    assert c.args[0][0][0][0][0] == 0.
    try:
        c.args[0][0][0][0][0] = 4.
    except TypeError:
        pass
    else:
        raise AssertionError('MUTABLE_CONTEXT')
    checks.append('context_owned_and_nested_immutable_no_source_alias')
    positive = SimpleNamespace(center=(0., 2.), planar=root.planar)
    negative = SimpleNamespace(center=(-0., 2.), planar=root.planar)
    assert geometry_key(positive) != geometry_key(negative)
    assert struct.pack('>d', c.margin(positive, *c.args)) != struct.pack('>d', c.margin(negative, *c.args))
    checks.append('signedzero_and_exact_float_bits_preserved')
    changed = SimpleNamespace(center=(3., 2.), planar=root.planar)
    assert c.margin(changed, *c.args) == 3.
    assert c.margin(root, *c.args) == 1.
    checks.append('distinct_root_and_return_to_prior_trial_do_not_leak_result')
    b = owner()
    d = Cache(b)
    assert not d.entries and d.margin(root, *d.args) == 1. and d.hits == 0
    assert d.entries is not c.entries
    checks.append('fresh_call_has_separate_empty_cache_no_history_state')
    for key, value in c.entries.items():
        assert isinstance(key, tuple) and isinstance(value, float)
    checks.append('cache_contains_only_structural_keys_and_immutable_scalar_results')
    try:
        c.margin(root, *d.args)
    except ValueError:
        pass
    else:
        raise AssertionError('CHANGED_CONTEXT_NOT_REJECTED')
    checks.append('foreign_geometry_context_is_rejected')
    c.restore()
    d.restore()
    assert not c.entries and not d.entries and a.static is c.old_static
    checks.append('restore_clears_all_entries_and_restores_owner')
    return dict(passed=True, checks=checks, chooser=0, geometry_evaluator=0,
                model=0, force=0, native=0), 0
