"""Register four fresh identities using source-only road and obstacle functions.

The caller supplies a frozen contract and a private exclusion snapshot. No
policy, renderer, environment or physics runtime is imported. This module is
an identity registration tool; registration does not authorize an evaluation.
Detailed seeds and coordinates must remain in the caller's private directory.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


EXCLUSION_KEYS = (
    'excluded_seeds', 'excluded_road_geometry_sha256',
    'excluded_obstacle_spec_sha256', 'excluded_physical_obstacles_sha256',
    'excluded_obstacle_rng_entropy', 'excluded_parent_entropy_vectors',
)


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_sha(values):
    return hashlib.sha256(np.asarray(values, dtype='<f8').tobytes(order='C')).hexdigest()


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    Path(path).chmod(0o600)


def source_only_guard():
    forbidden = ('Box2D', 'core.vendor.car_racing', 'env_wrapper')
    assert not any(name.startswith(forbidden) for name in sys.modules), 'Physics import'


def register(contract_path, output_dir):
    contract_path, output_dir = Path(contract_path).resolve(), Path(output_dir).resolve()
    assert np.__version__ == '1.26.0'
    expected_hash = contract_path.with_suffix('.sha256').read_text().split()[0]
    contract_hash = file_sha(contract_path)
    assert expected_hash == contract_hash, 'Contract hash'
    contract = json.loads(contract_path.read_text())
    assert contract['protocol'] == 'identity-only-four-v1'
    assert contract['authorized_to_draw'] is True
    assert contract['condition_draw_before_contract'] == 0
    assert contract['track_ids'] == [1, 2, 3, 4]
    assert contract['arm_orders'] == [['A', 'B'], ['B', 'A'], ['A', 'B'], ['B', 'A']]
    assert contract['case_order'] == [0, 1, 2, 3]
    assert contract['difficulty_or_performance_filter'] is False
    deadline = dt.datetime.fromisoformat(contract['selection_deadline_utc'])
    assert deadline.tzinfo is not None

    def check_time():
        assert dt.datetime.now(dt.timezone.utc) < deadline, 'Selection deadline'

    check_time()
    assert output_dir.exists() and output_dir.is_dir()
    for name in ('draw-receipt.json', 'split.json', 'split.sha256', 'selection-receipt.json'):
        assert not (output_dir / name).exists(), 'One-use output exists'
    snapshot_path = Path(contract['exclusion_snapshot_path']).resolve()
    assert file_sha(snapshot_path) == contract['exclusion_snapshot_sha256']
    metadata = json.loads(snapshot_path.read_text())
    excluded = {key: {tuple(value) if isinstance(value, list) else value
                     for value in metadata[key]} for key in EXCLUSION_KEYS}
    parent_words = {word for vector in excluded['excluded_parent_entropy_vectors'] for word in vector}
    helper_path = Path(contract['geometry_helper_path']).resolve()
    official_path = Path(contract['official_road_source_path']).resolve()
    obstacle_path = Path(contract['obstacle_source_path']).resolve()
    project_root = Path(contract['project_root']).resolve()
    for path in (Path(__file__).resolve(), helper_path, official_path, obstacle_path):
        assert str(path) in contract['source_sha256'], 'Required source unsealed'
    for path, expected in contract['source_sha256'].items():
        assert file_sha(path) == expected, 'Source hash'
    source_only_guard()
    sys.path.insert(0, str(project_root))
    from core.track_variables import _place_obstacles, OBSTACLE_RNG_STREAM
    spec = importlib.util.spec_from_file_location('identity_coordinate_prefix', helper_path)
    geometry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry)
    assert geometry.SOURCE_SHA256 == file_sha(official_path)
    assert geometry.EXTRACTED_PREFIX_AST_SHA256 == contract['coordinate_prefix_ast_sha256']
    source_only_guard()
    check_time()
    assert file_sha(contract_path) == contract_hash
    wall, cpu = time.perf_counter(), time.process_time()

    # No geometry is evaluated until the first uniform draw is durably recorded.
    rejected_parent_vectors = []
    while True:
        check_time()
        raw = os.urandom(16)
        initial_seeds = [int(value) for value in np.frombuffer(raw, dtype='<u4')]
        if tuple(initial_seeds) not in excluded['excluded_parent_entropy_vectors']:
            break
        rejected_parent_vectors.append({'bytes_hex': raw.hex(), 'reason': 'parent_vector_identity'})
    draw = {
        'stage': contract['stage'], 'contract_sha256': contract_hash,
        'drawn_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'initial_osurandom_bytes_hex': raw.hex(), 'initial_seed_draw': initial_seeds,
        'parent_entropy_vector': initial_seeds,
        'rejected_parent_vectors': rejected_parent_vectors,
        'track_ids': contract['track_ids'], 'case_order': contract['case_order'],
        'arm_orders': contract['arm_orders'],
        'selection': 'Single 16-byte draw, four little-endian uint32 seeds; identity-only replacements',
    }
    write_once(output_dir / 'draw-receipt.json', draw)
    # Keep the original draw vector even when one child seed is replaced.
    excluded['excluded_parent_entropy_vectors'].add(tuple(initial_seeds))
    cases, rejections = [], []
    for index, label in enumerate(contract['track_ids']):
        seed = initial_seeds[index]
        while True:
            check_time()
            seed_conflict = seed in excluded['excluded_seeds'] or seed in parent_words
            if seed_conflict:
                collisions = ['seed_or_parent_word_identity']
            else:
                # Official failed-track retry uses the same RNG and same seed.
                # Obstacle generation errors are technical STOPs, never a redraw.
                track, attempts = geometry.track_for_seed(seed)
                road_hash = geometry.geometry_hash(track)
                obstacles = _place_obstacles(label, seed, track, 40 / 6)
                values = np.asarray([[*item.position, item.radius] for item in obstacles], dtype='<f8')
                assert values.shape == (6, 3) and np.isfinite(values).all()
                spec_hash = array_sha(values)
                physical_hash = array_sha(values.astype(np.float32).astype(float))
                lineage = (label, seed, int(OBSTACLE_RNG_STREAM))
                collisions = [name for name, conflict in (
                    ('road_geometry', road_hash in excluded['excluded_road_geometry_sha256']),
                    ('obstacle_spec', spec_hash in excluded['excluded_obstacle_spec_sha256']),
                    ('physical_obstacles', physical_hash in excluded['excluded_physical_obstacles_sha256']),
                    ('obstacle_rng', lineage in excluded['excluded_obstacle_rng_entropy']),
                ) if conflict]
            if not collisions:
                break
            replacement = os.urandom(4)
            rejections.append({'case_index': index, 'rejected_seed': seed,
                               'identity_collisions': collisions,
                               'replacement_bytes_hex': replacement.hex()})
            seed = int.from_bytes(replacement, 'little')
        cases.append({
            'id': f'holdout{contract["stage"]}-{index}', 'case_index': index,
            'split': f'HOLDOUT_{contract["stage"]}', 'seed': seed, 'track_id': label,
            'road_geometry_sha256': road_hash, 'road_point_count': len(track),
            'source_track_generation_attempts': attempts,
            'obstacle_spec_sha256': spec_hash,
            'expected_physical_obstacles_sha256': physical_hash,
            'obstacle_rng_entropy': list(lineage), 'arm_order': contract['arm_orders'][index],
            'condition': 'Official grass friction .6, six radius1.2 obstacles; label selects obstacle RNG only',
        })
        for key, value in (
            ('excluded_seeds', seed), ('excluded_road_geometry_sha256', road_hash),
            ('excluded_obstacle_spec_sha256', spec_hash),
            ('excluded_physical_obstacles_sha256', physical_hash),
            ('excluded_obstacle_rng_entropy', lineage),
        ):
            excluded[key].add(value)

    assert len({case['seed'] for case in cases}) == len({case['road_geometry_sha256'] for case in cases}) == 4
    assert file_sha(contract_path) == contract_hash
    assert file_sha(snapshot_path) == contract['exclusion_snapshot_sha256']
    for path, expected in contract['source_sha256'].items():
        assert file_sha(path) == expected, 'Post-selection source hash'
    source_only_guard()
    check_time()
    result = {
        'stage': contract['stage'], 'registered_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'contract_sha256': contract_hash, 'cases': cases,
        'ordered_cases': [cases[index]['id'] for index in contract['case_order']],
        'family_entropy': initial_seeds, 'collision_redraws': rejections,
        'draw_receipt_sha256': file_sha(output_dir / 'draw-receipt.json'),
        'exclusion_snapshot_sha256': contract['exclusion_snapshot_sha256'],
        'source_sha256': contract['source_sha256'],
        'coordinate_prefix_ast_sha256': contract['coordinate_prefix_ast_sha256'],
        'difficulty_or_performance_filter': False,
        'selection': 'Keep first identity-valid seed for each fixed label; no ranking or geometry/difficulty filtering',
        'physical_hash_coverage_limit': metadata['physical_hash_coverage_limit'],
        'new_environment_world_physics_policy_model_calls': 0,
        'protected_performance_reads': 0, 'SEALED_raw_opened': False,
        'registration_alone_authorizes_evaluation': False,
        'selection_wall_s': time.perf_counter() - wall, 'selection_CPU_s': time.process_time() - cpu,
    }
    write_once(output_dir / 'split.json', result)
    split_hash = file_sha(output_dir / 'split.json')
    with (output_dir / 'split.sha256').open('x') as stream:
        stream.write(split_hash + '  split.json\n')
    (output_dir / 'split.sha256').chmod(0o600)
    receipt = {
        'stage': contract['stage'], 'status': 'REGISTERED_NOT_OPENED', 'registered_conditions': 4,
        'arm_order_counts': {'AB': 2, 'BA': 2}, 'identity_rejections': len(rejections),
        'parent_vector_rejections': len(rejected_parent_vectors),
        'prior_exclusion_counts': {key: len(metadata[key]) for key in EXCLUSION_KEYS},
        'contract_sha256': contract_hash, 'split_sha256': split_hash,
        'exclusion_snapshot_sha256': contract['exclusion_snapshot_sha256'],
        'draw_receipt_sha256': file_sha(output_dir / 'draw-receipt.json'),
        'selection_wall_s': result['selection_wall_s'], 'selection_CPU_s': result['selection_CPU_s'],
        'new_environment_world_physics_policy_model_calls': 0,
        'protected_performance_reads': 0, 'SEALED_raw_opened': False,
    }
    write_once(output_dir / 'selection-receipt.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(register(args.contract, args.output_dir)))


if __name__ == '__main__':
    main()
