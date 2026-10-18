"""Saved-only diagnostic: condition the SAME brake on measured contact limits.

This deliberately uses future measured contacts retrospectively. It is not a
controller, another candidate, a physical counterfactual, or promotion evidence.
"""
import importlib.abc,json,math,sys,time
from dataclasses import replace
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path=None,target=None):
        if name.startswith(('Box2D','core.vendor')):raise RuntimeError('SAVED504_NO_PHYSICS')
sys.meta_path.insert(0,NoPhysics())
from retry.brake502_response import State,Wheel
from retry.brake504_planar import Planar,step


def run():
    cpu=time.process_time();start=time.perf_counter();G=Path(__file__).resolve().parents[1]
    rows=json.loads(Path('/workspace/haic-response504-private/bench-raw.json').read_text());out={}
    for row in rows:
        data=row['initial_planar'];linear=dict(data['linear']);linear['wheels']=tuple(Wheel(**w) for w in linear['wheels'])
        data['linear']=State(**linear);frozen=Planar(**data);conditioned=frozen
        heading_drift=offset_drift=0.;friction_mismatch=0
        for actual in row['ticks']:
            observed=actual['before']['wheels']
            for a,w in zip(observed,frozen.linear.wheels):
                heading_drift=max(heading_drift,abs(a['heading']-w.heading));offset_drift=max(offset_drift,math.dist(a['offset'],w.offset));friction_mismatch+=int(a['friction']!=w.friction)
            conditioned=replace(conditioned,linear=replace(conditioned.linear,wheels=tuple(replace(w,friction=a['friction']) for a,w in zip(observed,conditioned.linear.wheels))))
            frozen=step(frozen,row['brake']);conditioned=step(conditioned,row['brake'])
        prediction=math.hypot(*frozen.linear.velocity)
        assert abs(prediction-row['prediction'])<1e-10
        observed=math.hypot(*row['ticks'][-1]['after_COM'])
        out[row['fixture']]=dict(frozen_forecast_error_m_s=observed-prediction,measured_contact_conditioned_forecast_error_m_s=observed-math.hypot(*conditioned.linear.velocity),predicted_heading_mismatch_max_rad=heading_drift,predicted_offset_mismatch_max_m_s=offset_drift,friction_mismatch_wheel_ticks=friction_mismatch)
    result=dict(scope='Retrospective model diagnosis with same executed command; future contacts forbidden to online candidate; no new physical trajectory',cases=out,worlds=0,integrations=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start)
    with (G/'retry/brake504_saved_result.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':run()
