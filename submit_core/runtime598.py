"""Original598 calculation core with explicit state inputs, not an Agent.

No observation adapter or episode data is provided. Cached test snapshots are
injected by an external private harness only. This module has no simulator,
research-driver, file, compiler or process dependencies.
"""
import math
import struct
from dataclasses import dataclass, replace, asdict
import numpy as np
from types import MappingProxyType

DT, POWER, INERTIA, RADIUS, STIFFNESS = .02, 40000., 1.6, .54, 82.
MASS = 29.249793766661764
REAR = 35.0188778925416
BRAKE = 91.16873397261595
MAX_MODEL_TICKS = 200000
HORIZON = 12
EXTERNAL_ADMISSION = 1.06
FORCE_BUFFER = .001
ADMISSION = EXTERNAL_ADMISSION-FORCE_BUFFER
TRACKING_RESERVE = .15
FOOTPRINT_ADMISSION = .50
LAP_QUALIFICATION_RATIO = .95
MIN_FORWARD_CROSSING_SPEED = 1e-4
MAX_LATERAL_TO_FORWARD_RATIO = 4.


SIZE = 0.02

WHEELPOS = [(-55, +80), (+55, +80), (-55, -82), (+55, -82)]

HULL_POLY1 = [(-60, +130), (+60, +130), (+60, +110), (-60, +110)]

HULL_POLY2 = [(-15, +120), (+15, +120), (+20, +20), (-20, 20)]

HULL_POLY3 = [(+25, +20), (+50, -10), (+50, -40), (+20, -90), (-20, -90), (-50, -40), (-50, -10), (-25, +20)]

HULL_POLY4 = [(-50, -120), (+50, -120), (+50, -90), (-50, -90)]

@dataclass(frozen=True)
class Wheel:
    omega: float
    gas: float = 0.0
    heading: float = 0.0
    friction: float = 400.0
    offset: tuple = (0.0, 0.0)


@dataclass(frozen=True)
class State:
    velocity: tuple
    wheels: tuple
    mass: float
    engine_multiplier: float = 1.0


def wheel_response(wheel, velocity, gas, brake, engine_multiplier=1.0):
    """One actual-source-ordered force evaluation, before a world step."""
    forward = (-math.sin(wheel.heading), math.cos(wheel.heading))
    side = (forward[1], -forward[0])
    vx, vy = (velocity[j] + wheel.offset[j] for j in range(2))
    vf = forward[0] * vx + forward[1] * vy
    vs = side[0] * vx + side[1] * vy
    omega_drive = wheel.omega + DT * POWER * engine_multiplier * gas / INERTIA / (abs(wheel.omega) + 5.0)
    if brake >= 0.9:
        omega_braked = 0.0
    elif brake > 0:
        omega_braked = omega_drive - math.copysign(min(15.0 * brake, abs(omega_drive)), omega_drive)
    else:
        omega_braked = omega_drive
    raw_f, raw_p = (STIFFNESS * (omega_braked * RADIUS - vf), -STIFFNESS * vs)
    magnitude = math.hypot(raw_f, raw_p)
    scale = min(1.0, wheel.friction / magnitude) if magnitude else 1.0
    force, lateral = (raw_f * scale, raw_p * scale)
    after = replace(wheel, omega=omega_braked - DT * force * RADIUS / INERTIA, gas=gas)
    return (after, (force * forward[0] + lateral * side[0], force * forward[1] + lateral * side[1]), {'omega_drive': omega_drive, 'omega_braked': omega_braked, 'longitudinal_force': force, 'lateral_force': lateral, 'clipped': magnitude > wheel.friction})


@dataclass(frozen=True)
class Planar:
    linear: object
    levers: tuple
    inertia: float
    angular_momentum: float
    yaw: float
    angle: float
    joints: tuple
    rates: tuple
    wheel_inertias: tuple
    steer: float
    steering_multiplier: float = 1.0


def step(state, brake):
    items = [wheel_response(w, state.linear.velocity, 0.0, brake, state.linear.engine_multiplier) for w in state.linear.wheels]
    velocity = tuple((state.linear.velocity[j] + DT * sum((x[1][j] for x in items)) / state.linear.mass for j in range(2)))
    torque = sum((r[0] * x[1][1] - r[1] * x[1][0] for r, x in zip(state.levers, items)))
    momentum = state.angular_momentum + DT * torque
    rates = tuple((math.copysign(min(50.0 * abs(state.steer - q), 3.0), state.steer - q) * state.steering_multiplier if i < 2 and state.steer != q else 0.0 for i, q in enumerate(state.joints)))
    yaw = (momentum - sum((I * r for I, r in zip(state.wheel_inertias, rates)))) / state.inertia
    delta = DT * yaw
    c, s = (math.cos(delta), math.sin(delta))
    levers = tuple(((c * x - s * y, s * x + c * y) for x, y in state.levers))
    joints = tuple((max(-0.4, min(0.4, q + DT * r)) for q, r in zip(state.joints, rates)))
    angle = state.angle + delta
    wheels = tuple((replace(x[0], heading=angle + q, offset=(-yaw * r[1], yaw * r[0])) for x, q, r in zip(items, joints, levers)))
    return replace(state, linear=replace(state.linear, velocity=velocity, wheels=wheels), levers=levers, angular_momentum=momentum, yaw=yaw, angle=angle, joints=joints, rates=rates)


@dataclass(frozen=True)
class Geometry:
    planar: object
    center: tuple
    roads: tuple
    current_contacts: tuple
    floor: float
    skin: float


