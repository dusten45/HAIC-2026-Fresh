"""Static full recorded-receipt structure and atomic failure checks, no model world."""
import copy,datetime,hashlib,io,json,math,os,pickle,random,sys,time,unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.planner419 import *
from retry.executor397 import canonical_projection
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.pilot420_json import json_ready,restore_bytes
G=Path(__file__).resolve().parents[1]

def fixture(root):
 # Entire real recorded parent/actual RNG and branch structures. Theold execution-local
 # global RNG tokenwasnotretained at420's failedwrite; usecurrentSTATICpreflighttoken,
 # clearlynotclaimingbitrecoveryofthe lost420context.
 r=root/'stage420';fork=read(root/'stage418/actual_A/fork-private.json');parent=read(r/'parent_P-private.json');state=parent['final_state'];memory=fork['controller']['before'];row=json.loads((root/'stage418/actual_A/trace-private.jsonl').read_text().splitlines()[118]);clock=round(state['physical']['actual_time']*50);ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),clock);rng=hashlib.sha256(pickle.dumps((random.getstate(),np.random.get_state()))).hexdigest();p=Parent.current(dict(terminal_model=state,provenance='CURRENT_MODEL_PARENT',immutable_actual_root_digest=ledger.digest()),memory,dict(archived_actual_rng=fork['RNG'],model_global_rng_digest=rng),clock);fixed=read(root/'stage269/N1-plan-private.json');pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);line=np.asarray(fixed['line']);h=state['physical']['hull'];q=canonical_projection(line,h['position'],h['velocity'],'FIRST_LAP');nodes=np.asarray(fixed['free_profile']['speed'])*pace;target=float(np.sqrt((1-q['u'])*nodes[q['index']]**2+q['u']*nodes[q['index']+1]**2));forward=float(np.asarray(h['velocity'])@np.asarray([-math.sin(h['angle']),math.cos(h['angle'])]));digest=hashlib.sha256((sha(G/'retry/signed417_executor.py')+sha(G/'retry/planner419.py')+sha(root/'stage269/N1-plan-private.json')).encode()).hexdigest();ctx=Current(p,ledger,digest,tuple(fork['controller']['nominal']),'FIRST_LAP',target,q['sigma'],forward,sum(fixed['free_profile']['ds'])-ledger.progress_m);ev={}
 for recipe in RECIPES:
  c=read(r/('P_decision1_'+recipe+'_1-private.json'));e=c['end13'];e['wheel_omega']=tuple(e['wheel_omega']);e['steering_joint']=tuple(e['steering_joint']);e['last_raw_force_ratio']=tuple(e['last_raw_force_ratio']);ev[recipe]=Evidence(recipe,ctx.parent.stamp(),ctx.ledger.digest(),ctx.policy_digest,tuple(c['rows'][0]['command']),c['initial_actions'],True,True,True,True,True,True,TerminalVector(**e),tail_status=c['status'],finish_ticks=TickBracket(**c['finish_ticks']),official_finish_qualified=True,tail_actions_integrated=c['tail_actions'],checkpoint_actions=tuple(c['checkpoints']),long_tail_physics_qualified=False)
 proposal=choose(ctx,ev);schedule=query_schedule(ctx,Budget(32768,64));payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={k:asdict(e) for k,e in ev.items()},decision=asdict(proposal),scope='STATICfullrecordedstructure; reconstructedpreflightglobalRNGtoken, notlost420executiontoken. No modelgenerated.')
 return ctx,ev,proposal,payload

def restore_typed(payload):
 c=payload['context'];ctx=Current(parent=Parent(**c['parent']),ledger=GoalLedger(**c['ledger']),policy_digest=c['policy_digest'],nominal=tuple(c['nominal']),phase=c['phase'],target_r=c['target_r'],sigma=c['sigma'],body_forward=c['body_forward'],remaining_path_m=c['remaining_path_m'],projection_qualified=c['projection_qualified'],input_restore_qualified=c['input_restore_qualified'],current_safety_qualified=c['current_safety_qualified'],official_finished=c['official_finished']);ev={}
 for name,raw in payload['evidence'].items():
  e=dict(raw);e['root']=Stamp(**e['root']);e['first_command']=tuple(e['first_command']);t=e['end13'];t['wheel_omega']=tuple(t['wheel_omega']);t['steering_joint']=tuple(t['steering_joint']);t['last_raw_force_ratio']=tuple(t['last_raw_force_ratio']);e['end13']=TerminalVector(**t);e['finish_ticks']=None if e['finish_ticks'] is None else TickBracket(**e['finish_ticks']);e['checkpoint_actions']=tuple(e['checkpoint_actions']);ev[name]=Evidence(**e)
 return ctx,ev

