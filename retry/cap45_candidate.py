"""One frozen global-cap contrast from the adopted normal24 package."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "126348c69d3ed9d6456a93ad6d6dd74f199c515aa150e07a23f016d9195a2e60"
OLD = b"super().__init__(11.4142485314592, -6.545558315185489, 42.5, 24.0, 5.0)"
NEW = b"super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 5.0)"


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
        members_sha256=members,speed_cap=45.0,normal24_near5_and_original_P_unchanged=True)
