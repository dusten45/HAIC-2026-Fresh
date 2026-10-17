"""463 bounded pair meter; durable conservative native debit before dispatch."""
import time
WORKER_START = time.perf_counter()  # Runner should pass its earlier, pre-import stamp.
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import signal
import tempfile
import fcntl

from retry.meter453 import Meter453
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop, TechnicalStop
from retry.loss389_analyze import sha


def _durable(path, value, exclusive=False):
    """Atomic JSON publication, including directory durability; never clobber first owner."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            os.link(temporary, path)
            os.unlink(temporary)
        else:
            os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Meter463(Meter453):
    MODEL_HARD_TICKS = 32768
    MODEL_SCOPE_TICKS = 30370
    MODEL_HARD_WORLDS = 768
    MODEL_SCOPE_WORLDS = 597
    ARMS = ('Original', 'SecantOnce')

    def __init__(self, d, worker_start=None):
        self.worker_start = WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d))
        self.phase = 'INITIALIZED'
        self.before_path = Path(self.p['budget_before_path'])
        self.before_hash = self.p['budget_before_sha256']
        self.ledger_path = Path(self.p['ledger_path'])
        self.native_directory = Path(self.p['native_directory'])
        if self.before_path.name != 'project-effective-budget-v474.json' or self.ledger_path.name != 'project-effective-budget-v475.json':
            raise TechnicalStop('463_budget_version_paths')
        if self.before_path.resolve().parent != self.ledger_path.resolve().parent:
            raise TechnicalStop('463_budget_parent')
        self.before = json.loads(self.before_path.read_text())
        self._verify_before()
        self.owner = dict(stage=463, pid=os.getpid(), plan_sha256=self.plan_sha,
                          native_directory=str(self.native_directory.resolve()))
        self.ledger_hash = None
        self.journal_sequence = 0
        if self.ledger_path.exists():
            raise TechnicalStop('463_existing_ledger_no_resume_or_overwrite')

    def _verify_before(self):
        if sha(self.before_path) != self.before_hash:
            raise TechnicalStop('463_frozen_v474_hash')
        expected = dict(version=474, research_remaining=26695,
                        actual_cumulative_wrapper_actions=1321369,
                        final_reserved_actions=84000, final_reserve_used=0)
        if any(self.before.get(k) != v for k, v in expected.items()):
            raise TechnicalStop('463_frozen_v474_balance')

    def _disk(self):
        for path in ('/tmp', '/workspace'):
            if shutil.disk_usage(path).free < 512 * 1024 * 1024:
                raise ResourceStop('463_disk_below512MiB_' + path.replace('/', '_'))

    def wholetime(self):
        return time.process_time(), time.perf_counter() - self.worker_start

    def persist(self):
        mc, mw = self.modeltime()
        nc, nw = self.nativetime()
        cpu, wall = self.wholetime()
        self.b.update(CPU_s=mc, execution_wall_s=mw)
        _durable(self.d / 'budget.json', dict(stage=463, model={**self.b, 'regions': self.regions},
                 actual={**self.nb, 'CPU_s': nc, 'wall_s': nw},
                 wholeworker_CPU_s=cpu, whole_execution_wall_s=wall,
                 exclusive_accounting=True, phase=getattr(self, 'phase', 'INITIALIZED'), pid=os.getpid()))

    def guard(self):
        self._disk()
        cpu, wall = self.wholetime()
        nc, nw = self.nativetime()
        if cpu >= 1800 or wall >= 2400:
            raise ResourceStop('463_wholeworker_CPU1800_wall2400')
        if nc >= 240 or nw >= 480:
            raise ResourceStop('463_actual_CPU240_wall480')
        deadline = min(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z', '+00:00')),
                       datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'))
        if datetime.datetime.now(datetime.timezone.utc) >= deadline:
            raise ResourceStop('463_deadline')
        self.persist()

    def timers(self):
        cpu, wall = self.wholetime()
        deadline = min(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z', '+00:00')),
                       datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'))
        limits = [1800 - cpu, 2400 - wall,
                  (deadline - datetime.datetime.now(datetime.timezone.utc)).total_seconds()]
        cpu_remaining = limits[0]
        wall_remaining = min(limits[1:])
        if self.actual_start and self.active is None:
            nc, nw = self.nativetime()
            cpu_remaining = min(cpu_remaining, 240 - nc)
            wall_remaining = min(wall_remaining, 480 - nw)
        signal.setitimer(signal.ITIMER_PROF, max(.001, cpu_remaining))
        signal.setitimer(signal.ITIMER_REAL, max(.001, wall_remaining))

    def world(self, state, tag):
        self.guard()
        if self.b['worlds'] >= self.MODEL_HARD_WORLDS:
            raise ResourceStop('463_world_hard768')
        if self.b['worlds'] >= self.MODEL_SCOPE_WORLDS:
            raise ResourceStop('463_world_scope597')
        return super().world(state, tag)

    def step(self, m, act, tag):
        self.guard()
        if self.b['reserved_ticks'] + 4 > self.MODEL_HARD_TICKS:
            raise ResourceStop('463_model_hard32768')
        if self.b['reserved_ticks'] + 4 > self.MODEL_SCOPE_TICKS:
            raise ResourceStop('463_model_scope30370')
        return Meter442.step(self, m, act, tag)

    def charge(self, kind, arm):
        assert self.actual_start and self.active is None
        if arm not in self.ARMS or kind not in ('reset', 'action'):
            raise TechnicalStop('463_native_registered_pair_only')
        self.guard()
        key, ak = ('resets', 'arm_resets') if kind == 'reset' else ('actions', 'arm_actions')
        cap, armcap = (2, 1) if kind == 'reset' else (390, 195)
        if self.nb[key] >= cap or self.nb[ak].get(arm, 0) >= armcap:
            raise ResourceStop('463_native_cap_' + arm + '_' + kind)
        # One process owns this ledger; a stale/replaced ledger or another plan stops.
        with open(str(self.ledger_path) + '.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._verify_before()
            if self.ledger_hash is None:
                if self.ledger_path.exists():
                    raise TechnicalStop('463_foreign_ledger')
            elif not self.ledger_path.exists() or sha(self.ledger_path) != self.ledger_hash:
                raise TechnicalStop('463_live_ledger_changed')
            self.nb[key] += 1
            self.nb[ak][arm] = self.nb[ak].get(arm, 0) + 1
            self.journal_sequence += 1
            debit = self.nb['actions']
            ledger = copy.deepcopy(self.before)
            ledger.update(version=475, prior_budget_path=str(self.before_path),
                          prior_budget_sha256=self.before_hash, owner=self.owner,
                          at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          research_remaining=26695 - debit,
                          actual_cumulative_wrapper_actions=1321369 + debit,
                          stage463_new_wrapper_actions=debit,
                          stage463_actual_resets=self.nb['resets'],
                          stage463_actual_retries=0, stage463_status='LIVE',
                          research_status='STAGE463_LIVE_CHARGED_BEFORE_DISPATCH',
                          current_stage_execution_cap='463 registered Original/SecantOnce only; no followup',
                          charged_attempts_no_refund=True)
            receipt = dict(stage=463, owner=self.owner, sequence=self.journal_sequence,
                           kind=kind, arm=arm, actions=debit, resets=self.nb['resets'],
                           arm_actions=dict(self.nb['arm_actions']), arm_resets=dict(self.nb['arm_resets']),
                           dispatch_status='CHARGED_BEFORE_CALL_CONSERVATIVE_NO_REFUND',
                           ledger_path=str(self.ledger_path), research_remaining=26695-debit)
            # Journal survives even if a later publication fails: caller must stop, never dispatch.
            _durable(self.native_directory / ('charge463-%04d-private.json' % self.journal_sequence), receipt, exclusive=True)
            _durable(self.ledger_path, ledger, exclusive=self.ledger_hash is None)
            self.ledger_hash = sha(self.ledger_path)
            self.persist()

    def checkpoint(self, phase, **facts):
        self.phase = phase
        mc, mw = self.modeltime()
        nc, nw = self.nativetime()
        cpu, wall = self.wholetime()
        q = dict(stage=463, phase=phase, pid=os.getpid(),
                 at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 actual_actions=self.nb['actions'], resets=self.nb['resets'],
                 arm_actions=dict(self.nb['arm_actions']), arm_resets=dict(self.nb['arm_resets']),
                 model_ticks=self.b['ticks'], model_reserved_ticks=self.b['reserved_ticks'],
                 model_worlds=self.b['worlds'], model_CPU_s=mc, model_wall_s=mw,
                 actual_CPU_s=nc, actual_wall_s=nw,
                 wholeworker_CPU_s=cpu, whole_execution_wall_s=wall, **facts)
        _durable(self.d / 'progress-private.json', q)
        self.persist()
        return q
