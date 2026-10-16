"""First-mismatch source replay gate for saved398; no native env or actor."""
import datetime,hashlib,json,math,signal,sys,time,traceback
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.chmod(0o600);temp.replace(p)

def prepare(root):
    d=root/'stage400';assert not d.exists();d.mkdir(mode=0o700);b=read(root/'project-effective-budget-v419.json');assert b['research_remaining']==32072 and b['final_reserved_actions']==84000 and b['final_reserve_used']==0
    p391=read(root/'stage391/plan.json');p398=read(root/'stage398/plan.json')
    paths=[Path(__file__),G/'retry/source_vehicle_transition.py',G/'damage.py',G/'retry/envelope399_result.md',G/'retry/envelope399_result.json',root/'project-effective-budget-v419.json',root/'research-deadline-current.json',root/'stage391/plan.json',root/'stage398/plan.json']+list((G/'core').rglob('*.py'))
    for k in ['O0','N1']:paths += [root/f'stage398/{k}/initial-private.json',root/f'stage398/{k}/trace-private.jsonl',Path(p398['fixed_plans'][k])]
    p=dict(stage=400,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case_order=['O0','N1'],actions={'O0':175,'N1':99},limits=p391['limits'],replay_model_tick_cap=1096,replay_CPU_cap_s=60,total_model_tick_cap=12288,total_CPU_cap_s=180,total_wall_cap_s=300,max_parallel=2,native_cap=0,actor_cap=0,learning_cap=0,SEALED_cap=0,reserve_use=0,source_model='UnmodifiedSourceVehicleTransition fromstored398initialphysicalsnapshot. Eachcaseoneworld continuouscommands, no intermediatecorrection. Noactualenvironment/reset/trackgenerator.',replay_gate='Initialbodies/tiles/progress exact; everyboundary speedabs<=.5,yawrateabs<=.05,posL2<=.1; collision/damage/contactedwheelcount exact391criteria. Firstmismatch globallystops,no remainingcase/profile/branch/factorial. Diagnosticsperwheelroadcounts,omega,joint,gas,brake,visited,counterarenotnewthresholds.',conditional_order=['Replay398qualification','Profilepace1.0staticresidual','Freshsnapshotbranchrestorationandcandidateindependence','Onlyifallqualified,fixed2x2modelcomparison'],profile_gate='Existing258pace1.0hypothesisonly,not sourceguaranteedenvelope. CheckW>=0/C,drive mintraction/power andbrake differences,initial0,terminalpositive; anyresidual ->unqualified,norepair/search.',branch_gate='Newbranchmustmatch untouchedparent underidenticalcommand at391criteria anddiscrete states; statecapturemustnotmutateparent;6candidatebranchesmustnotmutateparentoroneanother andfixedorderrepeatedreference mustagree. Allpositivequalificationtickscharge12288cap. Notstoredsolverwarmstarts.',factorial='OneknownN1, same reset/path/observations, profile1.5vs1.0 crossedwith C397pursuit vs6candidatejointonestepselection. 160actionsmaxperarm or398N1failurearc reached. Native0. Noadditionalcandidate/gain/profilefitting.',six_candidates='Steer[pursuit_request,negativecurrentfrontmeanjoint,0] x pedals[nominal,coast(0,0)] inlistedorder; clampstocurrentlimits. Sameprofiletarget. Candidateprediction safetyflagsfirst,thenpostpatherror,absyaw,negativeforwardprogress,listedorder lexicographic. Allunsafe/unqualified ->stop,nofallback.',safety='Same398patherror>3m,newcollision/damage,wheelroadloss/grass,meaningfulreverse. Domain/technical/source/resource/deadlinefailurestop. Do notlabelmodeloutcomeasactualenvironmentDNF.',factorial_readout='Mustreach398N1failurearcwithin160elsecensoredunconfirmed. EonlyvsJonlydiagnostic,safeEonlysupportsprofilesufficiencyforthisrecipe; safeJwithsameprofileandarrivalnot>one.08sactionslowerandmaxerror>=.1mlower supportsjointincrement beyondslowing;onlybothpass=>interaction;bothindividualpassoroverlappingsupport=>unidentified. Not296promotion/generalization/11simpossibility.',sources={str(f):sha(f) for f in paths},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(stage=400,registered=True,plan_sha256=sha(d/'plan.json'),model_replay_cap=1096,CPU_replay_cap=60)))

