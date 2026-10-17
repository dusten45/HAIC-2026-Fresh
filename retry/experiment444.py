"""Two separately registered, sequential model-only falsifications. No actual API."""
import time
WORKER_START = time.perf_counter()
import copy
import datetime
import json
import os
import signal
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.pilot436_meter import Meter as BaseMeter
from retry.pilot420_backend import capture_context, snapshot, fingerprint, rnghash
from retry.pilot420_backend import TechnicalStop, ResourceStop
from retry.observer435 import Child, GuardianChild
from retry.planner419 import GoalLedger
from retry.audit439 import replay, root_ledger
from retry.ledger439 import compare_first
from retry.paired417_common import arrival
from retry.pilot421_run import compare_frames
from retry.receipt421_io import load_receipt, save_receipt
from retry.loss389_analyze import read, save, sha


class PhysicalStop(Exception):
    pass


def checkpoint(directory, phase, **facts):
    save(directory/'progress-private.json', dict(stage=444, phase=phase, pid=os.getpid(),
         at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **facts))


class Meter444(BaseMeter):
    def persist(self):
        self.b.update(CPU_s=time.process_time(), execution_wall_s=time.perf_counter()-WORKER_START)
        save(self.d/'budget.json', self.b)

    def guard(self):
        self.persist()
        cap = self.p['caps']
        if time.process_time() >= cap['CPU_s'] or time.perf_counter()-WORKER_START >= cap['wall_s']:
            raise ResourceStop('model_time_cap')
        if datetime.datetime.now(datetime.timezone.utc) >= datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):
            raise ResourceStop('effective_Oct20_deadline')

    def world(self, state, tag):
        if self.b['worlds'] >= self.p['caps']['worlds']:
            raise ResourceStop('world_cap')
        return super().world(state, tag)

    def step(self, model, act, tag):
        if self.b['reserved_ticks']+4 > self.p['caps']['ticks']:
            raise ResourceStop('tick_cap')
        return super().step(model, act, tag)


