"""Read existingTRAIN count semantics; no candidate/threshold/model execution."""
import ast,datetime,json,math,time,sys,zipfile,itertools
from pathlib import Path
from collections import Counter
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import advance
from retry.confidence341_run import label
G=Path(__file__).resolve().parent.parent

def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def array_literals(source):
 out={}
 for node in ast.parse(source).body:
  if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='array':
   for target in node.targets:
    if isinstance(target,ast.Name):out[target.id]=np.array(ast.literal_eval(node.value.args[0]),float)
 return out

def summarize(rr):
 total=Counter();same=[];distinct=[]
 for x in rr:
  total.update(x['counts']);same.extend(x['same_fixture_birth_pair_distances']);distinct.extend(x['different_fixture_birth_pair_distances'])
 def dist(v):return dict(count=len(v),min=min(v) if v else None,median=float(np.median(v)) if v else None,max=max(v) if v else None)
 a,b=dist(same),dist(distinct);return dict(contexts=len(rr),totals=dict(total),same_fixture_birth_pair_distance_m=a,different_fixture_birth_pair_distance_m=b,pair_distance_ranges_overlap=bool(same and distinct and max(min(same),min(distinct))<=min(max(same),max(distinct))),single_distance_threshold_cannot_separate_all_labeled_pairs=bool(same and distinct and max(same)>=min(distinct)),scope='Repeatedcontexts/birth-compatiblefixtures,notindependentobjects,notcurrentsemanticIDtruth. UnknownbirthsnevernegativeGT;no thresholdchosenornewcountmappingcomputed.')

