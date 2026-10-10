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
import signal
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
        self.closed = False
        self.observed_peak_rss_bytes = 0
        self.memory_limit_bytes = 1_024_000_000
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
            self.check_memory()
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Worker response deadline')
            if not self.selector.select(min(remaining, .05)):
                continue
            try:
                chunk = os.read(self.process.stdout.fileno(),65536)
            except BlockingIOError:
                continue
            if not chunk: raise RuntimeError('Worker exited before response')
            self.buffer.extend(chunk)
            if len(self.buffer)>1024*1024: raise RuntimeError('Worker response size')
        line,_,rest = self.buffer.partition(b'\n')
        self.buffer = bytearray(rest)
        return json.loads(line)

    def check_memory(self):
        try:
            lines = Path('/proc')/str(self.process.pid)/'status'
            for line in lines.read_text().splitlines():
                if line.startswith(('VmRSS:', 'VmHWM:')):
                    self.observed_peak_rss_bytes = max(self.observed_peak_rss_bytes,
                                                       int(line.split()[1])*1024)
        except (FileNotFoundError, ProcessLookupError):
            return
        if self.observed_peak_rss_bytes > self.memory_limit_bytes:
            raise MemoryError('Participant RSS exceeded README memory limit')

    def call(self, operation, observation):
        started = time.perf_counter(); deadline = time.monotonic()+5
        request = {'op':operation,'observation':base64.b64encode(observation.tobytes()).decode('ascii')}
        payload = (json.dumps(request)+'\n').encode()
        writer = selectors.DefaultSelector(); writer.register(self.process.stdin,selectors.EVENT_WRITE)
        offset = 0
        try:
            while offset<len(payload):
                self.check_memory()
                remaining = deadline-time.monotonic()
                if remaining <= 0: raise TimeoutError('Worker input deadline')
                if not writer.select(min(remaining, .05)): continue
                try:
                    offset += os.write(self.process.stdin.fileno(),payload[offset:offset+65536])
                except BlockingIOError:
                    continue
                except BrokenPipeError as error:
                    raise RuntimeError('Worker exited during request') from error
        finally: writer.close()
        response = self.read(deadline)
        return response,(time.perf_counter()-started)*1000

    def close(self):
        if self.closed:
            return self.reap_receipt
        started = time.perf_counter()
        if self.process.poll() is None: self.process.kill()
        self.process.wait(timeout=2)
        self.selector.close()
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr): stream.close()
        try:
            os.waitpid(self.process.pid, os.WNOHANG)
            reaped = False
        except ChildProcessError:
            reaped = True
        absent = not (Path('/proc')/str(self.process.pid)).exists()
        self.reap_receipt = {'pid':self.process.pid,'returncode':self.process.returncode,
                             'waitpid_no_child':reaped,'proc_pid_absent':absent,
                             'process_reaped':reaped and absent,
                             'close_ms':(time.perf_counter()-started)*1000}
        self.closed = True
        return self.reap_receipt


