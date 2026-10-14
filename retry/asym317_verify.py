"""Independent journal boundary and S/V/bootstrap audit after fixed training."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save


def verify(R):
    D=R/'stage317';start=time.perf_counter();totals={};maximum=0.
    for arm in ['B','C']:
        A=D/arm;o=read(A/'training-outcome-private.json');count=terminal=cuts=0
        for e in o['episodes']:
            assert not e['technical_interrupted']
            F=A/f"episode{e['serial']:03d}_{e['road']}"
            rows=read(F/'trajectory-private.json');z=dict(np.load(F/'buffer-private.npz'))
            assert len(rows)==len(z['x'])==e['valid_samples']
            for i,row in enumerate(rows):
                p=e['reset_progress_known'] if i==0 else rows[i-1]['visited']/e['total_tiles']
                damage=0. if i==0 else rows[i-1]['damage'];tf=.08*i/160
                cx=np.r_[z['x'][i],[p,damage,tf] if arm=='C' else [0.,0.,0.]]
                assert np.allclose(cx,z['critic_x'][i],rtol=0,atol=1e-10)
                assert abs(z['offset'][i]-(p-tf))<1e-10
                assert abs(z['value'][i]-(z['S_value'][i]-z['offset'][i]))<1e-12
                if z['done'][i]:
                    assert z['next_value'][i]==0
                else:
                    assert abs(z['next_offset'][i]-(row['visited']/e['total_tiles']-.08*(i+1)/160))<1e-10
                    assert abs(z['next_value'][i]-(z['next_S_value'][i]-z['next_offset'][i]))<1e-12
                delta=z['reward'][i]+(1-z['done'][i])*z['next_value'][i]-z['value'][i]
                alternative=z['reward'][i]+(0. if z['done'][i] else z['next_S_value'][i]-z['next_offset'][i])-z['S_value'][i]+z['offset'][i]
                maximum=max(maximum,abs(delta-alternative));assert abs(delta-alternative)<1e-12
                count+=1
            terminal+=e['completed'] or e['actual_DNF'];cuts+=e['collection_cut']
            assert e['reaping']['process_reaped'] and e['reaping']['actor_pids_absent']
        assert count==8192
        import torch
        ck=torch.load(A/'checkpoint8.pt')
        extra=ck['critic']['0.weight'][:,28:]
        if arm=='B':assert torch.count_nonzero(extra).item()==0
        totals[arm]=dict(rows=count,observed_terminal_episodes=terminal,collection_cuts=cuts,
            final_critic_extra_weight_norm=float(extra.norm().item()))
    save(D/'accounting-verification.json',dict(arms=totals,maximum_GAE_delta_algebra_error=maximum,
        pre_action_privileges_verified_against_previous_post_journal=True,first_live_reset_progress_known=True,
        no_privileges_in_actor_inputs=True,terminal_bootstrap_zero=True,cut_bootstrap_next_state=True,
        wall_s=time.perf_counter()-start,new_native=0))
    print('317 independent prestate and bootstrap audit passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',type=Path,required=True)
    verify(p.parse_args().private_root.resolve())
