"""Final evaluation adapter. Import is inert; live use requires explicit authority.

Only synthetic backends are used in preparation. A claimed live run never resumes.
"""
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

G = Path(__file__).resolve().parent.parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def durable_save(path, value, *, exclusive=False):
    path = Path(path)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    if exclusive:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        target = path
    else:
        target = path.with_name(path.name+'.tmp')
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError('Short durable write')
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    if not exclusive:
        os.replace(target, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        self.sequence = 0
        self.previous = '0'*64
        parent = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)

    def event(self, kind, **fields):
        value = dict(seq=self.sequence, previous=self.previous, kind=kind, **fields)
        value['hash'] = digest(value)
        data = (json.dumps(value, allow_nan=False, separators=(',', ':'))+'\n').encode()
        view = memoryview(data)
        while view:
            n = os.write(self.fd, view)
            if n <= 0:
                raise OSError('Short journal write')
            view = view[n:]
        os.fsync(self.fd)
        self.sequence += 1
        self.previous = value['hash']

    def close(self):
        os.close(self.fd)


def recover(path):
    """Read the valid durable prefix; never append, resume, or re-execute."""
    events = []
    previous = '0'*64
    damaged = False
    for line in Path(path).read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):
            damaged = True
            break
        try:
            obj = json.loads(line)
            h = obj.pop('hash')
            assert obj['seq'] == len(events) and obj['previous'] == previous and digest(obj) == h
            obj['hash'] = h
        except (ValueError, KeyError, AssertionError):
            damaged = True
            break
        events.append(obj)
        previous = h
    return events, damaged


def summarize(path, count):
    events, damaged = recover(path)
    cases = [dict(case_index=i, status='UNOBSERVED', native_confirmed=0) for i in range(count)]
    intents, committed = set(), set()
    claims = set()
    confirmed_claims = set()
    reset_times = {}
    actor_metadata = []
    cap = None
    for e in events:
        if e['kind'] == 'batch_prepared':
            candidate_cap = e.get('per_case_cap')
            if not isinstance(candidate_cap, int) or isinstance(candidate_cap, bool) or candidate_cap <= 0 or e.get('count') != count or cap is not None:
                raise ValueError('Invalid batch cap metadata')
            cap = candidate_cap
        i = e.get('case_index')
        if i is not None:
            if not 0 <= i < count:
                raise ValueError('Invalid case index in journal')
            row = cases[i]
            if e['kind'] in {'claim_intent', 'case_claimed'}:
                claims.add(i)
                row['status'] = 'CENSORED_INTERRUPTED'
            if e['kind'] == 'case_claimed':
                confirmed_claims.add(i)
            if e['kind'] == 'reset_committed':
                reset_times[i] = e['metadata']['start_time_s']
                actor_metadata.append(e['metadata'])
            if e['kind'] == 'act_committed':
                actor_metadata.append(e['metadata'])
            if e['kind'] == 'step_intent':
                key = (i, e['step'])
                if key in intents:
                    raise ValueError('Duplicate step intent')
                intents.add(key)
            if e['kind'] == 'step_committed':
                key = (i, e['step'])
                if key not in intents or key in committed:
                    raise ValueError('Invalid step commit')
                committed.add(key)
                row['native_confirmed'] += 1
                row['last_metrics'] = e['metrics']
            if e['kind'] == 'case_terminal':
                if row['status'] in {'COMPLETED', 'DNF'}:
                    raise ValueError('Duplicate case terminal')
                row.update(status=e['status'], reason=e['reason'], lap_ms=e['lap_ms'])
            if e['kind'] == 'case_aborted':
                if row['status'] not in {'COMPLETED', 'DNF'}:
                    row.update(status=e['status'], reason=e['reason'])
    # A durable terminal metric survives loss of the later classification event.
    for i, row in enumerate(cases):
        m = row.get('last_metrics')
        if m and row['status'] not in {'COMPLETED', 'DNF'}:
            if m['finish_time_s'] is not None and i in reset_times:
                row.update(status='COMPLETED', reason='durable_finish_metric', lap_ms=round((m['finish_time_s']-reset_times[i])*1000))
            elif m['terminated'] or m['truncated']:
                row.update(status='DNF', reason=m.get('retire_reason') or 'official_truncation', lap_ms=None)
            elif cap is not None and {step for case, step in committed if case == i} == set(range(1, cap+1)) and not any(case == i for case, step in intents-committed):
                row.update(status='DNF', reason='max_steps', lap_ms=None)
    done = [r for r in cases if r['status'] == 'COMPLETED']
    laps = [r['lap_ms'] for r in done]
    counts = {k: sum(r['status'] == k for r in cases) for k in sorted({r['status'] for r in cases})}
    assert sum(counts.values()) == count
    return dict(planned_cases=count, case_rows=cases, counts=counts,
                completed=len(done), DNF=counts.get('DNF', 0),
                unobserved=counts.get('UNOBSERVED', 0),
                censored=sum(n for k, n in counts.items() if k.startswith('CENSORED')),
                claimed_cases=len(confirmed_claims), claimed_cases_upper=len(claims),
                actor_act_intents=sum(e['kind']=='act_intent' for e in events),
                actor_act_committed=sum(e['kind']=='act_committed' for e in events),
                actor_reset_intents=sum(e['kind']=='reset_intent' for e in events),
                actor_reset_committed=sum(e['kind']=='reset_committed' for e in events),
                raw_step_ticks=sum(e['metrics'].get('raw_step_ticks', 0) for e in events if e['kind']=='step_committed'),
                raw_reset_ticks=sum(e['metadata'].get('raw_reset_ticks', 0) for e in events if e['kind']=='reset_committed'),
                observed_peak_RSS_mib=max((x.get('rss_mib', 0) for x in actor_metadata), default=0),
                max_recorded_act_IPC_ms=max((x.get('IPC_ms', 0) for x in actor_metadata), default=0),
                native_confirmed=len(committed),
                native_unresolved=len(intents-committed),
                native_lower_bound=len(committed), native_upper_bound=len(intents),
                completed_lap_mean_ms=statistics.mean(laps) if laps else None,
                completed_lap_median_ms=statistics.median(laps) if laps else None,
                journal_damaged_suffix=damaged, durable_events=len(events),
                all_cases_definitive=len(done)+counts.get('DNF', 0) == count,
                batch_completed_event=any(e['kind']=='batch_completed' for e in events),
                batch_error=next((e['reason'] for e in reversed(events) if e['kind']=='batch_aborted'), None))


