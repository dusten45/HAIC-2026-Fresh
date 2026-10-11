"""Only two fixed same-axis boundary candidates from the adopted12 package."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "05c0c6ff68bf3b31b49266605eda41e16ed98ae1f371347f9814c4dc8793a523"
CANDIDATES = (14.0, 16.0)
OLD = b"super().__init__(11.4142485314592, -6.545558315185489, 40.0, 12.0, 5.0)"


def build(source, output, normal_lateral):
    source, output = Path(source), Path(output)
    normal_lateral = float(normal_lateral)
    assert normal_lateral in CANDIDATES
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    replacement = ("super().__init__(11.4142485314592, -6.545558315185489, "
                   f"40.0, {normal_lateral:.1f}, 5.0)").encode()
    members, changed = {}, []
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "x") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == 'agent.py':
                assert data.count(OLD) == 1
                data = data.replace(OLD, replacement)
                compile(data, 'agent.py', 'exec')
                changed.append(item.filename)
            members[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    assert changed == ['agent.py']
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        normal_lateral=normal_lateral, changed_members=changed,
        copied_other_members_byte_for_byte=len(members)-1, members_sha256=members)
