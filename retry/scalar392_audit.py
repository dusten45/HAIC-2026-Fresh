"""Stored-row scalar-law audit only. No actor, env, transition or model imports."""
import datetime, hashlib, json, math, signal, subprocess, sys, time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read, save, sha
G=Path(__file__).resolve().parent.parent
COMMIT='3e584dff988f0b90fce3dd563b7f6351a13d21f8'
DOC='retry/static_control_audit_20261016.md'

def static_doc():
    return subprocess.run(['git','show',COMMIT+':'+DOC],cwd=G,check=True,capture_output=True).stdout

def prepare(root):
    d=root/'stage392';assert not d.exists();d.mkdir(mode=0o700)
    b=read(root/'project-effective-budget-v411.json');assert b['research_remaining']==34139 and b['final_reserved_actions']==84000 and b['final_reserve_used']==0
    p390=read(root/'stage390/plan.json');sources=[Path(__file__),G/'retry/loss389_analyze.py',G/'retry/pace265_run.py',G/'retry/pace268_run.py',G/'retry/pace269_run.py',root/'project-effective-budget-v411.json',root/'research-deadline-current.json',root/'stage390/plan.json']
    for key in ['O0','N1']:
        sources += [root/('stage390/A-'+key)/name for name in ['trace-private.json','fixed-geometry-private.json','result.json']]+[Path(p390['A_plans'][key])]
    p=dict(stage=392,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',cases=['O0','N1'],row_cap=506,rows_expected=dict(O0=247,N1=259),native_cap=0,actor_cap=0,model_integration_cap=0,learning_cap=0,CPU_cap_s=60,static_document=dict(commit=COMMIT,path=DOC,content_sha256=hashlib.sha256(static_doc()).hexdigest()),sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},formula='a_old=f+k*(r-v); a_alt=f*(sigma/r)+k*(r-v),r>0,k1.5. Sameoriginalr,f,v,clamps,pedalmap; no newcommand affects anylaterrow.',projection='Exhaustive Euclidean projection of actualpreposition onto all closedpolyline segments. Unique strictlyinterior minimizer required (exactequalityties withfloat64; no hiddenepsilon). sigma=velocity dot unit tangent of thatsegment:local derivative of projectedarc wherepieceisuniqueandinterior. No poststate/time difference used forinput; no Frenetcurvaturefactor becausepolylinepiecehaszero curvature,verticesundefined.',reference_alignment='Originalcontroller r/f remain at originalcursor. If nearestsegment differsfromcursorsegment, alternative isoperational same-path scalarformula butexactchainrule identityatonecommonarcisnotqualified; disclosecountsandstalledsubset. No reprojectednewtargets.',zero_r='Return no alternatecommand and explicitzero_target_unqualified. No sigma/r and no epsilon/fallbacklaunch/stoprule. Thusglobalruntimecandidatecannotbequalifiedifzerorrowsoccur.',reverse='Keep signedsigmawithoutmax/clipping. Algebraevaluatedifvalidprojection/r>0; sigma<0 flaggedreverse_unsupportedforforwardtracking. Also report meaningfulreverse sigma<-.1m/s (390descriptive cut,notnumericzero). No claimreversecontroller.',nodes_and_seams='Closedlast-to-firstsegment included; tie/endpointprojection unqualified,notzero-filled. Sigmauseslocaltangent withoutarcdifferencing; diag arc unwrap uses signedshortestperiodicdelta, exacthalflap ambiguous. Profilelapbranch changes (cursorindex//N) flaggedchainruleunqualified. Perroworiginalone-sidedfheldfixed; no interpolation/replanning.',cursor='Flag originalcursor vsnearestpiece mismatch; diagnosticcursorjump whenabs(delta cursorfraction - delta unwrapped nearestfraction)>2segments, sameprior390scale. Flag onbothsideofsuchtransition; do not infer sigma fromcursor delta.',tests='1stationaryalgebra: for eachstoredr>0,f, evaluate symbolicv=sigma=0 ->kr>0; notmodifiedactualstate ortrajectory. 2actualnearrest: pre.speed<.1m/s (390definition),originalbrake>0,r>0; qualifiedprojectionalt mustnotrequestbrake. 3sigma=r algebraidentitywithoriginalr/f/v exactfloat64 equality. 4normalbraking: movingv>=.1,r>0,sigma>0,validprojection,oldraw<0; at leastonealt negative. Overspeedv>r withf<=0/sigma>=0 allmustremainnegative. Noselectedbrakerows removedfromdenominator.',rejection='Any finite-input algebra NaN/Inf, sigma=r identityfailure, symbolicpositive-targetstationarynonpositive, or actualnearrest qualifiedprojection a_alt<0 ->positive-targetformulaFAIL. Allnormalbrakingremoved ->FAIL; no normalbraking support ->INCONCLUSIVE. Undefinedprojection/zero_r/reverse/cursorlapbreak do notbecome fabricatedcommands; count andwithholdruntimequalification. Endpoint safety/lap nottested.',numerical='No r=max(r,epsilon),speedrounding,sigmafloor,curvaturedenominatorfloor orcommandmask. r<0/nonfiniteinput fatal. Existingrecordreconstructioncontrolidentity tolerance abs1e-10 (verificationroundoff only,notzeror/sign/projectionrule).',resource_and_split='Onlyexisting390O0/N1 knownTRAIN. No372failure-detail/DEV/HOLDOUT/SEALEDlookup,wrapper,actor,modelintegration,learning,paidresource. Research34139/reserve84000unchanged. Firsttechnical/source/CPUfailure stopsanalysiswithoutredrawingconditions.')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),rows=506,native=0,actor=0,model_integration=0)),flush=True)

def project(line,pos,vel):
    line=np.asarray(line,float);pos=np.asarray(pos,float);vel=np.asarray(vel,float);edges=np.roll(line,-1,axis=0)-line;length=np.linalg.norm(edges,axis=1);assert np.all(length>0)
    u=np.clip(np.sum((pos-line)*edges,axis=1)/(length*length),0,1);feet=line+u[:,None]*edges;distance2=np.sum((pos-feet)**2,axis=1);ix=np.flatnonzero(distance2==distance2.min());j=int(ix[0]);arc=float(np.sum(length[:j])+u[j]*length[j]);fraction=j+float(u[j]);valid=len(ix)==1 and 0<u[j]<1
    return dict(index=j,u=float(u[j]),tie_count=len(ix),valid=bool(valid),reason=None if valid else 'projection_tie' if len(ix)>1 else 'projection_endpoint',sigma=float(vel@(edges[j]/length[j])) if valid else None,arc_m=arc,fraction=fraction,period=float(sum(length)))

def pedals(acc,speed,model):
    cmd=float(np.clip(acc,-model['brake_accel'],model['rear_traction_accel']));gas=float(np.clip(model['effective_mass']*max(cmd,0)*(speed+2.7)/80000,0,1));brake=float(np.clip(model['effective_mass']*max(-cmd,0)/(4*1.6*15/(.02*.54)),0,1));return dict(raw_accel=acc,command_accel=cmd,gas=gas,brake=brake)

def run(root):
    d=root/'stage392';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
    for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    assert hashlib.sha256(static_doc()).hexdigest()==p['static_document']['content_sha256'];save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start,cpu=time.perf_counter(),time.process_time();raw=[];cases=[];count=0;errors=[];limits=[]
    def timeout(signum,frame):raise TimeoutError('392 CPU60s')
    oldsignal=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    try:
        p390=read(root/'stage390/plan.json')
        for key in p['cases']:
            rows=read(root/('stage390/A-'+key)/'trace-private.json');assert len(rows)==p['rows_expected'][key];line=np.asarray(read(root/('stage390/A-'+key)/'fixed-geometry-private.json')['line']);model=read(Path(p390['A_plans'][key]))['model'];N=len(line);data=[];last=None
            for row in rows:
                assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc']) and time.process_time()-cpu<60
                count+=1;assert count<=506;c=row['control'];r=float(c['target_speed_m_s']);v=float(row['pre']['speed']);f=float(c['feedforward_accel']);feedback=1.5*(r-v);old=f+feedback;assert r>=0 and all(math.isfinite(q) for q in [r,v,f,old]);assert abs(feedback-c['feedback_accel'])<=1e-10;original=pedals(old,v,model)
                assert np.array_equal(np.asarray([c['action'][1],c['action'][2]],np.float32),np.asarray([original['gas'],original['brake']],np.float32))
                q=project(line,row['pre']['pos'],row['pre']['vel']);period=int(c['cursor_index'])//N;branchchange=last is not None and period!=last['period'];jump=False
                if last is not None:
                    delta=(q['fraction']-last['fraction']+N/2)%N-N/2
                    ambiguous_half=abs(delta)==N/2
                    jump=ambiguous_half or abs((c['cursor_fraction']-last['cursor'])-delta)>2
                    if jump:data[-1]['cursor_jump_flag']=True
                aligned=q['index']==int(c['cursor_index'])%N and 0<(c['cursor_fraction']-c['cursor_index'])<1
                alt=None;reason=None;identity=True;stationary=True
                if r==0:reason='zero_target_unqualified'
                else:
                    identity=(f*(r/r)+feedback)==old;stationary=1.5*r>0
                    if not identity:errors.append(dict(case=key,step=row['step'],kind='sigma_equals_r_identity'))
                    if not stationary:errors.append(dict(case=key,step=row['step'],kind='stationary_symbolic'))
                    if not q['valid']:reason=q['reason']
                    else:
                        acc=f*(q['sigma']/r)+feedback
                        if not math.isfinite(acc):raise ArithmeticError('Nonfinitealternate')
                        alt=pedals(acc,v,model)
                        if v<.1 and c['action'][2]>0 and alt['raw_accel']<0:errors.append(dict(case=key,step=row['step'],kind='actual_nearrest_still_braking'))
                z=dict(case=key,step=row['step'],r=r,v=v,f=f,feedback=feedback,original=original,projection=q,reference_aligned=bool(aligned),profile_branch_change=branchchange,cursor_jump_flag=bool(jump),alternate=alt,withheld_reason=reason,reverse=bool(q['valid'] and q['sigma']<0),meaningful_reverse=bool(q['valid'] and q['sigma']<-.1),identity_passed=identity,symbolic_stationary_passed=stationary)
                data.append(z);last=dict(period=period,fraction=q['fraction'],cursor=c['cursor_fraction'])
            for z in data:z['forward_chainrule_qualified']=bool(z['alternate'] is not None and z['reference_aligned'] and not z['profile_branch_change'] and not z['cursor_jump_flag'] and not z['reverse'])
            positive=[z for z in data if z['r']>0];valid=[z for z in data if z['alternate'] is not None];rest=[z for z in valid if z['v']<.1 and z['original']['brake']>0];normal=[z for z in valid if z['v']>=.1 and z['projection']['sigma']>0 and z['original']['raw_accel']<0];overspeed=[z for z in valid if z['v']>z['r'] and z['f']<=0 and z['projection']['sigma']>=0];retained=sum(z['alternate']['raw_accel']<0 for z in normal)
            if normal and not retained:errors.append(dict(case=key,kind='all_normal_braking_removed'))
            if any(z['alternate']['raw_accel']>=0 for z in overspeed):errors.append(dict(case=key,kind='overspeed_nonpositive_feed_braking_removed'))
            cases.append(dict(case=key,rows=len(data),positive_target_rows=len(positive),zero_target_rows=sum(z['r']==0 for z in data),alternate_defined_rows=len(valid),projection_undefined_rows=sum(not z['projection']['valid'] for z in data),withheld_reasons={reason:sum(z['withheld_reason']==reason for z in data) for reason in sorted(set(z['withheld_reason'] for z in data if z['withheld_reason']))},reference_aligned_rows=sum(z['reference_aligned'] for z in data),reference_misaligned_rows=sum(not z['reference_aligned'] for z in data),reverse_sigma_rows=sum(z['reverse'] for z in data),meaningful_reverse_sigma_rows=sum(z['meaningful_reverse'] for z in data),profile_branch_changes=sum(z['profile_branch_change'] for z in data),cursor_jump_flag_rows=sum(z['cursor_jump_flag'] for z in data),forward_chainrule_qualified_rows=sum(z['forward_chainrule_qualified'] for z in data),symbolic_stationary_tests=len(positive),sigma_equals_r_tests=len(positive),nearrest_original_braking_rows=len(rest),nearrest_new_braking_rows=sum(z['alternate']['raw_accel']<0 for z in rest),nearrest_reference_aligned_rows=sum(z['reference_aligned'] for z in rest),nearrest_alt_raw_range=[min((z['alternate']['raw_accel'] for z in rest),default=None),max((z['alternate']['raw_accel'] for z in rest),default=None)],moving_original_braking_rows=len(normal),moving_braking_retained_rows=retained,overspeed_nonpositive_feed_rows=len(overspeed),overspeed_nonpositive_feed_retained=sum(z['alternate']['raw_accel']<0 for z in overspeed),original_brake_removed_rows=sum(z['original']['brake']>0 and z['alternate']['brake']==0 for z in valid),original_gas_to_brake_rows=sum(z['original']['gas']>0 and z['alternate']['brake']>0 for z in valid),max_abs_sigma_over_r=max((abs(z['projection']['sigma']/z['r']) for z in valid),default=None),minimum_positive_target=min((z['r'] for z in positive),default=None),normal_braking_support=bool(normal)))
            raw+=data
        status='POSITIVE_TARGET_FORMULA_FAILED' if errors else 'POSITIVE_TARGET_FORMULA_PASS_RUNTIME_UNQUALIFIED' if all(c['normal_braking_support'] for c in cases) else 'INCONCLUSIVE_BRAKING_SUPPORT'
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsignal)
    save(d/'row-evaluations-private.json',raw)
    result=dict(stage=392,status=status,cases=cases,errors=errors,rows_evaluated=count,new_wrapper_actions=0,new_actor_calls=0,new_model_integration_ticks=0,new_environment_resets=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,resource_cap=dict(rows=506,CPU_s=60,native=0,actor=0,model_integration=0),source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()),scope='Independentstoredstatecommands only; no rollout,performance,safety,legalpixelinput orfullruntimelaunch qualification')
    save(d/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    elif sys.argv[2]=='run':run(root)
    else:raise ValueError(sys.argv[2])
