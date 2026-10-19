"""Fixed public Box2D microfixture: HUD/own-action observer, no task reset."""
from pathlib import Path
import argparse,importlib.util,sys,json,math,time
import numpy as np
import Box2D
from core.vendor.car_dynamics import Car
from retry.hud_joint_check import render_joint
from core.vendor.car_racing import CarRacing
from types import SimpleNamespace as N
import pygame,cv2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('baseline');parser.add_argument('output');args=parser.parse_args()
    out=Path(args.output);assert not out.exists();start=time.process_time()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'));import observation_agent as new;import runtime598 as core
    spec=importlib.util.spec_from_file_location('public_baseline_observer',args.baseline);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    world=Box2D.b2World(gravity=(0,0));car=Car(world,0.,0.,0.)
    class Tile:road_friction=1.
    tile=Tile()
    for w in car.wheels:w.tiles.add(tile)
    physics=0
    def step(action):
        nonlocal physics
        car.steer(-float(action[0]));car.gas(float(action[1]));car.brake(float(action[2]));car.step(.02);world.Step(.02,180,60);physics+=1
    for _ in range(50):step((0.,0.,0.))
    def image():
        surface=pygame.Surface((1000,800));surface.fill((0,0,0));CarRacing._render_indicators(N(surf=surface,car=car),1000,800)
        surface=pygame.transform.smoothscale(surface,(96,96));rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
        return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.
    frames=[image()]*4;observers=[old.Agent(),new.Agent()];labels=['legacy_point_HUD','quantized_HUD_prediction']
    poly=((-100.,-100.),(100.,-100.),(100.,100.),(-100.,100.));scene=core.Scene([(poly,1.)],list(zip(poly,poly[1:]+poly[:1])),[])
    actions=[(0.,.5,0.)]*4+[(-.12,.3,0.)]*4+[(0.,.1,.15)]*4;records=[];flow_errors=[]
    for index,action in enumerate(actions):
        source_start=tuple(car.hull.position)
        for label,agent in zip(labels,observers):
            lateral=agent._state_estimates(np.asarray(frames));root=agent._root(scene,lateral)
            true_speed=math.hypot(*car.hull.linearVelocity);true_yaw=car.hull.angularVelocity;true_joint=car.wheels[0].joint.angle;true_rate=car.wheels[0].angularVelocity-true_yaw
            rate=root.planar.rates[0]
            records.append(dict(label=label,index=index,speed_error=abs(agent.speed-true_speed),yaw_error=abs(agent.yaw-true_yaw),joint_error=abs(agent.joint-true_joint),rate_error=abs(rate-true_rate),spin_MAE=float(np.mean([abs(w.omega-t.omega) for w,t in zip(root.planar.linear.wheels,car.wheels)]))))
            r=root
            for _ in range(4):
                r=core.replace(r,planar=core.replace(r.planar,steer=-float(action[0])));r=core.tick(r,float(action[1]),float(action[2]),scene.index,agent.counter)
            agent.previous_action=np.asarray(action);agent.last_root=root;agent.predicted_wheels=tuple((w.omega,w.gas) for w in r.planar.linear.wheels)
            velocity=core.hull_pose(r)[1];angle=r.planar.angle;agent.predicted_hull_speed=math.hypot(*velocity)
            agent.predicted_hull_velocity_body=(math.cos(angle)*velocity[0]+math.sin(angle)*velocity[1],-math.sin(angle)*velocity[0]+math.cos(angle)*velocity[1])
            if label==labels[1]:
                agent.predicted_joints=r.planar.joints;agent.predicted_joint_rates=r.planar.rates;agent.predicted_yaw=r.planar.yaw
                origin0=core.hull_pose(root)[0];origin1=core.hull_pose(r)[0];dx,dy=((origin1[j]-origin0[j])/.08 for j in range(2))
                agent.predicted_average_hull_velocity_body=(math.cos(angle)*dx+math.sin(angle)*dy,-math.sin(angle)*dx+math.cos(angle)*dy)
                agent.predicted_average_yaw=(r.planar.angle-root.planar.angle)/.08
        for _ in range(4):step(action)
        # Perfect rigid-image displacement from an independent Box2D motion,
        # with the same interval-average semantics as optical flow.
        angle=car.hull.angle;c,s=math.cos(angle),math.sin(angle);dx,dy=((car.hull.position[j]-source_start[j])/.08 for j in range(2))
        average=np.array([c*dx+s*dy,-s*dx+c*dy]);vx,vy=car.hull.linearVelocity;endpoint=np.array([c*vx+s*vy,-s*vx+c*vy])
        observer=observers[1];aligned=np.asarray(observer.predicted_hull_velocity_body)+average-np.asarray(observer.predicted_average_hull_velocity_body)
        flow_errors.append(dict(unadjusted=float(np.linalg.norm(average-endpoint)),aligned=float(np.linalg.norm(aligned-endpoint))))
        frames=frames[1:]+[image()]
    summaries=[]
    for label in labels:
        rows=[r for r in records if r['label']==label]
        summaries.append(dict(label=label,**{k:float(np.mean([r[k] for r in rows])) for k in ['speed_error','yaw_error','joint_error','rate_error','spin_MAE']}))
    result=dict(status='PASS',fixed_public_actions=len(actions),public_physics_ticks=physics,model_ticks=sum(a.counter[0] for a in observers),native_actions=0,DEV_actions=0,
        flow_average_as_endpoint_MAE_m_s=float(np.mean([r['unadjusted'] for r in flow_errors])),flow_aligned_endpoint_MAE_m_s=float(np.mean([r['aligned'] for r in flow_errors])),summaries=summaries,CPU_s=time.process_time()-start,scope='Fixed independent public Box2D/HUD microfixture; no challenge world/seed and no policy search. Not a universal observer guarantee.',records=records)
    result['status']='PASS' if all(summaries[1][k]<summaries[0][k] for k in ['speed_error','yaw_error','joint_error','rate_error','spin_MAE']) else 'FAIL'
    out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));assert result['status']=='PASS'


if __name__=='__main__':main()
