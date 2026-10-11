"""One privileged native episode with original raw road mask intersected with GT.

The visible-GT generator, mask substitution sites, archived policy, and inherited
postprocessing are reused unchanged. This is an evaluator diagnostic, not a
legal pixel-only policy. Private plans and complete receipts stay outside git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from retry import fresh_dev_distribution as native
from retry import paired_closed_loop as paired
from retry.qualify_pixel_package import PipeWorker
from retry.visible_road_occlusion import visible_road_mask


def intersect_raw_road(observation, visible):
    """Use the exact image and raw threshold of both archived road functions."""
    assert observation.shape == (4,84,84) and observation.dtype == np.float32
    assert visible.shape == (84,84) and visible.dtype == np.uint8
    assert np.isin(visible,[0,1]).all()
    image = observation[-1]
    original = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
    intersection = original & visible
    assert np.all(intersection <= original)
    assert np.array_equal(original-intersection, original*(1-visible))
    return original, intersection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    path = parser.parse_args().plan.resolve()
    directory = path.parent
    plan = json.loads(path.read_text())
    assert native.sha(path) == (directory/'plan.sha256').read_text().split()[0]
    assert plan['candidate']['archive_sha256'] == plan['original_v2_archive_sha256']
    assert plan['diagnostic_formula'] == 'C=P47 & B_visible_GT'
    factory, worker, clone = native.make_env, native.PipeWorker, native.clone
    active = {'mask_wall_s':0., 'mask_calls':0}
    arrays = {'original_raw':[], 'visible_GT':[], 'intersection':[], 'operation':[]}
    receipts_path = directory/'mask-receipts.jsonl'
    receipts = receipts_path.open('x'); receipts_path.chmod(0o600)

    def captured_factory():
        env = factory()
        active['env'] = env
        return env

    def boundary_clone(*args):
        execution = clone(*args)
        helper = execution[0]/'boundary.py'
        helper.write_bytes(Path(plan['boundary_path']).read_bytes()); helper.chmod(0o444)
        assert native.sha(helper) == native.sha(Path(plan['boundary_path']))
        return execution

    class DeletionWorker(PipeWorker):
        def call(self,operation,observation):
            before = time.perf_counter()
            visible, detail = visible_road_mask(active['env'])
            original, intersection = intersect_raw_road(observation,visible)
            active['mask_wall_s'] += time.perf_counter()-before
            active['mask_calls'] += 1
            if active['mask_calls'] == 1:
                assert detail['mask_sha256'] == plan['initial_visible_GT_sha256']
            receipt = {'operation':operation,'call_index':active['mask_calls'],
                       'observation_sha256':native.sha_bytes(observation),
                       'original_raw_sha256':native.sha_bytes(original),
                       'visible_GT_sha256':native.sha_bytes(visible),
                       'intersection_sha256':native.sha_bytes(intersection),
                       'original_raw_cells':int(original.sum()),
                       'visible_GT_cells':int(visible.sum()),
                       'intersection_cells':int(intersection.sum()),
                       'deleted_raw_cells':int((original-intersection).sum()),
                       'added_raw_cells':0,'subset_of_original_raw':True,
                       'visible_provenance':detail}
            arrays['original_raw'].append(original)
            arrays['visible_GT'].append(visible)
            arrays['intersection'].append(intersection)
            arrays['operation'].append(0 if operation == 'reset' else 1)
            receipts.write(json.dumps(receipt,allow_nan=False)+'\n'); receipts.flush()
            packed = np.concatenate((observation,intersection[None].astype(np.float32)),axis=0)
            response,duration = super().call(operation,packed)
            response['road_intersection_receipt'] = receipt
            if operation == 'act':
                response['route_telemetry']['privileged_road_mask_input'] = receipt
            return response,duration

    native.make_env, native.PipeWorker, native.clone = captured_factory, DeletionWorker, boundary_clone
    try:
        exit_code = paired.main()
    finally:
        native.make_env, native.PipeWorker, native.clone = factory, worker, clone
        receipts.close()
        target = directory/'road-masks.npz'
        np.savez_compressed(target,**{key:np.asarray(value,dtype=np.uint8) for key,value in arrays.items()})
        target.chmod(0o600)
        native.write(directory/'mask-cost.json',{
            'mask_calls':active['mask_calls'],'mask_generation_wall_s':active['mask_wall_s'],
            'extra_environment_steps':0,'extra_policy_calls':0,
            'visible_generator_unchanged':True,'new_hole_filling':False,
            'intersection_before_inherited_postprocessing':True})
    result = json.loads((directory/'paired-result.json').read_text())
    result.update(privileged_GT_diagnostic=True,legal_submission_candidate=False,promotion=False,
                  policy_changed_relative_to_original_v2=True,policy_changed_during_episode=False,
                  diagnostic_formula=plan['diagnostic_formula'],
                  mask_calls=active['mask_calls'],mask_generation_wall_s=active['mask_wall_s'],
                  raw_mask_additions=0,road_masks_sha256=native.sha(directory/'road-masks.npz'),
                  mask_receipts_sha256=native.sha(receipts_path))
    native.write(directory/'diagnostic-result.json',result)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
