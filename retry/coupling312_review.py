"""Read existing policy ZIP code and saved selected paths; never import a simulator.

No actor execution, candidate policy, fitting, or new labels. CLI arguments point
to private inputs. Output contains aggregate arithmetic and code-audit counts.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time
import zipfile

import numpy as np


def function(source, name):
    return next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == name)


def constants(source):
    values = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            values[node.targets[0].id] = ast.literal_eval(node.value)
    return values


def target(path, speed, scale):
    remaining = float(np.clip((4 + .35 * speed) * scale, 6 * scale, 14 * scale))
    for a, b in zip(path[:-1], path[1:]):
        length = float(np.linalg.norm(b - a))
        if length > 1e-8 and length >= remaining:
            return a + (b - a) * remaining / length
        remaining -= length
    return path[-1] if len(path) else None


def steer(point, previous, gain):
    x, forward = map(float, point)
    curvature = 2 * x / max(forward * forward + x * x, 1e-6)
    raw = float(np.clip(np.arctan(3.24 * curvature * gain), -.4, .4))
    return .8 * raw + .2 * previous


def review(package, traces, archives):
    started = time.perf_counter()
    with zipfile.ZipFile(package) as z:
        cfg = constants(z.read('retry/cem294_constants.py').decode())
        chosen = function(z.read('retry/connected_agent.py').decode(), 'choose_route')
        names = {n.id for n in ast.walk(chosen) if isinstance(n, ast.Name)}
        assert 'STEERING_GAIN' not in names and 'LOOKAHEAD_SCALE' not in names
        controller = z.read('retry/parameter_agent.py').decode()
        nominal = z.read('retry/nominal238_base.py').decode()
        assert 'curvature * STEERING_GAIN' in controller
        assert 'route_target(path, speed, LOOKAHEAD_SCALE)' in nominal
    archive_count = missing = aligned = 0
    bodies = set()
    for archive in sorted(archives):
        with zipfile.ZipFile(archive) as z:
            if 'retry/connected_agent.py' not in z.namelist():
                continue
            source = z.read('retry/connected_agent.py').decode()
            try:
                node = function(source, 'choose_route')
            except StopIteration:
                missing += 1
                continue
            archive_count += 1
            bodies.add(hashlib.sha256(ast.dump(node).encode()).hexdigest())
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            aligned += int({'STEERING_GAIN', 'LOOKAHEAD_SCALE'} <= names)
    errors, target_errors = [], []
    rows = nonempty = changed = 0
    target_max = nominal_max = final_max = 0.
    for trace in traces:
        for line in Path(trace).read_text().splitlines():
            r = json.loads(line)
            rows += 1
            path = np.asarray(r['pixel_path'], np.float64).reshape(-1, 2)
            f = r['features']
            if not len(path):
                assert f[0] == 1.
                continue
            nonempty += 1
            assert f[0] == 0.
            point = target(path, f[3], cfg['LOOKAHEAD_SCALE'])
            actual = steer(point, f[7], cfg['STEERING_GAIN'])
            target_max = max(target_max, float(np.max(np.abs(point - f[1:3]))))
            nominal_max = max(nominal_max, abs(float(np.float32(actual)) - f[13]))
            final_max = max(final_max, abs(float(np.float32(actual)) - r['action'][0]))
            proxy_point = target(path, f[3], 1.)
            proxy = steer(proxy_point, f[7], 1.)
            error = abs(proxy - actual)
            errors.append(error)
            target_errors.append(float(np.linalg.norm(proxy_point - point)))
            changed += int(np.float32(proxy) != np.float32(actual))
    assert target_max < 1e-10 and nominal_max == 0. and final_max == 0.
    return dict(stage=312, review_only=True,
        source_audit=dict(archived_choose_route_functions=archive_count,
            distinct_AST_bodies=len(bodies), archives_without_named_function=missing,
            explicit_gain_and_lookahead_aligned_functions=aligned,
            current_router_uses_default_target_and_unit_gain=True,
            current_controller_uses_frozen_gain_and_lookahead=True),
        selected_path_arithmetic=dict(rows=rows, nonempty_paths=nonempty,
            proxy_differs_in_float32=changed,
            proxy_steer_abs_error_rad=dict(mean=float(np.mean(errors)),
                median=float(np.median(errors)), p95=float(np.percentile(errors,95)),
                maximum=float(max(errors))),
            target_distance_difference_m=dict(mean=float(np.mean(target_errors)),
                p95=float(np.percentile(target_errors,95)), maximum=float(max(target_errors))),
            actual_target_max_abs_reconstruction_error=target_max,
            actual_nominal_and_final_steer_bit_exact=True,
            counterfactual_rank_changes_measured=False,
            closed_loop_benefit_measured=False),
        cost=dict(new_native=0, new_source_physics_ticks=0, new_fits=0,
            new_actor_calls=0, wall_s=time.perf_counter()-started))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--trace', type=Path, action='append', required=True)
    p.add_argument('--archive-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = review(a.package, a.trace, a.archive_root.glob('stage*/**/*.zip'))
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
