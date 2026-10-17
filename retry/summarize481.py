"""481 post-closure saved-only diagnostic aggregates. No model/actor calls."""
import time
START=time.perf_counter()
import hashlib,json,os,sys
from pathlib import Path
from retry.io481 import read
G=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
    d=root/'stage481';p=read(d/'plan.json');manifest=read(root/'stage481-retention-manifest-private.json');inventory={Path(x['path']).name:x for x in manifest['files']}
    def checked(path):
        path=Path(path);record=inventory[path.name];assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256'];return read(path)
    result=checked(d/'result.json');out=result['outcome'];last=out['parents'][1]['undispatched_preparation']['allocation_number'];empty=checked(d/f'empty-{last:03d}-private.json');failed=[]
    for opt in empty['options'].values():
        trace=checked(opt['first_path']);row=trace['rows'][0]
        failed.append(dict(aliases=opt['aliases'],M80=opt['M80'],valid=opt['valid'],status=trace['status'],error=trace['error'],safety=row['safety'],forecast_post_path_error_m=row['path_error_m'],progress_deadline_missed=trace['model_ledger']['deadline_missed']))
    baseline=checked(d/'baseline-private.json')['rows'];online=checked(d/'online-private.json')['rows'];same=0
    for a,b in zip(baseline,online):
        if a!=b:break
        same+=1
    firstcmd=next((i for i,(a,b) in enumerate(zip(baseline,online),1) if a['command']!=b['command']),None)
    changes={'gas_reductions':0,'brake_reductions':0};selected_repeats=0
    for q in out['online_queries']:
        if 'selected_aliases' not in q:continue
        selected_repeats+=1
        opts=list(q['options'].values());n=next(v for v in opts if 'nominal' in v['aliases']);chosen=next(v for v in opts if v['aliases']==q['selected_aliases'])
        for k,index in [('gas_reductions',1),('brake_reductions',2)]:changes[k]+=chosen['command'][index]<n['command'][index]
    budget=checked(d/'budget.json')['model']
    for group in ('protected','original408_preserve'):
        for f,h in p[group].items():assert sha(f)==h
    assert sha(p['ledger_path'])==p['ledger_sha256']
    summary=dict(stage=481,mode='SAVED_ONLY_POSTPROCESS_NO_NEW_EXPERIMENT',main_result_sha256=sha(d/'result.json'),source_code_sha256=sha(Path(__file__)),retention_manifest_sha256=sha(root/'stage481-retention-manifest-private.json'),parents=[{k:v for k,v in x.items() if k in ('arm','status','actions','max_path_error_m','last_path_error_m','official_own_model_finish')} for x in out['parents']],same_entire_row_prefix=same,first_command_divergence_action=firstcmd,interventions=changes,online_selected_independent_repeats=selected_repeats,empty_query=len(out['online_queries']),all_empty_candidates=failed,empty_own_dispatch=False,finish_gain=None,core_step_and_observer_CPU_s=sum(v for k,v in budget['CPU_by_tag'].items() if not k.endswith('_world_setup')),constructor_CPU_s=sum(v for k,v in budget['CPU_by_tag'].items() if k.endswith('_world_setup')),postprocess_CPU_s=time.process_time(),postprocess_wall_s=time.perf_counter()-START,new_physics=0,new_native=0,new_worlds=0,new_reset=0)
    target=G/'retry/online481_summary.json';assert not target.exists()
    with target.open('x') as f:json.dump(summary,f,indent=2,allow_nan=False);f.write('\n')
    private=root/'stage481-postprocess-private.json';assert not private.exists()
    cost=dict(summary=summary,CPU_s_after_write=time.process_time(),wall_s_after_write=time.perf_counter()-START,earlier_main_postread_CPU_s=.861370712,earlier_main_postread_wall_s=.4500142850447446,independent_audit_CPU_s=1.695921925,independent_audit_wall_s=1.329765377,independent_failed_reader_tool_wall_s=.091833020,independent_failed_reader_CPU_s=None,unmeasured_import_startup_conservative_CPU_charge_s=100,unmeasured_import_startup_conservative_wall_charge_s=5,logical_CPUs=os.cpu_count(),scope='Measured registration+worker+required full readbacks from main result; these postreads/audit/summary are separately added.100CPU/5wall conservatively charged for failed system-python reader import and unmeasured audit startup; charged values are not measurements. No physical experiment retry.')
    main=read(G/'retry/online481_result.json');cost['accounted_CPU_s']=main['whole_CPU_s']+cost['CPU_s_after_write']+.861370712+1.695921925+100;cost['accounted_wall_s']=main['whole_wall_s']+cost['wall_s_after_write']+.4500142850447446+1.329765377+.091833020+5
    assert cost['accounted_CPU_s']<900 and cost['accounted_wall_s']<1200
    with private.open('x') as f:json.dump(cost,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(summary));print(json.dumps({k:cost[k] for k in ('accounted_CPU_s','accounted_wall_s','logical_CPUs')}))
if __name__=='__main__':run(Path(sys.argv[1]))
