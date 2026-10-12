"""Current-policy visible-road diagnostic with explicit privileged-input receipts."""
import hashlib
from pathlib import Path
import time

import numpy as np

from retry.compact_dev_diagnostic import ScalarStats


def check_ready(worker, config):
    r=worker.ready
    assert r['privileged_road_input'] and not r['submission_candidate']
    assert r['boundary_sha256']==config['assets']['boundary.py']['sha256']
    assert set(r['mask_boundary'])=={'routing_problem','ridge_path'}
    assert all(v['one_threshold_statement_replaced'] for v in r['mask_boundary'].values())
    worker.configuration_ready_receipt.update(
        input_kind='four original official pixel planes plus privileged visible-road plane',
        privileged_road_input=True,submission_candidate=False)


class RoadStats(ScalarStats):
    def __init__(self,state):
        super().__init__();self.state=state;self.shadows=[]

    def add(self,row):
        row.update(self.state['extra'])
        if self.state.get('shadow') is not None:self.shadows.append(self.state['shadow'])
        super().add(row)

    def summary(self,completed):
        d=super().summary(completed);d.pop('near5_rows',None)
        d.update(road_input_checks=self.state['checks'],road_mask_sequence_sha256=self.state['mask_hash'].hexdigest(),
            same_input_route_comparisons=self.shadows,
            first_mask_change=self.state.get('first_change'),
            privileged_road_input=True,submission_candidate=False,
            oracle_scope='Only current renderer-visible physical road occupancy B=A & ~O replaces two road threshold arrays. Existing crop/7x7 close/distance/ridge processing remains. Occluded and offscreen road is not supplied; unchanged close may infer holes.',
            obstacle_and_speed_scope='Original four pixel planes reach detector/tracker/HUD unchanged. Renderer GT is used only for road visibility/occlusion; no obstacle coordinates, speed, world path or future road reaches the Agent.',
            shadow_scope='Pure route queries only at registered steps, on the oracle trajectory with original pixel-road mask; no new Agent/vision/tracker calls or native replay.')
        return d


def road_episode(plan_path,plan,case,initial_pairs):
    from retry import diagnose,frozen_composite_runtime as runtime,frozen_paired_evaluation as evaluator
    from retry.compact_dev_diagnostic import compact_episode
    from retry.visible_road_occlusion import visible_road_mask

    old_factory,old_prepare,old_write=diagnose.make_env,runtime.prepare,evaluator.write
    state=dict(mask_hash=hashlib.sha256(),checks=dict(calls=0,act_calls=0,
        original_four_plane_mismatches=0,mask_mismatches=0,mask_changed_actions=0,
        added_cells=0,removed_cells=0,planning_ROI_changed_actions=0,
        planning_ROI_added_cells=0,planning_ROI_removed_cells=0,
        removed_occluded_cells=0,visible_mask_generation_wall_s=0.,pure_route_shadow_queries=0))
    def factory(*args,**kwargs):
        env=old_factory(*args,**kwargs);state['env']=env;return env

    def prepare(config,*args,**kwargs):
        worker=old_prepare(config,*args,**kwargs);check_ready(worker,config);old_call=worker.call
        def call(operation,observation):
            started=time.perf_counter();mask,receipt=visible_road_mask(state['env'])
            c=state['checks'];c['visible_mask_generation_wall_s']+=time.perf_counter()-started
            packed=np.concatenate((observation,mask[None].astype(np.float32)))
            response,elapsed=old_call(operation,packed)
            rr=response['road_input_receipt']
            assert rr['original_four_planes_sha256']==hashlib.sha256(observation.tobytes()).hexdigest()
            assert rr['supplied_mask_sha256']==receipt['mask_sha256']==hashlib.sha256(mask.tobytes()).hexdigest()
            c['calls']+=1;state['mask_hash'].update(mask.tobytes())
            if operation=='act':
                c['act_calls']+=1
                pixel=((observation[-1]>.32)&(observation[-1]<.47)).astype(np.uint8)
                added=mask>pixel;removed=mask<pixel
                # Include the downstream 7x7-close neighborhood around the route ROI.
                roi=np.s_[21:60,0:84]
                extra=dict(road_added_cells=int(added.sum()),road_removed_cells=int(removed.sum()),
                    planning_ROI_added_cells=int(added[roi].sum()),planning_ROI_removed_cells=int(removed[roi].sum()),
                    occluded_road_cells_removed=receipt['removed_occluded_road_pixels'])
                c['mask_changed_actions']+=bool(added.any() or removed.any())
                c['added_cells']+=extra['road_added_cells'];c['removed_cells']+=extra['road_removed_cells']
                c['planning_ROI_changed_actions']+=bool(added[roi].any() or removed[roi].any())
                c['planning_ROI_added_cells']+=extra['planning_ROI_added_cells'];c['planning_ROI_removed_cells']+=extra['planning_ROI_removed_cells']
                c['removed_occluded_cells']+=extra['occluded_road_cells_removed']
                if state.get('first_change') is None and (added[roi].any() or removed[roi].any()):
                    state['first_change']=dict(step=c['act_calls'],**extra)
                shadow=response.get('road_route_shadow');c['pure_route_shadow_queries']+=shadow is not None
                state.update(extra=extra,shadow=shadow)
            return response,elapsed
        worker.call=call;return worker

    def write(path,value,**kwargs):
        if Path(path).name=='result.json':
            value.update(oracle_inputs_to_policy=True,privileged_road_input=True,submission_candidate=False,
                oracle_input_scope='Only current visible-road binary mask; four original observation planes unchanged')
        old_write(path,value,**kwargs)

    diagnose.make_env,runtime.prepare,evaluator.write=factory,prepare,write
    try:
        return compact_episode(plan_path,plan,case,initial_pairs,[],stats_factory=lambda:RoadStats(state))
    finally:
        diagnose.make_env,runtime.prepare,evaluator.write=old_factory,old_prepare,old_write
