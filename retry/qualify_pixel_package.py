"""Replay one saved pixel episode through an unchanged ZIP in a clean process.

This same-host qualification does not create an environment or establish
fresh-machine or official-server parity. Private replay data never enter the
worker filesystem or request metadata.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PipeWorker:
    def __init__(self, command, directory, environment):
        started = time.perf_counter()
        self.process = subprocess.Popen(command,cwd=directory,env=environment,
                                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,bufsize=0,close_fds=True)
        os.set_blocking(self.process.stdin.fileno(),False)
        os.set_blocking(self.process.stdout.fileno(),False)
        self.buffer = bytearray()
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout,selectors.EVENT_READ)
        try:
            self.ready = self.read(time.monotonic()+10)
            assert self.ready['ready'] and not self.ready['simulator_imported']
            self.cold_start_ms = (time.perf_counter()-started)*1000
        except Exception:
            self.close()
            raise

    def read(self, deadline):
        while b'\n' not in self.buffer:
            remaining = deadline-time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError('Worker response deadline')
            chunk = os.read(self.process.stdout.fileno(),65536)
            if not chunk: raise RuntimeError('Worker exited before response')
            self.buffer.extend(chunk)
            if len(self.buffer)>1024*1024: raise RuntimeError('Worker response size')
        line,_,rest = self.buffer.partition(b'\n')
        self.buffer = bytearray(rest)
        return json.loads(line)

    def call(self, operation, observation):
        started = time.perf_counter(); deadline = time.monotonic()+5
        request = {'op':operation,'observation':base64.b64encode(observation.tobytes()).decode('ascii')}
        payload = (json.dumps(request)+'\n').encode()
        writer = selectors.DefaultSelector(); writer.register(self.process.stdin,selectors.EVENT_WRITE)
        offset = 0
        try:
            while offset<len(payload):
                remaining = deadline-time.monotonic()
                if remaining <= 0 or not writer.select(remaining): raise TimeoutError('Worker input deadline')
                offset += os.write(self.process.stdin.fileno(),payload[offset:offset+65536])
        finally: writer.close()
        response = self.read(deadline)
        return response,(time.perf_counter()-started)*1000

    def close(self):
        if self.process.poll() is None: self.process.kill()
        self.process.wait(timeout=2)
        self.selector.close()
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr): stream.close()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan',required=True,type=Path)
    args = parser.parse_args(); plan_path = args.plan.resolve(); directory = plan_path.parent
    plan = json.loads(plan_path.read_text()); started = time.perf_counter()
    def check_window():
        current = datetime.datetime.now(datetime.timezone.utc)
        assert datetime.datetime.fromisoformat(plan['start_utc']) <= current < datetime.datetime.fromisoformat(plan['deadline_utc'])
    check_window()
    assert sha(plan_path) == (directory/'plan.sha256').read_text().split()[0]
    for name,wanted in plan['source_sha256'].items(): assert sha(Path(name)) == wanted,name
    for name,wanted in plan['replay_source_sha256'].items(): assert sha(Path(name)) == wanted,name
    archive = Path(plan['candidate']['archive_path'])
    assert sha(archive) == plan['candidate']['archive_sha256']
    clean = Path(tempfile.mkdtemp(prefix='haic-pixel-qualification-'))
    clean.chmod(0o700); package = clean/'package'; package.mkdir()
    shutil.copyfile(archive,clean/'candidate.zip'); assert sha(clean/'candidate.zip') == sha(archive)
    with zipfile.ZipFile(clean/'candidate.zip') as zipped:
        assert set(zipped.namelist()) == set(plan['candidate']['members_sha256'])
        for name,wanted in plan['candidate']['members_sha256'].items():
            relative = Path(name); assert not relative.is_absolute() and '..' not in relative.parts
            data = zipped.read(name); assert hashlib.sha256(data).hexdigest() == wanted
            target = package/relative; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data); target.chmod(0o444)
    worker_path = clean/'worker.py'; shutil.copyfile(plan['worker_path'],worker_path); worker_path.chmod(0o444)
    assert sha(worker_path) == sha(Path(plan['worker_path']))
    for path in sorted(package.rglob('*'),reverse=True):
        if path.is_dir(): path.chmod(0o555)
    package.chmod(0o555)
    (clean/'home').mkdir(); (clean/'tmp').mkdir()
    environment = {'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','HOME':str(clean/'home'),
                   'TMPDIR':str(clean/'tmp'),'LANG':'C.UTF-8','OPENBLAS_NUM_THREADS':'1',
                   'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','CUDA_VISIBLE_DEVICES':'',
                   'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
    saved = np.load(plan['replay_npz_path']); frames = saved['frames'].astype(np.float32)/255
    expected = saved['actions']; hashes = json.loads(Path(plan['observation_hashes_path']).read_text())
    assert frames.shape == (len(expected)+1,84,84) and expected.shape[1:] == (3,)
    assert len(expected) == plan['expected_actions'] and len(hashes['after']) == len(expected)
    observation = np.repeat(frames[:1],4,axis=0)
    assert hashlib.sha256(observation.tobytes()).hexdigest() == hashes['initial']
    worker = None; matched = observations = 0; compute = []; ipc = []; peak = 0.0; error = None
    report = {'plan_sha256':sha(plan_path),'archive_sha256':sha(archive),
              'clean_directory':str(clean),'new_environment_actions':0,'new_reset_or_step_calls':0,
              'HOLDOUT_details_opened':False,'SEALED_opened':False,'policy_changes':0,
              'isolation_scope':'Same cloud/host and installed runtime. Fresh temporary cwd and extracted immutable package, independent Python -I -B process, sanitized environment, one-core affinity, Python file/import audit. No fresh VM/container/OS sandbox/official-server parity.'}
    try:
        worker = PipeWorker([sys.executable,'-I','-B',str(worker_path),str(package)],clean,environment)
        report['worker_ready'] = worker.ready; report['cold_start_ms'] = worker.cold_start_ms
        assert not worker.ready['python_audit_denied_events']
        assert all(Path(path).is_relative_to(package) for path in worker.ready['policy_modules'].values())
        for name,path in worker.ready['policy_modules'].items():
            relative = str(Path(path).relative_to(package))
            assert sha(Path(path)) == plan['candidate']['members_sha256'][relative]
        reset,reset_ms = worker.call('reset',observation)
        assert reset['ok'] and not reset['python_audit_denied_events']
        report.update(reset_including_ipc_ms=reset_ms,reset_compute_ms=reset['reset_compute_ms'])
        peak = max(worker.ready['rss_mib'],reset['rss_mib'])
        observations = 1
        for index,action in enumerate(expected):
            check_window()
            response,duration = worker.call('act',observation)
            actual = np.asarray(response['action'],dtype=np.float32)
            assert actual.shape == (3,) and np.isfinite(actual).all()
            assert np.all(actual >= [-1,0,0]) and np.all(actual <= [1,1,1])
            assert np.array_equal(actual,action), 'Saved action mismatch at index '+str(index)
            assert not response['python_audit_denied_events']
            matched += 1; compute.append(response['act_compute_ms']); ipc.append(duration)
            peak = max(peak,response['rss_mib'])
            observation = np.concatenate([observation[1:],frames[index+1:index+2]])
            assert hashlib.sha256(observation.tobytes()).hexdigest() == hashes['after'][index]
            observations += 1
        report['actor_CPU_s'] = response['actor_cumulative_CPU_s']
        assert worker.cold_start_ms <= 10000 and reset_ms <= 5000
        assert max(ipc) <= 5000 and peak <= 1024
        report['verdict'] = 'PASS_SAME_HOST_CLEAN_CPU_PIXEL_REPLAY'
    except Exception as exc:
        error = repr(exc); report.update(verdict='FAIL_OR_INCONCLUSIVE_NO_POLICY_CHANGE',error=error)
    finally:
        if worker: worker.close()
    stats = lambda values: {'median_ms':float(np.median(values)),'p95_ms':float(np.percentile(values,95)),
                            'max_ms':max(values)} if values else None
    report.update(expected_actions=len(expected),matched_actions=matched,matched_observation_hashes=observations,
                  act_compute=stats(compute),act_including_ipc=stats(ipc),peak_actor_RSS_mib=peak,
                  elapsed_s=time.perf_counter()-started,cold_start_sessions=1,protocol_ops=['reset','act'],
                  worker_request_keys=['op','observation'])
    (directory/'replay-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report.get(key) for key in ('verdict','expected_actions','matched_actions','matched_observation_hashes',
                                                   'cold_start_ms','reset_including_ipc_ms','act_compute','act_including_ipc',
                                                   'peak_actor_RSS_mib','elapsed_s','new_environment_actions','error')}))
    return int(error is not None)


if __name__ == '__main__': sys.exit(main())
