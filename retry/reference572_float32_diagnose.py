"""Stored-model-only 572 quantization diagnosis; all source calls prohibited."""
import copy,inspect,json,textwrap,time
from pathlib import Path
import numpy as np
import retry.reference572_model as m
from retry.clip561_core import atomic_write
from retry.path569_design import sha
from core.vendor.car_racing import CarRacing
G=m.G;D=m.D;rd=m.rd

def forbidden(*a,**kw):raise RuntimeError('SOURCE_OR_NATIVE_FORBIDDEN_IN_READ_ONLY_DIAGNOSIS')
m.d.source_tick=m.d.force_rows=forbidden
CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
class Dry(m.Study):
 def support_model(self,*args):return tuple(np.asarray(self.support[k]) for k in ['seed_slacks','Jacobian','error_coefficients'])
 def capture(self,aa,bb,bounds,zz,tt,model_path,alpha,sol,keep,ids,q):
  mapping=np.flatnonzero(keep);K=len(q);M=len(mapping);N=68;R=len(ids);known=np.flatnonzero(np.isin(self.center['labels'],['force','body','reference']))
  def physical(i):
   k=i%10
   return dict(condition=self.center['labels'][i],raw=529+int(i)//10,force_wheel=int(k-3) if 3<=k<=6 else None)
  def name(i):
   blocks=[('physical',M),('rank_ratio',R),('signed_support',K),('support_upper',K),('scalar_error_upper',M),('path_error_upper',134),('ratio_error_upper',R),('physical_upper',len(known)),('norm_positive',N),('norm_negative',N),('path_support',536)]
   for block,n in blocks:
    if i<n:
     out=dict(block=block,row_in_block=int(i))
     if block in ['physical','scalar_error_upper']:out.update(physical(int(mapping[i])))
     elif block=='physical_upper':out.update(physical(int(known[i])))
     elif block in ['signed_support','support_upper']:
      key=self.support['keys'][i];raw,kind,poly,feature,vertex=key.split(':');out.update(raw=529+int(raw),kind=kind,polygon=int(poly),feature=int(feature),vertex=int(vertex),support_key=key)
     elif block in ['rank_ratio','ratio_error_upper']:out.update(raw=529+int(ids[i])//4,force_wheel=int(ids[i])%4)
     elif block in ['norm_positive','norm_negative']:out.update(hold=133+int(i)//2,control='steer' if i%2==0 else 'pedal')
     return out
    i-=n
   return dict(block='extra_path_support_cut',row_in_block=int(i))
  y=aa@np.r_[zz,tt];res=y-bb;top=[]
  for j in np.argsort(-res)[:8]:
   if res[j]>0:top.append(dict(name(int(j)),lhs=float(y[j]),rhs=float(bb[j]),residual=float(res[j]),exceeds_gate=bool(res[j]>1e-8)))
  bbad=[]
  for j,(value,(lo,hi)) in enumerate(zip(np.r_[zz,tt],bounds)):
   residual=max(lo-value,value-hi)
   if residual>0:bbad.append(dict(variable=j,hold=133+j//2 if j<68 else None,control=('steer' if j%2==0 else 'pedal') if j<68 else 'norm_epigraph',value=float(value),lower=float(lo),upper=float(hi),residual=float(residual)))
  self.repairs.append(dict(alpha=alpha,linear_violation=max(0.,float(max(res))),path_violation=max(0.,float(max(model_path-3))),bound_violation=max([0.]+[x['residual'] for x in bbad]),maximum_linear_rows=top,violated_bounds=bbad,accept_tolerance=1e-8))


def compact(out):
 value={k:v for k,v in out.items() if k!='repairs'};value['repairs']=[]
 for row in out['repairs']:
  entry={k:v for k,v in row.items() if k not in ['maximum_linear_rows','violated_bounds']}
  entry['failing_linear_rows']=[v for v in row['maximum_linear_rows'] if v['exceeds_gate']]
  bounds=row['violated_bounds'];entry['violated_bound_count']=len(bounds)
  entry['maximum_bound_example']=max(bounds,key=lambda v:v['residual']) if bounds else None
  value['repairs'].append(entry)
 value['reconstruction_code_sha256']=sha(G/'retry/reference572_float32_diagnose.py')
 return value

cpu,wall=time.process_time(),time.perf_counter();o=object.__new__(Dry);o.static=rd(m.base.INPUTS[1]);o.paths=rd(m.base.INPUTS[2]);tape=rd(m.base.INPUTS[0]);r=tape['rows'][527];o.start=dict(root=m.d.load_root(dict(r['root_without_roads'],roads=o.static['root']['roads'])),progress=r['progress'],tracking=[64,1728],tracker=m.d.FinishLineTracker(**r['tracker']));o.s900=m.base.station_point(o.paths['candidate'],900.);saved=rd(D/'proposal-2-0-diagnostic-private.json');o.center=o.metric(saved['rows']);o.center.update(x=np.asarray(saved['x']),rows=saved['rows'],label='proposal-2-0-diagnostic');o.seed_x=np.asarray(rd(m.OLD/'proposal-4-0-diagnostic-private.json')['x']);o.frozen_segments(o.center);o.support=rd(D/'proposal-3-0-support-private.json');o.repairs=[];linear={k:np.asarray(v) for k,v in rd(D/'linear-4-private.json')['linear'].items()};env=rd(D/'envelope-4-private.json')
source=textwrap.dedent(inspect.getsource(m.Study.solve));source=source.replace("atomic_write(D/(tag+'-precheck-private.json'),pre)","self.precheck=pre");needle='            if linear_violation<=1e-8 and path_violation<=1e-8 and bound_violation<=1e-8:';assert needle in source;source=source.replace(needle,'            self.capture(aa,bb,bounds,zz,tt,model_path,alpha,sol,keep,ids,support_q)\n'+needle);ns=dict(m.__dict__);exec(compile(source,'<same572-stored-model-solve-with-residual-capture>','exec'),ns);x,meta=ns['solve'](o,o.center,linear,env,.05,'proposal-3-0-readonly');paths=[D/'proposal-2-0-diagnostic-private.json',D/'linear-4-private.json',D/'envelope-4-private.json',D/'proposal-3-0-support-private.json',G/'retry/reference572_model.py'];out=dict(scope='Stored-model LP reconstruction only. Original per-repair residuals were not saved; these values reproduce the gate but are not direct historical residual logs.',source_ticks=0,native_actions=0,source_model_hashes={str(p):sha(p) for p in paths},same_precheck=o.precheck==rd(D/'proposal-3-0-precheck-private.json'),same_stop_reason=meta['reason']=='NO_FLOAT32_MODEL_FEASIBLE_STEP',source_candidate_produced=x is not None,repairs=o.repairs,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);atomic_write(D/'float32-diagnosis-private.json',out);public=compact(out);atomic_write(G/'retry/reference572_float32_diagnosis.json',public);print(json.dumps(public,indent=2))
