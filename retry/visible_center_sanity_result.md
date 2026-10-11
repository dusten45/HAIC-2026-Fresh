# Repaired visible-center sanity and DEV diagnostic (stage127)

**Prioritize pixel obstacle center estimation; keep champion 116.** The corrected privileged diagnostic completed the known failed DEV condition in **49.480s with zero damage**, after replacing 122 existing detection centers. It is research evidence, never a submission candidate. Stage126's inactive result and its original definition are preserved.

The actual native resampling path reduced an entirely white255 canvas to uniform **253**. Thus stage126's required255 ownership witness could not pass. Three stored pre-contact inputs, before actions164/168/172, had matched-component coverage248–253/233–253/249–253: each passed>=128 but failed the255 requirement. Native obstacle rendering differed from saved gray pixels by at most1/0/0 on those components. Input frameIndex=action-1 and truth_before were aligned with the hull-angle camera and native draw order. The reconstruction used uniform102 road, no curb/reward text and unrecorded wheel phase0; it establishes component sanity, not whole-frame or temporal-history parity.

The explicit definition change was **all component pixels>=128 AND any255 → all component pixels>0** in the same post-occlusion native ownership layers. Both directions of unique component/object matching remain required; competing or unmatched objects stay unchanged. There was no coverage cutoff search or distance matching. Original detector path, count/order/radii, pixels and tracker/route/controller source were retained. Hidden layers were excluded and no detections added.

All three stored frames then replaced one center each. Actual saved worker checks preserved the original detected path and fields. The first check mistakenly compared the pre-correction observer field with corrected detections; its core assertions had passed. The remaining two frames checked the actual tracker return, without repeating the first frame or adding physics.

| Evaluation | Native actions | Endpoint | Damage | Replacements |
|---|---:|---|---:|---:|
| Cached original 116 | 181 | Crash | 1.0 | 0 |
| Preserved stage126 | 181 | Crash, inactive | 1.0 | 0 |
| Stage127, cap2000 | **619** | **49.480s,300/300tiles** | **0** | **122** |

Stage127 saw181 detections:122 centers replaced on122 actions and59 unmatched entries retained. Ambiguity, added detections and hidden layers were zero. Count/order/radius and source-component alignment checks held throughout. Initial reset hashes and loaded policy bytes matched116; the actor was reaped. First replacement was action66; first actual action difference was72. The rescue includes trajectory changes before the original collision region and does not isolate a single frame or establish a unique cause.

Stage127 cost: **619/2000 native actions,27.840s wall**,23.449s evaluator CPU and4.484s actor CPU;2475 raw step ticks and51 reset ticks. Oracle context generation took1.043s within that wall time, using220 label raster passes. Preparation added3 stored scene draws,3 label passes,1 white resampling calibration and3 saved policy resets/actions, with no physics or model calls. Preparation wall/CPU is separate; the first checker-error timing was not captured, while all calls are counted.

Including failed126: **800 native actions,36.414s native wall**. Native total605950; research remaining16050; final reserve84000 untouched. Frozen116, rollbacks, original126 records and the terminated global+1pixel margin archive remain preserved. Protected HOLDOUT details and SEALED stayed closed. Ordinary research branch commit/push includes code and aggregate results only; private frames, seeds and archives remain private. Authorization still ends2026-10-16T10:01:55Z, with no paid resources or extension.

This selected DEV contrast supports the preregistered next priority: improve pixel center inverse-camera/centroid estimation before new candidate evaluation. It does not establish generalization or qualify a pixel-only implementation. No follow-up experiment or adoption was performed.
