"""Synthetic transaction/failure fixtures only; no scientific policy/env execution."""
import json
import hashlib
from pathlib import Path
import sys
from retry.final385_adapter import (Deadline, Journal, digest, durable_save,
    recover, recover_report, require_authority, run_batch, strict_action, summarize,
    claim_query, close_query, finalize_accounting, run_live, public_summary)


class Synthetic:
    def __init__(self, mode='finish'):
        self.mode, self.steps = mode, 0

    def reset(self):
        if self.mode == 'reset_error':
            raise RuntimeError('Synthetic reset fault')
        return 'synthetic-observation', dict(start_time_s=1.02, raw_reset_ticks=51, rss_mib=1)

    def act(self, obs):
        assert obs == 'synthetic-observation'
        if self.mode == 'timeout':
            raise TimeoutError('Synthetic timeout, no sleep')
        if self.mode == 'invalid':
            return [0, float('nan'), 0], {}
        return [0.1, 0.2, 0.0], dict(IPC_ms=2, rss_mib=1)

    def step(self, action):
        self.steps += 1
        if self.mode == 'step_error':
            raise RuntimeError('Synthetic uncertain step')
        finish = 1.08 if self.mode in {'finish', 'cleanup_error'} else None
        return 'synthetic-observation', dict(finish_time_s=finish,
            terminated=self.mode == 'DNF', truncated=finish is not None,
            retire_reason='crash' if self.mode == 'DNF' else None,
            damage=0.2, progress=0.99, raw_step_ticks=4)

    def close(self):
        return dict(process_reaped=self.mode != 'cleanup_error')


class SimulatedPowerLoss(BaseException):
    pass


