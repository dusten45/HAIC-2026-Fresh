"""Complete stored416 aggregation and remaining static boundary probes after expected projection rejection."""
import collections,datetime,json,math,os,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.domain416_audit import sigma_certificate
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.scalar392_audit import pedals
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage416';assert not(d/'completion-plan.json').exists();first=read(d/'result.json');assert first['status']=='STATIC_GATE_STOP' and first['error']=='ExecutorDomainError: Distinct_or_nonadjacent_projection_ambiguity' and first['rows']==5364 and first['recorded411_C_nominal_mismatches']==0
 base=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'result.json',d/'rows-private.json',d/'boundaries-private.json',d/'recorded411-nominal-checks.json',G/'retry/domain416_audit.py']
 p=dict(stage=416,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=base['deadline_utc'],recovery='Expectedvertexprojectiondomainrejectionwasuncaught inboundaryaudit. Preserveinitialfailure/5364rowcertificates/188Cpedalchecks and6completedvertexprobes. No rowsnumericre-evaluation/no policyprojectionrepair. Resumeonlyunprocessedvertexprobes and7synthetics; domainrejectionisreportedwithheldresult, nottreatedaspass. Read-onlyaggregation. OriginalstaticCPU60/wall120totalacrosstwoprocesses, nopreparationtimechargedasexecution.',CPU_remaining_s=60-first['CPU_s'],wall_remaining_s=120-first['wall_s'],sources={str(f):sha(f) for f in files},protected=base['protected'],original408_preserve=base['original408_preserve'])
 save(d/'completion-plan.json',p);(d/'completion-plan.sha256').write_text(sha(d/'completion-plan.json')+'\n');print('completion frozen',sha(d/'completion-plan.json'))

