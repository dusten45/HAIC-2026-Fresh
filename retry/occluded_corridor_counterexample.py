"""Public pixel-observability example; not a valid-track impossibility proof.

The positive scene is a straight fixed-width road. The negative scene adds a
synthetic hidden grass hole and is NOT certified to satisfy HAIC tile topology.
Identical visible pixels prove that a visibility test alone cannot distinguish
these masks. They do not prove that the real track contract permits the hole.
No renderer environment, model or Agent is instantiated.
"""
import json
import time
import numpy as np


def check():
    cpu = time.process_time()
    road = np.zeros((84, 84), dtype=bool)
    road[:, 20:40] = True  # 20 pixels / 1.5 px/m = public width 40/3 m.
    opaque = np.zeros_like(road)
    opaque[30:51, 26:36] = True
    negative = road.copy()
    negative[38:44, 29:33] = False  # Synthetic; no claim of HAIC-valid topology.

    def observed(mask):
        image = np.where(mask, 100, 160).astype(np.uint8)
        image[opaque] = 60
        return image

    positive_image, negative_image = observed(road), observed(negative)
    assert np.array_equal(positive_image, negative_image)
    # A six-sample plateau immediately beside the road/grass edge is visible.
    samples = [(x, y) for y in range(38, 41) for x in (38, 39)]
    raw_count = sum(positive_image[y, x] == 100 for x, y in samples)
    flat_count = sum(np.ptp(positive_image[y-1:y+2, x-1:x+2]) <= 7.1
                     for x, y in samples)
    assert raw_count == 6 and flat_count == 3
    # Both neighboring rows offer original horizontal >=3-pixel side anchors.
    for y in (37, 44):
        assert np.all(positive_image[y, 20:26] == 100)
        assert np.all(positive_image[y, 36:40] == 100)
    assert road[40, 30] and not negative[40, 30] and opaque[40, 30]
    return dict(
        visible_images_identical=True, visible_raw_plateau_samples=int(raw_count),
        flat_3x3_samples=int(flat_count), adjacent_horizontal_anchors_at_least_3=True,
        positive_hidden_point_is_road=True, synthetic_negative_hidden_point_is_road=False,
        positive_width_m=40/3, positive_turn_per_node_rad=0,
        negative_scope='Pixel-observability counterexample only; not certified as a valid HAIC tile chain.',
        conclusion='Raw plateau availability and hidden corridor validity are separate tests. '
                   'A real-contract same-ribbon/topology inclusion bound remains unproved; '
                   'this example proves neither universal impossibility nor a safe fill rule.',
        model_ticks=0, native_actions=0, CPU_s=time.process_time()-cpu)


if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True))
