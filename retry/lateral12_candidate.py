"""Build one fixed normal-lateral12 boundary candidate from adopted10."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "a140aaa4b008838773c4ce83fead5b639d28ab777ac3eaac2493cad95353a68d"
OLD = b"super().__init__(11.4142485314592, -6.545558315185489, 40.0, 10.0, 5.0)"
NEW = b"super().__init__(11.4142485314592, -6.545558315185489, 40.0, 12.0, 5.0)"


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    members, changed = {}, []
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "x") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "agent.py":
                assert data.count(OLD) == 1
                data = data.replace(OLD, NEW)
                compile(data, "agent.py", "exec")
                changed.append(item.filename)
            members[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    assert changed == ["agent.py"]
    output.chmod(0o600)
    return {"base_archive_sha256": BASE_SHA256,
            "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "members_sha256": members, "changed_members": changed,
            "change": "normal10 to12; near5 and cap40 fixed",
            "copied_other_members_byte_for_byte": len(members) - 1}
