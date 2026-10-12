"""One normal24->32 sensitivity point on the unchanged near8/cap45 champion."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = 'b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e'
OBSERVER_SHA256 = '4afda780a78309da90e7f50cbe926520b2bc09908599923e447966b95dc354ea'
OLD = b'super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)'
NEW = b'super().__init__(11.4142485314592, -6.545558315185489, 45.0, 32.0, 8.0)'


def build(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==BASE_SHA256
    hashes={};changed=[]
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(output,'x') as dst:
        for item in src.infolist():
            data=src.read(item.filename)
            if item.filename=='agent.py':
                assert data.count(OLD)==1
                data=data.replace(OLD,NEW);changed.append(item.filename);compile(data,item.filename,'exec')
            hashes[item.filename]=hashlib.sha256(data).hexdigest();dst.writestr(item,data)
    assert changed==['agent.py'];output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        members_sha256=hashes,changed_members=changed,other_members_identical=len(hashes)-1,
        normal_budget=32.,near_budget=8.,cap_m_s=45.,original_steering_and_P_unchanged=True,
        hull_reference_correction_included=False)


def build_observer(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==OBSERVER_SHA256
    text=source.read_text();old='assert (agent.lateral_fast, agent.lateral_safe) == (24.0, 8.0)'
    assert text.count(old)==1
    text=text.replace(old,'assert (agent.lateral_fast, agent.lateral_safe) == (32.0, 8.0)')
    compile(text,str(output),'exec')
    with output.open('x') as f:f.write(text)
    output.chmod(0o600)
