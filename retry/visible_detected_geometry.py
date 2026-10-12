"""Privileged geometry correction for existing current-frame detections only.

Reuses the positive rendered-ownership association from the earlier center
diagnostic. The actor receives one replacement list aligned to its actual
detector output, never visibility layers, hidden objects, IDs or new detections.
This is a research intervention and is not submission legal.
"""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from retry.visible_obstacle_oracle_v2 import detection_components, match_visible_centers

OBSERVER_SHA256 = 'a5d36c63c672b7d221c426da3646cd60f04f9889c257dca397a7e61e1a487b43'
OBS_BYTES = 4 * 84 * 84 * 4


def current_detections(components):
    # Exact frozen131/181 detector inverse; association still uses pixel support.
    return [((float(c['centroid_pixel_xy'][0])-41.542)/1.3608,
             (62.4475-float(c['centroid_pixel_xy'][1]))/1.701, 1.2)
            for c in components]


def associate(image, components, context, radii):
    original = current_detections(components)
    old_inverse = [(*c['detected_center'], 1.2) for c in components]
    _, receipt = match_visible_centers(image, old_inverse, context['body_centers'],
                                       context['visible_coverage'])
    assert receipt['source_component_alignment_exact']
    corrected = list(original)
    matches = []
    for item in receipt['decisions']:
        if item['decision'] != 'matched_center_only':
            continue
        i, j = item['detection_index'], item['GT_index']
        center = context['body_centers'][j]
        corrected[i] = (float(center[0]), float(center[1]), float(radii[j]))
        matches.append(dict(detection_index=i, obstacle_id=context['ids'][j],
            original=list(original[i]), corrected=list(corrected[i]),
            center_error_m=float(np.linalg.norm(np.asarray(original[i][:2])-center)),
            radius_error_m=abs(original[i][2]-float(radii[j])),
            component_area=components[i]['area']))
    assert len(corrected) == len(original)
    return dict(original=original, replacement=corrected), dict(
        detections=len(original), matched=len(matches), unmatched=len(original)-len(matches),
        matches=matches, effective_centers=sum(m['center_error_m']>1e-9 for m in matches),
        effective_radii=sum(m['radius_error_m']>1e-6 for m in matches),
        max_radius_error_m=max((m['radius_error_m'] for m in matches),default=0.0),
        added_detections=0, unmatched_unchanged=True)


def context_for_existing_detections(env, image):
    from retry.visible_obstacle_oracle_v2 import current_visible_context
    components = detection_components(image)
    if components:
        context = current_visible_context(env)
        radii = [float(env.unwrapped.obstacles[i].fixtures[0].shape.radius) for i in context['ids']]
        packet, receipt = associate(image, components, context, radii)
        receipt.update(label_raster_passes=context['receipt']['label_raster_passes'],
                       component_extractions=2, visible_context_calls=1)
    else:
        packet = dict(original=[], replacement=[])
        receipt = dict(detections=0,matched=0,unmatched=0,matches=[],effective_centers=0,effective_radii=0,
            max_radius_error_m=0.0,added_detections=0,unmatched_unchanged=True,
            label_raster_passes=0,component_extractions=1,visible_context_calls=0)
    return packet, receipt


def pack(observation, packet):
    assert observation.shape==(4,84,84) and observation.dtype==np.float32
    header=json.dumps(dict(kind='existing_detection_geometry_v1',**packet),allow_nan=False).encode()
    return np.frombuffer(observation.tobytes()+struct.pack('<I',len(header))+header,np.uint8)


def build_worker(source, destination):
    source=Path(source);text=source.read_text()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==OBSERVER_SHA256
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new)
    replace('import base64\n','import base64\nimport struct\n')
    replace('observed = {}\nroute_observed = {}','geometry_context = None\nobserved = {}\nroute_observed = {}')
    replace('    return output\n\n\ndef tracker', '''    original = np.asarray(output[1], np.float64).reshape(-1,3)
    expected = np.asarray(geometry_context['original'], np.float64).reshape(-1,3)
    replacement = np.asarray(geometry_context['replacement'], np.float64).reshape(-1,3)
    assert np.array_equal(original, expected) and original.shape == replacement.shape
    assert np.isfinite(replacement).all() and np.all(replacement[:,2] > 0)
    contact_observed['applied_detected_obstacles_xyr'] = replacement.tolist()
    contact_observed['privileged_geometry_replacement'] = True
    return output[0], [tuple(v) for v in replacement]


def tracker''')
    replace("'ready':True,'simulator_imported':False,", "'ready':True,'simulator_imported':False,\n                  'privileged_diagnostic':True,'submission_candidate':False,\n                  'geometry_boundary':'existing current detections only; original count/order/path; no visibility mask or object IDs',")
    replace('    obs = np.frombuffer(base64.b64decode(request[\'observation\']),dtype=np.float32).reshape(4,84,84).copy()', '''    packed = base64.b64decode(request['observation'], validate=True)
    obs_bytes = 4*84*84*4
    obs = np.frombuffer(packed[:obs_bytes], dtype=np.float32).reshape(4,84,84).copy()
    size = struct.unpack('<I', packed[obs_bytes:obs_bytes+4])[0]
    assert 0 < size <= 65536 and len(packed) == obs_bytes+4+size
    geometry_context = json.loads(packed[obs_bytes+4:])
    assert set(geometry_context) == {'kind','original','replacement'}
    assert geometry_context['kind'] == 'existing_detection_geometry_v1'
    assert len(geometry_context['original']) == len(geometry_context['replacement'])''')
    replace('Read-only pixel observer for frozen original and HUD pedal-feedback archives.',
            'Privileged existing-detection geometry diagnostic for frozen normal32; never a submission.')
    compile(text,str(destination),'exec')
    destination=Path(destination)
    with destination.open('x') as f:f.write(text)
    destination.chmod(0o600)
    return hashlib.sha256(destination.read_bytes()).hexdigest()
