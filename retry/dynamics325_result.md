# 325: 합법 HUD의 한 행동 전이 식별

**관측된 행동의 한 단계 전이 예측이라는 제한된 가설은 통과했다.** 고정 residual ridge는 세 상태의 다음 HUD 값 RMSE를 persistence보다 낮췄고 여섯 도로 모두 같은 방향이었다. 그러나 속도 MAE는 소폭 악화했고 yaw·joint의 최대 오차는 더 컸다. 관절은 기존 motor 식이 ridge보다 정확했다. Actor/controller 변경, native·source physics·PPO·새 보호 분할 평가는 없다.

과거 learned dynamics를 먼저 확인했다. 비공개40은 GT 차량12상태+action3의 degree2 다항 전이(2,040계수)였으며 HUD를 입력에서 제외했다. 41은 그 GT 모델의 support·계획 순위 진단이었다. 위험 구간과 다단계 tail 실패는 보존한다. 286·319는 고정속도 운동학이고 학습 식별이 아니다. 318은 순간 상태, 324는 terminal 개입 이득 표적이다. 검토한 코드·계획·결과에는 같은 HUD3+action3 한 단계 LORO 대조가 없었다. 동역학 학습 자체가 처음이라는 주장은 아니다.

결과 전에 여섯 TRAIN 도로, decoder·단위·분할·baseline·lambda·모델 크기·비용·중단 기준을 등록했다. fit 전 입력 검증에서 feature4가 목표점 없음 상태에서는 HUD 값 대신 feature3 픽셀 속도로 바뀐다는 오류를 발견했다. 기존 코드의 분기를 확인하고 원래 등록을 보존한 뒤 **fit 전에** 매 프레임 동일한 기존 HUD decoder를 직접 적용하는 계약으로 수정했다. 목표점·모델 결과에 따라 입력을 선택하지 않았다. 다른 값인 행은 T2950 18개, O2 2개였고 나머지는0이다. 모든1,754 프레임에서 HUD template이 일치해 speed fallback은0이었다. 이전318 등 결과를 다시 계산하거나 폐기하지 않았다.

현재 상태는 `[HUD norm speed(m/s), HUD yaw CCW(rad/s), HUD front0 joint angle(rad)]`, 입력은 이 상태3과 같은 행의 실제 float32 `[steer,gas,brake]`다. 속도·yaw·joint는 기존 decoder를 고정했고 새 GT calibration은 없다. 다음 pre-action HUD 세 값의 변화만 학습 표적이다. 미래 영상·GT·history·도로ID·elapsed·damage·collision·return·teacher 명령은 입력이 아니다. 현재 명령은 전이 조건으로 주며 그 결과를 이미 아는 입력은 사용하지 않았다.

306의 연속 캐시1,754 pre-action 행에서 terminal 이후 영상이 없는 여섯 마지막 행동을 제외한 **1,748개**의 동일 도로80ms 전이를 사용했다. 실제 간격 오차는1.71e−15초 이하다. Stack shift·현재 features/action·previous action을 원래 source 기록과 검증했고 미래 terminal endpoint를 합성하지 않았다. 도로 전체 LORO이며 같은 도로의 인접 행을 train/test에 섞지 않았다.

Persistence는 상태 유지다. Ridge는 persistence에 상태 변화 residual을 더하는 affine3-output 모델로, 입력6+bias1의 **21계수**, 정규화12값이다. TRAIN 도로마다 같은 총 가중치, mean/std floor1e−6, lambda1, bias 비정규화를 고정했다. 여섯 fit만 하고 최종 full fit·polynomial·history·lambda sweep은 없다. 보조 motor/kinematic baseline은 기존319의 4×20ms motor gain50·속도 제한3rad/s·목표관절 `−steer`, wheelbase3.24를 사용한다. 속도는 고정하고 관절 변화에서 yaw 변화를 근사하며 slip·wheel force·damage는 모른다. 물리 world나 source physics를 실행하지 않았다.

사전 진단 게이트는 세 표적의 도로 균등 RMSE가 모두 persistence보다 엄격히 낮은 것이다. 통과해도 actor·native·off-policy 계획을 승인하지 않는다.

| 다음 HUD 오차, 도로 균등 | speed RMSE / MAE / p95 | yaw RMSE / MAE / p95 | joint RMSE / MAE / p95 |
|---|---:|---:|---:|
| Persistence | 1.43623 / 0.75523 / 2.50000 | 0.54670 / 0.35296 / 1.23635 | 0.05319 / 0.03269 / 0.12268 |
| Residual ridge | 0.98497 / 0.75779 / 2.02636 | 0.22319 / 0.11982 / 0.37022 | 0.01330 / 0.00500 / 0.01495 |
| Motor/kinematic | 1.43623 / 0.75523 / 2.50000 | 0.31435 / 0.16686 / 0.64773 | 0.00460 / 0.00307 / 0.00821 |

각 열은 상태 자체의 단위다. 서로 다른 단위를 하나의 오차로 합치지 않는다. Speed MAE는0.75523 → 0.75779로 소폭 증가했다. Ridge yaw 최대 오차는3.69405rad/s로 persistence2.56594보다 크고 joint 최대 오차도0.30437rad 대0.24860rad로 악화했다. 가장 큰 yaw·joint 오차는 최초 접촉 이후 O2 행동137에 있었다. Motor joint RMSE0.00460은 ridge0.01330보다 정확했다. 모든 지표를 평균 RMSE 개선으로 상쇄하지 않는다. p99·bias·max 및 도로별·층별 전체 지표는 JSON에 보존했다. Tail 분위수는 각 도로에 같은 질량을 주는 경험 CDF의 역함수다.

