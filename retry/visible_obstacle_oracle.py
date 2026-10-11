"""Privileged current-visible obstacle-center diagnostic, never a policy.

The evaluator must supply per-obstacle *visible ownership*, after all later
obstacles, car and HUD occlusion, in the native resize pipeline. A projected disk
alone is insufficient. Hidden objects have zero ownership and cannot be added.
This module does not import a simulator or invoke a renderer, agent or model.
"""
import math

import cv2
import numpy as np


def world_to_body(centers_world, position_world, hull_angle):
    """Native camera rotates world differences by -hull.angle; x/right,y/forward."""
    points = np.asarray(centers_world, dtype=np.float64).reshape(-1, 2)
    position = np.asarray(position_world, dtype=np.float64).reshape(2)
    assert np.isfinite(points).all() and np.isfinite(position).all()
    assert math.isfinite(hull_angle)
    c, s = math.cos(hull_angle), math.sin(hull_angle)
    return (points - position) @ np.array([[c, -s], [s, c]])


def project_body_centers(centers_body, observation_time_s):
    """Return continuous raw and84px pixel-center coordinates, not a raster.

    Source:1000x800, camera origin(500,200), vertical pixel flip y'=799-y;
    smoothscale to96x96 then cv2 linear resize to84x84. Center-coordinate
    mapping is (raw+.5)*84/raw_size-.5; area/linear filter support is wider.
    Exact16-gon orientation/raster/visibility must come from the evaluator.
    """
    points = np.asarray(centers_body, dtype=np.float64).reshape(-1, 2)
    t = float(observation_time_s)
    assert np.isfinite(points).all() and math.isfinite(t) and t >= 0
    zoom = .6 * max(1 - t, 0) + 16.2 * min(t, 1)
    raw = points * np.array([zoom, -zoom]) + np.array([500., 599.])
    image = (raw + .5) * np.array([84 / 1000, 84 / 800]) - .5
    return {'zoom': zoom, 'raw_after_flip_xy': raw.tolist(),
            'observation_pixel_center_xy': image.tolist()}


def detection_components(image):
    """Source-identical component support from the frozen clearance detector.

    The returned pixel coordinates are(y,x), ordered like original detections.
    No road path is recomputed, returned or substituted.
    """
    image = np.asarray(image)
    assert image.shape == (84, 84) and image.dtype == np.float32
    assert np.isfinite(image).all() and image.min() >= 0 and image.max() <= 1
    road = ((image > .32) & (image < .47)).astype(np.uint8)
    road[61:] = 0
    closed = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    holes = ((closed != 0) & (road == 0) & (image >= .64) & (image <= .71)).astype(np.uint8)
    holes[61:] = 0
    count, labels, stats, centers = cv2.connectedComponentsWithStats(holes, connectivity=8)
    components = []
    for label in range(1, count):
        _, _, width, height, area = stats[label]
        if 3 <= area <= 30 and 2 <= width <= 9 and 2 <= height <= 9:
            cx, cy = centers[label]
            components.append({'label': label, 'centroid_pixel_xy': [float(cx), float(cy)],
                'detected_center': [(float(cx) - 42) / 1.3608, (63 - float(cy)) / 1.701],
                'pixels_yx': np.argwhere(labels == label), 'area': int(area)})
    return components


