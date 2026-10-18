"""One registered numerical recovery; retain original 555 code and results.

Disable bound-scaled gradient termination near zero gas. Admission residual,
branch, physical limits, clock target and iteration limit remain identical.
The exact transformed executable is retained privately and hashed in STARTED.
"""
import hashlib
import json
from pathlib import Path

G=Path(__file__).resolve().parents[1]
original=G/'retry/drift555_mechanism.py'
prior=json.loads((G/'retry/drift555_result.json').read_text())
assert prior['error']=='RuntimeError:LOW_SPEED_BRANCH_NOT_FOUND'
assert prior['cost']['model_ticks']==0 and prior['steady_stations_completed']==0
text=original.read_text()
changes=[
 ("haic-response555-private", "haic-response555-recovery-private"),
 ("G/'retry/drift555_contract.json'", "G/'retry/drift555_recovery_contract.json'"),
 ("G/'retry/drift555_result.json'", "G/'retry/drift555_recovery_result.json'"),
 ("SOURCES = ['retry/drift555_mechanism.py'", "SOURCES = ['retry/drift555_recovery.py', 'retry/drift555_mechanism.py'"),
 ("hypothesis='A quasi-steady", "recovery_reason='Original first-station near-zero-gas bound-scaled gradient termination left residual above1e-7. Disable gtol only; physical/admission/clock gates unchanged; original failure retained.',\n        original_contract_sha256='"+hashlib.sha256((G/'retry/drift555_contract.json').read_bytes()).hexdigest()+"',\n        hypothesis='A quasi-steady"),
 ("CPU_s=90, wall_s=120, analytic_wheel_evaluations=2000000", "CPU_s=89, wall_s=119, analytic_wheel_evaluations=1999472"),
 ("time.process_time()-cpu>=90 or time.perf_counter()-wall>=120", "time.process_time()-cpu>=89 or time.perf_counter()-wall>=119"),
 ("cost['analytic_wheel_evaluations']>=2000000", "cost['analytic_wheel_evaluations']>=1999472"),
 ("signal.ITIMER_PROF,90", "signal.ITIMER_PROF,89"),
 ("signal.ITIMER_REAL,120", "signal.ITIMER_REAL,119"),
 ("gtol=1e-10)", "gtol=None)"),
]
for old,new in changes:
    assert old in text,old
    text=text.replace(old,new)
assert "gtol=1e-10)" not in text
scope={'__name__':'registered_drift555_recovery','__file__':str(original)}
exec(compile(text,str(original)+'[registered-gtol-recovery]','exec'),scope)
# run() exclusively creates the recovery directory, so retain the transformed
# executable there as soon as the original save() first writes its STARTED pin.
base_save=scope['save']
def save(p,value):
    if p.name=='STARTED.json':
        executable=scope['D']/'executed-source-private.py'
        with executable.open('x') as f:f.write(text)
        executable.chmod(0o600)
        value=dict(value,executed_source_sha256=hashlib.sha256(text.encode()).hexdigest())
    return base_save(p,value)
scope['save']=save
scope['run']()
