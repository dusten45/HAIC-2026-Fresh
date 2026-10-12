"""Read-only gate for the existing stage221 DEV records; never run a simulator.

Usage: python retry/pixel_residual223_audit.py --records PRIVATE_STAGE221_DIR
Output contains counts only. No trajectory, identity, command, or private path
is emitted. This audits the existing format, not hypothetical future datasets.
"""
import argparse
import json
import time
from pathlib import Path


def audit(root):
    plan = json.loads((root / 'evaluation/plan.json').read_text())
    assert plan['stage'] == 221 and len(plan['cases']) == 4
    counts = []
    for label, case in zip(plan['labels'], plan['cases']):
        run = root / 'evaluation/runs' / (case['id'] + '__C')
        result = json.loads((run / 'result.json').read_text())
        diagnostic = json.loads((run / 'oracle-diagnostic.json').read_text())
        rows = diagnostic['actual_steps']
        assert len(rows) == result['charged_wrapper_actions']
        assert all(len(row['action']) == 3 for row in rows)
        # The evaluated archive is the teacher's normal32 nominal actor.
        assert result['archive_sha256'] == plan['arms']['C']['archive_sha256']
        assert result['saved_video_frames'] == 0
        assert result['saved_policy_telemetry_rows'] == 0
        assert not any('observation' in row for row in rows)
        # Inventory the complete stage directory, excluding extracted source.
        counts.append(dict(road=label,teacher_executed_command_rows=len(rows),
                           saved_video_frames=0,saved_policy_telemetry_rows=0,
                           observation_digest_present=bool(result['observation_sequence_sha256']),
                           champion_replay_qualified=False))
    binary = [p for p in root.rglob('*') if p.is_file()
              and 'package' not in p.parts
              and p.suffix.lower() in {'.npy','.npz','.png','.jpg','.jpeg','.mp4','.avi','.bin','.pkl','.pt','.h5'}]
    assert not binary, 'Unexpected potential observation asset; inspect privately before qualification'
    return dict(stage=223,status='BLOCKED_MISSING_PIXEL_REPLAY_DATA',roads=counts,
                teacher_executed_command_rows=sum(x['teacher_executed_command_rows'] for x in counts),
                observation_assets_found=0,qualified_training_rows=0,
                missing=['Exact reset and ordered act-input float32 (4,84,84) pixel observations',
                         'Current normal24 champion features/actions on that observation history',
                         'Verified causal champion state replay from reset through every act'],
                unavailable_replay_state=['previous_image','hazards','controller.previous_steer'],
                nominal_substitution_allowed=False,GT_feature_substitution_allowed=False,
                native_actions=0,model_queries=0,training_updates=0,LOO_folds_executed=0,
                student_inference_cost_ms=None,champion_changed=False,
                HOLDOUT_used=False,SEALED_opened=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    wall, cpu = time.perf_counter(), time.process_time()
    result = audit(args.records)
    result.update(audit_wall_s=time.perf_counter()-wall,
                  audit_CPU_s=time.process_time()-cpu)
    print(json.dumps(result,ensure_ascii=False,indent=2))