def match_visible_centers(image, detections, gt_body_centers, visible_coverage):
    """Replace only mutually unique, fully supported original detection centers.

    visible_coverage is evaluator-only uint8(N,84,84): each layer is the native
    white ownership stencil of ONE obstacle, cleared by all later opaque draws,
    flipped and resized1000x800→96→84. It is NOT an unoccluded footprint.
    Caller must bind layer order to gt_body_centers and current observation time.
    We demand every observed component pixel has coverage>=128, and at least
    one is255 (an unmixed ownership witness). Any nonzero overlap with another
    obstacle's visible layer makes the component ambiguous. An obstacle touching
    multiple components is also ambiguous. No nearest-distance rule is used.
    Conservatively unmatched/ambiguous components, radii, order and count remain
    unchanged; original path and tracker/control logic are outside this helper.
    """
    original = [tuple(item) for item in detections]
    values = np.asarray(original, dtype=np.float64).reshape(-1, 3)
    centers = np.asarray(gt_body_centers, dtype=np.float64).reshape(-1, 2)
    coverage = np.asarray(visible_coverage)
    assert np.isfinite(values).all() and np.isfinite(centers).all()
    assert coverage.dtype == np.uint8 and coverage.shape == (len(centers), 84, 84)
    components = detection_components(image)
    receipt = {'privileged': True, 'submission_legal': False,
        'input_detections': len(original), 'GT_layers': len(centers),
        'hidden_GT_layers': int(np.sum(~np.any(coverage != 0, axis=(1, 2)))),
        'added_detections': 0, 'replaced_centers': 0, 'decisions': [],
        'visibility_scope': 'Caller-supplied native per-obstacle visible ownership; component support and mutual uniqueness checked here'}
    if len(components) != len(original) or any(
            not np.array_equal(values[i, :2], np.asarray(component['detected_center']))
            for i, component in enumerate(components)):
        receipt['source_component_alignment_exact'] = False
        receipt['decisions'] = [{'detection_index': i, 'decision': 'unchanged_component_alignment_mismatch'}
                               for i in range(len(original))]
        return original, receipt
    receipt['source_component_alignment_exact'] = True
    overlaps, supported = [], []
    for component in components:
        pixels = component['pixels_yx']
        local = coverage[:, pixels[:, 0], pixels[:, 1]]
        overlaps.append(np.flatnonzero(np.any(local > 0, axis=1)).tolist())
        supported.append(np.flatnonzero(np.all(local >= 128, axis=1) &
                                        np.any(local == 255, axis=1)).tolist())
    touching = {index: [i for i, ids in enumerate(overlaps) if index in ids]
                for index in range(len(centers))}
    replaced = list(original)
    for i, component in enumerate(components):
        candidates = overlaps[i]
        decision = {'detection_index': i, 'component_label': component['label'],
                    'component_area': component['area'], 'overlapping_GT_indices': candidates,
                    'fully_supported_GT_indices': supported[i], 'decision': 'unchanged_unmatched'}
        if len(candidates) > 1:
            decision['decision'] = 'unchanged_ambiguous_GT_overlap'
        elif len(candidates) == 1:
            index = candidates[0]
            if len(touching[index]) != 1:
                decision['decision'] = 'unchanged_ambiguous_component_overlap'
            elif index not in supported[i]:
                decision['decision'] = 'unchanged_insufficient_visible_support'
            else:
                replaced[i] = (float(centers[index, 0]), float(centers[index, 1]), original[i][2])
                decision.update(decision='matched_center_only', GT_index=index,
                                original_center=list(original[i][:2]),
                                replacement_center=centers[index].tolist())
                receipt['replaced_centers'] += 1
        receipt['decisions'].append(decision)
    assert len(replaced) == len(original)
    assert all(new[2] == old[2] for new, old in zip(replaced, original))
    return replaced, receipt


