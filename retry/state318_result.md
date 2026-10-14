318 — legal 상태 식별 가능성의 기존 캐시 검증 완료

**직전 3개 이력은 전방 속도·joint angle 예측을 개선했지만 전체 횡속도·yaw RMSE는 악화했다.** 악화는 하나의 실패 도로와 충돌 이후 구간에서 컸다. 현재 픽셀의 기존 HUD yaw·wheel-angle proxy는 두 ridge보다 훨씬 정확했다. 상태 예측의 제한적인 정보와 표현 누락을 확인한 결과이며 제어·완주 성능 개선으로 주장하지 않는다. 새 native·source simulation·actor 평가·PPO 학습은 0이다.

시작 전 318 등록·실행이 없음을 확인했다. 317의 B/C 실패와 현재296을 보존하고 critic/PPO 실험을 반복하지 않았다. 표적·좌표·입력·분할·λ·평가 정의를 결과 전에 고정했다.

306의 기존 여섯 TRAIN 전체에는 각 action 직전 GT snapshot·legal16 feature·픽셀4×84×84·최종 실행 action이 있었다. **1,754행 전부** 시간 정렬이 확인됐고 제외·누락은0이다. Snapshot feature/action은 저장 trace·픽셀 cache의 action과 정확히 같았고 previous action·pre-damage는 이전 POST-step과 일치했다. 관측 stack의 시간 shift도 정확했으며 pre-action 간격은80ms, 최대 오차1.71e−15초였다. 300의 T2950 중복 trace는 GT 표적의 최대 차이0으로 교차 확인만 했고 학습 표본을 늘리지 않았다. 300 T2954는 고정 여섯 도로 밖이므로 추가하지 않았다. 315의 실제1,685행에는 정렬 가능한 pre-GT가 없어 제외했으며 다른296 궤적의 같은 step 표적을 전용하지 않았다.

| 고정 표적 | 정의·단위 |
|---|---|
| 전방 속도 | Hull local+y, `−sin(angle)*world_vx+cos(angle)*world_vy`, m/s |
| 우측 횡속도 | Hull local+x, `cos(angle)*world_vx+sin(angle)*world_vy`, m/s |
| yaw rate | Hull angular_velocity, 반시계방향 양수, rad/s |
| 실제 steering angle | 앞바퀴0 joint.angle, hull에 대한 실제 signed angle, rad |

Hull angle·velocity와 joint angle은 표적 복원에만 사용했다. A 입력은 현재 legal16, B는 현재16+lag1/2/3의16 feature+lag1/2/3 실행 action3+유효 mask3으로 **76개**다. Reset 이전이나 미래 관측은 채우지 않았고 없는 lag는0·mask0으로 표시했다. 각 history는 같은 episode의 연속80ms pre-observation만 사용했다. HUD state proxy도 ridge 입력에는 추가하지 않았다.

여섯 road의 leave-one-road-out에서 A/B를 fold당 한 번씩 적합했다. 총12번의 multioutput solve이며 별도 full fit·입력 탐색은 없다. λ1·bias penalty0·TRAIN 전용 weighted mean/std(std floor1e−6)·TRAIN road 동일 가중치를 같게 했다. 같은 road의 인접 행이 train/test에 나뉘지 않는다. 아래 road-balanced RMSE는 `sqrt(mean_road MSE)`, MAE·bias는 road별 값의 동일 가중 평균이다. 서로 다른 단위의 표적을 임의로 하나의 loss로 합치지 않았다.

| 표적 | A 현재16 RMSE | B history76 RMSE | 단순 proxy RMSE |
|---|---:|---:|---:|
| 전방 속도 m/s | 0.752557 | **0.487722** | 0.760960 |
| 우측 횡속도 m/s | **0.435303** | 0.482042 | 0.873696 |
| yaw rad/s | 0.934969 | 1.328552 | **0.053990** |
| front0 joint rad | 0.038871 | 0.022367 | **0.004167** |

