"""Stored-only COM/origin reference-point audit; preserves existing C semantics."""
import datetime,json,math,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.executor397 import canonical_projection
from retry.scalar392_audit import pedals
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage416';assert not(d/'point-plan.json').exists();p=read(d/'plan.json');a=read(d/'completion-result.json');files=[Path(__file__),G/'retry/loss389_replay.py',G/'retry/executor397.py',d/'completion-result.json',root/'stage269/N1-plan-private.json',root/'stage404/profiles-private.json']+[root/'stage413'/k/'trace-private.jsonl' for k in ['actual_A','actual_B']]+[root/'stage414/trace-private.jsonl']
 q=dict(stage=416,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=p['deadline_utc'],scope='Originpositionisprojected buthull.linearVelocityisCOMvelocity. Forcurrent C preserveCOMsigmasemantics. Trueorigin ds/dt usesv_origin=v_COM-omega J(Rc_local). Auditall stored413A/B414rawhulls, no controller/future/model. Treatcurrentchainrulejustificationasconditionalonmatchedpoint, notexactforCOMinput. No currentlawchange.',CPU_remaining_s=60-a['total_static_CPU_s'],wall_remaining_s=120-a['total_static_wall_s'],sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve'])
 save(d/'point-plan.json',q);(d/'point-plan.sha256').write_text(sha(d/'point-plan.json')+'\n');print('point audit frozen',sha(d/'point-plan.json'))
def run(root):
 d=root/'stage416';p=read(d/'point-plan.json');assert sha(d/'point-plan.json')==(d/'point-plan.sha256').read_text().strip();assert not(d/'point-opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 cpu=time.process_time();wall=time.perf_counter();save(d/'point-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));fixed=read(root/'stage269/N1-plan-private.json');line=np.asarray(fixed['line']);nodes=np.asarray(fixed['free_profile']['speed'])*np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);rows=[];error=None
 def timeout(*a):raise TimeoutError('416remaining_static_cap')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,p['CPU_remaining_s']);signal.setitimer(signal.ITIMER_REAL,p['wall_remaining_s'])
 try:
  for tag,file in [('413A',root/'stage413/actual_A/trace-private.jsonl'),('413B',root/'stage413/actual_B/trace-private.jsonl'),('414',root/'stage414/trace-private.jsonl')]:
   with file.open() as stream:
    for text in stream:
     z=json.loads(text)
     for h in z['raw_hull']:
      c=np.asarray(h['COM_local']);angle=h['angle'];rotation=np.asarray([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);lever=rotation@c;pred=np.asarray(h['COM_linear_velocity'])-h['yaw']*np.asarray([-lever[1],lever[0]]);origin=np.asarray(h['origin_linear_velocity']);com=np.asarray(h['COM_linear_velocity']);q=canonical_projection(line,h['origin_position'],com,'FIRST_LAP');i=q['index'];u=q['u'];t=(line[(i+1)%len(line)]-line[i]);t=t/np.linalg.norm(t);sO=float(origin@t);sC=q['sigma'];r=float(np.sqrt((1-u)*nodes[i]**2+u*nodes[i+1]**2));f=float((nodes[i+1]**2-nodes[i]**2)/(2*fixed['free_profile']['ds'][i]));v=float(np.linalg.norm(com));rawC=f*(sC/r)+1.5*(r-v) if r>0 else None;rawO=f*(sO/r)+1.5*(r-v) if r>0 else None;cmdC=pedals(rawC,v,fixed['model']) if r>0 else None;cmdO=pedals(rawO,v,fixed['model']) if r>0 else None
      rows.append(dict(dataset=tag,step=z['step'],time=h['time'],COM_local=h['COM_local'],yaw=h['yaw'],sigma_COM=sC,sigma_origin=sO,sigma_difference=sC-sO,kinematic_identity_speed_error_m_s=float(np.linalg.norm(pred-origin)),rotation_speed_bound=abs(h['yaw'])*float(np.linalg.norm(c)),raw_C_COM=rawC,raw_origin_point_only=rawO,raw_difference=None if r<=0 else rawC-rawO,raw_f_over_r_difference=None if r<=0 else f/r*(sC-sO),pedal_difference=None if r<=0 else max(abs(cmdC['gas']-cmdO['gas']),abs(cmdC['brake']-cmdO['brake'])),origin_point_guard_backward=sO<-.1,existing_COM_guard_backward=sC<-.1))
  status='STORED_POINT_MISMATCH_QUANTIFIED_NO_FORMULA_CHANGE'
 except Exception as e:status='POINT_AUDIT_STOP';error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for sig,h in old.items():signal.signal(sig,h)
 save(d/'point-rows-private.json',rows)
 result=dict(stage=416,status=status,error=error,raw_samples=len(rows),datasets={tag:dict(rows=len([z for z in rows if z['dataset']==tag]),max_abs_sigma_COM_minus_origin=max(abs(z['sigma_difference']) for z in rows if z['dataset']==tag),max_abs_raw_point_effect=max(abs(z['raw_difference']) for z in rows if z['dataset']==tag and z['raw_difference'] is not None),max_pedal_point_effect=max(z['pedal_difference'] for z in rows if z['dataset']==tag and z['pedal_difference'] is not None)) for tag in sorted(set(z['dataset'] for z in rows))},local_COM_values=[list(x) for x in sorted(set(tuple(z['COM_local']) for z in rows))],max_kinematic_identity_error_m_s=max(z['kinematic_identity_speed_error_m_s'] for z in rows),max_abs_sigma_difference=max(abs(z['sigma_difference']) for z in rows),max_point_effect_raw_difference=max(abs(z['raw_difference']) for z in rows if z['raw_difference'] is not None),max_point_effect_pedal_difference=max(z['pedal_difference'] for z in rows if z['pedal_difference'] is not None),guard_backward_classification_differences=sum(z['origin_point_guard_backward']!=z['existing_COM_guard_backward'] for z in rows),scope='Algebraic inputpointcomparison onstoredrawstates; no changedcontroller/no newtrajectory. KinematicidentityerrorreflectsBox2Dfloat32returnedpointvelocityvsfloat64trig, notderiveepsilon. CurrentCgamma/DecimalcertificatesapplyCOMformulaonly; trueoriginchainruleusesoriginvelocity.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_native_model_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'point-plan.json'))
 save(d/'point-result.json',result);print(json.dumps(result))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
