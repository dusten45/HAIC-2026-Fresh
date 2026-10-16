"""Saved-data/source audit only. No simulator, actor, dynamics import, integration or fit."""
import datetime,hashlib,json,math,signal,sys,time
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def stats(a):
    a=np.asarray(a,float);assert len(a) and np.isfinite(a).all()
    return dict(n=len(a),min=float(a.min()),median=float(np.median(a)),p95=float(np.percentile(a,95)),max=float(a.max()))

def force(samples):
    assert samples
    z=[]
    for s in samples:
        fx,fy,q=s['raw_long_N'],s['raw_lat_N'],s['force_ratio'];norm=math.hypot(fx,fy)
        limit=norm/q if q>0 else 400.;assert abs(limit-400)<1e-8
        assert math.isclose(fx,82*s['longitudinal_slip_m_s'],abs_tol=1e-9)
        assert math.isclose(fy,-82*s['lateral_slip_m_s'],abs_tol=1e-9)
        assert s['clipped']==(q>1) and not s['grass']
        scale=1/max(1,q)
        z.append(dict(q=q,lat=abs(fy)/limit,lon=abs(fx)/limit,rawlat=abs(fy),rawlon=abs(fx),applat=abs(fy)*scale,applon=abs(fx)*scale,retained=scale,clipped=q>1,latalone=abs(fy)>limit,mixed=q>1 and abs(fy)<=limit,gas=s['gas'],joint=s['joint_angle']))
    return dict(samples=len(z),clipped=sum(s['clipped'] for s in z),lateral_alone_over_limit=sum(s['latalone'] for s in z),combined_over_with_lateral_within_limit=sum(s['mixed'] for s in z),raw_lateral_ratio=stats([s['lat'] for s in z]),raw_longitudinal_ratio=stats([s['lon'] for s in z]),raw_vector_ratio=stats([s['q'] for s in z]),raw_abs_lateral_N=stats([s['rawlat'] for s in z]),raw_abs_longitudinal_N=stats([s['rawlon'] for s in z]),applied_abs_lateral_N=stats([s['applat'] for s in z]),applied_abs_longitudinal_N=stats([s['applon'] for s in z]),retained_vector_fraction=stats([s['retained'] for s in z]),gas=stats([s['gas'] for s in z]),joint_angle=stats([s['joint'] for s in z]))

