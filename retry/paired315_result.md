315 — paired action 검색 반증과 여섯 TRAIN 평가 완료

**후보 2/6 완주 대 296의 5/6으로 실패했다.** 완주 추가0·손실3이며 공통 두 완주도 평균 **+8.79초** 느렸다. 오프라인 label 오차의 작은 개선과 동시 pedal 제거가 현재 정책의 실제 개선으로 이어지지 않았다. 296과 rollback을 유지하고 새 후보·재튜닝·자동 확대·DEV·승격은 하지 않는다.

기존 315 등록·실행·결과가 없음을 확인하고 시작했다. 현재 legal 관측으로 차체 이동을 예측하는 방향과 306의 pedal 평균화 방향을 검토했다. 185/186은 차체 호·경로 이탈·목표 envelope, 286~289는 whole-path preview·source dynamics·progress/endpoint를 이미 시험했다. 이를 단순 preview 연장으로 반복하지 않았다. 228의 모드 classifier와 강도 회귀, 236의 출력 상호배타화도 보존했다.

차체 방향의 새 캐시 검토는 **286의 고정 운동학으로 실제 296 명령 한 행동의 이동을 예측**하고 저장 300의 실제 변위와 비교한 것이다. 입력은 legal HUD feedback speed·현재 명령·이전 steering memory이며 GT는 변위·slip·joint 평가 라벨에만 썼다. 신규 source 적분 없이 658개 운동학 예측·2,632개 수치 substep을 계산했다.

| 저장 296 trace의 충돌 전 또는 전체 정상 구간 | 한 행동 위치 오차 평균 / p95 | 실제 body 횡속도 평균 / p95 | 이전 명령과 실제 joint 차이 p95 |
|---|---:|---:|---:|
| T2950, 최초 충돌 전183행 | 0.1011 / 0.2095m | 0.4822 / 1.9125m/s | 0.00000539rad |
| T2954, 전체343개 80ms 구간 | 0.0992 / 0.2146m | 0.6380 / 2.0642m/s | 0.00000570rad |

실패·완주 양쪽의 평균 오차가 비슷하고 T2950 충돌 전 joint 추종은 정확했다. 따라서 이 scalar 운동학의 잔차만으로 조향 지연을 실패 원인으로 확정하거나 새 제어 변경을 고르지 않았다. 이 검사는 oriented swept footprint·차체 통과 가능성·steer/pedal 공동 가능성을 검증한 것이 아니다. 상태 식별의 필요성은 남아 있으며, 한 구현의 실패를 방법군 전체 불가능으로 해석하지 않는다.

선택한 단일 가설은 **teacher의 joint pedal 표적을 채널별 평균 대신 실제 관측 사례 하나로 보존하는 paired1NN**이다. 228처럼 mode logits·conditional intensity를 학습하지 않고 236처럼 현재 출력의 크기를 비교해 한 채널을 지우지도 않는다. 306의 새581개 label만 사용해 기존16개 legal feature를 TRAIN 전용 road-balanced 평균·표준편차(std floor1e-6)로 정규화한다. squared Euclidean 거리·k1·정확한 동률의 첫 저장 index를 고정하고, 선택된 teacher의 final gas/brake 쌍을 그대로 반환한다. 새로운 label·teacher/source 질의·metric/k sweep·scale 보정은 없다. 실행 steering·296 nominal memory는 유지한다. 이 표현 차이가 teacher first/future steering 불일치를 해결하지는 않는다.

첫 결과 전에 도로별 leave-one-road-out을 등록했다. 각 fold의 나머지 다섯 도로에서만 정규화하고 같은 held-out 입력을 296·같은 분할의306 residual ridge(λ1, bias penalty0)·paired1NN에 비교했다. road별 gas+brake MAE를 동일 가중 평균해 **두 대조 모두보다 엄격히 낮을 때만** 후보를 구현하도록 고정했다. 임의 최소 개선폭·도로별 veto는 없다.

| road-LOO joint L1 MAE | 값 |
|---|---:|
| 296 final pedal | 0.489641 |
| 같은 fold의 affine residual | 0.444297 |
| paired1NN | **0.442515** |

게이트는 통과했지만 affine 대비 차이는 **−0.001782, 약0.40%**로 작고 여섯 fold 중 세 곳은 더 나빴다. predictive label 오차를 정책 성능이나 다봉성의 인과 증거로 취급하지 않았다. 그 뒤 하나의 full TRAIN index를 고정했다. 기존 registration은 비공개 recipe-plan으로 원형·hash를 보존하고 실행 등록을 별도로 저장했다. 이후 표적·metric·gate를 바꾸지 않았다.

