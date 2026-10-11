"""Make the fixed normal-lateral8 candidate from the unchanged134 package."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "c66e2f3bfc42543a8bdcdc821898eb0fd8377ab54929ebcc46708cbee0667d55"
OLD = b"super().__init__(11.4142485314592, -6.545558315185489, 40.0, 7.0, 5.0)"
NEW = b"super().__init__(11.4142485314592, -6.545558315185489, 40.0, 8.0, 5.0)"


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    hashes, changed = {}, []
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "x") as dst:
        for member in src.infolist():
            data = src.read(member.filename)
            if member.filename == "agent.py":
                assert data.count(OLD) == 1
                data = data.replace(OLD, NEW)
                compile(data, "agent.py", "exec")
                changed.append(member.filename)
            hashes[member.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(member, data)
    assert changed == ["agent.py"]
    output.chmod(0o600)
    return {"source_archive_sha256": BASE_SHA256,
            "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "members_sha256": hashes, "changed_members": changed,
            "change": "normal lateral_fast7 to8; safe5 and cap40 unchanged",
            "copied_other_members_byte_for_byte": len(hashes) - 1}
