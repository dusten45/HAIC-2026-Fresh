# Fixed3/12 pulse gate252

Current240 completed8/8, continuous251 completed0/8, and fixedpulse252 completed**5/8**. Actual DNFs3, censored0, unexecuted0. Meanpaired officialtime delta on5commoncompletedroads:-0.58s. Stopfurthermatched-teacher affinevariants: fixeddurationgate stilllosesbaselinecompletion orfails pairedtimegain.

Onlycorrectionduration changed: first12actions current240; from13 each12-action cycle applies unchanged251affinecorrection for3actions and onlycurrent240pedals for9. Everyaction still computes nominalcontrol andupdates originalmemory fromactualpixels. All251coefficients,16inputs,normalization,clip/scales/steering stayedfrozen. No phase/duty/threshold/fit sweep. Thisclosed-loopoffphase isnot the249recordedfuturesequence; statesreceivingcorrection canchange as thetrajectorychanges.

| Road | 240 | Continuous251 | Pulse252 | Paired delta | Firstzero-road-wheels / collision | Gateon |
|---|---:|---|---|---:|---|---:|
| O0 | 23.66s | off_track | 23.06s | -0.60s | None / None | 70 |
| O2 | 20.98s | crash | 20.18s | -0.80s | None / 177 | 61 |
| N0 | 23.62s | off_track | 22.78s | -0.84s | 200 / 102 | 69 |
| N1 | 17.08s | crash | 17.30s | +0.22s | None / 31 | 52 |
| N2 | 21.56s | crash | crash | — | None / 62 | 15 |
| N3 | 18.76s | crash | off_track | — | None / 55 | 45 |
| S0 | 22.02s | off_track | 21.14s | -0.88s | None / None | 64 |
| S1 | 19.22s | off_track | off_track | — | 159 / None | 69 |

Firstzero-road-wheelcontact is a departureproxy, notofficialoff_tracktermination; collision anddamage arediagnostic. Continuous251didnotretain firsteventtiming, so itis notinvented orreplayedhere. Allfixedgate counts wereverified againstrecorded masks. Failurescontinued through thefixed8-road order. Currentresults reuse sixTRAINroads andtwo247DEV screens; theyare notindependent generalizationevidence.

Cost:1,846nativeactions,86.3s; gateon445actions. No newmodelticks orfits. FullAgent median5.61ms, IPCmax39.50ms. Researchbalance5,644; final84,000reserve unused. Champion240, main, Participants, backups andofficialHOLDOUT/SEALED unchanged. Rawcache/model/roadidentities private; completedruns saved withoutreplay. Noautomaticfollow-up.
