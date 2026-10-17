"""One bounded synthetic IO worker. Never imports or constructs a physics world."""
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import shutil
import time
import unittest

ROOT = Path('/workspace/haic-private-retry-20261009/stage467')
TMP = Path('/tmp/haic-retry-stage467-private')
RESERVE = 512 * 1024**2
CAP = 128 * 1024**2


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    start, cpu = time.monotonic(), time.process_time()
    free_before = {p: shutil.disk_usage(p).free for p in ('/tmp', '/workspace')}
    preserve_plan=json.loads((ROOT.parent/'stage465-plan-durable-private.json').read_text())
    protected={**preserve_plan['protected'],**preserve_plan['original408_preserve']}
    def verify_protected():
        for filename,expected in protected.items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest()!=expected:
                raise RuntimeError('protected_hash_changed:'+filename)
    verify_protected()
    def guard():
        if time.monotonic() - start >= 900 or time.process_time() - cpu >= 600:
            raise RuntimeError('worker_time_cap')
        for p, before in free_before.items():
            free = shutil.disk_usage(p).free
            if free < RESERVE or before - free > CAP:
                raise RuntimeError('volume_reserve_or_output_cap:' + p)
    guard()
    verify_protected()
    TMP.mkdir(mode=0o700)
    with (ROOT/'worker-start-private.json').open('x') as f:
        json.dump({'pid': os.getpid(), 'start_unix': time.time(), 'free_before': free_before}, f)
    from retry.evidence467_io import Evidence467
    from retry.pilot420_json import json_ready
    suite = unittest.defaultTestLoader.loadTestsFromName('retry.test_evidence467')
    test_start = time.monotonic()
    with (ROOT/'static-tests-private.log').open('x') as test_log:
        result = unittest.TextTestRunner(stream=test_log,verbosity=2).run(suite)
    test_wall = time.monotonic()-test_start
    guard()
    if not result.wasSuccessful():
        raise RuntimeError('static_integration_or_fault_test_failed')
    io = Evidence467(TMP/'benchmark', resource_guard=guard)
    rng = random.Random(467)
    vectors = [
        ('repeated', {'scope':'SYNTHETIC_ONLY', 'text':'관측0123456789\n' * 120000,
                      'bytes':b'\x00\xff' * 8192, 'minus_zero':-0.0}),
        ('mixed', {'scope':'SYNTHETIC_ONLY', 'text':'observation' * 60000,
                   'bytes':rng.randbytes(700000), 'rows':list(range(8192))}),
        ('entropy', {'scope':'SYNTHETIC_ONLY', 'bytes':rng.randbytes(1400000),
                     'all_fields':[None,True,False,1,-0.0,'한글',{},[]]}),
    ]
    measurements = []
    total_logical = total_physical = 0
    for name, value in vectors:
        guard()
        logical = (json.dumps(json_ready(value), ensure_ascii=False, indent=2,
                              allow_nan=False)+'\n').encode('utf-8')
        total_logical += len(logical)
        if total_logical > 32*1024**2:
            raise RuntimeError('aggregate_logical_cap')
        c, w = time.process_time(), time.monotonic()
        descriptor = io.write_receipt(name, value)
        write_cpu, write_wall = time.process_time()-c, time.monotonic()-w
        reads=[]
        for _ in range(3):
            c, w = time.process_time(), time.monotonic()
            restored=io.read_receipt(descriptor)
            if restored != value or descriptor['logical_sha256'] != hashlib.sha256(logical).hexdigest():
                raise RuntimeError('roundtrip_mismatch')
            reads.append({'CPU_s':time.process_time()-c,'wall_s':time.monotonic()-w})
        physical = descriptor['stored_bytes']
        total_physical += physical
        measurements.append({'case':name,'logical_bytes':len(logical),
                             'stored_bytes':physical,'stored_over_logical':physical/len(logical),
                             'write_including_full_readback_CPU_s':write_cpu,
                             'write_including_full_readback_wall_s':write_wall,
                             'additional_full_readbacks':reads,'descriptor':descriptor})
    guard()
    # Existing gzip is copied byte-for-byte: no second compression-ratio factor.
    shutil.copytree(TMP, ROOT/'retained-synthetic')
    guard()
    verify_protected()
    files=[p for p in TMP.rglob('*') if p.is_file()]
    peak_output=sum(p.stat().st_size for p in files)
    answer={'stage':467,'status':'IO_SYNTHETIC_GATE_PASSED','tests':result.testsRun,
            'test_wall_s':test_wall,'benchmark':measurements,
            'benchmark_total_logical_bytes':total_logical,'benchmark_total_stored_bytes':total_physical,
            'retained_tmp_file_bytes':peak_output,
            'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'peak_scope':'whole worker high-water RSS; retained file bytes are final observed allocation, not sampled transient RSS',
            'CPU_s':time.process_time()-cpu,'wall_s':time.monotonic()-start,
            'free_before':free_before,'free_after':{p:shutil.disk_usage(p).free for p in free_before},
            'new_physics_native_world_reset':0,
            'protected_hashes_verified':len(protected),
            'uncertainty':'Three synthetic cases, three warm full reads each; excludes cold-cache latency and representative real-run compression prediction. Full JSON parse remains in memory.'}
    with (ROOT/'result-private.json').open('x') as f:
        json.dump(answer,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps({k:v for k,v in answer.items() if k!='benchmark'},ensure_ascii=False))


if __name__ == '__main__':
    main()
