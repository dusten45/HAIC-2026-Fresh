"""One frozen paired-evaluation episode; save endpoints and hashes only.

Private plan/case data stay outside the repository. The child policy receives
only pixels. No images, per-step actions, paths, or simulator state are saved.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
from retry.diagnose import Budget, make_env
from retry.evaluate import check_window, observation_contract, percentiles
from retry.process_probe import Participant, valid_action


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_digest(values):
    return hashlib.sha256(np.asarray(values, dtype='<f8').tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--case', required=True)
    parser.add_argument('--arm', required=True)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    case = next(item for item in plan['cases'] if item['id'] == args.case)
    config = plan['arms'][args.arm]
    role = args.case + '__' + args.arm
    output = directory/'runs'/role
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    env = child = None
    used = raw_ticks = reset_ticks = 0
    action_hash, observation_hash = hashlib.sha256(), hashlib.sha256()
    act_times = []
    sim_wall = actor_cpu = actor_rss = 0.0
    ended = truncated = False
    result = {}

    def charged():
        with (directory/'budget.json').open() as handle:
            fcntl.flock(handle, fcntl.LOCK_SH)
            return json.load(handle)['stages'].get(role, 0)

    def stop(detail):
        try:
            with (directory/'stop.json').open('x') as handle:
                json.dump({'kind': 'INCONCLUSIVE_TECHNICAL_OR_BUDGET',
                           'role': role, 'detail': detail}, handle)
        except FileExistsError:
            pass

    try:
        check_window(plan)
        assert not (directory/'stop.json').exists()
        assert digest(plan_path) == (directory/'plan.sha256').read_text().split()[0]
        for name, wanted in plan['execution_source_sha256'].items():
            assert digest(Path(name)) == wanted, name
        assert digest(Path(config['archive_path'])) == config['archive_sha256']
        for name, wanted in config['members_sha256'].items():
            assert digest(Path(config['package_path'])/name) == wanted, name
        budget = Budget(plan_path, role)
        child = Participant(Path(sys.executable), command_override=[
            sys.executable, plan['worker_path'], config['package_path']])
        check_window(plan)
        env = make_env()
        before_reset = time.perf_counter()
        obs, _ = env.reset(seed=case['seed'], options={'track_id': case['track_id']})
        reset_wall = time.perf_counter()-before_reset
        reset_ticks = round(env.unwrapped.t*50)
        assert reset_ticks == 51
        observation_contract(obs)
        assert all(np.array_equal(obs[0], frame) for frame in obs[1:])
        geometry = array_digest(env.unwrapped.track)
        assert geometry == case['road_geometry_sha256']
        obstacles = array_digest([[*map(float, obstacle.position),
                                   float(obstacle.fixtures[0].shape.radius)]
                                  for obstacle in env.unwrapped.obstacles])
        assert obstacles == case['expected_physical_obstacles_sha256']
        hull = env.unwrapped.car.hull
        initial_state = array_digest([*hull.position, *hull.linearVelocity,
                                      hull.angle, env.unwrapped.t,
                                      env.unwrapped.tile_visited_count,
                                      env.damage.damage, env.off_track_counter])
        initial = {'geometry_sha256': geometry, 'obstacles_sha256': obstacles,
                   'initial_state_sha256': initial_state,
                   'initial_observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest()}
        # Each arm checks the shared initial conditions before acting.
        with (directory/('pair-initial-'+args.case+'.json')).open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            content = handle.read()
            if content:
                assert json.loads(content) == initial
            else:
                json.dump(initial, handle)
                handle.flush()
        _, actor_reset_wall = child.call('reset', obs)
        observation_hash.update(obs.tobytes())
        (output/'started.json').write_text(json.dumps({
            'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'plan_sha256': digest(plan_path), **initial}, indent=2)+'\n')
        reason = None
        for _ in range(plan['max_steps']):
            check_window(plan)
            if (directory/'stop.json').exists():
                reason = 'shared_stop_censored'
                break
            response, act_wall = child.call('act', obs)
            assert valid_action(response)
            action = np.asarray(response['action'], dtype=np.float32)
            assert np.all(action >= [-1, 0, 0]) and np.all(action <= [1, 1, 1])
            previous = obs
            before_time = env.unwrapped.t
            step_start = time.perf_counter()
            obs, _, ended, truncated, info = budget.step(env, action)
            sim_wall += time.perf_counter()-step_start
            used += 1
            ticks = round((env.unwrapped.t-before_time)*50)
            assert 1 <= ticks <= 4 and (ticks == 4 or ended or truncated)
            raw_ticks += ticks
            observation_contract(obs)
            assert np.array_equal(obs[:3], previous[1:])
            action_hash.update(action.tobytes())
            observation_hash.update(obs.tobytes())
            act_times.append(act_wall)
            actor_cpu = max(actor_cpu, response['actor_cumulative_CPU_s'])
            actor_rss = max(actor_rss, response['rss_mib'])
            if ended or truncated:
                reason = info['retire_reason']
                break
        else:
            reason = 'unexpected_no_official_endpoint_at_native_bound_censored'
        finish = env.unwrapped.finish_time_s
        terminal = bool(ended or truncated)
        assert finish is None or terminal
        assert charged() == used
        result = {'case': args.case, 'arm': args.arm, 'role': role,
                  'completed': finish is not None, 'terminal_observed': terminal,
                  'censored': not terminal, 'evaluation_endpoint_observed': terminal,
                  'finish_time_s': finish, 'terminated': bool(ended), 'truncated': bool(truncated),
                  'lap_ms': round((finish-1.02)*1000) if finish is not None else None,
                  'unique_tiles': env.unwrapped.tile_visited_count,
                  'total_tiles': len(env.unwrapped.track), 'damage': env.damage.damage,
                  'retire_reason': reason, 'charged_wrapper_actions': charged(),
                  'raw_step_ticks': raw_ticks, 'raw_reset_ticks': reset_ticks,
                  'frozen_archive_sha256': config['archive_sha256'], **initial,
                  'policy_module_boundary': child.ready, 'oracle_inputs_to_policy': False,
                  'steps': used, 'action_sequence_sha256': action_hash.hexdigest(),
                  'observation_sequence_sha256': observation_hash.hexdigest(),
                  'saved_video_frames': 0, 'saved_trajectory_rows': 0,
                  'reset_wall_s': reset_wall, 'actor_reset_wall_s': actor_reset_wall,
                  'wall_s': time.perf_counter()-started, 'sum_sim_step_wall_s': sim_wall,
                  'act_including_ipc': percentiles(act_times), 'actor_cumulative_CPU_s': actor_cpu,
                  'harness_CPU_s': resource.getrusage(resource.RUSAGE_SELF).ru_utime
                                   + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                  'child_peak_RSS_mib': actor_rss,
                  'harness_peak_RSS_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    except Exception as error:
        stop(repr(error))
        result = {'case': args.case, 'arm': args.arm, 'role': role,
                  'error': repr(error), 'traceback': traceback.format_exc(),
                  'completed': False, 'terminal_observed': False, 'censored': True,
                  'charged_wrapper_actions': charged(), 'steps': used,
                  'raw_step_ticks': raw_ticks, 'raw_reset_ticks': reset_ticks,
                  'saved_video_frames': 0, 'saved_trajectory_rows': 0,
                  'wall_s': time.perf_counter()-started, 'no_automatic_retry': True}
    finally:
        (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        if child:
            child.close()
        if env:
            env.close()
    # Endpoint performance stays in the private result; stdout is operational.
    print(json.dumps({'role': role, 'official_endpoint': result['terminal_observed'],
                      'charged_wrapper_actions': result['charged_wrapper_actions']}), flush=True)
    return int('error' in result)


if __name__ == '__main__':
    sys.exit(main())
