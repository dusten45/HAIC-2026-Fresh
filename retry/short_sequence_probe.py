"""Actual-simulator action-sequence diagnostic; never an online planner.

The private, preregistered plan supplies the scene and action basis. Every
branch replays its entire prefix. Future outcomes choose a diagnostic sequence,
so neither search nor its selected continuation is a legal pixel-policy result.
"""
import hashlib
import json
from pathlib import Path

import numpy as np


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def build_worker(source, destination):
    """Add fixed time-indexed commands and executed-steering feedback to observer."""
    text = Path(source).read_text()
    substitutions = {
        "\nobserved = {}\n": """
sequence_config = json.loads((clean / 'sequence-config.json').read_text())
sequence_step, sequence_anchor = 0, None
observed = {}
""",
        "        agent.reset(obs)": """        agent.reset(obs)
        sequence_step, sequence_anchor = 0, None""",
        "        action = np.asarray(agent.act(obs),dtype=np.float32)": """        action = np.asarray(agent.act(obs),dtype=np.float32)
        original_action = action.copy()
        sequence_step += 1
        offset = sequence_step - sequence_config['start_step']
        phase = None
        if not sequence_config['baseline'] and 0 <= offset < 2 * sequence_config['block_actions']:
            if offset == 0:
                sequence_anchor = original_action.copy()
            phase = offset // sequence_config['block_actions']
            action = sequence_anchor.copy()
            action[0] = np.clip(float(sequence_anchor[0]) + sequence_config['steer_offsets'][phase], -.4, .4)
            if sequence_config['brake_first_block'] and phase == 0:
                action[1:] = (0., sequence_config['brake_value'])
            agent.controller.previous_steer = float(action[0])
        sequence_receipt = dict(step=sequence_step, phase=phase,
            original_action=original_action.tolist(), executed_action=action.tolist(),
            anchor_action=None if sequence_anchor is None else sequence_anchor.tolist(),
            executed_steer_feedback=phase is not None)""",
        "        response = {'action':action.tolist(),'act_compute_ms':duration,":
        "        response = {'sequence_probe':sequence_receipt,'action':action.tolist(),'act_compute_ms':duration,",
    }
    for old, new in substitutions.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    compile(text, str(destination), 'exec')
    Path(destination).write_text(text)
    Path(destination).chmod(0o600)


