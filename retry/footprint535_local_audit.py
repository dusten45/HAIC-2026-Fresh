"""Read-only535 local intervention/steering/freshness audit; no integration."""
import hashlib,json,time
from pathlib import Path
from retry.plan513_model import load_root
from retry.lap518_control import steering
from retry.frozen534_projection import initial_progress
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response535-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());old=json.loads(Path('/workspace/haic-response534-private/cold-candidate-model-private.json').read_text());oldcommands={x['index']:x for x in old['commands']};oldrows={(x['index'],x['raw']):x for x in old['trace']};early=json.loads((D/'early-recovery-private.json').read_text());first=next(x for x in early['commands'] if x.get('action')!=oldcommands.get(x['index'],{}).get('action'));sameprefix=[x['root_without_roads']==oldrows[(x['index'],x['raw'])]['root_without_roads'] for x in early['trace'] if x['index']<first['index']];before=next(x for x in first['detail']['reports'] if x['mode']=='HIGH');final=next(x for x in first['detail']['reports'] if x['mode']=='FINAL')
    initial={x['index']:x for x in json.loads((D/'late-roots-private.json').read_text())+json.loads((D/'risks-private.json').read_text())};checks=[]
    for name in ('early-recovery-private.json','regression-obstacle-private.json','regression-curvature-private.json'):
        data=json.loads((D/name).read_text());lookup={(x['index'],x['raw']):x for x in data['trace']};case=initial[data['commands'][0]['index']];state=dict(case['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state);s=initial_progress(root,paths['candidate'],case['index']-1);same=0;fresh=0;minimum=float('inf')
        for command in data['commands']:
            same+=float(command['action'][0])==steering(root,paths['candidate'],s);report=next(x for x in command['detail']['reports'] if x['mode']=='FINAL');fresh+=bool(command['detail']['final_recertified'] and report['ok']);minimum=min(minimum,report['min_footprint_margin_m']);last=lookup[(command['index'],4)];root=load_root(dict(last['root_without_roads'],roads=static['root']['roads']));s=last['progress']
        checks.append(dict(window=name,commands=len(data['commands']),steering_rule_identical=same,fresh_final_certificates=fresh,minimum_selected_forecast_margin_m=minimum))
    c=json.loads((G/'retry/footprint535_contract.json').read_text());assert all(hashlib.sha256((G/z).read_bytes()).hexdigest()==h for z,h in c['source_sha256'].items());assert all(hashlib.sha256(Path(z).read_bytes()).hexdigest()==h for z,h in c['private_inputs_sha256'].items());assert all(x['commands']==x['steering_rule_identical']==x['fresh_final_certificates'] for x in checks)
    out=dict(first_pedal_intervention_index=first['index'],lead_before_original_failed_hold_s=(165-first['index'])*.08,first_intervention_steering_bit_identical_to534=first['action'][0]==oldcommands[first['index']]['action'][0],identical_executed_prefix_raw=len(sameprefix),identical_prefix_states=sum(sameprefix),rejected_HIGH_reason=before['reason'],rejected_HIGH_footprint_visibility=before['first_footprint_violation'],selected_FINAL_min_margin_m=final['min_footprint_margin_m'],selected_FINAL_ok=final['ok'],windows=checks,source_input_pins_verified=True,extra_model_ticks=0,extra_force_evaluations=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='Samefeedbacksteeringrulethroughout;afterpedalinterventionsteervaluesmaydifferbecauseownstatetrajectorydiffers. Localrecoverynotglobalfinish/actualgain.')
    with (G/'retry/footprint535_local_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
