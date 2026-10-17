"""Pure command adapter; no controller/world/memory/reference access."""
import numpy as np
from retry.allocator476 import solve,Unsupported

def allocate(command,wheels,dtype):
 a=np.asarray(command)
 if a.shape!=(3,) or a.dtype!=np.float32 or not np.isfinite(a).all():raise Unsupported('command_must_be_finite_float32_shape3')
 if not(0<=a[1]<=1 and 0<=a[2]<=1) or a[1]>0 and a[2]>0:raise Unsupported('pedal_command_domain')
 branch='gas' if a[1]>0 else 'brake' if a[2]>0 else 'none';active=1 if branch=='gas' else 2
 proof=solve(wheels,float(a[active]),branch,dtype)
 out=a.copy();out[active]=np.float32(proof['q'])
 if out[0]!=a[0] or not 0<=out[active]<=a[active]:raise Unsupported('adapter_invariance')
 return out,proof
