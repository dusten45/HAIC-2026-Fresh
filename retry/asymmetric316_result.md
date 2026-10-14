316 — training-only asymmetric critic의 캐시 선행 반증 완료

**C의 held-out 평균 MSE는 A와 offset-only B보다 낮았다. 다만 C−A bootstrap 구간은0을 포함하고 완주 episode의 오차는 커졌다.** 제한적인 긍정 증거이며 actor·정책 개선이나 PPO 실행 근거의 확정으로 주장하지 않는다. 새 native·source simulation·PPO update는0이고 296을 유지한다.

276은 actor·critic 모두 legal28을 사용했고277은 critic의 terminal return calibration이 약함을 확인했다. 이번에는 actor 입력을 바꾸지 않고, **훈련용 critic에만 현재 progress·damage·time을 넣으면 단순 reward 회계를 넘어선 정보가 생기는지** 기존 buffer의 고정 회귀로 확인했다. 실제 정책이나 critic 학습 recipe를 배포하지 않았다.

출처를 재확인한 terminal episode는 **231개(완주167/DNF64)**이며 collection cut62개·9,110행을 제외했다. accepted source의 기술 중단은0이다. terminal buffer54,378행에서 reset visited를 모르는 첫 행231개를 모든 arm에서 제외해 **54,147행**을 사용했다. 277의 road·early/late별 terminalID 정렬 `[4::5]` holdout을 재구성해 저장 split과 정확히 일치함을 확인했다. TRAIN188episode·44,185행, held-out43episode·9,962행이다. 이는 같은 여섯 TRAIN·변화하는 과거 policy 안의 episode holdout이며 unseen-road 평가가 아니다.

입력 X는 action k 전에 저장된 legal28이다. progress·damage는 POST-step journal의 **k−1행만** 사용했고 k≥2로 제한했다. progress 분모는 기존 TRAIN 등록의 불변 tile 수로, 각 episode의 실제 tile 수와 일치했다. terminal visited·final damage·episode length·종료 사유·미래 관측·road/policyID는 입력에 넣지 않았다.

source wrapper의 skip4와 episode raw tick 범위를 확인하고, k≥2의53,916개 nonterminal reward delta가80ms 간격과 일치하는지 별도로 검증했다. 최대 시간 오차는 **1.87e−14초**였다. `t_pre=.08*(k−1)`, `offset=p_pre−t_pre/160`, `G=현재 k부터의 reward suffix`로 계산했다. 모든 사용 행에서 **S=G+offset이 episode final score와 일치**했으며 최대 오차는 **1.20e−14**였다. reset progress를0으로 가정하거나 offset을 임의 보정하지 않았다. 첫 reward가 source의 previous progress0에서 시작하는 회계와, 실제 첫 reset visited를 모르는 관측 문제는 구분했다.

결과 전에 고정한 세 arm은 다음과 같다. λ1 scalar ridge·bias penalty0·TRAIN 전용 정규화(std floor1e−6)·동일 episode 가중치·같은 split을 사용해 각각 한 번만 적합했다.

| arm | 학습 입력·표적 | remaining-value 출력 |
|---|---|---|
| A | legal28 X → G | G_hat |
| B | legal28 X → S | S_hat−p_pre+t_pre/160 |
| C | X + p_pre + damage_pre + t_pre/160 → S | 같은 offset 변환 |

| held-out episode-balanced | MSE | RMSE | bias(V−G) | EV |
|---|---:|---:|---:|---:|
| A | 0.863377 | 0.929181 | −0.085716 | 0.036780 |
| B | 1.005139 | 1.002566 | −0.084281 | −0.123008 |
| C | **0.829917** | **0.910998** | −0.063458 | 0.070694 |

C의 평균 MSE는 A보다 0.033460, B보다 0.175222 낮다. 최소 개선율 조건은 두지 않았다. B는 A보다 나빴으므로 final score 표적과 알려진 offset 변환만으로 개선된 결과가 아니다. C의 상태 추가는 이 캐시에서 추가 예측 정보를 제공했다. 다만 이 선형 모델·실현 return·split에 한정한 해석이다.

