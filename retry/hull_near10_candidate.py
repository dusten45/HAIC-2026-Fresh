"""One registered speed interaction on the unchanged hull-reference tracker.

Reuse the fixed179 structure; change only Agent's near budget8 to10.
The original-controller near10 failure remains a required comparison case.
"""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = 'de131a7224123db47e97c35352ed41aae7162f92ba0393417f17e8bf8a272743'
OBSERVER_SHA256 = '6489d40ef14415c8e4cfd4190da02c1d5a997248d17e4ad26fbd0b6a82014a62'
OLD = b'super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)'
NEW = b'super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 10.0)'


def build(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==BASE_SHA256
    hashes={};changed=[]
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(output,'x') as dst:
        for item in src.infolist():
            data=src.read(item.filename)
            if item.filename=='agent.py':
                assert data.count(OLD)==1
                data=data.replace(OLD,NEW);changed.append(item.filename)
                compile(data,item.filename,'exec')
            hashes[item.filename]=hashlib.sha256(data).hexdigest();dst.writestr(item,data)
    assert changed==['agent.py'];output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256=hashes,
        changed_members=changed,other_members_identical=len(hashes)-1,
        near_budget=10.,normal_budget=24.,cap_m_s=45.,hull_reference_tracking_unchanged=True,
        pedal_law_and_perception_planning_unchanged=True)


def build_observer(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==OBSERVER_SHA256
    text=source.read_text();old='assert (agent.lateral_fast, agent.lateral_safe) == (24.0, 8.0)'
    assert text.count(old)==1
    text=text.replace(old,'assert (agent.lateral_fast, agent.lateral_safe) == (24.0, 10.0)')
    compile(text,str(output),'exec')
    with output.open('x') as f:f.write(text)
    output.chmod(0o600)
