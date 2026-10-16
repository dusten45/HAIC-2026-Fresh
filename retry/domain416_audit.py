"""Static signed-progress contract audit; never calls environment, controller act or model step."""
import collections,datetime,json,math,os,signal,sys,time
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.scalar392_audit import pedals
G=Path(__file__).resolve().parents[1]
INF=float('inf');U=2.**-53;TINY=np.finfo(float).tiny

def down(x):return math.nextafter(float(x),-INF)
def up(x):return math.nextafter(float(x),INF)
def add(x,y):return(down(x[0]+y[0]),up(x[1]+y[1]))
def sub(x,y):return(down(x[0]-y[1]),up(x[1]-y[0]))
def mul(x,y):
 z=[a*b for a in x for b in y];return(down(min(z)),up(max(z)))
def div(x,y):
 if y[0]<=0<=y[1]:raise ArithmeticError('interval_zero_denominator')
 z=[a/b for a in x for b in y];return(down(min(z)),up(max(z)))
def sqrt(x):
 if x[1]<0:raise ArithmeticError('negative_squared_length')
 return(max(0.,down(math.sqrt(max(0.,x[0])))),up(math.sqrt(x[1])))
def interval_sigma(a,b,v):
 es=[sub((b[i],b[i]),(a[i],a[i])) for i in range(2)];ss=add(mul(es[0],es[0]),mul(es[1],es[1]));norm=sqrt(ss);ts=[div(e,norm) for e in es];z=add(mul((v[0],v[0]),ts[0]),mul((v[1],v[1]),ts[1]));P=up(up(abs(v[0])*max(map(abs,ts[0])))+up(abs(v[1])*max(map(abs,ts[1]))));gamma=up((16*U)/(1-16*U));return z,up(gamma*P)
def sigma_certificate(a,b,v):
 a=np.asarray(a,float);b=np.asarray(b,float);v=np.asarray(v,float);e=b-a;le=float(np.linalg.norm(e));sigma=float(v@(e/le));iv,E=interval_sigma(a,b,v)
 with localcontext() as ctx:
  ctx.prec=100;D=Decimal.from_float;ed=[D(float(b[i]))-D(float(a[i])) for i in range(2)];vd=[D(float(x)) for x in v];hp=(vd[0]*ed[0]+vd[1]*ed[1])/(ed[0]**2+ed[1]**2).sqrt();err=abs(D(sigma)-hp);hp_in=D(iv[0])<=hp<=D(iv[1]);normal=all(x==0 or abs(x)>=TINY for x in [*e,*v,*(e/le),*(v*(e/le)),sigma]);gamma_ok=(err<=D(E)) if normal else None
  exact_num=sum((Fraction(float(v[i]))*(Fraction(float(b[i]))-Fraction(float(a[i]))) for i in range(2)),Fraction());exact_sign=(exact_num>0)-(exact_num<0);assert exact_sign==(hp>0)-(hp<0)
  if not(hp_in and iv[0]<=sigma<=iv[1] and gamma_ok is not False):raise ArithmeticError('sigma_error_certificate_failure')
  quant=0.
  roundtrip=all(float(np.float32(z))==z for z in v)
  if roundtrip:
   for j,z in enumerate(v):
    z32=np.float32(z);hi=float(np.nextafter(z32,np.float32(INF),dtype=np.float32));lo=float(np.nextafter(z32,np.float32(-INF),dtype=np.float32));tau=max(hi-z,z-lo)/2;quant=up(quant+up(tau*abs(float((e/le)[j]))))
  return dict(sigma=sigma,interval=[*iv],gamma16_bound=E,gamma_applicable=normal,high_precision_sigma=str(hp),exact_sign=exact_sign,absolute_error=float(err),roundoff_sign_uncertain=iv[0]<=0<=iv[1],float32_velocity_exact=roundtrip,velocity_halfULP_sigma_cell_bound=quant if roundtrip else None)