def point_segment(p, a, b):
    dx, dy = (b[0] - a[0], b[1] - a[1])
    d = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / d)) if d else 0.0
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def polygon_distance(a, b):
    separated = False
    for p in (a, b):
        for v, w in zip(p, p[1:] + p[:1]):
            axis = (v[1] - w[1], w[0] - v[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if min(pa) > max(pb) or min(pb) > max(pa):
                separated = True
    if not separated:
        return 0.0
    return min([point_segment(p, u, v) for p in a for u, v in zip(b, b[1:] + b[:1])] + [point_segment(p, u, v) for p in b for u, v in zip(a, a[1:] + a[:1])])


def rectangle(center, angle):
    c, s = (math.cos(angle), math.sin(angle))
    return [(center[0] + c * x - s * y, center[1] + s * x + c * y) for x, y in ((-0.28, -0.54), (0.28, -0.54), (0.28, 0.54), (-0.28, 0.54))]


def contacts(footprint, roads, skin):
    return tuple((i for i, (polygon, coefficient) in enumerate(roads) if polygon_distance(footprint, polygon) <= skin))


def bounds(roads):
    return tuple(((min((x for x, y in p)), max((x for x, y in p)), min((y for x, y in p)), max((y for x, y in p))) for p, c in roads))


def indexed_contacts(footprint, roads, index, skin):
    x0 = min((p[0] for p in footprint))
    x1 = max((p[0] for p in footprint))
    y0 = min((p[1] for p in footprint))
    y1 = max((p[1] for p in footprint))
    result = []
    for i, (a, b, c, d) in enumerate(index):
        if x1 + skin < a or b + skin < x0 or y1 + skin < c or (d + skin < y0):
            continue
        if contacts(footprint, (roads[i],), skin):
            result.append(i)
    return tuple(result)


def inside(p, poly):
    signs = [(b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) for a, b in zip(poly, poly[1:] + poly[:1])]
    return min(signs) >= 0.0 or max(signs) <= 0.0


def boundary_index(boundary):
    return [(min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in boundary]


def _base_tick(root, gas, brake, index, counter):
    counter[0] += 1
    if counter[0] > MAX_MODEL_TICKS:
        raise RuntimeError('MODEL_TICK_CAP')
    p = root.planar
    memberships = tuple((indexed_contacts(rectangle(tuple((root.center[j] + r[j] for j in range(2))), w.heading), root.roads, index, root.skin) for r, w in zip(p.levers, p.linear.wheels)))
    gases = tuple((w.gas + min(0.1, gas - w.gas) if i >= 2 else w.gas for i, w in enumerate(p.linear.wheels)))
    driven = tuple((replace(w, omega=w.omega + DT * 40000 * p.linear.engine_multiplier * g / 1.6 / (abs(w.omega) + 5.0)) for w, g in zip(p.linear.wheels, gases)))
    p = step(replace(p, linear=replace(p.linear, wheels=driven)), brake)
    wheels = tuple((replace(w, gas=g, friction=max([root.floor, *[400 * root.roads[i][1] for i in ids]])) for w, g, ids in zip(p.linear.wheels, gases, memberships)))
    return replace(root, planar=replace(p, linear=replace(p.linear, wheels=wheels)), center=tuple((root.center[j] + DT * p.linear.velocity[j] for j in range(2))), current_contacts=memberships)


def _dynamics_tick(root, gas, brake, index, counter):
    after = _base_tick(root, gas, brake, index, counter)
    yaw = after.planar.yaw
    wheels = tuple((replace(w, offset=(-yaw * r[1], yaw * r[0])) for w, r in zip(after.planar.linear.wheels, root.planar.levers)))
    return replace(after, planar=replace(after.planar, linear=replace(after.planar.linear, wheels=wheels)))


def load_root(x):
    p = dict(x['planar'])
    q = dict(p.pop('linear'))
    q['wheels'] = tuple((Wheel(**dict(w, offset=tuple(w['offset']))) for w in q['wheels']))
    q['velocity'] = tuple(q['velocity'])
    for name in ('levers', 'joints', 'rates', 'wheel_inertias'):
        p[name] = tuple((tuple(r) if isinstance(r, list) else r for r in p[name]))
    p['linear'] = State(**q)
    return Geometry(Planar(**p), tuple(x['center']), tuple(((tuple((tuple(v) for v in poly)), mu) for poly, mu in x['roads'])), tuple((tuple(z) for z in x['current_contacts'])), x['floor'], x['skin'])


def polygons(root):
    p = root.planar
    c, s = (math.cos(p.angle), math.sin(p.angle))
    rotate = lambda q: (c * q[0] - s * q[1], s * q[0] + c * q[1])
    origins = [tuple((root.center[j] + r[j] - rotate((wx * SIZE, wy * SIZE))[j] for j in range(2))) for r, (wx, wy) in zip(p.levers, WHEELPOS)]
    origin = tuple((sum((z[j] for z in origins)) / 4 for j in range(2)))
    hull = [[(origin[0] + rotate((x * SIZE, y * SIZE))[0], origin[1] + rotate((x * SIZE, y * SIZE))[1]) for x, y in poly] for poly in (HULL_POLY1, HULL_POLY2, HULL_POLY3, HULL_POLY4)]
    return hull + [rectangle(tuple((root.center[j] + r[j] for j in range(2))), w.heading) for r, w in zip(p.levers, p.linear.wheels)]


def scalar_road_margin(root, mesh, roadindex, edge, edgeindex):
    minimum = float('inf')
    for poly in polygons(root):
        x0 = min((x for x, y in poly))
        x1 = max((x for x, y in poly))
        y0 = min((y for x, y in poly))
        y1 = max((y for x, y in poly))
        distance = float('inf')
        for (a, b), (u0, u1, v0, v1) in zip(edge, edgeindex):
            lower = math.hypot(max(0.0, u0 - x1, x0 - u1), max(0.0, v0 - y1, y0 - v1))
            if lower >= distance:
                continue
            distance = min(distance, polygon_distance(poly, [a, b]))
        covered = all((any((a <= x <= b and c <= y <= d and inside((x, y), p) for (p, mu), (a, b, c, d) in zip(mesh, roadindex))) for x, y in poly))
        minimum = min(minimum, distance if covered else -distance)
    return minimum


def obstacle_margin(polys, obstacles):
    value = float('inf')
    for poly in polys:
        for center, radius in obstacles:
            d = min((point_segment(center, a, b) for a, b in zip(poly, poly[1:] + poly[:1])))
            value = min(value, (-d if inside(center, poly) else d) - radius)
    return value


def _force_rows(root, action):
    result = []
    for i, w in enumerate(root.planar.linear.wheels):
        g = w.gas + min(0.1, float(action[1]) - w.gas) if i >= 2 else w.gas
        after, force, d = wheel_response(w, root.planar.linear.velocity, g, float(action[2]), root.planar.linear.engine_multiplier)
        forward = (-math.sin(w.heading), math.cos(w.heading))
        side = (forward[1], -forward[0])
        v = tuple((root.planar.linear.velocity[j] + w.offset[j] for j in range(2)))
        vf = sum((forward[j] * v[j] for j in range(2)))
        vs = sum((side[j] * v[j] for j in range(2)))
        ratio = math.hypot(STIFFNESS * (d['omega_braked'] * RADIUS - vf), STIFFNESS * vs) / w.friction
        result.append(dict(wheel=i, ratio=ratio, clipped=ratio > 1.0, vector=list(force)))
    return result


def source_pedals(a, v):
    cmd = min(REAR, max(-BRAKE, a))
    gas = min(1.0, max(0.0, MASS * max(cmd, 0) * (v + 2.7) / 80000))
    brake = min(1.0, max(0.0, MASS * max(-cmd, 0) / (4 * 1.6 * 15 / (0.02 * 0.54))))
    return (gas, brake)


def raw_projection(position, path):
    points = path['points']
    arcs = path['arcs']
    out = []
    count=len(points)-1 if path.get('observed_open',False) else len(points)
    for i in range(count):
        a=points[i]
        b = points[(i + 1) % len(points)]
        dx, dy = (b[0] - a[0], b[1] - a[1])
        d = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((position[0] - a[0]) * dx + (position[1] - a[1]) * dy) / d))
        p = (a[0] + t * dx, a[1] + t * dy)
        out.append(dict(s=arcs[i] + t * math.sqrt(d), i=i, t=t, distance=math.dist(position, p), point=p, tangent=(dx / math.sqrt(d), dy / math.sqrt(d))))
    return out


def project(position, path, previous=None):
    L = path['length']
    rows = raw_projection(position, path)
    if path.get('observed_open',False):
        if previous is None:return min(rows,key=lambda q:q['distance'])
        valid=[q for q in rows if previous-5.<=q['s']<=previous+30.]
        if not valid:raise ValueError('OBSERVED_PATH_SUPPORT_EXHAUSTED')
        return min(valid,key=lambda q:q['distance'])
    if previous is None:
        q = min(rows, key=lambda x: x['distance'])
        q['s'] = q['s'] if q['s'] <= L / 2 else q['s'] - L
        return q
    valid = []
    for q in rows:
        q['s'] += round((previous - q['s']) / L) * L
        if previous - 5.0 <= q['s'] <= previous + 30.0:
            valid.append(q)
    if not valid:
        raise ValueError('PROJECTION_CONTINUITY_DOMAIN')
    return min(valid, key=lambda q: q['distance'])


def reference(s, path):
    L = path['length']
    first = path.get('observed_open',False) or 0 <= s <= L
    u = min(max(s, 0.0), L) if first or s < 0 else s % L
    i = next((i for i in range(len(path['ds'])) if path['arcs'][i + 1] >= u), len(path['ds']) - 1)
    d = path['ds'][i]
    f = max(0.0, min(1.0, (u - path['arcs'][i]) / d))
    values = path['launch_squared'] if first or s < 0 else path['periodic_squared'] + (path['periodic_squared'][0],)
    q0, q1 = values[i:i + 2]
    return (math.sqrt(max(0.0, q0 + f * (q1 - q0))), (q1 - q0) / (2 * d))


def point_at(s, path):
    u = min(max(s,0.),path['length']) if path.get('observed_open',False) else s % path['length']
    i = next((i for i in range(len(path['ds'])) if path['arcs'][i + 1] >= u), len(path['ds']) - 1)
    f = (u - path['arcs'][i]) / path['ds'][i]
    return tuple((path['points'][i][j] + f * (path['points'][(i + 1) % len(path['points'])][j] - path['points'][i][j]) for j in range(2)))


def steering(root, path, progress):
    q = project(root.center, path, progress)
    target = point_at(q['s'] + max(7.0, 0.3 * math.hypot(*root.planar.linear.velocity)), path)
    dx, dy = (target[j] - root.center[j] for j in range(2))
    a = root.planar.angle
    delta = math.atan(3.24 * 2 * (-math.sin(a) * dy - math.cos(a) * dx) / (dx * dx + dy * dy))
    return float(np.float32(-max(-0.4, min(0.4, delta))))


def nominal(root, path, progress):
    q = project(root.center, path, progress)
    v = math.hypot(*root.planar.linear.velocity)
    target, ff = reference(q['s'], path)
    sigma = sum((root.planar.linear.velocity[j] * q['tangent'][j] for j in range(2)))
    accel = ff * sigma / max(target, 1.0) + 2 * (target - v)
    gas, brake = source_pedals(accel, v)
    return np.array([steering(root, path, q['s']), gas, brake], np.float32)


def backup(root, high, low, s):
    a = nominal(root, high, s)
    b = nominal(root, low, s)
    return np.array([a[0], min(a[1], b[1]), max(a[2], b[2])], np.float32)


@dataclass
class FinishLineTracker:
    center: tuple[float, float]
    forward: tuple[float, float]
    half_width: float
    half_depth: float
    qualification_ratio: float = LAP_QUALIFICATION_RATIO
    departed_start_area: bool = False
    crossing_from_back: bool = False
    previous_longitudinal: float = 0.0
    previous_lateral: float = 0.0
    qualified_time_s: float | None = None
    candidate_crossing_time_s: float | None = None
    finish_time_s: float | None = None

    def update(self, position: tuple[float, float], velocity: tuple[float, float], progress: float, physics_time_s: float) -> bool:
        forward_x, forward_y = self.forward
        lateral_x, lateral_y = (forward_y, -forward_x)
        relative_x = float(position[0]) - self.center[0]
        relative_y = float(position[1]) - self.center[1]
        longitudinal = relative_x * forward_x + relative_y * forward_y
        lateral = relative_x * lateral_x + relative_y * lateral_y
        qualified = progress >= self.qualification_ratio
        if qualified and self.qualified_time_s is None:
            self.qualified_time_s = float(physics_time_s)
        if self.finish_time_s is not None:
            self.previous_longitudinal = longitudinal
            self.previous_lateral = lateral
            return False
        inside_width = abs(lateral) <= self.half_width
        previous_inside_width = abs(self.previous_lateral) <= self.half_width
        if not self.departed_start_area:
            if abs(longitudinal) > self.half_depth or not inside_width:
                self.departed_start_area = True
            self.previous_longitudinal = longitudinal
            self.previous_lateral = lateral
            return False
        entered_from_back = qualified and previous_inside_width and inside_width and (self.previous_longitudinal <= -self.half_depth) and (longitudinal > -self.half_depth)
        if not self.crossing_from_back and entered_from_back:
            self.crossing_from_back = True
        if self.crossing_from_back:
            if not inside_width or longitudinal <= -self.half_depth:
                self.crossing_from_back = False
                self.candidate_crossing_time_s = None
            else:
                forward_speed = float(velocity[0]) * forward_x + float(velocity[1]) * forward_y
                lateral_speed = float(velocity[0]) * lateral_x + float(velocity[1]) * lateral_y
                direction_is_valid = math.isfinite(forward_speed) and math.isfinite(lateral_speed) and (forward_speed > MIN_FORWARD_CROSSING_SPEED) and (abs(lateral_speed) <= forward_speed * MAX_LATERAL_TO_FORWARD_RATIO)
                if longitudinal < 0 and forward_speed <= 0:
                    self.candidate_crossing_time_s = None
                elif longitudinal >= 0 and direction_is_valid and (self.candidate_crossing_time_s is None):
                    self.candidate_crossing_time_s = float(physics_time_s)
            if self.crossing_from_back and longitudinal >= self.half_depth:
                crossing_time_s = self.candidate_crossing_time_s
                self.crossing_from_back = False
                self.candidate_crossing_time_s = None
                if qualified and crossing_time_s is not None:
                    self.finish_time_s = crossing_time_s
                    self.previous_longitudinal = longitudinal
                    self.previous_lateral = lateral
                    return True
        self.previous_longitudinal = longitudinal
        self.previous_lateral = lateral
        return False


def hull_pose(root):
    p = root.planar
    c, s = (math.cos(p.angle), math.sin(p.angle))
    rot = lambda x, y: (c * x - s * y, s * x + c * y)
    origins = [tuple((root.center[j] + r[j] - rot(wx * SIZE, wy * SIZE)[j] for j in range(2))) for r, (wx, wy) in zip(p.levers, WHEELPOS)]
    origin = tuple((sum((q[j] for q in origins)) / 4 for j in range(2)))
    mass = cx = cy = 0.0
    for poly in (HULL_POLY1, HULL_POLY2, HULL_POLY3, HULL_POLY4):
        vertices = [(x * SIZE, y * SIZE) for x, y in poly]
        cross = [a[0] * b[1] - b[0] * a[1] for a, b in zip(vertices, vertices[1:] + vertices[:1])]
        area = sum(cross) / 2
        x = sum(((a[0] + b[0]) * k for a, b, k in zip(vertices, vertices[1:] + vertices[:1], cross))) / (6 * area)
        y = sum(((a[1] + b[1]) * k for a, b, k in zip(vertices, vertices[1:] + vertices[:1], cross))) / (6 * area)
        mass += abs(area)
        cx += abs(area) * x
        cy += abs(area) * y
    offset = rot(cx / mass, cy / mass)
    lever = tuple((origin[j] + offset[j] - root.center[j] for j in range(2)))
    velocity = (p.linear.velocity[0] - p.yaw * lever[1], p.linear.velocity[1] + p.yaw * lever[0])
    return (origin, velocity)


def phase_failure(index, raw, peak, history, overspeed=None):
    if index <= 24:
        if peak > 2.5:
            return 'LAUNCH_FORCE'
        if index == 24 and raw == 4 and (history[0] / history[1] > 0.15):
            return 'LAUNCH_CLIP'
    else:
        if peak > 1.059:
            return 'TRACK_FORCE'
        if history[0] / history[1] > 0.1:
            return 'TRACK_CLIP'
        if overspeed is not None and overspeed > 4.85:
            return 'REFERENCE'
    return None


def certifier(root, high, low, progress, counter, cost, geometry, max_ticks=60000, history=(0, 0)):
    if geometry is None:
        raise ValueError('FULL_GEOMETRY_REQUIRED')
    cost.setdefault('geometry_checks', 0)
    index = bounds(root.roads)
    start_s = progress

    def check(r):
        if cost['geometry_checks'] >= geometry['max_checks']:
            raise RuntimeError('GEOMETRY_COST_CAP_536')
        cost['geometry_checks'] += 1
        return geometry['margin'](r, geometry['roads'], geometry['road_index'], geometry['boundary'], geometry['edge_index'], geometry['obstacles'])

    def certify(a):
        r = root
        s = progress
        peak = maxover = 0.0
        clipped, samples = history
        nt = 0
        first = None
        cost['forecast_calls'] += 1
        minimum = check(r)
        violation = None
        first_pass = False

        def result(ok, reason):
            return dict(ok=ok, reason=reason, peak=peak, max_reference_overspeed=maxover, clipped=clipped, samples=samples, model_ticks=nt, first_hold=first, min_footprint_margin_m=minimum, first_footprint_violation=violation, first_hold_pass=first_pass)
        if minimum < FOOTPRINT_ADMISSION:
            return result(False, 'CURRENT_FOOTPRINT_MARGIN')
        for j in range(HORIZON):
            use = a if j == 0 else backup(r, high, low, s)
            r = replace(r, planar=replace(r.planar, steer=-float(use[0])))
            for k in range(4):
                f = force_rows(r, use)
                cost['force_evaluations'] += 4
                samples += 4
                clipped += sum((z['clipped'] for z in f))
                peak = max(peak, max((z['ratio'] for z in f)))
                if peak > ADMISSION or clipped / samples > 0.1:
                    return result(False, 'FORCE_PEAK' if peak > ADMISSION else 'CLIP_HISTORY')
                if counter[0] >= max_ticks:
                    raise RuntimeError('MODEL_TICK_CAP_528')
                before = r
                r = tick(r, float(use[1]), float(use[2]), index, counter)
                cost['forecast_ticks'] += 1
                nt += 1
                q = project(r.center, high, s)
                delta = q['s'] - s
                s = q['s']
                v = math.hypot(*r.planar.linear.velocity)
                target = reference(s, high)[0]
                maxover = max(maxover, v - target)
                if j == 0 and k == 3:
                    first = dict(speed=v, reference=target, positive_deficit=max(0.0, target - v), progress_gain=s - start_s)
                minimum = min(minimum, check(r))
                if j == 0 and k == 3:
                    first['min_footprint_margin_m'] = minimum
                if minimum < FOOTPRINT_ADMISSION:
                    violation = dict(hold=j + 1, raw_in_hold=k + 1, raw_from_root=nt, margin_m=minimum)
                    return result(False, 'FORECAST_FOOTPRINT_MARGIN')
                if maxover > 5.0 - TRACKING_RESERVE:
                    return result(False, 'REFERENCE_WITH_NUMERIC_RESERVE')
                if q['distance'] > 3 or delta < -0.5 or delta > max(5.0, 2 * math.dist(before.center, r.center)):
                    return result(False, 'PROJECTION_OR_PATH')
                if j == 0 and k == 3:
                    first_pass = True
        return result(True, 'CERTIFIED_12HOLD_FLOAT32')
    return certify


def choose(root, high, low, progress, counter, cost, max_ticks=60000, history=(0, 0), geometry=None):
    initial = nominal(root, high, progress)
    alternative = backup(root, high, low, progress)
    nominal_u = float(initial[1]) if initial[1] > 0 else -float(initial[2])
    upper = 1.0
    oldlower = float(alternative[1]) if alternative[1] > 0 else -float(alternative[2])
    lower = -1.0
    before = cost['forecast_calls']
    trials = []
    cache = {}
    if oldlower > upper or not -1 <= upper <= 1:
        raise ValueError('PEDAL_DOMAIN')
    certify = certifier(root, high, low, progress, counter, cost, geometry, max_ticks, history)

    def command(u):
        u = float(np.float32(u))
        return np.array([initial[0], max(0.0, u), max(0.0, -u)], np.float32)

    def evaluate(u):
        u = float(np.float32(u))
        u = 0.0 if u == 0 else u
        if not lower <= u <= upper:
            raise ValueError('PEDAL_OUTSIDE_DOMAIN')
        if u not in cache:
            if len(cache) >= 31:
                raise RuntimeError('TRIAL_CAP_536')
            report = certify(command(u))
            cache[u] = dict(u=u, report=report)
            trials.append(dict(u=u, **report))
        return cache[u]
    high_trial = evaluate(upper)
    if high_trial['report']['ok']:
        full = command(upper)
        final = certify(full)
        if not final['ok']:
            return (None, dict(mode='FINAL_CERTIFICATION_FAILED', reports=[dict(mode='FINAL', **final)], final_recertified=False))
        return (full, dict(mode='SOURCE_FULL', reports=[dict(mode='HIGH', **high_trial['report']), dict(mode='FINAL', **final)], final_recertified=True, force_buffer=FORCE_BUFFER, internal_force_admission=ADMISSION, numerical_calls=0))
    lock = np.float32(0.9)
    if float(lock) < 0.9:
        lock = np.nextafter(lock, np.float32(1.0))
    below = np.nextafter(lock, np.float32(0.0))
    points = [float(np.float32(-1 + i / 8)) for i in range(17)] + [upper, nominal_u, oldlower, -float(lock), -float(below)]
    points = sorted(set((x for x in points if lower <= x <= upper)), reverse=True)
    coarse = [evaluate(x) for x in points]

    def regime(u):
        return 'locked' if u < 0 and -u >= 0.9 else 'brake' if u < 0 else 'coastgas'
    edges = []
    for a, b in zip(coarse, coarse[1:]):
        if a['report']['ok'] != b['report']['ok'] and regime(a['u']) == regime(b['u']):
            safe = a if a['report']['ok'] else b
            unsafe = b if a['report']['ok'] else a
            edges.append(dict(safe=safe['u'], unsafe=unsafe['u'], score=safe['report']['first_hold']['progress_gain']))
    edges.sort(key=lambda x: (-x['score'], -x['safe']))
    refinements = 0
    for i in range(9):
        if not edges or len(cache) >= 31:
            break
        edge = edges[i % len(edges)]
        middle = float(np.float32((edge['safe'] + edge['unsafe']) / 2))
        lo = min(edge['safe'], edge['unsafe'])
        hi = max(edge['safe'], edge['unsafe'])
        if not lo < middle < hi:
            continue
        tested = evaluate(middle)
        refinements += 1
        if tested['report']['ok']:
            edge['safe'] = middle
        else:
            edge['unsafe'] = middle
    feasible = [x for x in cache.values() if x['report']['ok']]
    nonmonotone = any((a['report']['ok'] and (not b['report']['ok']) for a, b in zip(coarse, coarse[1:])))
    if not feasible:
        return (None, dict(mode='NO_ADMISSIBLE_ACTION', reports=[dict(mode='HIGH', **high_trial['report'])], trials=trials, final_recertified=False, coarse_nonmonotone=nonmonotone, coarse_points=len(points), refinements=refinements, force_buffer=FORCE_BUFFER, internal_force_admission=ADMISSION))
    best = max(feasible, key=lambda x: (x['report']['first_hold']['progress_gain'], x['u']))
    action = command(best['u'])
    final = certify(action)
    if cost['forecast_calls'] - before > 32:
        raise RuntimeError('CERTIFICATE_CAP_536')
    if not final['ok']:
        return (None, dict(mode='FINAL_CERTIFICATION_FAILED', reports=[dict(mode='FINAL', **final)], trials=trials, final_recertified=False))
    if action[0].tobytes() != initial[0].tobytes() or (action[1] > 0 and action[2] > 0):
        raise RuntimeError('ACTION_STEER_DOMAIN')
    mode = 'BACKUP' if np.array_equal(action, alternative) else 'NOMINAL' if np.array_equal(action, initial) else 'SOURCE_RESPONSE'
    return (action, dict(mode=mode, reports=[dict(mode='HIGH', **high_trial['report']), dict(mode='FINAL', **final)], trials=trials, final_recertified=True, coarse_nonmonotone=nonmonotone, coarse_points=len(points), refinements=refinements, force_buffer=FORCE_BUFFER, internal_force_admission=ADMISSION, selected_below_old_backup=best['u'] < oldlower, selected_above_nominal=best['u'] > nominal_u, finite_samples_only=True))


def horizon(start):
    if not 1 <= start <= 39:
        raise ValueError('PREFIX1_TO39_ONLY')
    return [(h, 'FIXED577' if h < 40 else 'ANCHOR537' if h == 40 else 'BACKUP537') for h in range(start, start + 12)]


def payload(h, mode, commands, root, history, choose, backup, path, low, progress):
    if mode == 'FIXED577':
        return (commands[h].copy(), None)
    if mode == 'ANCHOR537':
        return choose(root, path, low, progress, tuple(history))
    if mode == 'BACKUP537':
        return (backup(root, path, low, progress), None)
    raise ValueError('UNKNOWN_FORECAST_MODE')


def prefix_certificate(owner, root, path, progress, start, commands, histories, tracker, visited, clock):
    r = root
    s = progress
    groups = {k: list(v) for k, v in histories.items()}
    tr = FinishLineTracker(**asdict(tracker))
    seen = set(visited)
    time_s = clock
    peaks = {'launch': 0.0, 'running': 0.0}
    minimum = owner.source_geometry(r)
    n = 0
    sequence = []
    anchor = None
    first_failure = None

    def result(ok, reason):
        return dict(ok=ok, reason=reason, mode='FIXED_PREFIX_WITH_SINGLE_537_ANCHOR_AND_BACKUP', start_global_hold=start, model_ticks=n, launch_peak=peaks['launch'], tracking_peak=peaks['running'], history=groups, min_footprint_margin_m=minimum, forecast_official_finish=tr.finish_time_s is not None, forecast_official_finish_time_s=tr.finish_time_s, certified_holds=sequence, anchor537=anchor, first_failure=first_failure)
    if minimum < 0.5:
        return result(False, 'CURRENT_FOOTPRINT')
    for h, mode in horizon(start):
        use, detail = payload(h, mode, commands, r, groups['running'], owner.transition_choose, owner.backup_command, path, owner.candidate_backup, s)
        sequence.append(dict(hold=h, mode=mode))
        if mode == 'ANCHOR537':
            anchor = detail
            if use is None:
                return result(False, 'TRANSITION537_NO_FRESH_FINAL')
        r = replace(r, planar=replace(r.planar, steer=-float(use[0])))
        group = 'launch' if h <= 24 else 'running'
        for k in range(1, 5):
            history_before = groups[group].copy()
            f = owner.model_force(r, use)
            groups[group][0] += sum((z['clipped'] for z in f))
            groups[group][1] += 4
            peaks[group] = max(peaks[group], max((z['ratio'] for z in f)))
            why = phase_failure(h, k, peaks[group], groups[group])
            row = dict(hold=h, raw=k, mode=mode, history_before=history_before, history_after=groups[group].copy(), force_peak=peaks[group], clip_fraction=groups[group][0] / groups[group][1], pre_failure=why, tick_executed=False)
            if why:
                first_failure = row
                return result(False, why)
            previous = r
            r = owner.model_tick(r, float(use[1]), float(use[2]), owner.source_index, owner.model)
            n += 1
            q = owner.project('prefix_forecast', r.center, path, s)
            delta = q['s'] - s
            s = q['s']
            gap = owner.source_geometry(r)
            minimum = min(minimum, gap)
            over = math.hypot(*r.planar.linear.velocity) - reference(s, path)[0]
            limit = max(5.0, 2 * math.dist(previous.center, r.center))
            why = phase_failure(h, k, peaks[group], groups[group], over)
            flags = dict(FOOTPRINT=minimum < 0.5, PATH=q['distance'] > 3, PROJECTION_BACKWARD=delta < -0.5, PROJECTION_FORWARD=delta > limit)
            split = 'REFERENCE' if why == 'REFERENCE' else next((name for name, v in flags.items() if v), None)
            row.update(tick_executed=True, path_error=q['distance'], projection_segment=q['i'], projection_delta=delta, projection_lower=-0.5, projection_upper=limit, footprint=gap, minimum_footprint=minimum, reference_excess=over, geometry_flags=flags, first_failure=why or split)
            if why or split:
                first_failure = row
                return result(False, why or split)
            for ids in r.current_contacts:
                seen.update(ids)
            time_s += 0.02
            pose, velocity = hull_pose(r)
            tr.update(pose, velocity, len(seen) / owner.track_nodes, time_s)
            if tr.finish_time_s is not None:
                return result(True, 'STRICT_THROUGH_FORECAST_OFFICIAL_FINISH')
    return result(True, 'STRICT_PREFIX_ANCHOR_BACKUP_HORIZON')


def force_rows(root, action):
    rows=_force_rows(root,action)
    if len(rows)!=4 or any(not math.isfinite(q['ratio']) or q['clipped']!=(q['ratio']>1.) for q in rows):
        raise ValueError('ORIGINAL_FORCE_IDENTITY')
    return rows


def body(root):
    return max(math.hypot(*hull_pose(root)[1]),
               *(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2)))
                 for w in root.planar.linear.wheels))


