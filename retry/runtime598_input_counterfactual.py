"""External-only saved-checkpoint diagnosis; never used by the Agent."""
import argparse
import dataclasses
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np


def load(path):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('checkpoint_directory')
    parser.add_argument('fixture');parser.add_argument('output_directory')
    args=parser.parse_args();directory=Path(args.checkpoint_directory);out=Path(args.output_directory)
    out.mkdir(exist_ok=False);start=time.perf_counter();cpu=time.process_time()
    sys.path.insert(0,str(directory/'package'));import runtime598 as core
    from retry.runtime598_diagnostic import dump
    import cv2
    checkpoint=load(directory/'checkpoint-private.json');truth=load(directory/'external-truth-private.json')
    fixture=load(args.fixture);static=fixture['static'];h=truth['hull']
    image=cv2.imread(str(directory/'initial-private.png'),0)
    initial=np.repeat((image/255.).astype(np.float32)[None],4,axis=0)
    assert hashlib.sha256(initial.tobytes()).hexdigest()==static['observation_sha256'],'DIFFERENT_WORLD_FIXTURE'
    co=math.cos(h['angle']);si=math.sin(h['angle'])
    def vector(v):return (co*v[0]+si*v[1],-si*v[0]+co*v[1])
    def position(p):return vector((p[0]-h['position'][0],p[1]-h['position'][1]))
    roads=[(tuple(position(v) for v in poly),grip) for poly,grip in static['roads']]
    boundary=[(position(a),position(b)) for a,b in static['boundary']]
    obstacles=[(position(center),radius) for center,radius in static['obstacles']]
    observed=core.Scene(checkpoint['roads'],checkpoint['boundary'],checkpoint['obstacles'])
    exact=core.Scene(roads,boundary,obstacles)
    estimated=core.load_required_root(checkpoint['root'])

    # Measured rigid state in the camera frame. Unrecorded relative wheel rates
    # and clip history stay estimated; this is not a full true-state certificate.
    mass=static['root']['planar']['linear']['mass'];mh=h['mass'];mw=(mass-mh)/4.
    center_world=tuple((mh*h['world_center'][j]+mw*sum(w['position'][j] for w in truth['wheels']))/mass for j in range(2))
    velocity_world=tuple((mh*h['velocity'][j]+mw*sum(w['velocity'][j] for w in truth['wheels']))/mass for j in range(2))
    levers=tuple(vector((w['position'][0]-center_world[0],w['position'][1]-center_world[1])) for w in truth['wheels'])
    wheel_inertias=tuple(static['root']['planar']['wheel_inertias'])
    rh=tuple(h['world_center'][j]-center_world[j] for j in range(2))
    central_hull_I=h['inertia']-mh*sum(v*v for v in h['local_center'])
    inertia=central_hull_I+mh*sum(v*v for v in rh)+sum(I+mw*sum(v*v for v in r) for I,r in zip(wheel_inertias,levers))
    rates=estimated.planar.rates
    wheels=tuple(core.Wheel(w['omega'],w['gas'],w['angle']-h['angle'],w['friction'],
                 vector((w['velocity'][0]-velocity_world[0],w['velocity'][1]-velocity_world[1]))) for w in truth['wheels'])
    linear=core.State(vector(velocity_world),wheels,mass,truth['engine_multiplier'])
    joints=tuple(w['joint_angle'] for w in truth['wheels'])
    planar=core.Planar(linear,levers,inertia,inertia*h['angular_velocity']+sum(I*r for I,r in zip(wheel_inertias,rates)),
        h['angular_velocity'],0.,joints,rates,wheel_inertias,estimated.planar.steer,truth['steering_multiplier'])
    measured=core.Geometry(planar,position(center_world),estimated.roads,estimated.current_contacts,
        400.*truth['grass_friction_multiplier']*truth['grip_multiplier'],estimated.skin)
    measured_origin,measured_hull_velocity=core.hull_pose(measured)
    representation_position_error=math.hypot(*measured_origin)
    representation_velocity_error=math.dist(measured_hull_velocity,vector(h['velocity']))
    assert representation_position_error<1e-5 and representation_velocity_error<1e-5,'FRAME_CONVERSION'

    def with_scene(root,scene):
        contacts=tuple(core.indexed_contacts(core.rectangle(tuple(root.center[j]+r[j] for j in range(2)),w.heading),
            scene.roads,scene.index,root.skin) for r,w in zip(root.planar.levers,root.planar.linear.wheels))
        return dataclasses.replace(root,roads=scene.roads,current_contacts=contacts)

    dump(out/'inputs-private.json',dict(estimated=estimated,measured=measured,roads=roads,boundary=boundary,obstacles=obstacles))
    results=[];ticks=0
    # The original A cell already has an exactly replayed saved report. Change
    # only one input axis at a time, then check their joint effect, without tuning.
    for label,root,scene in [('measured_vehicle_observed_map',measured,observed),
                             ('estimated_vehicle_true_map',estimated,exact),
                             ('measured_vehicle_true_map',measured,exact)]:
        assert time.process_time()-cpu<850. and time.perf_counter()-start<2300.
        controller=core.Controller(checkpoint['high'],checkpoint['low'],scene)
        controller.model[0]=checkpoint['counter_before'];root=with_scene(root,scene)
        before=controller.model[0];begin=time.perf_counter();begin_cpu=time.process_time()
        action,report=controller.select(root,checkpoint['progress'],checkpoint['hold'],checkpoint['launch_history'],checkpoint['running_history'])
        used=controller.model[0]-before;ticks+=used
        dump(out/(label+'-private.json'),dict(action=action,report=report,root=root))
        trials=report.get('trials',report.get('reports',[]));reasons=[t['reason'] for t in trials]
        row=dict(label=label,admitted=action is not None,mode=report['mode'],
                 rejection_counts={r:reasons.count(r) for r in set(reasons)},model_ticks=used,
                 CPU_s=time.process_time()-begin_cpu,wall_s=time.perf_counter()-begin)
        results.append(row);assert ticks<=100000 and row['wall_s']<5.,'DIAGNOSTIC_LIMIT'
    # Compare the old first-failure polygons directly with the saved true road.
    comparisons=[]
    for event in load(directory/'geometry-probe-private.json'):
        poly=event['polygon'];distance=min(core.polygon_distance(poly,edge) for edge in exact.boundary)
        covered=all(any(core.inside(v,p) for p,coefficient in exact.roads) for v in poly)
        comparisons.append(dict(observed_margin=event['road_margin'],true_road_margin=distance if covered else -distance))
    border_errors=[]
    for a,b in observed.boundary[:-2]:
        point=tuple((a[j]+b[j])/2 for j in range(2));distance=min(core.point_segment(point,u,v) for u,v in exact.boundary)
        covered=any(core.inside(point,p) for p,coefficient in exact.roads)
        border_errors.append(distance if covered else -distance)
    _,observed_hull_velocity=core.hull_pose(estimated)
    true_hull_velocity=vector(h['velocity'])
    summary=dict(world_identity_match=True,counterfactuals=results,model_ticks=ticks,native_actions=0,
        CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
        hull_position_error_m=math.dist(core.hull_pose(estimated)[0],(0.,0.)),
        measured_root_representation_position_error_m=representation_position_error,
        measured_root_representation_velocity_error_m_s=representation_velocity_error,
        hull_velocity_error_m_s=[observed_hull_velocity[j]-true_hull_velocity[j] for j in range(2)],
        yaw_error_rad_s=estimated.planar.yaw-h['angular_velocity'],
        wheel_angle_errors_rad=[w.heading-(t['angle']-h['angle']) for w,t in zip(estimated.planar.linear.wheels,truth['wheels'])],
        wheel_omega_errors_rad_s=[w.omega-t['omega'] for w,t in zip(estimated.planar.linear.wheels,truth['wheels'])],
        wheel_gas_errors=[w.gas-t['gas'] for w,t in zip(estimated.planar.linear.wheels,truth['wheels'])],
        boundary_signed_inside_distance_range_m=[min(border_errors),max(border_errors)],
        failed_polygon_margin_comparison=comparisons,
        limits='Actual joint rates and actual clipping history unrecorded; hold estimated values fixed. Observation-derived reference paths remain identical in all cells. No Agent receives true inputs.')
    dump(out/'result-private.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='failed_polygon_margin_comparison'},indent=2))


if __name__=='__main__':main()
