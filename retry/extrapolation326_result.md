# 326: 고정325 모델의 실제 개입 캐시 검증

**절대 전이 RMSE 개선은 남았지만 행동 변화 반응은 MPC 확대를 뒷받침하지 못했다.** 같은 reset에서 조향을 바꾼 두 비교에서 ridge는 yaw 방향을 맞췄으나 변화 크기를 과대 예측해 persistence보다 반응 오차가 컸다. Joint 반응은 persistence보다 좋지만 기존 motor 식보다 부정확했다. 큰 제동 pulse는 원시 픽셀이 없어 여전히 미검증이다. 모델·controller·actor를 변경하거나 새 시뮬레이션을 실행하지 않았다.

먼저 저장 가용성을 확인했다. 319/320/321/322의 실제 실행은 각각6/12/6/15개, 총 **39개**이며 원시 픽셀 파일이0개였다. Trace의 HUD audit·영상 hash는 픽셀을 대신하지 않았다. 따라서 baseline·steering-only·brake-only·joint pulse의 endpoint를 다른 실행의 같은 step에서 가져오거나 복원하지 않았다.

이전 실제 캐시에서는 291의12개 pixel 궤적과245·246의4개 궤적을 찾았다. 결과 전에 **8개 궤적**을 선택·등록했다. 325와 geometry가 정확히 같은 O0/O2의 baseline240·frozen290 네 궤적이 주 비교다. 남은291 신규 도로 네 개의8개 궤적은 주 비교를 기존 LORO 모델로 제한하기 위해 사용하지 않았다. S1의 baseline·gas-only·brake-only·두 pedal 변경 네 궤적은 별도 보조 비교다. 이 선택은 모델 오차를 확인하기 전 이루어졌다.

O0/O2에는 해당 도로를 제외한325 LORO 모델만 사용했다. S1은325의 여섯 학습 도로와 다른 geometry이며 full fit 파일이 실제로 없었다. 추가 fit 대신 기존 여섯 fold 예측의 **동일 가중 평균**을 보조 평가 정의로 사전 등록했다. 이 평균은 full fit이나 여섯 독립 모델 검증으로 부르지 않는다. 모든 normalization·계수·모델 hash를 보존했다.

각 궤적의 실제 pre-action 픽셀과 바로 다음 pre-action 픽셀만 연결했다. 관측 stack shift·초기 full pixel hash·실행 명령·80ms 간격을 검증했고, 마지막 행동 뒤 픽셀이 없는8개 endpoint는 제외했다. 총 **2,474개 전이**이며 주 비교1,508개, S1 보조966개다. 두 frozen290 실제 DNF 궤적과 S1의 세 고정 prefix censor를 그대로 포함했다. Censor를 DNF로 바꾸거나 실패 뒤 전이를 보간하지 않았다.

HUD decoder와 persistence·motor 기준은325 그대로다. 각 그룹에서 도로마다 같은 가중치, 같은 도로의 각 궤적에도 같은 총 가중치를 주었다. S1과 O0/O2는 모델 정의가 달라 합산하지 않았다. 각 열의 단위는 speed m/s, yaw rad/s, joint rad이다.

| 절대 next-HUD RMSE | Speed | Yaw | Joint |
|---|---:|---:|---:|
| O0/O2 persistence | 1.76950 | 0.50280 | 0.04671 |
| O0/O2 고정 ridge | **1.44586** | **0.31430** | **0.01031** |
| O0/O2 motor/kinematic | 1.76950 | 0.37175 | 0.00480 |
| S1 persistence | 2.39448 | 0.46000 | 0.04175 |
| S1 고정 여섯 모델 평균 | **2.26472** | **0.44665** | **0.01166** |
| S1 motor/kinematic | 2.39448 | 0.30501 | 0.00729 |

두 그룹 모두 persistence 대비 세 RMSE는 낮지만 모든 오차가 개선된 것은 아니다. Speed MAE는 주 비교0.89925 → 0.91811, S1 0.81995 → 0.99628로 증가했다. S1 yaw p95도0.93239 → 1.28612로 증가했고 motor0.44353보다 컸다. 주 비교 yaw·joint 최대 오차도 ridge에서 더 컸다. 모든 MAE·bias·p95·p99·max·궤적별 지표를 JSON에 남겼다.

