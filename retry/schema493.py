"""Pure stage-aware raw schema adapter. Missing evidence is never a value.

Only directly captured tick facts can satisfy required tracker-post fields.
Pre-force grass and nominal-phase/hold-end damage remain separate evidence.
"""
import copy,hashlib,json,math
from pathlib import Path

POST='AFTER_TRACKER_BEFORE_WRAPPER_DAMAGE_UPDATE'
PRE='CAR_FORCE_PRE_WORLD'
PHASES={'LAUNCH','FIRST_LAP','FINISH_CONFIRM','DONE'}
class SchemaError493(ValueError):pass
class MissingEvidence493(SchemaError493):pass

def require(value,reason):
    if not value:raise SchemaError493(reason)
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(v):return type(v) in (int,float) and math.isfinite(v)
def clock(t):
    require(finite(t),'time_not_finite');n=round(t*50)
    require(abs(t-n/50)<1e-8,'time_not_raw_tick');return n

def receipt(path):
    """Read complete481 codec/bytes receipts without importing a physics graph."""
    from retry.pilot420_json import json_ready,restore_bytes
    path=Path(path);data=json.loads(path.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(SchemaError493('nonfinite_json')))
    def canonical(v):return digest(json_ready(v))
    def expand(v):
        if isinstance(v,dict):
            if set(v)=={'__haic_full_state_ref481__'}:
                h=v['__haic_full_state_ref481__'];require(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'bad_state_ref')
                state=json.loads((path.parent/('state-'+h+'.json')).read_text())
                require(set(state)=={'full_state','sha256'} and state['sha256']==h and canonical(state['full_state'])==h,'state_digest')
                return state['full_state']
            return {k:expand(x) for k,x in v.items()}
        if isinstance(v,list):return [expand(x) for x in v]
        return v
    if isinstance(data,dict) and '__haic_lossless481__' in data:
        require(set(data)=={'__haic_lossless481__','payload','decoded_sha256'} and data['__haic_lossless481__']==1,'codec_schema')
        out=restore_bytes(expand(data['payload']));require(canonical(out)==data['decoded_sha256'],'decoded_digest');return out
    return restore_bytes(data)

def source_ref(path,pointer):
    p=Path(path);require(p.is_file(),'source_not_file')
    return dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pointer=pointer)

def read_ref(ref):
    p=Path(ref['path']);require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'],'direct_receipt_hash')
    pointer=ref['pointer'];require(isinstance(pointer,str) and (not pointer or pointer.startswith('/')),'direct_receipt_pointer')
    value=receipt(p)
    for token in pointer.split('/')[1:]:
        token=token.replace('~1','/').replace('~0','~')
        value=value[int(token)] if isinstance(value,list) else value[token]
    return value

