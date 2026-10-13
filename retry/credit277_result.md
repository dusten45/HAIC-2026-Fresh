# 277 — 저장된 TRAIN terminal credit 진단

**우선순위는 관측된 terminal return에 대한 critic 보정·긴 credit 전달을 확인하는 쪽이다.** 다만 GAE가 항상 반대 방향을 줬다는 근거는 없고, λ.95만276 실패 원인이라고 단정하지 않는다. 과거 feature 이력은 작은 추가 정보를 제공했지만 큰 temporal 개선을 우선할 강한 근거는 아직 없다. 새 policy 학습·주행·중간 checkpoint 성능 평가는0회다.

276의62개 TRAIN rollout(3–64)에서 실제 λ.95 GAE와 batch 정규화를 재구성했다. **실제 종료231episode·54,378samples**만 undiscounted remaining reward sum과 당시 value를 비교했다. Complete167개·DNF64개이며 cut62개·9,110samples(전체14.35%)는 MC/full return에 넣지 않았다. 학습 전반은update3–33, 후반은34–64다.

## 실제 return 예측

Episode별 동일 가중치, 오차는`value−observed remaining return`이다. Observed MC는 stochastic trajectory의 실현값으로, 잡음 없는 conditional expected value는 아니다. Complete/DNF 조건부 편향 자체만으로 critic이 틀렸다고 판단하지 않는다.

| 관측 terminal 표본 |RMSE |평균 편향 |explained variance |
|---|---:|---:|---:|
|전체 |1.026 |+0.208 |0.028 |
|전반 |0.990 |+0.024 |0.037 |
|후반 |1.061 |**+0.393** |0.081 |
|Complete |0.527 |−0.360 |−1.228 |
|DNF |1.753 |+1.690 |−5.539 |

후반의 값은평균1.182, 관측 remaining return은0.789로 과대예측했다. Bootstrap λ-target loss 감소를 이 표의 실제 return 정확성으로 대신하지 않았다. Source predicate의 첫 구현은 전체 pooling만 확인했으나, 사용자 요청의 전·후반 구분에서는 후반이 **동일한 사전 RMSE>0.5·절대 편향>0.25 기준**을 충족했다. Threshold·predictor·split을 바꾸지 않고 이 scope 검토를 기록한 뒤 예측 대조를 한 번 실행했다.

## DNF 앞20–100 action의 credit

Terminal action을k0으로 두고 backward distance20–100인 **4,442samples·64DNF episode**를 확인했다. Raw GAE 평균−0.149 대관측 MC advantage−1.503이며 raw 부호 불일치는14.5%다. 실제 학습의 GAE batch 정규화를 **같은 offset/scale로 MC에도 적용**하면 부호 불일치는22.3%(전반19.7%,후반24.7%)다. Cut의 MC가 없으므로 가상의 full-batch MC normalizer는 만들지 않았다.

| 도로 |전반 DNF episode / 정규화 부호 불일치 |후반 DNF episode / 불일치 |
|---|---:|---:|
|O0 |없음 |1 /3.7%* |
|O2 |2 /45.7%* |3 /56.8% |
|N0 |3 /21.0% |5 /26.7% |
|N1 |4 /27.3% |8 /37.5% |
|N2 |17 /11.0% |14 /12.4% |
|N3 |4 /31.5% |3 /15.5% |

*3episode 미만인 cell은inconclusive다. 같은 episode의 많은 sample을 독립 반복으로 취급하지 않는다.

당시 actor checkpoint는 **score Jacobian 재구성에만** 읽었고 정책을 평가·선택하지 않았다. 같은 DNF window에서 old-policy initial surrogate의 실제 actor parameter gradient를 비교했다. 46eligible rollout의 GAE/MC gradient cosine 중앙값은 **0.584**(전반0.733,후반0.557), 반대 방향은 **1/46**이었다. MC/GAE gradient norm 중앙비는6.25였지만 이는 global gradient clip·Adam **이전** 값이며 실제 optimizer step 차이나 정책 개선 효과를 뜻하지 않는다.

즉 dense reward·critic이 이미 일부 부정적 미래를 전달했다. `.95^20=.358`, `.95^100=.0059`만으로 실패를 설명할 수 없다. 차이는 많은 sample의 완전한 부호 역전보다 credit 크기·일부 방향 및 후반 calibration에 있다. 이것도 실패 원인을 분리한 인과 실험은 아니다.

## Cut과 한 번의 이력 예측 대조

Cut prefix는24–281action(중앙156), bootstrap value 평균1.055다. Cut 끝의value가 GAE target에 주는 contribution은prefix별 평균0.196, 마지막20action 평균0.677이다. 이는 실제 finite-prefix GAE의 bootstrap 항만 계산한 값이며 그 이후 terminal·full return·실패는 관측되지 않았다.

| 도로 |cut episode |prefix samples |prefix 중앙 길이 |
|---|---:|---:|---:|
|O0 |12 |2155 |207 |
|O2 |10 |1193 |88 |
|N0 |16 |2116 |114.5 |
|N1 |8 |1160 |157.5 |
|N2 |7 |1210 |232 |
|N3 |9 |1276 |142 |

Predictor는동일 scalar affine ridgeλ1·unpenalized bias·train-episode만의 normalization·episode 동일 가중치다. 현재 적법28입력 대현재28+이전3단계 pixel-derived16feature/availability mask의79입력을 비교했다. **188episode fit·43episode held-out**, road/전후반별 매5번째episode를미리 고정해같은split을썼다. RoadID·GT·미래 관측·평가 도로는 입력에 없다. Cut은 fit/test 모두 제외했다.

| 같은 held-out episode |RMSE |explained variance |
|---|---:|---:|
|당시 critic |0.958 |−0.007 |
|현재28 ridge |0.929 |0.037 |
|이력79 ridge |**0.909** |0.079 |

이력의relative RMSE 개선은 **2.2%**다. Episode paired bootstrap500회에서 ΔMSE95%구간은 **[−0.0566,−0.0197]**로작은 이득을 지지한다. 그러나 사전5%실용 기준에는못 미쳤고 절대 explained variance도낮다. 3-step 이력의 작은 추가 정보는 확인했지만 더 큰 temporal 모델이나 긴 이력의 우월성은inconclusive다. 바뀌는 역사적 정책과 같은6TRAIN 안의episode-held-out 비교이며 새 도로 일반화·정책 성능 검증이 아니다. 추가 availability mask가 기존 action-history mask 정보를 중복한다는 제한도남긴다.

## 비용·마감

진단/예측 계산 합계 **4.64초**, CPU4.32초, predictor fit합계0.18초다. **Native0·모델 물리0·policy optimizer update0·새 성능 평가0**이며 predictor fit만2개(한 paired 대조)다. 연구 잔여 **5,069**, 최종예비 **84,000**은 그대로다. 276학습을 재개하거나 중간 모델을 골라 평가하지 않았다.

다음 판단은 **긴 terminal credit/실제 return calibration을 우선 검토**, temporal 개선 우선순위는아직불확실이다. 관측MC의 stochastic variance, sparse DNF cell,14.35% terminal-unobserved cut 때문에 λ 변경의 효과·단일 실패 원인은확정하지 않는다. 새 실험 없이 마감했고240·main·Participants·백업·HOLDOUT·SEALED를 유지했다. Raw buffer·checkpoint·predictor arrays·개인 자료는비공개다.

[집계](credit277_result.json) · [credit/critic 재구성](credit277_analyze.py) · [조건부 paired predictor](credit277_predict.py)
