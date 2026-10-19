"""Package, isolate, and drive the current observation-only Agent on approved DEV.

Only this external harness sees the environment/case. IPC carries pixels only.
"""
import argparse
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import select
import subprocess
import sys
import time
import zipfile
import fcntl

START=time.perf_counter();CPU=time.process_time()
CHILD_START=resource.getrusage(resource.RUSAGE_CHILDREN)
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path('/workspace/haic-submission-private')
BANNED={'ctypes','importlib','multiprocessing','os','pathlib','resource','shutil','signal','socket','subprocess','sys'}
CALLS={'compile','eval','exec','__import__'}


def dump(p,q):p.write_text(json.dumps(q,indent=2,allow_nan=False)+'\n')


def package(out, source=None):
    source=Path(source) if source is not None else ROOT/'submit_agent/agent.py'
    code=source.read_text();tree=ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module]
            assert all(n.split('.')[0] not in BANNED for n in names),'BANNED_IMPORT'
            assert all(n.split('.')[0] in {'numpy','cv2','math'} for n in names),'UNEXPECTED_DEPENDENCY'
        if isinstance(node,ast.Call):
            name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
            assert name not in CALLS,'BANNED_DYNAMIC_CALL'
        if isinstance(node,ast.Name):assert node.id not in {'open','globals','locals','getattr','setattr','vars'},'UNEXPECTED_SIDE_CHANNEL'
    target=out/'package';target.mkdir();(target/'agent.py').write_text(code)
    archive=out/'submission.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:z.write(target/'agent.py','agent.py')
    with zipfile.ZipFile(archive) as z:
        assert z.namelist()==['agent.py'] and len(z.infolist())<=1000
        assert sum(i.file_size for i in z.infolist())<=2*1024**3
        assert all(i.file_size<=500*1024**2 and i.file_size/max(1,i.compress_size)<=100 for i in z.infolist())
        assert archive.stat().st_size<=500*1024**2
        assert z.read('agent.py')==(target/'agent.py').read_bytes()
    return target/'agent.py',hashlib.sha256(source.read_bytes()).hexdigest()


class Client:
    def __init__(self,source,out):
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        self.err=(out/'worker-stderr-private.log').open('wb');begin=time.perf_counter()
        self.p=subprocess.Popen([sys.executable,'-u',str(ROOT/'retry/submit_worker.py'),str(source)],
            cwd=source.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,env=env)
        try:
            self.ready=self.receive(10.);self.startup=time.perf_counter()-begin
            assert self.ready.get('ready') and self.startup<10.,'STARTUP_LIMIT'
        except BaseException:
            self.p.kill();self.p.wait();self.err.close();raise
    def receive(self,timeout):
        if not select.select([self.p.stdout],[],[],timeout)[0]:raise TimeoutError('WORKER_DEADLINE')
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('WORKER_EXIT')
        value=json.loads(line)
        if 'error' in value:raise RuntimeError(value['error'])
        return value
    def request(self,command,obs):
        begin=time.perf_counter();self.p.stdin.write(command+obs.tobytes(order='C'));self.p.stdin.flush()
        q=self.receive(5.)
        if command==b'A':
            import numpy as np
            a=np.asarray(q['action'],dtype=np.float32)
            assert a.shape==(3,) and np.isfinite(a).all()
            assert -1<=a[0]<=1 and 0<=a[1]<=1 and 0<=a[2]<=1
        total=time.perf_counter()-begin
        assert total<5.,'WHOLE_REQUEST_DEADLINE'
        assert q['max_RSS_KiB']<1024*1024,'RSS_LIMIT'
        q['whole_request_wall_s']=total
        return q
    def close(self):
        if self.p.poll() is None:
            try:self.p.stdin.write(b'Q');self.p.stdin.flush();self.p.wait(timeout=2)
            except BaseException:self.p.kill();self.p.wait()
        self.err.close()