def prepare(root):
    d=root/'stage399';assert not d.exists();d.mkdir(mode=0o700)
    p398=read(root/'stage398/plan.json')
    paths=[Path(__file__),G/'core/vendor/car_dynamics.py',G/'core/vendor/car_racing.py',G/'env_wrapper.py',G/'retry/pace265_run.py',G/'retry/pace268_profile.py',G/'retry/pace268_run.py',G/'retry/pace269_run.py',G/'retry/executor397.py',root/'stage398/plan.json',root/'stage398/cost.json',root/'project-effective-budget-v418.json',root/'research-deadline-current.json',root/'experiment-cost-lines.jsonl',root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']
    for k in ['O0','N1']:paths += [root/f'stage398/{k}/trace-private.jsonl',Path(p398['fixed_plans'][k])]
    historic=['stage265/O0_1.5','stage268/g1_p3','stage269/N1_baseline','stage269/N1_candidate']
    for h in historic:paths += [root/h/'trajectory-private.json',root/h/'result.json']
    paths += [root/'stage265/plan.json',root/'stage268/plan.json',root/'stage269/plan.json']
    p=dict(stage=399,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mode='Descriptivepost398audit, notconfirmatorycausaltest',CPU_cap_s=60,wall_cap_s=120,wrapper_cap=0,actor_cap=0,model_integration_cap=0,learning_cap=0,SEALED_cap=0,new_paid_cap=0,scope='All274saved398rows, last5percase declared failure window; historical265O0pace1.5,268selectedO0,269N1baseline/candidate only. No trajectory generation, policy recalculation, envelope optimization or gain/profile search.',metrics='Verifywheel-local source forces82*slip and400Nlive limits; decompose clipping into lateral-alone-over-limit vs combined, radial retained fraction, front/rear; compare target/actual speed, yaw, requestedsteer and actualjoint, actualpatherror, forwardcommand vs achievednormacceleration. Checkexistingpace1.5 squared-speed inequalities againstoriginalapproximate scalarbounds. Historicalmatchedstep onlywhen baseline265exact390commands/metrics verified; no claimedphysicalstatematching to268/269.',failure='Any source/hash/schema/nonfinite/force-equation mismatch or cap ->stop analysis and marktechnical/unqualified, do not substitutezeros or simulate. Missinghistorictelemetry explicitlyunavailable. Descriptivepatternsnotcausality. No finiteBcertificate fromnonmaxbraking.',promotion='Only choose proposeddiscriminatingexperiment if observations distinguish newassumptions and limitations explicit; no296promotion, no11simpossibilityclaim, no automatic execution.',sources={str(f):sha(f) for f in paths},static_reference_commit='3e584dff988f0b90fce3dd563b7f6351a13d21f8',static_reference_path='retry/static_control_audit_20261016.md',historic=historic)
    save(d/'plan.json',p);print('399 read-only analysis registered')

def run(root):
    d=root/'stage399';p=read(d/'plan.json');assert not(d/'result.json').exists()
    for f,h in p['sources'].items():assert sha(f)==h,f
    def timeout(*args):raise TimeoutError('399 CPU60')
    signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    start,cpu=time.perf_counter(),time.process_time();p398=read(root/'stage398/plan.json');cases=[]
    for key in ['O0','N1']:
        rows=[json.loads(s) for s in (root/f'stage398/{key}/trace-private.jsonl').read_text().splitlines()];assert len(rows)==(175 if key=='O0' else 99)
        fixed=read(Path(p398['fixed_plans'][key]));model=fixed['model'];prof=fixed['free_profile'];W=(1.5*np.asarray(prof['speed']))**2;ds=np.asarray(prof['ds']);k=np.abs(np.asarray(prof['curvature']));gradient=np.diff(W)/(2*ds)
        residual=dict(segments=len(ds),positive_gradient_over_original_traction_only=int(sum(gradient>model['rear_traction_accel'])),positive_gradient_over_original_drive_including_power=int(sum(gradient>np.minimum(model['rear_traction_accel'],80000/(np.sqrt(W[:-1])+2.7)/model['effective_mass']))),negative_gradient_over_original_brake=int(sum(-gradient>model['brake_accel'])),max_implied_accel=float(gradient.max()),max_implied_brake=float(-gradient.min()),max_node_lateral_proxy=float(max(W[:-1]*k)),original_lateral_allowance=model['lateral_accel'],interpretation='Originalscalarplanningallowances only, notsourcephysicalfeasibilitycertificate')
        def window(rr):
            def wheelgroup(indices):return force([s for r in rr for s in r['raw_tire_samples'] if s['wheel'] in indices])
            out=dict(actions=len(rr),front=wheelgroup([0,1]),rear=wheelgroup([2,3]),positive_gas_actions=sum(r['command'][1]>0 for r in rr),braking_actions=sum(r['command'][2]>0 for r in rr))
            for name,fn in dict(actual_speed=lambda r:r['pre']['speed'],target_speed=lambda r:r['reference'].get('r'),yaw_abs=lambda r:abs(r['pre']['yaw']),requested_steer=lambda r:r['command'][0],post_path_error=lambda r:r['post_projection']['path_error_m'],achieved_norm_accel=lambda r:(r['post']['speed']-r['pre']['speed'])/(r['post']['time']-r['pre']['time']),target_lateral_proxy=lambda r:None if r['reference'].get('r') is None else r['reference']['r']**2*k[r['reference']['projection']['index']],actual_lateral_proxy=lambda r:r['pre']['speed']**2*k[r['reference']['projection']['index']]).items():out[name]=stats([fn(r) for r in rr if fn(r) is not None])
            # Environment negates requested steer; joint target sign is opposite command.
            out['front_joint_target_error_abs']=stats([abs(s['joint_angle']+r['command'][0]) for r in rr for s in r['raw_tire_samples'] if s['wheel']<2])
            return out
        allsamples=[s for r in rows for s in r['raw_tire_samples']];last=rows[-1]
        clip_first={g:next((r['step'] for r in rows if any(s['clipped'] for s in r['raw_tire_samples'] if s['wheel'] in ids)),None) for g,ids in [('front',[0,1]),('rear',[2,3])]}
        # Rows with r defined; startup has no r and is excluded explicitly.
        active=[r for r in rows if r['reference'].get('r') is not None]
        cases.append(dict(case=key,rows=len(rows),whole=window(rows),last5=window(rows[-5:]),last_action=window([last]),original_profile_residual=residual,first_clip=clip_first,reference_rows=len(active),actual_above_target_rows=sum(r['pre']['speed']>r['reference']['r'] for r in active),positive_gas_while_front_or_rear_clipped=sum(r['command'][1]>0 and any(s['clipped'] for s in r['raw_tire_samples']) for r in rows),positive_gas_while_lateral_alone_over_limit=sum(r['command'][1]>0 and any(abs(s['raw_lat_N'])>400 for s in r['raw_tire_samples']) for r in rows),all_force_laws_checked_samples=len(allsamples)))
    historic=[]
    for h in p['historic']:
        rr=read(root/h/'trajectory-private.json');res=read(root/h/'result.json')
        historic.append(dict(source=h,rows=len(rr),lap_ms=res['lap_ms'],completed=res['completed'],actual_DNF=res['actual_DNF'],damage=res['damage'],max_pre_path_error=max(r['path_error_m'] for r in rr),speed=stats([r['speed_m_s'] for r in rr]),target=stats([r['target_speed_m_s'] for r in rr]),steer=stats([r['action'][0] for r in rr]),raw_tire_components_available=False,telemetry='265axlesummaryonly;268/269lightweight,no rawforces/yaw/positions. Same step is not same state/arc acrosspolicies.'))
    # 265 O0 and cached390 are exact action/speed/feed data, not merely matching labels.
    h=read(root/'stage265/O0_1.5/trajectory-private.json');old=read(root/'stage390/A-O0/trace-private.json');assert len(h)==len(old)
    exact_commands=sum(r['action']==s['control']['action'] for r,s in zip(h,old));exact_targets=sum(r['target_speed_m_s']==s['control']['target_speed_m_s'] for r,s in zip(h,old));exact_feed=sum(r['feedforward_accel']==s['control']['feedforward_accel'] for r,s in zip(h,old));exact_speed=sum(r['speed_m_s']==s['pre']['speed'] for r,s in zip(h,old));speed_max_abs=max(abs(r['speed_m_s']-s['pre']['speed']) for r,s in zip(h,old));assert exact_commands==exact_targets==exact_feed==247
    matched=dict(rows=247,exact_command_rows=exact_commands,exact_target_rows=exact_targets,exact_feedforward_rows=exact_feed,exact_speed_rows=exact_speed,max_speed_abs_difference=speed_max_abs,scope='No bitexactspeed claim; samecontrol/target/feed sequences, historic speed5rows differatfloat64normrounding scale. No tolerancebasedstatecertificate.')
    v=read(root/'project-effective-budget-v418.json');assert v['research_remaining']==32072 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    for f,h in p['sources'].items():assert sha(f)==h,f
    result=dict(stage=399,cases=cases,historic=historic,historic265_matches390_rows=matched,source_equations_verified=True,new_wrapper_actions=0,new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,research_remaining=32072,final_reserved_actions=84000,final_reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_hashes_rechecked=True,causal_identification=False,source_feasible_envelope_certified=False,pixel_promotion=False)
    assert result['CPU_s']<60 and result['wall_s']<120;signal.setitimer(signal.ITIMER_PROF,0);save(d/'result.json',result);print(json.dumps(dict(stage=399,CPU_s=result['CPU_s'],wall_s=result['wall_s'],native=0,model=0,cases=len(cases))))
if __name__=='__main__':
    root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
