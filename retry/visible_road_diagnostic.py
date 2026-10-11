"""Two fixed DEV episodes of the renderer-visible privileged road diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from retry import fresh_dev_distribution as cohort
from retry.full_route_reproduction import truth
from retry.qualify_pixel_package import PipeWorker
from retry.visible_road_occlusion import visible_road_mask


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    path=parser.parse_args().plan.resolve();D=path.parent;plan=json.loads(path.read_text());started=time.perf_counter()
    assert cohort.sha(path)==(D/'plan.sha256').read_text().split()[0]
    for n,h in plan['source_sha256'].items():assert cohort.sha(Path(n))==h,n
    assert len(plan['cases'])==2 and plan['max_actions']==4000
    execution=cohort.clone(plan,D);helper=execution[0]/'boundary.py'
    helper.write_bytes(Path(plan['boundary_path']).read_bytes());helper.chmod(0o444)
    assert cohort.sha(helper)==cohort.sha(Path(plan['boundary_path']))
    factory=cohort.make_env;worker=cohort.PipeWorker;active={};results=[];stop_reason=None
    class VisibleWorker(PipeWorker):
        def call(self,operation,observation):
            before=time.perf_counter();mask,detail=visible_road_mask(active['env'])
            active['mask_wall_s']+=time.perf_counter()-before;active['mask_calls']+=1
            response,duration=super().call(operation,np.concatenate((observation,mask[None].astype(np.float32)),axis=0))
            if operation=='act':response['route_telemetry']['privileged_road_mask_input']=detail
            return response,duration
    cohort.PipeWorker=VisibleWorker
    try:
        for case in plan['cases']:
            if stop_reason:
                result={'id':case['id'],'status':'UNEXECUTED','reason':stop_reason,'episode_count':0,'retries':0,'charged_wrapper_actions':0}
            else:
                receipt={};active.update(mask_wall_s=0.,mask_calls=0)
                def guarded_factory():
                    env=factory();active['env']=env;reset_original=env.reset
                    def reset(*args,**kwargs):
                        obs,info=reset_original(*args,**kwargs)
                        assert hashlib.sha256(obs.tobytes()).hexdigest()==case['baseline_initial_observation_sha256']
                        actual=truth(env);expected=case['baseline_initial_truth']
                        assert {k:actual[k] for k in expected}==expected
                        receipt.update(initial_full4pixels_equal=True,recorded_initial_truth_equal=True)
                        return obs,info
                    env.reset=reset;return env
                cohort.make_env=guarded_factory
                try:result,technical=cohort.episode(case,plan,path,execution)
                finally:cohort.make_env=factory
                result.update(baseline_identity_receipt=receipt,baseline_A=case['baseline_A'],
                              road_mask_calls=active['mask_calls'],road_mask_generation_wall_s=active['mask_wall_s'],
                              privileged_road_input=True,policy_changed=True,submission_candidate=False,
                              lost_A_completion=result['status']=='DNF')
                cohort.write(D/case['id']/'result.json',result)
                if technical:stop_reason='INCONCLUSIVE_TECHNICAL_OR_RESOURCE_BOUNDARY'
            results.append(result)
            report={'results':results,'stop_reason':stop_reason,'wall_s':time.perf_counter()-started,
                    'status_counts':{s:sum(a['status']==s for a in results) for s in ['COMPLETE','DNF','RESOURCE_CENSORED','UNEXECUTED']},
                    'single_intervention':'A fullcurrentGT -> B=A & ~rendererOcclusion; identical downstream processing',
                    'new_A_runs':0,'candidate_retries':0,'learning':0,'coefficient_tuning':0,'protected_runs':0,
                    'plan_sha256':cohort.sha(path),'original_v2_and_A_preserved':True,'submission_candidate':False}
            cohort.write(D/'comparison-report.json',report)
            print(json.dumps({k:result.get(k) for k in ['id','status','official_progress','official_lap_ms','damage','failure_type','charged_wrapper_actions','error']}),flush=True)
    finally:cohort.make_env=factory;cohort.PipeWorker=worker
    report.update(verdict='INCONCLUSIVE' if stop_reason else 'VISIBLE_OCCLUSION_DIAGNOSTIC_COMPLETED_NO_PROMOTION',
                  charged_wrapper_actions=json.loads((D/'budget.json').read_text())['actions'])
    cohort.write(D/'comparison-report.json',report);return int(bool(stop_reason))


if __name__=='__main__':raise SystemExit(main())