def sequence_episode(plan_path, plan, case, arm, initial_pairs, prefix_reference=None):
    """Use the existing charged evaluator, recording only a bounded suffix."""
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry import frozen_paired_evaluation as paired
    from retry.full_route_reproduction import truth

    spec = plan['arms'][arm]['constants']['sequence-config.json']
    prefix_length = spec['start_step'] - 1
    state = dict(steps=0, calls=0, contact_ids=set())
    rows, prefix = [], {}
    action_hash, observation_hash = hashlib.sha256(), hashlib.sha256()
    original_factory, original_prepare = diagnose.make_env, runtime.prepare

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        old_reset, old_step = env.reset, env.step

        def reset(*args, **kwargs):
            output = old_reset(*args, **kwargs)
            observation_hash.update(output[0].tobytes())
            state['env'] = env
            listener = env.unwrapped.world.contactListener_bug_workaround
            original_contact = listener._contact

            def contact(c, begin):
                if begin:
                    body = listener._match_obstacle_contact(c)
                    if body is not None:
                        state['contact_ids'].update(i for i, o in enumerate(env.unwrapped.obstacles) if o == body)
                return original_contact(c, begin)

            listener._contact = contact
            return output

        def step(action):
            index = state['steps'] + 1
            state['contact_ids'] = set()
            assert np.array_equal(action, np.asarray(state['response']['sequence_probe']['executed_action'], np.float32))
            output = old_step(action)
            state['steps'] = index
            obs, _, ended, truncated, info = output
            after = truth(env)
            if index <= prefix_length:
                action_hash.update(action.tobytes())
                observation_hash.update(obs.tobytes())
            if index == prefix_length:
                prefix.update(actions_sha256=action_hash.hexdigest(), observations_sha256=observation_hash.hexdigest(),
                    state=after, tile_bitmap=[bool(t.road_visited) for t in env.unwrapped.road],
                    policy=digest({key: state['response'][key] for key in
                        ('action', 'contact_probe', 'speed_constraint_probe', 'connection_selection', 'memory')}))
                if prefix_reference is not None:
                    assert prefix == prefix_reference, 'Actual replay prefix mismatch'
                assert after['damage'] == 0 and not ended and not truncated
            if index > prefix_length:
                rows.append(dict(step=index, state=after, action=list(map(float, action)),
                    contact_obstacle_ids=sorted(state['contact_ids']), collision=bool(info['collision']),
                    wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),
                    sequence_probe=state['response']['sequence_probe'],
                    observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),
                    terminal=bool(ended or truncated), retire_reason=info.get('retire_reason')))
            return output

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        old_call = worker.call

        def call(operation, observation, *extra, **kw):
            # Future scores / physics are never passed to this pixel actor.
            assert not extra and not kw
            assert isinstance(observation, np.ndarray) and observation.dtype == np.float32
            assert observation.shape == (4, 84, 84) and observation.nbytes == 112896
            response, latency = old_call(operation, observation)
            if operation == 'act':
                state['calls'] += 1
                assert response['sequence_probe']['step'] == state['calls']
                receipt = response['sequence_probe']
                if receipt['phase'] is not None:
                    assert response['memory']['previous_steer'] == receipt['executed_action'][0]
                state['response'] = response
            return response, latency

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        result = paired.episode(plan_path, plan, case, arm, initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
    diagnostic = dict(prefix=prefix, suffix=rows, GT_inputs_to_actor=False,
        future_outcomes_used_by_offline_selector=True, legal_policy_performance=False,
        scope='Whole prefix replay; no simulator/solver cloning. Bounded actual suffix; no stored pixels.')
    directory = plan_path.parent / 'runs' / (case['id'] + '__' + arm)
    paired.write(directory / 'sequence-diagnostic.json', diagnostic, exclusive=True)
    return result, diagnostic


def summarize_suffix(result, diagnostic):
    rows = diagnostic['suffix']
    before = diagnostic['prefix']['state']
    after = rows[-1]['state'] if rows else before
    return dict(technical_error=result.get('error'), steps=result['successful_wrapper_steps'],
        terminal=result['terminal_observed'], completed=result['completed'], lap_ms=result['lap_ms'],
        retire_reason=result['retire_reason'], damage=after['damage'], unique_tiles=after['unique_tiles'],
        new_tiles=after['unique_tiles'] - before['unique_tiles'], speed_m_s=after['speed_m_s'],
        first_contact_step=next((r['step'] for r in rows if r['contact_obstacle_ids'] or r['collision']), None),
        contact_steps=sum(bool(r['contact_obstacle_ids'] or r['collision']) for r in rows),
        maximum_off_track_counter=max([before['off_track_counter']] + [r['state']['off_track_counter'] for r in rows]),
        endpoint_wheel_road_contacts=rows[-1]['wheel_road_contacts'] if rows else None,
        suffix_sha256=digest(rows))


def choose(search_summaries, specifications, horizon):
    """Frozen actual-outcome rank, distinct from subsequent continuation check."""
    baseline = search_summaries['B']
    admissible = []
    for name, row in search_summaries.items():
        if name == 'B':
            continue
        ok = (not row['technical_error'] and row['steps'] == horizon and not row['terminal']
              and row['contact_steps'] == 0 and row['damage'] == 0
              and row['new_tiles'] >= 1 and row['unique_tiles'] >= baseline['unique_tiles']
              and row['maximum_off_track_counter'] <= 5 and row['endpoint_wheel_road_contacts'] >= 2)
        if ok:
            admissible.append(name)
    def key(name):
        row, spec = search_summaries[name], specifications[name]
        return (-row['unique_tiles'], -row['speed_m_s'], sum(abs(v) for v in spec['steer_offsets']),
                int(spec['brake_first_block']), name)
    admissible.sort(key=key)
    return dict(selected=admissible[0] if admissible else None, admissible=admissible,
        rule='zero contacts/damage, no terminal, baseline progress retained, offtrack<=5, >=2 road wheels; tiles/speed/control size/ID rank')