def run(root):
    from retry.source_vehicle_transition import SourceVehicleTransition
    import Box2D
    d=root/'stage400';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=__import__('os').getpid()))
    start,cpu=time.perf_counter(),time.process_time();ticks=reserved=worlds=0;cases=[];raw=[];error=None;first=None;active=None;status='RUNNING'
    def guard():
        assert time.process_time()-cpu<60 and time.perf_counter()-start<300
        assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
    def timeout(*args):raise TimeoutError('400replayCPU60')
    prior=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    try:
        for key in p['case_order']:
            guard();snapshot=read(root/f'stage398/{key}/initial-private.json')['physical'];truth=[json.loads(s) for s in (root/f'stage398/{key}/trace-private.jsonl').read_text().splitlines()];assert len(truth)==p['actions'][key]
            worlds+=1;active=SourceVehicleTransition(snapshot);initial=dict(bodies=active.initial_bodies_exact,tiles=active.initial_tiles_exact,progress=active.initial_progress_exact);rows=[]
            if not all(initial.values()):first=dict(case=key,step=0,failed_fields=['initialization'],initial=initial)
            else:
                for row in truth:
                    guard();assert reserved+4<=1096;reserved+=4;before=active.native_ticks
                    try:q=active.step(np.asarray(row['command'],np.float32))
                    finally:ticks+=active.native_ticks-before
                    assert active.native_ticks-before==4
                    a=row['post'];errs=dict(speed_m_s=abs(q['speed_m_s']-a['speed']),yaw_rate_rad_s=abs(q['angular_velocity']-a['yaw']),position_m=float(np.linalg.norm(np.asarray(q['position'])-a['pos'])))
                    matches=dict(collision=q['collision']==row['collision'],damage=q['damage']==row['damage'],wheel_road_contacts=q['wheel_road_contacts']==sum(n>0 for n in a['road_contacts']))
                    diag=dict(wheel_omega_max_abs=max(abs(float(w.omega)-t) for w,t in zip(active.car.wheels,a['wheel_omega'])),joint_max_abs=max(abs(float(w.joint.angle)-t) for w,t in zip(active.car.wheels,a['joint'])),gas_max_abs=max(abs(float(w.gas)-t) for w,t in zip(active.car.wheels,a['wheel_gas'])),brake_max_abs=max(abs(float(w.brake)-t) for w,t in zip(active.car.wheels,a['wheel_brake'])),wheel_tile_counts_match=[len(w.tiles) for w in active.car.wheels]==a['road_contacts'],visited_match=q['unique_tiles']==a['visited'],offtrackcounter_match=q['off_track_counter']==a['off_track_counter'])
                    failed=[k for k,v in errs.items() if v>p['limits'][k]]+[k for k,v in matches.items() if not v];r=dict(step=row['step'],errors=errs,discrete=matches,diagnostics=diag,passed=not failed);rows.append(r);raw.append(dict(case=key,step=row['step'],predicted=q,actual_post=a))
                    save(d/'progress.json',dict(ticks=ticks,reserved=reserved,case=key,step=row['step']))
                    if failed:first=dict(case=key,step=row['step'],failed_fields=failed,record=r);break
            cases.append(dict(case=key,initial=initial,checked_actions=len(rows),required_actions=p['actions'][key],passed=first is None and len(rows)==len(truth),rows=rows,max_errors={k:max((r['errors'][k] for r in rows),default=0.) for k in p['limits']}))
            active.close();active=None
            if first:break
        status='QUALIFIED' if first is None and len(cases)==2 else 'UNQUALIFIED_FIRST_MISMATCH'
    except BaseException as e:
        status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(d/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,prior)
        if active:active.close()
    save(d/'comparisons-private.json',raw)
    result=dict(stage=400,status=status,first_mismatch=first,technical_error=error,cases=cases,unexecuted_cases=[k for k in p['case_order'] if k not in [c['case'] for c in cases]],source_physics_ticks=ticks,reserved_ticks=reserved,unconfirmed_reserved_ticks=reserved-ticks,source_model_world_initializations=worlds,source_zero_time_contact_setups=worlds,new_wrapper_actions=0,new_environment_resets=0,new_actor_calls=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,profile_static_executed=False,branch_qualification_executed=False,factorial_executed=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,python=sys.version.split()[0],numpy=np.__version__,Box2D=Box2D.__version__,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()))
    save(d/'result.json',result);print(json.dumps(dict(stage=400,status=status,first_mismatch=first,ticks=ticks,CPU_s=result['CPU_s'],wall_s=result['wall_s']),ensure_ascii=False))
if __name__=='__main__':
    root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
