"""Opt-in495 direct ticks plus one immutable, nonrecursive bundle per hold.

No environment construction, integration, reset or policy query on import.
The494 callback and isolated callsite tap are reused; full ObserveMixin.one is
wrapped only after its original return, including its nominal-count checks.
"""
import copy
import functools
from dataclasses import asdict
from retry.capture494 import (Session494,Registry494,check,integer,number,encoded,
                              check_binding)
from retry.schema493 import (POST,PRE,PHASES,clock,digest,read_ref,adapt_hold,
                             complete493,compare493)

TICK_BYTES495=16*1024
BUNDLE_BYTES495=64*1024

def same(a,b):return encoded(a)==encoded(b)
def child_ref(ref,field):
    check(type(ref) is dict and {'path','sha256','pointer'}<=set(ref),'495_ref_shape')
    check(type(ref['pointer']) is str and (not ref['pointer'] or ref['pointer'].startswith('/')),'495_ref_pointer')
    return dict(path=ref['path'],sha256=ref['sha256'],pointer=ref['pointer']+'/'+field)


def _rebuild(payload,storage_ref,expected_binding):
    """Authenticate actual bundle/tick bytes, then rebuild all common fields."""
    check_binding(expected_binding)
    check(type(payload) is dict and payload.get('schema')=='HOLD_BUNDLE495_V1','495_bundle_schema')
    check(payload.get('binding')==expected_binding,'495_bundle_binding')
    owner=payload['owner'];hold=payload['hold_id'];kind=payload['kind']
    check(type(owner) is str and bool(owner) and integer(hold,1,2**53) and kind in ('native','model'),'495_bundle_owner_hold')
    posts=payload['posts'];force=payload['pre_force'];returned=payload['wrapper_return']
    check(type(posts) is list and 1<=len(posts)<=4,'495_posts_count')
    n=len(posts);tires=force['tires'];hulls=force['hulls']
    check(force['schema']=='PRE_FORCE495_V1' and force['owner']==owner and integer(force['hold_id'],1,2**53) and force['hold_id']==hold and force['binding']==expected_binding,'495_force_binding')
    check(type(tires) is list and len(tires)==4*n and type(hulls) is list and len(hulls)==n,'495_force_coverage')
    before=payload['ledger_before'];after=payload['ledger_after']
    check(type(before) is dict and type(after) is dict and integer(before['last_clock_tick'],0,2**53) and integer(after['last_clock_tick'],0,2**53),'495_ledger_clock_types')
    check(after['last_clock_tick']-before['last_clock_tick']==n,'495_ledger_clock_coverage')
    check(returned['schema']=='WRAPPER_RETURN495_V1' and returned['owner']==owner and integer(returned['hold_id'],1,2**53) and returned['hold_id']==hold and returned['binding']==expected_binding,'495_return_binding')
    check(all(type(returned[k]) is bool for k in ('terminal','terminated','truncated')),'495_return_terminal_types')
    check(returned['terminal']==(returned['terminated'] or returned['truncated']),'495_return_terminal_join')
    check(integer(returned['raw_clock'],0,2**53) and integer(returned['raw_ticks'],1,4) and returned['raw_ticks']==n and returned['raw_clock']==after['last_clock_tick'],'495_return_clock_coverage')
    check(n==4 or returned['terminal'],'495_partial_nonterminal')
    check(number(returned['time']) and clock(returned['time'])==after['last_clock_tick'] and returned['capture_stage']=='AFTER_WRAPPER_DAMAGE_UPDATE','495_return_microphase')
    check(number(returned['damage']) and returned['damage']>=0,'495_return_damage')
    nominal=returned['nominal_phase'];phase=returned['controller_phase']
    check(nominal in PHASES-{'DONE'} and phase in PHASES,'495_return_phase_types')
    check(phase==nominal or (returned['terminal'] and phase=='DONE'),'495_DONE_after_return_only')
    captures=payload['direct_captures']
    check(type(captures) is dict and set(captures)=={str(i) for i in range(1,n+1)},'495_capture_keys')
    direct={}
    for index,p in enumerate(posts,1):
        c=captures[str(index)];h=hulls[index-1];w=tires[4*(index-1):4*index]
        check(type(p['collision']) is bool and integer(p['wheel_road_contacts'],0,4),'495_post_flag_types')
        check(number(p['time']) and clock(p['time'])==before['last_clock_tick']+index,'495_post_clock')
        check(c['schema']=='DIRECT_RAW_POST493_V1' and c['capture_stage']==POST and c['owner']==owner and c['binding']==expected_binding,'495_direct_owner_binding_stage')
        check(integer(c['hold_id'],1,2**53) and c['hold_id']==hold and integer(c['raw_clock'],0,2**53) and c['raw_clock']==before['last_clock_tick']+index and number(c['time']) and c['time']==p['time'],'495_direct_clock_hold')
        check(type(c['collision_raw_event']) is bool and integer(c['wheel_road_contacts'],0,4) and number(c['damage']) and c['damage']>=0,'495_direct_value_types')
        check(c['post_digest']==digest(p) and c['collision_raw_event']==p['collision'] and c['wheel_road_contacts']==p['wheel_road_contacts'],'495_direct_post_join')
        check(c['controller_phase']==nominal and c['snapshot']['controller_memory']['C']['phase']==nominal,'495_direct_nominal_phase')
        snapshot=c['snapshot']
        check(same(snapshot['position'],p['position']) and same(snapshot['velocity'],p['velocity']) and same(snapshot['tracker_after'],p['tracker_after']),'495_direct_snapshot_join')
        check(number(snapshot['angle']) and number(snapshot['angular_velocity']),'495_direct_hull_numeric')
        tiles=snapshot['wheel_tiles']
        check(type(tiles) is list and len(tiles)==4 and all(type(t) is list and all(integer(j,0,2**31) for j in t) and t==sorted(set(t)) for t in tiles),'495_direct_wheel_tiles')
        check(sum(bool(t) for t in tiles)==c['wheel_road_contacts'],'495_direct_tile_contacts')
        if kind=='model':
            latch=c['begin_contact_latch_ids']
            check(type(latch) is list and all(integer(j,0,2**31) for j in latch) and latch==sorted(set(latch)),'495_model_contact_latch')
        else:check('begin_contact_latch_ids' not in c,'495_native_not_model_latch')
        stored=read_ref(c['observed_ref'])
        check(len(encoded(stored))<=TICK_BYTES495 and same(stored,{k:v for k,v in c.items() if k!='observed_ref'}),'495_tick_immutable_ref')
        check(integer(h['raw_tick'],1,4) and h['raw_tick']==index and number(h['time']) and clock(h['time'])==before['last_clock_tick']+index-1,'495_force_hull_clock')
        check(all(integer(t['raw_tick'],1,4) and integer(t['wheel'],0,3) and type(t['grass']) is bool for t in w),'495_force_tire_types')
        check([(t['raw_tick'],t['wheel']) for t in w]==[(index,j) for j in range(4)],'495_force_tire_order')
        direct[index]=copy.deepcopy(c)
    # All pre-force samples and returned metadata have the SAME authenticated
    # bundle owner. No separate force/post/seal file or circular self-reference.
    common=adapt_hold(owner=owner,post_rows=posts,tires=tires,hulls=hulls,
        ledger_before=before,ledger_after=after,nominal_phase=nominal,
        hold_end_damage=returned['damage'],hold_end_time=returned['time'],
        provenance=child_ref(storage_ref,'posts'),direct_captures=direct,
        collision_kind='RAW_STEP_EVENT')
    complete493(common)
    return common


