"""471 single P4 native contract and exact storage arithmetic; no integration."""
import hashlib,json,math,shutil,datetime
from fractions import Fraction
from pathlib import Path

G=Path(__file__).resolve().parents[1]
R=Path('/workspace/haic-private-retry-20261009')
MIB=1024**2
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,value):
 with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
 old= json.loads((R/'stage469-revision1/plan.json').read_text())
 for group in ['protected','original408_preserve']:
  for path,h in old[group].items():assert sha(path)==h,path
 assert sha(old['ledger_path'])==old['ledger_sha256']
 ledger=json.loads(Path(old['ledger_path']).read_text())
 assert (ledger['research_remaining'],ledger['final_reserved_actions'],ledger['final_reserve_used'])==(26346,84000,0)
 model_rate=Fraction(126087848,1353)
 latest=json.loads((G/'retry/compare470_retention.json').read_text())
 model_rate=max(model_rate,Fraction(latest['uncompressed_bytes_by_volume']['model'],1671))
 native=[];fixed_names=['initial-private.json','root-before-nominal-private.json','final-private.json','native-routing-history-private.json','first-transition-checks-private.json','result.json']
 for pattern in ['stage453/actual*','stage458/actual*','stage463-native/actual*']:
  for d in sorted(R.glob(pattern)):
   if not(d/'result.json').is_file():continue
   result=json.loads((d/'result.json').read_text());files=[p for p in d.rglob('*') if p.is_file()]
   size=sum(p.stat().st_size for p in files);actions=result['native_actions']
   trace=[json.loads(line) for line in (d/'trace-private.jsonl').read_text().splitlines() if line]
   ticks=sum(row['raw_ticks'] for row in trace);assert len(trace)==actions
   native.append(dict(source=str(d.relative_to(R)),bytes=size,actions=actions,raw_ticks=ticks,
     bytes_per_action=float(Fraction(size,actions)),bytes_per_raw_tick=float(Fraction(size,ticks)),
     fixed_bytes=sum((d/name).stat().st_size for name in fixed_names if (d/name).exists()),
     maximum_file_bytes=max(p.stat().st_size for p in files)))
 action_rate=max(Fraction(x['bytes'],x['actions']) for x in native)
 raw_rate=max(Fraction(x['bytes'],x['raw_ticks']) for x in native)
 header_parts={key:max(p.stat().st_size for p in (R/'stage469-revision1').glob(pattern)) for key,pattern in [
  ('constructor','world*-before-constructor-private.json'),('first_step','world*-before-first-step-private.json'),
  ('runtime_link','*-runtime-link-private.json'),('own_reference','*-own-reference-before-constructor-private.json')]}
 header=max(778235,sum(header_parts.values()))
 semantic=dict(old['semantic_sources']);semantic[str(G/'retry/design471.py')]=sha(__file__)
 growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode()))
 model=math.ceil(9216*model_rate*Fraction(5,4)+185*(header+3*(growth+4096)+16384)+18*MIB)
 # Prefix500+suffix280+reset51 raw ticks. Use the larger measured action/raw
 # projection; reset is explicit even though historical rates include headers.
 prefix=500*raw_rate*Fraction(5,4);suffix=280*raw_rate*Fraction(5,4);reset=51*raw_rate*Fraction(5,4)
 native_fixed=max(16*MIB,math.ceil(max(x['fixed_bytes'] for x in native)*Fraction(5,4)))
 native_bytes=math.ceil(max(prefix+suffix+reset,195*action_rate*Fraction(5,4)+reset)+native_fixed+32*MIB)
 combined=model+native_bytes;archive=math.ceil(combined*Fraction(11,10)+32*MIB);temp=32*MIB
 required_tmp=combined+archive+temp+512*MIB;required_workspace=64*MIB+512*MIB
 free={p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}
 shortage=max(0,required_tmp-free['/tmp']);assert shortage>0,'No executor in this design-only module'
 # A simpler favorable bound already fails, independently of new source and
 # explicit reset/header allowance. Preserve both figures to expose uncertainty.
 lower_model=math.ceil(9216*model_rate*Fraction(5,4)+185*(778235+16384)+18*MIB)
 lower_native=math.ceil(195*action_rate*Fraction(5,4)+32*MIB)
 lower_raw=lower_model+lower_native
 lower_required=lower_raw+math.ceil(lower_raw*Fraction(11,10)+32*MIB)+32*MIB+512*MIB
 contract=dict(stage=471,status='NOT_STARTED_STORAGE_GATE_FAILED',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  deadline_utc='2026-10-20T10:01:55Z',authorization_extension_sha256=old['authorization_extension_sha256'],
  authority='Current user explicitly requested one conditional single-candidate P4 transfer; no fresh paired gain claim',
  native=dict(arms=1,prefix_actions=125,suffix_actions=70,max_actions=195,max_resets=1,
   prefix='same saved458/463 native start/commands/state/memory/RNG/pixels/ledger exact125; stop on first mismatch',
   injection='P4 immutable nodes only after prefix125 and before native126 C.act',
   policy='one global first fullgas at native126; thereafter P4 point-FF/phase/own terminal tracker, no guardian/neutral/rescue/rank',
   actual_action_charge_unit='attempted wrapper env.step; charge195 cap before call, reset counted separately',
   failure='stop candidate at first invalid shadow/unsafe/domain/adapter/fidelity failure; no refund/retry or risk-rejection bypass',
   historical13_780s='reference only, not a fresh pair or causal/statistical gain'),
  shadow=dict(current_queries=70,independent_copies=2,horizon_actions=13,max_raw_ticks=7280,max_worlds=140,
   control='all13 actions P4 own reference; local shadow action0 is not a pulse reset',
   global_index='first-fullgas iff global native step126; forecast can extend fixed P4 law to suffix index82, while actual stops at70',
   observation='current actual state/memory/RNG/read-only GoalLedger and same nodes/source digest; immutable parent',
   qualification='both H13 valid incl existing finish/progress/safety/numeric gates; compare actual first transition with selected shadow, preserve actual fact even on mismatch',
   no_extra_model_parent_held_or_guardian=True),
  planned=dict(source=dict(ticks=1242,worlds=35),root=dict(ticks=216,worlds=6),current_P4_shadows=dict(ticks=7280,worlds=140),total_ticks=8738,total_worlds=181),
  hard=dict(model_ticks=9216,model_worlds=185,actual_actions=195,resets=1,whole_CPU_s=900,wall_s=1200,max_parallel=1),
  remaining_headroom=dict(ticks=478,worlds=4,additional_execution_authority=False),
  source_gate=dict(old_qualifications_reused_as_protocol_not_cached_pass=True,
   existing_Query463_reusable_unchanged=False,reason='old nominal/neutral guardian after first is not P4',
   integration_fixture='before any reset: actual plus every current/future/pending shadow bind same frozen P4 nodes/digest; act once; SourceC FIRST_LAP/FINISH_CONFIRM own nodes[-1]; no model DONE commits actual DONE',
   first_frame_and_charge_fact='reuse NativeAuthority439 charge-before-call, observed fact commit before forecast compare, next dispatch blocked on mismatch',
   unresolved_before_execution=['new P4-specific current/terminal/pending integration fixture and production adapter not implemented because pre-integration storage gate failed',
     'any additional physical parent/held/pending qualification would need explicit recosting before integration; 4 spare worlds are not permission']),
  storage=dict(model_rate_bytes_per_tick=float(model_rate),model_header_parts=header_parts,model_header_base_bytes=header,
   actual_new_manifest_growth_bytes=growth,prospective_manifest_allowance_bytes=4096,margin=1.25,
   native_rate_bytes_per_action=float(action_rate),native_rate_bytes_per_raw_tick=float(raw_rate),native_source_samples=native,
   native_prefix_raw_ticks=500,native_suffix_raw_ticks=280,native_reset_raw_ticks=51,native_total_raw_ticks=831,
   prefix_raw_forecast_bytes=math.ceil(prefix),suffix_raw_forecast_bytes=math.ceil(suffix),reset_raw_forecast_bytes=math.ceil(reset),
   native_fixed_allowance_bytes=native_fixed,native_metadata_bytes=32*MIB,model_metadata_and_plan_bytes=18*MIB,
   model_raw_bytes=model,native_raw_bytes=native_bytes,combined_raw_bytes=combined,archive_worst_allowance_bytes=archive,
   archive_multiplier=1.1,archive_metadata_bytes=32*MIB,temp_bytes=temp,reserve_each_bytes=512*MIB,
   tmp_required_bytes=required_tmp,workspace_required_bytes=required_workspace,free_at_gate=free,
   tmp_shortage_bytes=shortage,workspace_shortage_bytes=max(0,required_workspace-free['/workspace']),
   favorable_zero_growth_required_tmp_bytes=lower_required,favorable_zero_growth_shortage_bytes=max(0,lower_required-free['/tmp']),
   placement='new raw and full verified archive both same executor/tmp; workspace code/aggregate/input/privateplan/manifest/repro only',
   compression_credit=0,workspace_new_raw_archive_copies=0,old_files_deleted_moved_transformed=0,
   tmp_persistent_or_shared_assumed=False,loss_limit='If/tmp lost, exact new raw/archive cannot be reverified; hashes cannot reconstruct raw'),
  research_budget=dict(before=26346,proposed_max_charge=195,after_max_charge=26151,reserve=84000,reserve_used=0,actual_charge_now=0),
  actual=dict(model_ticks=0,model_worlds=0,native_calls=0,resets=0,worker_started=False,ledger_changed=False),
  conclusion='Resource stop before integration; no native result, no new policy falsification or promotion. Pending fixture remains a prerequisite.')
 d=R/'stage471';d.mkdir(mode=0o700)
 put(d/'contract-private.json',contract)
 put(d/'source-manifest-private.json',dict(script_sha256=sha(__file__),prior_plan_sha256=sha(R/'stage469-revision1/plan.json'),
  model_retention_sha256=sha(G/'retry/compare470_retention.json'),native_design463_sha256=sha(G/'retry/design463.json'),
  protected=old['protected'],original408_preserve=old['original408_preserve'],ledger_path=old['ledger_path'],ledger_sha256=old['ledger_sha256']))
 put(G/'retry/design471_next.json',contract)
 print(json.dumps(dict(stage=471,status=contract['status'],planned=contract['planned'],storage=contract['storage'],actual=contract['actual']),ensure_ascii=False))

if __name__=='__main__':main()
