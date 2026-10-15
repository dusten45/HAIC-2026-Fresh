"""Native-zero18condition reconciliation and unexecuted T2954contract."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import zipfile
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]


def baseline_folder(R,p,road):
    if road in p['original6']:return R/'stage306/collection'/road
    if road.startswith('N'):return R/'stage294/policies/g1p4'/road
    return R/'stage295/TRAIN'/road/'g1p4'


def safe(r):
    return dict(completed=r['completed'],actual_DNF=r['actual_DNF'],censored=r['censored'],technical_error=r['technical_error'],native_actions=r['native_actions'],lap_ms=r['lap_ms'],damage=r['damage'],visited=r.get('visited',r.get('unique_tiles')),total_tiles=r['total_tiles'],retire_reason=r.get('retire_reason'))


def members(cfg):
    assert sha(cfg['archive_path'])==cfg['archive_sha256']
    with zipfile.ZipFile(cfg['archive_path']) as z:out={n:z.read(n) for n in z.namelist()}
    assert {n:hashlib.sha256(v).hexdigest() for n,v in out.items()}==cfg['members_sha256']
    return out


def run(R):
    D=R/'stage354';assert not D.exists();D.mkdir(mode=0o700)
    p=read(R/'stage330/plan.json');s=read(R/'stage330/summary-private.json');q=read(R/'stage349/plan.json');new=read(R/'stage330/native-outcome-private.json')['results'];base=p['baseline296']['results'];order=p['roads'];assert len(set(order))==len(base)==len(new)==18
    remote_head=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],text=True).strip();remote_raw=subprocess.check_output(['git','show','FETCH_HEAD:retry/h1_330_result.json']);remote=json.loads(remote_raw);assert remote_raw==(G/'retry/h1_330_result.json').read_bytes()
    save(D/'remote330-report.json',remote)
    files=[G/'retry/lineage354.py',G/'retry/h1_330_result.json',G/'retry/h1_330_native.py',G/'retry/fallback334_stage.py',G/'retry/package349_stage.py',G/'local_runner.py',G/'env_wrapper.py',G/'retry/diagnose.py',R/'stage330/plan.json',R/'stage330/summary-private.json',R/'stage330/native-outcome-private.json',R/'stage330/artifacts-private.json',R/'stage334/configs-private.json',R/'stage334/plan.json',R/'stage349/plan.json',R/'stage350/plan.json',R/'stage350/summary-private.json',R/'stage352/plan.json',R/'stage352/summary-private.json',R/'stage353/plan.json',R/'stage353/summary-private.json',R/'stage337/plan.json',R/'stage337/B/result.json',R/'stage337/actual-reset-contract.json',R/'project-effective-budget-v366.json',R/'research-deadline-current.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',D/'remote330-report.json']
    for road in order:
        f=baseline_folder(R,p,road);files += [f/'job.json',f/'result.json',f/'trace-private.jsonl',R/f'stage330/evaluation/{road}/result.json',R/f'stage330/evaluation/{road}/trace-private.jsonl']
    cfg330=read(R/'stage330/artifacts-private.json')['ON'];cfg334=read(R/'stage334/configs-private.json')['ON']['ON']
    files += [Path(c['archive_path']) for c in [p['baseline296']['config'],cfg330,cfg334,q['configs']['baseline'],q['configs']['candidate']]]
    plan=dict(stage=354,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='Saved-evidence audit and proposal only',remote_reference_commit=remote_head,remote_report_sha256=hashlib.sha256(remote_raw).hexdigest(),scope='Exactly existing18known conditions and namedversionlineage. Validate individual terminal/censor/artifact/condition/source records. No new testcase, simulation, actor, routing, learning or parameter choice.',budget=dict(new_native=0,new_actor=0,new_fits=0,research_remaining=532,final_reserve=84000),stop='Audit mismatch is an evidence/blocker, never permission to run recoveryexperiments. ProposedT2954notexecuted/reserved/granted.',source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    start,cpu=time.perf_counter(),time.process_time();B={r['road']:r for r in base};C={r['road']:r for r in new};rb={r['road']:r for r in remote['baseline296']};rc={r['road']:r for r in remote['results']};table=[];private_checks=[]
    current334=dict(N2=(337,'B'),O0=(352,'A'),O2=(353,'A'));current349=dict(N2=(350,'B'),O0=(352,'B'),O2=(353,'B'))
    for road in order:
        f=baseline_folder(R,p,road);br=read(f/'result.json');cr=read(R/f'stage330/evaluation/{road}/result.json');job=read(f/'job.json')
        assert safe(br)==safe(B[road])=={k:rb[road].get(k) for k in safe(br)};assert safe(cr)==safe(C[road])=={k:rc[road].get(k) for k in safe(cr)}
        assert job['case']==p['cases'][road] and br['initial_observation_sha256']==p['initial_observations'][road] and br['geometry_sha256']==p['cases'][road]['road_geometry_sha256']
        assert br['archive_sha256']==job['config']['archive_sha256']==p['baseline296']['config']['archive_sha256'];assert cr['archive_sha256']==cfg330['archive_sha256']
        for mode,rr,folder,cfg in [('296',br,f,job['config']),('330',cr,R/f'stage330/evaluation/{road}',cfg330)]:
            trace=rows(folder/'trace-private.jsonl');assert len(trace)==rr['native_actions'] and trace[-1]['terminal'] and not any(x['terminal'] for x in trace[:-1]);assert not rr['technical_error'] and not rr['censored'] and rr['completed']!=rr['actual_DNF']
            assert (rr['lap_ms'] is not None)==rr['completed'];assert rr['reaping']['process_reaped'] and rr['reaping']['actor_pids_absent']
            assert trace[-1]['damage']==rr['damage']
            for row in trace:
                assert len(row['action'])==3 and all(math.isfinite(x) for x in row['action']);assert -1<=row['action'][0]<=1 and 0<=row['action'][1]<=1 and 0<=row['action'][2]<=1
            # Existing extracted policy bytes, no imports or policy invocations.
            for name,h in cfg['members_sha256'].items():assert sha(folder/'cpu/package'/name)==h,(road,mode,name)
            private_checks.append(dict(road=road,mode=mode,result=str(folder/'result.json'),case_exact=True,trace_actions=len(trace),terminal=True,censored=False,error=None,archive_sha256=rr['archive_sha256'],extracted_members_exact=True))
        row=dict(condition=road,baseline296=safe(br),H1_330=safe(cr),current334_ON_H1=None,frozen349=None)
        for mapping,key,expected_hash in [(current334,'current334_ON_H1',q['configs']['baseline']['archive_sha256']),(current349,'frozen349',q['configs']['candidate']['archive_sha256'])]:
            if road not in mapping:continue
            stage,arm=mapping[road];rr=read(R/f'stage{stage}/{arm}/result.json');pp=read(R/f'stage{stage}/plan.json');assert pp['case']==p['cases'][road]
            cfg=pp['configs'][arm] if 'configs' in pp else pp['config'];assert cfg['archive_sha256']==expected_hash
            row[key]=dict(**safe(rr),source_stage=stage,source_arm=arm,archive_sha256=expected_hash)
        table.append(row)
    gains=[r for r in order if not B[r]['completed'] and C[r]['completed']];losses=[r for r in order if B[r]['completed'] and not C[r]['completed']];bc=sum(r['completed'] for r in base);cc=sum(r['completed'] for r in new)
    assert (bc,cc)==(17,15) and gains==['T2950'] and losses==['N2','T2954','T29511'] and bc+len(gains)-len(losses)==cc
    assert remote['summaries']['all18']==s['summaries']['all18'];assert remote['summaries']['all18']['lost_completions']==losses
    x330=members(cfg330);x334=members(cfg334);x349=members(q['configs']['candidate']);xb=members(q['configs']['baseline']);x296=members(p['baseline296']['config'])
    assert x334==xb and {n for n in x330 if x330[n]!=x334[n]}=={'retry/temporal_agent.py'} and set(x330)==set(x334)
    assert {n for n in x334 if x334[n]!=x349[n]}=={'retry/temporal_agent.py','retry/nominal238_base.py'} and set(x349)-set(x334)=={'retry/support342_logic.py'}
    assert x330['retry/h1_330_base.py']==x296['agent.py'] and all(x330[n]==v for n,v in x296.items() if n!='agent.py')
    lineage=dict(archive_sha256=dict(champion296=p['baseline296']['config']['archive_sha256'],H1_330=cfg330['archive_sha256'],current334_ON_H1=cfg334['archive_sha256'],baseline349=q['configs']['baseline']['archive_sha256'],candidate349=q['configs']['candidate']['archive_sha256']),
        from296to330='296root retained as h1_330_base; root wrapper adds fixedsix-model equal-raw-speed-mean H1pedal selection with allmodel supportintersection. Original296dependencies preserved. Per-input steering/nominalmemory preserved; closedloopobservations can change. No newfit in354.',
        from330to334='Current selectedbranch is outerH1ON + innerfallbackON of334two-by-twofamily. Exactly temporal_agent.py differs: rejected/missingoptical fallback adds HUDyawrotation plus existingHUDspeedtranslation. Acceptedoptical branch, H1models/root/controller/scheduling/constants unchanged.',
        from334to349='349baseline byteidentical selected334ON/H1.349candidate moves fixed342zero-raw-road-ring birth metadata and lineage routing filter insidearchive: only temporal/nominalmetadata+filter and helperaddition. Fullhazards stilldrive near/count/min-distance; H1models/controller/fallback unchanged.',
        coverage='330has18actualoutcomes.334stageitselfwas fixedpixel diagnostic, not18actualevaluation; original6cache used H1OFFsourcecontext. Latercurrent334ON/H1and349actual data exist onlyN2/O0/O2 here. Other15rows remain unmeasured for theseversions; neverinherit330labels.')
    target_case=p['cases']['T2954'];reset=read(R/'stage337/actual-reset-contract.json');assert reset['postreset_action_cap']==2038
    contract=dict(status='Prepared only; native execution, reservation and budget grant not made.',question='Does unchanged frozen349officiallycomplete existing T2954 under ownobservations/fullreturnedcontrols/normalmemory? This separates an unmeasured policycondition ratherthan repeating O0/O2or tuning.',case_key='T2954',candidate_archive_sha256=q['configs']['candidate']['archive_sha256'],candidate_worker_sha256=q['configs']['candidate']['worker_sha256'],new_candidate_runs=1,new_baseline_runs=0,new_cached_actor_calls=0,
        normal_episode=dict(native_cap=2000,actor_act_cap=2000,environment_resets=1,actor_resets=1,maximum_step_ticks=8000,expected_reset_ticks=51,maximum_total_raw_ticks=8051,source='local_runner defaultmax_steps2000, also explicit350stop precedent. Allprefix/auxiliarynative ifany count within2000; plannedauxiliary0.'),
        budget=dict(current_research=532,minimum_additional_for_normal2000=1468,research_after_hypothetical_grant=2000,final_reserved_actions=84000,final_reserve_used=0,grant_made=False,full_underlying_TimeLimit_option=dict(action_cap=2038,additional_research_needed=1506,remaining_raw_ticks=8150,reset_ticks=51,total_raw_ticks=8201,last_action_raw_ticks=2,scope='Different explicitcap, not automaticextension of normal2000.8200rawlimit minus50elapsed afterreset, skip4.')),
        reuse='296T2954completed344/lap27440and330T2954DNF612/357of357are immutablecontext only, notnewruns orsame-policy causalcomparators. Reuse exactcase seed/track/geometry/initialpixel identities and existing349package/interface/reset/sourcequalification.334hasnoT2954caseoractualrecord. Do not assert an old334/296fullpolicy prefix for349.',
        required_before_execution='Explicitly register sufficientbudget, currentdeadline, same frozen349archive+observer/runtime/environment hashes, exactexisting T2954case/init/RNG and normal2000stop. Check freshreset geometry/obstacle/initpixelhash and input-only actor, loadedmodule paths/hashes, resetmetadataempty and legal finitecommands. Capture newbefore/after originalpolicy+metadata/tracker/physical/accessRNGandrawcontacts. No artifactchanges ornewthresholds.',
        prefix='Only a causally justified same-input/same-state comparison may be used. T2954has no current334/349qualifiedactualprefix; do notforce296/330storedactions/pixels/memory. Old330pixels can be inspected later as existing data, but are not an on-policy349continuation or requirednewactorcache.',
        stops='Officialfinish orretirement first, else2000protocolcap, deadline, source/reset/interface/leak/technicalfailure. No automaticretry/extraarm/extension.2000nofinish isprotocolcensor; distinguishactualDNFandtechnicalcensor. Atapproveddeadline stopnewexperiments.',
        outcomes='Completion first, officialcenter-crossinglap minuspostresetstart; separatequalification,center,finishdeclaration. Uniqueprogress/contact/damage andretirement jointly.357of357tiles alone isnotcompletion, as historical330T2954demonstrates.',
        inference='OneknownTRAINfeasibility only.349versus330also includes334fallback, so cannotattribute difference solelyto342rule. A later same-conditioncurrent334baseline would be required for isolatedrule effect, separatelybudgeted; no sucharm here. No championpromotion/splitopening/generalization.',deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'])
    save(D/'T2954-case-private.json',target_case);save(D/'T2954-contract-private.json',dict(contract=contract,case=target_case,config=q['configs']['candidate']));save(G/'retry/T2954_354_contract.json',contract)
    priorities=[dict(order=1,condition='T2954',reason='Current349unmeasured;330DNFdespite357/357tiles. Test officialcompletion with sufficientnormalepisodebudget.'),dict(order=2,condition='T29511',reason='Thirdactualcompletionloss omitted fromshortsummary:296finish267/lap21300;330offtrack181/progress79of277. No334/349actualrecord; a distinctregressionuncertainty.'),dict(order=3,condition='T2950',reason='Checkretentionof330gain:296DNF315/progress208of338 versus330finish361/lap28860.334fixedpixelcacheisnotanactualcurrent349finish; no transferofsuccess.'),dict(order=4,condition='Other unmeasured existing conditions',reason='No automatic eighteen-condition success claim fromthreeknowncase results; prioritize only afterdistinctquestion andbudget. No newprotectedcases.')]
    for f,h in plan['source_hashes'].items():assert sha(f)==h,f
    v=read(R/'project-effective-budget-v366.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1285511,532,84000,0)
    cost=dict(stage=354,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_learning_fits=0,new_routing_calls=0,new_thresholds=0,new_paid_resources=0,individual_episodes_checked=36,conditions_checked=18,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1285511,research_remaining=532,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1370043,measurement_scope='Read-onlyindividualrecords/source/zipmember audit; no policy orsimulator execution. Fetch/preparation/report/git andalltaskwall notfullytimed.')
    report=dict(stage=354,remote_report=dict(commit=remote_head,sha256=plan['remote_report_sha256'],local_bytes_identical=True,source_path='retry/h1_330_result.json'),arithmetic=dict(baseline296_completed=bc,H1_330_completed=cc,conditions=18,gains=gains,losses=losses,equation='17 +1 -3 =15',finding='Remote330report andindividualresults were alreadycorrect. The shortnarrative omittedT29511; not a newfailure orcensor correction.'),table=table,all36_uncensored_without_technical_error=True,lineage=lineage,T2954_next_contract=contract,priorities=priorities,cost=cost,champion296_preserved=True,promotion=False,new_protected_split_opened=False,next_episode_executed=False)
    save(D/'individual-evidence-private.json',private_checks);save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/lineage354_result.json',report);save(D/'final-report-verification.json',dict(passed=True,remote330correct=True,individual36checked=True,arithmetic17plus1minus3equals15=True,additional_loss_T29511=True,versionmembers_exact=True,current334and349coverage_not_extrapolated=True,new_actor_calls=0,new_native_actions=0,research_remaining=532,final_reserve=84000,next_T2954_executed=False))
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    v.update(version=367,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v366.json'),prior_budget_sha256=sha(R/'project-effective-budget-v366.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage354_new_wrapper_actions=0);assert not (R/'project-effective-budget-v367.json').exists();save(R/'project-effective-budget-v367.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==354 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(arithmetic=report['arithmetic'],cost=cost,normal2000_shortfall=1468,underlying2038_shortfall=1506,next_episode_executed=False)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