def fault_probe(command, clean, environment, observation, expected_first_action, mode):
    """Two supervisor faults on the unchanged loaded candidate, without physics."""
    assert mode in ('timeout', 'abnormal_exit')
    worker = None
    detected = False
    record = {'mode':mode,'policy_modified':False,'new_environment_actions':0}
    try:
        worker = PipeWorker(command, clean, environment)
        reset, reset_ms = worker.call('reset', observation)
        response, act_ms = worker.call('act', observation)
        assert np.asarray(response['action'],dtype=np.float32).tobytes() == expected_first_action.tobytes()
        assert reset['ok'] and not reset['python_audit_denied_events'] and not response['python_audit_denied_events']
        assert worker.cold_start_ms <= 10000 and reset_ms <= 5000 and act_ms <= 5000
        record.update(candidate_first_action_exact=True, cold_start_ms=worker.cold_start_ms,
                      reset_including_ipc_ms=reset_ms, first_act_including_ipc_ms=act_ms,
                      actor_CPU_s=response['actor_cumulative_CPU_s'],
                      participant_peak_rss_mib=max(worker.ready['rss_mib'],reset['rss_mib'],response['rss_mib']))
        os.kill(worker.process.pid, signal.SIGSTOP if mode == 'timeout' else signal.SIGKILL)
        started = time.perf_counter()
        try:
            worker.call('act', observation)
        except (TimeoutError, RuntimeError) as error:
            detected = (isinstance(error, TimeoutError) if mode == 'timeout'
                        else isinstance(error, RuntimeError))
            record.update(detected_error=repr(error), detection_ms=(time.perf_counter()-started)*1000)
    finally:
        if worker:
            record.update(reaping=worker.close(), observed_peak_rss_bytes=worker.observed_peak_rss_bytes)
    record['passed'] = detected and record.get('reaping',{}).get('process_reaped',False)
    return record


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
            assert actual.tobytes() == action.tobytes(), 'Saved action mismatch at index '+str(index)
            assert not response['python_audit_denied_events']
            matched += 1; compute.append(response['act_compute_ms']); ipc.append(duration)
            peak = max(peak,response['rss_mib'])
            observation = np.concatenate([observation[1:],frames[index+1:index+2]])
            assert hashlib.sha256(observation.tobytes()).hexdigest() == hashes['after'][index]
            observations += 1
        report['actor_CPU_s'] = response['actor_cumulative_CPU_s']
        assert worker.cold_start_ms <= 10000 and reset_ms <= 5000
        assert max(ipc) <= 5000 and peak <= 1024
        assert peak*1024*1024 <= worker.memory_limit_bytes
        reset_prefix = plan.get('reset_boundary_prefix_actions',0)
        if reset_prefix:
            assert 0 < reset_prefix <= len(expected)
            observation = np.repeat(frames[:1],4,axis=0)
            reset2, reset2_ms = worker.call('reset',observation)
            assert reset2['ok'] and not reset2['python_audit_denied_events']
            prefix_matches = 0
            for index in range(reset_prefix):
                check_window()
                response,duration = worker.call('act',observation)
                actual = np.asarray(response['action'],dtype=np.float32)
                assert actual.shape == (3,) and np.isfinite(actual).all()
                assert np.all(actual >= [-1,0,0]) and np.all(actual <= [1,1,1])
                assert actual.tobytes() == expected[index].tobytes(), 'Post-reset action mismatch'
                assert not response['python_audit_denied_events']
                prefix_matches += 1; compute.append(response['act_compute_ms']); ipc.append(duration)
                peak = max(peak,response['rss_mib'])
                observation = np.concatenate([observation[1:],frames[index+1:index+2]])
                assert hashlib.sha256(observation.tobytes()).hexdigest() == hashes['after'][index]
            report.update(reset_boundary_prefix_expected=reset_prefix,reset_boundary_prefix_matched=prefix_matches,
                          second_reset_including_ipc_ms=reset2_ms,second_reset_compute_ms=reset2['reset_compute_ms'])
            assert reset2_ms <= 5000 and max(ipc) <= 5000 and peak*1024*1024 <= worker.memory_limit_bytes
            report['actor_CPU_s'] = response['actor_cumulative_CPU_s']
        report['verdict'] = 'PASS_SAME_HOST_CLEAN_CPU_PIXEL_REPLAY'
    except Exception as exc:
        error = repr(exc); report.update(verdict='FAIL_OR_INCONCLUSIVE_NO_POLICY_CHANGE',error=error)
    finally:
        if worker:
            report['normal_worker_reaping'] = worker.close()
            report['supervisor_observed_peak_rss_bytes'] = worker.observed_peak_rss_bytes
            if not report['normal_worker_reaping']['process_reaped']:
                error = 'Normal worker was not reaped'
                report.update(verdict='FAIL_OR_INCONCLUSIVE_NO_POLICY_CHANGE',error=error)
    if error is None and plan.get('minimal_supervisor_faults',False):
        try:
            command = [sys.executable,'-I','-B',str(worker_path),str(package)]
            initial = np.repeat(frames[:1],4,axis=0)
            faults = []
            for mode in ('timeout','abnormal_exit'):
                check_window()
                faults.append(fault_probe(command,clean,environment,initial,expected[0],mode))
            report['minimal_supervisor_faults'] = faults
            assert all(item['passed'] for item in faults), 'Supervisor fault or process reaping failed'
        except Exception as exc:
            error = repr(exc)
            report.update(verdict='FAIL_OR_INCONCLUSIVE_NO_POLICY_CHANGE',error=error)
    stats = lambda values: {'median_ms':float(np.median(values)),'p95_ms':float(np.percentile(values,95)),
                            'max_ms':max(values)} if values else None
    report.update(expected_actions=len(expected),matched_actions=matched,matched_observation_hashes=observations,
                  act_compute=stats(compute),act_including_ipc=stats(ipc),peak_actor_RSS_mib=peak,
                  elapsed_s=time.perf_counter()-started,cold_start_sessions=1,protocol_ops=['reset','act'],
                  worker_request_keys=['op','observation'])
    report['memory_limit_bytes'] = 1_024_000_000
    (directory/'replay-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report.get(key) for key in ('verdict','expected_actions','matched_actions','matched_observation_hashes',
                                                   'cold_start_ms','reset_including_ipc_ms','act_compute','act_including_ipc',
                                                   'peak_actor_RSS_mib','elapsed_s','new_environment_actions','error')}))
    return int(error is not None)


if __name__ == '__main__': sys.exit(main())
