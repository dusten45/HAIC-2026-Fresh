"""469 frozen two-parent follow-up and read-only storage gate; never physics."""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil

G=Path(__file__).resolve().parents[1]
R=Path('/workspace/haic-private-retry-20261009')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,value):
    with path.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def calculate(rate,header,growth,prospective_manifest=0):
    # Fraction keeps ceil(required)-free exact, including empirical1.25/1.1.
    fixed=header+3*(growth+prospective_manifest)+16384
    payload=2048*rate*Fraction(5,4)+43*fixed+2*1024**2+16*1024**2
    tmp=payload+512*1024**2
    workspace=payload*Fraction(11,10)+32*1024**2+512*1024**2+2*1024**2
    return dict(raw_payload_forecast_bytes=math.ceil(payload),header_per_world_with_growth_bytes=fixed,
        tmp_required_bytes=math.ceil(tmp),workspace_required_bytes=math.ceil(workspace),
        rounding='ceil final required bytes; rational1.25 and1.1')

def main():
    prior=json.loads((R/'stage468/plan.json').read_text())
    observed=json.loads((G/'retry/compare468_result.json').read_text())
    retained=json.loads((G/'retry/compare468_retention.json').read_text())
    assert observed['status']=='H13_COMPARISON_COMPLETE' and retained['workspace_private_archives_verified']
    assert observed['model_only_promotion_criterion_passed'] and not observed['actual_promotion']
    for group in ['sources','protected','original408_preserve']:
        for path,sha in prior[group].items():assert digest(path)==sha,path
    assert digest(prior['ledger_path'])==prior['ledger_sha256']
    latest=Fraction(retained['uncompressed_bytes_by_volume']['model'],observed['cost']['model_ticks'])
    rate=max(latest,Fraction(str(prior['storage_forecast']['observed_bytes_per_tick'])))
    d=R/'stage468'
    header_parts={
      'constructor_max':max(p.stat().st_size for p in d.glob('world*-before-constructor-private.json')),
      'first_step_max':max(p.stat().st_size for p in d.glob('world*-before-first-step-private.json')),
      'runtime_link_max':max(p.stat().st_size for p in d.glob('*-runtime-link-private.json')),
      'own_reference_max':max(p.stat().st_size for p in d.glob('*-own-reference-before-constructor-private.json'))}
    header=max(770314,sum(header_parts.values()))
    semantic=dict(prior['semantic_sources']);semantic[str(G/'retry/design469.py')]=digest(__file__)
    growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(prior['semantic_sources'],indent=2).encode()))
    # Current measured growth is separate from a bounded allowance for not-yet
    # implemented production modules. Even growth0 lower bound already fails.
    optimistic=calculate(rate,770314,0)
    measured=calculate(rate,header,growth)
    forecast=calculate(rate,header,growth,4096)
    free={p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}
    for name,cost in [('optimistic_no_new_growth',optimistic),('measured_current_sources',measured),('registered_future_allowance',forecast)]:
        cost['space']={p:dict(free_bytes=free[p],required_bytes=cost['tmp_required_bytes' if p=='/tmp' else 'workspace_required_bytes'],shortage_bytes=max(0,cost['tmp_required_bytes' if p=='/tmp' else 'workspace_required_bytes']-free[p])) for p in free}
    fits=all(v['shortage_bytes']==0 for v in forecast['space'].values())
    assert not fits,'Current task expects a proved pre-integration space stop; no execution entrypoint exists'
    contract=dict(stage=469,status='NOT_STARTED_STORAGE_GATE_FAILED',execution_authorized_by_this_file=False,
      question='Does fixed-root Projected4 common-pulse advantage survive through each own model finish?',
      deadline_utc='2026-10-20T10:01:55Z',deadline_KST='2026-10-20 19:01:55',
      authorization_extension_evidence_sha256=prior['authorization_extension_sha256'],
      prior_plan_sha256=digest(R/'stage468/plan.json'),frozen_profile_sha256=prior['projection_sha256'],
      root=dict(native_pre_step=126,same_as468=True,new_root_search=False),
      policy=dict(arms=['OriginalReferenceCommonPulse','Projected4ReferenceCommonPulse'],
        point_FF_feedback_steering_line_pedal_hold_unchanged=True,common_first_fullgas_vector=True,
        nodes_immutable_before_first_act=True,finish='unchanged SourceC phase and each own finish tracker',
        projected_FINISH_CONFIRM_target='own projected nodes[-1], no handoff to Original',
        query_guardian_rescue_ranking=0,safety='existing raw-tick physical/progress/numeric gates without relaxation',
        unsafe='close that fixed law and window; no neutral rescue or replacement law',
        unsupported_domain='technical stop with exact phase/state; do not invent finish/pending behavior'),
      qualification=dict(existing_integrated468_gate='fresh source/root gate unchanged:35+6worlds, <=1458ticks',
        source_worlds=35,root_independent_H13_and_held_worlds=6,
        independent_whole_arm_repetition=False,prior_H13_not_relabelled_as_whole_arm_repeat=True),
      whole_parent=dict(worlds=2,max_actions_each=70,max_raw_ticks_each=280,
        capture_held_auxiliary_extra_worlds=0,extra_ticks_after_pending_at_cap=0,
        observer='existing whole-parent observation with initial_count0; generic H13 observation only; no selector or child-tail barrier bypass'),
      planned=dict(qualification_ticks=1458,qualification_worlds=41,whole_parent_ticks=560,whole_parent_worlds=2,total_ticks=2018,total_worlds=43),
      hard=dict(ticks=2048,worlds=43,CPU_s=180,wall_s=300,actual_actions=0,resets=0),
      outcomes=dict(primary='each own official model event bracket confirmed by own tracker within70 actions',
        both_finished='Original bracket minus P4 bracket; no addition of earlier+60m gain',
        unfinished='report finish censoring, common root+60m grid crossings, first failed boundary, endpoint progress/speed/debt/phase separately',
        common_boundaries='root+60m,+120m,... through greatest boundary both observed; never extrapolate beyond either observed endpoint',
        promotion='only both safe confirmed finishes with strict positive full remaining finish-time bracket supports full-window model gain',
        no_native_extrapolation=True,repeat_scope='only source/root qualification repeats; whole arms once each'),
      storage=dict(writer='existing verified plain writer; gzip467 adapter unused',
        latest_raw_bytes=retained['uncompressed_bytes_by_volume']['model'],latest_model_ticks=observed['cost']['model_ticks'],
        observed_bytes_per_tick=float(rate),ratio_fraction=[rate.numerator,rate.denominator],empirical_margin=1.25,
        latest_header_parts=header_parts,header_base_bytes=header,current_manifest_growth_bytes=growth,
        additional_future_manifest_allowance_bytes=4096,per_world_extra_bytes=16384,
        metadata_bytes=16*1024**2,plan_bytes=2*1024**2,reserve_each_volume_bytes=512*1024**2,
        full_private_raw_retention_multiplier=1.1,retention_metadata_bytes=32*1024**2,
        compression_credit=0,existing_compressed_files_transformed=0,old_files_deleted_or_moved=0,
        optimistic_no_new_growth=optimistic,measured_current_sources=measured,registered_future_allowance=forecast),
      actual=dict(model_ticks=0,model_worlds=0,qualification_runs=0,whole_arm_runs=0,native_actions=0,resets=0,
        new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,new_environment=0),
      conclusion='resource stop before integration; not a policy falsification. Finish persistence remains unmeasured.',
      protected_files_verified=18,ledger475_unchanged=True)
    out=R/'stage469';out.mkdir(mode=0o700)
    put(out/'contract-private.json',contract)
    put(out/'source-manifest-private.json',dict(script_sha256=digest(__file__),sources=prior['sources'],semantic_sources=semantic))
    put(G/'retry/design469_next.json',contract)
    print(json.dumps(dict(status=contract['status'],rate=float(rate),header=header,growth=growth,
      planned=contract['planned'],optimistic=optimistic,measured=measured,registered=forecast),ensure_ascii=False))

if __name__=='__main__':main()
