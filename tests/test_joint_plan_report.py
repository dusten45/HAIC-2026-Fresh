import pytest

from joint_plan.report import paired_finish_timing


def test_speed_comparison_uses_only_joint_finishes():
    def episode(seed, lap):
        return dict(track_id=4, geometry_seed=seed, lap_time_s=lap, finished=lap is not None,
                    complete=True, reset_sha256=str(seed))

    reference = dict(directory='champion', conditions={},
                     records=[episode(31, 20.), episode(32, 30.), episode(33, 100.), episode(36, None)])
    candidate = dict(directory='teacher_plan', conditions={},
                     records=[episode(31, 15.), episode(32, 25.), episode(33, None), episode(36, 1.)])
    result = paired_finish_timing(reference, candidate)
    assert result['common_road_count'] == result['common_geometry_count'] == 2
    assert result['paired_reference_mean_s'] == 25.
    assert result['paired_candidate_mean_s'] == 20.
    assert result['mean_paired_delta_s'] == -5.
    assert result['target_roads'][0]['gap_to_goal_s'] == 4.5
    assert result['target_roads'][0]['required_lap_reduction_percent'] == pytest.approx(30.)
    assert result['target_roads'][2]['candidate_s'] is None
    assert result['target_roads'][3]['paired_delta_s'] is None