def run(R):
 D=R/'stage379';assert not D.exists();D.mkdir(mode=0o700);wall,cpu=time.perf_counter(),time.process_time();v=read(R/'project-effective-budget-v396.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1312121,35943,84000,0,1432064)
 base=read(R/'stage296/champion-config.json');variant=read(R/'stage374/config-private.json');assert sha(base['archive_path'])==base['archive_sha256'] and sha(variant['archive_path'])==variant['archive_sha256']
 with zipfile.ZipFile(base['archive_path']) as z:
  model=array_literals(z.read('retry/submission232_model.py').decode());scales=array_literals(z.read('retry/scale238_model.py').decode())['SCALES'];source=z.read('retry/nominal238_base.py').decode();assert 'float(len(obstacles))' in source and 'standardized' in source
 assert model['HEAD_WEIGHTS'].shape==(17,2) and model['HEAD_STD'].shape==(16,) and np.all(model['HEAD_STD']>0) and np.all(scales>0);slope=model['HEAD_WEIGHTS'][11]/model['HEAD_STD'][11];save(D/'model-count-derivative-private.json',dict(head_module_sha256=base['members_sha256']['retry/submission232_model.py'],raw_residual_per_count=slope.tolist(),positive_final_scales=scales.tolist(),scope='Parameteralgebraonly,no modelforwardcall,no replacementmodel/candidate. Exactvaluesremainprivate.'))
 sources=[G/'retry/count379_review.py',G/'retry/fallback334_math.py',G/'retry/confidence341_run.py',G/'retry/lineage339_audit.py',R/'stage296/champion-config.json',R/'stage374/config-private.json',Path(base['archive_path']),Path(variant['archive_path']),R/'stage375/plan.json',R/'stage376/plan.json',R/'project-effective-budget-v396.json',R/'current-champion.json',R/'stage296/champion-manifest.json',R/'stage373/candidate365-rejected-locked.json',R/'protected-query-ledger-v1.json']
 # Full-method/feature-lineage metadata only; no protectedsplitperformanceused.
 names=['pixel_residual224','pixel_residual225','pixel_residual226','pedal_mode228','aggregate229','aggregate230','single231','submission232','addition237','conditional242','counterfactual245','counterfactual246','hud248','ablation279','ablation298','h1_330','lineage339','support342','package349','guard357','history365','fallback375','diagnosis376','control377','pedal378']
 for name in names:
  f=G/'retry'/(name+'_result.md')
  if f.exists():sources.append(f)
 for name in ['pixel_residual224_fit','aggregate229_fit','single231_fit','submission232_agent','conditional242_agent','hud248_fit','ablation279_prepare','ablation298_prepare','lineage339_audit','support342_stage','package349_stage']:
  f=G/'retry'/(name+'.py')
  if f.exists():sources.append(f)
 corpus=[]
 for key in ['T2950','T2953','T2956','T2959','O0','O2']:
  F=R/'stage334'/key;corpus.append(dict(group='296_old6_saved_replay',key=key,records=F/'OFF-private.jsonl',GT=F/'GT-private.json',format='334',enabled=False));sources += [F/'OFF-private.jsonl',F/'GT-private.json']
 order=read(R/'stage375/plan.json')['all18_order']
 for key in order:
  F=R/'stage374/B' if key=='T2950' else R/'stage375'/key/'B';corpus.append(dict(group='374_actual18',key=key,records=F/'trace-private.jsonl',GT=None,format='actual',enabled=True));sources += [F/'trace-private.jsonl',F/'result.json']
 F=R/'stage377/A';corpus.append(dict(group='296_actual_T29510_control',key='T29510',records=F/'trace-private.jsonl',GT=None,format='actual',enabled=False));sources += [F/'trace-private.jsonl',F/'result.json']
 for mode in ['296','374']:sources.append(R/'stage376'/mode/'records-private.jsonl')
 protected={str(f):sha(f) for f in [R/'current-champion.json',R/'stage296/champion-manifest.json',R/'stage373/candidate365-rejected-locked.json',R/'protected-query-ledger-v1.json',R/'project-effective-budget-v396.json']};excluded={str(f):f.stat().st_mtime_ns for f in [R/'stage372',R/'stage297']};plan=dict(stage=379,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='ReadexistingTRAIN334old6/374actual18/377T29510and376fixedinputrecords;oldmethodsource/metadataonly. No env/actor/model-forward/fit/candidate/count-ruleimplementation/thresholdsearch/newsplit/372data.',source_hashes={str(f):sha(f) for f in sources},protected_hashes=protected,excluded_directory_stats=excluded);save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
 contexts=[];cases=[]
 for case in corpus:
  data=rows(case['records']);gt={int(k):v for k,v in read(case['GT']).items()} if case['GT'] else None;nodes=[];rr=[]
  for i,x in enumerate(data):
   t=x['tracker'];f=x['features'];truth=gt.get(i) if gt is not None else x['pre_physical'];rebuilt,lin,_=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],case['enabled']);assert np.allclose(np.asarray(rebuilt).reshape(-1,4),np.asarray(t['after']).reshape(-1,4),atol=1e-12,rtol=0);new=[]
   for parent in lin:
    if parent>=0:node=nodes[parent]
    else:
     lab,idx=label(t['direct'][-parent-1],truth);node=dict(label=lab,fixture_index=idx)
    new.append(node)
   nodes=new;haz=t['after'];assert f[11]==len(haz);minimum=min((math.hypot(h[0],h[1]) for h in haz),default=100.);assert abs(minimum-f[12])<1e-12;lookahead=float(np.clip(4+.35*f[3],6,14));near=any(h[1]>0 and math.hypot(h[0],h[1])<=lookahead+2.6+h[2] for h in haz);assert bool(f[8])==near
   known=[j for j,n in enumerate(nodes) if n['label']=='fixture_supported'];ids=Counter(nodes[j]['fixture_index'] for j in known);duplicate=any(n>1 for n in ids.values());direct=[j for j,h in enumerate(haz) if h[3]==0];retained=[j for j,h in enumerate(haz) if h[3]>0];retained_only_ids=[k for k in ids if not any(nodes[j]['label']=='fixture_supported' and nodes[j]['fixture_index']==k for j in direct)];same=[];different=[];pairtypes=Counter()
   for j,k in itertools.combinations(known,2):
    distance=math.hypot(haz[j][0]-haz[k][0],haz[j][1]-haz[k][1])
    if nodes[j]['fixture_index']==nodes[k]['fixture_index']:
     same.append(distance);typ='DD' if haz[j][3]==haz[k][3]==0 else 'RR' if haz[j][3]>0 and haz[k][3]>0 else 'DR';pairtypes[typ]+=1
    else:different.append(distance)
   counts=dict(raw_hazard_point_contexts=len(haz),direct_point_contexts=len(direct),retained_point_contexts=len(retained),fixture_birth_supported_point_contexts=len(known),unknown_point_contexts=sum(n['label']!='fixture_supported' for n in nodes),known_duplicate_frames=int(duplicate),known_duplicate_excess_point_contexts=sum(n-1 for n in ids.values()),known_multi_fixture_frames=int(len(ids)>1),known_retained_only_fixture_frames=int(bool(retained_only_ids)),known_retained_only_fixture_instances=len(retained_only_ids),raw_behind_or_zero_forward_point_contexts=sum(h[1]<=0 for h in haz),direct_outside_retention_window_point_contexts=sum(not(abs(haz[j][0])<=35 and -5<=haz[j][1]<=35) for j in direct),same_fixture_DD_pairs=pairtypes['DD'],same_fixture_DR_pairs=pairtypes['DR'],same_fixture_RR_pairs=pairtypes['RR'])
   item=dict(group=case['group'],TRAIN=case['key'],step=i+1,counts=counts,same_fixture_birth_pair_distances=same,different_fixture_birth_pair_distances=different);rr.append(item);contexts.append(item)
  cases.append(dict(group=case['group'],TRAIN=case['key'],summary=summarize(rr)))
 # Naturalcount-onlycontrastsalreadygeneratedin376,nopolicy/modelcallsnow.
 pair={mode:rows(R/'stage376'/mode/'records-private.jsonl') for mode in ['296','374']};isolated=[]
 for i,(a,b) in enumerate(zip(pair['296'],pair['374'])):
  x,y=a['response'],b['response'];changes=[j for j,(u,vv) in enumerate(zip(x['features'],y['features'])) if u!=vv]
  if changes==[11]:isolated.append(dict(step=i+1,count296=x['features'][11],count374=y['features'][11],steering_same=x['action'][0]==y['action'][0],gas_delta_374_minus296=y['action'][1]-x['action'][1],brake_delta_374_minus296=y['action'][2]-x['action'][2],path_same=x['pixel_path']==y['pixel_path'],target_same=x['features'][:3]==y['features'][:3],scope='Existing376fixed374pixelstraces,notnewcounterfactualexecutionornewconditions.'))
 grouped={group:summarize([x for x in contexts if x['group']==group]) for group in sorted(set(x['group'] for x in contexts))};overall=summarize(contexts)
 report=dict(stage=379,review_only=True,new_candidate_implemented=False,new_threshold_search=False,new_native_actions=0,new_actor_calls=0,new_model_forward_calls=0,model_algebra_only=True,count_feature_semantics=dict(index=11,definition='len(allcurrenttrackerpoints):direct+retained,allages/behind/outofretentionwindowdirectbirths;notuniquephysicalobjectsandnotGTcount.',risk_roles=dict(near='Existenceofanyforwardtrackedcirclewithinexistinglookahead+2.6+radius;selectslateralsafebudget.',distance='Minimumhypotofalltrackedpoints,default100,notGTdistance/exclusivelyfront.',routing='Everyhazardfootprintparticipatesinexistingallowedmask/path;notcountscalar.',head='Oneof16standardizedaffinepedalresidualinputs;learnedstatisticalfeature,thenresidual/outputclipsandpositiveglobalscales.'),conditional_raw_count_derivative_sign=dict(gas=int(np.sign(slope[0])),brake=int(np.sign(slope[1])))),corpus=dict(trajectories=len(corpus),contexts=len(contexts),groups=grouped,overall=overall,scope='ExistingadaptiveTRAIN,repeatedprefixesandstalledframes.334isoldactual296pixelsreplayedalready,37418arenativeexisting,377onecontrol. Notindependent25trials/populationestimate.'),natural_count_only_contrasts_from376=isolated,prior_count_effect_not_new='339alreadycomparedrouting-onlyvsallhazard-derivedfeatures;countchangedpedalswithoutpathchange.242riskbasis,248featureaddition,279outputablation,298parameterablationnotcountrepresentation-onlywholeTRAIN.',dedicated_count_definition_only_full_native_ablation_found=False,absence_scope='Reviewedpublicresult/sourcefeaturelineages224-248/279/298/339/342/349/357/365/374-378andcodekeywordinventory,notproofeveryarchivedexperimentabsent.',source_only_safe_alternative_not_yet_justified=True,no372data_or_newsplit=True,champion296_unchanged=True,candidate365_rejected_unchanged=True,SEALED16_pending_preserved=True)
 save(D/'context-count-audit-private.json',contexts);save(D/'case-count-audit.json',cases);cost=dict(stage=379,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_model_forward_calls=0,new_candidate_implementations=0,new_threshold_search=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_paid_resources=0,audit_wall_s=time.perf_counter()-wall,audit_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1312121,research_remaining=35943,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1432064,scope='ReadoldTRAINJSON/immutablemodelparameteralgebra/GTbirth-labelpoint-pairdistancesonly;noforward/candidatecountfunction/thresholdfit. Coding/review/report/gitnotfullytimed.');report['cost']=cost
 for f,h in plan['source_hashes'].items():assert sha(f)==h,f
 for f,h in protected.items():assert sha(f)==h,f
 assert all(Path(f).stat().st_mtime_ns==h for f,h in excluded.items());assert not list(R.rglob('SEALED*.opened'));save(D/'summary-private.json',report);save(D/'cost.json',cost);save(G/'retry/count379_result.json',report);save(D/'final-report-verification.json',dict(passed=True,oldTRAINonly=True,no_actor_native_model_candidate_or_threshold_calls=True,protected_and_budget_unchanged=True,rawpoints_models_gt_private=True))
 v.update(version=397,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v396.json'),prior_budget_sha256=sha(R/'project-effective-budget-v396.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage379_new_wrapper_actions=0);assert not (R/'project-effective-budget-v397.json').exists();save(R/'project-effective-budget-v397.json',v);ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==379 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(groups=grouped,overall=overall,isolated_count_contrasts=isolated,cost=cost)),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