def strict_action(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError('Strict action shape')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
        raise ValueError('Strict finite action')
    if not (-1 <= value[0] <= 1 and 0 <= value[1] <= 1 and 0 <= value[2] <= 1):
        raise ValueError('Strict action range')
    return value


def run_batch(directory, count, cap, factory, *, check_time=lambda: None,
              on_open=lambda: None, on_claim=lambda index: None,
              after_step=lambda: None):
    """Same control flow for synthetic and live backends; no retry or resume."""
    directory = Path(directory)
    directory.mkdir(mode=0o700)  # Existing directory is a hard stop.
    journal = Journal(directory/'events-private.jsonl')
    batch_error = None
    try:
        journal.event('batch_prepared', count=count, per_case_cap=cap)
        on_open()
        journal.event('batch_opened')
        for i in range(count):
            backend = None
            claimed = False
            try:
                check_time()
                journal.event('claim_intent', case_index=i)
                claimed = True
                on_claim(i)
                journal.event('case_claimed', case_index=i)
                backend = factory(i)
                journal.event('reset_intent', case_index=i)
                obs, reset_metadata = backend.reset()
                journal.event('reset_committed', case_index=i, metadata=reset_metadata)
                for step in range(1, cap+1):
                    check_time()
                    journal.event('act_intent', case_index=i, step=step)
                    action, actor_metadata = backend.act(obs)
                    action = strict_action(action)
                    journal.event('act_committed', case_index=i, step=step,
                                  action=action, metadata=actor_metadata)
                    check_time()
                    journal.event('step_intent', case_index=i, step=step,
                                  action_sha256=digest(action))
                    obs, metrics = backend.step(action)
                    after_step()  # Synthetic crash seam; live default is inert.
                    journal.event('step_committed', case_index=i, step=step, metrics=metrics)
                    complete = metrics['finish_time_s'] is not None
                    if complete or metrics['terminated'] or metrics['truncated'] or step == cap:
                        if complete:
                            lap = round((metrics['finish_time_s']-reset_metadata['start_time_s'])*1000)
                            if lap < 0:
                                raise ValueError('Negative lap time')
                            status, reason = 'COMPLETED', 'official_finish'
                        else:
                            lap = None
                            status = 'DNF'
                            reason = metrics.get('retire_reason') or ('max_steps' if step == cap or metrics['truncated'] else 'off_track')
                        journal.event('case_terminal', case_index=i, status=status, reason=reason, lap_ms=lap)
                        break
            except (Exception, KeyboardInterrupt, SystemExit) as exc:
                status = 'CENSORED_DEADLINE' if isinstance(exc, Deadline) else 'CENSORED_INTERRUPTED' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'CENSORED_TECHNICAL'
                if claimed:
                    journal.event('case_aborted', case_index=i, status=status, reason=type(exc).__name__)
                else:
                    journal.event('case_not_started', case_index=i, reason=type(exc).__name__)
                raise
            finally:
                if backend is not None:
                    receipt = backend.close()
                    journal.event('cleanup', case_index=i, receipt=receipt)
                    if not receipt.get('process_reaped', False):
                        raise RuntimeError('Actor cleanup failed')
        journal.event('batch_completed')
    except (Exception, KeyboardInterrupt, SystemExit) as exc:
        batch_error = type(exc).__name__+': '+str(exc)
        journal.event('batch_aborted', reason=type(exc).__name__)
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
    finally:
        journal.close()
        summary = summarize(directory/'events-private.jsonl', count)
        summary['batch_error'] = batch_error
        summary['batch_qualification_passed'] = batch_error is None and summary['batch_completed_event'] and summary['all_cases_definitive'] and not summary['native_unresolved'] and not summary['journal_damaged_suffix']
        durable_save(directory/'summary-private.json', summary)
        public = public_summary(summary)
        durable_save(directory/'summary-public.json', public)
    return summary


def recover_report(directory, count=16):
    """Metadata-only reconstruction; creates an additional receipt, never resumes."""
    directory = Path(directory)
    result = summarize(directory/'events-private.jsonl', count)
    result['recovery_only_no_reexecution'] = True
    target = directory/('recovered-'+digest(result)+'.json')
    if not target.exists():
        durable_save(target, result, exclusive=True)
    return result


def public_summary(summary):
    result = {k: v for k, v in summary.items() if k != 'case_rows'}
    if result.get('batch_error'):
        result['batch_error'] = result['batch_error'].split(':', 1)[0]
    return result


class Deadline(RuntimeError):
    pass


def require_authority(path):
    if path is None or not Path(path).is_file():
        raise PermissionError('Explicit final opening authority file required')
    a = read(path)
    if a.get('kind') != 'EXPLICIT_FINAL_SEALED_OPENING' or a.get('authorized') is not True or not a.get('user_authorization_reference'):
        raise PermissionError('Final opening is not authorized')
    return a


def preflight(root, authority):
    """Pure metadata gates; called before any live backend import or seed parsing."""
    if sys.version.split()[0] != '3.11.16' or Path(sys.executable).absolute() != G/'.venv/bin/python':
        raise RuntimeError('Use the frozen absolute interpreter')
    stage = authority.get('preparation_stage', 385)
    if stage != 386:
        raise PermissionError('Unknown preparation revision')
    preparation_directory = root/('stage'+str(stage))
    preservation = preparation_directory/'source-and-protected-hashes.json'
    if authority.get('preservation_receipt_sha256') != sha(preservation):
        raise PermissionError('Preparation preservation binding mismatch')
    for path, expected in read(preservation)['protected_hashes'].items():
        if sha(path) != expected:
            raise RuntimeError('Prepared champion/contract/query snapshot changed')
    preparation = preparation_directory/'execution-plan-private.json'
    if authority.get('preparation_plan_sha256') != sha(preparation):
        raise PermissionError('Preparation plan binding mismatch')
    for path, expected in read(preparation)['frozen_execution_sources'].items():
        if sha(path) != expected:
            raise RuntimeError('Frozen environment/adapter source changed')
    b = read(root/'stage384/binding-private.json')
    checks = {'binding384_sha256': sha(root/'stage384/binding-private.json'),
              'adapter_source_sha256': sha(Path(__file__)),
              'original_manifest_sha256': b['original_split_manifest_sha256']}
    for k, h in checks.items():
        if authority.get(k) != h:
            raise PermissionError('Authority binding mismatch: '+k)
    if authority.get('no_concurrent_research') is not True:
        raise PermissionError('Exclusive final phase must be authorized')
    expected_cost_hash = authority.get('experiment_cost_ledger_sha256')
    if expected_cost_hash != sha(root/'experiment-cost-lines.jsonl'):
        raise PermissionError('Exposure/cost ledger changed since authorization')
    if authority.get('case_count') != 16 or authority.get('native_cap') != 32000:
        raise PermissionError('Authority capacity mismatch')
    if sha(root/'preregistered-v1.json') != b['original_split_manifest_sha256']:
        raise RuntimeError('Condition manifest changed')
    if sha(G/'retry/final382_contract.md') != b['immutable_contract382_sha256']:
        raise RuntimeError('Contract changed')
    if sha(Path(sys.executable).resolve()) != b['runtime']['interpreter_sha256']:
        raise RuntimeError('Interpreter changed')
    for rel, h in b['execution_sources'].items():
        if sha(G/rel) != h:
            raise RuntimeError('Frozen execution source changed')
    verify_dependencies(read(root/'stage384/dependency-files-private.json'), b['runtime']['distributions'])
    champion = read(root/'current-champion.json')
    if champion['archive_sha256'] != b['candidate296_zip_sha256'] or sha(champion['archive_path']) != b['candidate296_zip_sha256']:
        raise RuntimeError('Champion changed')
    if sha(root/'stage88/pixel-read-sandbox') != b['native_sandbox_sha256']:
        raise RuntimeError('Native sandbox changed')
    if read(root/'protected-query-ledger-v1.json')['SEALED'] != {'episodes_used': 0, 'future_episode_queries_this_phase_max': 0}:
        raise RuntimeError('SEALED was already claimed or enabled')
    if list(root.rglob('SEALED*.opened')):
        raise RuntimeError('SEALED opening marker exists')
    deadline = read(root/'research-deadline-current.json')['deadline_utc']
    if authority.get('deadline_utc') != deadline:
        raise PermissionError('Authority deadline mismatch')
    def check_time():
        if sha(root/'experiment-cost-lines.jsonl') != expected_cost_hash:
            raise RuntimeError('Concurrent cost/exposure ledger change')
        if datetime.datetime.now(datetime.timezone.utc) >= datetime.datetime.fromisoformat(deadline.replace('Z', '+00:00')):
            raise Deadline('Approval window ended')
    check_time()
    budget_path = Path(authority['budget_path']).resolve()
    if budget_path.parent != root or sha(budget_path) != authority['budget_sha256']:
        raise PermissionError('Budget binding mismatch')
    budget = read(budget_path)
    if budget['final_reserved_actions'] < 32000 or budget.get('final_reserve_used') != 0:
        raise RuntimeError('Final reserve unavailable')
    return b, champion['configuration'], budget, budget_path, check_time


def verify_dependencies(snapshot, expected, resolver=None):
    """Bind untrusted file maps to immutable384 schema/digests before iteration."""
    if not isinstance(snapshot, dict) or set(snapshot) != set(expected):
        raise RuntimeError('Dependency names differ from384 binding')
    for name, bound in expected.items():
        value = snapshot[name]
        if not isinstance(value, dict) or value.get('version') != bound['version']:
            raise RuntimeError('Dependency snapshot version differs from384')
        files = value.get('files_sha256')
        if not isinstance(files, dict) or len(files) != bound['file_count'] or value.get('file_count') != bound['file_count']:
            raise RuntimeError('Dependency snapshot file count differs from384')
        canonical = hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()).hexdigest()
        if canonical != bound['content_manifest_sha256'] or value.get('content_manifest_sha256') != canonical:
            raise RuntimeError('Dependency snapshot digest differs from384')
    if resolver is None:
        import importlib.metadata
        resolver = importlib.metadata.distribution
    for name, bound in expected.items():
        dist = resolver(name)
        if dist.version != bound['version']:
            raise RuntimeError('Installed dependency version changed')
        for rel, h in snapshot[name]['files_sha256'].items():
            if sha(dist.locate_file(rel)) != h:
                raise RuntimeError('Installed dependency content changed')


