"""Correct one nominal hull-target steering geometry term.

For hull origin O=(0,0), rear axle (0,-r) and ICR=(R,-r), a circle
through O and the unchanged target (x,y) satisfies
    x*x + y*y + 2*r*y - 2*R*x = 0.
Thus rear curvature is 2*x/(x*x+y*y+2*r*y). Wheelbase and r come
from the vehicle source, not fitted driving outcomes. This is an ideal
no-slip geometry correction; it does not model tire slip or actuator lag.

Keep the original nominal previous_steer for frozen route scoring. A separate
tracking memory applies the existing .8/.2 smoothing to corrected steering.
Pedal curvature and the selected target remain unchanged.
"""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = 'b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e'
OBSERVER_SHA256 = '4afda780a78309da90e7f50cbe926520b2bc09908599923e447966b95dc354ea'
REAR_OFFSET_M = 1.64
WHEELBASE_M = 3.24

MEMORY = '''    def reset(self):
        super().reset()
        self.tracking_previous_steer = 0.0

    def action(self, far_x, speed):
        action = super().action(far_x, speed)
        if far_x is None:
            # Preserve the original fallback output and synchronize tracking.
            self.tracking_previous_steer = self.previous_steer
        return action

'''
TRACKING = '''        # previous_steer remains the original route-ranking proxy.
        # Same hull target, with ICR on the rear axle's transverse line.
        tracking_curvature = 2 * x / max(forward * forward + x * x + 2 * 1.64 * forward, 1e-6)
        tracking_raw = float(np.clip(np.arctan(3.24 * tracking_curvature), -0.4, 0.4))
        steer = 0.8 * tracking_raw + 0.2 * self.tracking_previous_steer
        self.tracking_previous_steer = steer
'''


def change(source):
    edits = [
        ('        self.lateral_acceleration = float(lateral_acceleration)\n',
         '        self.lateral_acceleration = float(lateral_acceleration)\n        self.tracking_previous_steer = 0.0\n'),
        ('    def action_target(self, x, forward, speed, pedal_speed=None):\n',
         MEMORY + '    def action_target(self, x, forward, speed, pedal_speed=None):\n'),
        ('        self.previous_steer = steer\n', '        self.previous_steer = steer\n' + TRACKING)]
    for old,new in edits:
        assert source.count(old)==1
        source=source.replace(old,new)
    return source


def build(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==BASE_SHA256
    hashes={};changed=[]
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(output,'x') as dst:
        for item in src.infolist():
            data=src.read(item.filename)
            if item.filename=='retry/parameter_agent.py':
                data=change(data.decode()).encode();compile(data,item.filename,'exec');changed.append(item.filename)
            hashes[item.filename]=hashlib.sha256(data).hexdigest();dst.writestr(item,data)
    assert changed==['retry/parameter_agent.py'];output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        members_sha256=hashes,changed_members=changed,other_members_identical=len(hashes)-1,
        source_rear_offset_m=REAR_OFFSET_M,source_wheelbase_m=WHEELBASE_M,
        target_and_pedal_curvature_unchanged=True,nominal_planner_memory_preserved=True)


def build_observer(source,output):
    source,output=Path(source),Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==OBSERVER_SHA256
    text=source.read_text()
    old="('previous_steer', 'lateral_acceleration', 'speed_cap')"
    assert text.count(old)==1
    text=text.replace(old,"('previous_steer', 'lateral_acceleration', 'speed_cap', 'tracking_previous_steer')")
    compile(text,str(output),'exec')
    with output.open('x') as f:f.write(text)
    output.chmod(0o600)