def run(root):
 d=root/'stage416';p=read(d/'completion-plan.json');assert sha(d/'completion-plan.json')==(d/'completion-plan.sha256').read_text().strip();assert not(d/'completion-opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'completion-opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));rows=read(d/'rows-private.json');first=read(d/'result.json');boundaries=read(d/'boundaries-private.json');done=len(boundaries);groups={};synthetic=[];error=None;probe=0
 def timeout(*a):raise TimeoutError('remaining_static_CPU_wall')
 previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,p['CPU_remaining_s']);signal.setitimer(signal.ITIMER_REAL,p['wall_remaining_s'])
 try:
  paths=[];p390=read(root/'stage390/plan.json')
  for case in ['O0','N1']:
   fixed=read(Path(p390['A_plans'][case]));paths.append(('390_'+case,fixed,np.asarray(fixed['free_profile']['speed'])*1.5))
  fixed=read(root/'stage269/N1-plan-private.json');paths.append(('N1_268',fixed,np.asarray(fixed['free_profile']['speed'])*np.asarray(read(root/'stage404/profiles-private.json')['frozen268'])))
  for name,(fixed,nodes) in [(name,(fixed,nodes)) for name,fixed,nodes in paths]:
   line=np.asarray(fixed['line']);ds=np.asarray(fixed['free_profile']['ds']);edges=np.roll(line,-1,axis=0)-line;ts=edges/np.linalg.norm(edges,axis=1)[:,None];feeds=np.diff(nodes**2)/(2*ds)
   for i in range(len(line)):
    j=(i-1)%len(line);rL=float(nodes[i] if i else nodes[-1]);rR=float(nodes[i]);tangent=ts[j]+ts[i];tangent=tangent/np.linalg.norm(tangent)
    for direction in [0,1,-1]:
     probe+=1
     if probe<=done:continue
     vel=direction*rR*tangent;v=float(np.linalg.norm(vel));sigL=float(vel@ts[j]);sigR=float(vel@ts[i]);aL=feeds[j]*(sigL/rL)+1.5*(rL-v) if rL>0 else None;aR=feeds[i]*(sigR/rR)+1.5*(rR-v) if rR>0 else None;cmdL=pedals(aL,v,fixed['model']) if aL is not None else None;cmdR=pedals(aR,v,fixed['model']) if aR is not None else None;rejected=None;side=None;identity=None;ties=None
     try:
      cp=canonical_projection(line,line[i],vel,'FIRST_LAP');assert cp['index']==(len(line)-1 if i==0 else i);side=cp['side']
     except ExecutorDomainError as e:
      rejected=str(e);u=np.clip(np.sum((line[i]-line)*edges,axis=1)/(ds*ds),0,1);feet=line+u[:,None]*edges;dist=np.sum((feet-line[i])**2,axis=1);ties=np.flatnonzero(dist==dist.min()).tolist();identity=all(z in [j,i] and (np.array_equal(line[i],line[z]) or np.array_equal(line[i],line[(z+1)%len(line)])) for z in ties)
     boundaries.append(dict(path=name,node=i,direction=direction,stationary=direction==0,seam=i==0,r_left=rL,r_right=rR,raw_left=aL,raw_right=aR,raw_jump=None if aL is None or aR is None else aR-aL,pedal_jump=None if cmdL is None or cmdR is None else max(abs(cmdR['gas']-cmdL['gas']),abs(cmdR['brake']-cmdL['brake'])),canonical_side=side,canonical_rejected=rejected,rounded_ties_adjacent_same_exact_vertex=identity,float_tied_segments=ties,meaningful_reverse=(sigL<-.1 or sigR<-.1)))
  for sigma in [0.,2.**-40,-2.**-40,1.,-1.,math.ulp(0.),-math.ulp(0.)]:
   cert=sigma_certificate([0.,0.],[1.,0.],[sigma,0.]);raw=-3.*(sigma/2.)+1.5*(2.-abs(sigma));synthetic.append(dict(sigma=sigma,speed=abs(sigma),raw=raw,meaningful_reverse=sigma<-.1,certificate=cert));assert math.isfinite(raw)
  assert synthetic[0]['raw']==3. and synthetic[4]['meaningful_reverse']
  for dataset in sorted(set(z['dataset'] for z in rows)):
   data=[z for z in rows if z['dataset']==dataset];valid=[z for z in data if 'sigma' in z];neg=[z for z in valid if z['sigma']['sigma']<0];changed=[z for z in valid if z['changed_definition']];normal=[z for z in valid if z['positive_target'] and z['sigma']['sigma']>=0];defined=[z for z in valid if z['defined']]
   groups[dataset]=dict(rows=len(data),projection_unqualified=len(data)-len(valid),projection_reasons=dict(collections.Counter(z.get('withheld') for z in data if 'sigma' not in z)),positive_target=sum(z['positive_target'] for z in valid),r_zero=sum(not z['positive_target'] for z in valid),prior393_withheld=dict(collections.Counter(z['prior393_withheld'] for z in valid if z['prior393_withheld'])),algebra_defined=len(defined),strict_negative_rejects=len(neg),negative_sigma_range=[min((z['sigma']['sigma'] for z in neg),default=None),max((z['sigma']['sigma'] for z in neg),default=None)],meaningful_reverse_unsafe=sum(z['meaningful_reverse_unsafe'] for z in valid),changed_definition=len(changed),changed_definition_brakes=sum(z['signed_C_algebra']['brake']>0 for z in changed),changed_definition_gas=sum(z['signed_C_algebra']['gas']>0 for z in changed),roundoff_sign_uncertain=sum(z['sigma']['roundoff_sign_uncertain'] for z in valid),float32_velocity_roundtrip=sum(z['sigma']['float32_velocity_exact'] for z in valid),max_sigma_evaluation_error=max((z['sigma']['absolute_error'] for z in valid),default=None),max_gamma16_bound=max((z['sigma']['gamma16_bound'] for z in valid),default=None),nonnegative_existing_expression_unchanged=len(normal),max_recorded393_C_raw_delta=max((abs(z['recorded393_C_raw_delta']) for z in valid if z.get('recorded393_C_raw_delta') is not None),default=None))
  status='STATIC_SIGNED_ALGEBRA_VALIDATED_BOUNDARY_HOLES_REMAIN_NO_POLICY_CHANGE'
 except Exception as e:status='COMPLETION_GATE_STOP';error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in previous.items():signal.signal(s,h)
 save(d/'boundaries-complete-private.json',boundaries);save(d/'synthetic-complete.json',synthetic)
 nonseam=[z for z in boundaries if not z['seam']];forward=[z for z in nonseam if z['direction']==1];stationary=[z for z in nonseam if z['stationary']];rejected=[z for z in boundaries if z.get('canonical_rejected')];boundary=dict(total_probes=len(boundaries),completed_before_recovery=done,remaining_probes=len(boundaries)-done,rejected=len(rejected),rejected_vertices=len(set((z['path'],z['node']) for z in rejected)),adjacent_same_exact_vertex_rejections=sum(bool(z['rounded_ties_adjacent_same_exact_vertex']) for z in rejected),nonseam_stationary_max_raw_jump=max(abs(z['raw_jump']) for z in stationary if z['raw_jump'] is not None),nonseam_forward_max_raw_jump=max(abs(z['raw_jump']) for z in forward if z['raw_jump'] is not None),nonseam_forward_max_pedal_jump=max(z['pedal_jump'] for z in forward if z['pedal_jump'] is not None),nonseam_forward_nonzero_pedal_jumps=sum(z['pedal_jump'] is not None and z['pedal_jump']>0 for z in forward),seam_zero_outgoing=len([z for z in boundaries if z['seam'] and z['r_right']==0]),by_path={name:dict(vertices=len(line['line']),rejected_vertices=len(set(z['node'] for z in rejected if z['path']==name))) for name,line,nodes in paths},scope='Mathematicalone-sidedCjumps preexist; exactvertexcanonicalfalseambiguity unmodified. Noepsilon/repair/fallback. Directioncasesreusevertexnotindependentobservations.')
 final=next(z for z in rows if z['dataset']=='414_final');valid=[z for z in rows if 'sigma' in z];changed=[z for z in valid if z['changed_definition']];checks=read(d/'recorded411-nominal-checks.json')
 result=dict(stage=416,status=status,error=error,initial_boundary_exception_preserved=True,no_stored_state_numeric_reexecution=True,rows=len(rows),numeric_certificates=len(valid),datasets=groups,total_strict_negative_rejects=sum(z['strict_negative_gate_reject'] for z in valid),total_changed_definition=len(changed),meaningful_reverse_unsafe=sum(z['meaningful_reverse_unsafe'] for z in valid),changed_definition_max_speed=max(z['speed'] for z in changed),changed_definition_max_abs_sigma=max(abs(z['sigma']['sigma']) for z in changed),all_numeric_certificates_passed=error is None,recorded411_C_nominal_checks=len(checks),recorded411_C_nominal_mismatches=sum(not z['passed'] for z in checks),boundary_summary=boundary,final414=final,synthetic_cases=len(synthetic),zero_target_contract='undefinedpositive-targetformula; keepexistingphasegates. Noepsilon/fallback.',actual_policy_changed=False,new_native_reset_model_actor_learning_SEALED_reserve_paid=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,initial_execution_CPU_s=first['CPU_s'],initial_execution_wall_s=first['wall_s'],plan_sha256=sha(d/'completion-plan.json'))
 result.update(total_static_CPU_s=result['CPU_s']+first['CPU_s'],total_static_wall_s=result['wall_s']+first['wall_s']);assert result['total_static_CPU_s']<60 and result['total_static_wall_s']<120
 save(d/'completion-result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['datasets']}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