class LiveBackend:
    """Instantiated only after authorized opening and durable case claim."""
    def __init__(self, config, directory, sandbox, case):
        self.worker = self.env = None
        self.config, self.directory, self.sandbox, self.case = config, directory, sandbox, case

    def reset(self):
        import numpy as np
        from retry.frozen_composite_runtime import prepare, validate_response
        from gymnasium.wrappers import TimeLimit
        from core.vendor.car_racing import CarRacing
        from env_wrapper import CarEnvironment
        self.worker = prepare(self.config, self.directory/'cpu', self.sandbox)
        self.env = CarEnvironment(TimeLimit(CarRacing(continuous=True, render_mode=None), max_episode_steps=8200), skip_frames=4)
        obs, _ = self.env.reset(seed=self.case['seed'], options={'track_id': self.case['track_id']})
        if self.env.env._elapsed_steps != 50 or self.env._skip_frames != 4:
            raise RuntimeError('Reset boundary changed')
        response, ms = self.worker.call('reset', obs)
        validate_response(response, self.config, obs, 'reset')
        self.np = np
        self.validate_response = validate_response
        return obs, dict(start_time_s=float(self.env.unwrapped.t), raw_reset_ticks=round(self.env.unwrapped.t*50), reset_IPC_ms=ms, cold_start_ms=self.worker.cold_start_ms, rss_mib=response['rss_mib'], actor_supervisor_pid=self.worker.process.pid, actor_pids=sorted(self.worker.actor_pids))

    def act(self, obs):
        response, ms = self.worker.call('act', obs)
        action = self.validate_response(response, self.config, obs, 'act')
        return action.tolist(), dict(IPC_ms=ms, compute_ms=response['act_compute_ms'], rss_mib=response['rss_mib'], actor_CPU_s=response['actor_cumulative_CPU_s'])

    def step(self, action):
        before = self.env.unwrapped.t
        obs, _, terminated, truncated, info = self.env.step(self.np.asarray(action, dtype=self.np.float32))
        return obs, dict(finish_time_s=self.env.unwrapped.finish_time_s,
                        terminated=bool(terminated), truncated=bool(truncated),
                        retire_reason=info.get('retire_reason'), damage=float(self.env.damage.damage),
                        progress=float(self.env._calculate_progress()), collision=bool(info.get('collision')),
                        raw_step_ticks=round((self.env.unwrapped.t-before)*50))

    def close(self):
        receipt = dict(process_reaped=True)
        try:
            if self.worker is not None:
                receipt = self.worker.close()
        finally:
            if self.env is not None:
                self.env.close()
        return receipt


