"""474 registered saved-only source/raw analysis. No new physics is authorized."""
import datetime,hashlib,json,math,os,platform,shutil,subprocess,sys,time
from fractions import Fraction
from pathlib import Path

G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage474-private')
MIB=1024**2
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
    with Path(p).open('x') as handle:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
    Path(p).chmod(0o600)

def prospective_cost(root):
    old=read(root/'stage473/plan.json');semantic=dict(old['semantic_sources'])
    for name in ['audit474_run.py','audit474_controls.py','audit474_traces.py']:semantic[str(G/'retry'/name)]=sha(G/'retry'/name)
    growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode()))
    headers={}
    for stage in ['stage472','stage473']:
        directory=root/stage
        headers[stage]={k:max((p.stat().st_size for p in directory.glob(pattern)),default=0) for k,pattern in [('constructor','world*-before-constructor-private.json'),('first_step','world*-before-first-step-private.json'),('runtime_link','*-runtime-link-private.json'),('own_reference','*-own-reference-before-constructor-private.json')]}
    base=sum(max(h[k] for h in headers.values()) for k in headers['stage473']);header=base+3*(growth+8192)+16384
    samples=[(126087848,1353),(503172296,5461),(140364368,1881),(138331916,1671)];rate=max(Fraction(a,b) for a,b in samples)
    native=read(root/'stage471/contract-private.json')['storage']['native_source_samples'];rawrate=max(Fraction(x['bytes'],x['raw_ticks']) for x in native);actionrate=max(Fraction(x['bytes'],x['actions']) for x in native)
    def native_bytes(actions,resets):
        # Fixed source empirical maxima, no guessed compression or deletion.
        return math.ceil(max((actions*4+resets*51)*rawrate,actions*actionrate+resets*51*rawrate)*Fraction(5,4)+resets*(16+32)*MIB)
    free={v:shutil.disk_usage(v).free for v in ['/tmp','/workspace']};variants={}
    for name,planned,worlds,hard,hardworlds,actions,resets,cpu,wall in [
        ('whole_model_pair',3674,49,4096,49,0,0,300,600),
        ('single_native_bridge',27674,547,32768,576,272,1,1800,2400),
        ('fresh_native_pair',53674,1047,65536,1088,544,2,3600,4800)]:
        model=math.ceil(hard*rate*Fraction(5,4)+hardworlds*header+18*MIB);nat=native_bytes(actions,resets) if actions else 0;required=model+nat+32*MIB+512*MIB
        variants[name]=dict(planned_model_ticks=planned,planned_model_worlds=worlds,hard_model_ticks=hard,hard_model_worlds=hardworlds,actual_actions_cap=actions,resets_cap=resets,whole_CPU_cap_s=cpu,whole_wall_cap_s=wall,model_raw_forecast_bytes=model,native_raw_forecast_bytes=nat,tmp_required_bytes=required,tmp_free_bytes=free['/tmp'],tmp_shortage_bytes=max(0,required-free['/tmp']),workspace_required_bytes=64*MIB+512*MIB,workspace_free_bytes=free['/workspace'],workspace_shortage_bytes=max(0,64*MIB+512*MIB-free['/workspace']),execution_authorized=False)
    return dict(qualification=dict(source=dict(ticks=1242,worlds=35),root_Original_oldP4_changedP4=dict(ticks=324,worlds=9),changed_pending_pair_and_held=dict(ticks=108,worlds=3),total=dict(ticks=1674,worlds=47)),
                arithmetic='whole:1674+2*250*4=3674,47+2=49; one native:1674+250*2*13*4=27674,47+500=547; native pair:1674+500*2*13*4=53674,47+1000=1047',
                model_bytes_per_tick=float(rate),model_rate_samples=samples,observed_header_parts=headers,latest_header_base_bytes=base,actual_source_manifest_growth_bytes=growth,prospective_additional_manifest_allowance_bytes=8192,header_bytes_each=header,empirical_margin=1.25,native_bytes_per_raw_tick=float(rawrate),native_bytes_per_action=float(actionrate),variants=variants,
                conditions='Prospective only; all physical auxiliary counted conservatively. A future implementation must re-register actual sources, adapter/pending fixtures, ticks/worlds, time, exact current free and full raw cost before any integration. No unused headroom authorizes extra worlds.')

