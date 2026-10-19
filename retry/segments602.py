"""One exact candidate: prepare directed segment operands in road margin only.

No new pruning, distance approximation, axis normalization or min reordering.
"""
import math
import struct
from types import SimpleNamespace
from unittest.mock import patch
import retry.plan513_model as original
import retry.corner515_model as full
from retry.brake506_geometry import point_segment, polygon_distance
from retry.reuse601 import freeze


def segment(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = dx * dx + dy * dy
    return (a[0], a[1], dx, dy, d)


def directed(poly):
    return tuple(segment(a, b) for a, b in zip(poly, poly[1:] + poly[:1]))


def query(p, prepared):
    ax, ay, dx, dy, d = prepared
    t = max(0., min(1., ((p[0] - ax) * dx + (p[1] - ay) * dy) / d)) if d else 0.
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def distance(a, a_edges, b, b_edges):
    # Exactly the original SAT axes/order and pa/pb arithmetic/min/max order.
    separated = False
    for p in (a, b):
        for v, w in zip(p, p[1:] + p[:1]):
            axis = (v[1] - w[1], w[0] - v[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if min(pa) > max(pb) or min(pb) > max(pa):
                separated = True
    if not separated:
        return 0.
    # Both orientations of the two-point boundary are retained: reversed
    # point-segment arithmetic may round differently and cannot be discarded.
    return min([query(p, edge) for p in a for edge in b_edges] +
               [query(p, edge) for p in b for edge in a_edges])


class Road:
    def __init__(self, mesh, index, boundary, edgeindex, already_frozen=False):
        self.args = ((mesh, index, boundary, edgeindex) if already_frozen else
                     tuple(freeze(q) for q in (mesh, index, boundary, edgeindex)))
        self.prepared = tuple((edge, directed(edge), bounds)
                              for edge, bounds in zip(self.args[2], self.args[3]))
        self.margin_calls = self.segment_pairs = 0

    def __call__(self, root, mesh, roadindex, edge, edgeindex):
        # These are owned immutable arrays established before the call.
        if not all(a is b for a, b in zip((mesh, roadindex, edge, edgeindex), self.args)):
            raise ValueError('602_IMMUTABLE_CONTEXT_IDENTITY')
        self.margin_calls += 1
        minimum = float('inf')
        for poly in original.polygons(root):
            x0 = min(x for x, y in poly); x1 = max(x for x, y in poly)
            y0 = min(y for x, y in poly); y1 = max(y for x, y in poly)
            distance_value = float('inf')
            edges = directed(poly)
            for endpoints, prepared, (u0, u1, v0, v1) in self.prepared:
                lower = math.hypot(max(0., u0 - x1, x0 - u1), max(0., v0 - y1, y0 - v1))
                if lower >= distance_value:
                    continue
                self.segment_pairs += 1
                distance_value = min(distance_value, distance(poly, edges, endpoints, prepared))
            covered = all(any(a <= x <= b and c <= y <= d and original.inside((x, y), p)
                              for (p, mu), (a, b, c, d) in zip(mesh, roadindex)) for x, y in poly)
            minimum = min(minimum, distance_value if covered else -distance_value)
        return minimum


def same(a, b):
    return struct.pack('>d', a) == struct.pack('>d', b)


def outcome(fn):
    try:
        return ('value', struct.pack('>d', fn()).hex())
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        return ('exception', type(exc).__name__)


def pure_checks(charge):
    checks = []
    point_cases = [((.3, .2), (0., 0.), (1., 0.)),
                   ((-1., 1.), (0., 0.), (1., 0.)),
                   ((2., -1.), (0., 0.), (1., 0.)),
                   ((0., 0.), (0., 0.), (0., 0.)),
                   ((-0., 0.), (0., -0.), (-0., 0.)),
                   ((.5, 0.), (1., 0.), (0., 0.)),
                   ((1.e154, -1.e154), (-1.e154, 0.), (1.e154, 0.))]
    for value in (float('nan'), float('inf'), -float('inf')):
        point_cases.extend([((value, 0.), (0., 0.), (1., 0.)),
                            ((0., 0.), (value, 0.), (1., 0.)),
                            ((0., 0.), (0., 0.), (value, 0.))])
    for p, a, b in point_cases:
        charge(2)
        assert outcome(lambda: point_segment(p, a, b)) == outcome(lambda: query(p, segment(a, b)))
    checks.append('point_query_bits_or_exception_exact_boundary_endpoint_degenerate_extreme_nonfinite_signedzero')
    square = [(-1., -1.), (1., -1.), (1., 1.), (-1., 1.)]
    pairs = [(square, [(2., -2.), (2., 2.)]),
             (square, [(1., -1.), (1., 1.)]),
             (square, [(0., -.5), (0., .5)]),
             (square, [(2., 2.), (2., 2.)]),
             ([(0., 0.)], [(-0., -0.), (0., 0.)]),
             ([], [(0., 0.), (1., 0.)]),
             (square, [(float('nan'), 0.), (float('inf'), 1.)]),
             ([(float('inf'), 0.)], [(0., 0.), (1., 0.)])]
    for a, b in pairs:
        charge(2)
        assert outcome(lambda: polygon_distance(a, b)) == outcome(lambda: distance(a, directed(a), tuple(b), directed(tuple(b))))
    checks.append('polygon_SAT_and_min_sequence_bits_or_exception_exact_including_ties_and_nonfinite')
    mesh = [(square, 1.)]
    index = ((-1., 1., -1., 1.),)
    boundary = list(zip(square, square[1:] + square[:1]))
    bounds = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in boundary]
    samples = [[[(0., 0.), (.25, 0.), (.25, .25), (0., .25)]],
               [[(1., -.2), (1., .2)]], [[(2., -.2), (2., .2)]],
               [[(0., 0.)]], [[(-0., -0.), (0., 0.)]],
               [[(float('nan'), 0.), (0., 0.)]],
               [[(float('inf'), 0.), (float('inf'), 1.)]],
               [[(0., 0.)], [(1., -.2), (1., .2)]],
               [[(1., -.2), (1., .2)], [(0., 0.)]]]
    for polys in samples:
        road = Road(mesh, index, boundary, bounds)
        with patch.object(original, 'polygons', lambda root: polys):
            charge(2)
            assert outcome(lambda: original.margin(None, *road.args)) == outcome(lambda: road(None, *road.args))
    checks.append('full_road_inside_outside_signed_min_boundary_degenerate_NaN_inf_and_polygon_order_exact')
    road = Road(mesh, index, boundary, bounds)
    with patch.object(original, 'polygons', lambda root: [[(2., -.2), (2., .2)]]):
        charge(2)
        untouched = outcome(lambda: original.margin(None, *road.args))
        mesh[0][0][0] = (999., 999.)
        assert outcome(lambda: road(None, *road.args)) == untouched
    assert isinstance(road.prepared, tuple) and all(isinstance(v, tuple) for v in road.args)
    checks.append('prepared_context_owned_immutable_and_no_alias_to_mutable_source')
    # Verify the original lower>=distance skip, tie and traversal sequence,
    # without introducing any new excluded candidate.
    mesh2 = [([(-3., -3.), (3., -3.), (3., 3.), (-3., 3.)], 1.)]
    edges2 = [((1., -2.), (1., 2.)), ((-1., -2.), (-1., 2.)),
              ((2., -2.), (2., 2.)), ((-0., -0.), (0., 0.))]
    bounds2 = [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in edges2]
    r = Road(mesh2, ((-3., 3., -3., 3.),), edges2, bounds2)
    visits = [[], []]
    real_old = original.polygon_distance
    real_new = distance
    def trace_old(a, b):
        visits[0].append(freeze(b)); return real_old(a, b)
    def trace_new(a, ae, b, be):
        visits[1].append(freeze(b)); return real_new(a, ae, b, be)
    with patch.object(original, 'polygons', lambda root: [[(0., 0.)]]), \
         patch.object(original, 'polygon_distance', trace_old), patch(__name__ + '.distance', trace_new):
        charge(2)
        assert same(original.margin(None, *r.args), r(None, *r.args))
    assert visits[0] == visits[1]
    checks.append('existing_lower_bound_skip_ties_and_segment_visit_order_unchanged_no_new_pruning')
    # Artificial boundary/coverage separation makes +0 and -0 coexist, so the
    # first-equal min behavior is observable independently of real road maps.
    zero_mesh = [([(.5, -.5), (1.5, -.5), (1.5, .5), (.5, .5)], 1.)]
    zero_edges = [((0., -1.), (0., 1.)), ((1., -1.), (1., 1.))]
    zero_bounds = [(0., 0., -1., 1.), (1., 1., -1., 1.)]
    zr = Road(zero_mesh, ((.5, 1.5, -.5, .5),), zero_edges, zero_bounds)
    for polys, sign in [([[(1., 0.)], [(0., 0.)]], 1.),
                        ([[(0., 0.)], [(1., 0.)]], -1.)]:
        with patch.object(original, 'polygons', lambda root: polys):
            charge(2)
            a = original.margin(None, *zr.args); b = zr(None, *zr.args)
            assert same(a, b) and a == 0. and math.copysign(1., a) == sign
    for m in (zero_mesh, []):
        empty = Road(m, ((.5, 1.5, -.5, .5),) if m else (), [], [])
        with patch.object(original, 'polygons', lambda root: [[(1., 0.)]]):
            charge(2)
            assert outcome(lambda: original.margin(None, *empty.args)) == outcome(lambda: empty(None, *empty.args))
    checks.append('outside_negativezero_and_first_equal_signedzero_min_plus_empty_boundary_infinities_exact')
    return dict(passed=True, checks=checks, synthetic_comparisons=len(point_cases) + len(pairs) + len(samples) + 6,
                model=0, force=0, chooser=0, native=0)
