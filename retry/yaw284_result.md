# 284 — GT yaw-rate 고정식 steering 진단

**두도로모두완주했지만240보다느려개선게이트를통과하지못했다.** gain수정·재실행·pixel HUD transfer·학습을진행하지않는다. GT진단이며적법챔피언후보가아니다.

| 기존 TRAIN | 실제결과 | 저장240 | 시간차 | damage |
|---|---:|---:|---:|---:|
| O0 | 23.68초완주 | 23.66초 | +.02초 | .2 |
| N0 | 23.70초완주 | 23.62초 | +.08초 | .4 |

현재pixel에서240을한번호출한final steering u·적법HUD feedbackspeed v를사용했다. `L=3.24`, `r=−hull.angularVelocity`, `k_command=tan(u)/L`, `k_error=k_command−r/v`, `u_return=clip(atan(L*(k_command+k_error)),−.4,.4)`를그대로고정했다. source WHEELPOS의앞80·뒤−82와SIZE.02로wheelbase3.24m를확인했다. unitgain1은진단선택이며최적값의source증명이아니다. smoothing·gain탐색0이다.

target없음·전방아님·v비양수·비유효입력은240그대로반환한다. 각도로feedback296action·fallback1action이었다. clipping은O0 18/N0 16action이었다. GT angularVelocity만추가control입력이며GT lateral/forward velocity는진단에만기록했다. path·target·lookahead를다시계산하거나수정하지않고현재호출의final gas/brake를그대로유지했다. **594action의pedals byte-exact와반환steering memory/이력일치를검증했다.** steering이basefloat32와같으면기존float64nominalmemory를보존하고,다르면실제반환float32를memory에반영했다. 이후closed-loop path/feature/pedals변화는정상적피드백이다.

Yaw추종오차는각pre-action의240명령으로고정한`r_target=v*tan(u)/L`를기준으로했다. rad/s RMSE는O0 pre .8241→해당action뒤 .6508, N0 pre .9053→뒤 .6735였다. curvature error RMSE는.01709/.01920 m⁻¹, pre yaw최대절대오차3.366/6.406rad/s였다. 이는변경된궤적에서현재명령과한action뒤yaw의진단이며기존240yaw와의독립인과대조나주행시간개선을뜻하지않는다. path error는계산하지않았고매번원점에서시작하는새path의거리로일치도를주장하지않는다.

`tan(u)/L`와`r/v`의curvature근사는sideslip·friction saturation·wheel actuator lag에서깨질수있고HUD speed의양자화/fallback도true longitudinalspeed와다르다. 진단GT lateral velocity의최대절대값은2.249/2.340m/s였다. 이값을control에넣지않았다.

두주행정상종료:실제DNF0·cap검열0·기술오류0. 기존공식2000action horizon을유지했다. 신규 **594native**는총4000상한내며baseline재주행0·모델physics0·학습0·새DEV/HOLDOUT/SEALED0이다. 실제elapsed35.322초,물리tick2371·reset tick102. 누적948,492 + 연구잔여31,508 + 최종예비84,000 =B1,064,000. 예비사용0·유료자원추가0. 챔피언240·main·Participants·백업보존.

raw trace/GT진단·receipt는비공개에보존했고공개는 `yaw284_prepare.py`, `yaw284_run.py`, `yaw284_result.json`의코드와집계다.
