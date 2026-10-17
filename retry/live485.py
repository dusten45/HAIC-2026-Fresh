"""Current live wheel reads -> frozen arithmetic allocator. Never reads traces."""
import copy,json,time
import numpy as np
from retry.adapter476 import allocate
from retry.allocator476 import force
from retry.audit476_verify import verify
from retry.audit476_boundaries import verify_rank_metadata
from retry.pilot420_backend import TechnicalStop,ResourceStop,fingerprint,rnghash
from retry.loss389_analyze import save

def inputs_current(model):
 car=model.car;out=[]
 for j,w in enumerate(car.wheels):
  forward=w.GetWorldVector((0,1));side=w.GetWorldVector((1,0));velocity=w.linearVelocity
  vf=forward[0]*velocity[0]+forward[1]*velocity[1];vs=side[0]*velocity[0]+side[1]*velocity[1];limit=400.*car.grass_friction_multiplier
  for tile in w.tiles:limit=max(limit,400.*tile.road_friction)
  limit*=car.grip_multiplier
  out.append(dict(wheel=j,omega=float(w.omega),gas=float(w.gas),vf=float(vf),vs=float(vs),limit=float(limit),engine=float(car.engine_multiplier),radius=float(w.wheel_rad)))
 return out

def allocate_current(child,nominal,index):
 meter=child.meter;meter.guard();cpu=time.process_time();wall=time.perf_counter()
 if meter.allocator_calls>=52:raise ResourceStop('485_allocator52')
 meter.allocator_calls+=1;number=meter.allocator_calls;meter.persist()
 memory=copy.deepcopy(child.ctrl.memory());nodes=child.ctrl.policy.nodes.copy();rh=rnghash();phase=child.ctrl.phase();w=inputs_current(child.m);initial=fingerprint(w)
 payload=dict(number=number,label=child.label,action=index+1,physical_time=float(child.m.t),phase=phase,nominal=nominal.tolist(),current_wheels=w,input_source='CURRENT_MODEL_WHEEL_READS_NO_STORED_FUTURE',hold_s=.08)
 if len((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode())>4096:raise ResourceStop('485_allocator_input4KiB')
 save(meter.d/f'allocation-input-{number:03d}.json',payload)
 command,proof=allocate(nominal,w,'model64');branch='gas' if nominal[1]>0 else 'brake' if nominal[2]>0 else 'none';active=1 if branch=='gas' else 2
 verify(w,float(nominal[active]),branch,'model64',proof);verify_rank_metadata(proof)
 if fingerprint(w)!=initial or child.ctrl.memory()!=memory or not np.array_equal(child.ctrl.policy.nodes,nodes) or rnghash()!=rh or command[0]!=nominal[0] or child.ctrl.phase()!=phase:raise TechnicalStop('485_allocator_nonpedal_mutation')
 before=[force(x,float(nominal[active]),branch,'model64') for x in w];after=[force(x,float(command[active]),branch,'model64') for x in w]
 # Store compact source-order q0/predictedfirst forces; checked against actualraw
 # after child.one, without using that futuretelemetry for command selection.
 packet=dict(number=number,label=child.label,action=index+1,phase=phase,command=command.tolist(),changed=not np.array_equal(command,nominal),proof=proof,q0_forces=before,allocated_first_forces=after)
 if len((json.dumps(packet,ensure_ascii=False,indent=2)+'\n').encode())>8192:raise ResourceStop('485_allocator_proof8KiB')
 save(meter.d/f'allocation-proof-{number:03d}.json',packet)
 elapsed=time.process_time()-cpu;welapsed=time.perf_counter()-wall;meter.allocator_CPU_s+=elapsed;meter.allocator_wall_s+=welapsed
 if elapsed>.25 or welapsed>.5 or meter.allocator_CPU_s>16 or meter.allocator_wall_s>32:raise ResourceStop('485_allocator_time_cap')
 meter.allocation_pending=(child.label,index+1,number,after)
 meter.persist();meter.guard()
 return command

def check_first_raw(child,index):
 meter=child.meter;label,i,n,forces=meter.allocation_pending
 if (label,i)!=(child.label,index+1):raise TechnicalStop('485_allocation_row_join')
 observed=[t for t in child.rows[-1]['tires'] if t['raw_tick']==1]
 if len(observed)!=4:raise TechnicalStop('485_no_first_raw')
 for a,b in zip(forces,observed):
  fields={'omega':'omega','gas':'gas','brake':'brake','long':'raw_long_N','lat':'raw_lat_N','ratio':'force_ratio'}
  if any(a[k]!=b[v] for k,v in fields.items()):raise TechnicalStop('485_allocated_first_raw_not_exact')
 meter.allocation_pending=None