def prepare(root):
 d=root/'stage421';assert not(d/'preflight-plan.json').exists();base=read(root/'stage420/plan.json');files=[Path(__file__),G/'retry/receipt421_io.py',G/'retry/pilot420_json.py',G/'retry/planner419.py',root/'stage421/original420-manifest.json',root/'stage420/parent_P-private.json',root/'stage418/actual_A/fork-private.json',root/'stage418/actual_A/trace-private.jsonl',root/'stage269/N1-plan-private.json',root/'stage404/profiles-private.json',G/'retry/signed417_executor.py']+[root/('stage420/P_decision1_'+recipe+'_1-private.json') for recipe in RECIPES];p=dict(stage=421,scope='Beforeany421integration: bytes+fullrecordedreceiptshape roundtrip/digests/typedselector equivalence andpartialfileerror cleanup; model0. 420 lostglobalRNGtokennotrecovered; staticfixturecontextreconstructedtransparently.',sources={str(p):sha(p) for p in files},protected=base['protected'],original408_preserve=base['original408_preserve']);save(d/'preflight-plan.json',p);(d/'preflight-plan.sha256').write_text(sha(d/'preflight-plan.json')+'\n');print('421 staticpreflight frozen')

def run(root):
 d=root/'stage421';plan=read(d/'preflight-plan.json');assert not(d/'preflight-result.json').exists()
 for f,h in {**plan['sources'],**plan['protected'],**plan['original408_preserve']}.items():assert sha(f)==h
 for f,h in read(d/'original420-manifest.json').items():assert sha(f)==h
 cpu=time.process_time();wall=time.perf_counter();folder=d/'preflight-files';folder.mkdir(mode=0o700);ctx,ev,proposal,payload=fixture(root);stamp=ctx.parent.stamp();digest=receipt_digest(payload);checks=[]
 def mark(name,value):
  if not value:raise AssertionError(name)
  checks.append(name)
 mark('bytes_encode_decode',restore_bytes(json.loads(json.dumps(json_ready({'bytes':b'\x00\xff'}))))=={'bytes':b'\x00\xff'})
 target=folder/'full-receipt.json';save_receipt(target,payload);restored=load_receipt(target);ctx2,ev2=restore_typed(restored);mark('full_recorded_structure_digest',receipt_digest(restored)==digest);mark('full_context_parent_digest',ctx2.parent.stamp()==stamp);mark('full_context_state_memory_rng_bytes',(ctx2.parent.state_bytes,ctx2.parent.memory_bytes,ctx2.parent.rng_bytes)==(ctx.parent.state_bytes,ctx.parent.memory_bytes,ctx.parent.rng_bytes));mark('typed_receipts_selector_equal',choose(ctx2,ev2)==proposal);mark('immutable_parent_not_changed',ctx.parent.stamp()==stamp)
 old=target.read_bytes()
 try:save_receipt(target,{'overwrite':True})
 except FileExistsError:pass
 else:raise AssertionError('existing_target_overwritten')
 mark('existing_receipt_preserved',target.read_bytes()==old)
 partial=folder/'write-failure.json'
 def fail(file,text):file.write(text[:47]);file.flush();raise OSError('injected_partial_write')
 try:
  with patch('retry.receipt421_io._write_all',fail):save_receipt(partial,payload)
 except OSError:pass
 else:raise AssertionError('injectedwritefailure_notraised')
 mark('partial_write_no_target_no_orphan',not partial.exists() and not list(folder.glob('write-failure.json.*.tmp')))
 link=folder/'publish-failure.json'
 try:
  with patch('retry.receipt421_io.os.link',side_effect=OSError('injected_publish_failure')):save_receipt(link,payload)
 except OSError:pass
 else:raise AssertionError('injectedpublishfailure_notraised')
 mark('failed_publish_no_target_no_orphan',not link.exists() and not list(folder.glob('publish-failure.json.*.tmp')))
 stale=folder/'stale-receipt.json.tmp';stale.write_bytes(b'{incomplete420-style');stalehash=sha(stale);save_receipt(folder/'stale-receipt.json',payload);mark('legacy_partial_not_overwritten_or_used',sha(stale)==stalehash)
 unsupported=folder/'unsupported.json'
 try:save_receipt(unsupported,{'x':object()})
 except TypeError:pass
 else:raise AssertionError('unknown_type_silently_coerced')
 mark('encoding_failure_before_file_creation',not unsupported.exists() and not list(folder.glob('unsupported.json.*.tmp')))
 nonfinite=folder/'nan.json'
 try:save_receipt(nonfinite,{'x':float('nan')})
 except ValueError:pass
 else:raise AssertionError('numericalNaN_masked')
 mark('nonfinite_not_masked_no_partial',not nonfinite.exists() and not list(folder.glob('nan.json.*.tmp')))
 for f,h in read(d/'original420-manifest.json').items():assert sha(f)==h
 q=dict(stage=421,status='STATIC_FULL_RECEIPT_PREFLIGHT_PASSED',checks=checks,tests=len(checks),receipt_file_bytes=target.stat().st_size,canonical_digest=digest,parent_stamp=asdict(stamp),fixture_scope=plan['scope'],new_native_model_world_calls=0,original420_preserved=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'preflight-result.json',q);print(json.dumps({k:v for k,v in q.items() if k!='parent_stamp'}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
