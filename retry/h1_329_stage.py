"""Immutable six fold artifacts and cache admission before any native extension."""
import argparse
import hashlib
import importlib.util
import json
import time
import zipfile
from pathlib import Path

import numpy as np

from retry.h1_329_select import choose
from retry.hud248_features import decode
from retry.path271_run import read,save,sha


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage329';p=verify(D);assert not (D/'artifacts-private.json').exists()
    training=np.load(R/'stage325/heldout-predictions-private.npz');configs={};models={}
    for road in p['roads']:
        z=np.load(R/'stage325'/(road+'-ridge-private.npz'));mask=training['roads']!=road
        model={name:z[name].copy() for name in z.files};model.update(low=training['x'][mask].min(0),high=training['x'][mask].max(0));models[road]=model
    for road in p['roads']:
        for enabled in ([False,True] if road==p['roads'][0] else [True]):
            label=road if enabled else 'OFF';F=D/'artifacts'/label;F.mkdir(parents=True,mode=0o700)
            with zipfile.ZipFile(p['base_config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
            oldroot=members['agent.py'];members['retry/h1_329_base.py']=oldroot;members['agent.py']=(G/'retry/h1_329_agent.py').read_bytes()
            members['retry/h1_329_select.py']=(G/'retry/h1_329_select.py').read_bytes();members['retry/hud248_features.py']=(G/'retry/hud248_features.py').read_bytes()
            code='import numpy as np\nENABLED='+repr(enabled)+'\nMODEL={\n'+''.join(repr(k)+':np.array('+repr(v.tolist())+',float),\n' for k,v in models[road].items())+'}\n'
            members['retry/h1_329_model.py']=code.encode();archive=F/'policy.zip'
            with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
                for name,b in sorted(members.items()):
                    item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
            archive.chmod(0o600)
            cfg=dict(p['base_config'],archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})
            with zipfile.ZipFile(p['base_config']['archive_path']) as source:
                assert all(members[n]==source.read(n) for n in source.namelist() if n!='agent.py')
                assert members['retry/h1_329_base.py']==source.read('agent.py')
            configs[label]=cfg
    save(D/'artifacts-private.json',configs);save(D/'build-receipt.json',dict(original296dependencies_byte_exact=True,original_root_byte_exact_preserved=True,fold_models_unchanged=True,runtime_road_id_branches=0,new_fits=0,
        public_code_hashes={str(G/'retry'/n):sha(G/'retry'/n) for n in ['h1_329_agent.py','h1_329_select.py','h1_329_stage.py']}))
    print('329sixfixedONfoldartifacts+OFFbuilt;original296dependenciespreserved',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage329';p=verify(D);configs=read(D/'artifacts-private.json');assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time();details=[];total=dict(rows=0,changed=0,acceleration=0,deceleration=0,wrong_direction=0,missing_target=0);distribution={};failures=[]
    spec=importlib.util.spec_from_file_location('speed329',R/'stage306/zero-replay/O0/package/retry/hud_feedback.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    for road in p['roads']:
        F=R/'stage306/collection'/road;z=np.load(F/'observations-actions-private.npz');rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        off=prepare(configs['OFF'],D/'cache'/road/'OFF',p['sandbox_path']);on=prepare(configs[road],D/'cache'/road/'ON',p['sandbox_path'])
        count=dict(road=road,rows=len(rows),changed=0,acceleration=0,deceleration=0,wrong_direction=0,missing_target=0,reasons={},choices={},baseline_objective_sum=0.,selected_objective_sum=0.)
        private=[]
        try:
            off.call('reset',z['observations'][0]);on.call('reset',z['observations'][0])
            for i,(obs,expected,row) in enumerate(zip(z['observations'],z['actions'],rows)):
                a,_=off.call('act',obs);b,_=on.call('act',obs);actual=np.array(b['action'],np.float32);audit=b['delta_audit']
                assert np.array_equal(np.array(a['action'],np.float32),expected) and a['features']==row['features']==b['features']
                assert actual[0]==expected[0];assert np.float32(a['state']['previous_steer'])==np.float32(row['memory'])
                for name in ['previous_steer','lateral_acceleration','hazards_sha256','previous_image_sha256']:assert a['state'][name]==b['state'][name],name
                aa,_=off.call('commit',expected);bb,_=on.call('commit',actual)
                assert aa['memory']==row['memory']==bb['memory']
                for name in ['previous_steer','lateral_acceleration','hazards_sha256','previous_image_sha256']:assert aa['state'][name]==bb['state'][name],name
                reason=audit['reason'];count['reasons'][reason]=count['reasons'].get(reason,0)+1;name=audit['selected_name'];count['choices'][name]=count['choices'].get(name,0)+1
                if row['features'][0]:assert np.array_equal(actual,expected);count['missing_target']+=1
                if audit['changed']:
                    assert audit['selected_supported'] and audit['chosen_error']<audit['baseline_error'];assert not np.array_equal(actual,expected)
                    change=audit['chosen_next_speed']-audit['baseline_next_speed'];gap=audit['q']-audit['baseline_next_speed']
                    count['wrong_direction']+=int(change*gap<=0);count['acceleration']+=int(change>0);count['deceleration']+=int(change<0);count['changed']+=1
                if audit['baseline_error'] is not None:
                    count['baseline_objective_sum']+=audit['baseline_error'];count['selected_objective_sum']+=audit['chosen_error']
                private.append(dict(step=i+1,action=actual.tolist(),audit=audit))
            # Undefined/missing target helper tests do not call a simulator.
            f=np.array(rows[0]['features']);f[0]=1;out,_=choose(z['actions'][0],f,None,{},True);assert np.array_equal(out,z['actions'][0])
        finally:
            r1=off.close();r2=on.close()
        assert all(r['process_reaped'] and r['actor_pids_absent'] for r in [r1,r2]);save(D/(road+'-cache-audits-private.json'),private)
        for k in total:total[k]+=count[k]
        for name,n in count['choices'].items():distribution[name]=distribution.get(name,0)+n
        details.append(count);save(D/'cache-partial-private.json',details);print(json.dumps(count),flush=True)
    passed=bool(total['rows']==1754 and total['changed']>0 and total['acceleration']>0 and total['deceleration']>0 and total['wrong_direction']==0)
    if not passed:failures.append('Fixedcachegatefailed:identity/actionchange/bidirectionalstrictimprovement required')
    receipt=dict(passed=passed,total=total,choices=distribution,details=details,OFF_action_features_steer_memory_exact=True,ON_nominal_controller_tracker_state_exact=True,causal_current_input_only=True,
        undefined_target_fallback=True,models_frozen=True,new_native=0,new_fits=0,failures=failures,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)
    save(D/'cache-receipt.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['build','cache']);parser.add_argument('--private-root',type=Path,required=True)
    args=parser.parse_args();globals()[args.phase](args.private_root.resolve())