class Session495(Session494):
    def __init__(self,**kwargs):
        writer=kwargs['writer'];self.bundle_writer495=writer;self.pending_payload495=None
        def tick_writer(name,value):
            check(len(encoded(value))<=TICK_BYTES495,'495_tick_16KiB')
            return writer(name,value)
        super().__init__(**{**kwargs,'writer':tick_writer})
    def build_payload(self,*,tires,hulls,nominal_phase,ledger_after,terminal,terminated,truncated,wrapper_return_phase):
        self.require_owner()
        check(not self.active and not self.failed and not self.finished and self.pending_payload495 is None,'495_build_sequence')
        n=len(self.posts);check(1<=n<=4,'495_build_callbacks')
        check(all(type(v) is bool for v in (terminal,terminated,truncated)) and terminal==(terminated or truncated),'495_build_terminal')
        check(wrapper_return_phase==self.controller.phase(),'495_live_return_phase')
        after=asdict(ledger_after) if hasattr(ledger_after,'__dataclass_fields__') else copy.deepcopy(ledger_after)
        check(type(after) is dict and integer(after['last_clock_tick'],0,2**53) and after['last_clock_tick']==clock(self.raw.t),'495_live_return_ledger')
        returned=dict(schema='WRAPPER_RETURN495_V1',owner=self.owner,hold_id=self.hold,
            raw_clock=clock(self.raw.t),time=self.raw.t,capture_stage='AFTER_WRAPPER_DAMAGE_UPDATE',
            damage=self.damage.damage,controller_phase=wrapper_return_phase,nominal_phase=nominal_phase,
            raw_ticks=n,terminal=terminal,terminated=terminated,truncated=truncated,binding=copy.deepcopy(self.binding))
        payload=dict(schema='HOLD_BUNDLE495_V1',owner=self.owner,kind=self.kind,hold_id=self.hold,
            binding=copy.deepcopy(self.binding),ledger_before=copy.deepcopy(self.start),ledger_after=after,
            posts=copy.deepcopy(self.posts),pre_force=dict(schema='PRE_FORCE495_V1',owner=self.owner,hold_id=self.hold,
                tires=copy.deepcopy(tires),hulls=copy.deepcopy(hulls),binding=copy.deepcopy(self.binding)),
            wrapper_return=returned,direct_captures={str(k):copy.deepcopy(v) for k,v in self.captures.items()})
        check(len(encoded(payload))<=BUNDLE_BYTES495,'495_bundle_64KiB')
        self.pending_payload495=copy.deepcopy(payload)
        return payload
    def finalize_payload(self,payload,storage_ref):
        self.require_owner();check(not self.failed and not self.finished and self.pending_payload495 is not None,'495_finalize_sequence')
        check(same(payload,self.pending_payload495) and same(read_ref(storage_ref),payload),'495_bundle_immutable_ref')
        common=_rebuild(payload,storage_ref,self.binding)
        hold=dict(schema='CAPTURED_HOLD495_V1',bundle_ref=copy.deepcopy(storage_ref),common=common,
                  wrapper_return=copy.deepcopy(payload['wrapper_return']),binding=copy.deepcopy(self.binding),
                  kind=self.kind,synthetic_or_real_owner=self.kind)
        authenticate_hold495(hold,self.binding)
        self.pending_payload495=None;self.finished=True
        return hold
    def finish_hold(self,**kwargs):
        payload=self.build_payload(**kwargs)
        ref=self.bundle_writer495(f'{self.owner}-h{self.hold}-bundle.json',payload)
        return self.finalize_payload(payload,ref)


