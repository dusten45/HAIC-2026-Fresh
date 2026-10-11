"""Privileged current-camera road-mask diagnostic; never a submission policy."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np
import pygame
from pygame import gfxdraw

from core.vendor.car_racing import SCALE, STATE_H, STATE_W, WINDOW_H, WINDOW_W, ZOOM


def camera(raw):
    angle = -float(raw.car.hull.angle)
    zoom = .1*SCALE*max(1-raw.t,0)+ZOOM*SCALE*min(raw.t,1)
    position = raw.car.hull.position
    scroll = pygame.math.Vector2((-position[0]*zoom,-position[1]*zoom)).rotate_rad(angle)
    translation = WINDOW_W/2+scroll.x, WINDOW_H/4+scroll.y
    return zoom, translation, angle


def render_road_mask(polygons, zoom, translation, angle, draw):
    """Use the native raster/flip/96-pixel scaling and wrapper's 84-pixel resize."""
    surface = pygame.Surface((WINDOW_W,WINDOW_H)); surface.fill((0,0,0))
    visible = 0
    for polygon in polygons:
        projected = [pygame.math.Vector2(point).rotate_rad(angle)*zoom+translation for point in polygon]
        xs = [p.x for p in projected]; ys = [p.y for p in projected]
        if max(xs)<0 or min(xs)>=WINDOW_W or max(ys)<0 or min(ys)>=WINDOW_H: continue
        visible += 1
        draw(surface, polygon, (255,255,255), zoom, translation, angle, clip=False)
    surface = pygame.transform.flip(surface,False,True)
    surface = pygame.transform.smoothscale(surface,(STATE_W,STATE_H))
    rgb = np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    gray = cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY)
    return (gray >= 128).astype(np.uint8), visible


def draw_polygon(surface, polygon, color, zoom, translation, angle, clip=False):
    # The native helper ignores its surface argument and draws on self.surf.
    # Copy its raster operations onto a separate canvas without mutating raw.surf.
    points = [pygame.math.Vector2(point).rotate_rad(angle) for point in polygon]
    points = [(p.x*zoom+translation[0],p.y*zoom+translation[1]) for p in points]
    gfxdraw.aapolygon(surface,points,color)
    gfxdraw.filled_polygon(surface,points,color)


def road_mask(env):
    raw = env.unwrapped
    polygons = [[tuple(tile.GetWorldPoint(v)) for v in tile.fixtures[0].shape.vertices] for tile in raw.road]
    mask, visible = render_road_mask(polygons,*camera(raw),draw_polygon)
    return mask, {'visible_road_polygons':visible,'road_pixels':int(mask.sum()),
                  'mask_sha256':hashlib.sha256(mask.tobytes()).hexdigest(),
                  'scope':'current camera only; occluded road included; curb excluded',
                  'observation_time_s':raw.t}


def main():
    from retry import fresh_dev_distribution as cohort
    from retry.full_route_reproduction import truth
    from retry.qualify_pixel_package import PipeWorker
    parser=argparse.ArgumentParser(); parser.add_argument('--plan',type=Path,required=True)
    args=parser.parse_args(); path=args.plan.resolve(); directory=path.parent
    plan=json.loads(path.read_text()); started=time.perf_counter()
    assert cohort.sha(path)==(directory/'plan.sha256').read_text().split()[0]
    for name,wanted in plan['source_sha256'].items(): assert cohort.sha(Path(name))==wanted,name
    assert len(plan['cases'])==3 and plan['max_actions']==8000
    execution=cohort.clone(plan,directory)
    # Boundary helper belongs to the evaluator worker, outside the archived policy.
    helper=execution[0]/'boundary.py'; helper.write_bytes(Path(plan['boundary_path']).read_bytes()); helper.chmod(0o444)
    assert cohort.sha(helper)==cohort.sha(Path(plan['boundary_path']))
    official_factory=cohort.make_env; original_worker=cohort.PipeWorker
    active={}; results=[]; stop_reason=None

    class RoadWorker(PipeWorker):
        def call(self,operation,observation):
            before=time.perf_counter(); mask, detail=road_mask(active['env'])
            active['mask_wall_s']+=time.perf_counter()-before; active['mask_calls']+=1
            self.last_mask_receipt=detail
            packed=np.concatenate((observation,mask[None].astype(np.float32)),axis=0)
            response,duration=super().call(operation,packed)
            response['road_mask_receipt']=detail
            if operation=='act': response['route_telemetry']['privileged_road_mask_input']=detail
            return response,duration

    cohort.PipeWorker=RoadWorker
    try:
        for case in plan['cases']:
            if stop_reason is not None:
                result={'id':case['id'],'status':'UNEXECUTED','reason':stop_reason,'charged_wrapper_actions':0,'episode_count':0,'retries':0}
            else:
                receipt={}; active.update(mask_wall_s=0.,mask_calls=0)
                def guarded_factory():
                    env=official_factory(); active['env']=env; original_reset=env.reset
                    def reset(*args,**kwargs):
                        obs,info=original_reset(*args,**kwargs)
                        assert hashlib.sha256(obs.tobytes()).hexdigest()==case['baseline_initial_observation_sha256']
                        expected=case['baseline_initial_truth']; actual=truth(env)
                        assert {k:actual[k] for k in expected}==expected
                        receipt.update(initial_full_pixel_stack_equal=True,recorded_initial_truth_equal=True)
                        return obs,info
                    env.reset=reset
                    return env
                cohort.make_env=guarded_factory
                try: result,technical_stop=cohort.episode(case,plan,path,execution)
                finally: cohort.make_env=official_factory
                result.update(baseline_identity_receipt=receipt,road_mask_calls=active['mask_calls'],
                              road_mask_generation_wall_s=active['mask_wall_s'],privileged_road_input=True,
                              submission_candidate=False,policy_changed=True)
                baseline=case['baseline_result']; result['baseline_result']=baseline
                result['control_completion_regression']=bool(case['role']=='normal_control' and baseline['completed'] and result['status']=='DNF')
                cohort.write(directory/case['id']/'result.json',result)
                if technical_stop: stop_reason='INCONCLUSIVE_TECHNICAL_OR_RESOURCE_BOUNDARY'
            results.append(result)
            report={'results':results,'stop_reason':stop_reason,'plan_sha256':cohort.sha(path),
                    'wall_s':time.perf_counter()-started,'status_counts':{s:sum(r['status']==s for r in results) for s in ('COMPLETE','DNF','RESOURCE_CENSORED','UNEXECUTED')},
                    'new_baseline_runs':0,'new_learning':0,'coefficient_tuning':0,'protected_runs':0,
                    'single_intervention':'current-camera ground-truth road threshold mask only; occluded road included',
                    'original_v2_archive_preserved':True,'submission_candidate':False}
            cohort.write(directory/'diagnostic-report.json',report)
            print(json.dumps({k:result.get(k) for k in ('id','status','official_progress','failure_type','official_lap_ms','damage','charged_wrapper_actions','error')}),flush=True)
    finally:
        cohort.PipeWorker=original_worker; cohort.make_env=official_factory
    report['charged_wrapper_actions']=json.loads((directory/'budget.json').read_text())['actions']
    report['verdict']='INCONCLUSIVE' if stop_reason else 'DIAGNOSTIC_COMPLETED_NO_PROMOTION'
    cohort.write(directory/'diagnostic-report.json',report)
    return int(stop_reason is not None)


if __name__=='__main__': raise SystemExit(main())
