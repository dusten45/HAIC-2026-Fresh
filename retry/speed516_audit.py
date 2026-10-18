"""Actual saved raw recovery event, no model/native advancement."""
import json,math,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response516-private')

def run():
    t=time.perf_counter();cpu=time.process_time();r=json.loads((G/'retry/speed516_native_result.json').read_text());raw=[json.loads(p.read_text()) for p in sorted(D.glob('raw-*.json'))];offset=0;items=[]
    for arm in r['arms']:
        n=arm['reset_ticks']+arm['actions']*4;rows=raw[offset:offset+n];offset+=n;epoch=rows[arm['reset_ticks']-1]['time'];event=None
        for before,after in zip(rows,rows[1:]):
            if after['phase']!='action' or before['time']-epoch<arm['events']['corner_exit']['time']:continue
            if before['speed']<50<=after['speed']:
                fraction=(50-before['speed'])/(after['speed']-before['speed']);event=dict(lower=before['time']-epoch,upper=after['time']-epoch,time=before['time']-epoch+.02*fraction,speed=50.);break
        items.append(dict(budget=arm['budget'],recovery50=event,after_corner_exit_s=event['time']-arm['events']['corner_exit']['time'] if event else None))
    assert offset==len(raw)==574
    out=dict(arms=items,recovery_after_exit_improvement_s=items[0]['after_corner_exit_s']-items[1]['after_corner_exit_s'] if all(x['after_corner_exit_s'] is not None for x in items) else None,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,additional_native_actions=0,additional_model_ticks=0,scope='Saved actual raw20ms linear recovery event, within completed fixedwindow.')
    with (G/'retry/speed516_recovery.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
