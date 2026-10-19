"""Read stored 586 values only; no dynamics, optimizer or derivative evaluation."""
import hashlib,json,time
from pathlib import Path
import numpy as np

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response586-recovery-private');P=Path('/workspace/haic-response586-private');inputs={}
 def read(p):
  b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return json.loads(b)
 seed=read(P/'positive-private.json')['suffix'];x0=np.asarray(seed['x']);base=float(seed['f']);g0=np.asarray(seed['g']);S=np.tile([.02,.1],25)
 events=read(G/'retry/shoot586_events.json');cases={e['id']:read(D/f"case-{e['id']:03d}-private.json")['case'] for e in events};names=['force0','force1','force2','force3','clipping','footprint','path','reference','projection_low','projection_high','body']
 proposals=[]
 for e in events:
  if e['candidate_kind']!='proposal':continue
  c=cases[e['id']];delta=np.asarray(c['x'])-x0
  proposals.append(dict(id=e['id'],admissible=c['admissible'],failure=c['failure'],objective_delta_s=c['f']-base,changed_coordinates=int(np.count_nonzero(delta)),early25_34_changed=int(np.count_nonzero(delta[:20])),early_steering_max_abs=float(np.max(np.abs(delta[:20:2]))),early_pedal_max_abs=float(np.max(np.abs(delta[1:20:2]))),all_steering_max_abs=float(np.max(np.abs(delta[::2]))),all_pedal_max_abs=float(np.max(np.abs(delta[1::2]))),normalized_Linf=float(np.max(np.abs(delta/S))),first_failure_raw=e['first_failure_raw']))
 batches=[]
 for p in sorted(D.glob('FD-*-private.json')):
  fd=read(p);df=np.asarray(fd['df']);J=np.asarray(fd['J']);anchor=np.asarray(fd['anchor']);anchor_c=seed if np.array_equal(anchor,x0) else next(c for c in cases.values() if np.array_equal(np.asarray(c['x']),anchor));ac=np.asarray(anchor_c['g']);detail=fd['details'];valid=np.asarray([t['admissible'] for t in detail]);components={n:dict(min_residual=float(ac[:-2].reshape(156,11)[:,k].min()),rows_under_001=int(np.sum(ac[:-2].reshape(156,11)[:,k]<.01))) for k,n in enumerate(names)}
  grads={}
  for label,sl in [('early25_34',slice(0,20)),('later35_49',slice(20,50))]:
   inds=np.arange(50)[sl];good=inds[valid[inds]];bad=inds[~valid[inds]]
   grads[label]=dict(columns=len(inds),admissible_FD=len(good),failed_FD=len(bad),max_abs_df_all=float(np.max(np.abs(df[inds]))),max_abs_df_admissible=float(np.max(np.abs(df[good]))) if len(good) else None,failed_objective_jump_range_s=[float(min(cases[detail[j]['case_id']]['f']-anchor_c['f'] for j in bad)),float(max(cases[detail[j]['case_id']]['f']-anchor_c['f'] for j in bad))] if len(bad) else None)
  anchor_id=anchor_c['id']
  for pr in proposals:
   if (pr['id']<=62)!=(anchor_id==0):continue
   z=(np.asarray(cases[pr['id']]['x'])-anchor)/S;predg=ac+J@z
   pr.update(anchor_case_id=anchor_id,linear_predicted_objective_delta_from_anchor_s=float(df@z),linear_predicted_negative_residuals=int(np.sum(predg<0)),linear_predicted_minimum_residual=float(predg.min()))
  batches.append(dict(file=p.name,anchor_case_id=anchor_id,anchor_is_seed=np.array_equal(anchor,x0),anchor_admissible=anchor_c['admissible'],gradient_groups=grads,anchor_constraint_groups=components,failed_FD_causes={why:sum(cases[t['case_id']]['failure']==why for t in detail) for why in sorted({cases[t['case_id']]['failure'] for t in detail if not t['admissible']})},terminal_J_nonzero_columns=int(np.sum(np.any(J[-2:]!=0,axis=0))),J_max_abs=float(np.max(np.abs(J))),df_max_abs=float(np.max(np.abs(df)))))
 out=dict(status='SOURCE0_DIRECTION_RESELECTION_ONLY',source_ticks=0,force_calls=0,new_FD=0,new_solver=0,native_actions=0,deadline_utc='2026-10-20T10:01:55Z',seed_minimum_residual=float(g0.min()),seed_signed_pedal_at_abs1=int(np.sum(np.abs(x0[1::2])==1)),proposals=proposals,stored_complete_Jacobians=batches,inputs_sha256=inputs,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,prior_source0_analysis_and_import_conservative_CPU_wall_charge_s=5.)
 out['total_source0_analysis_CPU_s']=out['CPU_s']+5.;out['total_source0_analysis_wall_s']=out['wall_s']+5.
 (G/'retry/reselect587_analysis.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items() if k!='inputs_sha256'},indent=2))
if __name__=='__main__':run()
