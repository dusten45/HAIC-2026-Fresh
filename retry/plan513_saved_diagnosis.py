"""Two fixed saved-state evaluations, no policy tuning and no native calls."""
import json,math,time,hashlib
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.plan513_control import arrival,steering,steered
from retry.plan512_control import BRAKE,TARGET,station,hold
from retry.brake508_corridor import bounds
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response513-private')

def run():
    plan=dict(kind='saved-only max-brake viability and preceding registered command forecast',max_model_ticks=2048,CPU_s=30,wall_s=45,native_worlds=0,native_resets=0,native_actions=0,criteria_changes=0,policy_searches=0)
    with (D/'saved-diagnosis-contract.json').open('x') as f:json.dump(plan,f,indent=2)
    t=time.perf_counter();cpu=time.process_time();counter=[0];x=json.loads((D/'plan-stop-response-private.json').read_text());root=load_root(x['root']);p=x['plan']
    action=np.array([steering(root,p),0.,BRAKE],np.float32);root=steered(root,action)
    stop,cross=arrival(root,action,p,bounds(root.roads),counter)
    last=json.loads((D/'action-response-035.json').read_text());before=load_root(last['root']);applied=np.asarray(last['record']['action'],np.float32)
    predicted,rows=hold(before,applied,bounds(before.roads),counter)
    future=steered(predicted,[steering(predicted,p),0.,BRAKE]);priorstop,priorcross=arrival(future,np.array([steering(future,p),0.,BRAKE],np.float32),p,bounds(future.roads),counter)
    measured_late=(stop-p['gate']) if cross is None else None;prior_late=(priorstop-p['gate']) if priorcross is None else None
    result=dict(physical_goal_m_s=30.,planning_target_m_s=TARGET,current_distance_to_gate_m=p['gate']-station(root.center,p),maximum_brake_forecast_crossing_speed_m_s=cross,
        maximum_brake_forecast_crossing_excess_over_planning_target_m_s=(cross-TARGET) if cross is not None else None,maximum_brake_forecast_target_distance_lateness_m=measured_late,
        preceding_command_forecast_next_state_crossing_speed_m_s=priorcross,preceding_command_forecast_next_target_lateness_m=prior_late,
        next_state_position_error_m=math.dist(root.center,predicted.center),next_state_station_error_m=station(root.center,p)-station(predicted.center,p),next_state_speed_error_m_s=math.hypot(*root.planar.linear.velocity)-math.hypot(*predicted.planar.linear.velocity),
        model_ticks=counter[0],CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_worlds=0,native_resets=0,native_actions=0,
        interpretation='Strict planning target feasibility lost near saturated brake boundary under tiny native/model discrepancy. No proof physical30+/-0.5 goal is unreachable; no action dispatched or threshold changed.')
    assert counter[0]<=2048 and result['CPU_s']<30 and result['wall_s']<45
    with (G/'retry/plan513_diagnosis.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
