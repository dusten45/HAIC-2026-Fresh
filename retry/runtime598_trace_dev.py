"""External diagnostic prefix capture and one fixed failed HIGH physical probe.

The participant package, inputs and chooser are unchanged. The optional probe
runs only after the participant has stopped; its action is the recorded first
original HIGH trial, never a searched action or participant fallback.
"""
import argparse,json,sys,time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--probe-failed-high-raw',type=int,default=0,choices=(0,1,2))
    parser.add_argument('--probe-call',type=int)
    parser.add_argument('--compare-checkpoint')
    args,rest=parser.parse_known_args();sys.argv=[sys.argv[0],*rest]
    from retry import submit_dev as run
    if args.probe_failed_high_raw:
        assert args.probe_call is not None and args.compare_checkpoint
        from core.vendor.car_racing import CarRacing
        from retry.runtime598_diagnostic import external_truth,dump
        original_close=CarRacing.close;completed=False
        def close(raw):
            nonlocal completed
            out=None;dispatches=0;raw_done=0
            try:
                if completed:return
                completed=True
                label=rest[rest.index('--label')+1];out=run.PRIVATE/label
                checkpoint=json.loads((out/'checkpoint-private.json').read_text())
                report=json.loads((out/'original-report-private.json').read_text())['report']
                assert checkpoint['call']==args.probe_call and report['mode']=='NO_ADMISSIBLE_ACTION'
                assert all(t['reason']=='FORCE_PEAK' for t in report['trials'])
                import numpy as np
                compared=Path(args.compare_checkpoint)
                assert np.array_equal(np.load(out/'input-private.npy'),np.load(compared/'input-private.npy')),'DIAGNOSTIC_PREFIX_PIXELS_DIVERGED'
                before=json.loads((compared/'external-truth-private.json').read_text())
                current=external_truth(raw)
                assert before['hull']==current['hull'],'DIAGNOSTIC_PREFIX_POSE_DIVERGED'
                forecasts=json.loads((out/'forecasts-private.json').read_text());action=forecasts[0]['action']
                assert action[1]==1. and action[2]==0. and report['trials'][0]['u']==1.
                cpu=time.process_time();wall=time.perf_counter();snapshots=[]
                run.ledger_charge('actions')
                dispatches=1
                for i in range(args.probe_failed_high_raw):
                    snapshots.append(dict(raw=i+1,time_s=raw.t,truth=external_truth(raw)))
                    before_time=raw.t;raw.step(np.asarray(action,np.float32))
                    assert round((raw.t-before_time)/.02)==1
                    run.ledger_charge('raw')
                    raw_done+=1
                snapshots.append(dict(raw=args.probe_failed_high_raw+1,time_s=raw.t,truth=external_truth(raw)))
                dump(out/'fixed-high-physical-probe-private.json',dict(action=action,snapshots=snapshots,
                    exact_prefix_pixels_and_pose=True,participant_already_stopped=True,
                    diagnostic_DEV_dispatches=1,raw_physics=args.probe_failed_high_raw,model_ticks=0,
                    CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,
                    limit='External fixed original HIGH trial only; no policy continuation, new candidate, true Agent input or scored lap.'))
            except Exception as exc:
                if out is not None:
                    dump(out/'fixed-high-physical-probe-error-private.json',dict(
                        status='PROBE_FAILED',error=type(exc).__name__+':'+str(exc),
                        diagnostic_DEV_dispatches=dispatches,raw_physics=raw_done,
                        limit='No successful physical-probe claim; prefix and worker cleanup retained.'))
            finally:original_close(raw)
        CarRacing.close=close
    run.main()


if __name__=='__main__':main()
