"""Read-only audit of frozen610 inputs, exact A, finite C grid and charged work."""
import collections
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

CPU=time.process_time()
G=Path(__file__).resolve().parents[1]
D=Path('/workspace/haic-response610-private')
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def f32(x): return struct.unpack('<f',struct.pack('<f',x))[0]


def expected_pairs(nominal,modified):
    lock_bits=struct.unpack('<I',struct.pack('<f',.9))[0]+1
    lock=struct.unpack('<f',struct.pack('<I',lock_bits))[0]
    below=struct.unpack('<f',struct.pack('<I',lock_bits-1))[0]
    net=lambda a:a[1] if a[1]>0 else -a[2]
    values=[-1+i/8 for i in range(17)]+[-lock,-below,net(nominal),net(modified)]
    unique={}
    for u in values:
        u=f32(u); u=0. if u==0 else u; unique[struct.pack('<f',u)]=u
    grid=sorted(unique.values(),reverse=True); pairs=[]; seen={}
    for row,steer in sorted([('base',nominal[0]),('shifted',modified[0])],key=lambda q:q[1]):
        for u in grid:
            bits=struct.pack('<3f',steer,max(0.,u),max(0.,-u)).hex()
            if bits in seen: pairs[seen[bits]]['rows'].append(row)
            else:
                seen[bits]=len(pairs); pairs.append(dict(index=len(pairs),row=row,rows=[row],u=u,action_bits=bits))
    return pairs


