"""Independent same-foot target/gradient/progress comparison; no state propagation."""
import datetime,json,math,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.scalar392_audit import project,pedals
G=Path(__file__).resolve().parent.parent

def subjects(root):
    old=read(root/'stage392/row-evaluations-private.json')
    return [dict(case=z['case'],step=z['step']) for z in old if z['alternate'] is not None and z['v']>=.1 and z['projection']['sigma']>0 and z['original']['raw_accel']<0 and z['alternate']['raw_accel']>=0]

def prepare(root):
    d=root/'stage393';assert not d.exists();d.mkdir(mode=0o700);p390=read(root/'stage390/plan.json');v=read(root/'project-effective-budget-v412.json');assert v['research_remaining']==34139 and v['final_reserved_actions']==84000
    sources=[Path(__file__),G/'retry/scalar392_audit.py',G/'retry/loss389_analyze.py',G/'retry/pace265_run.py',G/'retry/racing258_plan.py',root/'stage390/plan.json',root/'stage392/row-evaluations-private.json',root/'stage392/plan.json',root/'stage392/result.json',root/'project-effective-budget-v412.json',root/'research-deadline-current.json']
    for k in ['O0','N1']:sources += [root/('stage390/A-'+k)/x for x in ['trace-private.json','fixed-geometry-private.json','result.json']]+[Path(p390['A_plans'][k])]
    seven=subjects(root);assert len(seven)==7
    p=dict(stage=393,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',cases=['O0','N1'],rows=dict(O0=247,N1=259),row_cap=506,CPU_cap_s=60,new_wrapper_cap=0,new_actor_cap=0,new_model_integration_cap=0,new_learning_cap=0,new_SEALED_queries_cap=0,seven_lost_braking_subjects=seven,nearrest_subjects='Same392actualspeed<.1 andoriginalbrake>0,r>0:99N1rows; noresampling',variants=dict(O='originalcursorf+1.5*(r-v)',H='392oldcursorf*(sigma/r)+1.5*(r-v)',P='sameactualfoot f_new+1.5*(r_new-v)',C='sameactualfoot f_new*(sigma/r_new)+1.5*(r_new-v)'),same_foot='392uniqueinteriorclosedpolyline nearestprojection. Frozenoriginal speednodes ofthatrow branch, interpolationw=(1-u)*v_i²+u*v_i+1²,r=sqrt(w),f=(v_i+1²-v_i²)/(2ds_i); sigma=actualvelocity dotsegment unit tangent. Nointerpolation/smoothing/profileoptimization beyondoriginalsquaredspeedrule; unchangedclamp/pedalmapping.',lap_domain='Originalprofilev0=0,unrestrictedvN isnotperiodic. Unwrapactualnearestarc bysignedshortestperiodicchange, initialgauge nearestoriginalcursorarc. Originalindex<N branchqualifiedonly0<=actualunwrappedarc<=L; originalindex>=N branchqualifiedonlyactualunwrappedarc>=L. Withholdiforiginalbranchswitchesbeforeactuallap; noepsilon/extrapolation/seamclipping. Usecurrentroworiginalbranchforbothprofilevariants; nofuturestate.',zero_and_reverse='Invalid/multiple/endpointprojection orr_new==0 ->noCcommand; explicitzero_target_unqualified. Noepsilon/imaginedlaunchrule. Signed sigma preserved, negativeflaggedoutsideforwarddomain; report meaningfulnegative<-.1 (prior390descriptive).',cause_analysis='Reconstructoldnearestnodecandidate [max(0,previndex-2),previndex+18), index=max(previndex,nearestnode),thenboundedprojectionu. Compareeveryrowindex/u/r/f tostored. Nearrestclassify adjacent-ahead nearestnode/u0 vs monotonehold vs other; reportactualarc/footseparation andprofilevalues. Boundaryroundoff only diagnostic iffootseparation <= onefloat32coordinateULP L2+64float64eps*coordinatescale; noformula/inputchangedbythistolerance.',checks='506oldcontrols reproduce;505Hresults reproduce392. Samefoot sigma=r mustexactlyequalP. Symbolicrest r_new>0 ->1.5r_new>0. Eachactualnearrest99musthavevalidC andCraw>=0; anyfailureblockspositive-targetqualification. Normaloriginalmovingbrake93denominator retainedincludingwithheld; at leastonenegativeCpercase. Overspeedcoherentr_new<v,f_new<=0,sigma>=0 mustbrake. Missingdomain/branch/zero/reverse meanspartialdomainonly,no fullruntimeclaim.',rejection='Any nonfinite orsource/reconstruction mismatch, identityfailure,actualnearrestnegativeC,allnormalbrakingremoved ->FAIL. No normalbrake support ->INCONCLUSIVE. Sevenrowinput/controltermsallreportedevenifunchanged. Firsttechnical/CPU/deadlinefailure stopwithoutnewconditions.',next_actual_design='Proposalonlyafterresults; no newactualrun/model permittedin393. PreferonefixedknownTRAINpre-nearreststate fourstaticvariants forks toseparateprojection/formula; freezefutureprefixcost/gatesbeforeexecution.',sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},resource='Research34139/reserve84000unchanged;newpaid0;no372details/DEV/HOLDOUT/SEALED read',provenance='Parentoriginalplan/methodrereadrelayed; consumerdirectfullreadnotclaimed')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),rows=506,lost_braking_subjects=seven,new_native=0,new_model=0)),flush=True)

def runtime_nodes(fixed,index):
    nodes=np.array(fixed['free_profile']['speed'],float)
    if index>=len(fixed['line']):nodes=np.minimum(100.,np.sqrt(fixed['model']['lateral_accel']/np.maximum(abs(np.r_[fixed['free_profile']['curvature'],fixed['free_profile']['curvature'][0]]),1e-6)))
    return nodes*1.5

def rf(nodes,ds,j,u):
    w=(1-u)*nodes[j]**2+u*nodes[j+1]**2;assert w>=0 and ds[j]>0
    return float(np.sqrt(w)),float((nodes[j+1]**2-nodes[j]**2)/(2*ds[j]))

def run(root):
    d=root/'stage393';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
    for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));start,cpu=time.perf_counter(),time.process_time();raw=[];summaries=[];errors=[];count=0
    def timeout(signum,frame):raise TimeoutError('393 CPU60s')
    prevsig=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    try:
        p390=read(root/'stage390/plan.json');prior={(z['case'],z['step']):z for z in read(root/'stage392/row-evaluations-private.json')}
        for case in p['cases']:
            rows=read(root/('stage390/A-'+case)/'trace-private.json');fixed=read(Path(p390['A_plans'][case]));line=np.array(fixed['line']);edges=np.roll(line,-1,axis=0)-line;ds=np.array(fixed['free_profile']['ds']);assert np.all(ds>0);sarc=np.r_[0,np.cumsum(ds)];L=float(sarc[-1]);N=len(line);model=fixed['model'];last_index=0;last_arc=None;unwrapped=None;out=[]
            for row in rows:
                assert time.process_time()-cpu<60 and datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc']);count+=1;assert count<=506
                c=row['control'];pos=np.array(row['pre']['pos']);velocity=np.array(row['pre']['vel']);v=row['pre']['speed'];q=project(line,pos,velocity);old=prior[case,row['step']]
                cand=np.arange(max(0,last_index-2),last_index+18);nearestnode=int(cand[np.argmin(np.linalg.norm(line[cand%N]-pos,axis=1))]);index=max(last_index,nearestnode);j=index%N;edge=edges[j];u=float(np.clip((pos-line[j])@edge/(edge@edge),0,1));nodes=runtime_nodes(fixed,index);r,f=rf(nodes,ds,j,u)
                assert index==c['cursor_index'] and abs((index+u)-c['cursor_fraction'])<=1e-10 and abs(r-c['target_speed_m_s'])<=1e-9 and abs(f-c['feedforward_accel'])<=1e-9
                O=pedals(f+1.5*(r-v),v,model);assert np.array_equal(np.array([O['gas'],O['brake']],np.float32),np.array(c['action'][1:],np.float32))
                H=None
                if q['valid'] and r>0:
                    H=pedals(f*(q['sigma']/r)+1.5*(r-v),v,model);assert old['alternate'] is not None and abs(H['raw_accel']-old['alternate']['raw_accel'])<=1e-9
                else:assert old['alternate'] is None
                if last_arc is None:unwrapped=q['arc_m']+round((c['cursor_arc_m']-q['arc_m'])/L)*L
                else:unwrapped+=(q['arc_m']-last_arc+L/2)%L-L/2
                last_arc=q['arc_m'];foot=line[q['index']]+q['u']*edges[q['index']];oldfoot=line[j]+u*edge;footgap=float(np.linalg.norm(oldfoot-foot));arcgap=(c['cursor_arc_m']-q['arc_m']+L/2)%L-L/2
                quant=float(np.linalg.norm(np.spacing(pos.astype(np.float32)).astype(float)))+64*np.finfo(float).eps*max(float(np.linalg.norm(pos)),float(np.linalg.norm(oldfoot)),1.)
                if footgap<=quant:cause='within_one_position_ULP_or_same_foot'
                elif index>nearestnode:cause='monotone_cursor_hold'
                elif (q['index']+1)%N==j and u==0:cause='nearest_node_ahead_clamped_to_start'
                else:cause='other_projection_difference'
                C=P=None;rn=fn=None;why=None;identity=None;expected_startbranch=index<N
                if not q['valid']:why=q['reason']
                elif expected_startbranch and not 0<=unwrapped<=L:why='outside_standingstart_arc_domain'
                elif not expected_startbranch and unwrapped<L:why='profile_branch_before_actual_lap'
                else:
                    rn,fn=rf(nodes,ds,q['index'],q['u']);P=pedals(fn+1.5*(rn-v),v,model)
                    if rn==0:why='zero_target_unqualified'
                    else:
                        C=pedals(fn*(q['sigma']/rn)+1.5*(rn-v),v,model);identity=(fn*(rn/rn)+1.5*(rn-v))==P['raw_accel']
                        assert all(math.isfinite(a) for a in [rn,fn,C['raw_accel']])
                        if not identity:errors.append(dict(case=case,step=row['step'],kind='samefoot_identity'))
                        if 1.5*rn<=0:errors.append(dict(case=case,step=row['step'],kind='samefoot_stationary_symbolic'))
                        if v<.1 and O['brake']>0 and C['raw_accel']<0:errors.append(dict(case=case,step=row['step'],kind='actual_nearrest_negativeC'))
                z=dict(case=case,step=row['step'],v=v,sigma=q['sigma'],r_cursor=r,f_cursor=f,r_foot=rn,f_foot=fn,O=O,H=H,P=P,C=C,withheld=why,nearest_node_index=nearestnode,cursor_index=index,projection_index=q['index'],cursor_u=u,projection_u=q['u'],arc_gap_m=float(arcgap),foot_gap_m=footgap,position_ULP_bound_m=quant,cause=cause,monotone_hold=index>nearestnode,projection_valid=q['valid'],unwrapped_arc_m=unwrapped,firstlap_branch=expected_startbranch,identity_passed=identity,nearrest_original_brake=bool(v<.1 and O['brake']>0),meaningful_reverse=bool(q['valid'] and q['sigma']<-.1),reverse=bool(q['valid'] and q['sigma']<0))
                out.append(z);last_index=index
            rest=[z for z in out if z['nearrest_original_brake']];normal=[z for z in out if z['H'] is not None and z['v']>=.1 and z['sigma']>0 and z['O']['raw_accel']<0];defined=[z for z in out if z['C'] is not None];retained=[z for z in normal if z['C'] is not None and z['C']['raw_accel']<0];overspeed=[z for z in defined if z['v']>z['r_foot'] and z['f_foot']<=0 and z['sigma']>=0]
            if any(z['C'] is None for z in rest):errors.append(dict(case=case,kind='nearrest_domain_unqualified'))
            if normal and not retained:errors.append(dict(case=case,kind='all_normal_braking_removed'))
            if any(z['C']['raw_accel']>=0 for z in overspeed):errors.append(dict(case=case,kind='coherent_overspeed_nonpositivefeed_no_brake'))
            def extent(zs,key):return [min((z[key] for z in zs),default=None),max((z[key] for z in zs),default=None)]
            summaries.append(dict(case=case,rows=len(out),C_defined=len(defined),withheld_reasons={k:sum(z['withheld']==k for z in out) for k in sorted(set(z['withheld'] for z in out if z['withheld']))},samefoot_identity_tests=sum(z['identity_passed'] is not None for z in out),samefoot_identity_failures=sum(z['identity_passed'] is False for z in out),nearrest_rows=len(rest),nearrest_C_defined=sum(z['C'] is not None for z in rest),nearrest_C_braking=sum(z['C'] is not None and z['C']['brake']>0 for z in rest),nearrest_causes={k:sum(z['cause']==k for z in rest) for k in sorted(set(z['cause'] for z in rest))},nearrest_monotone_holds=sum(z['monotone_hold'] for z in rest),nearrest_foot_gap_m=extent(rest,'foot_gap_m'),nearrest_arc_gap_m=extent(rest,'arc_gap_m'),nearrest_position_ULP_bound_m=extent(rest,'position_ULP_bound_m'),nearrest_original_r=extent(rest,'r_cursor'),nearrest_coherent_r=extent(rest,'r_foot'),nearrest_original_f=extent(rest,'f_cursor'),nearrest_coherent_f=extent(rest,'f_foot'),nearrest_raw_O=extent([dict(z,raw=z['O']['raw_accel']) for z in rest],'raw'),nearrest_raw_H=extent([dict(z,raw=z['H']['raw_accel']) for z in rest if z['H'] is not None],'raw'),nearrest_raw_P=extent([dict(z,raw=z['P']['raw_accel']) for z in rest if z['P'] is not None],'raw'),nearrest_raw_C=extent([dict(z,raw=z['C']['raw_accel']) for z in rest if z['C'] is not None],'raw'),normal_original_braking_rows=len(normal),normal_C_withheld=sum(z['C'] is None for z in normal),normal_C_braking_retained=len(retained),coherent_overspeed_nonpositivefeed=len(overspeed),coherent_overspeed_braking=sum(z['C']['raw_accel']<0 for z in overspeed),reverse_C_rows=sum(z['reverse'] for z in defined),meaningful_reverse_rows=sum(z['meaningful_reverse'] for z in out),min_positive_coherent_r=min((z['r_foot'] for z in defined),default=None)))
            raw+=out
        seven=[]
        for item in p['seven_lost_braking_subjects']:
            z=next(z for z in raw if z['case']==item['case'] and z['step']==item['step']);seven.append({k:z[k] for k in ['case','step','v','sigma','r_cursor','f_cursor','r_foot','f_foot','O','H','P','C','withheld','cause','arc_gap_m','foot_gap_m']})
        result=dict(stage=393,status='SAME_FOOT_POSITIVE_TARGET_PASS_RUNTIME_BOUNDARIES_UNQUALIFIED' if not errors else 'FORMULA_OR_DOMAIN_GATE_FAILED',cases=summaries,seven_lost_braking=seven,errors=errors,rows_evaluated=count,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()),scope='Frozenpath/profile/prestates;fouralgebraicvariants independent;notactualmotion orlaunch/seam/generalization qualification')
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,prevsig)
    save(d/'row-evaluations-private.json',raw);save(d/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    elif sys.argv[2]=='run':run(root)
    else:raise ValueError(sys.argv[2])
