# Fresh pixel experiments

This package provides a small observation-only baseline and a local evaluation
harness for the unchanged `variables-6` simulator. It does not import any previous
research packages or replace the root `agent.py`.

`pixel_agent.py` contains the straight-gas control, a gray-road-following policy,
and one speed/curvature variant. Policies receive only `(4, 84, 84)` observations.
The harness owns seeds, simulator state, metrics, and timing.

Use a Python 3.11 environment with the repository dependencies:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m retry.evaluate \
  --plan /path/to/private/preregistered-v1.json \
  --output /path/to/private/new-run \
  --policy pixel_basic --split DEV --case-limit 3 --max-steps 120

.venv/bin/python -m unittest retry.test_boundaries -v
```

The private JSON plan contains `start_utc`, `deadline_utc`, `base`, `frame_skip`,
`max_steps`, and disjoint `split` lists of `{track_id, seed}` objects. Register the
plan and acceptance criteria before starting simulations. Outputs must be inside
the private plan directory and may not overwrite an existing run. Every run logs
plan/source SHA-256, observation/stack audits, actual raw ticks, completion,
progress, damage, diagnostic reward, reset/act/environment latency, and process
RSS. No plotting or training is required to run the harness.

Long DEV evaluations require `gate-cost.json` with passing `G0`/`G1` and the
matching `plan_sha256`. HOLDOUT/SEALED additionally require a private
`promotion.json` with the previous passing gate, frozen policy name and
`policy_sha256`; each protected split can be opened once. The harness checks the
authorization window before starting cases and simulation steps. On expiry it
stops and writes the available summary; it creates no scheduled work.

At 50 FPS, an action normally advances four raw ticks. Reset includes one internal
physics tick plus 50 warmup ticks, so the lap clock starts at `t=1.02`. Completion
uses `finish_time_s`, the finish-line center crossing tick, rather than the later
confirmation tick or the action count. `render_mode=None` still computes state
pixels on every raw tick.

The local thread guards match `local_runner.py`. They do not reproduce the
official isolated participant process, import deadline, or memory limit. Process
RSS includes the harness and is only a local estimate. Never include the harness,
tests, private plans, seed lists, run logs, or discarded research in a submission.
Only the observation-only policy is intended as potential participant code.
