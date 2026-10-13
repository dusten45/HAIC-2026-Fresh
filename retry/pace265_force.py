"""Read-only actual source tire-vector saturation aggregation; never controller input."""
import inspect,sys
from core.vendor.car_dynamics import Car

class TireTrace:
 def __init__(self):
  lines,first=inspect.getsourcelines(Car.step);self.line=first+next(i for i,l in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit:' in l);self.previous=None;self.total=[];self.current=[]
 def trace(self,frame,event,arg):
  if frame.f_code is not Car.step.__code__:return None
  if event=='line' and frame.f_lineno==self.line:
   q=frame.f_locals;wheel=next(i for i,w in enumerate(q['self'].wheels) if w==q['w']);limit=float(q['friction_limit']);ratio=float(q['force'])/limit;r=dict(wheel=wheel,clipped=ratio>1,raw_force_ratio=ratio,grass=bool(q['grass']),lateral_slip=abs(float(q['vs'])));self.current.append(r);self.total.append(r)
  return self.trace
 def enable(self):self.previous=sys.gettrace();sys.settrace(self.trace)
 def disable(self):sys.settrace(self.previous)
 def begin_action(self):self.current=[]
 def summarize(self,rows=None):
  rows=self.current if rows is None else rows
  def group(indices):
   r=[x for x in rows if x['wheel'] in indices]
   return dict(samples=len(r),clipped_fraction=sum(x['clipped'] for x in r)/len(r) if r else 0.,road_clipped_fraction=sum(x['clipped'] for x in r if not x['grass'])/max(1,sum(not x['grass'] for x in r)),grass_fraction=sum(x['grass'] for x in r)/len(r) if r else 0.,max_raw_force_ratio=max((x['raw_force_ratio'] for x in r),default=0.),mean_abs_lateral_slip=sum(x['lateral_slip'] for x in r)/len(r) if r else 0.)
  return dict(front=group([0,1]),rear=group([2,3]),all=group([0,1,2,3]))