class Experiment:
    def __init__(self, root, d, meter):
        self.root, self.d, self.meter = root, d, meter
        self.p = read(d/'plan.json')
        self.fixed = read(Path(self.p['fixed_plan']))
        self.pace = np.asarray(read(root/'stage404/profiles-private.json')['frozen268'])
        self.rows = [json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
        self.index = self.p['root_step']-1
        packet = load_receipt(root/f'stage442/actual_C0/C0_step{self.index+1}-before-native-private.json')
        self.full = packet['full_pre_before_nominal']
        from retry.terminal410_model import from_actual_full
        self.state = from_actual_full(self.full)
        self.memory = packet['full_pre_before_nominal']['controller']
        self.actual = root_ledger(self.rows[self.index])
        self.actual_stamp = self.actual.digest()
        self.children = []
        self.held = None
        self.qualification = None
        self.arm_summaries = []

    def new(self, state, memory, ledger, label, recipe='nominal', guardian=False):
        self.meter.capture_inputs(state, memory, ledger, label+'_inputs', gate='444_MODEL_ONLY')
        cls = GuardianChild if guardian else Child
        c = cls(self.meter, copy.deepcopy(state), copy.deepcopy(memory), ledger,
                self.fixed, self.pace, label, recipe=recipe, world_tag=label)
        self.children.append(c)
        return c

    def close(self, c):
        c.dump(self.d)
        c.close()

    def assert_actual(self):
        if self.actual.digest() != self.actual_stamp:
            raise TechnicalStop('actual_ledger_mutated_by_model')

    def qualify(self):
        held = self.new(self.state, self.memory, self.actual, 'held')
        self.held = held
        nominal = held.ctrl.act(held.m)
        self.context = capture_context(held.m, held.ctrl, self.memory, nominal, self.actual,
                                       self.fixed, '444_DIAGNOSTIC', {}, self.actual_stamp)
        self.state = snapshot(held.m)
        state_hash, memory_hash, rng_hash = fingerprint(snapshot(held.m)), fingerprint(held.ctrl.memory()), rnghash()
        def unchanged():
            if (fingerprint(snapshot(held.m)), fingerprint(held.ctrl.memory()), rnghash()) != (state_hash, memory_hash, rng_hash):
                raise TechnicalStop('held_parent_memory_state_RNG_mutation')
            self.assert_actual()
        sigs, audits = [], []
        expected = self.rows[self.index:self.index+self.p['horizon']]
        first = None
        for rep in range(2):
            c = self.new(self.state, self.memory, self.actual, 'qualification'+str(rep+1))
            try:
                for row in expected:
                    c.one('qualification', first_override=row['command'])
                    if c.status != 'ACTIVE':
                        raise TechnicalStop('factual_calibration_nonactive')
                    unchanged()
                audit = replay(c.rows, expected, self.fixed)
                if audit['certified_prefix_actions'] != len(expected) or audit['fresh_current_first_pass'] < 1:
                    raise TechnicalStop('factual_body_wheel_geometry_ledger_or_current_input')
                # Exact copied-current input/memory/nominal gate; future replay
                # memory drift is diagnostic rather than fresh-current equality.
                compare_first(self.actual, c.rows[0], expected[0], self.fixed)
                sigs.append(c.signature())
                audits.append(audit)
                if first is None:
                    first = copy.deepcopy(c.rows[0])
            finally:
                self.close(c)
        if sigs[0] != sigs[1]:
            raise TechnicalStop('calibration_independent_repeat')
        unchanged()
        held.one('held_first', prepared_nominal=nominal, prepared_before=self.memory)
        check = compare_frames(held.rows[0], first)
        if not check['passed'] or check['wheel']['clipped_flag_mismatches']:
            raise TechnicalStop('held_parent_own_first_transition')
        self.close(held)
        self.qualification = dict(passed=True, replays=audits, held_first=check,
                                  actual_ledger_unchanged=True)
        save(self.d/'qualification-private.json', self.qualification)
        self.meter.qualification_passed = True
        checkpoint(self.d, 'QUALIFICATION_PASSED', ticks=self.meter.b['ticks'], worlds=self.meter.b['worlds'])

    def branch(self, label, recipe, horizon):
        c = self.new(self.state, self.memory, self.actual, label, recipe)
        try:
            c.initial13('experiment_initial13')
            if horizon == 14 and c.status == 'ACTIVE' and c.initial_safe and c.initial_progress:
                # Freeze H13 on this exact world, then observe only transition14.
                root_parent = self.root_context()
                c.stream.prepare_boundary(root_parent)
                c.stream.start_tail()
                c.one('experiment_transition14')
                c.tail_count = 1
                save_receipt(self.d/(label+'-one-transition-tail-private.json'), asdict(c.stream.tail_record()))
            summary = dict(label=label, recipe=recipe, status=c.status, error=c.error,
                           actions=len(c.rows), safe=not any(r['safety'] for r in c.rows),
                           progress=not c.ledger.deadline_missed,
                           initial13_safe=c.initial_ok and c.initial_safe and c.initial_progress,
                           signature=c.signature(), rows=copy.deepcopy(c.rows))
            self.arm_summaries.append({k:v for k,v in summary.items() if k!='rows'})
            return summary
        finally:
            self.close(c)
            self.assert_actual()

    def root_context(self):
        return self.context

    def h1(self):
        from retry.executor397 import canonical_projection
        pre = self.rows[self.index]['pre']
        nominal = self.rows[self.index]['nominal']
        q = canonical_projection(self.fixed['line'], pre['pos'], pre['vel'], self.memory['C']['phase'])
        j, u = q['index'], q['u']
        nodes = np.asarray(self.fixed['free_profile']['speed'])*self.pace
        target = float(np.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2))
        if not (self.memory['C']['phase']=='FIRST_LAP' and nominal[2]>0 and 30<=pre['speed']<target and q['sigma']>=0 and all(x>0 for x in pre['road_contacts'])):
            return dict(status='PREDICATE_NOT_MET', learning='Current H1 opportunity absent; no replacement root.')
        arms = {}
        for recipe in ['nominal','fullgas']:
            pair = []
            for rep in range(2):
                a = self.branch(recipe+str(rep+1), recipe, 13)
                pair.append(a)
                if not a['safe'] or not a['progress'] or len(a['rows']) != 13:
                    return dict(status='PHYSICAL_REFUTATION', failed_recipe=recipe,
                                observed_actions=len(a['rows']), reason=a['error'],
                                learning='No other pulse/root; naive first-gas headroom not established here.')
            if pair[0]['signature'] != pair[1]['signature']:
                raise TechnicalStop('H1_independent_repeat')
            arms[recipe] = pair[0]
        start = self.actual.progress_m
        exits = {}
        for name, arm in arms.items():
            hit = arrival(arm['rows'], np.asarray(self.fixed['line']), start, start+30.)
            speed = yaw = path = joint = omega = None
            if hit['reached']:
                lo, hi = hit['rawtick_bracket']
                endpoints = []
                for row in arm['rows']:
                    for hull in row['raw_hull']:
                        tick = round((hull['time']-self.state['physical']['actual_time'])*50)
                        if tick in [lo,hi]:
                            endpoints.append(float(np.linalg.norm(hull['COM_linear_velocity'])))
                if endpoints:
                    speed = [min(endpoints),max(endpoints)]
            last = arm['rows'][-1]
            exits[name] = dict(**hit, observed_exit_speed_endpoints=speed,
                              terminal_speed=last['predicted']['speed_m_s'],
                              terminal_yaw=last['predicted']['angular_velocity'],
                              terminal_path_error_m=last['path_error_m'],
                              terminal_joint=[z['joint_angle'] for z in last['tires'][-4:-2]],
                              terminal_omega=[z['omega'] for z in last['tires'][-4:]],
                              terminal_force_ratio=[z['force_ratio'] for z in last['tires'][-4:]])
        a,b = exits['nominal'], exits['fullgas']
        gain = None
        if a['reached'] and b['reached']:
            gain = [a['elapsed_bracket_s'][0]-b['elapsed_bracket_s'][1],
                    a['elapsed_bracket_s'][1]-b['elapsed_bracket_s'][0]]
        sampled_speed_debt = (a['observed_exit_speed_endpoints'] is None or b['observed_exit_speed_endpoints'] is None or
                              b['observed_exit_speed_endpoints'][0] < a['observed_exit_speed_endpoints'][1])
        return dict(status='H1_COMPLETED_MODEL_ONLY', common_exit=exits, gain_bracket_s=gain,
                    timing_threshold_met=bool(gain and gain[0]>=.08),
                    sampled_exit_speed_debt=sampled_speed_debt,
                    promotion=False, learning='Report even small/overlapping effects; terminal state debt unresolved, no lap/actual promotion.')

    def guardian_parent(self, label):
        p = self.new(self.state, self.memory, self.actual, label)
        choices = []
        try:
            for k in range(14):
                before = copy.deepcopy(p.ctrl.memory())
                nominal = p.ctrl.act(p.m)
                ph,mh,rh = fingerprint(snapshot(p.m)), fingerprint(p.ctrl.memory()), rnghash()
                selected = None
                for recipe in ['nominal','neutralbrake']:
                    pair = []
                    for rep in range(2):
                        c = self.new(snapshot(p.m), before, p.ledger,
                                     label+f'_decision{k+1}_{recipe}{rep+1}', recipe, guardian=True)
                        try:
                            c.initial13('B_shadow')
                            if (fingerprint(snapshot(p.m)),fingerprint(p.ctrl.memory()),rnghash()) != (ph,mh,rh):
                                raise TechnicalStop('B_parent_query_mutated')
                            pair.append(dict(signature=c.signature(), valid=c.initial_ok and c.initial_safe and c.initial_progress,
                                             first=copy.deepcopy(c.rows[0])))
                        finally:
                            self.close(c)
                    if pair[0]['signature'] != pair[1]['signature']:
                        raise TechnicalStop('B_shadow_repeat')
                    if pair[0]['valid']:
                        selected = pair[0]['first']
                        choices.append(recipe)
                        break
                if selected is None:
                    raise PhysicalStop('B_both_guardians_infeasible')
                # B is a model parent with conditional actions, not nominal C
                # planner continuation. Its observed generic H13 is diagnostic.
                old_progress, old_goal = p.ledger.progress_m, p.ledger.goal_m
                parent_before = snapshot(p.m)
                p.one('B_parent', first_override=selected['command'],
                      prepared_nominal=nominal, prepared_before=before)
                check = compare_frames(p.rows[-1],selected)
                if not check['passed'] or check['wheel']['clipped_flag_mismatches']:
                    raise TechnicalStop('B_own_parent_vs_selected_first')
                own = p.rows[-1]
                if own['memory_before'] != selected['memory_before'] or own['memory_after'] != selected['memory_after']:
                    raise TechnicalStop('B_first_nominal_memory_exact')
                if p.ledger.age_actions != selected['model_age'] or p.ledger.last_clock_tick != round(selected['predicted']['time']*50):
                    raise TechnicalStop('B_first_discrete_ledger')
                from retry.geometry439 import Projection439, Interval
                geometry = Projection439(self.fixed['line'], sum(self.fixed['free_profile']['ds']), .1)
                h0, h1 = own['raw_hull'][0], selected['raw_hull'][0]
                pose = lambda h:dict(pos=h['origin_position'],vel=h['COM_linear_velocity'])
                post = lambda r:dict(pos=r['predicted']['position'],vel=r['predicted']['velocity'])
                transition = geometry.transition(pose(h0),post(own),pose(h1),post(selected),before['C']['phase'],own['memory_after']['C']['phase'])
                bound = geometry.progress_interval(Interval.point(old_progress),transition)
                if not(bound.contains(p.ledger.progress_m) and bound.contains(selected['model_progress'])) or ((p.ledger.progress_m>=old_goal)!=(selected['model_progress']>=old_goal)):
                    raise TechnicalStop('B_model_ledger_geometry_or_goal_side')
                if p.status != 'ACTIVE':
                    raise PhysicalStop('B_parent_'+p.status)
                self.assert_actual()
                checkpoint(self.d,'B_DECISION_COMPLETE',label=label,decision=k+1,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
            return dict(signature=p.signature(), choices=choices, actions=len(p.rows),safe=True)
        finally:
            self.close(p)

    def h2(self):
        pair = [self.branch('predicate_nominal'+str(rep+1),'nominal',14) for rep in range(2)]
        if pair[0]['signature'] != pair[1]['signature']:
            raise TechnicalStop('H2_nominal_repeat')
        a = pair[0]
        predicate = a['initial13_safe'] and a['status']=='UNSAFE' and len(a['rows'])==14
        if not predicate:
            return dict(status='PREDICATE_NOT_MET', nominal=a['status'],nominal_actions=len(a['rows']),
                        initial13_safe=a['initial13_safe'],learning='New nominal14 prediction did not show the proposed mismatch; no B or replacement root.')
        b = [self.guardian_parent('B'+str(rep+1)) for rep in range(2)]
        if b[0]['signature'] != b[1]['signature'] or b[0]['choices'] != b[1]['choices']:
            raise TechnicalStop('B_parent_independent_repeat')
        return dict(status='H2_LOCAL_REPRESENTATION_COUNTEREXAMPLE',nominal_safe13_unsafe14=True,
                    B14_safe=True,B_choices=b[0]['choices'],B_independent_repeat_exact=True,
                    finish_witness=False,time_ranking_eligible=False,promotion_to_actual=False)


def prepare(root):
    g = Path(__file__).resolve().parents[1]
    d = root/'stage444'
    assert not d.exists()
    d.mkdir(mode=0o700)
    old = read(root/'stage442/plan.json')
    v = read(root/'project-effective-budget-v463.json')
    deadline = read(root/'research-deadline-current.json')['deadline_utc']
    assert v['authorization_end_utc']==deadline=='2026-10-20T10:01:55Z'
    assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27516,84000,0)
    files = {Path(x) for x in old['sources'] if str(x).startswith(str(g))}
    files.update(g/'retry'/x for x in ['experiment444.py','static444.py','decompose443.py','design443.py'])
    files.update([Path(old['fixed_plan']),root/'stage404/profiles-private.json',root/'stage442/actual_C0/trace-private.jsonl',
                  root/'project-effective-budget-v463.json',root/'research-deadline-current.json',g/'retry/hypotheses443_design.json'])
    for step in [23,90]:
        files.add(root/f'stage442/actual_C0/C0_step{step}-before-native-private.json')
    sources = {str(p):sha(p) for p in files}
    semantic = dict(old['semantic_sources'])
    semantic.update({str(p):sha(p) for p in files if str(p).startswith(str(g)) and p.suffix=='.py'})
    base = dict(stage=444,deadline_utc=deadline,fixed_plan=old['fixed_plan'],sources=sources,
                semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],
                actual_reset_learning_new_seed_HOLDOUT_SEALED_reserve_paid_cap=0,
                first_technical_error_stops_both=True,no_retry=True)
    save(d/'plan.json',base)
    (d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    for name,step,horizon,caps,worst,worlds in [('H1',23,13,dict(ticks=512,worlds=8,CPU_s=90,wall_s=150),316,7),
                                             ('H2',90,14,dict(ticks=6656,worlds=128,CPU_s=240,wall_s=480),6164,119)]:
        folder=d/name;folder.mkdir(mode=0o700)
        p=dict(base,hypothesis=name,root_step=step,horizon=horizon,caps=caps,
               worst_planned_ticks=worst,worst_planned_worlds=worlds,
               proposal=read(g/'retry/hypotheses443_design.json')['hypotheses'][0 if name=='H1' else 1])
        assert worst<=caps['ticks'] and worlds<=caps['worlds']
        save(folder/'plan.json',p);(folder/'plan.sha256').write_text(sha(folder/'plan.json')+'\n')
    checkpoint(d,'PLANS_FROZEN',new_actual_actions=0,new_model_ticks=0)
    print('444 separate H1/H2 plans frozen; arithmetic316/7 and6164/119; no integration')


def run(root, name):
    d=root/'stage444'/name
    p=read(d/'plan.json')
    assert not(d/'opening.json').exists()
    assert read(root/'stage444/static-result.json')['passed']
    if name=='H2':
        assert read(root/'stage444/H1/result.json')['status']!='TECHNICAL_STOP'
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for group in [p['sources'],p['protected']]:
        for file,digest in group.items():assert sha(file)==digest,file
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);ex=None;outcome={};error=None
    def timeout(*args):raise ResourceStop('registered_model_time_signal')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,p['caps']['CPU_s']-time.process_time()))
    signal.setitimer(signal.ITIMER_REAL,max(.001,p['caps']['wall_s']-(time.perf_counter()-WORKER_START)))
    checkpoint(d,'QUALIFICATION_STARTED',ticks=0,worlds=0)
    try:
        ex=Experiment(root,d,meter);ex.qualify();outcome=ex.h1() if name=='H1' else ex.h2()
    except PhysicalStop as e:
        outcome=dict(status='PHYSICAL_REFUTATION',reason=str(e),promotion=False)
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
        outcome=dict(status='TECHNICAL_STOP',error=error)
        save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        if ex:
            for c in ex.children:
                if not c.closed:
                    try:ex.close(c)
                    except BaseException:pass
        meter.closeall();meter.persist()
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in previous.items():signal.signal(s,h)
    result=dict(stage=444,hypothesis=name,**outcome,budget=read(d/'budget.json'),
                qualification=None if ex is None else ex.qualification,
                arms=[] if ex is None else ex.arm_summaries,actual_actions_resets_learning_new_seed_SEALED=0,
                plan_sha256=sha(d/'plan.json'))
    save(d/'result.json',result)
    checkpoint(d,'HYPOTHESIS_CLOSED',status=outcome['status'],error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])
    print(json.dumps(dict(hypothesis=name,status=outcome['status'],error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])))


if __name__=='__main__':
    root=Path(sys.argv[2])
    prepare(root) if sys.argv[1]=='prepare' else run(root,sys.argv[1])