def prepare(root):
    root=Path(root);d=root/'stage474';assert not d.exists() and not d.is_symlink() and not RAW.exists()
    from retry.audit474_controls import SOURCES,HISTORICAL,HISTORICAL_PATH
    from retry.audit474_traces import source_paths
    previous=read(root/'stage473/plan.json');ledger=root/'project-effective-budget-v476.json';v=read(ledger)
    assert v['stage472_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26175,84000,0)
    correction=root/'stage441/authorization-correction-private.json';assert sha(correction)==previous['authorization_extension_sha256']
    assert read(root/'research-deadline-current.json')['deadline_utc']=='2026-10-20T10:01:55Z'
    files=set(source_paths(root))|{G/n for n in SOURCES}|{G/'retry'/n for n in ['audit474_run.py','audit474_controls.py','audit474_traces.py','retain474.py','retain472.py','receipt421_io.py','pilot420_json.py']}
    files.update([ledger,correction,Path(previous['projection_path']),root/'stage473-retention-manifest-private.json',root/'stage471/contract-private.json'])
    historical=subprocess.check_output(['git','show',HISTORICAL+':'+HISTORICAL_PATH],cwd=G)
    history=root/'stage474-static-control-audit-input-private.md'
    with history.open('xb') as handle:handle.write(historical)
    history.chmod(0o600);files.add(history)
    inputs=root/'stage474-input-material-private.json'
    put(inputs,dict(fixed=read(previous['fixed_plan']),frozen_P4_projection=read(previous['projection_path']),source_input_manifest={str(f):dict(bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(files)},historical_git_object=HISTORICAL+':'+HISTORICAL_PATH,clock_rules=dict(raw_dt_s=.02,wrapper_hold_s=.08,pre23_physical_s=2.78,reset_complete_s=1.02,pre23_elapsed_s=1.76),raw_inputs='Original existing complete input traces remain in their registered locations; never copy/delete/move/transform. Derived474 evidence has one new copy in/tmp. Workspace material preserves full small geometry/profile plus complete input identity and conditions.'))
    files.add(inputs);reserve=512*MIB;required=256*MIB+32*MIB+reserve;free={v:shutil.disk_usage(v).free for v in ['/tmp','/workspace']}
    assert free['/tmp']>=required and free['/workspace']>=64*MIB+reserve
    p=dict(stage=474,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mode='SAVED_ONLY_SOURCE_AND_RAW_ANALYSIS',new_model_worlds=0,new_model_ticks=0,new_native_actions=0,new_resets=0,new_actor_calls=0,
           sources={str(f):sha(f) for f in sorted(files)},protected=previous['protected'],original408_preserve=previous['original408_preserve'],ledger_path=str(ledger),ledger_sha256=sha(ledger),input_material_path=str(inputs),input_material_sha256=sha(inputs),
           deadline_utc='2026-10-20T10:01:55Z',authorization_extension_path=str(correction),authorization_extension_sha256=sha(correction),
           storage=dict(derived_raw_allowance_bytes=256*MIB,verification_temp_bytes=32*MIB,reserve_each_bytes=reserve,tmp_required_bytes=required,workspace_required_bytes=64*MIB+reserve,free_bytes=free,new_archive_created=False,workspace_new_raw_copies=0),
           selected_windows='Two existing473 first failures ±30m on same canonical line, post-hoc diagnostic only. Native472 and442C0/P matched spatially; no simulated or interpolated state.',
           future_contract_scope='At most two explanations; one steering-prefilter-removal proposal conditional on saved evidence. No future physics execution is authorized.',prospective_cost=prospective_cost(root),
           reproduction=dict(python=sys.version,platform=platform.platform(),git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),commands=['python -m retry.audit474_run run ROOT'],new_paid_resources=0),
           preservation='All original raw/archive/files and fixed safety thresholds preserved. If /tmp is lost exact raw cannot be reverified; hashes cannot reconstruct raw.')
    for group in ['protected','original408_preserve']:
        for filename,h in p[group].items():assert sha(filename)==h
    RAW.mkdir(mode=0o700);d.symlink_to(RAW,target_is_directory=True);put(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');put(root/'stage474-plan-durable-private.json',p)
    print(json.dumps(dict(stage=474,phase='PLAN_FROZEN_SAVED_ONLY',plan_sha256=sha(d/'plan.json'),storage=p['storage'],prospective_variants=p['prospective_cost']['variants'])))

def run(root):
    root=Path(root);d=root/'stage474';p=read(d/'plan.json');assert not(d/'opening-private.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for group in ['sources','protected','original408_preserve']:
        for filename,h in p[group].items():assert sha(filename)==h,filename
    put(d/'opening-private.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_verified=True,new_physics=0))
    cpu=time.process_time();wall=time.perf_counter()
    from retry.audit474_controls import run as controls
    from retry.audit474_traces import analyze as traces
    c=controls(root,d);t=traces(root,d)
    assert t['physics']==dict(new_models=0,native_steps=0,resets=0,SourceC_act_calls=0,import_guard_attempts=[])
    for group in ['sources','protected','original408_preserve']:
        for filename,h in p[group].items():assert sha(filename)==h,filename
    size=sum(f.stat().st_size for f in d.iterdir() if f.is_file());assert size<p['storage']['derived_raw_allowance_bytes']
    q=dict(stage=474,status='SAVED_ONLY_ANALYSIS_COMPLETE',plan_sha256=sha(d/'plan.json'),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_model_ticks=0,new_model_worlds=0,new_native_actions=0,new_resets=0,new_actor_calls=0,import_guard_attempts=t['physics']['import_guard_attempts'],ledger_unchanged=sha(p['ledger_path'])==p['ledger_sha256'],sources_preserved=True,protected18_preserved=True)
    put(d/'result.json',q);print(json.dumps(q))

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
