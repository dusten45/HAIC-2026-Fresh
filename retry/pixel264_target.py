"""Choose the one nominal longitudinal goal; preserve all downstream240 computation."""
import time
from retry.profile263_frozen import profile
from retry.mode264 import SAME_TARGET


def select_target_speed(agent,path,feedback,forward,original,obstacles):
    if SAME_TARGET:
        agent.last_plan=dict(active=False,fallback=False,identity=True,planner_ms=0.,original_target=original,selected_target=original,steering_unchanged=True,nominal_memory_preserved=True)
        return original
    if forward<=0:return original
    tic=time.perf_counter();result=profile(path,max(0,feedback),agent.controller.lateral_acceleration,agent.controller.speed_cap)
    if result is None:return original
    chosen=float(result['speed'][0])
    agent.last_plan=dict(active=True,fallback=False,identity=False,planner_ms=(time.perf_counter()-tic)*1000,original_target=original,selected_target=chosen,feedback_speed_m_s=feedback,path_points=len(path),path_length_m=result['length'],obstacle_count=len(obstacles),tail_curvature=float(result['curvature'][-1]),tail_curvature_cap=float(result['limits'][-1]),tail_profile_speed=float(result['speed'][-1]),steering_unchanged=True,nominal_memory_preserved=True,head_and_global_scales_preserved=True)
    return chosen
