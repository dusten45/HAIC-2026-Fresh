"""Outward-rounded evaluation of the unchanged projection on a certified branch."""
import math
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from retry.executor397 import canonical_projection
class GeometryStop439(ValueError):pass

def need(value,reason):
 if not value:raise GeometryStop439(reason)
def down(x):need(math.isfinite(x),'INTERVAL_NONFINITE');return math.nextafter(x,-math.inf)
def up(x):need(math.isfinite(x),'INTERVAL_NONFINITE');return math.nextafter(x,math.inf)
@dataclass(frozen=True)
class Interval:
 lo:float
 hi:float
 def __post_init__(self):need(math.isfinite(self.lo) and math.isfinite(self.hi) and self.lo<=self.hi,'INVALID_INTERVAL')
 @classmethod
 def point(cls,x):return cls(float(x),float(x))
 def __add__(self,b):return Interval(down(self.lo+b.lo),up(self.hi+b.hi))
 def __sub__(self,b):return Interval(down(self.lo-b.hi),up(self.hi-b.lo))
 def __mul__(self,b):
  z=[a*c for a in [self.lo,self.hi] for c in [b.lo,b.hi]];return Interval(down(min(z)),up(max(z)))
 def __truediv__(self,b):
  need(not b.lo<=0<=b.hi,'INTERVAL_ZERO_DIVISION');z=[a/c for a in [self.lo,self.hi] for c in [b.lo,b.hi]];return Interval(down(min(z)),up(max(z)))
 def contains(self,x):return math.isfinite(x) and self.lo<=x<=self.hi
 def values(self):return [self.lo,self.hi]

def vector(v):
 need(isinstance(v,(tuple,list,np.ndarray)) and np.asarray(v).shape==(2,),'POSITION_SHAPE');need(all(math.isfinite(float(x)) for x in v),'POSITION_NONFINITE');return [float(x) for x in v]
def wrap(post,pre,L):return (post-pre+L/2)%L-L/2

class Projection439:
 def __init__(self,line,L,position_tolerance):
  self.line=np.asarray(line,float);self.L=float(L);self.rho=float(position_tolerance);need(self.line.ndim==2 and self.line.shape[1]==2 and len(self.line)>=3 and np.isfinite(self.line).all(),'GEOMETRY_SHAPE_OR_NONFINITE');need(math.isfinite(self.L) and self.L>0 and math.isfinite(self.rho) and self.rho>0,'GEOMETRY_LENGTH_OR_TOLERANCE');self.edges=np.roll(self.line,-1,axis=0)-self.line;self.ds=np.linalg.norm(self.edges,axis=1);need(np.all(self.ds>0),'NONPOSITIVE_SEGMENT');self.sarc=np.r_[0,np.cumsum(self.ds)]
 def pair(self,actual_position,model_position,actual_velocity,model_velocity,phase):
  a=vector(actual_position);m=vector(model_position);av=vector(actual_velocity);mv=vector(model_velocity)
  # Fractions check the axis bound exactly, avoiding a new fitted epsilon and
  # avoiding a rounded norm at the existing 0.1m physical tolerance edge.
  need(all(abs(Fraction.from_float(x)-Fraction.from_float(y))<=Fraction.from_float(self.rho) for x,y in zip(a,m)),'POSITION_OUTSIDE_EXISTING_AXIS_BOUND')
  try:qa=canonical_projection(self.line,a,av,phase);qm=canonical_projection(self.line,m,mv,phase)
  except Exception as e:raise GeometryStop439('PROJECTION_AMBIGUOUS_OR_DOMAIN:'+str(e)) from e
  need(qa['index']==qm['index'] and qa['side']==qm['side'],'SEGMENT_OR_VERTEX_TRANSITION_UNCERTIFIED')
  j=qa['index']
  if a==m:
   need(qa['arc']==qm['arc'],'EXACT_POSITION_PROJECTION_MISMATCH');interval=Interval.point(qa['arc']);kind='IDENTICAL_POSITION_SAME_SOURCE_BRANCH'
  elif qa['side']!='interior':
   need(qa['u']==qm['u'] and qa['arc']==qm['arc'],'VERTEX_CONSTANT_NOT_IDENTICAL');interval=Interval.point(qa['arc']);kind='SAME_CANONICAL_VERTEX_CONSTANT'
  else:
   need(qa['ties']==qm['ties']==1 and 0<qa['u']<1 and 0<qm['u']<1,'INTERIOR_BRANCH_NOT_UNIQUE')
   box=[Interval(down(x-self.rho),up(x+self.rho)) for x in a];delta=[box[i]-Interval.point(self.line[j,i]) for i in range(2)];dot=delta[0]*Interval.point(self.edges[j,0])+delta[1]*Interval.point(self.edges[j,1]);den=float(self.ds[j]*self.ds[j]);fraction=dot/Interval.point(den);fraction=Interval(max(0.,min(1.,fraction.lo)),max(0.,min(1.,fraction.hi)));interval=Interval.point(self.sarc[j])+fraction*Interval.point(self.ds[j]);kind='SAME_UNIQUE_INTERIOR_OUTWARD_FLOAT_EVALUATION'
  need(interval.contains(qa['arc']) and interval.contains(qm['arc']),'PROJECTION_INTERVAL_IMPLEMENTATION_MISMATCH')
  return dict(actual=qa,model=qm,model_arc_interval=interval.values(),branch=kind,position_tolerance=self.rho)
 def delta_interval(self,before,after):
  pre=Interval(*before['model_arc_interval']);post=Interval(*after['model_arc_interval']);half=Interval.point(self.L/2);numerator=post-pre+half
  # Arcs occupy one period. Away from a half-period cut the Python modulo is
  # identity, subtract L, or add L (k=0,+1,-1); each operation is rounded outward.
  k=math.floor((after['actual']['arc']-before['actual']['arc']+self.L/2)/self.L);need(k in [-1,0,1],'UNSUPPORTED_WINDING');lo=Fraction.from_float(k*self.L);hi=Fraction.from_float((k+1)*self.L)
  need(Fraction.from_float(numerator.lo)>lo and Fraction.from_float(numerator.hi)<hi,'UNWRAP_CUT_UNCERTIFIED')
  km=math.floor((after['model']['arc']-before['model']['arc']+self.L/2)/self.L);need(km==k,'WINDING_MISMATCH')
  out=numerator-Interval.point(k*self.L)-half;actual=wrap(after['actual']['arc'],before['actual']['arc'],self.L);model=wrap(after['model']['arc'],before['model']['arc'],self.L);need(out.contains(actual) and out.contains(model),'WRAP_INTERVAL_IMPLEMENTATION_MISMATCH');return out,numerator-Interval.point(k*self.L)
 def transition(self,actual_pre,actual_post,model_pre,model_post,phase_before,phase_after):
  before=self.pair(actual_pre['pos'],model_pre['pos'],actual_pre['vel'],model_pre['vel'],phase_before);after=self.pair(actual_post['pos'],model_post['pos'],actual_post['vel'],model_post['vel'],phase_after);interval,modulus=self.delta_interval(before,after)
  return dict(before=before,after=after,delta_interval=interval.values(),mod_interval=modulus.values(),actual_mod=(after['actual']['arc']-before['actual']['arc']+self.L/2)%self.L,model_mod=(after['model']['arc']-before['model']['arc']+self.L/2)%self.L,actual_delta=wrap(after['actual']['arc'],before['actual']['arc'],self.L),model_delta=wrap(after['model']['arc'],before['model']['arc'],self.L))

 def progress(self,old,transition,which):
  # Preserve the source expression association: (old + mod) - L/2.
  return old+transition[which+'_mod']-self.L/2
 def progress_interval(self,old_interval,transition):return (old_interval+Interval(*transition['mod_interval']))-Interval.point(self.L/2)

