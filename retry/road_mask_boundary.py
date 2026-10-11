"""Research-only replacement of two road-threshold arrays in an archived policy."""
import hashlib
import inspect

import numpy as np


def install_mask_boundary(connected):
    """Keep original image arguments, obstacles and every downstream statement."""
    original = {'routing_problem':connected.routing_problem, 'ridge_path':connected.ridge_path}
    replacements = {}; receipt = {}
    old = 'road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)'
    new = 'road = _diagnostic_road_mask.copy()'
    namespaces = []
    for name, function in original.items():
        source = inspect.getsource(function)
        assert source.count(old) == 1
        changed = source.replace(old, new)
        assert changed.replace(new, old) == source
        # Routing must retain its live module globals so its ridge observer and
        # the original downstream helpers remain the ones actually called.
        namespace = function.__globals__ if name == 'routing_problem' else dict(function.__globals__)
        exec(compile(changed, function.__code__.co_filename, 'exec'), namespace)
        replacements[name] = namespace[name]; namespaces.append(namespace)
        receipt[name] = {'original_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                         'one_threshold_statement_replaced':True}
    for name, function in replacements.items(): setattr(connected, name, function)

    def set_mask(mask):
        assert mask.shape == (84,84) and np.isin(mask,[0,1]).all()
        for namespace in namespaces: namespace['_diagnostic_road_mask'] = mask.astype(np.uint8)
    def restore():
        for name, function in original.items(): setattr(connected, name, function)
    def activate():
        for name, function in replacements.items(): setattr(connected, name, function)
    return set_mask, restore, activate, receipt
