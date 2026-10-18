"""Freeze one empirical interior rule from saved564 errors; source ticks0."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write,plain,prefix_slacks
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response565-private');OLD=Path('/workspace/haic-response564-private');rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(mode=0o700,exist_ok=False);cpu,wall=time.process_time(),time.perf_counter();inputs={};errors=[];quant=[];ordererrors=[];ordquant=[];ratioerrors=[];rquant=[];details=[]
 atomic_write(D/'DESIGN-STARTED.json',dict(source_sha256=sha(G/'retry/interior565_design.py'),rule='2*(max positive optimistic error over final TWO564restoration steps + max fullfloat32controlULP propagation + fourbinary64ULPs). No buffer sweep. All-slack and prefix arrays fixed before565model.'))
 for l,c,t in [(2,'trial-00-00','trial-00-01'),(3,'trial-00-01','trial-00-02')]:
  paths=[OLD/(c+'-surrogate-private.json'),OLD/(t+'-surrogate-private.json')]+[OLD/f'FD-{l:02d}-{j:02d}-private.json' for j in range(40)];inputs.update({str(p):sha(p) for p in paths});a,b,*fd=map(rd,paths);dx=np.array(b['x'])-a['x'];jg=np.array([(np.array(q['g'])-a['g'])/(q['x'][j]-a['x'][j]) for j,q in enumerate(fd)]).T;jr=np.array([(np.array(q['ratios'])-a['ratios'])/(q['x'][j]-a['x'][j]) for j,q in enumerate(fd)]).T;ulp=np.array([max(abs(float(np.spacing(np.float32(v)))),abs(float(np.nextafter(np.float32(v),np.float32(np.inf)))-v)) for v in b['x']]);pg=np.array(a['g'])+jg@dx;pr=np.array(a['ratios'])+jr@dx;eg=pg-b['g'];er=np.array(b['ratios'])-pr;eo=prefix_slacks(pr,3,160)-b['order'];qg=abs(jg)@ulp;qr=abs(jr)@ulp;qo=np.maximum.accumulate(qr).reshape(-1,4)[:,-1];errors.append(np.maximum(0,eg));ratioerrors.append(np.maximum(0,er));ordererrors.append(np.maximum(0,eo));quant.append(qg);rquant.append(qr);ordquant.append(qo);details.append(dict(linearization=l,ratio_positive_error_max=float(max(er)),order_optimism_max=float(max(eo)),ratio_control_ULP_max=float(max(qr))))
 ge=np.max(errors,axis=0);gq=np.max(quant,axis=0);pe=np.max(ordererrors,axis=0);pq=np.max(ordquant,axis=0);re=np.max(ratioerrors,axis=0);rq=np.max(rquant,axis=0);floor=4*np.finfo(float).eps
 gm=2*(ge+gq+floor);pm=2*(pe+pq+floor);rm=2*(re+rq+floor)
 atomic_write(D/'interior-targets-private.json',dict(physical=gm,prefix=pm,ratio=rm,physical_error=ge,physical_quant=gq,prefix_error=pe,prefix_quant=pq,ratio_error=re,ratio_quant=rq,details=details))
 groups={}
 for label,value in zip(a['labels'],gm):groups[label]=max(groups.get(label,0.),float(value))
 out=dict(rule='Two times (maximum positive slack overoptimism across last TWO564 restoration predictions + maximum propagated fullfloat32controlULP + fourbinary64ULPs). Force is physical slack,clipping uses prefix orderstat target>0. Same fixed arrays for all565iterations. Empirical numerical interior,not universal errorbound or relaxed safety.',source_sha256=sha(G/'retry/interior565_design.py'),inputs_sha256=inputs,private_targets_sha256=sha(D/'interior-targets-private.json'),physical_margin_max_by_label=groups,prefix_margin_min=float(min(pm)),prefix_margin_max=float(max(pm)),ratio_margin_max=float(max(rm)),details=details,model_ticks=0,force_calls=0,geometry_calls=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 atomic_write(G/'retry/interior565_design.json',out);print(json.dumps(plain({k:v for k,v in out.items() if k!='inputs_sha256'}),indent=2))
if __name__=='__main__':main()
