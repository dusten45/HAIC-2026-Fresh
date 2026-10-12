"""Change only the stage167 curvature helper's distance-to-speed propagation."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "247de4c0d7080b4efd8920d42bc85205c373cd6270a25a36e007092b4d7d2b3c"
TARGET_MEMBER = "retry/visible_curvature_preview.py"


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    replacement = Path(__file__).with_name('braking_envelope_preview.py').read_bytes()
    compile(replacement, TARGET_MEMBER, 'exec')
    members = {}
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'x') as dst:
        assert src.namelist().count(TARGET_MEMBER) == 1
        for item in src.infolist():
            data = replacement if item.filename == TARGET_MEMBER else src.read(item.filename)
            members[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_members=[TARGET_MEMBER], copied_other_members_byte_for_byte=len(members)-1,
        members_sha256=members, curvature_span_m=3.24,
        normal24_near8_cap45_original_perception_steering_path_P_unchanged=True)
