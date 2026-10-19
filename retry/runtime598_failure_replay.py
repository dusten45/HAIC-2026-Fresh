"""Replay one estimated-input checkpoint in the external private harness."""
import argparse
import json
import pickle
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('private_directory')
    parser.add_argument('--full-agent',action='store_true')
    args=parser.parse_args();directory=Path(args.private_directory)
    output=directory/'single-replay-private.json'
    assert not output.exists(),'NO_REPEAT_REPLAY'
    sys.path.insert(0,str(directory/'package'))
    import runtime598 as core
    if args.full_agent:
        # Trusted, locally generated private checkpoint; no external truth read.
        import agent as participant
        import numpy as np
        agent=participant.Agent()
        agent.__dict__=pickle.loads((directory/'agent-before-private.pkl').read_bytes())
        observation=np.load(directory/'input-private.npy');observation.flags.writeable=False
        native=json.loads((directory/'result-private.json').read_text())
        expected=json.loads((directory/'original-report-private.json').read_text()) if (directory/'original-report-private.json').exists() else {}
        captured={};select=core.Controller.select
        def record(controller,*args,**kwargs):
            result=select(controller,*args,**kwargs);captured['report']=result[1];return result
        core.Controller.select=record
        before=agent.counter[0];start=time.perf_counter();cpu=time.process_time();error=None
        try:agent.act(observation)
        except BaseException as exc:error=type(exc).__name__+':'+str(exc)
        result=dict(error_identical=error==native['worker_failure']['error'],
            full_report_identical=captured.get('report')==expected.get('report'),
            diagnostics_identical=agent.diagnostics==native['worker_failure']['diagnostics'],
            counter_identical=agent.counter[0]==native['worker_failure']['resource_model_ticks'],
            model_ticks=agent.counter[0]-before,CPU_s=time.process_time()-cpu,
            wall_s=time.perf_counter()-start,native_actions=0,
            inputs='Full pre-act reset-local memory and pixels; persistent counter restored and replay delta charged separately; no true state read.')
        output.write_text(json.dumps(result,indent=2)+'\n')
        assert all(result[k] for k in ('error_identical','full_report_identical','diagnostics_identical','counter_identical'))
        print(json.dumps(result));return
    checkpoint=json.loads((directory/'checkpoint-private.json').read_text())
    expected=json.loads((directory/'original-report-private.json').read_text())
    start=time.perf_counter();cpu=time.process_time()
    root=core.load_required_root(checkpoint['root'])
    scene=core.Scene(checkpoint['roads'],checkpoint['boundary'],checkpoint['obstacles'])
    controller=core.Controller(checkpoint['high'],checkpoint['low'],scene)
    controller.model[0]=checkpoint['counter_before']
    action,report=controller.select(root,checkpoint['progress'],checkpoint['hold'],
        checkpoint['launch_history'],checkpoint['running_history'])
    actual_action=None if action is None else action.tolist()
    result=dict(action_identical=actual_action==expected['action'],
        full_report_identical=report==expected['report'],
        counter_identical=controller.model[0]==expected['counter_after'],
        model_ticks=controller.model[0]-checkpoint['counter_before'],
        CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,native_actions=0,
        inputs='Saved estimated root/history/finite scene only; no external truth supplied.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    assert result['action_identical'] and result['full_report_identical'] and result['counter_identical']
    print(json.dumps(result))


if __name__=='__main__':main()
