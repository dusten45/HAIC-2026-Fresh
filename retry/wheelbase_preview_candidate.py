"""Change only curvature estimation in the frozen stage166 preview archive."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "6fb5ecdf4b656ef199a4a5ca9e9a005585efe6c8555cfd25e5a12fdd8fa8307f"
TARGET_MEMBER = "retry/visible_curvature_preview.py"


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    replacement = Path(__file__).with_name('wheelbase_curvature_preview.py').read_bytes()
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
        changed_members=[TARGET_MEMBER], added_members=[],
        copied_other_members_byte_for_byte=len(members)-1,
        members_sha256=members, curvature_total_arc_span_m=3.24,
        curvature_arc_half_span_m=1.62,
        preview_structure_normal24_near8_cap45_perception_route_steering_P_unchanged=True)