306 저장 픽셀 전체1,754개에서 OFF는 296 행동·features·memory와 정확히 일치했다. ON은 동일한 steering·features·nominal tracker/controller 상태를 보존하면서 **1,754개 모두 pedal이 변경**됐다. 모든 nearest index와 pair를 독립 재계산해 확인했다. OFF/ON의 executor history에는 각자의 반환 pedal이 기록되며 이는 이 정책의 입력이 아니다. ON actor p95는 도로별15.93~30.28ms, 최대117.52ms였고 IPC 최대122.42ms였다. preflight wall68.604초이며 모든 worker를 회수했다. 이 replay는 새 closed-loop 상태의 성능을 대신하지 않는다.

그 뒤 후보 하나를 고정해 기존 여섯 TRAIN을 한 번씩 실행했다. 비교는 **완주 수 우선, 같으면 공통 완주 시간 평균의 엄격한 개선**이다. 추가/손실을 함께 보고하고 damage는 별도 진단이며 veto가 아니다. baseline은 정확한 기존296 결과를 재사용했다. 기술 오류·검열·예산/deadline 중단은 미관측으로 구분하고 정상 DNF로 만들지 않도록 등록했다.

| TRAIN | 296 캐시 | paired1NN | 공식 종료 / native |
|---|---:|---:|---|
| T2950 | 미완주 | 미완주 | off_track / 370 |
| T2953 | 23.80초 | 미완주 | off_track / 180 |
| T2956 | 23.32초 | 31.88초 | 완주 / 399 |
| T2959 | 21.18초 | 30.20초 | 완주 / 378 |
| O0 | 24.32초 | 미완주 | off_track / 249 |
| O2 | 22.36초 | 미완주 | crash / 109 |

여섯 결과 모두 공식 끝점을 관측했다. 실제 DNF4·기술 오류0·검열0·미관측0이다. 공통 완주 차이는 +8.56초·+9.02초이며 평균+8.79초다. 모든1,685개 실제 입력에서 nearest index·teacher pair·반환 pedal·steering 보존을 검증했고 해당 현재 입력의296 출력 대비 pedal도 모두 달랐다. Runtime은 **gas1,290회·brake395회·coast0**, 동시 양수0회였다. 228의 전부 gas 결과와 달리 mode 전환과 brake가 실제 사용됐지만, 현재 기준선의 완주·시간은 개선하지 못했다. 306의0/6 학생보다 성공 수가 많다는 역사적 사실도 296 대비 실패를 뒤집거나 표현 변경 하나의 인과효과를 완전히 분리하지 않는다.

새 비용은 **native1,685/3,880**, source physics·새 teacher 질의·유료 자원0이다. raw step6,737·reset306틱, native screen wall164.257초, runner CPU130.877초·actor CPU28.897초다. 캐시 분석 wall/CPU0.535/1.062초에 여섯 small ridge 대조 solve와 고정 index 구성을 포함했다. neural/classifier 학습은 없다. 준비·검토·게시 시간을 실행 비용에 포함했다고 주장하지 않는다.

**누적1,243,805 + 연구 잔여2,195 + 예비84,000 = B1,330,000**이다. reserve 사용0이며 v322 비용 원장에 실제 비용을 반영했다. 313 행동 불변,314의 제한적 도로 지지 증거와 모든 과거 실패를 보존한다. 296·240 rollback·main·Participants·기존 백업·개인 원문은 변경하지 않았다. model/index·label·ZIP·seed·픽셀·개별 trace는 비공개이며 공개물은 일반 코드와 집계다.

남은 연구 질문은 단순 mode 제거보다 **legal 상태의 식별 가능성과 teacher/student 제어 결합**이다. 현재16개 feature와 짧은 과거 관측이 실제 sideslip/yaw/actuator 상태를 예측하는지의 캐시 검증은 248의 HUD pedal imitation과 구별된다. 이번 고정 계획을 그 방향으로 사후 변경하거나 새 fit·source·native를 시작하지 않았다. oriented swept footprint를 도입하려면 그런 상태 예측과 공동 실행 가능성의 증거가 먼저 필요하며 큰 계산량을 자동 확대하지 않는다.

[고정 캐시 반증](paired315_cache.py) · [실제 paired 검색 정책](paired315_agent.py) · [단일 후보 실행](paired315_execute.py) · [집계·비용](paired315_result.json)
