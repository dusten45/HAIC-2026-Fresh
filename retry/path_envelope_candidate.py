"""Build and observe one final-target-only candidate on two frozen variants."""
import hashlib
from pathlib import Path
import zipfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(source, expected_sha, helper, destination):
    assert sha(source)==expected_sha
    hashes={};changed=[]
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(destination,'x') as dst:
        for item in src.infolist():
            data=src.read(item.filename)
            if item.filename=='retry/schedule_agent.py':
                old=b'from retry.route_agent import route_target'
                assert data.count(old)==1
                data=data.replace(old,b'from retry.path_envelope_target import route_target')
                old=b'previous_steer=self.controller.previous_steer), speed)'
                assert data.count(old)==1
                data=data.replace(old,b'previous_steer=self.controller.previous_steer), speed, obstacles)')
                compile(data,item.filename,'exec');changed.append(item.filename)
            hashes[item.filename]=hashlib.sha256(data).hexdigest();dst.writestr(item,data)
        name='retry/path_envelope_target.py';data=Path(helper).read_bytes();compile(data,name,'exec')
        assert name not in hashes
        hashes[name]=hashlib.sha256(data).hexdigest();dst.writestr(name,data)
    Path(destination).chmod(0o600)
    assert changed==['retry/schedule_agent.py']
    return dict(archive_sha256=sha(destination),members_sha256=hashes,changed_original_members=changed,
        added_members=['retry/path_envelope_target.py'],other_original_members_identical=13,
        connected_route_scoring_target_unchanged=True)


def build_observer(source, expected_sha, destination):
    assert sha(source)==expected_sha
    text=Path(source).read_text()
    binding='original_target = schedule.route_target\n'
    assert text.count(binding)==1
    text=text.replace(binding,binding+"assert connected.route_target.__module__ == 'retry.route_agent'\nassert original_target.__module__ == 'retry.path_envelope_target'\n")
    old="    point = original_target(*args, **kwargs)\n"
    assert text.count(old)==1
    text=text.replace(old,old+"    route_observed['goal_selection_audit'] = dict(original_target.__globals__['LAST_TARGET_DIAGNOSTIC'])\n")
    compile(text,str(destination),'exec')
    with Path(destination).open('x') as f:f.write(text)
    Path(destination).chmod(0o600)
    return sha(destination)


def target_episode(plan_path,plan,case,arm,*,oracle):
    from retry import diagnose,frozen_composite_runtime as runtime
    from retry.compact_dev_diagnostic import compact_episode
    from retry.true_ego_geometry import ego_episode
    from retry.frozen_paired_evaluation import write
    factory0,prepare0=diagnose.make_env,runtime.prepare
    counts=dict(rows=0,changed=0,original_clear=0,no_hazards=0,empty_path=0,
        no_certified_target_original_fallback=0,shorter_path_target=0,first_change=None)
    examples=[];state=dict(steps=0)
    cap=plan['stage_budgets'][case['id']+'__'+arm]
    def factory(*args,**kwargs):
        env=factory0(*args,**kwargs);step0=env.step
        def step(action):
            output=step0(action);state['steps']+=1
            obs,reward,ended,truncated,info=output
            if state['steps']==cap and not(ended or truncated):
                state['administrative_stop']=True
                return obs,reward,ended,True,dict(info,retire_reason='fixed_full_lap_cap_censored')
            return output
        env.step=step
        return env
    def prepare(*args,**kwargs):
        worker=prepare0(*args,**kwargs);call0=worker.call
        def call(operation,obs):
            response,elapsed=call0(operation,obs)
            if operation=='act':
                q=response['speed_constraint_probe'];audit=q['goal_selection_audit'];counts['rows']+=1
                assert audit['selected_target']==q['returned_target']
                counts[audit['reason']]+=1;counts['changed']+=audit['changed']
                if audit['changed']:
                    assert audit['selected_screen']['margin_m']>=0
                    assert audit['selected_path_distance_m']<audit['original_path_distance_m']
                    if counts['first_change'] is None:counts['first_change']=counts['rows']
                    if len(examples)<3:examples.append(dict(step=counts['rows'],audit=audit))
            return response,elapsed
        worker.call=call
        return worker
    diagnose.make_env,runtime.prepare=factory,prepare
    try:
        initial=dict(plan['cached_initial_pairs'])
        result=ego_episode(plan_path,plan,case,initial,arm) if oracle else compact_episode(plan_path,dict(plan,max_steps=cap),case,initial,[],arm=arm)
    finally:
        diagnose.make_env,runtime.prepare=factory0,prepare0
    if state.get('administrative_stop'):
        result.update(terminal_observed=False,censored=True,evaluation_endpoint_observed=False,truncated=False,
            retire_reason='fixed_full_lap_cap_censored')
    result.update(target_selection_only=True,privileged_diagnostic=oracle,submission_candidate=False,
        oracle_inputs_to_policy=oracle,champion_promotion=False)
    directory=plan_path.parent/'runs'/(case['id']+'__'+arm)
    write(directory/'result.json',result)
    write(directory/'target-diagnostic.json',dict(counts=counts,examples=examples,
        selected_targets_verified_every_actual_call=True,extra_policy_calls=0,
        path_scoring_target_unchanged=True,controller_and_pedal_equations_unchanged=True),exclusive=True)
    return result
