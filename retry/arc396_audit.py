"""Stored395 time-versus-arc observations only; no state/model/control propagation."""
import datetime,math,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parent.parent

def prepare(root):
    d=root/'stage396';assert not d.exists();d.mkdir(mode=0o700);b=read(root/'project-effective-budget-v415.json');assert b['research_remaining']==32346 and b['final_reserved_actions']==84000
    p395=read(root/'stage395/plan.json');sources=[Path(__file__),G/'retry/loss389_analyze.py',G/'retry/window395_run.py',root/'stage395/plan.json',root/'stage395/analysis.json',root/'project-effective-budget-v415.json',root/'research-deadline-current.json']
    for key in ['N1','O0']:
        sources.append(Path(p395['fixed_plans'][key]))
        for arm in ['O','C']:sources += [root/('stage395/'+key+'-'+arm)/name for name in ['window-private.json','result.json']]
    p=dict(stage=396,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',cases=['N1','O0'],rows=48,CPU_cap_s=60,new_wrapper_cap=0,new_actor_cap=0,new_model_integration_cap=0,new_learning_cap=0,new_SEALED_cap=0,elapsed_comparison='Samewindowaction1..12 is sameelapsedtime,.08s intervals; ownpositions/states differ. Fullwindowcounts395 reproductiononly.',common_arc='Common signedactualprojectedprogress [0,min(endO,endC)],requiremonotone pre/postprogresswithin recordedprecision. ThresholdsO0 exactly5,10,...50m,all10 kept; thresholdoutsidecommon ->unsupported,no extrapolation. N1same5..50thresholds expectedunsupported ifOstationary; do notmanufacturemovingcontrols.',crossing='Firstactualinterval withpreprogress<threshold<=postprogress. Record[pre_time,post_time],actualendpointv/signedlateralerror/brake/frontclip andprofilecurvatures; no interpolatedstate,exactcrossingtime orpoint-safetyclaim. TimeCminusO interval=[Clo-Ohi,Chi-Olo]; disjointifupper<0 orlower>0,otherwiseunresolved. Repeatedintervalsmaycovermultiplethresholds; never sumduplicatedclipsacrossthresholds.',curvature='Frozenfree_profile curvature_i from258s3pointgeometry (notpolylineinsidepiecesFrenetcurvature); atcommonarc lookup right-sidedsegmentk_i,staticroadturn descriptor. Atobservedpre/post lookup ownclosestsegment; v²absk asgeometricdemandproxyonly,notactualforce/acceleration orfrictioncertificate.',cooccurrence='AllO0 actionintervals withanyactualfrontwheelclip>1 listedwithactualendpointvelocity,ownpre/postarc,k,requestbrake/actualbrake,lateralerror/yaw/steering/slip andclipcount/ratio. Compareclip vsnonclip rangeswithinarmdescriptively,nop-values/regression/causalattribution.',common_counts='Forcommon-domain eventcounts useonlywholeactionintervals fullyinsidecommonrange. Reportboundarystraddlingandoutsideintervals andtheireventcountsseparately,no fractional allocation ofrawclips whenrawhullpositionnotstored. Commonarcpointbrackets areobservedcontexts,notmatchedphysicalstates.',limits='No firstpassage/curvature extrapolation beyondcommonarc, no brakingdistance reserve estimate withoutvalidateddeceleration/actuator/tireandfuturetrajectorymodel. .96srecoverynotlaporlongtermsafety. Forwardvelocitybracketsareendpointobservationsnotcontinuousbound.',validation='48windowsreproduce395frontclip3/9andprogressgain,all10O0crossings supported orreportmissing;definition/monotonicity/source/finite/CPU/deadlineerror stopswithoutchanginggrid. Nocandidatepromotion orconditionselection.',sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},resource='Nativebudget32346/reserve84000unchanged;no newstate/actor/model/fit/SEALED/paidresource')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(__import__('json').dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),row_cap=48,thresholds_m=list(range(5,51,5)),native=0,model=0)),flush=True)

def run(root):
    d=root/'stage396';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
    for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));start,cpu=time.perf_counter(),time.process_time();cases=[];private=[];count=0
    def timeout(signum,frame):raise TimeoutError('396CPU60s')
    oldsignal=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    try:
        p395=read(root/'stage395/plan.json')
        for key in p['cases']:
            fixed=read(Path(p395['fixed_plans'][key]));line=np.asarray(fixed['line']);edges=np.roll(line,-1,axis=0)-line;length=np.linalg.norm(edges,axis=1);sarc=np.r_[0,np.cumsum(length)];curve=np.asarray(fixed['free_profile']['curvature']);L=sarc[-1];arms={};origins={}
            def curvature_at(arc):
                q=arc%L;j=min(len(line)-1,int(np.searchsorted(sarc,q,side='right')-1));return float(curve[j])
            for arm in ['O','C']:
                w=read(root/('stage395/'+key+'-'+arm)/'window-private.json');assert len(w)==12;origin=float(w[0]['pre_arc_unwrapped_m']);origins[arm]=origin;time0=w[0]['pre']['time'];rows=[]
                for i,z in enumerate(w):
                    assert time.process_time()-cpu<60 and datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc']);count+=1;assert count<=48
                    a=z['pre_arc_unwrapped_m']-origin;b=z['post_arc_unwrapped_m']-origin;assert a>=0 and b>=a and (i==0 or a==rows[-1]['arc_interval_m'][1])
                    endpoint=[]
                    for phase,spatial_key in [('pre','pre_spatial'),('post','post_spatial')]:
                        state=z[phase];sp=z[spatial_key];j=sp['index'];tangent=edges[j]/length[j];foot=line[j]+sp['u']*edges[j];delta=np.asarray(state['pos'])-foot;ey=float(tangent[0]*delta[1]-tangent[1]*delta[0]);k=float(curve[j])
                        endpoint.append(dict(v_m_s=state['speed'],sigma_m_s=sp['sigma'],signed_lateral_error_m=ey,abs_path_error_m=sp['path_error_m'],yaw_rate_rad_s=state['yaw'],curvature_m_inv=k,geometric_v2_abs_k_m_s2=state['speed']**2*abs(k)))
                    samples=[s for s in z['raw_tire_samples'] if s['wheel']<2];frontclip=sum(s['clipped'] for s in samples);rows.append(dict(window_action=i+1,actual_step=z['step'],elapsed_interval_s=[z['pre']['time']-time0,z['post']['time']-time0],arc_interval_m=[a,b],pre=endpoint[0],post=endpoint[1],requested_gas=z['command'][1],requested_brake=z['command'][2],requested_steer_rad=z['command'][0],front_clipped_ticks=frontclip,front_wheel_ticks=len(samples),front_max_force_ratio=max(s['force_ratio'] for s in samples),front_max_abs_lateral_slip_m_s=max(abs(s['lateral_slip_m_s']) for s in samples),front_actual_brake_range=[min(s['brake'] for s in samples),max(s['brake'] for s in samples)]))
                arms[arm]=rows;private.append(dict(case=key,arm=arm,observations=rows))
            assert origins['O']==origins['C'];common=float(min(arms['O'][-1]['arc_interval_m'][1],arms['C'][-1]['arc_interval_m'][1]));thresholds=[]
            for target in range(5,51,5):
                if target>common:thresholds.append(dict(arc_m=target,supported=False,reason='outside_common_arc'));continue
                pair={}
                for arm in ['O','C']:
                    row=next((z for z in arms[arm] if z['arc_interval_m'][0]<target<=z['arc_interval_m'][1]),None);assert row is not None;pair[arm]=row
                lo=pair['C']['elapsed_interval_s'][0]-pair['O']['elapsed_interval_s'][1];hi=pair['C']['elapsed_interval_s'][1]-pair['O']['elapsed_interval_s'][0]
                thresholds.append(dict(arc_m=target,supported=True,common_profile_curvature_m_inv=curvature_at(origins['O']+target),O=pair['O'],C=pair['C'],CminusO_time_interval_s=[lo,hi],timing='C_earlier_resolved' if hi<0 else 'O_earlier_resolved' if lo>0 else 'overlap_or_touch_unresolved'))
            summaries={};events=[]
            for arm,rows in arms.items():
                groups={tag:[] for tag in ['fully_common','straddles_common_end','outside_common']}
                for z in rows:
                    tag='fully_common' if z['arc_interval_m'][1]<=common else 'straddles_common_end' if z['arc_interval_m'][0]<common else 'outside_common';groups[tag].append(z)
                    if key=='O0' and z['front_clipped_ticks']:events.append(dict(arm=arm,common_domain_category=tag,**z))
                def summary(zs):
                    def extent(values):return [min(values),max(values)] if values else [None,None]
                    return dict(actions=len(zs),front_clipped_ticks=sum(z['front_clipped_ticks'] for z in zs),front_wheel_ticks=sum(z['front_wheel_ticks'] for z in zs),speed_endpoint_range_m_s=extent([z[ph]['v_m_s'] for z in zs for ph in ['pre','post']]),abs_curvature_endpoint_range_m_inv=extent([abs(z[ph]['curvature_m_inv']) for z in zs for ph in ['pre','post']]),brake_request_range=extent([z['requested_brake'] for z in zs]),abs_lateral_error_endpoint_range_m=extent([abs(z[ph]['signed_lateral_error_m']) for z in zs for ph in ['pre','post']]),max_force_ratio=max((z['front_max_force_ratio'] for z in zs),default=None))
                summaries[arm]=dict(full_window=summary(rows),common_domain_groups={tag:summary(zs) for tag,zs in groups.items()},clipped_actions=summary([z for z in rows if z['front_clipped_ticks']]),nonclipped_actions=summary([z for z in rows if not z['front_clipped_ticks']]),first_positive_brake=next((z for z in rows if z['requested_brake']>0),None),first_brake_over05=next((z for z in rows if z['requested_brake']>.05),None),first_front_clip=next((z for z in rows if z['front_clipped_ticks']),None))
            elapsed=[dict(window_action=i+1,O_arc_m=arms['O'][i]['arc_interval_m'],C_arc_m=arms['C'][i]['arc_interval_m'],O_speed_end_m_s=arms['O'][i]['post']['v_m_s'],C_speed_end_m_s=arms['C'][i]['post']['v_m_s'],O_curvature_pre_m_inv=arms['O'][i]['pre']['curvature_m_inv'],C_curvature_pre_m_inv=arms['C'][i]['pre']['curvature_m_inv'],O_brake=arms['O'][i]['requested_brake'],C_brake=arms['C'][i]['requested_brake'],O_front_clip=arms['O'][i]['front_clipped_ticks'],C_front_clip=arms['C'][i]['front_clipped_ticks']) for i in range(12)]
            cases.append(dict(case=key,common_arc_m=[0,common],endpoint_progress_m={a:z[-1]['arc_interval_m'][1] for a,z in arms.items()},same_elapsed_comparison=elapsed,common_arc_thresholds=thresholds,summaries=summaries,front_clip_intervals=events))
        assert count==48
        o0=next(c for c in cases if c['case']=='O0');assert [o0['summaries'][a]['full_window']['front_clipped_ticks'] for a in ['O','C']]==[3,9]
        result=dict(stage=396,cases=cases,rows=count,new_wrapper_actions=0,new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_environment_resets=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()),scope='Descriptive48storedintervals;samearcfirstpassagebracketsnotmatchedphysicalstates,notcausalorsafetyreserve/wholelapclaims')
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsignal)
    save(d/'observations-private.json',private);save(d/'result.json',result);print(__import__('json').dumps(dict(stage=396,rows=count,common={c['case']:c['common_arc_m'] for c in cases},CPU_s=result['CPU_s'],wall_s=result['wall_s']),ensure_ascii=False),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    elif sys.argv[2]=='run':run(root)
    else:raise ValueError(sys.argv[2])
