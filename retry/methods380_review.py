"""Record a source-only method review. Never imports a policy or simulator."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

G = Path(__file__).resolve().parent.parent
NAMES = ['coupling312', 'structure314', 'ppo244', 'ppo276', 'ppo278',
         'macro290', 'vision291', 'vision292', 'asymmetric316', 'asym317',
         'pixel_residual224', 'aggregate229', 'aggregate230', 'pedal306',
         'paired315', 'contact_pool221', 'intervention327', 'hybrid328',
         'speed309', 'route310', 'endpoints311', 'shield319', 'shield320',
         'h1_330', 'fallback374', 'fallback375', 'control377', 'pedal378',
         'count379']

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, obj):
    p = Path(p)
    temporary = p.with_suffix(p.suffix + '.tmp')
    with temporary.open('x') as f:
        os.chmod(temporary, 0o600)
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    temporary.replace(p)

def run(root):
    d = root / 'stage380'
    assert not d.exists(), 'Review already recorded; do not charge twice'
    prior = root / 'project-effective-budget-v397.json'
    budget = json.loads(prior.read_text())
    balance = ['actual_cumulative_wrapper_actions', 'research_remaining',
               'final_reserved_actions', 'final_reserve_used', 'B_operating_cap']
    assert [budget[k] for k in balance] == [1312121, 35943, 84000, 0, 1432064]
    protected = [root / 'current-champion.json', root / 'stage296/champion-manifest.json',
                 root / 'stage373/candidate365-rejected-locked.json',
                 root / 'protected-query-ledger-v1.json', prior]
    frozen = {str(p): sha(p) for p in protected}
    excluded = {str(root / name): (root / name).stat().st_mtime_ns
                for name in ['stage372', 'stage297']}
    sources = [G / 'retry/methods380_review.py', G / 'retry/methods380_result.md',
               root / 'stage20/family-premise-review.json',
               root / 'stage112/corrected-original-document-audit-20261011.json']
    sources += [G / 'retry' / (n + '_result.md') for n in NAMES
                if (G / 'retry' / (n + '_result.md')).exists()]
    start, cpu = time.perf_counter(), time.process_time()
    hashes = {str(p): sha(p) for p in sources}
    # Accounting uses historical per-stage new wrapper counts, never summed as
    # independent evidence or confused with teacher/source physics ticks.
    stages = [221, 224, 229, 230, 244, 247, 248, 251, 276, 278, 290,
              291, 292, 294, 295, 296, 298, 306, 309, 310, 311, 315,
              317, 319, 320, 321, 322, 327, 329, 330, 374, 375, 377, 378, 379]
    costs = {str(i): budget[f'stage{i}_new_wrapper_actions'] for i in stages}
    assert all(sha(p) == h for p, h in frozen.items())
    assert all(Path(p).stat().st_mtime_ns == t for p, t in excluded.items())
    d.mkdir(mode=0o700)
    cost = dict(stage=380, new_wrapper_actions=0, new_actor_calls=0,
                new_environment_resets=0, new_model_forward_calls=0,
                new_learning_fits=0, new_candidate_implementations=0,
                new_threshold_search=0, new_source_physics_rollout_ticks=0,
                new_paid_resources=0, audit_wall_s=time.perf_counter()-start,
                audit_CPU_s=time.process_time()-cpu,
                scope='Source hashing and existing ledger metadata only; human/code review and publication time not fully timed',
                **{k: budget[k] for k in balance})
    result = dict(stage=380, review_only=True, champion296_retained=True,
                  new_scientific_hypotheses=0, original_documents_full_read=False,
                  original_document_mapping='BLOCKED: originals/complete extracts unavailable; working W01-W16 normalization only',
                  evidence_scope='Existing TRAIN and already exposed DEV reports only; no stage372 individual data or new split',
                  family_count=16, failed_recipe_is_not_family_impossibility=True,
                  count_and_specific_time_intervention_lines_closed=True,
                  no_new_experiment_started=True, research_program_not_declared_terminated=True,
                  historical_stage_wrapper_actions=costs, cost=cost)
    save(d/'plan.json', dict(stage=380, source_hashes=hashes,
                            protected_hashes=frozen, excluded_directory_stats=excluded,
                            scope='No simulator/policy/model execution, no protected outcome access'))
    save(d/'cost.json', cost)
    save(d/'summary.json', result)
    save(G/'retry/methods380_result.json', result)
    ledger = root/'experiment-cost-lines.jsonl'
    assert not any(json.loads(line).get('stage') == 380 for line in ledger.read_text().splitlines())
    budget.update(version=398, at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  prior_budget_path=str(prior), prior_budget_sha256=sha(prior),
                  cost_path=str(d/'cost.json'), cost_sha256=sha(d/'cost.json'),
                  B_increment=0, stage380_new_wrapper_actions=0)
    assert not (root/'project-effective-budget-v398.json').exists()
    save(root/'project-effective-budget-v398.json', budget)
    with ledger.open('a') as f:
        f.write(json.dumps(cost)+'\n')
    save(d/'verification.json', dict(passed=True, source_hashes_unchanged=all(sha(p)==h for p,h in hashes.items()),
                                    preserved_hashes_unchanged=all(sha(p)==h for p,h in frozen.items()),
                                    excluded_directory_stats_unchanged=all(Path(p).stat().st_mtime_ns==t for p,t in excluded.items()),
                                    balance_unchanged=True, ledger_entries=1))
    print(json.dumps(cost, ensure_ascii=False))

if __name__ == '__main__':
    run(Path(sys.argv[1]).resolve())