class Registry495(Registry494):
    def native(self,authority,*,owner,writer,binding):
        env=authority.env;ctrl=authority.ctrl;raw=env.unwrapped
        def owned():return authority.env is env and authority.ctrl is ctrl and authority._bound_env is env and authority._bound_ctrl is ctrl
        return self.add(Session495(owner=owner,kind='native',raw=raw,controller=ctrl,damage=env.damage,
            ledger=lambda:authority.ledger,owner_check=owned,writer=writer,binding=binding))
    def model(self,child,*,owner,writer,binding):
        model=child.m;ctrl=child.ctrl
        return self.add(Session495(owner=owner,kind='model',raw=model,controller=ctrl,damage=model.damage,
            ledger=lambda:child.ledger,owner_check=lambda:child.m is model and child.ctrl is ctrl,writer=writer,binding=binding))


def authenticate_hold495(hold,expected_binding):
    check_binding(expected_binding)
    check(type(hold) is dict and hold.get('schema')=='CAPTURED_HOLD495_V1' and hold.get('binding')==expected_binding,'495_hold_schema_binding')
    if 'sealed_hold_ref' in hold:
        check(same(read_ref(hold['sealed_hold_ref']),{k:v for k,v in hold.items() if k!='sealed_hold_ref'}),'495_optional_outer_seal')
    payload=read_ref(hold['bundle_ref'])
    check(len(encoded(payload))<=BUNDLE_BYTES495,'495_bundle_64KiB')
    rebuilt=_rebuild(payload,hold['bundle_ref'],expected_binding)
    check(same(hold['common'],rebuilt) and same(hold['wrapper_return'],payload['wrapper_return']) and hold['kind']==hold['synthetic_or_real_owner']==payload['kind'],'495_rebuilt_hold_join')
    return hold


