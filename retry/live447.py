"""Same-object H13 prefix seal; diagnostic continuation, never finish evidence."""
from dataclasses import dataclass
from retry.pilot420_backend import fingerprint,snapshot


class LiveGateError(ValueError):
    pass


def check_historical_h13(child, archive):
    if len(child.rows)!=13 or not child.initial_ok or not child.initial_safe or not child.initial_progress:
        raise LiveGateError('current_H13_safety_or_progress')
    if child.rows!=archive['rows']:
        raise LiveGateError('H13_rows_differ_from444')
    if child.ctrl.memory()!=archive['controller_memory'] or snapshot(child.m)!=archive['final_state']:
        raise LiveGateError('H13_state_or_memory_differs_from444')


@dataclass(frozen=True)
class LiveH13447:
    child: object
    world: object
    stream: object
    key: str
    prefix_digest: str

    @classmethod
    def seal(cls,c):
        if len(c.rows)!=13 or c.stream.boundary is None:
            raise LiveGateError('missing_live_H13_boundary')
        return cls(c,c.m,c.stream,c.stream.boundary.key(),fingerprint(c.rows))

    def validate(self,c):
        if c is not self.child or c.m is not self.world or c.stream is not self.stream:
            raise LiveGateError('child_world_or_stream_replaced')
        if c.stream.key!=self.key or c.stream.boundary.key()!=self.key or fingerprint(c.rows[:13])!=self.prefix_digest:
            raise LiveGateError('H13_seal_or_prefix_changed')
        return True