def run(root):
    root = Path(root)
    root.mkdir(mode=0o700)
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append(name)
    def batch(name, modes, **options):
        return run_batch(root/name, 16, 2, lambda i: Synthetic(modes[i] if i < len(modes) else 'finish'), **options)
    r = batch('mixed', ['finish', 'DNF', 'cap'])
    check('finish dominates truncation and retroactive lap', r['case_rows'][0]['status']=='COMPLETED' and r['case_rows'][0]['lap_ms']==60)
    check('normal retirement and outer cap are DNF', r['case_rows'][1]['reason']=='crash' and r['case_rows'][2]['reason']=='max_steps')
    check('all16 retained and conditional lap mean', len(r['case_rows'])==16 and r['completed']==14 and r['DNF']==2 and r['completed_lap_mean_ms']==60)
    check('confirmed native accounting and reset layer separated', r['native_confirmed']==17 and r['native_unresolved']==0 and r['raw_reset_ticks']==816)
    for mode in ['timeout', 'invalid', 'reset_error']:
        r = batch(mode, [mode])
        check(mode+' stops batch with15 unobserved and native0', r['censored']==1 and r['unobserved']==15 and r['native_confirmed']==r['native_unresolved']==0 and not r['batch_qualification_passed'])
    r = batch('uncertain', ['step_error'])
    check('uncertain step held not falsely charged or retried', r['native_lower_bound']==0 and r['native_upper_bound']==1 and r['unobserved']==15)
    calls = [0]
    def crash():
        calls[0] += 1
        raise SimulatedPowerLoss()
    try:
        batch('power_loss', ['finish'], after_step=crash)
    except SimulatedPowerLoss:
        pass
    else:
        raise AssertionError('Power loss did not propagate')
    restored = recover_report(root/'power_loss')
    check('crash recovery is read only and exposes pending effect', calls[0]==1 and restored['native_confirmed']==0 and restored['native_unresolved']==1 and restored['unobserved']==15)
    try:
        batch('power_loss', ['finish'])
    except FileExistsError:
        pass
    else:
        raise AssertionError('Duplicate episode allowed')
    checks.append('existing output prohibits retry or resume')
    r = batch('cleanup', ['cleanup_error'])
    check('cleanup failure preserves observed finish and stops rest', r['completed']==1 and r['unobserved']==15 and not r['batch_qualification_passed'])
    def expired():
        raise Deadline('Synthetic expired approval')
    r = batch('deadline', [], check_time=expired)
    check('deadline before claim creates no actor or step', r['unobserved']==16 and r['actor_act_intents']==0 and r['native_confirmed']==0)
    p = root/'torn.jsonl'
    journal = Journal(p)
    journal.event('case_claimed', case_index=0)
    journal.event('step_intent', case_index=0, step=1)
    journal.close()
    with p.open('ab') as f:
        f.write(b'{"torn":')
    restored = summarize(p, 16)
    check('torn suffix preserves valid prefix and unknown step', restored['journal_damaged_suffix'] and restored['native_upper_bound']==1 and restored['unobserved']==15)
    p = root/'finish_without_classification.jsonl'
    journal = Journal(p)
    journal.event('case_claimed', case_index=0)
    journal.event('reset_committed', case_index=0, metadata=dict(start_time_s=1.02))
    journal.event('step_intent', case_index=0, step=1)
    journal.event('step_committed', case_index=0, step=1, metrics=dict(finish_time_s=1.08,terminated=False,truncated=True))
    journal.close()
    restored = summarize(p, 16)
    check('durable finish metric survives missing classification file', restored['completed']==1 and restored['case_rows'][0]['lap_ms']==60)
    for authority in [None, root/'missing-authority.json']:
        try:
            require_authority(authority)
        except PermissionError:
            pass
        else:
            raise AssertionError('Missing authority accepted')
    false = root/'disabled-authority.json'
    durable_save(false, dict(kind='EXPLICIT_FINAL_SEALED_OPENING', authorized=False), exclusive=True)
    try:
        require_authority(false)
    except PermissionError:
        pass
    else:
        raise AssertionError('Disabled authority accepted')
    checks.append('absent or disabled opening authority denied')
    fake_live_root = root/'must-not-be-created'
    try:
        run_live(fake_live_root, false)
    except PermissionError:
        pass
    else:
        raise AssertionError('Disabled live entry was entered')
    check('live entry denied before any root or backend access', not fake_live_root.exists())
    for action in [[0,2,0],[0,0], [False,0,0], [0,float('inf'),0]]:
        try:
            strict_action(action)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid action accepted')
    checks.append('strict shape finite range no clipping')
    qpath = root/'synthetic-query-ledger.json'
    durable_save(qpath, dict(SEALED=dict(episodes_used=0, future_episode_queries_this_phase_max=16, status='opened_once_no_retry', claims=[]), other_pool=dict(preserved=True)), exclusive=True)
    claim_query(qpath, 0)
    try:
        claim_query(qpath, 0)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Duplicate query claim accepted')
    close_query(qpath, json.loads((root/'uncertain/summary-private.json').read_text()))
    closed = json.loads(qpath.read_text())
    check('query claim consumed before reset and cannot repeat', closed['SEALED']['episodes_used']==1 and closed['SEALED']['future_episode_queries_this_phase_max']==0 and closed['other_pool']['preserved'])
    accounting = root/'accounting'
    accounting.mkdir()
    budget_path = accounting/'prior.json'
    prior = dict(actual_cumulative_wrapper_actions=10,research_remaining=20,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=84030)
    durable_save(budget_path, prior, exclusive=True)
    (accounting/'experiment-cost-lines.jsonl').touch(mode=0o600)
    finalize_accounting(accounting, root/'power_loss', prior, budget_path, hashlib.sha256(b'').hexdigest(), hashlib.sha256(budget_path.read_bytes()).hexdigest())
    finalize_accounting(accounting, root/'power_loss', prior, budget_path, hashlib.sha256(b'').hexdigest(), hashlib.sha256(budget_path.read_bytes()).hexdigest())
    b = json.loads((accounting/'project-effective-budget-final385.json').read_text())
    check('uncertain cost held with exact confirmed-only debit', b['actual_cumulative_wrapper_actions']==10 and b['final_reserved_actions']==84000 and b['final_reserve_encumbered_unresolved']==1 and b['native_accounting_status']=='UNRESOLVED_NO_RETRY')
    check('metadata accounting recovery is idempotent', len((accounting/'experiment-cost-lines.jsonl').read_text().splitlines())==1)
    redacted = public_summary(dict(case_rows=[dict(private='synthetic')], batch_error='RuntimeError: synthetic private detail'))
    check('public summary omits case rows and raw exception details', 'case_rows' not in redacted and redacted['batch_error']=='RuntimeError')
    check('dry run imported no real policy or simulator', not any(n.split('.')[0] in {'numpy','cv2','gymnasium','Box2D','core','env_wrapper','agent'} for n in sys.modules))
    result = dict(passed=True,fixture_assertions=len(checks),checks=checks,
        real_actor_calls=0,real_environment_creation=0,real_native_actions=0,
        SEALED_reads=0,synthetic_only=True)
    durable_save(root/'verification.json', result, exclusive=True)
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    run(Path(sys.argv[1]).resolve())
