"""Four raw-tick torque/slip brake response, a diagnostic candidate only.

Frozen headings and wheel-to-assembly velocity offsets; no yaw/joint/contact
prediction. Source-sized wheel omega is a privileged diagnostic input, not pixels.
"""
from dataclasses import dataclass, replace
import math
import struct

DT, POWER, INERTIA, RADIUS, STIFFNESS = .02, 40000., 1.6, .54, 82.


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def bits(value):
    return struct.unpack('I', struct.pack('f', value))[0]


def from_bits(value):
    return struct.unpack('f', struct.pack('I', value))[0]


@dataclass(frozen=True)
class Wheel:
    omega: float
    gas: float = 0.
    heading: float = 0.
    friction: float = 400.
    offset: tuple = (0., 0.)


@dataclass(frozen=True)
class State:
    velocity: tuple
    wheels: tuple
    mass: float
    engine_multiplier: float = 1.


def wheel_response(wheel, velocity, gas, brake, engine_multiplier=1.):
    """One actual-source-ordered force evaluation, before a world step."""
    forward = (-math.sin(wheel.heading), math.cos(wheel.heading))
    side = (forward[1], -forward[0])
    vx, vy = (velocity[j] + wheel.offset[j] for j in range(2))
    vf = forward[0]*vx + forward[1]*vy
    vs = side[0]*vx + side[1]*vy
    omega_drive = wheel.omega + DT*POWER*engine_multiplier*gas/INERTIA/(abs(wheel.omega)+5.)
    if brake >= .9:
        omega_braked = 0.
    elif brake > 0:
        omega_braked = omega_drive - math.copysign(min(15.*brake, abs(omega_drive)), omega_drive)
    else:
        omega_braked = omega_drive
    raw_f, raw_p = STIFFNESS*(omega_braked*RADIUS-vf), -STIFFNESS*vs
    magnitude = math.hypot(raw_f, raw_p)
    scale = min(1., wheel.friction/magnitude) if magnitude else 1.
    force, lateral = raw_f*scale, raw_p*scale
    after = replace(wheel, omega=omega_braked-DT*force*RADIUS/INERTIA, gas=gas)
    return after, (force*forward[0]+lateral*side[0], force*forward[1]+lateral*side[1]), {
        'omega_drive': omega_drive, 'omega_braked': omega_braked,
        'longitudinal_force': force, 'lateral_force': lateral,
        'clipped': magnitude > wheel.friction,
    }


def forecast(state, brake, ticks=4):
    if len(state.wheels) != 4 or state.mass <= 0 or not 0 <= brake <= 1 or ticks != 4:
        raise ValueError('UNSUPPORTED_RESPONSE_DOMAIN')
    rows = []
    for _ in range(ticks):
        wheels, forces, detail = [], [], []
        for w in state.wheels:
            # Candidate is braking-only: gas(0) decreases immediately in source.
            after, force, extra = wheel_response(w, state.velocity, 0., brake, state.engine_multiplier)
            wheels.append(after); forces.append(force); detail.append(extra)
        velocity = tuple(state.velocity[j]+DT*sum(f[j] for f in forces)/state.mass for j in range(2))
        state = replace(state, velocity=velocity, wheels=tuple(wheels))
        rows.append({'velocity': velocity, 'wheels': detail})
    return state, rows


def choose_brake(state, target_speed):
    """Invert the four-tick response and verify the adjacent float32 command.

    Numeric monotonicity checks are local checks, not a continuum certificate.
    The lock discontinuity uses the first float32 actually >= source's .9.
    """
    if target_speed < 0 or not math.isfinite(target_speed):
        raise ValueError('BAD_TARGET')
    end = lambda b: math.hypot(*forecast(state, b)[0].velocity)
    prelock = f32(.9)
    lock = from_bits(bits(prelock)+1) if prelock < .9 else prelock
    values = [end(prelock*i/16) for i in range(17)]
    if any(b > a+1e-10 for a,b in zip(values,values[1:])):
        raise ValueError('RESPONSE_NONMONOTONE_STOP')
    if values[0] <= target_speed:
        return 0., values[0]
    if values[-1] > target_speed:
        prediction = end(lock)
        if prediction > target_speed:
            raise ValueError('RESPONSE_TARGET_UNREACHABLE')
        return lock, prediction
    low, high = 0, bits(prelock)
    while low < high:
        middle = (low+high)//2
        if end(from_bits(middle)) <= target_speed:
            high = middle
        else:
            low = middle+1
    brake = from_bits(low); prediction = end(brake)
    if prediction > target_speed or (low and end(from_bits(low-1)) <= target_speed):
        raise ValueError('RESPONSE_FLOAT32_BOUNDARY_STOP')
    return brake, prediction
