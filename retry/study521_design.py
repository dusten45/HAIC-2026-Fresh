"""One preregistered deterministic bounded path search on current saved map."""
import datetime,hashlib,json,signal,time
from pathlib import Path
from retry.path521_control import solve
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response521-private')

def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/study521_contract.json').read_text())
    if (D/'DESIGN_STARTED.json').exists():raise RuntimeError('NO_DESIGN_RETRY')
    for n,h in c['model_source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(c['deadline_utc'])
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('DESIGN_CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,60)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('DESIGN_WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,90)
    with (D/'DESIGN_STARTED.json').open('x') as f:json.dump(dict(contract_sha256=hashlib.sha256((G/'retry/study521_contract.json').read_bytes()).hexdigest()),f)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());baseline,candidate,out,coeff=solve(static)
    for name,data in [('frozen-paths-private.json',dict(baseline=baseline,spline=candidate)),('coefficients-private.json',coeff)]:
        p=D/name
        with p.open('x') as f:json.dump(data,f,indent=2)
        p.chmod(0o600)
    out.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_integrator_ticks=0,native_actions=0,native_resets=0,frozen_paths_private_sha256=hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest(),scope='Exactly194 objective calls on currentDEV map, not old lost-run reproduction; scalar clock is a screen, not actual gain or feasible bound.')
    with (G/'retry/study521_design.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
