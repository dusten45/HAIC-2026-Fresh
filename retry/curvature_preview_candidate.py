"""Build one speed-target-only preview addition to the frozen near8 package."""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = "b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e"


def replace_once(source, old, new):
    assert source.count(old) == 1
    return source.replace(old, new)


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    assert not output.exists()
    with zipfile.ZipFile(source) as src:
        original = {item.filename: src.read(item.filename) for item in src.infolist()}
        members = dict(original)
        schedule = members['retry/schedule_agent.py'].decode()
        schedule = replace_once(schedule,
            'from retry.hud_feedback import decode_feedback_speed\n',
            'from retry.hud_feedback import decode_feedback_speed\n'
            'from retry.visible_curvature_preview import visible_curvature_preview\n')
        schedule = replace_once(schedule,
            '        target = route_target(connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer), speed)\n',
            '        path = connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer)\n'
            '        target = route_target(path, speed)\n')
        schedule = replace_once(schedule,
            '        return self.controller.action_target(float(target[0]), float(target[1]), speed, pedal_speed=decode_feedback_speed(image, speed))\n',
            '        preview_speed = (visible_curvature_preview(path, speed, self.lateral_safe)["speed_limit_m_s"]\n'
            '                         if near else None)\n'
            '        return self.controller.action_target(float(target[0]), float(target[1]), speed, pedal_speed=decode_feedback_speed(image, speed), preview_speed=preview_speed)\n')
        controller = members['retry/parameter_agent.py'].decode()
        controller = replace_once(controller,
            '    def action_target(self, x, forward, speed, pedal_speed=None):\n',
            '    def action_target(self, x, forward, speed, pedal_speed=None, preview_speed=None):\n')
        controller = replace_once(controller,
            '        feedback_speed = speed if pedal_speed is None else pedal_speed\n',
            '        if preview_speed is not None:\n'
            '            target = min(target, preview_speed)\n'
            '        feedback_speed = speed if pedal_speed is None else pedal_speed\n')
        members['retry/schedule_agent.py'] = schedule.encode()
        members['retry/parameter_agent.py'] = controller.encode()
        added = 'retry/visible_curvature_preview.py'
        members[added] = Path(__file__).with_name('visible_curvature_preview.py').read_bytes()
        changed = [name for name in original if original[name] != members[name]]
        assert changed == ['retry/parameter_agent.py', 'retry/schedule_agent.py']
        for name in changed + [added]:
            compile(members[name], name, 'exec')
        with zipfile.ZipFile(output, 'x') as dst:
            for item in src.infolist():
                dst.writestr(item, members[item.filename])
            item = zipfile.ZipInfo(added, (1980, 1, 1, 0, 0, 0))
            item.external_attr = 0o100644 << 16
            dst.writestr(item, members[added])
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_members=changed, added_members=[added],
        copied_other_members_byte_for_byte=len(original)-len(changed),
        members_sha256={k: hashlib.sha256(v).hexdigest() for k, v in members.items()},
        normal24_near8_cap45_original_perception_route_steering_P_unchanged=True)