def tick(root, gas, brake, index, counter):
    after = _dynamics_tick(root, gas, brake, index, counter)
    value = body(after)
    if not math.isfinite(value) or value >= 100.:
        raise ValueError('ORIGINAL_BODY_DOMAIN_GE100_OR_NONFINITE')
    return after


def freeze(value):
    if isinstance(value,np.ndarray):
        return tuple(freeze(v) for v in value)
    if isinstance(value,np.generic):
        return value.item()
    if isinstance(value, dict):
        return MappingProxyType({k:freeze(v) for k,v in value.items()})
    if isinstance(value, (tuple,list)):
        return tuple(freeze(v) for v in value)
    return value


def polygon_distance_array(a, b):
    """Independent elementwise binary64 ops; CPython hypot remains scalar.

    No dot/reduction, FMA, approximate sqrt, reordering or parallel reduction.
    The external numerical tests may select the scalar fallback instead.
    """
    aa=np.asarray(a,dtype=np.float64);bb=np.asarray(b,dtype=np.float64)
    axes=[]
    for p in (aa,bb):
        for v,w in zip(p,np.roll(p,-1,axis=0)):
            axes.append((v[1]-w[1],w[0]-v[0]))
    axis=np.asarray(axes)
    pa=aa[None,:,0]*axis[:,None,0]+aa[None,:,1]*axis[:,None,1]
    pb=bb[None,:,0]*axis[:,None,0]+bb[None,:,1]*axis[:,None,1]
    if not np.any((pa.min(axis=1)>pb.max(axis=1))|(pb.min(axis=1)>pa.max(axis=1))):
        return 0.
    values=[]
    for points,segments in ((aa,bb),(bb,aa)):
        end=np.roll(segments,-1,axis=0)
        dx=end[:,0]-segments[:,0];dy=end[:,1]-segments[:,1]
        den=dx*dx+dy*dy
        px=points[:,None,0]-segments[None,:,0]
        py=points[:,None,1]-segments[None,:,1]
        numerator=px*dx+py*dy
        t=np.divide(numerator,den,out=np.zeros_like(numerator),where=den!=0)
        t=np.maximum(0.,np.minimum(1.,t))
        rx=px-t*dx;ry=py-t*dy
        values.extend(math.hypot(float(x),float(y)) for x,y in zip(rx.ravel(),ry.ravel()))
    return min(values)


