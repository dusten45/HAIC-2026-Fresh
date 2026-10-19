"""Read605 logs only. No model/controller/geometry evaluator imports or calls."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import ast,collections,copy,datetime,hashlib,json,math,signal,struct
from pathlib import Path
G=Path(__file__).resolve().parents[1];P=Path('/workspace/haic-response605-private');D=Path('/workspace/haic-response606-private')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def bits_action(x):return struct.pack('<3f',*x).hex()
def action(bits):return struct.unpack('<3f',bytes.fromhex(bits))
def norm(x):return math.hypot(*x)
def difference(a,b):return [x-y for x,y in zip(a,b)]
def physical(root):
    q=copy.deepcopy(root);q['planar'].pop('steer',None);return q
def state_delta(a,b):
    pa=a['planar'];pb=b['planar'];wa=pa['linear']['wheels'];wb=pb['linear']['wheels']
    return dict(center_separation_m=norm(difference(a['center'],b['center'])),
        velocity_separation_m_s=norm(difference(pa['linear']['velocity'],pb['linear']['velocity'])),
        speed_delta_m_s=norm(pa['linear']['velocity'])-norm(pb['linear']['velocity']),
        angle_delta_rad=pa['angle']-pb['angle'],yaw_delta_rad_s=pa['yaw']-pb['yaw'],
        max_joint_delta_rad=max(abs(x-y) for x,y in zip(pa['joints'],pb['joints'])),
        wheel_heading_delta_rad=[x['heading']-y['heading'] for x,y in zip(wa,wb)],
        wheel_omega_delta_rad_s=[x['omega']-y['omega'] for x,y in zip(wa,wb)],
        wheel_gas_memory_delta=[x['gas']-y['gas'] for x,y in zip(wa,wb)],
        same_friction=[x['friction']==y['friction'] for x,y in zip(wa,wb)],
        same_contacts=a['current_contacts']==b['current_contacts'],
        physical_state_equal=digest(physical(a))==digest(physical(b)))
def saturations(a):
    limit=struct.unpack('<f',struct.pack('<f',.4))[0]
    return dict(steer_at_actuator_limit=abs(a[0])==limit,pedal_at_actuator_limit=a[1]==1. or a[2]==1.,
                both_actuator_limits=abs(a[0])==limit and (a[1]==1. or a[2]==1.))
def net(a):return a[1] if a[1]>0 else -a[2]


class Reader:
    def __init__(self):
        D.mkdir(mode=0o700,exist_ok=True)
        if (D/'CLOSED-private.json').exists():raise RuntimeError('606_ANALYSIS_ALREADY_CLOSED')
        self.result605=read(P/'as-executed-result-private.json');self.cache={};self.consumed={}
        self.pin={};self.cases={}
    def guard(self):
        if time.process_time()-CPU+5>=180 or time.perf_counter()-WALL+5>=300:raise RuntimeError('606_READ_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise RuntimeError('DEADLINE')
    def get(self,name):
        self.guard();p=P/name
        if name not in self.cache:
            h=sha(p);assert h==self.result605['private_sha256'][name],('605_PIN',name)
            self.pin[name]=h;self.cache[name]=read(p)
        return self.cache[name]
    def decode(self,label,h):
        key=(label,h)
        if key in self.consumed:return self.consumed[key]
        data=self.get(f'{label}-hold-{h:03d}-private.json');w=data['wheel_results'];at=0;frames=[];trials=[];trial=None;frame=None
        for e in data['events']:
            if e['kind']=='TRACKING_TRIAL_START':
                trial=dict(start=e,frames=[]);trials.append(trial)
            elif e['kind']=='BEFORE_MODEL_FORCE':
                pack=w[at:at+4];assert len(pack)==4 and all(q[0]=='external_force' for q in pack);at+=4
                frame=dict(before=e,external=[q[1] for q in pack],trial=trial)
                frames.append(frame)
                if trial is not None:trial['frames'].append(frame)
            elif e['kind']=='MODEL_FORCE_VERDICT':
                assert frame is not None and e['root_sha256']==frame['before']['root_sha256'];frame['verdict']=e
            elif e['kind']=='BEFORE_MODEL_TICK':
                pack=w[at:at+4];assert len(pack)==4 and all(q[0]=='internal_force' for q in pack);at+=4;frame['internal']=[q[1] for q in pack]
            elif e['kind']=='AFTER_MODEL_TICK':frame['after']=e
            elif e['kind']=='TRACKING_TRIAL_END':trial['end']=e;trial=None
        assert at==len(w),('UNCONSUMED_WHEEL_RESULT',label,h,at,len(w))
        self.consumed[key]=(data,frames,trials);return data,frames,trials
    def row_map(self,label):return {q['global_raw_before']+1:q for q in self.get(label+'-result-private.json')['rows']}
    def frame(self,label,row):
        _,frames,_=self.decode(label,row['index'])
        expected=digest(row['before_root_without_roads']);matches=[f for f in frames if f['before']['mode']=='applied' and f['before']['root_sha256']==expected and f['before']['action_bits']==bits_action(row['action'])]
        assert len(matches)==1
        f=matches[0]
        assert f['verdict']['ratios']==[x['ratio'] for x in row['forces']]
        assert all(digest(f['external'][i][1])==digest(row['forces'][i]['vector']) for i in range(4))
        return f
    def command(self,label,row):
        data,_,_=self.decode(label,row['index']);detail=data['detail'];a=action(detail['action_bits']);inc=action(detail['incumbent_bits'])
        assert bits_action(row['action'])==detail['action_bits']
        return dict(inc=inc,out=a,meta=detail['residual'],detail=detail)
    def wheels(self,crow,zrow,cframe,zframe):
        out=[]
        for i in range(4):
            cf=cframe['external'][i];zf=zframe['external'][i]
            cd=cf[2];zd=zf[2];mu=crow['before_root_without_roads']['planar']['linear']['wheels'][i]['friction'];zm=zrow['before_root_without_roads']['planar']['linear']['wheels'][i]['friction']
            x,y=cd['longitudinal_force'],cd['lateral_force'];den=x*x+y*y
            out.append(dict(wheel=i,axle='front' if i<2 else 'rear',
                zero_ratio=zrow['forces'][i]['ratio'],candidate_ratio=crow['forces'][i]['ratio'],
                ratio_delta=crow['forces'][i]['ratio']-zrow['forces'][i]['ratio'],
                zero_clipped=zd['clipped'],candidate_clipped=cd['clipped'],
                postclip_longitudinal_over_mu_delta=x/mu-zd['longitudinal_force']/zm,
                postclip_lateral_over_mu_delta=y/mu-zd['lateral_force']/zm,
                candidate_postclip_lateral_squared_share=y*y/den if den else 0.,
                omega_drive_delta=cd['omega_drive']-zd['omega_drive'],omega_braked_delta=cd['omega_braked']-zd['omega_braked'],
                returned_gas_delta=cf[0]['gas']-zf[0]['gas']))
        return out
    def case(self,label,rows,zero):
        row=rows[max(rows)];raw=row['global_raw_before']+1;zr=zero[raw]
        f=self.frame(label,row);zf=self.frame('zero',zr);cmd=self.command(label,row);zc=self.command('zero',zr)
        prev=rows.get(raw-1);previ=rows.get(4*(row['index']-1))
        prior_hold=self.get(f'{label}-hold-{row["index"]-1:03d}-private.json')['detail']
        zp=self.get(f'zero-hold-{row["index"]-1:03d}-private.json')['detail']
        pa=action(prior_hold['action_bits']);zpa=action(zp['action_bits'])
        history=[]
        for n in range(max(97,raw-5),raw+1):
            if n not in rows:continue
            a=rows[n];b=zero[n]
            history.append(dict(raw=n,force_ratio_peak=max(z['ratio'] for z in a['forces']),
                zero_force_peak=max(z['ratio'] for z in b['forces']),footprint=a.get('margin'),zero_footprint=b.get('margin'),
                state_delta=state_delta(a['before_root_without_roads'],b['before_root_without_roads']),
                applied_action_same_as_previous=(bits_action(a['action'])==bits_action(rows[n-1]['action'])) if n-1 in rows else None))
        details=[]
        for h in range(25,row['index']+1):
            dd=self.get(f'{label}-hold-{h:03d}-private.json')['detail']
            if dd:details.append((h,dd))
        changed=[4*(h-1)+1 for h,dd in details if dd['action_bits']!=dd['incumbent_bits']]
        changed_state=[n for n,q in rows.items() if q.get('tick_executed') and digest(physical(q['root_without_roads']))!=digest(physical(zero[n]['root_without_roads']))]
        heading_diff=[n for n,q in rows.items() if q.get('tick_executed') and any(x['heading']!=y['heading'] for x,y in zip(q['root_without_roads']['planar']['linear']['wheels'],zero[n]['root_without_roads']['planar']['linear']['wheels']))]
        before_state=state_delta(row['before_root_without_roads'],zr['before_root_without_roads'])
        out=dict(label=label,first_failure_raw=raw,kind=row['pre_failure'] or row['post_failure'],hold=row['index'],raw_in_hold=row['raw'],
            first_nonzero_applied_command_raw=min(changed) if changed else None,
            first_post_state_diff_raw=min(changed_state) if changed_state else None,first_post_heading_diff_raw=min(heading_diff) if heading_diff else None,
            base_command_same_as_zero=bits_action(cmd['inc'])==bits_action(zc['inc']),
            applied_vs_base_steer_delta=cmd['out'][0]-cmd['inc'][0],applied_vs_base_netpedal_delta=net(cmd['out'])-net(cmd['inc']),
            candidate_vs_zero_netpedal_delta=net(cmd['out'])-net(zc['out']),
            residual_target_offset_change_from_prior_hold=cmd['meta']['offset']-prior_hold['residual']['offset'],
            residual_pedal_change_from_prior_hold=cmd['meta']['pedal_residual']-prior_hold['residual']['pedal_residual'],
            candidate_hold_steer_step=cmd['out'][0]-pa[0],zero_hold_steer_step=zc['out'][0]-zpa[0],
            unchanged_command_from_immediately_previous_raw=prev is not None and bits_action(prev['action'])==bits_action(row['action']),
            candidate_saturation=saturations(cmd['out']),zero_saturation=saturations(zc['out']),
            current_state_delta=before_state,wheels=self.wheels(row,zr,f,zf),last_raws=history,
            match_scope='SAME_RAW_CLOCK_NOT_SAME_PHYSICAL_STATE',raw_unsaturated_longitudinal_lateral_not_logged=True)
        if row.get('post_failure'):
            out['footprint_context']=dict(candidate=row['margin'],zero=zr['margin'],candidate_path_error=row['path_error'],zero_path_error=zr['path_error'],
                reference_excess=row['reference_overspeed'],body_speed=row['body'],peak_force=max(q['ratio'] for q in row['forces']),
                clip_fraction=row['proposed_history'][0]/row['proposed_history'][1],component_label_missing=True)
        if row['index']>=40:
            data,frames,trials=self.decode(label,row['index'])
            if cmd['detail']['original_FINAL'] and cmd['detail']['original_FINAL'].get('final_recertified'):
                final=trials[-1];ff=final['frames'][0]
                same=digest(physical(ff['before']['root']))==digest(physical(row['before_root_without_roads']))
                out['stored_same_state_original_FINAL_first_raw']=dict(physical_state_equal_ignoring_steer_latch=same,
                    original_force_ratios=ff['verdict']['ratios'],modified_force_ratios=f['verdict']['ratios'],
                    same_base_command=ff['before']['action_bits']==cmd['detail']['incumbent_bits'],
                    original_trial_safe=final['end']['original']['ok'],original_FIRST4_recorded=len(final['frames'])>=4,
                    pedal_components_differ=cmd['out'][1:]!=cmd['inc'][1:],steer_diff=cmd['out'][0]-cmd['inc'][0])
                assert same and ff['before']['action_bits']==cmd['detail']['incumbent_bits']
                out['same_state_original_vs_modified_wheel_delta']=[dict(wheel=i,
                    postclip_long_delta=f['external'][i][2]['longitudinal_force']-ff['external'][i][2]['longitudinal_force'],
                    postclip_lat_delta=f['external'][i][2]['lateral_force']-ff['external'][i][2]['lateral_force'],
                    omega_braked_delta=f['external'][i][2]['omega_braked']-ff['external'][i][2]['omega_braked']) for i in range(4)]
        self.cases[label]=out
    def run(self):
        deadline='2026-10-20T10:01:55Z'
        files=[G/'retry/residual605_result.json',G/'retry/residual605_audit.json',G/'retry/residual605_contract.json',
               G/'retry/speed516_control.py',G/'retry/brake502_response.py',G/'retry/brake504_planar.py',G/'retry/structure537_control.py',G/'retry/residual604_math.py']
        contract=dict(study=606,status='FROZEN_READ_ONLY_BEFORE_LOG_ANALYSIS',deadline_utc=deadline,
            cap_CPU_s=180,cap_wall_s=300,prior_charge_s=5,read_sha256={str(p.relative_to(G)):sha(p) for p in files},
            reader_sha256=sha(Path(__file__)),new_model_tick=0,new_chooser=0,new_force=0,new_geometry_evaluator=0,native=0,
            method='Stored same-clock rows and primitive wheel results only; chronological mapping external/internal results validated. Norm/delta/ratio arithmetic on stored values; no trig, slip/force law re-evaluation or counterfactual rollout. Same-state FINAL first-raw witness if already recorded.',
            privacy='Only aggregate differences/ratios/saturationflags/reasons public. Raw state/coordinates/base/applied command bytes and private input packet stay outsideGit.',research_remaining=22211,reserve=84000,reserve_used=0)
        (G/'retry/forensic606_contract.json').write_text(json.dumps(contract,indent=2)+'\n')
        zero=self.row_map('zero')
        for label in ['H0','H1','H2','H3','H4','H5','H7']:self.case(label,self.row_map(label),zero)
        h6rows=self.row_map('H6');last=h6rows[max(h6rows)];_,frames,trials=self.decode('H6',40)
        trial_info=[]
        for t in trials:
            report=t['end']['original'];sf=t['frames'][0]
            trial_info.append(dict(reason=report['reason'],completed_raw=report['model_ticks'],first_hold_pass=report['first_hold_pass'],
                first_force_peak=max(sf['verdict']['ratios']),first_force_failed=sf['verdict']['pre_failure'] is not None,
                first_footprint_violation=report['first_footprint_violation']))
        assert len(trial_info)==20
        steering_count=len({action(t['start']['action_bits'])[0] for t in trials})
        self.cases['H6']=dict(label='H6',last_safe_applied_raw=156,next_unapplied_raw=157,
            state_delta=state_delta(last['root_without_roads'],zero[156]['root_without_roads']),
            current_safe_margin=last['margin'],zero_current_margin=zero[156]['margin'],current_path_error=last['path_error'],
            current_force_peak=max(x['ratio'] for x in last['forces']),
            original_trial_count=len(trial_info),distinct_first_action_steers=steering_count,
            trial_reasons=dict(collections.Counter(t['reason'] for t in trial_info)),
            trials_passing_first_hold=sum(t['first_hold_pass'] for t in trial_info),
            by_reason={reason:dict(count=sum(t['reason']==reason for t in trial_info),
                min_completed_raw=min(t['completed_raw'] for t in trial_info if t['reason']==reason),
                max_completed_raw=max(t['completed_raw'] for t in trial_info if t['reason']==reason),
                first_hold_pass=sum(t['first_hold_pass'] for t in trial_info if t['reason']==reason)) for reason in {t['reason'] for t in trial_info}},
            modified_action_applied_at_hold40=False,physical_future_failure_observed=False)
        (D/'H6-trial-depths-private.json').write_text(json.dumps(trial_info,indent=2)+'\n')
        # Private reusable evidence packet, not authorization to evaluate it.
        h1=self.get('H1-result-private.json');cp=h1['checkpoint'];assert cp['global_raw']==160
        packet=dict(scope='PROPOSED_LOCAL_SOURCE_TEST_ONLY_NOT_NATIVE_OR_PIXEL',checkpoint=cp,
                    stored_hold41_detail=self.get('H1-hold-041-private.json')['detail'],
                    source605_sha256=sha(P/'as-executed-result-private.json'))
        (D/'proposed-input-private.json').write_text(json.dumps(packet,indent=2)+'\n')
        for p in D.glob('*.json'):p.chmod(0o600)
        assert all(sha(P/name)==h for name,h in self.pin.items())
        result=dict(study=606,cases=self.cases,validated_hold_wheel_streams=len(self.consumed),input_log_sha256=self.pin,
            proposed_private_input_sha256=sha(D/'proposed-input-private.json'),
            limits=['Same-clock comparisons change state and command together; no steering-only/pedal-only interventions.',
                    'Current force_rows does not read action[0]/planar.steer; steering changes subsequent tick wheel headings/offsets.',
                    'Logged longitudinal/lateral forces are AFTER friction clipping; unsaturated components and slip velocities not recorded.',
                    'No PPtarget coordinates/normal or unclamped steering residual recorded; cannot attribute a target-segment discontinuity from logs.',
                    'Full footprint minimum lacks bodypart/boundary/obstacle contributor; no new geometry query allowed.'],
            new_model_tick=0,new_chooser=0,new_force=0,new_geometry_evaluator=0,native=0,
            time=dict(CPU_s=time.process_time()-CPU+5,wall_s=time.perf_counter()-WALL+5),
            research_remaining=22211,reserve=84000,reserve_used=0)
        self.guard();assert sha(Path(__file__))==contract['reader_sha256']
        (G/'retry/forensic606_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        (D/'CLOSED-private.json').write_text(json.dumps(dict(time=dict(CPU_s=time.process_time()-CPU+5,wall_s=time.perf_counter()-WALL+5),result_sha256=sha(G/'retry/forensic606_analysis.json')),indent=2)+'\n')
        print(json.dumps(dict(time=result['time'],cases=list(result['cases']),wheel_streams=len(self.consumed)),indent=2))


if __name__=='__main__':
    def stop(*a):raise RuntimeError('606_READ_TIMER')
    signal.signal(signal.SIGPROF,stop);signal.signal(signal.SIGALRM,stop)
    signal.setitimer(signal.ITIMER_PROF,175);signal.setitimer(signal.ITIMER_REAL,295)
    Reader().run()
