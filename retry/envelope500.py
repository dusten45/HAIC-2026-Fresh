"""One frozen forward scalar envelope. Pure arithmetic; no simulator/controller imports.

Nodes and state are diagnostic inputs, not a pixel-observation policy. Exact
rational residuals certify binary64 selection, not physical tyre feasibility.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import math
import struct

MASS = 29.249793766661764
REAR = 35.0188778925416
BRAKE = 91.16873397261595
TIMES = (Q(1, 50), Q(2, 50), Q(3, 50), Q(4, 50))
TAU = TIMES[-1]


class EnvelopeStop(ValueError):
    pass


def rational(x):
    if not isinstance(x, (float, int)) or isinstance(x, bool) or not math.isfinite(x):
        raise EnvelopeStop('NONFINITE_OR_NONSCALAR')
    return Q(x)


def context(s, v, sigma, arcs, speeds):
    s, v, sigma = map(rational, (s, v, sigma))
    arcs, speeds = tuple(map(rational, arcs)), tuple(map(rational, speeds))
    if len(arcs) != len(speeds) or len(arcs) < 2 or arcs[0] != 0 or any(b <= a for a, b in zip(arcs, arcs[1:])):
        raise EnvelopeStop('NODE_DOMAIN')
    if speeds[0] != 0 or any(r <= 0 for r in speeds[1:]):
        raise EnvelopeStop('NODE_SPEED_DOMAIN')
    if s == arcs[-1]:
        raise EnvelopeStop('TERMINAL_HANDOFF_NO_ACTION')
    if not 0 < s < arcs[-1]:
        raise EnvelopeStop('FIRST_LAP_DOMAIN_NO_WRAP')
    if v < 0 or sigma < 0:
        raise EnvelopeStop('REVERSE_OR_NEGATIVE_SPEED')
    # Source map's speed+2.7 is an actual binary64 intermediate, retained here.
    shift = float(v) + 2.7
    if not math.isfinite(shift):
        raise EnvelopeStop('NUMERIC_DOMAIN')
    A = min(Q(REAR), Q(80000) / (Q(MASS) * Q(shift)))
    low = max(-Q(BRAKE), -v / TAU, -sigma / TAU)
    nodes = tuple((x-s, r) for x, r in zip(arcs[1:], speeds[1:]) if x >= s)
    return dict(s=s, v=v, sigma=sigma, low=low, high=A, nodes=nodes, L=arcs[-1])


def residuals(c, a):
    """Independent exact polynomial oracle, no quadratic roots or sqrt.

    Crossed: sqrt(sigma²+2ad)<=r-v+sigma, with nonnegative RHS.
    Uncrossed: (v+at)²<=r²+2B(d-sigma*t-a*t²/2).
    Equality belongs to crossed branch; both predicates agree on the seam.
    """
    a = a if isinstance(a, Q) else rational(a)
    failures = []
    if not c['low'] <= a <= c['high']:
        failures.append('ACCEL_OR_NONNEGATIVE_DOMAIN')
    v, sigma, B = c['v'], c['sigma'], Q(BRAKE)
    for i, (d, r) in enumerate(c['nodes']):
        if d == 0:
            if v > r:
                failures.append(('CURRENT_NODE', i))
            continue
        for k, t in enumerate(TIMES):
            travel = sigma*t + a*t*t/2
            if travel >= d:
                z = r-v+sigma
                discriminant = sigma*sigma + 2*a*d
                if z < 0 or discriminant < 0 or discriminant > z*z:
                    failures.append(('CROSSED', i, k))
            else:
                E = (v+a*t)**2-r*r-2*B*(d-travel)
                if E > 0:
                    failures.append(('UNCROSSED', i, k))
    return failures


def _decimal(q):
    return Decimal(q.numerator)/Decimal(q.denominator)


def _bound(c):
    """Algebraic partition at each crossing switch; intersection upper bound.

    On the uncrossed branch E'(a)=2t(v+at)+Bt²>0. On the crossed
    branch crossing speed v-sigma+sqrt(sigma²+2ad) is nondecreasing.
    They meet continuously at travel=d. Thus each feasible set is downward
    closed within [low,high]; all-node intersection has no skipped islands.
    """
    with localcontext() as dc:
        dc.prec = 80
        lo, hi = _decimal(c['low']), _decimal(c['high'])
        v, sigma, B = map(_decimal, (c['v'], c['sigma'], Q(BRAKE)))
        cuts = []
        for i, (dq, rq) in enumerate(c['nodes']):
            if dq == 0:
                continue  # exact lower-end check already handles current node
            d, r = _decimal(dq), _decimal(rq)
            for k, tq in enumerate(TIMES):
                t = _decimal(tq)
                switch = 2*(d-sigma*t)/(t*t)
                # Switch speed is nonnegative when switch lies in domain.
                if switch <= lo or (switch < hi and v+switch*t <= r):
                    z = r-v+sigma
                    if z < 0:
                        raise EnvelopeStop('EMPTY_SET')
                    cut = ((r-v)*(2*sigma+r-v))/(2*d)
                    branch = 'crossed'
                else:
                    bb = 2*v*t+B*t*t
                    cc = v*v-r*r-2*B*(d-sigma*t)
                    disc = bb*bb-4*t*t*cc
                    if disc < 0:
                        raise EnvelopeStop('ROOT_DISCRIMINANT')
                    # Stable larger quadratic root; bb>0 because B,t>0.
                    cut = -2*cc/(bb+disc.sqrt())
                    branch = 'uncrossed'
                # Roots outside their branch only occur above the whole domain;
                # they cannot cut hi. Certify final representable answer below.
                upper = min(hi, cut)
                cuts.append((i, k, branch, str(switch), str(cut)))
                hi = upper
        return lo, hi, cuts


def solve(s, v, sigma, arcs, speeds):
    c = context(s, v, sigma, arcs, speeds)
    if residuals(c, c['low']):
        raise EnvelopeStop('EMPTY_SET')
    first = float(c['low'])
    if Q(first) < c['low']:
        first = math.nextafter(first, math.inf)
    if residuals(c, first):
        raise EnvelopeStop('EMPTY_BINARY64')
    lo, upper, cuts = _bound(c)
    a = float(upper)
    if not math.isfinite(a):
        raise EnvelopeStop('NUMERIC_DOMAIN')
    # Decimal is a root approximation, never the feasibility authority. Exact
    # oracle picks the greatest feasible binary64 within bounded ULP repair.
    adjustments = 0
    while residuals(c, a):
        a = math.nextafter(a, -math.inf)
        adjustments += 1
        if adjustments > 8:
            raise EnvelopeStop('ROOT_ROUNDING_CERTIFICATE')
    for _ in range(9):
        nxt = math.nextafter(a, math.inf)
        if residuals(c, nxt):
            break
        a = nxt
        adjustments += 1
    else:
        raise EnvelopeStop('MAXIMALITY_CERTIFICATE')
    assert not residuals(c, a) and residuals(c, math.nextafter(a, math.inf))
    return dict(accel=a, next_float=math.nextafter(a, math.inf), algebraic_upper=str(upper),
                interval_lower=str(c['low']), interval_upper=str(upper),
                partitions=len(cuts), ulp_adjustments=adjustments,
                maximal_binary64_certified=True), c


def float32(x):
    return struct.unpack('!f', struct.pack('!f', x))[0]


def next32(x, up):
    # Pedals use only nonnegative finite float32 in[0,1]. Zero has one owner.
    if not 0 <= x <= 1 or float32(x) != x:
        raise EnvelopeStop('PEDAL_BITS')
    if x == 0:
        x = 0.  # signed zero has one nonnegative pedal owner
    bits = struct.unpack('!I', struct.pack('!f', x))[0]
    if (up and x == 1) or (not up and x == 0):
        return None
    return struct.unpack('!f', struct.pack('!I', bits+(1 if up else -1)))[0]


def source_pedals(a, v):
    # Same finite-source operations as scalar392_audit.pedals; AST-isolated
    # comparison in verification avoids importing its unrelated audit driver.
    cmd = min(REAR, max(-BRAKE, a))
    gas = min(1., max(0., MASS*max(cmd, 0)*(v+2.7)/80000))
    brake = min(1., max(0., MASS*max(-cmd, 0)/(4*1.6*15/(.02*.54))))
    return gas, brake


def decode_pedals(gas, brake, v):
    if gas and brake:
        raise EnvelopeStop('SIMULTANEOUS_PEDALS')
    return (80000*gas/(MASS*(v+2.7)) if gas else
            -brake*(4*1.6*15/(.02*.54))/MASS if brake else 0.)


def command(solution, c, steer):
    steer = float32(float(rational(steer)))
    if not -.4 <= steer <= .4:
        # Source float32 bound .4 is slightly above mathematical .4.
        if abs(steer) != float32(.4):
            raise EnvelopeStop('STEERING_BOUNDS')
    a, v = solution['accel'], float(c['v'])
    gas, brake = map(float32, source_pedals(a, v))
    mode = 'gas' if a >= 0 else 'brake'
    def effective(g, b): return decode_pedals(g, b, v)
    repaired = 0
    while residuals(c, effective(gas, brake)):
        # Move toward less acceleration in the same one-pedal family. No new
        # policy fallback; an unrepresentable feasible interval stops.
        z = next32(gas if mode == 'gas' else brake, mode == 'brake')
        if z is None or repaired >= 8:
            raise EnvelopeStop('FLOAT32_MAPPING_EMPTY_OR_UNCERTIFIED')
        if mode == 'gas': gas = z
        else: brake = z
        repaired += 1
    # Verify maximal representable pedal for this fixed scalar map as well.
    for _ in range(9):
        z = next32(gas if mode == 'gas' else brake, mode == 'gas')
        if z is None: break
        ng, nb = (z, brake) if mode == 'gas' else (gas, z)
        if residuals(c, effective(ng, nb)): break
        gas, brake = ng, nb
        repaired += 1
    else:
        raise EnvelopeStop('FLOAT32_MAPPING_MAXIMALITY')
    mapped = effective(gas, brake)
    return dict(action=[steer, gas, brake], scalar_mapped_accel=mapped,
                scalar_mapping_error=mapped-a, float32_ulp_adjustments=repaired,
                scalar_feasible=True, physical_tyre_feasible_claimed=False)


def act(nominal, phase, s, v, sigma, arcs, speeds):
    """Pure caller boundary: preserve steering; no memory/state mutation.

    Caller invokes frozen SourceC nominal once, then supplies its FIRST_LAP
    observation and immutable P4. FINISH_CONFIRM must use existing qualified
    law, so this function refuses to manufacture a terminal action.
    """
    if phase != 'FIRST_LAP':
        raise EnvelopeStop('EXISTING_PHASE_HANDOFF')
    if len(nominal) != 3:
        raise EnvelopeStop('NOMINAL_SHAPE')
    for x in nominal:
        rational(x)
    if not (-float32(.4) <= nominal[0] <= float32(.4) and 0 <= nominal[1] <= 1 and 0 <= nominal[2] <= 1):
        raise EnvelopeStop('NOMINAL_BOUNDS')
    solution, c = solve(s, v, sigma, arcs, speeds)
    result = command(solution, c, nominal[0])
    result['selection'] = solution
    return result
