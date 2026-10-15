"""Saved-lineage/coordinate audit and exactly two frozen routing/target entries."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import cv2
import numpy as np
from retry.path271_run import read,save,sha
from retry.lineage339_audit import components,track,centers,pixels
from retry.support342_logic import advance_evidence

G=Path(__file__).resolve().parent.parent


def rows(path):return [json.loads(x) for x in path.read_text().splitlines()]


def run(R):
    D=R/'stage356';assert not D.exists();D.mkdir(mode=0o700);cfg=read(R/'stage355/plan.json')['config'];assert sha(cfg['archive_path'])==cfg['archive_sha256'];package=R/'stage355/B/cpu/package'
    files=[G/'retry/boundary356.py',G/'retry/link348_functions.py',G/'retry/lineage339_audit.py',G/'retry/support342_logic.py',G/'retry/support342_stage.py',G/'retry/support342_run.py',G/'retry/confidence341_run.py',G/'core/vendor/car_racing.py',G/'env_wrapper.py',R/'stage355/plan.json',R/'stage355/summary-private.json',R/'stage355/B/trace-private.jsonl',R/'stage355/B/frames-actions-private.npz',R/'stage349/plan.json',R/'project-effective-budget-v369.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',Path(cfg['archive_path'])]
    dependency_names=['retry/nominal238_base.py','retry/parameter_agent.py','retry/h1_330_base.py','retry/h1_330_select.py','retry/h1_329_select.py','agent.py','retry/hud248_features.py','retry/hud_feedback.py','retry/support342_logic.py']
    for name in dependency_names:assert sha(package/name)==cfg['members_sha256'][name];files.append(package/name)
    plan=dict(stage=356,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Saved355lineage/currentcomponent91-93and exact92filtered-versus-restoreonly92:0route/target. No newactor/controller/environment, fit, rulechange orhypothesis application.',budgets=dict(direct_routing_entries=2,direct_target_entries=2,actor_calls=0,controller_calls=0,native_actions=0,environment_resets=0,metadata_updates=94),stop='Stop at source/lineage/coordinate/originalroute/target reproduction mismatch. If route/target differs, leave fullcontrol effect unresolved; no automaticactor/clone/controllerexpansion.',source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    start,cpu=time.perf_counter(),time.process_time();rr=rows(R/'stage355/B/trace-private.jsonl');frames=np.load(R/'stage355/B/frames-actions-private.npz')['frames_uint8'];assert len(rr)==356 and len(frames)==357
    lineage=track(rr[:94]);previous=[]
    for i,r in enumerate(rr[:94]):
        state=advance_evidence(r['tracker'],previous,i+1,frames[i].astype(np.float32)/255);assert state==r['support_record'];previous=state['after']
    detail=[];local=[]
    constants={}
    for n in ast.parse((G/'core/vendor/car_racing.py').read_text()).body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id in ['WINDOW_W','WINDOW_H','ZOOM','SCALE']:constants[t.id]=ast.literal_eval(n.value)
    for step in [90,91,92,93]:
        r=rr[step-1];comp=components(frames[step-1]);assert [c['metric'] for c in comp]==r['tracker']['direct']
        assert r['pre_physical']==rr[step-2]['post_physical']
        assert hashlib.sha256(frames[step-1].tobytes()).hexdigest()==r['actor_state']['previous_image_sha256']
        for j,c in enumerate(comp):
            born=r['support_record']['births'][j];assert born['uid']==[step,j] and born['point']==c['metric']
            index=next(k for k,e in enumerate(r['support_record']['after']) if e['uid']==[step,j]);assert r['tracker']['after'][index]==c['metric']+[0]
            assert lineage['records'][step-1]['tags'][index]==f'{step}:{j}' and lineage['records'][step-1]['points'][index]['mode']=='direct_birth'
            gt=r['pre_physical'];body=gt['obstacles'][2]['body'];localpos=gt['obstacles'][2]['fixture']['geometry']['pos'];assert localpos==[0.0,0.0]
            # Independently derive ideal pixel-center projection from source camera.
            dx,dy=np.asarray(body['position'])-np.asarray(gt['hull']['position']);a=-gt['hull']['angle'];sx=np.cos(a)*dx-np.sin(a)*dy;sy=np.sin(a)*dx+np.cos(a)*dy;zoom=constants['ZOOM']*constants['SCALE'];W,H=constants['WINDOW_W'],constants['WINDOW_H']
            surface_x=W/2+zoom*sx;surface_y=H-1-(H/4+zoom*sy);projected=np.array([(surface_x+.5)*84/W-.5,(surface_y+.5)*84/H-.5]);assert np.allclose(projected,pixels(centers(gt))[2],rtol=0,atol=1e-12)
            assert np.allclose(pixels(np.asarray(c['metric'][:2])),c['centroid'],rtol=0,atol=1e-12)
            dist=np.linalg.norm(centers(gt)-np.asarray(c['metric'][:2]),axis=1);radii=np.asarray([o['fixture']['radius'] for o in gt['obstacles']]);supported=np.flatnonzero(dist<=radii).tolist();assert supported==[2]
            mask=np.zeros((84,84),np.uint8);xy=np.asarray(c['pixel_xy']);mask[xy[:,1],xy[:,0]]=1;ring=(cv2.dilate(mask,np.ones((3,3),np.uint8))!=0)&(mask==0);image=frames[step-1].astype(np.float32)/255;road=((image>.32)&(image<.47)).astype(np.uint8);road[61:]=0
            padded=np.pad(mask,1);complete_ring=(cv2.dilate(padded,np.ones((3,3),np.uint8))!=0)&(padded==0);missing=int(complete_ring.sum()-ring.sum());neighbors=int(road[ring].sum());assert neighbors==born['raw_road_neighbors']
            radius=radii[2];ellipse=np.sum(((xy-projected)/np.array([zoom*84/W*radius,zoom*84/H*radius]))**2,axis=1);assert np.all(ellipse<=1)
            item=dict(action=step,uid=born['uid'],age=0,current_direct=True,area_pixels=c['area'],touches_left_boundary=c['bbox'][0]==0,road_neighbors=neighbors,low=born['low'],observed_ring_pixels=int(ring.sum()),outside_unobserved_ring_positions=missing,ring_gray_range=[int(frames[step-1][ring].min()),int(frames[step-1][ring].max())],fixture_supported_ids=supported,fixture_center_distance_m=float(dist[2]),fixture_radius_m=float(radius),all_component_centers_inside_projected_fixture=True,coordinate_roundtrip_and_independent_camera_passed=True)
            local.append(item);detail.append(dict(summary=item,component=c,projected_fixture_center=projected.tolist(),tracker_record=r['tracker'],support_record=r['support_record'],lineage=lineage['records'][step-1]))
    r=rr[91];e=r['routing_evidence'];assert e['removed_indices']==[1] and e['removed_evidence'][0]['uid']==[92,0] and r['tracker']['after'][1][3]==0
    associations=[a for step in [92,93] for a in lineage['records'][step-1]['associations'] if a['old_tag'] in ['91:0','92:0']];assert [(a['old_tag'],a['new_tag']) for a in associations]==[('91:0','92:0'),('92:0','93:0')]
    held=[x['step'] for x in rr if any(item['uid']==[92,0] for item in x['routing_evidence']['removed_evidence'])];assert held==[92]
    save(D/'provenance-coordinate-private.json',dict(local_details=detail,associations=associations,lineage_max_error=lineage['maximum_reconstruction_error']))
    inp=dict(images=str(D/'image92-private.npz'),members_sha256=cfg['members_sha256'],states=[dict(label='355_T2954',step=92,features=r['features'],pixel_path=r['pixel_path'],routing_hazards=[h[:3] for h in e['routing_hazards']],full_hazards=[h[:3] for h in e['full_hazards']])]);np.savez_compressed(D/'image92-private.npz',images=np.asarray([frames[91].astype(np.float32)/255]));(D/'image92-private.npz').chmod(0o600);save(D/'function-input-private.json',inp)
    for f,h in plan['source_hashes'].items():assert sha(f)==h,f
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='');env.pop('PYTHONPATH',None)
    subprocess.run([str(G/'.venv/bin/python'),'-I','-B',str(G/'retry/link348_functions.py'),'--package',str(package),'--input',str(D/'function-input-private.json'),'--output',str(D/'function-output-private.json')],env=env,check=True)
    out=read(D/'function-output-private.json');assert out['calls']==dict(routing=2,target=2);comparison=out['records'][0];same=not comparison['path_changed'] and not comparison['target_changed']
    control=dict(actual_record_preserved=True,route_changed=comparison['path_changed'],target_changed=comparison['target_changed'],full_hazards_schedule_count_min_distance_unchanged=True,same_pixels_speed_previous_steer_precontroller=True,new_controller_or_actor_calls=0,conclusion='No same-call action/audit/nominal-memory change follows by deterministic frozen-source dependency: samepath/target => samepathlength/count, nominalfeatures/controlleroutput, scaledpedals andH1inputs.' if same else 'Route/target changes; fullcontrol effect unresolved underthisfunction-onlybudget.',evidence_type='Source-dependency inference with actualoriginalroute/target reproduction, not a separatelyexecutedcounterfactualcontroller orclosedloop.',closed_loop_harm_or_lap_effect_identified=False)
    gate=dict(public_source='retry/support342_stage.py:64',exact_requirement='Any fixture-supported direct or birth-supported retained point withheld, any reproduction/integrity failure: stop, no candidate pass.',implementation_sources=['retry/support342_run.py:55','retry/support342_run.py:58','retry/support342_run.py:59'],definition='Fixture support: birthpoint liesinsideexactlyonecapturedcircle in preactionego frame. Directbirth and birth-supportedretained routing exclusions forbidden; semanticmaterial/occlusiontruth unverified.',violation='92:0is a freshage0directbirth and geometricallysupportedatbirth92. Originalrulefiltersit immediately. Not a pastunsupportedlineage gainingcurrentGTsupport and not coordinate/time-labeldrift. The existingdirectbirth check andremoved-evidence check bothflagthesame UID; oneexcludedfootprint, nottwoindependentlosses.',unchanged_route_does_not_waive_gate=True,full_tracker_deletion=False)
    proposal=dict(status='Hypothesis/contract only; not applied to code, archive, metadata or replay.',single_policy_change='Only hard-routing selection: exclude a low-birth-flag point iff its existing tracker age>0. Always retain currentage0direct detections in routing. Birthpredicate, detector, metadata/association/expiry, fullhazardfeatures, H1/controller/fallback unchanged; no newnumericthreshold orGTinput.',why='Currentdirect imageevidence mustnotbe hardvetoed solelyby a zeroonepixelroad ring, especiallywhenborderclipping andmidgrayhalo make supportunobservable. Distinguishcurrentdirect fromagedretention.',predictions='Saved92is age0so would bepreserved; criticalknownN2routing121lineageat127-129hasage6-8so would remaineligible. Predictions only, no modifiedrule execution. Otherfreshlowbirths andnormalmemoryeffects mustbeverified.',limitations='Not a complete safetyfix: a genuine lowflagbirth mightsurvivewithoutredetection and laterbeexcluded asretained. The originalbirth-supportedretained gate remainsmandatory; preserving92alone isinsufficient. Border-onlyexemption isnotchosen: itwouldalsoprotect a knownN2topboundaryunresolvedbirth andrisksremovingtheknownroutingeffect.',validation=dict(stage1='Freezeprivatevariantcopywithonlythisselectionchange; preserve349/296. AuditactualroutingUIDmembership onexisting342corpus+355, direct andbirth-supportedretained separately. GTposthoconly. Lowmetadatalabel isnot itselfexclusion undernewguard: checkactualroutingmembership withoutweakeningtheoriginalwithheld-point requirement. Any supportedretained exclusion fails andstops.',stage2='Only afterstage1, boundedfrozenfunctioncheck at savedT295492andN2121: reproduceoldroute/target thennewselection; cap4directrouting+4directtargetentries, actor/controller/native0. N2127-129inputselection mustremainidenticalbyageUIDaudit. Baselinereproductionmismatch orloss ofrequiredknownN2effect stops, no thresholdrepair/sweep.',stage3='Stateful replay ornewclosedloop only if a distinctunresolvedmemory/trajectoryquestion survives, withseparatepreregisteredcaps. Not authorized orscheduled here.'),native_execution_now=0,actor_execution_now=0)
    for f,h in plan['source_hashes'].items():assert sha(f)==h,f
    v=read(R/'project-effective-budget-v369.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1285867,1644,84000,0)
    cost=dict(stage=356,new_wrapper_actions=0,new_actor_calls=0,new_controller_calls=0,new_environment_resets=0,new_learning_fits=0,candidate_modifications=0,direct_routing_entries=2,direct_target_entries=2,metadata_updates=94,tracker_lineage_updates=94,new_paid_resources=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,function_wall_s=out['wall_s'],function_CPU_s=out['CPU_s'],actual_cumulative_wrapper_actions=1285867,research_remaining=1644,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1371511,scope='Directentry counts; internalroute_targetcandidateevaluations includedinroutingcomputation, notseparatelycounted. Read-onlymetadata/coordinateaudit andtwo frozenfunctionvariants; no simulation. Preparation/git/taskwall notfullytimed.')
    report=dict(stage=356,classification='Freshcurrentdirect age0detectorbirth at92, geometricallymatchingfixture2; previous91birthdedup-replaced, new93directredetection replaces92. No coordinate/time-labelbug found; semanticpixelmaterial lacksauthoritativeRGBmask.',local_support=local,exclusion_actions=held,dedup_association_distances_m=[a['distance_m'] for a in associations],source_evidence='Leftviewport-clippedcomponent. At92observedonepixelring has8samples,4positionsoutsideimageunknown, allobservedringgray136-161above rawroadband. Nearbyrawroad existsfartherthanonepixel. Thuszero-ringcount isnot evidenceofnon-obstacle; resampling/antialiashalo isconsistentwithsourcepipeline butnotindependentlyrerendered.',routing_and_control=control,gate=gate,smallest_modification_hypothesis=proposal,privacy='Rawpixels/crops, privateposes/GT, seeds, models andpersonaldocuments stayprivate. Onlyderivedaggregates/sourcequotes andgenericcode published.',cost=cost,champion296_preserved=True,promotion=False,new_protected_split_opened=False,modified_hypothesis_applied=False)
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/boundary356_result.json',report);save(D/'final-report-verification.json',dict(passed=True,directbirth_not_retained=True,current_and_birthsupport_sameframe=True,coordinate_and_time_alignment_passed=True,oneframe92only=True,originalroute_target_reproduced=True,source_inferred_control_no_change=same,new_actor_native_learning_candidate_modification=0,preservation_gate_still_failed=True,research_remaining=1644,final_reserve=84000,hypothesis_not_applied=True))
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    v.update(version=370,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v369.json'),prior_budget_sha256=sha(R/'project-effective-budget-v369.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage356_new_wrapper_actions=0);assert not (R/'project-effective-budget-v370.json').exists();save(R/'project-effective-budget-v370.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==356 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(classification=report['classification'],local=local,held=held,routing_control=control,cost=cost,hypothesis_applied=False)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