class Scene:
    """Owned immutable geometry, <=5000 exact full-margin cache entries.

    Coordinates/metres; road coefficients dimensionless; obstacle radius/metres.
    These are required inputs, not reconstructed from observation by this module.
    """
    def __init__(self, roads, boundary, obstacles, max_entries=5000, array_distance=False):
        if not roads or not boundary:raise ValueError('FULL_GEOMETRY_REQUIRED')
        self.roads=freeze(roads);self.boundary=freeze(boundary);self.obstacles=freeze(obstacles)
        self.index=bounds(self.roads);self.edges=freeze(boundary_index(self.boundary))
        self.road_boxes=np.asarray(self.index,np.float64);self.road_boxes.flags.writeable=False
        self.edge_boxes=np.asarray(self.edges,np.float64);self.edge_boxes.flags.writeable=False
        self.max_entries=min(int(max_entries),5000);self.cache={}
        self.array_distance=bool(array_distance);self.hits=self.misses=0

    def clear(self):
        self.cache.clear();self.hits=self.misses=0

    def context(self):
        return dict(roads=self.roads,road_index=self.index,boundary=self.boundary,
                    edge_index=self.edges,obstacles=self.obstacles,max_checks=600000,margin=self.margin)

    def margin(self, root, *unused):
        p=root.planar
        values=(*root.center,p.angle,*(v for r in p.levers for v in r),*(w.heading for w in p.linear.wheels))
        if not all(math.isfinite(v) for v in values):raise ValueError('NONFINITE_GEOMETRY_INPUT')
        key=struct.pack('!'+str(len(values))+'d',*values)
        if key in self.cache:self.hits+=1;return self.cache[key]
        if len(self.cache)>=self.max_entries:raise RuntimeError('IMMUTABLE_MARGIN_CACHE5000')
        self.misses+=1;polys=polygons(root);minimum=float('inf')
        distance_fn=polygon_distance_array if self.array_distance else polygon_distance
        boxes=self.edge_boxes
        for poly in polys:
            x0=min(x for x,y in poly);x1=max(x for x,y in poly)
            y0=min(y for x,y in poly);y1=max(y for x,y in poly)
            # max(dx,dy) is an exact conservative lower bound on hypot(dx,dy).
            # Final selection still follows original edge order/scalar hypot.
            dx=np.maximum(0.,np.maximum(boxes[:,0]-x1,x0-boxes[:,1]))
            dy=np.maximum(0.,np.maximum(boxes[:,2]-y1,y0-boxes[:,3]))
            lower=np.maximum(dx,dy)
            # One exact edge distance supplies a certified upper bound before
            # the original-order loop. Finite nonnegative min is order-invariant;
            # no approximate distance or road/obstacle exclusion is introduced.
            seed=int(np.argmin(lower))
            distance=distance_fn(poly,self.boundary[seed])
            eligible_edges=np.flatnonzero(lower<distance)
            for k in eligible_edges:
                if k==seed:continue
                if lower[k]>=distance:continue
                a,b=self.boundary[k];u0,u1,v0,v1=self.edges[k]
                bound=math.hypot(max(0.,u0-x1,x0-u1),max(0.,v0-y1,y0-v1))
                if bound>=distance:continue
                distance=min(distance,distance_fn(poly,(a,b)))
            covered=True
            for x,y in poly:
                q=self.road_boxes
                eligible=np.flatnonzero((q[:,0]<=x)&(x<=q[:,1])&(q[:,2]<=y)&(y<=q[:,3]))
                if not any(inside((x,y),self.roads[k][0]) for k in eligible):covered=False;break
            minimum=min(minimum,distance if covered else -distance)
        result=min(minimum,obstacle_margin(polys,self.obstacles))
        self.cache[key]=result
        return result


