# 328: 사후 선택 hybrid의 캐시 open-loop rollout

**H1 채널 결합은 정확했지만 hybrid는 모든 채널에서 우세하지 않았다.** O0/O2 H12에서 hybrid speed RMSE는 전체 ridge보다 소폭 낮고 joint는 motor 수준이었으나, yaw RMSE는1.58811rad/s로 ridge0.72652보다 컸다. 모델 선택은327을 본 사후 선택이고,326에서 이미 평가한 궤적을 재사용하므로 독립 확증으로 주장하지 않는다. 새 fit·actor/controller·native·source physics·PPO·보호 분할 평가·승격은 없다.

중복 등록·실행이 없음을 확인한 뒤 결과 전에8개 고정 궤적·horizon1/3/12·모델·입력·채점·support·이상값 집계를 등록했다. Speed는 고정325 residual ridge, yaw·joint는 기존 motor 식이다. 각 step의 두 branch는 **같은 predicted pre-state**를 입력받는다. Joint 목표는−steer이며 yaw는 `old yaw + old speed/3.24 × (tan(next motor joint) − tan(clipped old joint))`다. 새 speed로 yaw를 계산하지 않는다. Motor는 damage·torque·slip을 생략한 근사다.

O0/O2는 해당 도로 제외 모델, 신규 S1은 기존 여섯 모델의 고정 평균이다. 매 step에서 여섯 모델을 같은 predicted state/action에 적용해 평균하며 여섯 개의 독립 rollout을 나중에 평균하지 않는다. 최초 관측 HUD는326의 동일 실행에서 직접 decode한 캐시를 재사용하고 원시 source·모델 hash 및 상태 chain을 검증했다. 재귀 함수의 입력은 초기 HUD·주어진 실제 action 열·고정 모델뿐이다. 미래 픽셀·feature3 fallback·실제 다음 상태·contact flag는 재귀 입력에 없다. 실제 미래 HUD는 채점 target만이다.

네 방법은 각 horizon에서 정확히 같은 창을 사용했다. 전이 중간에 관측값으로 재초기화하지 않았다. 궤적별 horizon endpoint가 실제 존재하는 모든 시작점을 사용하고 마지막 누락 endpoint나 terminal 이후 관측을 만들지 않았다. H1은 teacher-forced one-step과 동일한 비교로 **별도 표시**했으며 H3/H12에 teacher forcing을 하지 않았다.

| Horizon | 실제 시간 | 전체 eligible 창 | O0/O2 | S1 |
|---|---:|---:|---:|---:|
| 1 | 0.08초 | 2,474 | 1,508 | 966 |
| 3 | 0.24초 | 2,458 | 1,500 | 958 |
| 12 | 0.96초 | 2,386 | 1,464 | 922 |

창은 중첩돼 독립 표본이 아니다. 같은 도로 안에서는 궤적마다 같은 총 가중치, 도로 사이에도 같은 총 가중치를 주었다. O0/O2와 S1은 별도로 집계했다. 채널 순서는 speed m/s, yaw rad/s, joint rad이며 서로 다른 단위를 합산하지 않는다.

| O0/O2 RMSE | 방법 | Speed | Yaw | Joint |
|---|---|---:|---:|---:|
| H1 | Persistence | 1.76950 | 0.50280 | 0.04671 |
| H1 | 전체 ridge | 1.44586 | 0.31430 | 0.01031 |
| H1 | Motor | 1.76950 | 0.37175 | 0.00480 |
| H1 | Hybrid | 1.44586 | 0.37175 | 0.00480 |
| H3 | Persistence | 3.28829 | 1.21842 | 0.11349 |
| H3 | 전체 ridge | 1.89941 | 0.54646 | 0.01016 |
| H3 | Motor | 3.28829 | 0.78709 | 0.00484 |
| H3 | Hybrid | 1.89325 | 0.77899 | 0.00484 |
| H12 | Persistence | 8.36874 | 1.96939 | 0.20875 |
| H12 | 전체 ridge | 2.83971 | 0.72652 | 0.00996 |
| H12 | Motor | 8.36874 | 1.63627 | 0.00490 |
| H12 | Hybrid | 2.77884 | 1.58811 | 0.00490 |

H1에서 hybrid speed는 ridge, yaw·joint는 motor와 예측 배열이 정확히 일치했다.326에 저장된 전체 ridge·motor의 one-step 예측도 정확히 재현했다. H3/H12에는 각 방법이 자기 예측 상태를 쓰므로 hybrid speed가 독립적으로 rollout한 전체 ridge speed와 같아야 하는 것은 아니다. Joint는 속도에 의존하지 않는 기존 motor 갱신을 공유해 세 horizon 모두 motor와 정확히 같았다.

| H12 보조 S1 RMSE | Speed | Yaw | Joint |
|---|---:|---:|---:|
| Persistence | 10.96000 | 1.50239 | 0.15147 |
| 전체 ridge | 10.41271 | 1.08176 | 0.01251 |
| Motor | 10.96000 | 1.24003 | 0.00929 |
| Hybrid | 10.33137 | 1.10736 | 0.00929 |

