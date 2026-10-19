"""Public own-action transitions must preserve force on camera-frame rebase."""
import argparse,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output')
    args=parser.parse_args();out=Path(args.output);assert not out.exists()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    spec=importlib.util.spec_from_file_location('rebase_agent',args.source)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);c=a.core
    cpu=time.process_time();counter=[0];records=[]
    polygon=((-100.,-100.),(100.,-100.),(100.,100.),(-100.,100.))
    scene=c.Scene([(polygon,1.)],list(zip(polygon,polygon[1:]+polygon[:1])),[])
    for yaw in (-2.8,-.5,0.,.5,2.8):
      for brake in (0.,.125):
        observer=a.Agent();observer.speed=25.;observer.yaw=yaw;observer.joint=.2 if yaw>0 else -.2
        initial=observer._root(scene,-1. if yaw>0 else 1.)
        action=np.array([-.3 if yaw>0 else .3,.2 if brake==0 else 0.,brake],np.float32)
        root=initial
        for _ in range(4):
            root=c.replace(root,planar=c.replace(root.planar,steer=-float(action[0])))
            root=c.tick(root,float(action[1]),float(action[2]),scene.index,counter)
        velocity=c.hull_pose(root)[1];angle=root.planar.angle;co,si=math.cos(angle),math.sin(angle)
        body=(co*velocity[0]+si*velocity[1],-si*velocity[0]+co*velocity[1])
        observer.speed=math.hypot(*body);observer.yaw=root.planar.yaw
        observer.joint=root.planar.joints[0];observer.joint_rate=root.planar.rates[0]
        observer.predicted_wheels=tuple((w.omega,w.gas) for w in root.planar.linear.wheels)
        observer.previous_action=action.copy()
        rebased=observer._root(scene,body[0])
        # Force is rotation invariant. This compares original transitioned
        # state with a fresh observation adapter reconstruction, not two copies
        # of the offset formula. No hidden map/state is used by a live Agent.
        errors=[]
        for command in (action,np.array([action[0],0.,.25],np.float32)):
            first=c.force_rows(root,command);second=c.force_rows(rebased,command)
            errors.append(max(abs(x['ratio']-y['ratio']) for x,y in zip(first,second)))
        records.append(dict(initial_yaw=yaw,brake=brake,max_ratio_error=max(errors)))
    maximum=max(r['max_ratio_error'] for r in records)
    record=dict(status='PASS' if maximum<1e-11 else 'FAIL',cases=len(records),max_force_ratio_rebase_error=maximum,records=records,
        model_ticks=counter[0],native_actions=0,CPU_s=time.process_time()-cpu,
        scope='Synthetic public vehicle/plane and original own-action core transitions. A rotation-invariance roundtrip, not a universal observer accuracy claim.')
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='records'}))
    assert maximum<1e-11,'FORCE_NOT_PRESERVED_ON_REBASE'


if __name__=='__main__':main()