class MissingInput(ValueError):
    pass


# Availability annotations, not additional inputs or an estimator implementation.
INPUT_AVAILABILITY = MappingProxyType({
    'observation_estimate_possible_not_exact': (
        'speed/yaw/front-steer from quantized HUD and temporal pixels',
        'visible local road/obstacle geometry; reset-local action/observation memory'),
    'required_but_not_supplied_here': (
        'full global primary/backup path and road/material/obstacle geometry',
        'full hull/wheel/joint/contact state, including true wheel gas/friction',
        'actual clipped-wheel sample history and prefix tracker/visited/clock',
        'original fixed39 prefix commands, excluded from observation submission'),
    'scope': 'Numerical kernel only. Estimates do not inherit true-state safety claims.'})


def load_required_root(record):
    """Explicit SI state interface. No missing physical values are imputed.

    center/levers/offset: m / m / m/s (wheel velocity offset).
    velocity:m/s; angle/joints/heading/steer:rad; yaw/rates:rad/s;
    omega:rad/s; mass:kg; inertia:kg*m^2; angular_momentum:kg*m^2/s;
    gas:[0,1]; friction:N; floor:N; skin:m; multipliers:dimensionless.
    current_contacts are ordered per-wheel road-index memberships with original
    pre-step sensor timing. This module does not estimate any of these values.
    """
    groups=[(record,Geometry),(record.get('planar',{}),Planar),
            (record.get('planar',{}).get('linear',{}),State)]
    for fields,kind in groups:
        if not set(kind.__dataclass_fields__)<=set(fields):raise MissingInput(kind.__name__+'_FIELDS')
    for wheel in record['planar']['linear']['wheels']:
        if not set(Wheel.__dataclass_fields__)<=set(wheel):raise MissingInput('WHEEL_FIELDS')
    return load_root(record)