def compare_repeat495(a,b,expected_binding):
    def measured(hold):
        authenticate_hold495(hold,expected_binding)
        p=copy.deepcopy(read_ref(hold['bundle_ref']))
        # These are exactly the owner labels and immutable receipt identities;
        # every original tire/hull field, ledger, latch and controller state stays.
        p.pop('owner');p['pre_force'].pop('owner');p['wrapper_return'].pop('owner')
        for c in p['direct_captures'].values():c.pop('owner');c.pop('observed_ref')
        return p
    check(same(measured(a),measured(b)),'495_repeat_all_measurements_exact')
    return dict(passed=True,all_measurement_fields_exact=True,full_tires_hulls_compared=True,
                each_provenance_authenticated=True,only_owner_and_receipt_identity_excluded=True)


def compare_flags495(a,b,expected_binding):
    authenticate_hold495(a,expected_binding);authenticate_hold495(b,expected_binding)
    result=compare493(a['common'],b['common'])
    safe=all(p['direct_tracker_capture']['damage']==0 and not p['direct_tracker_capture']['collision_raw_event'] and
        p['direct_tracker_capture']['wheel_road_contacts']==4 and not p['pre_force']['grass']
        for h in (a,b) for p in h['common']['rows']) and all(h['wrapper_return']['damage']==0 for h in (a,b))
    result.update(safe=safe,wrapper_return_damage_included=True,
                  scope='RAW_DISCRETE_FLAGS_ONLY_PHYSICAL_FIDELITY_AND_HISTORY_SEPARATE')
    return result


def install_model495(graph,registry,writer_factory,binding):
    """Attach to FULL cloned ObserveMixin lifecycle, after its original init/one."""
    check_binding(binding);module=graph.import_module('observer435')
    check(getattr(module,'__private_clone492__',False) is True and module.__name__.startswith('retry492.'),'495_original_observer_patch_forbidden')
    check(registry.installed is not None and registry.installed['model'] is module,'495_tap_must_be_installed_first')
    cls=module.ObserveMixin;check(not getattr(cls,'_capture495_installed',False),'495_observer_already_wrapped')
    original_init=cls.__init__;original_one=cls.one
    def ensure(self):
        if hasattr(self,'capture_session495'):
            check(hasattr(self,'capture_holds495'),'495_partial_registration')
            self.capture_session495.require_owner()
            return self.capture_session495
        check(not hasattr(self,'capture_holds495') and getattr(self,'stream',None) is not None,'495_registration_before_stream')
        self.capture_holds495=[]
        self.capture_session495=registry.model(self,owner=self.label,writer=writer_factory(self),binding=binding)
        return self.capture_session495
    @functools.wraps(original_init)
    def init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        ensure(self)
    @functools.wraps(original_one)
    def one(self,*args,**kwargs):
        # Shadow deliberately calls BaseGuardian.__init__ + Stream directly;
        # its full inherited one still registers here BEFORE any tap/integration.
        session=ensure(self);count=len(self.rows)
        try:
            result=original_one(self,*args,**kwargs)
            check(len(self.rows) in (count,count+1),'495_full_one_row_count')
            if len(self.rows)==count:
                check(not session.posts,'495_raw_without_observed_row')
                # An original pre-query stop is a zero-integration outcome, not
                # a fabricated hold and not permission to call this child again.
                session.failed=True;session.close_error='495_ORIGINAL_ZERO_RAW_OUTCOME'
                return result
            row=self.rows[-1];q=row['predicted']
            hold=session.finish_hold(tires=row['tires'],hulls=row['raw_hull'],
                nominal_phase=row['memory_after']['C']['phase'],ledger_after=self.ledger,
                terminal=q['terminal'],terminated=q['terminated'],truncated=q['truncated'],
                wrapper_return_phase=self.ctrl.phase())
            self.capture_holds495.append(hold)
            return result
        except BaseException as exc:
            session.failed=True;session.close_error=type(exc).__name__+': '+str(exc)
            raise
    cls.__init__=init;cls.one=one;cls._capture495_installed=True
    return dict(module=module,original_init=original_init,original_one=original_one,
                wrapped_init=init,wrapped_one=one,full_original_one_called_once=True)