동일 pre-state의 action 차이 대조는 **reset의 첫 행동만** 사용했다. O0/O2의 baseline 대 steering+0.015 두 pair, S1의 baseline 대 gas-only·brake-only·두 pedal 변경 세 pair다. Initial full pixels·case·이미 실행한 action0개를 확인했다. 이후에는 이전 action이 달라졌으므로 HUD나 같은 step이 일치하더라도 동일 물리 상태로 간주하지 않았다. 실제 steering+pedal 동시 joint factorial과 큰 brake pulse의 원시 픽셀 pair는 없다.

| 두 조향 pair의 반응 MAE | Speed | Yaw | Joint |
|---|---:|---:|---:|
| Persistence | 0 | **0.05035** | 0.01716 |
| Ridge | 0.01811 | 0.07833 | 0.00337 |
| Motor/kinematic | 0 | **0.05035** | **0.00216** |

두 pair의 관측 yaw 변화는 모두−0.05035, joint 변화는−0.01716이었다. Ridge는 yaw·joint의 비영 반응 부호를2/2씩 맞췄지만 yaw 변화는−0.12173/−0.13562로 과대 예측했다. 관측 speed 차이는0인데 비영 speed 차이를 예측했다. 방향 정답을 크기 예측의 성공으로 바꾸지 않는다.

S1 첫 행동의 gas 변화는약0.000948, brake 변화는약0.00000592로 매우 작았다. 세 pair의 실제 post-HUD 차이는 세 채널 모두0이었고 persistence·motor는 이를0으로 예측했다. Ridge 반응 MAE는 `[0.003071,0.0001194,0.00000259]`였다. HUD에서0이라는 것은 물리 반응이 정확히0이라는 뜻이 아니다. 비영 반응 표본이 없으므로 S1 방향 정확도는 분모0으로 남겼다. 다섯 pair는 reset의 작고 편향된 표본이며 고속·접촉 상황의 action sensitivity를 입증하지 않는다.

접촉 가용성도 구분했다. S1에는 실제 collision flag가 있어 contact8개·noncontact958개를 별도 집계했다. 291의1,508개 전이에는 direct collision flag가 없어 **unknown**으로 남겼다. 저장 damage 증가9개는 별도 proxy이며 나머지를 직접 확인된 무접촉으로 꾸미지 않았다. 첫 조향 pair는 flag unknown·damage 증가0, S1 첫 pedal pair는 직접 무접촉이다. 접촉 중 동일 pre-state의 paired 개입 검증은 없다.

원래325 학습 주변 action 범위 밖인 전이는 O0 baseline6·macro122, O2 baseline4·macro64, S1 네 궤적3/22/22/3개였다. 실제 macro 캐시에는 gas1·brake0 등이 있었지만 **gas0 / brake≥0.5**의 큰 제동 pulse 원시 endpoint는 없다. 주변 범위를 벗어난 실제 행동에서 절대 예측을 평가한 것과, 임의 state-action의 인과적 응답을 정확히 계획하는 것은 다르다. 지원 밖 성능을 새로 추정해 채우지 않았다.

여덟 궤적의 저장 예측을 고정 모델로 독립 재계산해 차이0을 확인했다. 모든 입력·모델·계수 hash와296·240 rollback을 보존했다. 새 native·source physics·fit·actor 호출·PPO·유료 자원은 **모두0**이다. 분석 wall/CPU는1.289/1.285초이며 비용 원장은 한 번 기록했다. 연구 잔여 **395**, 예비 **84,000**과 예산 v331을 유지했다. 새 DEV/HOLDOUT/SEALED나 champion 변경은 없다. 원시 픽셀·GT·비공개 trace·모델·개인 자료는 공개하지 않는다.

판단은 **MPC/controller 확장 보류**다. 관측 적합만으로 행동 변화의 정확성을 주장할 수 없고, 핵심 큰 제동 개입의 픽셀 부재도 남았다. 이번 캐시 전용 범위에서는 이 부재를 새 실행으로 메우지 않았다.