def fraction_interval(lo,hi):
 return Interval(down(float(lo)),up(float(hi)))

class Telescope439:
 """Cancel shared intermediate arc endpoints; retain IEEE roundoff intervals.

 p_i = p_(i-1) + arc_i - arc_(i-1) - k_i L + rounding_i.
 After equal winding and validated arc continuity, the arc errors telescope.
 Only the initial/current arc uncertainty plus roundoff sums remain. The error
 bound is point-input outward evaluation minus the exact rational expression;
 it is not fitted to an observed ledger discrepancy.
 """
 def __init__(self,projection):self.p=projection;self.initial=None;self.last=None;self.model_error=Interval.point(0.);self.actual_error=Interval.point(0.)
 def rounding(self,old,pre,post):
  before=dict(model_arc_interval=[pre,pre],actual=dict(arc=pre),model=dict(arc=pre));after=dict(model_arc_interval=[post,post],actual=dict(arc=post),model=dict(arc=post));_,mod=self.p.delta_interval(before,after);evaluated=(Interval.point(old)+mod)-Interval.point(self.p.L/2);k=math.floor((post-pre+self.p.L/2)/self.p.L);ideal=Fraction.from_float(old)+Fraction.from_float(post)-Fraction.from_float(pre)-k*Fraction.from_float(self.p.L);return fraction_interval(Fraction.from_float(evaluated.lo)-ideal,Fraction.from_float(evaluated.hi)-ideal)
 def advance(self,actual_old,model_old,actual_next,model_next,t):
  before=t['before'];after=t['after'];need(advance_float(actual_old,after['actual']['arc'],before['actual']['arc'],self.p.L)==actual_next and advance_float(model_old,after['model']['arc'],before['model']['arc'],self.p.L)==model_next,'TELESCOPE_SOURCE_ARITHMETIC')
  if self.initial is None:
   need(actual_old==model_old,'TELESCOPE_INITIAL_LEDGER_NOT_SHARED');self.initial=before
  else:need(self.last['actual']['arc']==before['actual']['arc'] and self.last['model']['arc']==before['model']['arc'],'TELESCOPE_ARC_CONTINUITY_UNPROVEN')
  self.actual_error=self.actual_error+self.rounding(actual_old,before['actual']['arc'],after['actual']['arc']);self.model_error=self.model_error+self.rounding(model_old,before['model']['arc'],after['model']['arc']);self.last=after
  current_error=Interval(*after['model_arc_interval'])-Interval.point(after['actual']['arc']);initial_error=Interval(*self.initial['model_arc_interval'])-Interval.point(self.initial['actual']['arc']);bound=Interval.point(actual_next)+current_error-initial_error+self.model_error-self.actual_error;need(bound.contains(actual_next) and bound.contains(model_next),'TELESCOPE_INTERVAL_IMPLEMENTATION_MISMATCH');return bound

def advance_float(old,post,pre,L):return old+(post-pre+L/2)%L-L/2
