"""One frozen stored-input/static-contract gate; never vehicle dynamics or native."""
import copy,datetime,json,math,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.executor397 import CoherentExecutor,ExecutorDomainError,canonical_projection
G=Path(__file__).resolve().parent.parent

FIXTURES=['same_vertex_outgoing','terminal_vertex_incoming','zero_positive_target_rest','tiny_positive_target_no_epsilon','stop_intent_rest','stop_intent_moving','reject_nonlaunch_zero_target','reject_reverse','reject_distinct_feet','reject_selfcrossing_arcs','official_center_not_DONE','official_forwardedge_DONE_center_timestamp','reject_stale_finish_confirm','reject_future_finish_metadata','qualified_only_not_DONE','reject_seam_without_officialcandidate','reject_duplicate_boundary']

def prepare(root):
    d=root/'stage397';assert not d.exists();d.mkdir(mode=0o700);v=read(root/'project-effective-budget-v416.json');assert v['research_remaining']==32346 and v['final_reserved_actions']==84000
    p395=read(root/'stage395/plan.json');sources=[Path(__file__),G/'retry/executor397.py',G/'retry/pilot398_run.py',G/'retry/scalar392_audit.py',G/'retry/loss389_analyze.py',G/'core/finish_line.py',root/'project-effective-budget-v416.json',root/'research-deadline-current.json',root/'stage395/plan.json']
    for key in ['N1','O0']:sources += [Path(p395['fixed_plans'][key]),root/('stage390/A-'+key)/'trace-private.json',root/('stage395/'+key+'-C')/'window-private.json',root/('stage395/'+key+'-C')/'fork-boundary-private.json',root/('stage394/'+key+'-O')/'initial-private.json']
    p=dict(stage=397,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',CPU_cap_s=60,new_wrapper_cap=0,new_actor_cap=0,new_model_integration_cap=0,new_learning_cap=0,new_SEALED_cap=0,sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},required=dict(stored_C_commands=24,recorded_launches=2,recorded_positive_transitions=2,late_cursor_firstlap_reference=1,static_fixtures=FIXTURES),contract='Onefrozencase-independentLAUNCH/FIRST_LAP/FINISH_CONFIRM/DONE andseparatestopintent. Canonicalsamevertexfixedone-sidedprojection; distinctclosestarc ambiguityfailclosed. Strictnegativeprogressdomain, no epsilon/futureinput. Samepath/profilepace1.5/gainclamp/pursuitsteering.',launch='ResetphasefirstcommandalwaysfiniteoriginalOstartup;latertransitiontoC onlycurrentactualpositivearc/target. Nominimumtimeorcase/frameIDpatch. Ongoingtruezero-targetisunsupported,notautomaticlaunch.',firstlap='Profilephasebasedownunwrappedactualarc,notoldGTsteeringcursor. Oldcursor maywrapearlierwithouttarget0restart. Sharedvertexright-sidedexceptterminalnode0incoming;firstlaparc>=L withoutcurrentofficialcandidate stops,notcomplete.',finish='FINISH_CONFIRMonlycurrentqualifiedvalidforwardcentercandidate inofficialcorridor;positivefixedterminaltarget,f0;abortstale/invalidmetadata. DONEonlyofficialfinish_time setafterforwardedge,recordcenter-crossingtime. No newlap loop.',tests='Staticfixturesexplicitlysyntheticnotvehiclestatepredictions. FinishLineTracker logiccalls onprovidedpoints arecontracttests,novehicleworld/integration. Stored395C replay seedsFIRST_LAPatforkand usesonlycurrentrow/previousfinishmetadata tocheckunchangedinterior law,notfull-resetperformance.',pass_rule='Allrequiredchecks exactly; anyunexpectedassert/domain/technical/CPU/sourcefailure ->passedfalseandNO actualpilot. No postresultpolicy/ruleediting toforcepass.',next_if_pass='Withoutfurtherapproval register398onecandidate2knownTRAINfullpilot C vs cachedO, max1600/800each,reset2,CPU180/wall300/parallel2. Sourcesalreadyboundhere;no retuningafterpilot.',forbidden='Native/actor/vehicledynamics/modelintegration/learning/SEALED/paidresource/read372failures/conditionreselections')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),fixtures=len(FIXTURES),stored_commands=24,native_cap=0)),flush=True)

def seed_first(fixed,state,s=None):
    c=CoherentExecutor(fixed);c.phase='FIRST_LAP';c.launch_commanded=True;q=canonical_projection(c.line,state['pos'],state['vel'],c.phase);c.previous_arc=q['arc'];c.s=q['arc'] if s is None else s;return c

def state(pos,vel,t):return dict(pos=list(pos),vel=list(vel),speed=float(np.linalg.norm(vel)),time=float(t),angle=0.)

def run(root):
    from core.finish_line import FinishLineTracker
    d=root/'stage397';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
    for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));start,cpu=time.perf_counter(),time.process_time();checks=[];fixtures=[];error=None;failure=None
    def guard():assert time.process_time()-cpu<60 and datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
    def timeout(signum,frame):raise TimeoutError('397CPU60')
    oldsig=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    def okay(name,**details):guard();fixtures.append(dict(name=name,passed=True,**details))
    def reject(name,fun):
        try:fun()
        except ExecutorDomainError as e:okay(name,expected_domain_rejection=str(e));return
        raise AssertionError(name+' acceptedunsupportedinput')
    try:
        pp=read(root/'stage395/plan.json');matched=0;launches=[];transitions=[]
        for key in ['N1','O0']:
            fixed=read(Path(pp['fixed_plans'][key]));w=read(root/('stage395/'+key+'-C')/'window-private.json');c=seed_first(fixed,w[0]['pre'],w[0]['pre_arc_unwrapped_m']);finish=read(root/('stage395/'+key+'-C')/'fork-boundary-private.json')['wrapper']['finish_tracker']
            for row in w:
                guard();command,meta=c.act(row['pre'],row['nominal_command'],finish)
                assert command.tolist()==row['command'] and meta['phase']=='FIRST_LAP';matched+=1;finish=row['post_full']['wrapper']['finish_tracker']
            old=read(root/('stage390/A-'+key)/'trace-private.json');c=CoherentExecutor(fixed);initialfinish=read(root/('stage394/'+key+'-O')/'initial-private.json')['wrapper']['finish_tracker'];command,meta=c.act(old[0]['pre'],old[0]['control']['action'],initialfinish,old[0]['control']['cursor_arc_m']);assert command.tolist()==old[0]['control']['action'] and c.phase=='LAUNCH';launches.append(dict(case=key,finite=True,phase=c.phase))
            command,meta=c.act(old[1]['pre'],old[1]['control']['action'],{},old[1]['control']['cursor_arc_m']);assert c.phase=='FIRST_LAP' and meta['r']>0 and np.isfinite(command).all();transitions.append(dict(case=key,phase=c.phase,r=meta['r']))
        assert matched==24;checks += [dict(name='stored_C_commands',count=matched,passed=True),dict(name='recorded_launches',count=len(launches),passed=True,records=launches),dict(name='recorded_positive_transitions',count=len(transitions),passed=True,records=transitions)]
        fixed=read(Path(pp['fixed_plans']['O0']));old=read(root/'stage390/A-O0/trace-private.json');row=old[-1];assert row['control']['cursor_index']>=len(fixed['line']);c=seed_first(fixed,row['pre']);a,m=c.act(row['pre'],row['control']['action'],{},row['control']['cursor_arc_m']);j=m['projection']['index'];u=m['projection']['u'];expected=float(np.sqrt((1-u)*c.nodes[j]**2+u*c.nodes[j+1]**2));assert c.phase=='FIRST_LAP' and m['r']==expected;checks.append(dict(name='late_cursor_firstlap_reference',count=1,passed=True,old_target=row['control']['target_speed_m_s'],firstlap_target=m['r']))
        toy=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.,10.,10.,10.],speed=[0.,8.,8.,8.,8.]),model=fixed['model']);nominal=np.asarray([0.,.05,0.],np.float32)
        s=state([10,0],[1,0],10);c=seed_first(toy,s);a,m=c.act(s,nominal,{});assert m['projection']['side']=='outgoing_vertex' and m['r']==12 and np.isfinite(a).all();okay('same_vertex_outgoing')
        q=canonical_projection(toy['line'],[0,0],[0,-1],'FIRST_LAP');assert q['side']=='incoming_terminal_vertex' and q['arc']==40 and q['index']==3 and q['u']==1;okay('terminal_vertex_incoming')
        s=state([5,0],[0,0],10);c=seed_first(toy,s);a,m=c.act(s,nominal,{});assert m['r']>0 and m['raw_accel']==1.5*m['r'] and a[2]==0;okay('zero_positive_target_rest')
        s=state([1e-12,0],[0,0],10);c=seed_first(toy,s);a,m=c.act(s,nominal,{});assert 0<m['r']<1e-4 and np.isfinite(a).all();okay('tiny_positive_target_no_epsilon',r=m['r'])
        for name,velocity in [('stop_intent_rest',[0,0]),('stop_intent_moving',[2,0])]:
            c=CoherentExecutor(toy,'stop');a,m=c.act(state([0,0],velocity,10),nominal,{});assert c.phase=='STOP' and a[1]==0 and (a[2]>0 if velocity[0] else a[2]==0);okay(name)
        bad=copy.deepcopy(toy);bad['free_profile']['speed'][2]=0;reject('reject_nonlaunch_zero_target',lambda:CoherentExecutor(bad,'lap'))
        s=state([5,0],[-1,0],10);c=seed_first(toy,s);reject('reject_reverse',lambda:c.act(s,nominal,{}))
        reject('reject_distinct_feet',lambda:canonical_projection(toy['line'],[5,5],[1,0],'FIRST_LAP'))
        reject('reject_selfcrossing_arcs',lambda:canonical_projection([[0,0],[10,10],[0,10],[10,0]],[5,5],[1,0],'FIRST_LAP'))
        ft=FinishLineTracker(center=(0.,0.),forward=(1.,0.),half_width=2.,half_depth=1.)
        assert not ft.update((-2.,0.),(2.,0.),.95,1.) and not ft.update((-.5,0.),(2.,0.),.95,2.) and not ft.update((.25,0.),(2.,0.),.95,3.);assert ft.finish_time_s is None and ft.candidate_crossing_time_s==3.
        c=CoherentExecutor(toy);c.phase='FIRST_LAP';c.previous_arc=39.5;c.s=39.5;c.launch_commanded=True;a,m=c.act(state([.25,0],[2,0],3),nominal,dict(ft.__dict__));assert c.phase=='FINISH_CONFIRM' and m['r']==12 and m['f']==0 and np.isfinite(a).all();okay('official_center_not_DONE')
        assert ft.update((1.25,0.),(2.,0.),.95,4.) and ft.finish_time_s==3.;a,m=c.act(state([1.25,0],[2,0],4),nominal,dict(ft.__dict__));assert a is None and c.phase=='DONE' and m['official_finish_time_s']==3.;okay('official_forwardedge_DONE_center_timestamp')
        fin=dict(center=(0.,0.),forward=(1.,0.),half_width=2.,half_depth=1.,qualified_time_s=1.,candidate_crossing_time_s=3.,crossing_from_back=True,finish_time_s=None)
        c=CoherentExecutor(toy);c.phase='FINISH_CONFIRM';c.previous_arc=.25;c.s=40.25;stale=dict(fin,candidate_crossing_time_s=None,crossing_from_back=False);reject('reject_stale_finish_confirm',lambda:c.act(state([.4,0],[2,0],3.5),nominal,stale))
        c=CoherentExecutor(toy);c.phase='FIRST_LAP';c.previous_arc=39.5;c.s=39.5;reject('reject_future_finish_metadata',lambda:c.act(state([.25,0],[2,0],2.5),nominal,fin))
        s=state([5,0],[1,0],10);c=seed_first(toy,s);a,m=c.act(s,nominal,dict(qualified_time_s=9.,candidate_crossing_time_s=None,finish_time_s=None));assert a is not None and c.phase!='DONE';okay('qualified_only_not_DONE')
        s=state([0,0],[0,-1],10);c=seed_first(toy,s,40.);reject('reject_seam_without_officialcandidate',lambda:c.act(s,nominal,{}))
        s=state([5,0],[1,0],10);c=seed_first(toy,s);c.act(s,nominal,{});reject('reject_duplicate_boundary',lambda:c.act(s,nominal,{}))
        assert [f['name'] for f in fixtures]==FIXTURES and all(c['passed'] for c in checks)
    except BaseException as e:
        failure=type(e).__name__+': '+str(e);error=None if isinstance(e,(AssertionError,ExecutorDomainError)) else failure;save(d/'failure-private.json',dict(failure=failure,traceback=traceback.format_exc()))
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig)
    result=dict(stage=397,passed=failure is None,qualification_failure=failure,technical_error=error,stored_checks=checks,fixtures=fixtures,fixture_count=len(fixtures),new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_source_physics_rollout_ticks=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()),scope='Staticcontract/24storedinteriorcommands only; fullcandidatephysicalperformanceunknown; expectedinvaliddomainsreject,notuniversalstatecoverage')
    save(d/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    else:run(root)
