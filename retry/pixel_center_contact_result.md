# Stage129: accurate current centers did not establish safe control

**Keep 116; no retry or threshold tuning.** On the DEV lost by 128, the corrected
center was more accurate in every one of 21 fixed pre-contact inputs. A single
frozen 127 visible-center oracle run completed, but incurred damage. These
results do not identify a unique estimator, tracker or controller cause.

Before computing errors, the saved comparison fixed inputs 396–416 and the
immediate subset 412–416. First contact occurred during action 416; each input
uses its own `truth_before`. The unique nearest physical obstacle had a current,
uniquely supported detection in all 21 inputs. The actual 128 center was checked
against the source formula on the same pixels. GT labels remained research-only.

| Fixed risk subset | Mean error, m | p95 error, m | Maximum error, m |
| --- | ---: | ---: | ---: |
| All 21 inputs, original inverse → 128 | 0.521 → 0.146 | 0.664 → 0.267 | 0.781 → 0.329 |
| Last 5 inputs, original inverse → 128 | 0.527 → 0.142 | 0.581 → 0.241 | 0.585 → 0.267 |

No row worsened. The final pre-contact error fell from 0.494 to 0.073m. There
were no unmatched/retained-only gaps in this saved window, detector-edge touches,
or GT centers outside the component bounds. This local evidence passed the
registered gate for one native diagnostic; it does not guarantee future control.

The diagnostic reused the exact original 116 archive and unchanged 127 hook.
It replaced only current visible, uniquely matched existing centers. It did not
apply the 128 inverse or change detection count/order/radius, path, tracker,
route or control. It is privileged research, never a submission candidate.

| Same selected DEV | Endpoint | Actions | Lap | Damage |
| --- | --- | ---: | ---: | ---: |
| Cached 116 | Completed | 548 | 43.820s | 0 |
| Cached pixel 128 | Crash | 423 | — | 1.0 |
| Visible-center oracle 129 | Completed | 548 | 43.800s | 0.4 |

The oracle made 121 effective center replacements; 29 unmatched detections stayed
unchanged, with no additions, hidden layers or ambiguities. Its first correction
was at action 85; actions diverged from 116 at 92 and from 128 at 93. It therefore
does not isolate a swap immediately before the original contact.

The oracle contacted at actions 403 and 405. **Both inputs had zero current
detections and only retained tracks**, which this intervention does not correct.
The nearest physical obstacle was the same as for 128, but no contact-pair ID was
recorded. Oracle completion shows compatibility with completion in this case;
its damage does not prove that a controller failed with exact centers at contact.
Dependence on biased coordinates remains unproven. Any later design must assess
current-center accuracy, continuity after detection loss and downstream response
separately. No successor experiment was launched.

Cost: **548/2000 native actions**, 24.381s wall, 20.482s evaluator CPU and 3.972s
actor CPU. Saved analysis used 21 label contexts/raster passes and 42 component
extractions, with zero policy or native calls. Baselines were reused. Runtime,
observed reset hashes, source guards, correction invariants and actor reaping
passed. Cumulative native 607527; research 14473; reserve 84000 untouched.
Champion 116 and prior artifacts remain preserved; HOLDOUT details and SEALED
stayed closed. Private pixels, labels, seeds, plans and archives remain private.
No paid resources or extension; authorization ends 2026-10-16T10:01:55Z.

Exact aggregate evidence: [pixel_center_contact_result.json](pixel_center_contact_result.json).
