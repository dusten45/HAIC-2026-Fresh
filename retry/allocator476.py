"""Pure first-raw pedal allocation. No environment, actor or physics imports.

Certified domain: NumPy1.26 scalar operations, finite float64 state, float32
command ranks [0,q0], positive friction limit, no intermediate overflow.
"""
import math,struct
import numpy as np
class Unsupported(RuntimeError):pass
def bits32(x):return struct.unpack('>I',struct.pack('>f',float(x)))[0]
def q32(i):return struct.unpack('>f',struct.pack('>I',i))[0]
def bits64(x):return struct.unpack('>Q',struct.pack('>d',float(x)))[0]
def t64(i):return struct.unpack('>d',struct.pack('>Q',i))[0]
def finite(*xs):
 if not all(math.isfinite(float(x)) for x in xs):raise Unsupported('nonfinite_intermediate')
def force(w,q,branch,dtype):
 if np.__version__!='1.26.0' or dtype not in ('native32','model64') or branch not in ('gas','brake','none'):raise Unsupported('unsupported_dtype_or_branch')
 cast=np.float32 if dtype=='native32' else np.float64;q=cast(q)
 if not 0<=float(q)<=1:raise Unsupported('pedal_domain')
 vals=[w[k] for k in ('omega','gas','vf','vs','limit','engine','radius')]
 if any(type(x) is not float for x in vals) or type(w['wheel']) is not int:raise Unsupported('state_scalar_dtype')
 finite(*vals)
 if not(w['limit']>0 and 0<w['engine']<=1 and 0<w['radius']<=1 and 0<=w['gas']<=1 and w['wheel'] in range(4)):raise Unsupported('state_domain')
 gas=w['gas']
 if w['wheel']>=2:
  request=q if branch=='gas' else cast(0);diff=np.clip(request,0,1)-gas
  if diff>0.1:diff=0.1
  gas+=diff
 omega=w['omega'];engine_term=.02*(40000.*w['engine'])*gas/1.6/(abs(omega)+5.);finite(gas,engine_term)
 omega+=engine_term;finite(omega);brake=q if branch=='brake' else cast(0)
 if brake>=.9:omega=0.;brake_branch='lock'
 elif brake>0:
  val=15*brake
  if abs(val)>abs(omega):val=abs(omega);brake_branch='zero_clamp'
  else:brake_branch='linear'
  omega+=-np.sign(omega)*val
 else:brake_branch='none'
 vr=omega*w['radius'];long=(-w['vf']+vr)*82.;lat=-w['vs']*82.;finite(omega,vr,long,lat)
 with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
  a=np.square(long);b=np.square(lat);ss=a+b;norm=np.sqrt(ss);ratio=norm/w['limit'];excess=max(0.,float(ratio-1.))
 finite(a,b,ss,norm,ratio,excess)
 return dict(long=float(long),lat=float(lat),omega=float(omega),gas=float(gas),brake=float(brake),norm=float(norm),ratio=float(ratio),excess=excess,brake_branch=brake_branch)
class Wheel:
 def __init__(self,w,hi,branch,dtype,counter,base=0):
  self.base=base;self.w=w;self.hi=hi;self.branch=branch;self.dtype=dtype;self.cache={};self.counter=counter
  a=self.at(0)['long'];b=self.at(hi)['long'];self.increasing=b>=a
  lo,h=0,hi
  pred=lambda r:self.at(r)['long']>=0 if self.increasing else self.at(r)['long']<=0
  if not pred(h):cross=h
  else:
   while lo<h:
    m=(lo+h)//2
    if pred(m):h=m
    else:lo=m+1
   cross=lo
  candidates={0,hi,cross,max(0,cross-1)};self.seed=min(candidates,key=lambda r:(self.at(r)['excess'],r))
 def at(self,r):
  if r not in self.cache:
   self.counter[0]+=1
   if self.counter[0]>100000:raise Unsupported('operation_cap')
   self.cache[r]=force(self.w,q32(self.base+r),self.branch,self.dtype)
  return self.cache[r]
 def interval(self,t):
  seed=self.seed
  if self.at(seed)['excess']>t:return None
  lo,h=0,seed
  while lo<h:
   m=(lo+h)//2
   if self.at(m)['excess']<=t:h=m
   else:lo=m+1
  left=lo;lo,h=seed,self.hi
  while lo<h:
   m=(lo+h+1)//2
   if self.at(m)['excess']<=t:lo=m
   else:h=m-1
  return left,lo
 def proof(self,t):
  iv=self.interval(t)
  return dict(interval=iv,seed=self.seed,seed_excess=self.at(self.seed)['excess'],left_outside=None if iv is None or iv[0]==0 else self.at(iv[0]-1)['excess'],right_outside=None if iv is None or iv[1]==self.hi else self.at(iv[1]+1)['excess'])
def solve(wheels,q0,branch,dtype='model64',rank_lo=0,rank_hi=None):
 # Restricted rank range is a fixture-only adapter; production always [0,q0].
 finite(q0)
 if branch=='none' and q0!=0:raise Unsupported('none_branch_nonzero_q0')
 if len(wheels)!=4 or {w['wheel'] for w in wheels}!={0,1,2,3}:raise Unsupported('wheel_identity_set')
 if q0<0 or q0>1 or q32(bits32(q0))!=q0:raise Unsupported('q0_not_nonnegative_float32')
 if q0==0:q0=0.
 top=bits32(q0) if rank_hi is None else rank_hi
 if rank_lo<0 or top<rank_lo or top>bits32(q0):raise Unsupported('rank_domain')
 hi=top-rank_lo
 counter=[0];ws=[Wheel(w,hi,branch,dtype,counter,rank_lo) for w in wheels]
 if len(ws)!=4:raise Unsupported('need_four_wheels')
 def intersection(t):
  intervals=[w.interval(t) for w in ws]
  if any(x is None for x in intervals):return None
  lo=max(x[0] for x in intervals);h=min(x[1] for x in intervals)
  return (lo,h) if lo<=h else None
 m0=max(w.at(hi)['excess'] for w in ws);low=-1;high=bits64(m0);threshold_iterations=0
 while high-low>1:
  mid=(low+high)//2;threshold_iterations+=1
  if intersection(t64(mid)) is not None:high=mid
  else:low=mid
 t=t64(high);iv=intersection(t);assert iv is not None;qrank=iv[1];m=max(w.at(qrank)['excess'] for w in ws)
 if m!=t or m>m0:raise Unsupported('objective_witness_mismatch')
 prev=None if high==0 else intersection(t64(high-1))
 if prev is not None:raise Unsupported('predecessor_threshold_feasible')
 if qrank<hi and max(w.at(qrank+1)['excess'] for w in ws)<=t:raise Unsupported('next_q_passes')
 out=dict(q=q32(rank_lo+qrank),q_rank=rank_lo+qrank,domain_rank_lo=rank_lo,q0=q32(top),q0_rank=top,objective=m,objective_q0=m0,threshold_rank=high,threshold_predecessor=None if high==0 else t64(high-1),threshold_predecessor_empty=True,q_next_objective=None if qrank==hi else max(w.at(qrank+1)['excess'] for w in ws),intersection=list(iv),wheel_proofs=[w.proof(t) for w in ws],predecessor_wheel_proofs=None if high==0 else [w.proof(t64(high-1)) for w in ws],threshold_iterations=threshold_iterations,wheel_evaluations=counter[0],new_physics=0)
 return out
