"""First-lap saved-root initialization; preserve cold signed-seam semantics."""
from retry.drive519_control import project


def initial_progress(root,path,completed):
    s=project(root.center,path,None)['s']
    # All registered non-cold roots are known first-lap prefixes, not new laps.
    return s+path['length'] if completed>0 and s<0 else s