def records(root):
 p390=read(root/'stage390/plan.json');data393=read(root/'stage393/row-evaluations-private.json');ref393={(x['case'],x['step']):x for x in data393}
 for case in ['O0','N1']:
  fixed=read(Path(p390['A_plans'][case]));rows=read(root/('stage390/A-'+case)/'trace-private.json')
  for tag in ['390','393']:
   for z in rows:yield dict(dataset=tag+'_'+case,state=z['pre'],fixed=fixed,pace=1.5,reference393=ref393[(case,z['step'])],step=z['step'],lifecycle='historical393withheld' if ref393[(case,z['step'])]['withheld'] else 'firstlap_algebra')
 fixed=read(root/'stage269/N1-plan-private.json');pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268'])
 with (root/'stage410/forecasts-private.jsonl').open() as file:
  for index,text in enumerate(file):
   z=json.loads(text)
   for row in z['forecast']['rows']:
    q=row['predicted'];state=dict(pos=q['position'],vel=q['velocity'],speed=q['speed_m_s'],angle=q['angle']);yield dict(dataset='410_'+z['arm'],state=state,fixed=fixed,pace=pace,step=[index,row['offset']],lifecycle='forecast_poststate_no_runtime_phase',finished=q['finished'])
 for stage,label in [(411,'policy_O'),(411,'policy_C'),(413,'actual_A'),(413,'actual_B'),(414,'')]:
  file=root/('stage'+str(stage))/label/'trace-private.jsonl'
  with file.open() as stream:
   for text in stream:
    z=json.loads(text);ref=z if stage==411 and label=='policy_C' else None;yield dict(dataset=str(stage)+('_'+label if label else ''),state=z['pre'],fixed=fixed,pace=pace,step=z['step'],reference411=ref,lifecycle='actual_prestate')
 final=read(root/'stage414/final-private.json');h=final['physical']['hull'];yield dict(dataset='414_final',state=dict(pos=h['position'],vel=h['velocity'],speed=float(np.linalg.norm(h['velocity'])),angle=h['angle']),fixed=fixed,pace=pace,step=197,lifecycle='stopped_final_noCmemory')

def prepare(root):
 d=root/'stage416';assert not(d/'plan.json').exists();old=read(root/'stage415/plan.json');v=read(root/'project-effective-budget-v435.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(29880,84000,0)
 p390=read(root/'stage390/plan.json');files=[Path(__file__),G/'retry/domain416_contract.md',G/'retry/executor397.py',G/'retry/scalar392_audit.py',G/'retry/cross404_common.py',G/'retry/loss389_replay.py',G/'core/vendor/car_dynamics.py',root/'stage390/plan.json',root/'stage393/row-evaluations-private.json',root/'stage410/forecasts-private.jsonl',root/'stage269/N1-plan-private.json',root/'stage404/profiles-private.json',root/'stage414/final-private.json',root/'project-effective-budget-v435.json',root/'research-deadline-current.json']
 files += [Path(p390['A_plans'][case]) for case in ['O0','N1']]+[root/('stage390/A-'+case)/'trace-private.json' for case in ['O0','N1']]
 files += [root/f'stage{stage}'/label/'trace-private.jsonl' for stage,label in [(411,'policy_O'),(411,'policy_C'),(413,'actual_A'),(413,'actual_B'),(414,'')]]
 p=dict(stage=416,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],contract_file=str(G/'retry/domain416_contract.md'),CPU_cap_s=60,wall_cap_s=120,row_cap=6000,max_parallel=1,no_native_model_actor_learning_SEALED_reserve_paid=True,sources={str(f):sha(f) for f in files},protected=old['protected'],original408_preserve=old['original408_preserve'],numerical_contract='gamma16derived11ops+intervalDAG+Decimal100andFractionexactsignednumerator. Float32representationcellnotphysicalerror. Noepsilon/clip; sigma<-.1 orbodyforward<-.1safetyunchanged. SignedCformulaallreal sigma whenr>0; existingexecutionfilefrozen. Firstcertificate/normalCpedal mismatch stop.',synthetic='r2 f-3, v=abs(sigma), sigma in[0,+-2^-40,+-1,+-minsubnormal]. r0undefined. Allvertices allstored390casepaths+N1frozen268, commonpositive-node r, v=0 orforward/reverseunitbisector atnode r. Phase/seamseparate.')
 for f,h in {**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,CPU_fully_measured=False));print('416 frozen',sha(d/'plan.json'))