| 표적 | A MAE / bias | B MAE / bias | proxy MAE / bias |
|---|---:|---:|---:|
| 전방 속도 | 0.633388 / −0.006587 | 0.354922 / −0.017038 | 0.651843 / +0.044998 |
| 횡속도 | 0.172787 / −0.033282 | 0.147931 / −0.042037 | 0.548274 / +0.129354 |
| yaw | 0.262211 / +0.081522 | 0.266683 / +0.129130 | 0.042489 / −0.014909 |
| joint | 0.005656 / +0.003204 | 0.004825 / +0.000495 | 0.003005 / −0.000906 |

전방 proxy는 현재 legal HUD **norm speed를 전방 속도로 간주**한 값이며 두 물리량이 본래 같다는 가정은 하지 않는다. 횡속도 proxy는 관측값이 아닌 **0 null prediction**이다. Yaw/joint는 수정·재보정 없이 기존248의 current-pixel HUD decoder를 사용했다. 별도의 norm-speed 기준으로 실제 `hypot(v_forward,v_lateral)`과 비교하면 legacy speed RMSE2.684871m/s, HUD norm speed RMSE0.760533m/s였다. 실제 joint에 대한 `−previous steering command` 기준은 RMSE0.013459rad·MAE0.000829rad로, 낮은 평균 오차에도 드문 actuator 차이가 남는다.

| 진단 구간 | road / 행 | 전방 RMSE A→B | 횡속도 RMSE A→B | yaw RMSE A→B | joint RMSE A→B |
|---|---:|---:|---:|---:|---:|
| 완주 궤적 | 5 /1,439 | 0.718765→0.433218 | 0.236597→0.197938 | 0.344493→0.298255 | 0.012942→0.011883 |
| DNF 궤적 | 1 /315 | 0.902738→0.699175 | 0.925765→1.094665 | 2.156762→3.185204 | 0.090709→0.047914 |
| 최초 충돌 전·무충돌 | 6 /1,243 | 0.716444→0.400608 | 0.177309→0.143753 | 0.252064→0.175473 | 0.008054→0.011074 |
| 최초 충돌 후 | 4 /511 | 0.812196→0.667763 | 0.749909→0.870455 | 1.701624→2.489286 | 0.071379→0.037102 |

충돌 상태는 현재 action의 미래 충돌을 사용하지 않고 **직전 action까지의 최초 충돌 이력**으로 구분했다. 최초 충돌 action 자체의 입력은 아직 충돌 전이다. 각 구간에서도 road 가중치를 같게 했고, 구간별 활성 road 집합이 달라 전체 수치의 단순 합으로 해석하지 않는다. 모든 구간의 MAE·bias·proxy·fold별 결과는 JSON에 보존했다.

완주한 다섯 held-out 도로에서는 B가 네 표적 RMSE를 모두 줄였지만, 실패한 T2950에서 횡속도·yaw의 큰 오차가 전체 결과를 바꿨다. 이는 고정 선형 모델·이 캐시의 외삽/표현 문제와 일치하는 관찰이며 유일한 원인을 확정하지 않는다. History가 일반적으로 부족하거나 충분하다는 증명도 아니다. 특히 실제 yaw/joint 정보는 이 캐시에서 **현재의 합법 HUD만으로 더 정확히 읽을 수 있었다.** 248의 HUD pedal imitation 실패를 이 물리 관측의 부재·무용함으로 확대해서는 안 된다. 그렇다고 그 proxy를 넣은 새로운 controller가 개선된다는 뜻도 아니다.

실제 비용은 **12 multioutput ridge solve, wall13.836초·CPU13.816초**이며 parsing·proxy 계산·캐시 비교·fit·집계를 포함한다. 새 native·source physics·actor 호출·PPO update·유료 자원은0이다. Raw GT·snapshot·픽셀·계수·개별 예측은 비공개로 유지한다.

**누적1,263,220 + 연구 잔여2,969 + 예비84,000 = B1,350,189**을 유지하고 v324 원장은 변경하지 않았다. 296·240 rollback·317 실패·main·Participants·기존 backup·개인 원문을 보존한다. DEV/HOLDOUT/SEALED·승격·자동 확대·더 긴 history·추가 신경망·입력 탐색은 없다. 캐시가 여섯 road의 표적을 제공했으므로 이번에 추가 관측 수집이나 주행 예산을 제안·집행하지 않았다.

[시간 정렬·좌표·고정 LOO 코드](state318_fit.py) · [전체 표적·proxy·구간·비용](state318_result.json)
