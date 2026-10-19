"""Replay one estimated-input checkpoint in the external private harness."""
import argparse
import json
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser();parser.add_argument('private_directory')
    args=parser.parse_args();directory=Path(args.private_directory)
    output=directory/'single-replay-private.json'
    assert not output.exists(),'NO_REPEAT_REPLAY'
    sys.path.insert(0,str(directory/'package'))
    import runtime598 as core
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