긴 창의 tail도 남겼다. O0/O2 H12 yaw p95는 hybrid3.93376 대 ridge1.83801rad/s, 최대는9.60018 대4.00816이다. S1 H12 hybrid speed p95는33.73388m/s, 최대62.98202m/s로 큰 오차가 있었다. 이 보조 집합의 speed RMSE가 persistence보다 약간 낮다는 사실로 tail을 상쇄하지 않는다. 각 도로·horizon·방법·채널의 MAE·RMSE·bias·p95·p99·max는 JSON에 모두 있다.

| 도로별 hybrid RMSE | H1 speed/yaw/joint | H3 speed/yaw/joint | H12 speed/yaw/joint |
|---|---|---|---|
| O0 | 1.11848 / 0.31942 / 0.00492 | 1.46865 / 0.74086 / 0.00493 | 2.81053 / 1.60728 / 0.00498 |
| O2 | 1.71174 / 0.41758 / 0.00467 | 2.23872 / 0.81535 / 0.00475 | 2.74678 / 1.56871 / 0.00481 |
| S1 | 2.26472 / 0.30501 / 0.00729 | 4.15457 / 0.56331 / 0.00911 | 10.33137 / 1.10736 / 0.00929 |

Support는 각 LORO TRAIN(보조는325 전체)의 상태3+action3 주변 min/max와 매 predicted input을 비교했다. 이는 joint state-action 지지나 외삽 안전성의 증명이 아니다. 범위 밖 창을 제거하지 않았다. 다음 빈도는 전체8개 궤적의 hybrid이며 중첩 창·예측 step의 반복 노출 수다.

| Horizon | 한 번이라도 주변 support 밖인 창 | 범위 밖 predicted input step | 기존 joint 입력 clip | 기존 motor 속도 포화 tick |
|---|---:|---:|---:|---:|
| H1 | 362/2474 | 362/2474 | 102/2474 | 428/9896 |
| H3 | 731/2458 | 1564/7374 | 170/7374 | 1239/29496 |
| H12 | 1427/2386 | 8028/28632 | 377/28632 | 4850/114528 |

네 방법·세 horizon 모두 **음수 speed·nonfinite 예측은0**이었다. 이 데이터에서 음수 예측이 없었다는 것이 모델의 일반적 양수성 보장은 아니다. 추가 output clip·재양자화는0이다. 위 joint±0.4 입력 clip과 motor speed±3 제한은 기존 비교식의 일부이며 결과 후 넣은 보정이 아니다. Motor/hybrid의 strict `|joint|>0.4` 예측 step은 H1/H3/H12에서39/111/336개였고 최대값은0.4000000059604645다. 실제 float32 action의 경계 표현에 따른 이 값도 숨기거나 재clip하지 않았다. 전체 ridge의 joint 최대 절댓값은 약0.44224다. 방법·horizon·궤적별 부호·비정상·지원 범위·clip 빈도와 분모도 JSON에 보존했다.

327은 사용하지 않았다.327은66obs/65actions로 마지막 개입 이후 endpoint가 하나뿐이므로 개입 뒤H3/12가 없다. 같은64-prefix를 네 arm에서 중복 집계하거나 이전 창을 지속적 제동 검증이라고 부르지 않는다.306은 support 통계의 원래325 학습 입력에만 연결되며 누락 마지막 endpoint를 생성하지 않았다.

배치 재귀와 별도 단일 창 순차 재귀24개를 비교한 최대 차이는7.11e−15였다. 최초 H1 비교·motor 부호/old-speed 식·모델 평균의 공통 입력·모든 원본 hash를 검증했다. 미래 feature·target을 받지 않는 재귀 API를 유지했다. 실패/범위 밖 창의 선택 제거, coefficient 변경, 새로운 clip·quantization은 없다.

추가 native·source physics·fit·actor 호출·PPO·유료 자원은 **모두0**이다. 벡터화한154천 정도의 예측 step 노출(정확히153,920)을 계산했으며 분석 wall/CPU는0.466/0.465초다. 연구 잔여 **0**, 예비 **84,000**, 누적native1,274,701과 예산 v333을 유지했고 비용 원장은 한 번 기록했다.296·원래 모델·기존 실패·사용자 변경·main·Participants·백업을 보존했다. 원시 픽셀·개인 자료·모델·개별 rollout 배열은 비공개다.

이 결과는 주어진 실제 behavior action 열에 조건부인 예측 진단이다. Predicted state에서 새 행동을 고르는 planner나 새 controller의 성능이 아니다. 사후 선택·재사용 데이터·큰 yaw 및 speed tail을 고려해 **hybrid의 전면 우월성이나 MPC 적격성을 주장하지 않는다.** 새 실험·fit·승격을 시작하지 않았다.