class Controller:
    """598 fixed-prefix -> original537 chooser with explicit external inputs.

    high/low: complete global point/arc/launch+periodic reference-speed paths,
    not local visible fragments. progress:m unwrapped. Histories contain actual
    [number of clipped wheel samples,total wheel samples], launch<=24/running>24.
    Prefix additionally requires actual tracker,visitedIDs,elapsed clock and the
    original fixed39commands. These inputs remain unavailable to a pixel Agent.
    No map/state/tape is embedded and this is deliberately not an Agent entrypoint.
    """
    def __init__(self, high, low, scene, commands=None, track_nodes=None):
        required={'points','arcs','length','ds','launch_squared','periodic_squared'}
        if not required<=set(high) or not required<=set(low):raise MissingInput('GLOBAL_REFERENCE_PATHS')
        self.high=freeze(high);self.candidate_backup=freeze(low);self.scene=scene
        self.geometry_context=scene.context();self.model=[0]
        self.planner=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
        self.source_index=bounds(scene.roads);self.track_nodes=track_nodes
        self.commands=None if commands is None else {h:np.asarray(v,np.float32).copy() for h,v in commands.items()}
        if self.commands is not None:
            for action in self.commands.values():action.flags.writeable=False

    def source_geometry(self, root):return self.scene.margin(root)
    def model_force(self, root, action):
        f=force_rows(root,action)
        if len(f)!=4 or any(not math.isfinite(q['ratio']) or q['clipped']!=(q['ratio']>1.) for q in f):
            raise ValueError('ORIGINAL_FORCE_IDENTITY')
        return f
    def model_tick(self, *args):return tick(*args)
    def project(self, category, *args):return project(*args)
    def backup_command(self, *args):return backup(*args)
    def transition_choose(self,root,path,low,progress,history):
        return choose(root,path,low,progress,self.model,self.planner,180000,
                      history=history,geometry=self.geometry_context)

    def select(self,root,progress,hold,launch_history,running_history,tracker=None,visited=None,clock=None):
        self.scene.clear()
        if hold<=39:
            if self.commands is None or not set(range(1,40))<=set(self.commands):raise MissingInput('FIXED_PREFIX39_COMMANDS')
            if tracker is None or visited is None or clock is None or self.track_nodes is None:raise MissingInput('PREFIX_TRACKER_VISITED_CLOCK')
            report=prefix_certificate(self,root,self.high,progress,hold,self.commands,
                dict(launch=launch_history,running=running_history),tracker,visited,clock)
            return (self.commands[hold].copy() if report['ok'] else None),report
        return choose(root,self.high,self.candidate_backup,progress,self.model,self.planner,180000,
                      history=tuple(running_history),geometry=self.geometry_context)