43개 episode의 대응하는 개별 MSE를 저장하고, 같은 episode resample을 사용하는 고정 500회 bootstrap(seed316)을 수행했다. 개별 ID·예측·loss는 비공개로 보관했다.

| paired episode loss | 평균 ΔMSE | 중앙값 ΔMSE | 왼쪽 arm이 낮은 비율 | 평균 차이의 95% 구간 |
|---|---:|---:|---:|---:|
| C−A | −0.033460 | **+0.008042** | 15/43 (34.9%) | **[−0.123519,+0.042045]** |
| C−B | −0.175222 | **+0.023731** | 11/43 (25.6%) | [−0.348454,−0.027741] |
| B−A | +0.141762 | −0.006394 | 25/43 (58.1%) | [+0.063029,+0.236878] |

평균 개선은 많은 episode에서 고르게 나타난 것이 아니다. 특히 C−A는 이 bootstrap에서 방향이 확정되지 않는다. Bootstrap 단위는 episode이며 같은 도로·시기·과거 policy의 의존성을 완전히 제거한 독립 표본은 아니다.

| held-out 진단 | episode | A MSE | B MSE | C MSE |
|---|---:|---:|---:|---:|
| 완주 | 34 | 0.377823 | 0.369997 | **0.460814** |
| DNF | 9 | 2.697692 | 3.404564 | **2.224306** |
| 전반 | 21 | 0.742457 | 0.860341 | 0.741530 |
| 후반 | 22 | 0.978802 | 1.143355 | 0.914286 |

평균 개선은 DNF·후반 쪽이 주도했고 완주 쪽은 악화했다. Complete/DNF 조건부 bias나 EV만으로 critic이 틀렸다고 확정하지 않는다. 모든 진단의 RMSE·bias·EV와 complete×early/late도 JSON에 저장했다. 예측 개선을 credit·actor gradient·완주/time 개선으로 대신하지 않았다.

향후 실제 PPO matched pilot을 검토할 때의 **비용만** 제안한다. B offset-only와 C asymmetric 두 arm의 legal28 actor·초기 actor/RNG·S target과 offset·나머지 PPO 조건을 일치시키고 C의 추가 critic 입력만 바꾼다. 각 arm 8,192 action·8 update, 최종 checkpoint만 기존 여섯 TRAIN에서 비교하는 작은 인과 pilot이라면 **학습 16,384 + 최종 평가 cap 6,000 = 새 native cap 22,384**다. 현 잔액 2,195를 사용한다면 이 cap에 필요한 추가 연구량은 **20,189**이며 예비는 쓰지 않는다. 이는 수렴에 필요한 학습량의 증명이나 이번 실행·예산 요청·자동 확대가 아니다. 평가 cap 안에서 12개 결과를 모두 관측할 보장은 없으며 cap censor는 미관측으로 취급한다.

비용 근거는 278의 두 arm 각 8,192 action 실측 학습 532.723초, 276의 19.02 native/초, 315의 1,685 native/164.257초이며 같은 지정 cloud에서 약 **14~36분**을 예상한다. 부하·episode 길이·critic 구성에 따라 달라진다. 이번의 약한 C−A 증거와 완주 쪽 악화를 고려해 pilot을 자동 실행하지 않고 계획만 남겼다.

316 실측은 **ridge 3 fit, wall 5.609초·CPU 5.278초**이며 fit 단독 wall 합계는 0.184초다. 새 native·source physics·actor 호출·PPO update·유료 자원은 0이다. **누적 1,243,805 + 연구 잔여 2,195 + 예비 84,000 = B1,330,000**을 유지하고 v322 예산 원장은 변경하지 않았다. 315 실패·296·rollback·main·Participants·backup·개인 원문을 보존했다. DEV/HOLDOUT/SEALED·승격·자동 확대는 없다. Raw buffer·journal·계수·예측·episode ID는 비공개이며 일반 코드와 집계만 공개한다.

[고정 fit·회계 검증 코드](asymmetric316_fit.py) · [집계·전체 진단·비용](asymmetric316_result.json)
