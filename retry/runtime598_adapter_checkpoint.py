"""One changed-adapter evaluation of a trusted full private checkpoint."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import pickle
import sys
import time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('checkpoint_directory')
    parser.add_argument('output_directory');parser.add_argument('--source',required=True)
    args=parser.parse_args();directory=Path(args.checkpoint_directory);out=Path(args.output_directory)
    out.mkdir(exist_ok=False)
    source=Path(args.source).resolve();sys.path.insert(0,str(source.parent))
    spec=importlib.util.spec_from_file_location('agent',source)
    module=importlib.util.module_from_spec(spec);sys.modules['agent']=module;spec.loader.exec_module(module)
    import numpy as np
    import runtime598 as core
    from retry.runtime598_diagnostic import dump
    agent=module.Agent();memory=pickle.loads((directory/'agent-before-private.pkl').read_bytes())
    # Earlier code did not retain pixels. An empty new buffer is honest; the
    # actual incoming stack may bootstrap it, but no older images are invented.
    if 'road_frames' not in memory:memory['road_frames']=[]
    backfill_ticks=0;backfill_cpu=0.;backfill_wall=0.
    needed=('predicted_hull_velocity_body','predicted_joints','predicted_joint_rates','predicted_yaw','predicted_average_hull_velocity_body','predicted_average_yaw')
    if any(key in agent.__dict__ and key not in memory for key in needed):
        # Derive a missing new field from the exact recorded own-action model
        # transition. Never replace old spin/history/grip with external truth.
        cpu=time.process_time();start=time.perf_counter();root=memory['last_root'];counter=[0]
        action=memory['previous_action']
        for _ in range(4):
            root=core.replace(root,planar=core.replace(root.planar,steer=-float(action[0])))
            root=core.tick(root,float(action[1]),float(action[2]),core.bounds(root.roads),counter)
        velocity=core.hull_pose(root)[1];angle=root.planar.angle
        assert tuple((w.omega,w.gas) for w in root.planar.linear.wheels)==memory['predicted_wheels']
        assert math.hypot(*velocity)==memory['predicted_hull_speed']
        if 'predicted_hull_velocity_body' not in memory:
            memory['predicted_hull_velocity_body']=(math.cos(angle)*velocity[0]+math.sin(angle)*velocity[1],
                -math.sin(angle)*velocity[0]+math.cos(angle)*velocity[1])
        if 'predicted_joints' not in memory:
            memory['predicted_joints']=root.planar.joints
            memory['predicted_joint_rates']=root.planar.rates
        if 'predicted_yaw' not in memory:memory['predicted_yaw']=root.planar.yaw
        if 'predicted_average_hull_velocity_body' not in memory:
            before_origin=core.hull_pose(memory['last_root'])[0];after_origin=core.hull_pose(root)[0]
            dx,dy=((after_origin[j]-before_origin[j])/.08 for j in range(2))
            memory['predicted_average_hull_velocity_body']=(math.cos(angle)*dx+math.sin(angle)*dy,-math.sin(angle)*dx+math.cos(angle)*dy)
            memory['predicted_average_yaw']=(root.planar.angle-memory['last_root'].planar.angle)/.08
        backfill_ticks=counter[0];backfill_cpu=time.process_time()-cpu;backfill_wall=time.perf_counter()-start
    agent.__dict__=memory
    observation=np.load(directory/'input-private.npy');observation.flags.writeable=False
    select=core.Controller.select;captured={}
    def record(controller,*args,**kwargs):
        dump(out/'estimated-input-private.json',dict(root=args[0],high=controller.high,
             low=controller.candidate_backup,progress=args[1],roads=controller.scene.roads,
             boundary=controller.scene.boundary,obstacles=controller.scene.obstacles))
        action,report=select(controller,*args,**kwargs);captured['report']=report
        dump(out/'report-private.json',dict(action=action,report=report))
        return action,report
    core.Controller.select=record
    before=agent.counter[0];start=time.perf_counter();cpu=time.process_time();error=None;action=None
    try:action=agent.act(observation)
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    result=dict(action=action,error=error,diagnostics=agent.diagnostics,
        model_ticks=agent.counter[0]-before+backfill_ticks,CPU_s=time.process_time()-cpu+backfill_cpu,
        wall_s=time.perf_counter()-start+backfill_wall,native_actions=0,
        memory_overwritten=False,derived_new_field_model_ticks=backfill_ticks,
        source=str(source),grip_prior_after=agent.grip_prior)
    dump(out/'result-private.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('action','diagnostics','source')}))
    assert result['wall_s']<5.,'WHOLE_ACT_LIMIT'


if __name__=='__main__':main()