def adapt_hold(*,owner,post_rows,tires,hulls,ledger_before,ledger_after,nominal_phase,hold_end_damage,hold_end_time,provenance,direct_captures=None,collision_kind,reference_reader=read_ref):
    """Return partial stage-aware facts. complete493() is a separate hard gate.

    direct_captures, if present, must be fresh observed post records bound to
    each raw post's exact body/tracker digest, owner, tick AND microphase.
    Existing492 input supplies None; no boundary fact is cast into this shape.
    """
    require(type(owner) is str and owner,'owner')
    n=len(post_rows);require(1<=n<=4 and len(tires)==4*n and len(hulls)==n,'coverage')
    start=ledger_before['last_clock_tick'];end=ledger_after['last_clock_tick']
    require(type(start) is int and type(end) is int and end-start==n,'ledger_clock_coverage')
    require(nominal_phase in PHASES and finite(hold_end_damage) and hold_end_damage>=0,'boundary_fields')
    require(clock(hold_end_time)==end,'hold_end_clock')
    require(collision_kind in {'RAW_STEP_EVENT','RAW_STEP_EVENT_OR_CONTACTS_LATCH'},'collision_semantics')
    require(type(provenance) is dict and {'path','sha256','pointer'}<=set(provenance),'provenance')
    captures={} if direct_captures is None else direct_captures
    require(type(captures) is dict and set(captures)<=set(range(1,n+1)),'capture_tick_keys')
    out=[]
    for i,p in enumerate(post_rows,1):
        require(clock(p['time'])==start+i,'post_clock')
        h=hulls[i-1];require(h['raw_tick']==i and clock(h['time'])==start+i-1 and abs(p['time']-h['time']-.02)<1e-8,'pre_post_clock_join')
        w=tires[4*(i-1):4*i]
        require([(z['raw_tick'],z['wheel']) for z in w]==[(i,j) for j in range(4)],'tire_tick_wheel_join')
        require(all(type(z['grass']) is bool for z in w),'grass_type')
        require(type(p['collision']) is bool and type(p['wheel_road_contacts']) is int and 0<=p['wheel_road_contacts']<=4,'post_flag_types')
        missing=['damage_at_tracker_post','controller_phase_at_tracker_post','collision_raw_event']
        direct={}
        if i in captures:
            c=captures[i]
            require(c['schema']=='DIRECT_RAW_POST493_V1' and c['capture_stage']==POST,'capture_microphase')
            require(c['owner']==owner and c['raw_clock']==start+i and c['time']==p['time'],'capture_owner_clock')
            require(c['post_digest']==digest(p),'capture_post_digest')
            require(type(c['collision_raw_event']) is bool and finite(c['damage']) and c['damage']>=0 and c['controller_phase'] in PHASES,'capture_values')
            require(c['wheel_road_contacts']==p['wheel_road_contacts'],'capture_contacts')
            if collision_kind=='RAW_STEP_EVENT':require(c['collision_raw_event']==p['collision'],'capture_collision')
            else:require(not c['collision_raw_event'] or p['collision'],'capture_collision_latch')
            require(c['controller_phase']==nominal_phase,'capture_phase_drift')
            require(type(c['observed_ref']) is dict and {'path','sha256','pointer'}<=set(c['observed_ref']),'capture_direct_provenance')
            recorded={k:v for k,v in c.items() if k!='observed_ref'}
            require(reference_reader(c['observed_ref'])==recorded,'direct_record_not_observed_receipt')
            direct=copy.deepcopy(c);missing=[]
        elif collision_kind=='RAW_STEP_EVENT':missing.remove('collision_raw_event')
        out.append(dict(raw_clock=start+i,time=p['time'],owner=owner,
            tracker_post=dict(capture_stage=POST,position=copy.deepcopy(p['position']),velocity=copy.deepcopy(p['velocity']),tracker_after=copy.deepcopy(p['tracker_after']),collision=p['collision'],collision_semantics=collision_kind,wheel_road_contacts=p['wheel_road_contacts']),
            pre_force=dict(capture_stage=PRE,raw_clock=start+i-1,grass=any(z['grass'] for z in w),wheel_grass=[z['grass'] for z in w]),
            nominal=dict(capture_stage='AFTER_NOMINAL_BEFORE_HOLD',controller_phase=nominal_phase),
            wrapper_end=dict(capture_stage='AFTER_WRAPPER_DAMAGE_UPDATE',raw_clock=end,time=hold_end_time,damage=hold_end_damage),
            direct_tracker_capture=direct,missing=missing,provenance=copy.deepcopy(provenance)))
    return dict(schema='COMMON_RAW493_V1',owner=owner,rows=out,complete=all(not p['missing'] for p in out),missing_count=sum(len(p['missing']) for p in out),checks_deleted=False,defaults_filled=False)

def complete493(value):
    require(value['schema']=='COMMON_RAW493_V1','common_schema')
    missing=[dict(raw_clock=p['raw_clock'],fields=p['missing']) for p in value['rows'] if p['missing']]
    if missing:raise MissingEvidence493(json.dumps(missing,sort_keys=True))
    require(value['complete'] is True,'complete_marker');return value

def compare493(native,model):
    complete493(native);complete493(model)
    require(len(native['rows'])==len(model['rows']),'comparison_count')
    for a,b in zip(native['rows'],model['rows']):
        require(a['raw_clock']==b['raw_clock'] and abs(a['time']-b['time'])<1e-8,'comparison_clock')
        x=a['direct_tracker_capture'];y=b['direct_tracker_capture']
        for name in ('damage','controller_phase','collision_raw_event','wheel_road_contacts'):
            require(type(x[name]) is type(y[name]) and x[name]==y[name],'comparison_'+name)
        require(a['pre_force']['grass']==b['pre_force']['grass'],'comparison_pre_force_grass')
        require(a['nominal']['controller_phase']==b['nominal']['controller_phase'],'comparison_nominal_phase')
        require(a['wrapper_end']['damage']==b['wrapper_end']['damage'],'comparison_wrapper_end_damage')
    return dict(passed=True,raw_ticks=len(native['rows']),damage_phase_direct=True,pre_force_grass_exact=True,raw_event_contact_exact=True,no_fields_deleted=True)
