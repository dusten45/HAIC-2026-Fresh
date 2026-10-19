"""External private recorder. Never shipped in the participant archive."""
import dataclasses
import json
import math
import pickle
from pathlib import Path
import sys
from collections.abc import Mapping
import numpy as np


def plain(value):
    if dataclasses.is_dataclass(value):return plain(dataclasses.asdict(value))
    if isinstance(value,Mapping):return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [plain(v) for v in value]
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    return value


def dump(path,value):
    Path(path).write_text(json.dumps(plain(value),allow_nan=False)+'\n')


class Recorder:
    def __init__(self,agent,directory,target=36):
        self.agent=agent;self.directory=Path(directory);self.target=target
        self.calls=0;self.active=None;self.active_count=0;self.trials=[]
        self.core=sys.modules['runtime598']
        self.original_select=self.core.Controller.select
        self.original_certifier=self.core.certifier
        self.original_forces=self.core.force_rows
        recorder=self

        def enabled():return recorder.target is None or recorder.calls==recorder.target

        def select(controller,*args,**kwargs):
            if not enabled():return recorder.original_select(controller,*args,**kwargs)
            root,progress,hold,launch,running=args[:5]
            names=('speed','yaw','joint','previous_joint','distance','previous_action',
                   'predicted_wheels','history','grip_prior','engine_prior','steering_prior','calls')
            dump(recorder.directory/'checkpoint-private.json',dict(root=root,progress=progress,
                hold=hold,launch_history=launch,running_history=running,high=controller.high,
                low=controller.candidate_backup,roads=controller.scene.roads,
                boundary=controller.scene.boundary,obstacles=controller.scene.obstacles,
                call=recorder.calls,counter_before=controller.model[0],memory={n:getattr(agent,n) for n in names}))
            try:action,report=recorder.original_select(controller,*args,**kwargs)
            except BaseException as exc:
                dump(recorder.directory/'original-report-private.json',dict(error=str(exc),
                    counter_after=controller.model[0],trials=recorder.trials))
                raise
            dump(recorder.directory/'original-report-private.json',dict(action=action,report=report,
                 counter_after=controller.model[0],trials=recorder.trials))
            return action,report

        def certifier(*args,**kwargs):
            certify=recorder.original_certifier(*args,**kwargs)
            if not enabled():return certify
            def wrapped(action):
                force_steps=[];recorder.active=force_steps;recorder.active_count=0
                try:report=certify(action)
                except BaseException as exc:
                    recorder.trials.append(dict(action=plain(action),error=str(exc),force_steps=force_steps))
                    raise
                else:recorder.trials.append(dict(action=plain(action),report=report,force_steps=force_steps))
                finally:
                    recorder.active=None
                    if recorder.target is None:dump(recorder.directory/'forecasts-private.json',recorder.trials)
                return report
            return wrapped

        def force_rows(root,action):
            rows=recorder.original_forces(root,action)
            if recorder.active is not None:
                details=[];core=recorder.core
                for i,w in enumerate(root.planar.linear.wheels):
                    gas=w.gas+min(.1,float(action[1])-w.gas) if i>=2 else w.gas
                    _,_,d=core.wheel_response(w,root.planar.linear.velocity,gas,float(action[2]),root.planar.linear.engine_multiplier)
                    forward=(-math.sin(w.heading),math.cos(w.heading));side=(forward[1],-forward[0])
                    velocity=tuple(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))
                    vf=sum(forward[j]*velocity[j] for j in range(2));vs=sum(side[j]*velocity[j] for j in range(2))
                    details.append(dict(wheel=i,omega=w.omega,gas=gas,heading=w.heading,
                        friction=w.friction,contacts=root.current_contacts[i],
                        longitudinal_velocity=vf,lateral_velocity=vs,
                        longitudinal_force_raw=core.STIFFNESS*(d['omega_braked']*core.RADIUS-vf),
                        lateral_force_raw=-core.STIFFNESS*vs,**d,ratio=rows[i]['ratio']))
                recorder.active_count+=1
                step=dict(raw_from_root=recorder.active_count,
                    body_velocity=root.planar.linear.velocity,yaw=root.planar.yaw,
                    action=plain(action),wheels=details)
                if recorder.target is None:recorder.active[:]=[step]
                else:recorder.active.append(step)
            return rows

        self.core.Controller.select=select;self.core.certifier=certifier;self.core.force_rows=force_rows

    def before_action(self,observation):
        self.calls+=1
        if self.target is None or self.calls==self.target:
            np.save(self.directory/'input-private.npy',observation)
            (self.directory/'agent-before-private.pkl').write_bytes(pickle.dumps(self.agent.__dict__,protocol=pickle.HIGHEST_PROTOCOL))
            dump(self.directory/'agent-before-private.json',dict(call=self.calls,
                counter_limit=self.agent.counter.limit,memory=self.agent.__dict__))
            self.trials=[]
            if self.target is None:
                for name in ('checkpoint-private.json','original-report-private.json','forecasts-private.json'):
                    (self.directory/name).unlink(missing_ok=True)


def external_truth(raw):
    car=raw.car;h=car.hull
    return dict(hull=dict(position=list(h.position),world_center=list(h.worldCenter),
        local_center=list(h.localCenter),velocity=list(h.linearVelocity),angle=float(h.angle),
        angular_velocity=float(h.angularVelocity),mass=float(h.mass),inertia=float(h.inertia)),
        engine_multiplier=car.engine_multiplier,steering_multiplier=car.steering_multiplier,
        grip_multiplier=car.grip_multiplier,grass_friction_multiplier=car.grass_friction_multiplier,
        wheels=[dict(position=list(w.position),velocity=list(w.linearVelocity),angle=float(w.angle),
            joint_angle=float(w.joint.angle),omega=float(w.omega),gas=float(w.gas),
            road_frictions=[float(t.road_friction) for t in w.tiles],
            friction=max([400.*car.grass_friction_multiplier,*[400.*t.road_friction for t in w.tiles]])*car.grip_multiplier)
            for w in car.wheels])