| 제외 도로 / 전이 수 | speed RMSE P → ridge | yaw RMSE P → ridge | joint RMSE P → ridge |
|---|---:|---:|---:|
| T2950 / 314 | 1.55991 → 1.07788 | 0.53480 → 0.25686 | 0.05554 → 0.01492 |
| T2953 / 297 | 1.43056 → 0.98719 | 0.54580 → 0.18207 | 0.05257 → 0.00967 |
| T2956 / 291 | 1.34517 → 0.98597 | 0.47796 → 0.15379 | 0.04354 → 0.00613 |
| T2959 / 264 | 1.42064 → 0.90878 | 0.57546 → 0.17319 | 0.05523 → 0.00797 |
| O0 / 303 | 1.43082 → 0.98090 | 0.51937 → 0.15557 | 0.04737 → 0.00654 |
| O2 / 279 | 1.42188 → 0.96150 | 0.61647 → 0.34916 | 0.06277 → 0.02454 |

최초 contact 전 또는 contact 없는1,237개 전이의 RMSE(speed/yaw/joint)는 P `[1.60648,0.53078,0.04961]` → ridge `[1.00241,0.15972,0.00731]`이다. 최초 contact를 포함하는 네 전이는 별도 분리했다. 이 층의 speed 변화 HUD 표적은 모두0이라 P 오차0인데 ridge RMSE0.82097이다. 양자화와 실제 충돌 변화가 다르므로 좋은 충돌 속도 모델이라고 해석하지 않는다. 최초 contact 후507개에서는 P `[1.36765,0.53380,0.05559]` → ridge `[0.98561,0.27920,0.01739]`다. Contact 판정은 사후 층화이며 입력에 없다.

GT는 held-out 예측 뒤 decoder와 실제 전이 오차를 구분하는 데만 썼다. GT norm speed·hull yaw·front0 joint로 비교했으며 norm speed를 longitudinal velocity로 부르지 않는다. 다음 상태 decoder RMSE는 `[0.74234,0.05408,0.00417]`, 관측 변화와 실제 변화의 차이인 decoder transition noise RMSE는 `[0.97947,0.03117,0.00252]`다. 예측한 HUD 변화와 실제 GT 변화 비교는 P `[0.99255,0.52735,0.05169]` → ridge `[0.22855,0.21533,0.01299]`였다. 이는 Δ over80ms이며 시간으로 나눈 순간 가속도 표적이 아니다. HUD 예측 오차+decoder 변화 오차=실제 변화 예측 오차의 항등식도 검증했다. 두 오차가 상관되므로 RMSE를 더하거나 빼서 기여도를 추정하지 않는다.

관측 행동의 전체 범위는 steer `[−0.39999,+0.38432]`, gas `[0.08293,0.77463]`, brake `[0.01241,0.19826]`이다. **1,748개 모두 gas·brake가 동시에 양수**인296 행동이다. 도로별 표본 수·action min/max/p5/p95/std·동시 pedal 비율을 기록했다. LORO TRAIN의 주변 min/max 밖인 test 행동은 T2950 17개, O2 6개, 나머지0이다. 이들도 원래 관측된 행동이므로 제외하지 않고 평가했다. 주변 범위 안에 있다고 joint state-action 지지나 인과적 action sensitivity가 확인되는 것은 아니다.

319·321의 gas0 / brake≥0.5 개입은 이 학습 행동 범위에 **없다**. 따라서 그 개입을 모델로 계획할 수 있다고 주장하지 않는다. 알려진 행동에서의 한 단계 적합성과 미관측 행동·연속 rollout·translation·충돌·완주 예측은 별개다. 표본은 여섯 알려진TRAIN 정책 궤적이며 하나의 DNF 도로가 포함되고 인접 전이는 상관된다.

저장된 여섯 모델의 TRAIN 통계·normal equation·held-out 예측·motor baseline을 독립 재구성했다. 예측 차이는0, normal-equation 최대 잔차는2.84e−13이었다. Motor 입력 joint를 기존 규칙으로±0.4 clip한23행도 보고한다. 코드·원래 캐시·296·240 rollback·사용자 파일과 기준 main을 보존한다.

새 native·source physics·actor 호출·PPO·유료 자원은 **0**, ridge fit은6이다. 성공한 분석 wall/CPU는37.72/37.57초였다. fit 전 필드 계약 오류 시도의 CPU는 수집하지 못해 전체 시도 CPU로 주장하지 않는다. 실패 시도 fit·native는0이며 중복 fit이나 비용 등록은 없다. 연구 잔여 **395**, 예비 **84,000**과 예산 v331을 유지했다. 모델·원문·픽셀·GT·원시 추적은 공개하지 않는다.

다음 최소 검토는 새 모델이나 controller가 아니라 **기존 실제 개입 캐시가 이 모델의 행동 지지 밖 예측을 검증할 수 있는지 확인하는 것**이다. 가능한 경우 고정된 road-excluded 모델과 이미 측정된 한 action 전이로 반증해야 한다. 이번 단계에서 그 검토·재학습·시뮬레이션은 시작하지 않았다.
