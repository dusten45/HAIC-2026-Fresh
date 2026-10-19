"""Frozen six-coefficient spatial residual, no evaluation or adaptation."""
import math
import numpy as np
from retry.lap518_control import point_at

KNOTS = (80., 100., 130., 160., 190., 220.)


def smooth(u):
    u = max(0., min(1., u))
    return u * u * (3. - 2. * u)


def window(s, a, b):
    if not a < s < b:
        return 0.
    mid = (a + b) / 2
    return smooth((s - a) / (mid - a)) if s <= mid else smooth((b - s) / (b - mid))


def offset(s, coeff):
    if not 80. < s < 220.:
        return 0.
    values = (0., *coeff[:4], 0.)
    i = next(i for i in range(5) if s <= KNOTS[i + 1])
    f = smooth((s - KNOTS[i]) / (KNOTS[i + 1] - KNOTS[i]))
    return values[i] + f * (values[i + 1] - values[i])


def family():
    h = [[1]]
    for _ in range(3):
        h = [r + r for r in h] + [r + [-x for x in r] for r in h]
    return [('zero', [0.] * 6)] + [
        ('H' + str(i), [row[j] * (.20 if j < 5 else .025) for j in range(1, 7)])
        for i, row in enumerate(h)]


def target(s, path):
    p = point_at(s, path)
    u = s % path['length']
    i = next((i for i in range(len(path['ds'])) if path['arcs'][i + 1] >= u), len(path['ds']) - 1)
    a = path['points'][i]; b = path['points'][(i + 1) % len(path['points'])]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    return p, (-dy / length, dx / length)


def pp(root, p):
    dx, dy = p[0] - root.center[0], p[1] - root.center[1]
    den = dx * dx + dy * dy
    if not den > 0 or not math.isfinite(den):
        raise ValueError('604_PP_DOMAIN')
    a = root.planar.angle
    delta = math.atan(3.24 * 2 * (-math.sin(a) * dy - math.cos(a) * dx) / den)
    return float(np.float32(-max(-.4, min(.4, delta))))


def action(root, path, progress, incumbent, coeff, project, get_target):
    # Byte-preserving exits avoid all float arithmetic on the incumbent.
    if not any(coeff) or not 80. < progress < 220.:
        return incumbent.copy(), dict(offset=0., pedal_residual=0., byte_exit=True)
    lateral = offset(progress, coeff)
    pedal = coeff[4] * window(progress, 80., 140.) + coeff[5] * window(progress, 140., 220.)
    out = incumbent.copy()
    if lateral != 0.:
        q = project(root.center, path, progress)
        s = q['s'] + max(7., .3 * math.hypot(*root.planar.linear.velocity))
        p, normal = get_target(s, path)
        shifted = tuple(p[j] + lateral * normal[j] for j in range(2))
        residual = pp(root, shifted) - pp(root, p)
        limit = float(np.float32(.4))
        out[0] = np.float32(max(-limit, min(limit, float(incumbent[0]) + residual)))
    if pedal != 0.:
        old = float(incumbent[1]) if incumbent[1] > 0 else -float(incumbent[2])
        u = float(np.float32(max(-1., min(1., old + pedal))))
        out[1:] = (max(0., u), max(0., -u))
    return out, dict(offset=lateral, pedal_residual=pedal, byte_exit=False)


def pure_checks():
    f = family()
    assert len(f) == 9 and len({tuple(c) for _, c in f}) == 9
    signs = np.asarray([[int(np.sign(v)) for v in c] for _, c in f[1:]])
    assert np.array_equal(signs.T @ signs, 8 * np.eye(6, dtype=int))
    assert all(abs(c[j]) == (.2 if j < 4 else .025) for _, c in f[1:] for j in range(6))
    for _, c in f:
        assert offset(80., c) == offset(220., c) == 0.
        assert all(offset(s, c) == c[i] for i, s in enumerate(KNOTS[1:-1]))
        assert all(abs(offset(s, c)) <= .200000000000001 for s in range(60, 241))
    assert window(80., 80., 140.) == window(140., 80., 140.) == 0.
    assert window(110., 80., 140.) == window(180., 140., 220.) == 1.
    from types import SimpleNamespace
    root = SimpleNamespace(center=(0., 0.), planar=SimpleNamespace(angle=0., linear=SimpleNamespace(velocity=(0., 10.))))
    a = np.array([-.0, .3, -.0], np.float32)
    def forbidden(*args):
        raise AssertionError('UNEXPECTED_GEOMETRY_IN_ZERO_EXIT')
    for s, c in [(110., f[0][1]), (80., f[1][1]), (220., f[1][1]), (400., f[1][1])]:
        b, _ = action(root, {}, s, a, c, forbidden, forbidden)
        assert b.tobytes() == a.tobytes() and b is not a
    b, _ = action(root, {}, 110., a, f[1][1], lambda *a: {'s': 110.}, lambda *a: ((0., 10.), (-1., 0.)))
    assert b.dtype == np.float32 and abs(float(b[0])) <= float(np.float32(.4)) and 0 <= b[1] <= 1 and b[1] * b[2] == 0
    assert a.tobytes() == np.array([-.0, .3, -.0], np.float32).tobytes()
    return dict(passed=True, checks=['Hadamard8_columns2to7_fixed_order', 'amplitudes_and_smoothstep_knots',
        'two_fixed_C1_midpoint_windows', 'zero_and_outside_preserve_all_float32_bytes',
        'no_mutation_or_forecast_history', 'actuator_saturation_and_exclusive_pedals'],
        chooser=0, model=0, force=0, geometry_evaluator=0)
