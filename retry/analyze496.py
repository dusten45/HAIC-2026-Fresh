"""Saved-only496 unique-context/candidate diagnostic. No physics imports."""
import time
START=time.perf_counter()
import copy,datetime,hashlib,importlib.abc,json,math,os,resource,sys
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');D=R/'stage496';M=Path('/tmp/haic-retry-stage495-qualified-private/model')
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('Box2D') or fullname in {'core.vendor.car_racing','core.vendor.car_dynamics','retry.terminal410_model','retry.source_vehicle_transition','retry.diagnose'}:raise RuntimeError('496_FORBIDDEN_PHYSICS_IMPORT:'+fullname)
        return None
sys.meta_path.insert(0,NoPhysics())
from retry.schema493 import receipt,digest
from retry.pilot420_json import json_ready
from retry.projection491 import canonical_projection
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(v,msg):
    if not v:raise RuntimeError('496_'+msg)
def save(p,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();check(len(data)<=2*1024**2,'FILE2MIB');check(not p.exists(),'OUTPUT_EXISTS')
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(p,0o600);check(p.read_bytes()==data,'READBACK')
def geo(line,pos,vel,angle):
    p=canonical_projection(line,pos,vel,'FIRST_LAP');j=p['index'];a=np.asarray(line[j]);edge=np.asarray(line[(j+1)%len(line)])-a;t=edge/np.linalg.norm(edge);normal=np.asarray([-t[1],t[0]])
    foot=a+p['u']*edge;v=np.asarray(vel);forward=np.asarray([-math.sin(angle),math.cos(angle)]);right=np.asarray([math.cos(angle),math.sin(angle)])
    return dict(error_m=p['path_error_m'],signed_error_m=float((np.asarray(pos)-foot)@normal),heading_deg=math.degrees(math.atan2(float(t[0]*forward[1]-t[1]*forward[0]),float(t@forward))),normal_velocity_m_s=float(v@normal),body_lateral_m_s=float(v@right),speed_m_s=float(np.linalg.norm(v)),sigma=p['sigma'],segment=j,u=p['u'])

def run():
    # Saved-data closeout is allowed after the experiment authorization ends.
    # This entrypoint never authorizes physics or an automatic extension.
    check(not D.exists(),'ONCE');D.mkdir(mode=0o700)
    pins={e['path']:e['sha256'] for e in receipt(R/'stage495-retention-final-private.json')['files']}
    for p in [R/'project-effective-budget-v495.json',R/'stage495-publication-private.json',G/'retry/diagnostic482_findings.json',G/'retry/diagnostic482_summary.json',G/'retry/diagnostic482_result.md',G/'retry/diagnostic483_result.json',G/'retry/diagnostic483_result.md']:pins[str(p)]=sha(p)
    sources={str(p):sha(p) for p in [Path(__file__),G/'retry/schema493.py',G/'retry/projection491.py']}
    save(D/'plan-private.json',dict(stage=496,mode='SAVED_ONLY',sources=sources,source_manifest_sha256=sha(R/'stage495-retention-final-private.json'),caps=dict(CPU_s=60,wall_s=90,outputs_bytes=8*1024**2,files=64,physics=0),dedup='Exact complete causal state, before/after nominal memory, ledger, RNG, nominal/qstar/current wheels plus frozen input/node digests. Arm/repetition/label/action number/receipt path are provenance, not independent samples.',metrics='Same root before-boundary;80ms maxguard includes allpre/post; preforce tires labelled separately; no cross-context/runs causal comparisons.',experiment_authorization_end_utc='2026-10-16T10:01:55Z',analysis_after_deadline_only=True,registered_before_metric_execution=True))
    accessed={}
    def load(path):
        path=Path(path);check(str(path) in pins,'UNPINNED:'+str(path));check(sha(path)==pins[str(path)],'PIN:'+str(path));accessed[str(path)]=pins[str(path)];return receipt(path)
    from retry.executor490_input import load as inputs
    inputpath=Path('/tmp/haic-retry-stage490-private/input-manifest-private.json');fixed,pace,nodes=inputs(inputpath);line=fixed['line'];ds=fixed['free_profile']['ds']
    query=load(M/'query-details-private.json');contexts={};groups={};nquery=0
    for path in sorted(M.glob('context-*-private.json')):
        ctx=load(path);contexts[(ctx['label'],ctx['index']+1)]=ctx
    for branch in query:
        for q in branch['queries']:
            nquery+=1;label='D495-A_'+branch['arm']+'_'+str(branch['repetition']);ctx=contexts[(label,q['local_query'])]
            keyfields={k:ctx[k] for k in ('state','before','after','ledger','RNG','nominal','qstar','wheels')}
            keyfields['frozen_input']=load(M/'result.json')['binding']
            key=digest(json_ready(keyfields));origin=dict(arm=branch['arm'],rep=branch['repetition'],local_query=q['local_query'],allocation_number=ctx['allocation_number'])
            if key in groups:
                g=groups[key];g['occurrences'].append(origin)
                # Candidate receipt paths differ; compare every saved measured
                # option field except those explicit provenance identities.
                signature={k:{f:v for f,v in opt.items() if f not in ('first_path','first_sha256')} for k,opt in q['options'].items()}
                check(g['option_signature']==digest(signature),'DEDUP_CANDIDATE_MEASUREMENTS')
                continue
            h=ctx['state']['physical']['hull'];pre=geo(line,h['position'],h['velocity'],h['angle']);j=pre['segment'];u=pre['u'];ref=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
            options=[]
            for k,opt in q['options'].items():
                trace=load(opt['first_path']);row=trace['rows'][0];check(sha(opt['first_path'])==opt['first_sha256'] and row['command']==opt['command'],'CANDIDATE_COMMAND_REF')
                pred=row['predicted'];post=geo(line,pred['position'],pred['velocity'],pred['angle'])
                errors=[geo(line,x['origin_position'],x['origin_linear_velocity'],x['angle'])['error_m'] for x in row['raw_hull']]+[post['error_m']]
                error=max(errors);check(abs(error-opt['max_guard_path_error_m'])<1e-10,'GUARD_METRIC')
                tires=row['tires'];ratio=max(t['force_ratio'] for t in tires);M80=max(0.,ratio-1);check(abs(M80-opt['M80'])<1e-12,'FORCE_METRIC')
                tire={}
                for name,ids in [('front',(0,1)),('rear',(2,3))]:
                    samples=[t for t in tires if t['wheel'] in ids]
                    tire[name]=dict(max_force_ratio=max(t['force_ratio'] for t in samples),max_abs_lat_N=max(abs(t['raw_lat_N']) for t in samples),max_abs_long_N=max(abs(t['raw_long_N']) for t in samples),max_abs_lat_slip_m_s=max(abs(t['lateral_slip_m_s']) for t in samples),clipped=sum(t['clipped'] for t in samples))
                options.append(dict(key=k,aliases=opt['aliases'],command=opt['command'],valid=opt['valid'],M80=M80,margin_m=3-error,guard_error_m=error,root_ceiling_m=3-pre['error_m'],post={k:v for k,v in post.items() if k not in ('segment','u')},tires=tire))
            eligible=[x for x in options if x['valid']]
            active=1 if ctx['nominal'][1]>0 else 2 if ctx['nominal'][2]>0 else None
            def rank(x,variant):
                tail=(x['M80'],-(0. if active is None else x['command'][active]))
                return (x['guard_error_m'],)+tail if variant else tail
            c=min(eligible,key=lambda x:rank(x,False));v=min(eligible,key=lambda x:rank(x,True))
            margins=[x['margin_m'] for x in eligible];pedals=[x['command'][active] for x in eligible] if active is not None else [0.]
            signature={k:{f:v for f,v in opt.items() if f not in ('first_path','first_sha256')} for k,opt in q['options'].items()}
            g=dict(context_digest=key,occurrences=[origin],option_signature=digest(signature),pre={k:v for k,v in pre.items() if k not in ('segment','u')},reference_m_s=ref,speed_excess_m_s=pre['speed_m_s']-ref,steer_increment_rad=ctx['nominal'][0]-ctx['before']['laststeer'],active_branch='gas' if active==1 else 'brake' if active==2 else 'none',nominal_qstar_same=ctx['nominal']==ctx['qstar'],options=options,rank_control=c['key'],rank_variant=v['key'],rank_disagreement=c['key']!=v['key'],same_context_rank_margin_gain_m=v['margin_m']-c['margin_m'],eligible_margin_spread_m=max(margins)-min(margins),eligible_active_pedal_span=max(pedals)-min(pedals),all_eligible_M80_zero=all(x['M80']==0 for x in eligible),root_ceiling_binds_all=all(abs(x['margin_m']-(3-pre['error_m']))<1e-12 for x in eligible))
            groups[key]=g
    values=list(groups.values());check(nquery==26,'26QUERIES')
    save(D/'unique-context-candidates-private.json',dict(stage=496,queries=nquery,unique_contexts=len(values),contexts=values))
    def ranges(seq):return [min(seq),max(seq)]
    result=dict(stage=496,mode='SAVED_ONLY',queries=26,unique_contexts=len(values),independent_DEV_conditions=1,new_conditions=0,occurrences=[len(g['occurrences']) for g in values],unique_rank_disagreements=sum(g['rank_disagreement'] for g in values),unique_candidate_traces=sum(len(g['options']) for g in values),all_unique_nominal_qstar_same=all(g['nominal_qstar_same'] for g in values),all_unique_eligible_M80_zero=all(g['all_eligible_M80_zero'] for g in values),root_ceiling_binds_all_count=sum(g['root_ceiling_binds_all'] for g in values),pre_speed_range_m_s=ranges([g['pre']['speed_m_s'] for g in values]),pre_speed_excess_range_m_s=ranges([g['speed_excess_m_s'] for g in values]),pre_abs_heading_range_deg=ranges([abs(g['pre']['heading_deg']) for g in values]),pre_abs_normal_velocity_range_m_s=ranges([abs(g['pre']['normal_velocity_m_s']) for g in values]),pedal_span_range=ranges([g['eligible_active_pedal_span'] for g in values]),margin_spread_range_m=ranges([g['eligible_margin_spread_m'] for g in values]),same_context_rank_gain_range_m=ranges([g['same_context_rank_margin_gain_m'] for g in values]),max_abs_steer_increment_rad=max(abs(g['steer_increment_rad']) for g in values),contexts_public=[dict(id='C'+str(i+1),occurrences=len(g['occurrences']),active_branch=g['active_branch'],pre_speed_m_s=g['pre']['speed_m_s'],speed_excess_m_s=g['speed_excess_m_s'],pre_error_m=g['pre']['error_m'],pre_heading_deg=g['pre']['heading_deg'],pre_normal_velocity_m_s=g['pre']['normal_velocity_m_s'],steer_increment_rad=g['steer_increment_rad'],pedal_span=g['eligible_active_pedal_span'],margin_spread_m=g['eligible_margin_spread_m'],rank_gain_m=g['same_context_rank_margin_gain_m'],root_ceiling_binds_all=g['root_ceiling_binds_all'],candidates=[{k:x[k] for k in ('aliases','valid','M80','margin_m','post','tires')} for x in g['options']]) for i,g in enumerate(values)],new_world_reset_step_seed_tuning=0,research_remaining=26027,reserve=84000,reserve_used=0,best_s=13.640,CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,no_auto_execution=True)
    for path,h in {**accessed,**sources}.items():check(sha(path)==h,'FINAL_IMMUTABLE')
    save(D/'result-private.json',result);save(D/'read-files-private.json',accessed)
    check(time.process_time()<60 and time.perf_counter()-START<90,'RESOURCE_CAP')
    print(json.dumps({k:result[k] for k in ('stage','unique_contexts','unique_rank_disagreements','all_unique_nominal_qstar_same','root_ceiling_binds_all_count','margin_spread_range_m','CPU_s','wall_s')}),flush=True)
if __name__=='__main__':run()