def run_live(root, authority_path):
    # This check precedes all root access and live imports. Preparation never calls live.
    authority = require_authority(authority_path)
    root = Path(root).resolve()
    b, config, prior, budget_path, check_time = preflight(root, authority)
    output = root/'final385-evaluation'
    if output.exists():
        raise RuntimeError('A prior final run cannot resume or retry')
    lock = os.open(root/'final385.lock', os.O_WRONLY | os.O_CREAT, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cases = []
    def on_open():
        check_time()
        # Recheck under lock, then consume the once-only opening before parsing cases.
        if read(root/'protected-query-ledger-v1.json')['SEALED'] != {'episodes_used': 0, 'future_episode_queries_this_phase_max': 0}:
            raise RuntimeError('Concurrent or prior opening')
        durable_save(root/'SEALED.opened', dict(adapter_sha256=sha(Path(__file__)), authority_sha256=sha(authority_path)), exclusive=True)
        q = read(root/'protected-query-ledger-v1.json')
        q['SEALED'] = dict(episodes_used=0, future_episode_queries_this_phase_max=16, status='opened_once_no_retry', adapter_sha256=sha(Path(__file__)), claims=[])
        durable_save(root/'protected-query-ledger-v1.json', q)
        cases.extend(read(root/'preregistered-v1.json')['split']['SEALED'])
        if len(cases) != 16 or digest(cases) != b['SEALED_ordered_identity_block_sha256']:
            raise RuntimeError('SEALED identity block mismatch')
    def on_claim(i):
        claim_query(root/'protected-query-ledger-v1.json', i)
    def factory(i):
        directory = output/f'case-{i:02d}'
        directory.mkdir(mode=0o700)
        return LiveBackend(config, directory, root/'stage88/pixel-read-sandbox', cases[i])
    try:
        return run_with_settlement(
            lambda: run_batch(output,16,2000,factory,check_time=check_time,on_open=on_open,on_claim=on_claim),
            lambda: settle_live(root,output,prior,budget_path,authority))
    finally:
        os.close(lock)


def claim_query(path, index):
    q = read(path)
    pool = q['SEALED']
    if pool.get('status') != 'opened_once_no_retry' or pool['episodes_used'] != index or len(pool['claims']) != index or not 0 <= index < 16:
        raise RuntimeError('Query ledger drift or duplicate claim')
    pool['episodes_used'] += 1
    pool['claims'].append(dict(case_index=index, status='claimed_before_reset_no_retry'))
    durable_save(path, q)


def close_query(path, summary):
    q = read(path)
    pool = q['SEALED']
    if pool == {'episodes_used': 0, 'future_episode_queries_this_phase_max': 0}:
        pool['claims'] = []
    elif pool.get('status') not in {'opened_once_no_retry','closed_completed','closed_aborted_no_retry'}:
        raise RuntimeError('Unknown final query state')
    pool['future_episode_queries_this_phase_max'] = 0
    pool['status'] = 'closed_completed' if summary.get('batch_qualification_passed') else 'closed_aborted_no_retry'
    pool['native_confirmed'] = summary['native_confirmed']
    pool['native_unresolved_upper'] = summary['native_unresolved']
    pool['accounting_status'] = summary.get('accounting_status', 'UNKNOWN')
    for claim in pool['claims']:
        claim['observed_status'] = summary['case_rows'][claim['case_index']]['status']
    durable_save(path, q)


def ensure_receipt(path, value):
    if Path(path).exists():
        if read(path) != value:
            raise RuntimeError('Conflicting immutable accounting receipt')
    else:
        durable_save(path, value, exclusive=True)


def finalize_accounting(root, output, prior, budget_path, expected_ledger_sha256, expected_budget_sha256):
    """Revalidate under ledger lock; drift only emits independent reconciliation."""
    summary = summarize(output/'events-private.jsonl', 16)
    confirmed, pending = summary['native_confirmed'], summary['native_unresolved']
    if confirmed+pending > 32000:
        raise RuntimeError('Final native cap exceeded')
    journal_hash = sha(output/'events-private.jsonl')
    cost = dict(stage='FINAL385', new_wrapper_actions=confirmed, unresolved_native_upper=pending,
                exact_native=not pending, query_cases_claimed_upper=summary['claimed_cases_upper'],
                actor_act_intents=summary['actor_act_intents'], actor_reset_intents=summary['actor_reset_intents'],
                raw_step_ticks_confirmed=summary['raw_step_ticks'], raw_reset_ticks_confirmed=summary['raw_reset_ticks'],
                no_retry=True, journal_sha256=journal_hash)
    ledger = root/'experiment-cost-lines.jsonl'
    with ledger.open('r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read()
        original_lines, own = [], []
        reason = None
        try:
            for line in raw.splitlines(keepends=True):
                value = json.loads(line)
                if value.get('stage') == 'FINAL385':
                    own.append(value)
                else:
                    original_lines.append(line)
            base_hash = hashlib.sha256(''.join(original_lines).encode()).hexdigest()
            if base_hash != expected_ledger_sha256:
                reason = 'CONCURRENT_COST_LEDGER_DRIFT'
            if len(own)>1 or own and own[0]!=cost:
                reason = 'CONFLICTING_FINAL_COST_LINE'
        except (ValueError, TypeError):
            base_hash = None
            reason = 'COST_LEDGER_DAMAGED'
        try:
            observed_budget_hash = sha(budget_path)
            if observed_budget_hash != expected_budget_sha256 or read(budget_path) != prior:
                reason = 'PRIOR_BUDGET_CHANGED'
        except (OSError, ValueError, TypeError):
            observed_budget_hash = None
            reason = 'PRIOR_BUDGET_UNREADABLE'
        # Receipt contains only this run's facts, never stale project balances.
        ensure_receipt(output/'cost-independent.json', cost)
        if reason:
            reconciliation = dict(status='RECONCILIATION_REQUIRED', reason=reason,
                expected_ledger_sha256=expected_ledger_sha256, observed_base_ledger_sha256=base_hash,
                expected_budget_sha256=expected_budget_sha256, observed_budget_sha256=observed_budget_hash,
                independent_cost_sha256=sha(output/'cost-independent.json'),
                native_confirmed=confirmed, native_unresolved_upper=pending,
                shared_budget_published=False, shared_cost_line_appended=False, no_reexecution=True)
            target = output/('reconciliation-'+digest(reconciliation)+'.json')
            ensure_receipt(target, reconciliation)
            summary['accounting_status'] = 'RECONCILIATION_REQUIRED'
            summary['batch_qualification_passed'] = False
            return summary
        budget = dict(prior)
        budget.update(version='FINAL385', prior_budget_path=str(budget_path), prior_budget_sha256=expected_budget_sha256,
                      actual_cumulative_wrapper_actions=prior['actual_cumulative_wrapper_actions']+confirmed,
                      final_reserved_actions=prior['final_reserved_actions']-confirmed,
                      final_reserve_used=prior['final_reserve_used']+confirmed,
                      unresolved_final_native_upper=pending, final_reserve_encumbered_unresolved=pending,
                      native_accounting_status='UNRESOLVED_NO_RETRY' if pending else 'CONFIRMED',
                      final_journal_sha256=journal_hash)
        assert budget['actual_cumulative_wrapper_actions']+budget['research_remaining']+budget['final_reserved_actions']==budget['B_operating_cap']
        # Check all existing receipts before publishing any project balance.
        receipts=[(output/'project-budget-after.json',budget),
                  (root/'project-effective-budget-final385.json',budget),(output/'cost.json',cost)]
        for path, value in receipts:
            if path.exists() and read(path)!=value:
                raise RuntimeError('Conflicting immutable accounting receipt')
        for path, value in receipts:
            ensure_receipt(path,value)
        if not own:
            f.seek(0, os.SEEK_END)
            f.write(json.dumps(cost)+'\n')
            f.flush()
            os.fsync(f.fileno())
    summary['accounting_status'] = 'UNRESOLVED_NO_RETRY' if pending else 'CONFIRMED'
    return summary


def run_with_settlement(run, settle):
    """Catchable exits preserve metadata in finally, then propagate unchanged."""
    try:
        result = run()
    finally:
        settled = settle()
    return settled if settled is not None else result


def settle_live(root, output, prior, budget_path, authority):
    """No backend calls: used on normal return and catchable interruption."""
    if not (output/'events-private.jsonl').exists():
        return None
    result = recover_report(output,16)
    result['batch_qualification_passed'] = result['batch_completed_event'] and result['all_cases_definitive'] and not result['batch_error'] and not result['native_unresolved'] and not result['journal_damaged_suffix']
    try:
        accounting = finalize_accounting(root,output,prior,budget_path,
            authority['experiment_cost_ledger_sha256'],authority['budget_sha256'])
        result['accounting_status'] = accounting['accounting_status']
        if accounting['accounting_status']=='RECONCILIATION_REQUIRED':
            result['batch_qualification_passed'] = False
    except BaseException:
        result['batch_qualification_passed'] = False
        result['accounting_status'] = 'SETTLEMENT_ERROR_RECONCILIATION_REQUIRED'
        raise
    finally:
        # Even failed accounting cannot leave the query phase enabled.
        close_query(root/'protected-query-ledger-v1.json',result)
    ensure_receipt(output/('settlement-'+digest(result)+'.json'),result)
    return result


def recover_live_metadata(root, authority_path):
    """After interruption only: lock + journal reporting/accounting, no backend."""
    authority = require_authority(authority_path)
    root = Path(root).resolve()
    marker = read(root/'SEALED.opened')
    if marker['authority_sha256'] != sha(authority_path) or marker['adapter_sha256'] != sha(Path(__file__)):
        raise PermissionError('Recovery authority/source mismatch')
    budget_path = Path(authority['budget_path']).resolve()
    if budget_path.parent != root or sha(budget_path) != authority['budget_sha256']:
        raise PermissionError('Recovery budget mismatch')
    lock = os.open(root/'final385.lock', os.O_WRONLY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output = root/'final385-evaluation'
        return settle_live(root,output,read(budget_path),budget_path,authority)
    finally:
        os.close(lock)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--authorization', type=Path, required=True)
    p.add_argument('--recover-metadata', action='store_true')
    args = p.parse_args()
    if args.recover_metadata:
        result = recover_live_metadata(args.root, args.authorization)
    else:
        result = run_live(args.root, args.authorization)
    print(json.dumps(public_summary(result), ensure_ascii=False), flush=True)
    if not result.get('batch_qualification_passed', False):
        sys.exit(2)