def main():
    r=read(D/'as-executed-result-private.json'); public=read(G/'retry/early610_result.json')
    c=read(G/'retry/early610_contract.json'); tests=read(G/'retry/early610_tests.json'); closed=read(D/'CLOSED-private.json')
    checks=dict(frozen_source=all(sha(G/p)==h for p,h in c['source_sha256'].items()),
        frozen_tests=sha(G/'retry/early610_tests.json')==c['tests_sha256'],
        registered_contract=read(D/'REGISTERED-private.json')['contract_sha256']==sha(G/'retry/early610_contract.json'),
        closed_results=sha(G/'retry/early610_result.json')==closed['result_sha256'] and sha(D/'as-executed-result-private.json')==closed['raw_sha256'],
        private_pins=all(sha(D/p)==h for p,h in r['private_sha256'].items()),
        actual_object_preflight=tests['passed'] and tests['actual_object'] and not tests['callbacks_noop'] and tests['physical_kernel']==tests['chooser']==tests['real_geometry_evaluator']==0,
        preflight_private_pins=all(sha(D/tests['private_preflight_directory']/p)==h for p,h in tests['private_preflight_sha256'].items()),
        stub_queries_charged=tests['logical_stub_projection_queries_charged']==2064 and r['cost']['geometry']>=2064,
        prefix_both_histories=r['checks']['phase_history_prefix96']['all_raw_checkpoint_hashes_exact'],
        A_runtime_gate=r['checks'].get('A_all_rows_commands_full_checkpoint_planes_exact605',False),
        nominal_source_calls=r['checks'].get('nominal_direct_matches_original_calls',False))
    zero=read(Path('/workspace/haic-response605-private/zero-result-private.json')); a=read(D/'A-result-private.json')
    checks['A_independent_full_saved_identity']=all(digest(a[k])==digest(zero[k]) for k in ['rows','commands','checkpoint','crossings'])
    counts=collections.Counter(); certificates=0
    for p in sorted(D.glob('*-telemetry-private.json')):
        q=read(p)
        for e in q['events']:
            counts['model_attempted']+=e['kind']=='BEFORE_MODEL_FORCE'
            counts['model_completed']+=e['kind']=='AFTER_MODEL_TICK'
            certificates+=e['kind']=='TRACKING_TRIAL_START'
        counts.update(w[0] for w in q['wheel_results'])
    checks['all_primitive_model_force_counts']=all(counts[k]==r['cost'][k] for k in counts)
    checks['force_sum']=counts['external_force']+counts['internal_force']==r['cost']['total_force']
    grid_ok=selection_ok=True; pair_count=final_count=zero_grids=0
    for p in sorted(D.glob('C-pairs-*-private.json')):
        q=read(p); pairs=q['pairs']; pair_count+=len(pairs)
        nominal=struct.unpack('<3f',bytes.fromhex(q['nominal_bits'])); modified=struct.unpack('<3f',bytes.fromhex(q['modified_bits']))
        expected=expected_pairs(nominal,modified)
        grid_ok &= len(pairs)==len(expected)<=42 and all(all(e[k]==v[k] for k in e) for e,v in zip(expected,pairs))
        if q['meta']['offset']==q['meta']['pedal_residual']==0:
            zero_grids+=1; grid_ok &= q['nominal_bits']==q['modified_bits'] and len(pairs)>1
        eligible=[e for e in pairs if e['report']['ok']]
        if eligible:
            winner=min(eligible,key=lambda e:(-e['end_progress'],-e['first4_progress'],e['index']))
            selection_ok &= winner['action_bits']==q['selected_bits']; final_count+=1
            hold=int(p.name.split('-')[2]); detail=read(D/f'C-{hold:03d}-telemetry-private.json')['detail']
            selection_ok &= detail['action_bits']==q['selected_bits'] and detail['final']['ok']
        else: selection_ok &= q['selected_bits'] is None
    checks['C_exact_current_grid_and_zero_policy']=bool(grid_ok)
    checks['C_end48_first4_index_selection_fresh_FINAL']=bool(selection_ok)
    head='0'*64; kinds=collections.Counter(); reservations=collections.Counter()
    for i,line in enumerate((D/'applied-journal-private.jsonl').read_text().splitlines()):
        e=json.loads(line); h=e.pop('sha256'); assert e['previous']==head and e['sequence']==i and digest(e)==h; head=h
        kinds[e['kind']]+=1
        if e['kind']=='RESERVE': reservations[e['arm']]+=1
    checks['durable_journal_chain']=True
    checks['global_caps_and_kernel']=all(r['cost'].get(k,0)<=v for k,v in c['caps'].items()) and r['kernel_hardcap']==200000 and r['model_counter']==r['cost']['model_completed']
    allowed={'before_raw','after_raw','fraction','time_s','hold','eligible','whole_hold_safe'}
    checks['public_crossings_aggregate_only']=all(set(q)<=allowed for arm in public['arms'] for q in arm['crossings'].values())
    baseline=r['arms'][0]['crossings']['400']['time_s']
    improved=[arm for arm in r['arms'][1:] if arm['safe_s400'] and arm['crossings']['400']['time_s']<baseline]
    if improved:
        best=min(improved,key=lambda q:(q['crossings']['400']['time_s'],q['arm']))
        checks['only_best_positive_replayed']=r['replay'] is not None and r['replay']['exact'] and r['replay']['arm']==best['arm']
        rep=read(D/'independent-initial-replay-private.json'); win=read(D/f"{best['arm']}-result-private.json")
        checks['replay_full_rows_checkpoint_planes']=digest(rep['rows'][96:])==digest(win['rows']) and digest(rep['checkpoint'])==digest(win['checkpoint']) and digest(rep['crossings'])==digest(win['crossings'])
    else: checks['no_positive_no_replay']=r['replay'] is None and not (D/'REPLAY_STARTED-private.json').exists()
    checks['zero_forbidden_work']=all(r[k]==0 for k in ['native','worlds','resets','new_seed','carry','HOLDOUT','SEALED'])
    checks['prior609_preserved']=sha(G/'retry/early609.py')==c['preserve609']['code'] and sha(G/'retry/early609_closeout.json')==c['preserve609']['closeout']
    checks['main_Participants_ledger']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip() and r['research_remaining']==22211 and r['reserve_used']==0
    task=read(D/'TASK_STARTED-private.json'); wall=time.time()-task['start_epoch']+task['prior_preparation_wall_s']+c['preserve609']['failure_cost']['whole_task_accounted_wall_s']
    audit_cpu=time.process_time()-CPU
    checks['combined609_610_time_cleanup_reserved']=wall+120<6600 and r['time']['CPU_s']+audit_cpu+90<5400
    out=dict(study=610,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',checks=checks,
        primitive_counts=dict(counts),certificates=certificates,C_pairs=pair_count,C_fresh_FINAL=final_count,C_zero_residual_grids=zero_grids,
        durable_events=dict(kinds),reservations_by_arm=dict(reservations),new_evaluations=0,audit_CPU_s=audit_cpu,
        combined609_610_wall_through_audit_s=wall,result_sha256=sha(G/'retry/early610_result.json'))
    (G/'retry/early610_audit.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); assert all(checks.values())


if __name__=='__main__': main()
