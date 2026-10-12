"""One pedal contrast confined to the normal-mode, strictly dominant45 cap.

Near mode and curvature-limited or tied targets keep the original commands.
The fixed2.5m/s band is one existing HUD bin, not a fitted speed threshold.
"""
import hashlib
from pathlib import Path
import zipfile

import numpy as np

BASE_SHA256 = 'b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e'
OBSERVER_SHA256 = '4afda780a78309da90e7f50cbe926520b2bc09908599923e447966b95dc354ea'
BAND_M_S = 2.5
OLD = b'''        gas = float(np.clip(0.08 * (target - feedback_speed), 0, 0.5))
        brake = float(np.clip(0.04 * (feedback_speed - target), 0, 0.5))'''
NEW = OLD + b'''
        # Frozen schedule:24 means normal,8 means near. Exclude cap/curve ties.
        cap_dominates = (self.lateral_acceleration == 24.0 and self.speed_cap == 45.0
            and float(np.sqrt(self.lateral_acceleration / max(abs(curvature), 1e-6))) > self.speed_cap)
        error = target - feedback_speed
        if cap_dominates and abs(error) < 2.5:
            softened_error = error * abs(error) / 2.5
            gas = float(np.clip(0.08 * softened_error, 0, 0.5))
            brake = float(np.clip(-0.04 * softened_error, 0, 0.5))'''


def eligible(curvature, lateral, cap, near):
    return (not near and lateral == 24.0 and cap == 45.0
            and float(np.sqrt(lateral / max(abs(curvature), 1e-6))) > cap)


def effective_error(error, probe):
    before = probe['controller_before']
    if (eligible(probe['curvature'], before['lateral_acceleration'],
                 before['speed_cap'], probe['near']) and abs(error) < BAND_M_S):
        return error * abs(error) / BAND_M_S
    return error


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    changed, hashes = [], {}
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'x') as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == 'retry/parameter_agent.py':
                assert data.count(OLD) == 1
                data = data.replace(OLD, NEW)
                compile(data, item.filename, 'exec')
                changed.append(item.filename)
            hashes[item.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(item, data)
    assert changed == ['retry/parameter_agent.py']
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_members=changed, copied_other_members_byte_for_byte=len(hashes)-1,
        members_sha256=hashes, band_m_s=BAND_M_S, temporal_state_added=False)


def build_observer(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == OBSERVER_SHA256
    original = '''    expected_pedals = np.asarray([float(np.clip(0.08 * (target_speed-feedback), 0, 0.5)),
                                 float(np.clip(0.04 * (feedback-target_speed), 0, 0.5))], np.float32)'''
    replacement = original + '''
    cap_dominates = (before['lateral_acceleration'] == 24.0 and before['speed_cap'] == 45.0
        and float(np.sqrt(before['lateral_acceleration'] / max(abs(curvature), 1e-6))) > before['speed_cap'])
    error = target_speed-feedback
    if cap_dominates and abs(error) < 2.5:
        softened_error = error * abs(error) / 2.5
        expected_pedals = np.asarray([float(np.clip(0.08 * softened_error, 0, 0.5)),
                                     float(np.clip(-0.04 * softened_error, 0, 0.5))], np.float32)'''
    text = source.read_text()
    assert text.count(original) == 1
    text = text.replace(original, replacement)
    compile(text, str(output), 'exec')
    with output.open('x') as stream:
        stream.write(text)
    output.chmod(0o600)