def run(root):
 d=root/'stage416';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));out=[];groups={};normal_checks=[];error=None;boundaries=[];synthetic=[];paths={};skips=collections.Counter()
 def timeout(*a):raise TimeoutError('staticCPU60_wall120')
 previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,60);signal.setitimer(signal.ITIMER_REAL,120)
 try:
  for n,z in enumerate(records(root)):
   if n>=p['row_cap']:raise RuntimeError('rowcap6000')
   if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')):raise TimeoutError('deadline')
   fixed=z['fixed'];line=np.asarray(fixed['line'],float);nodes=np.asarray(fixed['free_profile']['speed'],float)*z['pace'];paths.setdefault('390_'+z['dataset'].split('_')[-1] if z['dataset'].startswith(('390_','393_')) else 'N1_268',(fixed,nodes));state=z['state'];vel=np.asarray(state['vel'],float);speed=state['speed'];row=dict(dataset=z['dataset'],step=z['step'],lifecycle=z['lifecycle'],speed=speed)
   try:q=canonical_projection(line,state['pos'],vel,'FIRST_LAP')
   except ExecutorDomainError as e:row.update(defined=False,withheld=str(e));out.append(row);continue
   i=q['index'];cert=sigma_certificate(line[i],line[(i+1)%len(line)],vel);r=float(np.sqrt((1-q['u'])*nodes[i]**2+q['u']*nodes[i+1]**2));f=float((nodes[i+1]**2-nodes[i]**2)/(2*fixed['free_profile']['ds'][i]));forward=float(vel@np.asarray([-math.sin(state['angle']),math.cos(state['angle'])]));unsafe=q['sigma']<-.1 or forward<-.1;old_reject=q['sigma']<0
   old393=z.get('reference393');prior_withheld=old393['withheld'] if old393 else None;defined=r>0 and prior_withheld is None;raw=f*(q['sigma']/r)+1.5*(r-speed) if r>0 else None;newpedal=pedals(raw,speed,fixed['model']) if raw is not None else None
   row.update(projection_index=i,projection_u=q['u'],projection_side=q['side'],sigma=cert,r=r,f=f,defined=defined,positive_target=r>0,prior393_withheld=prior_withheld,strict_negative_gate_reject=old_reject,meaningful_reverse_unsafe=unsafe,body_forward=forward,signed_C_algebra=newpedal,changed_definition=bool(defined and old_reject and not unsafe),runtime_qualification=False)
   if raw is not None:
    if not math.isfinite(raw):raise ArithmeticError('nonfinite_C')
    # Same law, node inputs, operation order; extension introduces no changedpositive-sigma expression.
    if not old_reject:
     existing=f*(q['sigma']/r)+1.5*(r-speed)
     if pedals(existing,speed,fixed['model'])!=newpedal:raise AssertionError('positive_sigma_pedal_changed')
   ref=z.get('reference411')
   if ref and ref['nominal_memory_after']['C']['phase']=='FIRST_LAP' and r>0 and not old_reject:
    predicted=np.asarray([newpedal['gas'],newpedal['brake']],np.float32);observed=np.asarray(ref['nominal'][1:],np.float32);ok=bool(np.array_equal(predicted,observed));normal_checks.append(dict(step=z['step'],passed=ok,max_abs=float(np.max(abs(predicted-observed)))))
    if not ok:raise AssertionError('recorded411_C_nominal_pedal_mismatch:'+str(z['step']))
   if old393 and old393['C'] is not None:
    # Independentstored393 ruleusesdifferentprojectionimplementation; comparisonnotforcedbitexact.
    row['recorded393_C_raw_delta']=raw-old393['C']['raw_accel'] if raw is not None else None
   out.append(row)
  # Allstoredvertices; one-sided algebra. No smoothing/pathmutation.
  for name,(fixed,nodes) in paths.items():
   line=np.asarray(fixed['line']);ds=np.asarray(fixed['free_profile']['ds']);edges=np.roll(line,-1,axis=0)-line;ts=edges/np.linalg.norm(edges,axis=1)[:,None];feeds=np.diff(nodes**2)/(2*ds)
   for i in range(len(line)):
    before=(i-1)%len(line);rL=float(nodes[i] if i else nodes[-1]);rR=float(nodes[i]);tangent=ts[before]+ts[i];tangent=tangent/np.linalg.norm(tangent)
    for direction in [0,1,-1]:
     vel=direction*rR*tangent;v=float(np.linalg.norm(vel));sigL=float(vel@ts[before]);sigR=float(vel@ts[i]);aL=feeds[before]*(sigL/rL)+1.5*(rL-v) if rL>0 else None;aR=feeds[i]*(sigR/rR)+1.5*(rR-v) if rR>0 else None
     cmdL=pedals(aL,v,fixed['model']) if aL is not None else None;cmdR=pedals(aR,v,fixed['model']) if aR is not None else None
     cp=canonical_projection(line,line[i],vel,'FIRST_LAP');assert cp['index']==(len(line)-1 if i==0 else i)
     boundaries.append(dict(path=name,node=i,direction=direction,stationary=direction==0,seam=i==0,r_left=rL,r_right=rR,raw_left=aL,raw_right=aR,raw_jump=None if aL is None or aR is None else aR-aL,pedal_jump=None if cmdL is None or cmdR is None else max(abs(cmdR['gas']-cmdL['gas']),abs(cmdR['brake']-cmdL['brake'])),canonical_side=cp['side'],meaningful_reverse=(sigL<-.1 or sigR<-.1)))
  for sigma in [0.,2.**-40,-2.**-40,1.,-1.,math.ulp(0.),-math.ulp(0.)]:
   cert=sigma_certificate([0.,0.],[1.,0.],[sigma,0.]);raw=-3.*(sigma/2.)+1.5*(2.-abs(sigma));synthetic.append(dict(sigma=sigma,speed=abs(sigma),raw=raw,meaningful_reverse=sigma<-.1,certificate=cert));assert math.isfinite(raw)
  assert synthetic[0]['raw']==3. and synthetic[4]['meaningful_reverse']
  for dataset in sorted(set(z['dataset'] for z in out)):
   rows=[z for z in out if z['dataset']==dataset];valid=[z for z in rows if 'sigma' in z];neg=[z for z in valid if z['sigma']['sigma']<0];changed=[z for z in valid if z['changed_definition']];defd=[z for z in valid if z['defined']]
   groups[dataset]=dict(rows=len(rows),projection_unqualified=len(rows)-len(valid),positive_target=sum(z['positive_target'] for z in valid),r_zero=sum(not z['positive_target'] for z in valid),prior393_withheld=dict(collections.Counter(z['prior393_withheld'] for z in valid if z['prior393_withheld'])),algebra_defined=len(defd),strict_negative_rejects=len(neg),negative_sigma_range=[min((z['sigma']['sigma'] for z in neg),default=None),max((z['sigma']['sigma'] for z in neg),default=None)],meaningful_reverse_unsafe=sum(z['meaningful_reverse_unsafe'] for z in valid),changed_definition=len(changed),changed_definition_brakes=sum(z['signed_C_algebra']['brake']>0 for z in changed),changed_definition_gas=sum(z['signed_C_algebra']['gas']>0 for z in changed),roundoff_sign_uncertain=sum(z['sigma']['roundoff_sign_uncertain'] for z in valid),float32_velocity_roundtrip=sum(z['sigma']['float32_velocity_exact'] for z in valid),max_sigma_evaluation_error=max((z['sigma']['absolute_error'] for z in valid),default=None),max_gamma16_bound=max((z['sigma']['gamma16_bound'] for z in valid),default=None),normal_nonnegative_expression_unchanged=sum(z['positive_target'] and z['sigma']['sigma']>=0 for z in valid))
  status='STATIC_SIGNED_CONTRACT_VALIDATED_NO_POLICY_CHANGE'
 except Exception as e:status='STATIC_GATE_STOP';error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for sig,handler in previous.items():signal.signal(sig,handler)
 save(d/'rows-private.json',out);save(d/'boundaries-private.json',boundaries);save(d/'synthetic.json',synthetic);save(d/'recorded411-nominal-checks.json',normal_checks)
 interior=[z for z in boundaries if not z['seam']];moving=[z for z in interior if z['direction']==1];stationary=[z for z in interior if z['stationary']];bsummary=dict(vertex_cases=len(boundaries),nonseam_stationary_raw_jump_max=max((abs(z['raw_jump']) for z in stationary if z['raw_jump'] is not None),default=None),forward_nonseam_raw_jump_max=max((abs(z['raw_jump']) for z in moving if z['raw_jump'] is not None),default=None),forward_nonseam_pedal_jump_max=max((z['pedal_jump'] for z in moving if z['pedal_jump'] is not None),default=None),forward_nonseam_nonzero_pedal_jumps=sum(z['pedal_jump'] is not None and z['pedal_jump']>0 for z in moving),seams_with_zero_outgoing_target=sum(z['seam'] and z['r_right']==0 for z in boundaries),canonical_node_rule_assertions=len(boundaries),scope='One-sidedexistingpiecewiseprofilejumps, notintroducedbyallowingsignedsigma. launch/finishseamnotperiodic, zerorwithheld.')
 final=next((z for z in out if z['dataset']=='414_final'),None);result=dict(stage=416,status=status,error=error,rows=len(out),datasets=groups,all_numeric_certificates_passed=error is None,recorded411_C_nominal_checks=len(normal_checks),recorded411_C_nominal_mismatches=sum(not z['passed'] for z in normal_checks),boundary_summary=bsummary,final414=final,synthetic_cases=len(synthetic),new_native_reset_model_actor_learning_SEALED_reserve_paid=0,actual_policy_changed=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,plan_sha256=sha(d/'plan.json'))
 save(d/'result.json',result);print(json.dumps(result))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
