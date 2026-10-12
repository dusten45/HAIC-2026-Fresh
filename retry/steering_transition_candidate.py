"""Wrap the unchanged pixel Agent once, without feeding output limiting back
into its original steering memory or path-ranking state.
"""
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = 'b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e'
AGENT_SOURCE = '''from retry.schedule_agent import HazardScheduledAgent
from retry.steering_transition import SteeringTransitionLimiter

class Agent(HazardScheduledAgent):
    def __init__(self):
        super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)
        self.steering_transition = SteeringTransitionLimiter()

    def reset(self, observation):
        super().reset(observation)
        self.steering_transition.reset()

    def act(self, observation):
        original = super().act(observation)
        near = self.controller.lateral_acceleration == self.lateral_safe
        return self.steering_transition.apply(original, near)
'''


def build(source, output):
    source, output = Path(source), Path(output)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_SHA256
    helper = Path(__file__).with_name('steering_transition.py').read_bytes()
    hashes, changed = {}, []
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'x') as dst:
        assert 'retry/steering_transition.py' not in src.namelist()
        for member in src.infolist():
            data = src.read(member.filename)
            if member.filename == 'agent.py':
                assert data.decode() == '''from retry.schedule_agent import HazardScheduledAgent

class Agent(HazardScheduledAgent):
    def __init__(self):
        super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)
'''
                data = AGENT_SOURCE.encode()
                changed.append(member.filename)
            hashes[member.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(member, data)
        dst.writestr('retry/steering_transition.py', helper)
        hashes['retry/steering_transition.py'] = hashlib.sha256(helper).hexdigest()
    assert changed == ['agent.py']
    output.chmod(0o600)
    return dict(base_archive_sha256=BASE_SHA256,
        archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        changed_original_members=changed, added_members=['retry/steering_transition.py'],
        copied_original_members_byte_for_byte=len(hashes)-2, members_sha256=hashes,
        maximum_near_steering_change_rad=.18, controller_memory_feedback=False)
