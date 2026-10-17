"""Small private checkpoints at completed decision/phase boundaries only."""
import datetime
import os
from retry.loss389_analyze import save


def checkpoint(directory, phase, **facts):
    value = dict(stage=442, phase=phase, pid=os.getpid(),
                 at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 deadline_utc='2026-10-20T10:01:55Z', **facts)
    save(directory / 'progress-private.json', value)
    return value
