"""One frozen near-lateral-budget contrast from the adopted normal24 package."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "a36b9a771e5ed4289c4b4210cc832ae5984bbd600987f1ff2493a56058d4e3e0"
OLD = b"super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 6.0)"
NEW = b"super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)"


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    members = {}
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'x') as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == 'agent.py':
                assert data.count(OLD) == 1
                data = data.replace(OLD, NEW)
                compile(data, item.filename, 'exec')
            members[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_members=['agent.py'],copied_other_members_byte_for_byte=len(members)-1,
        members_sha256=members,near_lateral_budget=8.0,speed_cap45_normal24_original_P_unchanged=True)
