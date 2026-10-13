"""Replace only286 rollout: unchanged control bytecode with sourceworld clones."""
import types,time
import numpy as np
from retry import progress288_objective as original
from retry.source_vehicle_transition import SourceVehicleTransition

def control(base,features,path,snapshot,counters,corridor):
 start=dict(counters);origin=np.array(snapshot['hull']['position'],float);angle=snapshot['hull']['angle'];right=np.array([np.cos(angle),np.sin(angle)]);forward=np.array([-np.sin(angle),np.cos(angle)])
 def rollout(U,v,previous):
  assert counters['world_build_attempts']<80000;counters['world_build_attempts']+=1;tic=time.perf_counter();model=None
  try:
   model=SourceVehicleTransition(snapshot);counters['clone_initializations']+=1;counters['clone_build_wall_s']+=time.perf_counter()-tic
   assert model.initial_tiles_exact and model.initial_progress_exact and model.initial_bodies_exact
   positions=[];tic=time.perf_counter()
   for u in U:
    assert counters['physics_ticks']+model.native_ticks+4<=2560000
    # Float64candidate is same optimizerparameter as286; current240 pedals held.
    row=model.step(np.array([u,float(base[1]),float(base[2])],float));delta=np.array(row['position'])-origin;positions.append([float(delta@right),float(delta@forward)])
    # No added terminal exclusion or penalty:286 objective has neither.
   counters['integration_wall_s']+=time.perf_counter()-tic
   return np.array(positions)
  finally:
   if model:
    counters['physics_ticks']+=model.native_ticks;model.close()
 globals_copy=dict(original.control.__globals__);globals_copy['rollout']=rollout;globals_copy['CURRENT_CORRIDOR']=corridor
 matched=types.FunctionType(original.control.__code__,globals_copy)
 action,audit=matched(base,features,path)
 calls=counters['world_build_attempts']-start['world_build_attempts'];ticks=counters['physics_ticks']-start['physics_ticks']
 assert calls==audit['kinematic_rollouts'] and ticks==audit['kinematic_substeps']
 audit['source_clone_queries']=calls;audit['source_model_physics_ticks']=ticks;audit['source_zero_time_initializations']=counters['clone_initializations']-start['clone_initializations'];audit.pop('kinematic_rollouts');audit.pop('kinematic_substeps');return action,audit