def current_visible_context(env):
    """Evaluator-only native label raster; never import/call this in an actor.

    Returns ids(visible original indices), body_centers(float64 N,2), visible_coverage(uint8 N,84,84),
    and an evaluator receipt. Only nonzero currently visible layers are returned.
    Root may transmit the centers and coverage through a dedicated privileged packet;
    the actor policy hook must still preserve the original detected path/count.
    Label rasterization does not call env.render/reset/step or mutate raw.surf.
    """
    # These imports are deliberately lazy: the pure matching helper is usable
    # inside a worker whose audit denies core/gym/Box2D imports.
    import pygame
    from core.vendor.car_racing import OBSTACLE_RENDER_VERTICES, WINDOW_W, WINDOW_H, STATE_W, STATE_H
    from core.vendor.car_dynamics import SIZE, WHEEL_R, WHEEL_W
    from retry.current_view_road_oracle import camera
    from retry.visible_road_occlusion import renderer_polygon, polygon_pixels, hud_polygons

    raw = env.unwrapped
    cam = camera(raw)
    polygons, candidates = [], []
    for index, body in enumerate(raw.obstacles):
        x, y = body.position
        radius = body.fixtures[0].shape.radius
        polygon = [(x + radius * math.cos(2 * math.pi * i / OBSTACLE_RENDER_VERTICES),
                    y + radius * math.sin(2 * math.pi * i / OBSTACLE_RENDER_VERTICES))
                   for i in range(OBSTACLE_RENDER_VERTICES)]
        polygons.append(polygon)
        points = np.asarray(polygon_pixels(polygon, *cam))
        # Two raw pixels of conservative AA margin; nonzero scaled ownership
        # below is the final visibility test, never this bounding box alone.
        if (points[:, 0].max() >= -2 and points[:, 0].min() < WINDOW_W + 2
                and points[:, 1].max() >= -2 and points[:, 1].min() < WINDOW_H + 2):
            candidates.append(index)
    state = {'speed_m_s': math.hypot(*raw.car.hull.linearVelocity),
             'angular_velocity': float(raw.car.hull.angularVelocity),
             'wheels': [{'omega': float(w.omega), 'joint_angle': float(w.joint.angle)}
                        for w in raw.car.wheels]}
    ids, centers, layers = [], [], []
    for index in candidates:
        surface = pygame.Surface((WINDOW_W, WINDOW_H))
        surface.fill((0, 0, 0))
        renderer_polygon(surface, polygons[index], 255, *cam)
        # Later obstacles overwrite this obstacle exactly in native draw order.
        for polygon in polygons[index + 1:]:
            renderer_polygon(surface, polygon, 0, *cam)
        # Native state_pixels omits skid particles. Every actual wheel/hull
        # fixture and rotating stripe is opaque and clears obstacle ownership.
        for obj in raw.car.drawlist:
            for fixture in obj.fixtures:
                polygon = [tuple(obj.transform * v) for v in fixture.shape.vertices]
                pygame.draw.polygon(surface, (0, 0, 0), polygon_pixels(polygon, *cam))
                if not hasattr(obj, 'phase'):
                    continue
                phase = obj.phase
                s1, s2 = math.sin(phase), math.sin(phase + 1.2)
                c1, c2 = math.cos(phase), math.cos(phase + 1.2)
                if s1 > 0 and s2 > 0:
                    continue
                if s1 > 0:
                    c1 = float(np.sign(c1))
                if s2 > 0:
                    c2 = float(np.sign(c2))
                stripe = [(-WHEEL_W * SIZE, WHEEL_R * c1 * SIZE),
                          (WHEEL_W * SIZE, WHEEL_R * c1 * SIZE),
                          (WHEEL_W * SIZE, WHEEL_R * c2 * SIZE),
                          (-WHEEL_W * SIZE, WHEEL_R * c2 * SIZE)]
                polygon = [tuple(obj.transform * v) for v in stripe]
                pygame.draw.polygon(surface, (0, 0, 0), polygon_pixels(polygon, *cam))
        surface = pygame.transform.flip(surface, False, True)
        for polygon in hud_polygons(state):
            pygame.draw.polygon(surface, (0, 0, 0), polygon)
        # Native reward text is completely inside the opaque HUD slab already
        # cleared above, so no font initialization or text rendering is needed.
        scaled = pygame.transform.smoothscale(surface, (STATE_W, STATE_H))
        rgb = np.transpose(np.array(pygame.surfarray.pixels3d(scaled)), (1, 0, 2))
        coverage = cv2.cvtColor(cv2.resize(rgb, (84, 84)), cv2.COLOR_RGB2GRAY)
        if not np.any(coverage):
            continue
        body = raw.obstacles[index]
        center = world_to_body([tuple(body.position)], tuple(raw.car.hull.position),
                               float(raw.car.hull.angle))[0]
        ids.append(index)
        centers.append(center)
        layers.append(coverage)
    return {'ids': ids, 'body_centers': np.asarray(centers, np.float64).reshape(-1, 2),
            'visible_coverage': np.asarray(layers, np.uint8).reshape(-1, 84, 84),
            'receipt': {'privileged_diagnostic_only': True,
                        'observation_time_s': float(raw.t), 'label_raster_passes': len(candidates),
                        'returned_visible_entries': len(centers),
                        'new_env_render_reset_step_calls': 0,
                        'ownership': 'Native16-gon order, later-obstacle/car/stripe/HUD erasure; flip,96smoothscale,84lineargray',
                        'road_or_hidden_centers_sent_to_policy': False}}
