"""Freeze one all-road ensemble artifact and admit it using cached observations."""
import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path

import numpy as np

from retry.path271_run import read,save,sha


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage330';p=verify(D);assert not (D/'artifacts-private.json').exists()
    training=np.load(R/'stage325/heldout-predictions-private.npz');x=training['x'];roads=training['roads'];models=[]
    for road,path in p['models'].items():
        z=np.load(path);model={k:z[k].copy() for k in z.files};mask=roads!=road;model.update(low=x[mask].min(0),high=x[mask].max(0));models.append(model)
    configs={}
    for enabled in [False,True]:
        label='ON' if enabled else 'OFF';F=D/'artifacts'/label;F.mkdir(parents=True,mode=0o700)
        with zipfile.ZipFile(p['base_config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
        members['retry/h1_330_base.py']=members['agent.py'];members['agent.py']=(G/'retry/h1_330_agent.py').read_bytes()
        for name in ['h1_330_select.py','h1_329_select.py','hud248_features.py']:members['retry/'+name]=(G/'retry'/name).read_bytes()
        modelcode='import numpy as np\nENABLED='+repr(enabled)+'\nMODELS=[\n'
        for model in models:modelcode+='{'+''.join(repr(k)+':np.array('+repr(v.tolist())+',float),' for k,v in model.items())+'},\n'
        modelcode+=']\n';members['retry/h1_330_model.py']=modelcode.encode();archive=F/'policy.zip'
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
            for name,b in sorted(members.items()):
                item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
        archive.chmod(0o600)
        with zipfile.ZipFile(p['base_config']['archive_path']) as z:
            assert all(members[n]==z.read(n) for n in z.namelist() if n!='agent.py');assert members['retry/h1_330_base.py']==z.read('agent.py')
        configs[label]=dict(p['base_config'],archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})
    save(D/'artifacts-private.json',configs);save(D/'build-receipt.json',dict(one_identical_ON_artifact_all18=True,model_count=6,fixed_equal_weights=True,
        original296dependencies_and_root_preserved=True,runtime_road_or_fold_branch=False,new_fits=0,source_hashes={str(G/'retry'/name):sha(G/'retry'/name) for name in ['h1_330_agent.py','h1_330_select.py','h1_330_stage.py','h1_329_select.py']}))
    print('330oneON+OFFartifactsfrozen; sixraw-outputmodels all roads, intersectionguard',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage330';p=verify(D);configs=read(D/'artifacts-private.json');assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time();details=[];total=dict(rows=0,changed=0,acceleration=0,deceleration=0,wrong_direction=0,missing_target=0);distribution={};max_mean_error=0.;support_rejections=0
    for road in p['original6']:
        F=R/'stage306/collection'/road;z=np.load(F/'observations-actions-private.npz');rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        off=prepare(configs['OFF'],D/'cache'/road/'OFF',p['sandbox_path']);on=prepare(configs['ON'],D/'cache'/road/'ON',p['sandbox_path'])
        count=dict(road=road,rows=len(rows),changed=0,acceleration=0,deceleration=0,wrong_direction=0,missing_target=0,reasons={},choices={},support_rejected_candidates=0);private=[]
        try:
            off.call('reset',z['observations'][0]);on.call('reset',z['observations'][0])
            for obs,expected,row in zip(z['observations'],z['actions'],rows):
                a,_=off.call('act',obs);b,_=on.call('act',obs);actual=np.array(b['action'],np.float32);audit=b['delta_audit']
                assert np.array_equal(np.array(a['action'],np.float32),expected);assert a['features']==row['features']==b['features'];assert actual[0]==expected[0]
                for k in ['previous_steer','lateral_acceleration','hazards_sha256','previous_image_sha256']:assert a['state'][k]==b['state'][k],k
                aa,_=off.call('commit',expected);bb,_=on.call('commit',actual);assert aa['memory']==row['memory']==bb['memory']
                for k in ['previous_steer','lateral_acceleration','hazards_sha256','previous_image_sha256']:assert aa['state'][k]==bb['state'][k],k
                if row['features'][0]:assert np.array_equal(actual,expected);count['missing_target']+=1
                for candidate in audit['candidates']:
                    assert candidate['supported']==all(candidate['support_by_model']) and len(candidate['support_by_model'])==6
                    if candidate['supported']:
                        assert len(candidate['model_next_speeds'])==6
                        error=abs(candidate['next_speed']-float(np.mean(candidate['model_next_speeds'])));assert error==0.;max_mean_error=max(max_mean_error,error)
                    else:assert candidate['model_next_speeds'] is None and candidate['next_speed'] is None;count['support_rejected_candidates']+=1
                if audit['base_support_by_model'] is not None and not all(audit['base_support_by_model']):assert audit['action']==row['action']
                if audit['changed']:
                    assert audit['selected_supported'] and audit['chosen_error']<audit['baseline_error'];delta=audit['chosen_next_speed']-audit['baseline_next_speed'];gap=audit['q']-audit['baseline_next_speed']
                    count['changed']+=1;count['acceleration']+=int(delta>0);count['deceleration']+=int(delta<0);count['wrong_direction']+=int(delta*gap<=0)
                reason=audit['reason'];name=audit['selected_name'];count['reasons'][reason]=count['reasons'].get(reason,0)+1;count['choices'][name]=count['choices'].get(name,0)+1
                private.append(dict(action=actual.tolist(),audit=audit))
        finally:r1=off.close();r2=on.close()
        assert all(r['process_reaped'] and r['actor_pids_absent'] for r in [r1,r2]);save(D/(road+'-cache-audits-private.json'),private)
        for k in total:total[k]+=count[k]
        support_rejections+=count['support_rejected_candidates']
        for k,n in count['choices'].items():distribution[k]=distribution.get(k,0)+n
        details.append(count);save(D/'cache-partial-private.json',details);print(json.dumps(count),flush=True)
    passed=bool(total['rows']==1754 and total['changed']>0 and total['acceleration']>0 and total['deceleration']>0 and not total['wrong_direction'])
    save(D/'cache-receipt.json',dict(passed=passed,total=total,details=details,choices=distribution,max_mean_arithmetic_error=max_mean_error,support_rejected_candidates=support_rejections,
        one_ON_artifact_for_all_roads=True,OFF_actions_features_memory_exact=True,ON_nominal_controller_tracker_steering_preserved=True,six_models_never_dropped=True,
        new_native=0,new_fits=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu))
    print('330cachegate='+str(passed),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['build','cache']);parser.add_argument('--private-root',type=Path,required=True)
    args=parser.parse_args();globals()[args.phase](args.private_root.resolve())
