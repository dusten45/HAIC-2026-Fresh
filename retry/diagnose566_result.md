# 566 — finite time gain partly repaid late; tracker keeps the same raw finish sample

551’s saved reference trajectory, 562’s modified prefix plus feedback continuation, and 565’s final verified tape each contain 662 raw records. Their first136 raw states and forces match exactly. This analysis reads those stored rows and applies no source ticks, force evaluations, geometry checks, or native actions.

The official source finish is **13.219999999999807s for all three**. The 565 finite result’s **11.3353ms** compares its safe feedback continuation against its own starting incumbent at the action75 plane. Against551, its action75 crossing is **12.1304ms earlier**; the two comparisons use different references.

## Fixed spatial boundaries

At each common boundary below, the reported time is a linear interpolation between adjacent saved raw centers. It is diagnostic only. Cumulative difference is relative to551; negative means that candidate crossed earlier.

|Boundary|562 cumulative Δ vs551|565 cumulative Δ vs551|
|---|---:|---:|
|Original action75 plane|−0.795ms|−12.130ms|
|Original path arc s=400m|−0.814ms|−12.146ms|
|s=500m|−1.951ms|−10.089ms|
|s=600m|−1.801ms|−8.559ms|
|s=700m|−8.290ms|−18.570ms|
|s=800m|−9.408ms|−22.950ms|
|s=900m|−2.501ms|−5.628ms|
|Finish center plane, interpolated|−0.037ms|−1.292ms|

The important late change occurs between **s=800m and s=900m**: 565 takes 17.322ms longer than551 over that interval. It takes another 4.336ms longer from s=900m to the interpolated center-plane crossing. That repays 21.658ms of the 22.950ms lead at s=800m, leaving a diagnostic 1.292ms lead at the center plane. The center-plane crossing estimate uses linear interpolation across a20ms raw pair; it does not replace the tracker time.

562 shows the same pattern at a smaller scale: it repays 6.907ms between s=800m and s=900m, then takes 2.464ms longer from s=900m to the center plane. Its interpolated center-plane time is effectively tied with551.

This gives both parts of the answer. A real later delay erases most of the earlier finite gain. The remainder does not change the official finish because all three trajectories produce the same sampled crossing event.

## Tracker bracket and route state

The saved finish tracker has a20ms raw update clock. For each trajectory the center-plane sign change is bracketed by raw **660→661**, at13.20–13.22s source time. The reconstructed sampled center-plane candidate is raw661 at13.22s, matching the tracker’s stored physics-clock finish time14.24s after subtracting the1.02s warm-up. The tracker confirms crossing the forward half-depth later at raw662, bracketed by13.22–13.24s. It retains the raw661 candidate time. Thus the official result remains13.22s even though the diagnostic interpolated center crossing differs by up to1.292ms.

The early finite gain follows a changed line through the fixed sections. At the original action54 plane, 565 crosses **2.778m to the side** of551, with speed92.35 versus92.82m/s and heading difference about+.019rad. At s=200m its offset is−2.494m versus551’s+.325m. By s=400m the offsets have converged (−.148m versus−.142m), and at action75 both cross within1mm laterally. A fast crossing at action75 therefore describes an alternate line and state, not a uniform speed improvement along the lap.

The late finish approach also has a different state. At s=900m, 565 is about.87m/s slower than551 (59.24 versus60.10m/s), its heading differs by.00384rad and yaw rate by.183rad/s, while its lateral offset is close (−.104 versus−.090m). The finish tracker’s final lateral values remain close across all three. These are route/state correlations in saved source trajectories; they do not isolate a single cause.

All three share55 launch clipping events. Tracking clipping totals are84/2264 for551,81/2264 for562, and89/2264 for565. At s=700m the respective counts are59,57,64; at s=900m they are64,62,69. The 565 count is higher at those late boundaries, but the s=600→700 segment is faster than551. The counts alone do not explain the timing change.

## What the next objective should measure

The evidence supports retaining the interior-target restoration and fresh-feedback checks that produced two safe finite improvements. It does **not** support another update whose objective ends at action75 alone: the largest remaining timing loss is after s=800m, while the terminal event is decided at the finish center plane and sampled at raw661.

For a next optimization, keep action75 as a diagnostic and measure the s=900m approach and the tracker candidate sample from the same freshly computed feedback policy. Use spatial state (lateral offset, speed, heading, yaw rate, and clipping history) to tell whether a boundary gain comes from a changed line. Require exact original safety and whole-source replay for any candidate. The official score can only improve when the tracker candidate moves to an earlier raw sample; interpolated crossing time can guide local search but cannot claim a whole-lap result.

This is a source-model diagnosis, not a native or pixel-policy performance result. No new source integration, native action, protected evaluation, or reserve use occurred. The analysis processed only stored trajectories; its audit checks nine consistency conditions, with model/force/geometry counts all0 and CPU about.18s.

[Read-only analysis code](diagnose566.py) · [Aggregated crossings, state, clipping, and raw brackets](diagnose566_result.json)
