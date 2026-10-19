"""Float32 50-coordinate map and fixed-size shooting residuals; no dynamics."""
import math
import numpy as np
SCALE=np.tile([.02,.1],25)
DOMAIN=np.tile([float(np.float32(.4)),1.],25)
FD_STEP=.001
NRAW=156;PER_RAW=11;NCON=NRAW*PER_RAW+2
class ExpressionStop(RuntimeError):pass

def seed_controls(commands):
    return np.asarray([v for i in range(25,50) for v in [commands[i][0],commands[i][1]-commands[i][2]]],np.float32).astype(float)
def canonical(z,seed):
    z=np.asarray(z,float)
    if z.shape!=(50,) or not np.all(np.isfinite(z)):raise ExpressionStop('NONFINITE_CONTROL_PROPOSAL')
    x=np.clip(seed+SCALE*z,-DOMAIN,DOMAIN).astype(np.float32);x[x==0]=np.float32(0.)
    return x.astype(float)
def action(x,index):
    s,u=x[2*(index-25):2*(index-25)+2];return np.array([s,max(0.,u),max(0.,-u)],np.float32)
def command_key(x):return b''.join(action(x,i).tobytes() for i in range(25,50))
def fd_point(x,j):
    sign=1 if x[j]+FD_STEP*SCALE[j]<=DOMAIN[j] else -1
    y=x.copy();y[j]=float(np.float32(x[j]+sign*FD_STEP*SCALE[j]));y[j]=max(-DOMAIN[j],min(DOMAIN[j],y[j]));delta=(y[j]-x[j])/SCALE[j]
    if delta==0 or not math.isfinite(delta):raise ExpressionStop('QUANTIZED_FD_ZERO')
    return y,delta,sign

def residuals(rows,complete,admissible_crossing):
    g=np.full((NRAW,PER_RAW),-1.,float)
    for r in rows:
        i=r['global_raw_before']-96
        if not 0<=i<NRAW:raise ExpressionStop('SUFFIX_ROW_INDEX')
        if len(r['forces'])!=4:raise ExpressionStop('FORCE_DIMENSION')
        g[i,:4]=[1.059-f['ratio'] for f in r['forces']]
        clips,samples=r['proposed_history'];g[i,4]=(.1-clips/samples)/.1
        if 'body' in r:g[i,10]=(100.-r['body'])/100.
        if 'margin' in r:
            g[i,5]=(r['margin']-.5);g[i,6]=(3.-r['path_error'])/3.;g[i,7]=(4.85-r['reference_overspeed'])/5.;g[i,8]=r['progress_delta']+.5;g[i,9]=(r['projection_limit']-r['progress_delta'])/5.
    result=np.r_[g.ravel(),1. if complete else -1.,1. if admissible_crossing else -1.]
    if result.shape!=(NCON,) or not np.all(np.isfinite(result)):raise ExpressionStop('NONFINITE_RESIDUAL')
    return result

def numeric_resolution(a,b):return 32*max(math.ulp(float(a)),math.ulp(float(b)))
def faster(a,b):return a<b-numeric_resolution(a,b)
def objective(valid,hit,baseline_time,rows_count):
    return hit['time_s'] if valid else baseline_time+1.+(NRAW-min(NRAW,rows_count))/NRAW
