"""Positive/negative synthetic contract fixtures; no physics dependencies."""
import copy
from retry.schema493 import *

def fixture(owner='native'):
    posts=[dict(time=(i+1)/50,position=[i,0.],velocity=[1.,0.],tracker_after={'x':i},collision=False,wheel_road_contacts=4) for i in range(4)]
    tires=[dict(raw_tick=i,wheel=j,grass=False) for i in range(1,5) for j in range(4)]
    hulls=[dict(raw_tick=i,time=(i-1)/50) for i in range(1,5)]
    ref=dict(path='synthetic-only',sha256='a'*64,pointer='/fixture')
    caps={i:dict(schema='DIRECT_RAW_POST493_V1',capture_stage=POST,owner=owner,raw_clock=i,time=posts[i-1]['time'],post_digest=digest(posts[i-1]),damage=0.,controller_phase='FIRST_LAP',collision_raw_event=False,wheel_road_contacts=4,observed_ref=ref) for i in range(1,5)}
    def synthetic_reader(ref):
        assert ref['path']=='synthetic-only'
        # Synthetic in-memory observer record, explicitly no real authority.
        capture=next(c for c in caps.values() if c['observed_ref'] is ref)
        return {k:v for k,v in capture.items() if k!='observed_ref'}
    for i,c in caps.items():c['observed_ref']=dict(path='synthetic-only',sha256='a'*64,pointer='/fixture/'+str(i))
    return dict(owner=owner,post_rows=posts,tires=tires,hulls=hulls,ledger_before={'last_clock_tick':0},ledger_after={'last_clock_tick':4},nominal_phase='FIRST_LAP',hold_end_damage=0.,hold_end_time=.08,provenance=ref,direct_captures=caps,collision_kind='RAW_STEP_EVENT',reference_reader=synthetic_reader)

def run():
    tests=[]
    def good(name,fn):fn();tests.append(name)
    def reject(name,fn):
        try:fn()
        except SchemaError493:tests.append(name);return
        raise AssertionError('MUST_REJECT:'+name)
    good('matching_native_model_direct_capture',lambda:compare493(adapt_hold(**fixture()),adapt_hold(**fixture('model'))))
    for field,value,label in [('capture_stage','AFTER_WRAPPER_DAMAGE_UPDATE','same_clock_wrong_microphase'),('owner','other','other_owner'),('raw_clock',2,'neighbor_tick'),('post_digest','0'*64,'different_post_body'),('controller_phase','LAUNCH','phase_mixed_before_nominal'),('wheel_road_contacts',3,'other_contacts')]:
        def f(field=field,value=value):
            x=fixture();x['direct_captures'][1][field]=value;adapt_hold(**x)
        reject(label,f)
    def missing():
        x=fixture();x['direct_captures']=None;complete493(adapt_hold(**x))
    reject('boundary_zero_damage_does_not_fill_missing_tick',missing)
    def partial():
        x=fixture();del x['direct_captures'][2];complete493(adapt_hold(**x))
    reject('one_missing_tick_rejects_whole_hold',partial)
    def forged_ref():
        x=fixture();x.pop('reference_reader');adapt_hold(**x)
    reject('synthetic_reference_cannot_authorize_real_adapter',forged_ref)
    def changed_ref():
        x=fixture();x['reference_reader']=lambda ref:{'not':'the recorded capture'};adapt_hold(**x)
    reject('capture_must_equal_its_observed_receipt',changed_ref)
    def grassclock():
        x=fixture();x['tires'][0]['raw_tick']=2;adapt_hold(**x)
    reject('grass_neighbor_tick_rejected',grassclock)
    def prepostclock():
        x=fixture();x['hulls'][0]['time']=.02;adapt_hold(**x)
    reject('pre_hull_cannot_be_post_clock',prepostclock)
    def badledger():
        x=fixture();x['ledger_after']['last_clock_tick']=3;adapt_hold(**x)
    reject('ledger_partial_coverage_rejected',badledger)
    def badcollision():
        x=fixture('model');x['direct_captures'][1]['collision_raw_event']=True;x['post_rows'][0]['collision']=True;x['direct_captures'][1]['post_digest']=digest(x['post_rows'][0]);compare493(adapt_hold(**fixture()),adapt_hold(**x))
    reject('actual_event_contact_disagreement_rejected',badcollision)
    def baddamage():
        x=fixture('model');x['direct_captures'][1]['damage']=.2;compare493(adapt_hold(**fixture()),adapt_hold(**x))
    reject('raw_damage_disagreement_rejected',baddamage)
    def badgrass():
        x=fixture('model');x['tires'][0]['grass']=True;compare493(adapt_hold(**fixture()),adapt_hold(**x))
    reject('pre_force_grass_disagreement_rejected',badgrass)
    def latch():
        x=fixture('model');x['collision_kind']='RAW_STEP_EVENT_OR_CONTACTS_LATCH';x['direct_captures']=None;complete493(adapt_hold(**x))
    reject('aggregate_contact_not_raw_event_authority',latch)
    def holdend():
        x=fixture('model');x['hold_end_damage']=.2;compare493(adapt_hold(**fixture()),adapt_hold(**x))
    reject('wrapper_end_damage_check_preserved',holdend)
    # Collision can increase damage only at wrapper return; direct raw samples
    # remain0 in both worlds. This positive fixture proves stages stay distinct.
    def collision_update():
        a=fixture();b=fixture('model')
        for x in (a,b):
            x['hold_end_damage']=.2
            x['post_rows'][3]['collision']=True
            x['direct_captures'][4].update(collision_raw_event=True,post_digest=digest(x['post_rows'][3]))
        compare493(adapt_hold(**a),adapt_hold(**b))
    good('collision_hold_raw_zero_and_wrapper_point2_separated',collision_update)
    return dict(passed=True,test_count=len(tests),tests=tests,worlds=0,steps=0,resets=0,synthetic_only=True)
