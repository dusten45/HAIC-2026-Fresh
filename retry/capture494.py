"""Opt-in direct tracker callback capture. No world/reset/step on import.

Install aliases only in an explicitly isolated graph. Existing437/435/492/493
files and original modules are unchanged. A future physics owner supplies its
quota writer and calls finish_hold after the original wrapper/child returns.
"""
import copy,hashlib,json,os,tempfile
from dataclasses import asdict
from pathlib import Path
from retry.pilot420_json import json_ready
from retry.schema493 import POST,PRE,PHASES,digest,clock,read_ref,adapt_hold,complete493,SchemaError493

class CaptureError494(SchemaError493):pass
def check(v,msg):
    if not v:raise CaptureError494(msg)
def integer(v,lo,hi):return type(v) is int and lo<=v<=hi
def number(v):
    import math
    return type(v) in (int,float) and math.isfinite(v)
def encoded(v):return (json.dumps(json_ready(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
BINDING_KEYS={'input_manifest_sha256','projection491_sha256','runtime492_sha256','line_sha256','nodes_sha256','capture494_sha256'}
def check_binding(value):
    check(type(value) is dict and set(value)==BINDING_KEYS,'binding_keys')
    check(all(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in value.values()),'binding_hash_types')

class ImmutableWriter494:
    """Finite private synthetic writer; future physics must inject its quota IO."""
    def __init__(self,root,max_files=128,max_bytes=8*1024**2):
        self.root=Path(root);check(not self.root.exists(),'writer_root_exists');self.root.mkdir(mode=0o700)
        self.max_files=max_files;self.max_bytes=max_bytes;self.files={}
    def __call__(self,name,value):
        check(Path(name).name==name and name.endswith('.json'),'receipt_name')
        p=self.root/name;data=encoded(value)
        check(not p.exists() and len(data)<=1024**2,'receipt_exists_or_oversize')
        check(len(self.files)<self.max_files and sum(self.files.values())+len(data)<=self.max_bytes,'receipt_quota')
        temp=None
        try:
            with tempfile.NamedTemporaryFile('wb',dir=self.root,delete=False) as f:
                temp=Path(f.name);os.chmod(temp,0o600);f.write(data);f.flush();os.fsync(f.fileno())
            os.link(temp,p)
            fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        finally:
            if temp is not None and temp.exists():temp.unlink()
        check(p.read_bytes()==data,'receipt_readback');self.files[str(p)]=len(data)
        return dict(path=str(p.resolve()),sha256=hashlib.sha256(data).hexdigest(),pointer='')

class Session494:
    def __init__(self,*,owner,kind,raw,controller,damage,ledger,owner_check,writer,binding):
        check(type(owner) is str and owner and type(kind) is str and kind in ('native','model'),'owner_kind')
        check(callable(ledger) and callable(owner_check) and callable(writer),'bound_accessors')
        self.owner=owner;self.kind=kind;self.raw=raw;self.controller=controller;self.damage=damage
        check_binding(binding)
        self.ledger=ledger;self.owner_check=owner_check;self.writer=writer;self.binding=copy.deepcopy(binding)
        self.tracker=raw.finish_line_tracker;self.hold=0;self.active=False;self.failed=False;self.finished=False
        self.posts=[];self.captures={};self.start=None;self.close_error=None
    def require_owner(self):
        check(self.owner_check() is True and self.raw.finish_line_tracker is self.tracker,'bound_owner_or_tracker_changed')
    def begin(self):
        self.require_owner();check(not self.active and not self.failed and (self.hold==0 or self.finished),'hold_sequence')
        value=self.ledger();value=asdict(value) if hasattr(value,'__dataclass_fields__') else copy.deepcopy(value)
        check(type(value) is dict and integer(value['last_clock_tick'],0,2**53),'ledger_type')
        check(clock(self.raw.t)==value['last_clock_tick'],'ledger_start_clock')
        self.hold+=1;self.start=value;self.posts=[];self.captures={};self.active=True;self.finished=False
    def observe(self,p):
        self.require_owner();check(self.active and not self.failed,'callback_without_active_hold')
        ordinal=len(self.posts)+1;check(ordinal<=4,'callback_cap4')
        check(number(p['time']) and p['time']==self.raw.t and clock(p['time'])==self.start['last_clock_tick']+ordinal,'callback_clock')
        check(p['tracker_after']==asdict(self.tracker),'callback_not_after_original_tracker')
        hull=self.raw.car.hull
        check(list(hull.position)==p['position'] and list(hull.linearVelocity)==p['velocity'],'callback_body_join')
        before=copy.deepcopy(self.controller.memory());phase=self.controller.phase()
        check(before==self.controller.memory() and phase in PHASES,'controller_accessor_not_readonly')
        check(before['C']['phase']==phase,'controller_memory_phase')
        check(type(self.raw._collision_this_step) is bool,'raw_collision_type')
        damage=self.damage.damage;check(number(damage) and damage>=0,'direct_damage_type')
        wheels=self.raw.car.wheels;check(len(wheels)==4,'four_wheels')
        tiles=[[t.idx for t in w.tiles] for w in wheels]
        check(all(integer(i,0,2**31) for wheel in tiles for i in wheel),'wheel_tile_index_type')
        normalized=json_ready(copy.deepcopy(p));normalized.update(collision=self.raw._collision_this_step,wheel_road_contacts=sum(bool(w.tiles) for w in wheels))
        capture=dict(schema='DIRECT_RAW_POST493_V1',capture_stage=POST,owner=self.owner,hold_id=self.hold,raw_clock=self.start['last_clock_tick']+ordinal,time=p['time'],post_digest=digest(normalized),damage=damage,controller_phase=phase,collision_raw_event=self.raw._collision_this_step,wheel_road_contacts=normalized['wheel_road_contacts'],
            snapshot=dict(position=list(hull.position),velocity=list(hull.linearVelocity),angle=float(hull.angle),angular_velocity=float(hull.angularVelocity),wheel_tiles=[sorted(x) for x in tiles],tracker_after=copy.deepcopy(p['tracker_after']),controller_memory=before),
            binding=copy.deepcopy(self.binding))
        if self.kind=='model':
            # BeginContact IDs accumulated since model hold start. They are
            # deliberately named latch, never current touch or raw tick event.
            check(type(self.raw.contacts) is set,'model_contact_latch_type')
            check(all(integer(i,0,2**31) for i in self.raw.contacts),'model_contact_latch_id_type')
            capture['begin_contact_latch_ids']=sorted(self.raw.contacts)
        capture=json_ready(capture)
        # Publish the immutable capture BEFORE giving mutable legacy observers
        # a different copy. The ref lives outside the hashed capture itself.
        ref=self.writer(f'{self.owner}-h{self.hold}-t{ordinal}.json',capture)
        check(read_ref(ref)==capture,'immutable_capture_roundtrip')
        self.posts.append(normalized);self.captures[ordinal]=dict(**capture,observed_ref=ref)
    def close_tap(self,exc):
        self.active=False
        if exc is not None:self.failed=True;self.close_error=type(exc).__name__+': '+str(exc)
    def finish_hold(self,*,tires,hulls,nominal_phase,ledger_after,terminal,terminated,truncated,wrapper_return_phase):
        self.require_owner();check(not self.active and not self.failed and not self.finished,'finish_sequence')
        n=len(self.posts);check(1<=n<=4,'callback_count')
        check(all(type(x) is bool for x in (terminal,terminated,truncated)),'terminal_types')
        check(n==4 or terminal or terminated or truncated,'nonterminal_partial_hold')
        check(wrapper_return_phase==self.controller.phase() and wrapper_return_phase in PHASES,'return_phase')
        check(nominal_phase in PHASES and all(c['controller_phase']==nominal_phase for c in self.captures.values()),'nominal_phase_not_direct_phase')
        check(wrapper_return_phase==nominal_phase or (terminal and wrapper_return_phase=='DONE'),'return_phase_change')
        ledger_after=asdict(ledger_after) if hasattr(ledger_after,'__dataclass_fields__') else ledger_after
        end=clock(self.raw.t);check(integer(ledger_after['last_clock_tick'],0,2**53) and ledger_after['last_clock_tick']==end,'return_ledger_clock')
        # Strict494 validation precedes493 where Python bool/int compare equal.
        check(integer(self.start['last_clock_tick'],0,2**53) and end-self.start['last_clock_tick']==n,'return_tick_count')
        for i,p in enumerate(self.posts,1):
            c=self.captures[i];check(integer(c['raw_clock'],0,2**53) and integer(c['wheel_road_contacts'],0,4),'capture_integer_types')
            check(integer(p['wheel_road_contacts'],0,4),'post_contact_type')
        for h in hulls:check(integer(h['raw_tick'],1,4),'hull_raw_tick_type')
        for t in tires:check(integer(t['raw_tick'],1,4) and integer(t['wheel'],0,3) and type(t['grass']) is bool,'tire_index_type')
        force_ref=self.writer(f'{self.owner}-h{self.hold}-pre-force.json',dict(schema='PRE_FORCE494_V1',owner=self.owner,hold_id=self.hold,tires=copy.deepcopy(tires),hulls=copy.deepcopy(hulls),binding=copy.deepcopy(self.binding)))
        posts_ref=self.writer(f'{self.owner}-h{self.hold}-posts.json',dict(schema='IMMUTABLE_POSTS494_V1',owner=self.owner,posts=copy.deepcopy(self.posts),binding=copy.deepcopy(self.binding)))
        common=adapt_hold(owner=self.owner,post_rows=self.posts,tires=tires,hulls=hulls,ledger_before=self.start,ledger_after=ledger_after,nominal_phase=nominal_phase,hold_end_damage=self.damage.damage,hold_end_time=self.raw.t,provenance={**posts_ref,'pointer':'/posts'},direct_captures=self.captures,collision_kind='RAW_STEP_EVENT')
        complete493(common)
        returned=dict(schema='WRAPPER_RETURN494_V1',owner=self.owner,hold_id=self.hold,raw_clock=end,time=self.raw.t,capture_stage='AFTER_WRAPPER_DAMAGE_UPDATE',damage=self.damage.damage,controller_phase=wrapper_return_phase,nominal_phase=nominal_phase,raw_ticks=n,terminal=terminal,terminated=terminated,truncated=truncated,binding=copy.deepcopy(self.binding))
        return_ref=self.writer(f'{self.owner}-h{self.hold}-return.json',returned)
        check(read_ref(return_ref)==returned,'wrapper_return_roundtrip')
        self.finished=True
        result=dict(schema='CAPTURED_HOLD494_V1',common=common,wrapper_return=returned,wrapper_return_ref=return_ref,pre_force_ref=force_ref,binding=copy.deepcopy(self.binding),synthetic_or_real_owner=self.kind)
        seal=self.writer(f'{self.owner}-h{self.hold}-sealed.json',result)
        return dict(**result,sealed_hold_ref=seal)

class Registry494:
    def __init__(self):self.sessions=[];self.installed=None
    def native(self,authority,*,owner,writer,binding):
        env=authority.env;ctrl=authority.ctrl;raw=env.unwrapped
        def owned():return authority.env is env and authority.ctrl is ctrl and authority._bound_env is env and authority._bound_ctrl is ctrl
        return self.add(Session494(owner=owner,kind='native',raw=raw,controller=ctrl,damage=env.damage,ledger=lambda:authority.ledger,owner_check=owned,writer=writer,binding=binding))
    def model(self,child,*,owner,writer,binding):
        model=child.m;ctrl=child.ctrl
        return self.add(Session494(owner=owner,kind='model',raw=model,controller=ctrl,damage=model.damage,ledger=lambda:child.ledger,owner_check=lambda:child.m is model and child.ctrl is ctrl,writer=writer,binding=binding))
    def add(self,s):
        check(all(x.tracker is not s.tracker for x in self.sessions),'duplicate_tracker_owner');self.sessions.append(s);return s
    def install(self,graph):
        check(self.installed is None,'registry_already_installed')
        capture=graph.import_module('capture434');native=graph.import_module('actual437_boundary');model=graph.import_module('observer435')
        for m in (capture,native,model):check(getattr(m,'__private_clone492__',False) is True and m.__name__.startswith('retry492.'),'original_graph_patch_forbidden')
        base=capture.PostTrackerTap;registry=self
        class BoundTap494:
            def __init__(self,tracker,callback):
                matches=[s for s in registry.sessions if s.tracker is tracker]
                check(len(matches)==1,'unregistered_tracker');self.session=matches[0];self.callback=callback
                def observed(p):
                    self.session.observe(copy.deepcopy(p));callback(copy.deepcopy(p))
                self.tap=base(tracker,observed)
            def __enter__(self):
                self.session.begin()
                try:return self.tap.__enter__()
                except BaseException as exc:self.session.close_tap(exc);raise
            def __exit__(self,*args):
                try:result=self.tap.__exit__(*args)
                except BaseException as exc:self.session.close_tap(exc);raise
                self.session.close_tap(args[1]);return result
        # Keep capture434.PostTrackerTap global intact: its own __enter__ reads
        # that class's _active. Only actual/model callsite aliases opt in.
        check(native.PostTrackerTap is base and model.PostTrackerTap is base,'tap_alias_drift')
        native.PostTrackerTap=BoundTap494;model.PostTrackerTap=BoundTap494
        self.installed=dict(native=native,model=model,base=base,tap=BoundTap494)
        return self.installed

def authenticate_hold494(hold,expected_binding):
    check_binding(expected_binding);check(hold['binding']==expected_binding,'external_binding')
    check(read_ref(hold['sealed_hold_ref'])=={k:v for k,v in hold.items() if k!='sealed_hold_ref'},'sealed_hold_roundtrip')
    check(hold['schema']=='CAPTURED_HOLD494_V1','hold_schema');common=complete493(hold['common'])
    force=read_ref(hold['pre_force_ref']);r=hold['wrapper_return']
    check(force['schema']=='PRE_FORCE494_V1' and force['owner']==common['owner'] and force['hold_id']==r['hold_id'] and force['binding']==expected_binding,'force_owner_hold_binding')
    check(len(force['tires'])==4*len(common['rows']) and len(force['hulls'])==len(common['rows']),'force_full_coverage')
    for index,p in enumerate(common['rows']):
        c=p['direct_tracker_capture'];check(integer(c['raw_clock'],0,2**53) and integer(c['wheel_road_contacts'],0,4),'auth_integer_types')
        check(integer(p['raw_clock'],0,2**53) and integer(p['pre_force']['raw_clock'],0,2**53) and integer(p['wrapper_end']['raw_clock'],0,2**53),'auth_common_integer_types')
        check(integer(p['tracker_post']['wheel_road_contacts'],0,4) and p['raw_clock']==c['raw_clock']==clock(c['time']) and number(p['time']) and p['time']==c['time'],'auth_common_clock_contacts')
        check(p['owner']==c['owner']==common['owner'] and c['capture_stage']==POST and p['tracker_post']['capture_stage']==POST and p['pre_force']['capture_stage']==PRE,'auth_owner_microphase')
        check(c['binding']==r['binding']==expected_binding and integer(c['hold_id'],1,2**53) and c['hold_id']==r['hold_id'],'auth_capture_binding_hold')
        check(p['pre_force']['raw_clock']+1==c['raw_clock'] and type(p['pre_force']['grass']) is bool and all(type(v) is bool for v in p['pre_force']['wheel_grass']),'auth_force_clock_grass')
        check(len(p['pre_force']['wheel_grass'])==4 and p['pre_force']['grass']==any(p['pre_force']['wheel_grass']),'auth_wheel_grass_aggregate')
        h=force['hulls'][index];w=force['tires'][4*index:4*(index+1)]
        check(integer(h['raw_tick'],1,4) and h['raw_tick']==index+1 and number(h['time']) and clock(h['time'])==p['pre_force']['raw_clock'],'auth_force_hull_clock')
        check(all(integer(t['raw_tick'],1,4) and integer(t['wheel'],0,3) and type(t['grass']) is bool for t in w) and [(t['raw_tick'],t['wheel']) for t in w]==[(index+1,j) for j in range(4)],'auth_force_wheel_join')
        check([t['grass'] for t in w]==p['pre_force']['wheel_grass'],'auth_force_grass_ref')
        check(type(c['collision_raw_event']) is bool and number(c['damage']) and c['controller_phase'] in PHASES,'auth_value_types')
        check(read_ref(c['observed_ref'])=={k:v for k,v in c.items() if k!='observed_ref'},'auth_capture_ref')
        ref=dict(p['provenance']);posts=read_ref(ref);ordinal=c['raw_clock']-common['rows'][0]['raw_clock']
        check(integer(ordinal,0,3) and ordinal==index and len(posts)==len(common['rows']) and digest(posts[ordinal])==c['post_digest'],'auth_immutable_post_ref')
        saved=posts[ordinal]
        expected=dict(capture_stage=POST,position=saved['position'],velocity=saved['velocity'],tracker_after=saved['tracker_after'],collision=saved['collision'],collision_semantics='RAW_STEP_EVENT',wheel_road_contacts=saved['wheel_road_contacts'])
        check(p['tracker_post']==expected and saved['collision']==c['collision_raw_event'] and saved['wheel_road_contacts']==c['wheel_road_contacts'],'auth_common_post_join')
        check(c['snapshot']['position']==saved['position'] and c['snapshot']['velocity']==saved['velocity'] and c['snapshot']['tracker_after']==saved['tracker_after'],'auth_direct_snapshot_join')
        check(c['snapshot']['controller_memory']['C']['phase']==c['controller_phase']==p['nominal']['controller_phase'] and p['nominal']['capture_stage']=='AFTER_NOMINAL_BEFORE_HOLD','auth_phase_join')
    r=hold['wrapper_return'];check(read_ref(hold['wrapper_return_ref'])==r,'auth_return_ref')
    check(integer(r['raw_clock'],0,2**53) and integer(r['raw_ticks'],1,4) and type(r['terminal']) is bool,'auth_return_types')
    check(type(r['terminated']) is bool and type(r['truncated']) is bool and r['terminal']==(r['terminated'] or r['truncated']),'auth_terminal_types')
    check(r['raw_ticks']==4 or r['terminal'],'auth_partial_terminal')
    check(r['owner']==common['owner'] and r['capture_stage']=='AFTER_WRAPPER_DAMAGE_UPDATE' and number(r['time']) and clock(r['time'])==r['raw_clock'],'auth_return_owner_stage')
    check(r['raw_ticks']==len(common['rows']) and r['raw_clock']==common['rows'][-1]['raw_clock'],'auth_return_coverage')
    check(r['nominal_phase'] in PHASES and r['controller_phase'] in PHASES and all(p['nominal']['controller_phase']==r['nominal_phase'] for p in common['rows']),'auth_return_nominal_phase')
    check(r['controller_phase']==r['nominal_phase'] or (r['terminal'] and r['controller_phase']=='DONE'),'auth_done_only_after_terminal_return')
    check(number(r['damage']) and all(p['wrapper_end']['damage']==r['damage'] and p['wrapper_end']['raw_clock']==r['raw_clock'] for p in common['rows']),'auth_wrapper_damage')
    return hold

def compare_repeat494(a,b,expected_binding):
    authenticate_hold494(a,expected_binding);authenticate_hold494(b,expected_binding)
    def measured(x):
        rows=[]
        for p in x['common']['rows']:
            c=copy.deepcopy(p['direct_tracker_capture']);c.pop('owner');c.pop('observed_ref')
            rows.append(dict(capture=c,pre_force=p['pre_force'],tracker_post=p['tracker_post'],nominal=p['nominal'],wrapper_end=p['wrapper_end']))
        r=copy.deepcopy(x['wrapper_return']);r.pop('owner')
        force=copy.deepcopy(read_ref(x['pre_force_ref']));force.pop('owner')
        return dict(rows=rows,wrapper_return=r,pre_force_samples=force)
    check(measured(a)==measured(b),'repeat_measurement_mismatch')
    return dict(passed=True,each_provenance_authenticated=True,all_measurement_fields_exact=True,only_owner_and_receipt_identity_excluded=True)

def compare_flags494(a,b,expected_binding):
    from retry.schema493 import compare493
    authenticate_hold494(a,expected_binding);authenticate_hold494(b,expected_binding)
    result=compare493(a['common'],b['common'])
    # Keep wrapper-return damage in safety independently of raw-post damage.
    safe=all(c['direct_tracker_capture']['damage']==0 and not c['direct_tracker_capture']['collision_raw_event'] and c['direct_tracker_capture']['wheel_road_contacts']==4 and not c['pre_force']['grass'] for h in (a,b) for c in h['common']['rows']) and all(h['wrapper_return']['damage']==0 for h in (a,b))
    result.update(safe=safe,wrapper_return_damage_included=True,scope='RAW_DISCRETE_FLAGS_ONLY_PHYSICAL_FIDELITY_AND_HISTORY_SEPARATE')
    return result
