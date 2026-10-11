"""Launch an immutable pixel-only research configuration on the current host.

The configuration binds an archive, external frozen assets and its actual worker.
This is a research execution adapter, not an official submission ZIP validator.
It never imports a simulator or reads a replay into the participant process.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import zipfile

import numpy as np

from retry.pixel_sandbox_runtime import SandboxWorker


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _relative(name):
    value = Path(name)
    if value.is_absolute() or '..' in value.parts or not value.parts:
        raise ValueError('Unsafe configuration member')
    return value


def _copy(source, destination, expected):
    assert sha(source) == expected, str(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert sha(destination) == expected
    destination.chmod(0o444)


def prepare(config, clean, sandbox):
    """Extract/verify assets, sanitize the environment and validate readiness.

    ``clean`` must be absent or empty. The caller freezes config and the native
    sandbox hash before launch. Assets and constants live beside ``package``.
    """
    assert config['type'] in ('champion', 'student')
    assert np.__version__ == '1.26.0'
    assert sys.version_info[:2] == (3, 11)
    clean = Path(clean).resolve()
    if clean.exists():
        assert clean.is_dir() and not any(clean.iterdir())
    else:
        clean.mkdir(parents=True, mode=0o700)
    clean.chmod(0o700)
    package = clean / 'package'
    package.mkdir()
    archive = Path(config['archive_path'])
    assert sha(archive) == config['archive_sha256']
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        assert len(names) == len(set(names))
        assert set(names) == set(config['members_sha256'])
        for name, expected in config['members_sha256'].items():
            member = zipped.getinfo(name)
            assert not stat.S_ISLNK(member.external_attr >> 16)
            target = package / _relative(name)
            data = zipped.read(name)
            assert hashlib.sha256(data).hexdigest() == expected
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o444)
    _copy(config['worker_path'], clean / 'worker.py', config['worker_sha256'])
    used = {'package', 'worker.py', 'home', 'tmp'}
    for name, asset in config.get('assets', {}).items():
        relative = _relative(name)
        assert relative.parts[0] not in used
        _copy(asset['path'], clean / relative, asset['sha256'])
    for name, value in config.get('constants', {}).items():
        relative = _relative(name)
        assert relative.parts[0] not in used and not (clean / relative).exists()
        target = clean / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
        target.chmod(0o444)
    for directory in sorted(package.rglob('*'), reverse=True):
        if directory.is_dir():
            directory.chmod(0o555)
    package.chmod(0o555)
    (clean / 'home').mkdir()
    (clean / 'tmp').mkdir()
    environment = {
        'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin',
        'HOME': str(clean / 'home'), 'TMPDIR': str(clean / 'tmp'),
        'LANG': 'C.UTF-8', 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
        'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1',
        'CUDA_VISIBLE_DEVICES': '', 'SDL_VIDEODRIVER': 'dummy',
        'SDL_AUDIODRIVER': 'dummy',
    }
    worker = SandboxWorker(
        [sys.executable, '-I', '-B', str(clean / 'worker.py'), str(package)],
        clean, environment, sandbox=Path(sandbox).resolve())
    worker.runtime_directory = clean
    worker.runtime_environment = environment
    try:
        worker.configuration_ready_receipt = validate_ready(worker, config)
    except BaseException:
        worker.close()
        raise
    return worker


def validate_ready(worker, config):
    """Check exact loaded module origins, versions, assets and local limits."""
    ready = worker.ready
    assert ready['ready'] is True and ready['simulator_imported'] is False
    assert ready['numpy_version'] == '1.26.0'
    assert len(ready['CPU_affinity']) == 1
    assert ready['address_space_limit_bytes'] == 1_024_000_000
    assert worker.memory_limit_bytes == 1_024_000_000
    assert worker.cold_start_ms <= 10_000
    assert len(worker.actor_pids) == 1
    assert not ready.get('python_audit_denied_events', [])
    package = worker.runtime_directory / 'package'
    key = 'policy_module_sha256' if config['type'] == 'champion' else 'module_sha256'
    hashes = ready[key]
    assert set(hashes) == set(ready['policy_modules']) and 'agent' in hashes
    for name, location in ready['policy_modules'].items():
        path = Path(location).resolve()
        assert path.is_relative_to(package)
        relative = str(path.relative_to(package))
        assert hashes[name] == config['members_sha256'][relative] == sha(path)
    if config['type'] == 'champion':
        assert ready['opencv_version'] == '4.8.1'
    else:
        assert ready['observer_additional_policy_calls'] == 0
        assert ready['privileged_diagnostic'] is False
        assert ready['input_contract'] == 'float32(4,84,84) grayscale only'
        assert ready['student_model_sha256'] == config['assets']['student.xml']['sha256']
        if config.get('intervention') == 'road_mask_only':
            mode = config['constants']['mask-config.json']
            assert set(mode) == {'source'} and mode['source'] in ('student', 'original')
            assert ready['intervention'] == 'road_mask_only'
            assert ready['mask_source'] == mode['source']
            assert ready['control_parameters'] == {
                'speed_cap': 28.0, 'lateral_fast': 7.0, 'lateral_safe': 5.0,
                'speed_gain': 11.4142485314592, 'speed_bias': -6.545558315185489}
            assert ready['distance_cap_applied'] is False and ready['curve_applied'] is False
            assert ready['observer_additional_model_calls'] == 0
            assert not any('distance_cap' in name or 'curve' in name for name in hashes)
            assert ready['student_source_sha256'] == config['assets']['student.py']['sha256']
            assert ready['boundary_source_sha256'] == config['assets']['boundary.py']['sha256']
            assert all(value['one_threshold_statement_replaced'] is True
                       for value in ready['mask_boundary'].values())
            assert set(ready['mask_boundary']) == {'routing_problem', 'ridge_path'}
        else:
            assert ready['curve_source_sha256'] == config['assets']['curve.py']['sha256']
            assert ready['curve_coefficient'] == config['constants']['curve-config.json']['coefficient']
    worker.check_memory()
    return {'module_hashes_exact': True, 'loaded_module_count': len(hashes),
            'one_native_actor': True, 'one_CPU_and_one_thread': True,
            'numpy_version': ready['numpy_version'],
            'memory_limit_bytes': worker.memory_limit_bytes,
            'input_kind': 'reset/act + official pixels only',
            'submission_qualification': False, 'fresh_machine_parity': False}


def validate_response(response, config, obs, operation):
    """Validate one response without an extra policy or student invocation."""
    assert operation in ('reset', 'act')
    assert obs.shape == (4, 84, 84) and obs.dtype == np.float32
    assert np.isfinite(obs).all() and obs.min() >= 0 and obs.max() <= 1
    assert not response.get('python_audit_denied_events', [])
    assert math_finite_nonnegative(response['rss_mib'])
    assert response['rss_mib'] * 1024 * 1024 <= 1_024_000_000
    assert math_finite_nonnegative(response['actor_cumulative_CPU_s'])
    if config['type'] == 'student':
        mask = np.frombuffer(base64.b64decode(response['student_mask_base64'], validate=True),
                             dtype=np.uint8).reshape(84, 84)
        original = ((obs[-1] > .32) & (obs[-1] < .47)).astype(np.uint8)
        receipt = response['student_receipt']
        assert np.isin(mask, [0, 1]).all() and np.all(mask <= original)
        assert hashlib.sha256(mask.tobytes()).hexdigest() == receipt['student_mask_sha256']
        assert hashlib.sha256(original.tobytes()).hexdigest() == receipt['original_P_sha256']
        assert receipt['added_cells'] == 0
        assert receipt['original_P_cells'] == int(original.sum())
        assert receipt['kept_cells'] == int(mask.sum())
        assert receipt['deleted_cells'] == int(original.sum() - mask.sum())
        if config.get('intervention') == 'road_mask_only':
            source = config['constants']['mask-config.json']['source']
            assert source in ('student', 'original')
            assert response['intervention'] == receipt['intervention'] == 'road_mask_only'
            assert response['mask_source'] == receipt['mask_source'] == source
            assert response['distance_cap_applied'] is False and response['curve_applied'] is False
            assert response['control_parameters'] == {
                'speed_cap': 28.0, 'lateral_fast': 7.0, 'lateral_safe': 5.0,
                'speed_gain': 11.4142485314592, 'speed_bias': -6.545558315185489}
            assert receipt['input_shape'] == [4, 84, 84]
            assert receipt['input_dtype'] == 'float32'
            assert receipt['input_kind'] == 'official_grayscale_only'
            assert receipt['mask_evaluations'] == 1
            assert receipt['model_mask_calls'] == int(source == 'student')
            if source == 'original':
                assert np.array_equal(mask, original) and receipt['inference_ms'] == 0
    if operation == 'reset':
        assert response['ok'] is True
        return None
    action = np.asarray(response['action'], dtype=np.float32)
    assert action.shape == (3,) and np.isfinite(action).all()
    assert np.all(action >= np.asarray([-1, 0, 0], np.float32))
    assert np.all(action <= np.asarray([1, 1, 1], np.float32))
    if config['type'] == 'student':
        calls = response['original_calls']
        assert all(calls.get(name) == 1 for name in ('detection', 'tracker', 'ridge', 'route', 'target'))
        assert calls.get('action_target', 0) + calls.get('fallback_action', 0) == 1
        if config.get('intervention') == 'road_mask_only':
            assert response['cap_diagnostic'] is None and response['curve_diagnostic'] is None
            telemetry = response['route_telemetry']
            assert np.array_equal(action, np.asarray(telemetry['controller_output'], dtype=np.float32))
            assert telemetry['controller_before']['speed_cap'] == 28.0
            assert telemetry['controller_after']['speed_cap'] == 28.0
            assert telemetry['controller_after']['previous_steer'] == response['previous_steer_after']
        else:
            curve = response['curve_diagnostic']
            if curve is not None:
                assert curve['coefficient'] == config['constants']['curve-config.json']['coefficient']
                assert curve['steering_unchanged'] is True
    return action


def math_finite_nonnegative(value):
    return bool(np.isfinite(value) and value >= 0)