def ledger_charge(kind):
    path=PRIVATE/'usage-private.json';lock=PRIVATE/'usage.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        q=json.loads(path.read_text()) if path.exists() else dict(research_start=22211,actions=0,worlds=0,resets=0,raw=0,reserve=84000,reserve_used=0)
        if kind=='actions' and q['actions']>=22211:raise RuntimeError('RESEARCH_LEDGER_EXHAUSTED')
        q[kind]+=1;q['research_remaining']=22211-q['actions']
        temp=path.with_suffix('.tmp');dump(temp,q);os.replace(temp,path)
    return q


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);parser.add_argument('--steps',type=int,default=120)
    args=parser.parse_args();assert 0<args.steps<=2000
    PRIVATE.mkdir(mode=0o700,exist_ok=True);out=PRIVATE/args.label;out.mkdir(mode=0o700,exist_ok=False)
    source,source_hash=package(out);client=None;env=None;rows=[];status='TECHNICAL_FAILURE';error=None;reset=None;summary={}
    try:
        client=Client(source,out)
        import numpy as np
        # Mandatory reset/action/shape/memory checks use the exact packaged Agent
        # before any environment creation. No privileged input enters its process.
        blank=np.zeros((4,84,84),np.float32)
        client.request(b'R',blank);one=client.request(b'A',blank)
        client.request(b'R',blank);two=client.request(b'A',blank)
        assert one['action']==two['action'],'RESET_LEAK'
        os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
        import cv2
        from gymnasium.wrappers import TimeLimit
        from core.vendor.car_racing import CarRacing
        from env_wrapper import CarEnvironment
        case=json.loads(Path('/workspace/haic-response541-private/approved-case-private.json').read_text())
        ledger_charge('worlds');raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=2000*4+200),**case['wrapper'])
        ledger_charge('resets');obs,info=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
        assert obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all()
        reset=client.request(b'R',obs);epoch=raw.t
        cv2.imwrite(str(out/'initial-private.png'),np.rint(obs[-1]*255).astype(np.uint8))
        status='ACTION_LIMIT_CENSORED'
        with (out/'decisions-private.jsonl').open('w') as log:
            for i in range(args.steps):
                if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):status='AUTHORIZATION_CENSORED';break
                q=client.request(b'A',obs);a=np.asarray(q['action'],np.float32)
                before=raw.t;ledger_charge('actions');obs,reward,terminated,truncated,info=env.step(a)
                ticks=round((raw.t-before)/.02)
                row=dict(index=i+1,action=q['action'],diagnostics=q.get('diagnostics'),whole_act_wall_s=q['whole_request_wall_s'],worker_wall_s=q['wall_s'],worker_CPU_s=q['CPU_s'],max_RSS_KiB=q['max_RSS_KiB'],raw=ticks,progress=info['progress'],damage=info['damage'],true_hull_speed=float(np.linalg.norm(raw.car.hull.linearVelocity)))
                rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
                if i%20==0:cv2.imwrite(str(out/f'frame-{i+1:04d}-private.png'),np.rint(obs[-1]*255).astype(np.uint8))
                if terminated or truncated:
                    status='FINISHED' if info.get('finished') else 'DNF';break
            if args.steps==2000 and len(rows)==2000 and not info.get('finished'):status='DNF_ACTION_HORIZON'
        summary=dict(progress=info.get('progress'),damage=info.get('damage'),finish_time_s=raw.finish_time_s,
            lap_time_s=(raw.finish_time_s-epoch) if raw.finish_time_s is not None else None,
            drive_raw=round((raw.t-epoch)/.02),reset_physics_raw=round(epoch/.02),retire_reason=info.get('retire_reason'))
    except BaseException as exc:
        status='TECHNICAL_FAILURE'
        error=type(exc).__name__+':'+str(exc)
        import traceback
        (out/'error-private.txt').write_text(traceback.format_exc())
    finally:
        if env is not None:env.close()
        if client is not None:client.close()
        usage=json.loads((PRIVATE/'usage-private.json').read_text()) if (PRIVATE/'usage-private.json').exists() else {}
        # Raw counts are finalized once; action dispatches are precharged above.
        if rows:
            path=PRIVATE/'usage-private.json';usage['raw']+=sum(q['raw'] for q in rows)+summary.get('reset_physics_raw',51);dump(path,usage)
        child=resource.getrusage(resource.RUSAGE_CHILDREN)
        total_cpu=time.process_time()-CPU+child.ru_utime+child.ru_stime-CHILD_START.ru_utime-CHILD_START.ru_stime
        result=dict(label=args.label,status=status,error=error,source_sha256=source_hash,
            steps=len(rows),startup_wall_s=client.startup if client is not None else None,
            reset_wall_s=reset['whole_request_wall_s'] if reset else None,
            max_whole_act_wall_s=max((r['whole_act_wall_s'] for r in rows),default=None),
            max_worker_RSS_KiB=max((r['max_RSS_KiB'] for r in rows),default=None),
            summary=summary,usage=usage,wall_s=time.perf_counter()-START,CPU_s=total_cpu,
            official_server_runtime_parity=False,inputs='Only binaryfloat32 observation transmitted; no metadata/state/reward/case in worker',archive='submission.zip')
        dump(out/'result-private.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
