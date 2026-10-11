"""Freeze a learned observation-only worker and run one recorded native episode."""
import argparse
import base64
import json
from pathlib import Path

import numpy as np

from retry import fresh_dev_distribution as native
from retry import paired_closed_loop as paired
from retry.qualify_pixel_package import PipeWorker


def copy_assets(plan,execution):
    for source,name in [(plan['boundary_path'],'boundary.py'),
                        (plan['student_feature_path'],'student.py'),
                        (plan['student_model_path'],'student.xml')]:
        target=execution[0]/name
        target.write_bytes(Path(source).read_bytes());target.chmod(0o444)
        assert native.sha(target)==plan['source_sha256'][source]
    return execution


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    path=parser.parse_args().plan.resolve();D=path.parent;p=json.loads(path.read_text())
    assert native.sha(path)==(D/'plan.sha256').read_text().split()[0]
    assert json.loads(Path(p['learning_result']).read_text())['status']=='PASS_FROZEN_STUDENT_FOR_ONE_NATIVE_PROBE'
    assert native.sha(Path(p['student_model_path']))==p['student_model_sha256']
    original_clone,original_worker=native.clone,native.PipeWorker
    masks=[];receipts=[]

    def clone(*args):return copy_assets(p,original_clone(*args))

    class RecordedStudent(PipeWorker):
        def __init__(self,*args):
            super().__init__(*args)
            assert self.ready['student_model_sha256']==p['student_model_sha256']
            assert self.ready['input_contract']=='float32(4,84,84) grayscale only'
            assert not self.ready['privileged_diagnostic']

        def call(self,operation,observation):
            assert observation.shape==(4,84,84) and observation.dtype==np.float32
            response,duration=super().call(operation,observation)
            mask=np.frombuffer(base64.b64decode(response.pop('student_mask_base64')),dtype=np.uint8).reshape(84,84).copy()
            P=((observation[-1]>.32)&(observation[-1]<.47)).astype(np.uint8)
            detail=response['student_receipt']
            assert np.isin(mask,[0,1]).all() and np.all(mask<=P)
            assert native.sha_bytes(mask)==detail['student_mask_sha256']
            assert native.sha_bytes(P)==detail['original_P_sha256']
            masks.append(mask);receipts.append({'operation':operation,'observation_sha256':native.sha_bytes(observation),**detail})
            return response,duration

    native.clone,native.PipeWorker=clone,RecordedStudent
    try:code=paired.main()
    finally:
        native.clone,native.PipeWorker=original_clone,original_worker
        target=D/'student-masks.npz';np.savez_compressed(target,masks=np.asarray(masks,dtype=np.uint8));target.chmod(0o600)
        native.write(D/'student-mask-receipts.json',receipts)
    result=json.loads((D/'paired-result.json').read_text())
    result.update(student_model_sha256=p['student_model_sha256'],student_mask_calls=len(masks),
                  privileged_runtime_input=False,competition_training_eligibility_verified=False,
                  policy_changed_relative_to_original_v2=True,policy_changed_during_episode=False,
                  champion_promotion=False,extra_teacher_or_renderer_calls=0)
    native.write(D/'student-result.json',result)
    return code


if __name__=='__main__':raise SystemExit(main())
