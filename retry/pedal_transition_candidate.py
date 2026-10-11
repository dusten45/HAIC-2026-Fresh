"""One memoryless pedal contrast, with its width fixed by the HUD bin spacing.

The existing proportional law is already continuous. This contrast makes its
slope vanish at zero speed error; it changes neither target nor speed estimate.
Errors of at least one HUD bin retain the exact original pedal commands.
"""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "41b53b1a3cffea2053de1bc9ed1994a6a96d66f228b9a4818c32aeaf6f22c199"
HUD_BIN_M_S = 2.5
OLD = b"""        gas = float(np.clip(0.08 * (target - feedback_speed), 0, 0.5))
        brake = float(np.clip(0.04 * (feedback_speed - target), 0, 0.5))"""
NEW = b"""        # One exact-HUD bin; no time filter, retained action, or added delay.
        error = target - feedback_speed
        softened_error = error * min(abs(error) / 2.5, 1.0)
        gas = float(np.clip(0.08 * softened_error, 0, 0.5))
        brake = float(np.clip(-0.04 * softened_error, 0, 0.5))"""


def softened_error(error):
    return error * min(abs(error) / HUD_BIN_M_S, 1.0)


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    members, changed = {}, []
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, "x") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "retry/parameter_agent.py":
                assert data.count(OLD) == 1
                data = data.replace(OLD, NEW)
                compile(data, item.filename, "exec")
                changed.append(item.filename)
            members[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    assert changed == ["retry/parameter_agent.py"]
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_members=changed, copied_other_members_byte_for_byte=len(members)-1,
        members_sha256=members, width_m_s=HUD_BIN_M_S, temporal_state_added=False)
