"""Reproduce only the explicitly authorized initial DEV identity binding.

Read fixed paths in one named commit; never search repositories/private seeds,
sample a seed, instantiate an environment, or overwrite an existing case file.
"""
import ast,hashlib,json,subprocess
from pathlib import Path

G=Path(__file__).resolve().parents[1]
COMMIT='e0ac6effdf65b723f5467068c53f2133a4874050'


def prepare():
    read=lambda name:subprocess.check_output(['git','show',COMMIT+':'+name],cwd=G)
    source=read('research/initial_probe.py');tree=ast.parse(source)
    main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
    cases=next(ast.literal_eval(x.value) for x in main.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in x.targets))
    old=json.loads(read('research/results/initial_probe.json'));case=cases[0];episode=old['episodes'][0]
    assert (episode['track_id'],episode['seed'],episode['policy'])==case and episode['split']=='DEV'
    assert old['settings']['max_steps']==256 and old['settings']['frame_skip']==4
    checks={name:hashlib.sha256(read(name)).hexdigest()==hashlib.sha256((G/name).read_bytes()).hexdigest()
            for name in ('agent.py','env_wrapper.py','local_runner.py','core/vendor/car_racing.py','core/vendor/car_dynamics.py','core/track_variables.py')}
    assert all(checks.values())
    value={'source_commit':COMMIT,'source_path':'research/initial_probe.py','source_sha256':hashlib.sha256(source).hexdigest(),'case_index':0,
        'track_id':case[0],'seed':case[1],'prior_policy':case[2],
        'old_episode':{k:episode[k] for k in ('geometry_sha256_diagnostic_only','obstacles_sha256_diagnostic_only','reset_raw_ticks_including_internal_initial_step')},
        'base':dict(continuous=True,render_mode=None,verbose=False,lap_complete_percent=.95,domain_randomize=False,grass_friction_multiplier=.6),
        'wrapper':dict(skip_frames=4,stack_frames=4,no_operation=50,max_off_track_steps=100),
        'TimeLimit_max_episode_steps':1224,'current_core_source_equals_initial':checks,
        'reference':'retry.pixel_agent.PixelAgent(adaptive=True), new frozen diagnostic reference, not old starter/champion reconstruction'}
    folder=Path('/workspace/haic-response510-private');folder.mkdir(mode=0o700,exist_ok=True)
    with (folder/'approved-case-private.json').open('x') as handle:json.dump(value,handle,indent=2)
    print('Fixed public DEV identity bound privately; no reset/seed draw performed.')


if __name__=='__main__':prepare()
