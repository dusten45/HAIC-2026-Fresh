"""Serialize native input logs before physics; no policy or simulation code."""
from dataclasses import asdict
from retry.clip561_core import plain

def native_input_fields(before,action):
    return dict(before_state=plain(asdict(before)),payload=None if action is None else action.tolist())
