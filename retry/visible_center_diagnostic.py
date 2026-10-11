"""One privileged DEV contrast: correct only visible detected obstacle centers.

The unchanged frozen116 archive is never a submission candidate with this
teacher input. Original pixels, detector count/order/radii, retained-track
prediction, routing and control source are preserved. Ambiguous matches stay
unchanged. The cached endpoint runner provides the one-use native budget.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct
import time

import numpy as np


OBSERVER_SHA256 = 'a9e2693d424b38744c50df288ce3dd6eb7bae9ae18c1e8be0e2b303703e8b36b'
OBS_BYTES = 4 * 84 * 84 * 4


def build_worker(destination):
    """Bind the existing observer plus one explicit detector-return hook."""
    source = Path(__file__).with_name('hud_contact_pixel_worker.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == OBSERVER_SHA256
    text = source.decode()

    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, old
        text = text.replace(old, new)

    replace('import base64\n', 'import base64\nimport importlib.util\nimport struct\n')
    replace('agent = Agent()\n', '''helper_path = clean / 'oracle_boundary.py'
spec = importlib.util.spec_from_file_location('oracle_boundary', helper_path)
oracle_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle_helper)
oracle_context = None
oracle_observed = {}
agent = Agent()
''')
    replace('    return output\n\n\ndef tracker', '''    corrected, receipt = oracle_helper.match_visible_centers(
        argument(args, kwargs, 'image', 0), output[1],
        oracle_context['gt_body_centers'], oracle_context['visible_coverage'])
    assert len(corrected) == len(output[1])
    assert all(a[2] == b[2] for a, b in zip(output[1], corrected))
    oracle_observed.update(receipt=receipt, original_detections=output[1],
                          corrected_detections=corrected,
                          privileged_diagnostic=True, submission_candidate=False)
    return output[0], corrected


def tracker''')
    replace("'observer_extra_vision_calls':0", "'observer_extra_vision_calls':1")
    replace("'ready':True,'simulator_imported':False,", """'ready':True,'simulator_imported':False,
                  'privileged_diagnostic':True,'submission_candidate':False,
                  'oracle_helper_sha256':hashlib.sha256(helper_path.read_bytes()).hexdigest(),
                  'input_contract':'original4pixels plus current visible ownership and GT centers',""")
    replace("    obs = np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(4,84,84).copy()", '''    packed = base64.b64decode(request['observation'], validate=True)
    obs_bytes = 4 * 84 * 84 * 4
    obs = np.frombuffer(packed[:obs_bytes], dtype=np.float32).reshape(4,84,84).copy()
    header_size = struct.unpack('<I', packed[obs_bytes:obs_bytes+4])[0]
    assert 0 < header_size <= 65536
    end = obs_bytes + 4 + header_size
    header = json.loads(packed[obs_bytes+4:end])
    assert header['kind'] == 'privileged_visible_centers_v1'
    centers = np.asarray(header['gt_body_centers'], dtype=np.float64).reshape(-1,2)
    assert len(centers) <= 6 and np.isfinite(centers).all()
    coverage = np.frombuffer(packed[end:], dtype=np.uint8).reshape(len(centers),84,84)
    assert all(np.any(layer) for layer in coverage)
    oracle_context = {'gt_body_centers':centers, 'visible_coverage':coverage}
    oracle_observed.clear()''')
    replace("'observer_extra_policy_calls':0,\n                    'memory':", """'observer_extra_policy_calls':0,
                    'oracle_probe':dict(oracle_observed),
                    'memory':""")
    replace('Read-only pixel observer for frozen original and HUD pedal-feedback archives.',
            'Privileged visible-center diagnostic for frozen HUD archives; not a submission.')
    replace("coordinate_scope='Original image-derived x/forward returns; no new world-coordinate transform'",
            "coordinate_scope='Original detections followed by visible GT center-only correction'")
    ast.parse(text)
    destination = Path(destination)
    with destination.open('x') as stream:
        stream.write(text)
    destination.chmod(0o600)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def pack_context(observation, context):
    assert observation.shape == (4, 84, 84) and observation.dtype == np.float32
    centers = np.asarray(context['body_centers'], dtype=np.float64).reshape(-1, 2)
    coverage = np.asarray(context['visible_coverage'])
    assert coverage.dtype == np.uint8 and coverage.shape == (len(centers), 84, 84)
    assert len(centers) <= 6 and all(np.any(layer) for layer in coverage)
    header = json.dumps({'kind': 'privileged_visible_centers_v1',
                         'gt_body_centers': centers.tolist()}, allow_nan=False).encode()
    packed = observation.tobytes() + struct.pack('<I', len(header)) + header + coverage.tobytes()
    assert packed[:OBS_BYTES] == observation.tobytes()
    return np.frombuffer(packed, dtype=np.uint8)


def oracle_episode(plan_path, plan, case, initial_pairs):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry import hud_feedback_generalization as recorder
    from retry import frozen_paired_evaluation as paired
    from retry.champion_dev_survey import diagnostic_episode
    from retry.visible_obstacle_oracle import current_visible_context

    factory, prepare = diagnose.make_env, runtime.prepare
    result_write, record_write = paired.write, recorder.write
    active = {'context_calls': 0, 'context_wall_s': 0.0, 'label_raster_passes': 0}

    def make_env(*args, **kwargs):
        env = factory(*args, **kwargs)
        active['env'] = env
        return env

    def prepare_worker(*args, **kwargs):
        worker = prepare(*args, **kwargs)
        assert worker.ready['privileged_diagnostic'] is True
        assert worker.ready['submission_candidate'] is False
        assert worker.ready['oracle_helper_sha256'] == plan['arms']['A']['assets']['oracle_boundary.py']['sha256']
        worker.configuration_ready_receipt['input_kind'] = 'privileged visible-center diagnostic'
        original_call = worker.call

        def call(operation, obs):
            if operation == 'act':
                before = time.perf_counter()
                context = current_visible_context(active['env'])
                active['context_wall_s'] += time.perf_counter() - before
                active['context_calls'] += 1
                active['label_raster_passes'] += context['receipt']['label_raster_passes']
            else:
                context = {'body_centers': np.empty((0, 2)),
                           'visible_coverage': np.empty((0, 84, 84), np.uint8)}
            response, elapsed = original_call(operation, pack_context(obs, context))
            if operation == 'act':
                assert response['oracle_probe']['privileged_diagnostic'] is True
                response['oracle_probe']['visible_context_receipt'] = context['receipt']
            return response, elapsed

        worker.call = call
        return worker

    def write_result(path, value, **kwargs):
        if Path(path).name == 'result.json':
            value.update(oracle_inputs_to_policy=True, privileged_diagnostic=True,
                         submission_candidate=False,
                         intervention='visible existing detection centers only',
                         oracle_context_calls=active['context_calls'],
                         oracle_context_wall_s=active['context_wall_s'],
                         oracle_label_raster_passes=active['label_raster_passes'])
        return result_write(path, value, **kwargs)

    def write_record(path, value, **kwargs):
        if Path(path).name == 'record-receipt.json':
            value.update(GT_sent_to_policy=True, privileged_diagnostic=True,
                         submission_candidate=False,
                         oracle_context_calls=active['context_calls'],
                         extra_native_renderer_calls=0)
        return record_write(path, value, **kwargs)

    diagnose.make_env, runtime.prepare = make_env, prepare_worker
    paired.write, recorder.write = write_result, write_record
    try:
        return diagnostic_episode(plan_path, plan, case, initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare = factory, prepare
        paired.write, recorder.write = result_write, record_write


def run(plan_path):
    from retry import cached_dev_comparison as comparison
    from retry.frozen_paired_evaluation import write

    plan = json.loads(Path(plan_path).read_text())
    assert plan['privileged_diagnostic'] is True and plan['submission_candidate'] is False
    assert plan['max_actions'] == 2000 and len(plan['cases']) == 1
    assert plan['arms']['A']['archive_sha256'] == plan['baseline_archive_sha256']
    original_episode = comparison.diagnostic_episode
    comparison.diagnostic_episode = oracle_episode
    try:
        report = comparison.run(plan_path)
    finally:
        comparison.diagnostic_episode = original_episode
    report.update(privileged_diagnostic=True, submission_candidate=False,
                  oracle_inputs_to_policy=True, no_promotion=True)
    # The canonical report explicitly carries the diagnostic boundary.
    write(Path(plan_path).parent / 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    report = run(parser.parse_args().plan)
    print(json.dumps({'status': report['status'],
                      'native_actions': report['cost']['native_wrapper_actions'],
                      'privileged_diagnostic': True, 'submission_candidate': False}))
    raise SystemExit(0 if report['failure'] is None else 1)
