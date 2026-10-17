"""Saved evidence only. Reads442/458/463; constructs no models or environments."""
import hashlib,json,math,shutil,time
from pathlib import Path
import numpy as np
from retry.design464_math import saved_secant_terms,calculate

def run(root):
    cpu,wall=time.process_time(),time.perf_counter();g=Path(__file__).resolve().parents[1];manifest={}
    def read(path,lines=False):
        data=path.read_bytes();manifest[str(path)]=hashlib.sha256(data).hexdigest()
        return [json.loads(s) for s in data.splitlines()] if lines else json.loads(data)
    plan=read(root/'stage453/plan.json');fixed=read(Path(plan['fixed_plan']));pace=np.asarray(read(Path(plan['pace_path']))['frozen268'])
    contract=read(g/'retry/design464_next.json');v=read(root/'project-effective-budget-v475.json')
    assert v['stage463_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26346,84000,0)
    preserved=read(root/'stage463-plan-durable-private.json')
    for group in ['protected','original408_preserve']:
        for path,digest in preserved[group].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    prior=read(g/'retry/structural461_result.json');actual=read(g/'retry/transfer463_result.json');assert actual['official_lap_gain_s']==.22
    traces=dict(P442=root/'stage442/actual_P/trace-private.jsonl',P458=root/'stage458/actual_P/trace-private.jsonl',Original463=root/'stage463-native/actual_Original/trace-private.jsonl',PulseOnce463=root/'stage463-native/actual_SecantOnce/trace-private.jsonl')
    public={};private={}
    for label,path in traces.items():
        rows=read(path,True);terms=[dict(step=row['step'],**saved_secant_terms(fixed,pace,row)) for row in rows]
        valid=[t for t in terms if t['eligible']];window=[t for t in valid if 126<=t['step']<=138];changed=[t['step']-125 for t in window if t['changed_from_dispatched']]
        public[label]=dict(eligible_saved_actions=len(valid),changed_from_nominal=sum(t['changed_from_nominal'] for t in valid),crossed_node_actions=sum(t['crossed_nodes']>0 for t in valid),interior_valley_actions=sum(t['interior_reference_valley'] for t in valid),endpoint_drives_despite_interior_target_below_speed=sum(t['endpoint_drives_despite_interior_target_below_speed'] for t in valid),ineligible_saved_actions=len(terms)-len(valid),root13_changed_from_dispatched_relative_actions=changed)
        if label in ['Original463','PulseOnce463']:
            subset=rows[125:138];assert len(subset)==13 and all(t['eligible'] for t in window)
            public[label].update(root13_observed_progress_m=subset[-1]['progress_after']-subset[0]['progress_before'],root13_observed_duration_s=subset[-1]['post']['time']-subset[0]['pre']['time'])
            if label=='PulseOnce463':
                first=next(t for t in valid if t['step']==126);assert not first['changed_from_dispatched'] and first['gas']==1 and first['brake']==0
                assert any(n>1 for n in changed),'S13 has no additional saved-state intervention'
                assert all(row['command']==row['nominal'] for row in subset[1:]),'PulseOnce control must be first pulse then original nominal'
        private[label]=terms
    stages={};rates=[];headers=[]
    for stage,ticks in [(462,10766),(463,10375)]:
        folder=root/f'stage{stage}';files=[f for f in folder.resolve().rglob('*') if f.is_file()];total=sum(f.stat().st_size for f in files)
        retained=read(root/('stage462-retained/retention-result.json' if stage==462 else 'stage463-retained-recovery1/retention-result.json'))
        measured=retained['uncompressed_bytes'] if stage==462 else retained['uncompressed_bytes_by_volume']['model']
        rate=measured/ticks;rates.append(rate);fixedmax={}
        for pattern in ['world*-before-constructor-private.json','world*-before-first-step-private.json','*-runtime-link-private.json']:
            matched=list(folder.glob(pattern));fixedmax[pattern]=max(f.stat().st_size for f in matched)
        headers.append(sum(fixedmax.values()));stages[str(stage)]=dict(retained_raw_bytes=measured,ticks=ticks,bytes_per_tick=rate,fixed_max_bytes=fixedmax,fixed_sum_bytes=sum(fixedmax.values()),current_raw_file_bytes=total)
    assert contract['storage']['observed_max_model_bytes_per_tick']>=max(rates)
    assert contract['storage']['observed_fixed_bytes_per_world']>=max(headers)
    cost=calculate(contract);disk={p:dict(total=shutil.disk_usage(p).total,used=shutil.disk_usage(p).used,free=shutil.disk_usage(p).free) for p in ['/tmp','/workspace']}
    ratio=prior['profile']['lateral_accel_ratio_to_base_allowance_max'];friction_fraction=.4*ratio
    source_paths=['retry/design464_math.py','retry/analyze464.py','retry/static464.py','retry/design464_next.md','retry/signed417_executor.py','retry/scalar392_audit.py','retry/pilot420_backend.py','retry/guardian426_confirmed.py','retry/pilot436_run.py','retry/pilot428_run.py','retry/observer435.py','retry/planner419.py','retry/paired417_common.py','retry/racing258_plan.py','retry/racing258_run.py','retry/pace268_profile.py','core/vendor/car_dynamics.py']
    source_hashes={}
    for rel in source_paths:
        path=g/rel;source_hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest();manifest[str(path)]=source_hashes[rel]
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in manifest.items())
    d=root/'stage464';assert not d.exists(),'preserve each saved analysis attempt';d.mkdir(mode=0o700)
    def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
    save(d/'input-sha256-private.json',manifest);save(d/'saved-proposals-private.json',private)
    result=dict(stage=464,status='SAVED_ANALYSIS_AND_DESIGN_ONLY',new_actual_actions=0,new_model_ticks=0,new_worlds=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,
        source_hashes=source_hashes,private_manifest_sha256=hashlib.sha256((d/'input-sha256-private.json').read_bytes()).hexdigest(),input_files=len(manifest),protected_files_verified=18,
        best_native_s=13.760,latest_native_s=13.780,best_updated=False,single_pulse_native_gain_s=.220,model462_gain_bracket_s=[.20,.24],
        H2A_prior_reference_summary=prior['profile'],H2A_lateral_interpretation=dict(base_allowance_fraction_of_nominal_aggregate_friction=.4,max_demand_fraction_under_same_pointmass_allroad_grip1_assumptions=friction_fraction,aggregate_longitudinal_remaining_fraction_at_that_same_proxy_point=math.sqrt(max(0,1-friction_fraction**2)),exact_tyre_or_path_feasibility_certified=False),
        saved_proposal_summary=public,storage_observations=stages,current_storage=disk,selected_future_cost=cost,execution_authorized=False,
        ledger=dict(version=475,research_remaining=26346,actual_cumulative_wrapper_actions=1321718,reserve=84000,reserve_used=0),deadline_utc='2026-10-20T10:01:55Z',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    save(d/'result-private.json',result);return result
