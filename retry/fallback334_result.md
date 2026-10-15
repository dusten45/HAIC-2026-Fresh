334의 고정 fallback 회전·이동 식을 저장 TRAIN 관측에서 검증했다. OFF 저장 기록 1970행을 재현했고, 출생 시 실제 fixture와 유일하게 대응되는 점의 이동 오차와 중복은 줄었다. 그러나 전체 최근접 대응에는 미해결 검출점이 많고 실제 가림 보존 증거가 없어 승격하지 않았다. native·새 학습·source physics rollout은 모두 0이다.

식은 사전에 고정했다. HUD yaw는 CCW 양의 rad/s이며 `Δψ=.08×(이전 yaw+현재 yaw)/2`, `d_old=(0,현재 HUD 속도×.08)`, `p_next=R(-Δψ)(p_old-d_old)`다. 기존 `previous_image`에서 이전 yaw를 읽으므로 새 학습 상태나 계수는 없다. 속도 평균·횡이동 모델·confidence/threshold fitting을 추가하지 않았다. metric x 오른쪽/y 전방, 기존 pixel 원점·y 반전·비등방 scale, 순수 회전·직진·원점·역변환의 대수 검증을 통과했다. 첫 reset frame 9개는 interval에서 제외했고 서로 다른 episode·reset stack 복제·시간 gap을 연결하지 않았다.

승인된 optical affine 변환은 그대로다. 같은 영상 interval에서 양쪽 모두 운반할 점이 있을 때 optical 분기가 일치했고, 공통 승인 행렬 596개가 bit exact였다. 단일 interval에서 승인 optical 출력도 완전히 같았다. 순차 OFF/ON의 승인 수는 646/601이며, 원래 `hazards` 존재 여부 gate가 보존·중복 제거 결과에 따라 달라진 interval이 65개였다. 승인 optical을 HUD 회전으로 바꾼 323의 실패와 구별된다. 수정 archive는 기존 archive와 temporal fallback 한 파일만 다르다.

| 등록한 저장 증거 | 픽셀 입력 | 실제 pose/obstacle GT | 가림 label |
|---|---:|---|---|
| 기존 6 TRAIN 수집 궤적 | 1754 | 모든 preaction 입력; 연속 interval1748 | 없음 |
| 333 B N2 | 72 | 모든 입력 pose; 장애물은 기록된 static fixture 계약 | 없음 |
| 330=331 A N2 | 72 | 실제 경계64–71만; 별도 GT8개 | 없음 |
| 331 B N2 | 72 | 실제 경계64–71만; 별도 GT8개 | 없음 |

330과 331 A는 한 궤적으로 셌다. N2의 공통 interval은 동일 픽셀과 원래 초기 tracker state로 중복 제거하고, GT가 있는 333 기록을 우선했다. 없는 331 초기 GT를 만들지 않았다. 기존296 N2 성공에는 363행 trace만 있고 픽셀·pose GT가 없다. 더 오래된 O0/O2 240·290 계열 4궤적에는 픽셀1512개가 있지만 해당 trace schema에 pose GT가 없으며, 이번에 고정한296/330 archive 평가에는 넣지 않았다. 오래된 파일의 상대 경로를 잘못 확인한 목록 값은 수정하고 이전 목록과 복구 기록을 보존했다. 전체 옛 버퍼나 보호 split을 재개·개방하지 않았다.

OFF 전체 재현 후 두 평가를 분리했다. 단일 interval은 같은 OFF 초기 hazard·같은 검출·같은 optical 결과에서 fallback만 바꿨다. 순차 ON은 고정된 실제 픽셀열에서 원래 controller의 메모리 갱신을 계속하며, 저장된 물리 명령을 observer history로만 유지했다. ON이 계산한 명령을 시뮬레이터에 실행하지 않았으므로 물리 closed-loop가 아니다. 검출·radius·age·expiry·dedup·routing·controller 법칙과 기존 모델 계수는 유지했다.

최근접 GT를 임의로 물리 identity라고 부르면 큰 오차를 잘못 해석할 수 있었다. 기존6에서는 원래 최근접 single-interval 후보1324점 중 출생 시 기록된 실제 circle fixture 내부에 유일하게 들어가는 lineage가664점(50.2%)이었다. N2는65점 중44점이다. 출생 검출464개 중92개는 어떤 실제 fixture에도 대응되지 않았다. 이들을 단순 제거해 원래 집계를 숨기지 않았다. 원래 최근접 거리·둘째 후보 margin·age·tail·coverage 집계를 그대로 보존했다.

추가 기하 감사는 사후 분석으로 표시했다. 출생 검출 중심이 실제 fixture의 물리 반경 안에 유일하게 포함될 때만 identity를 부여하고 기존 age/dedup lineage로 운반했다. 미래 GT로 identity를 다시 붙이지 않았고, GT가 없거나 기하가 맞지 않는 출생은 unknown으로 유지했다. 이는 학습한 신뢰 임계값이나 visibility label이 아니다.

| 같은 초기 점의 fallback 오차(m), fixture 출생 대응 subset | OFF | ON |
|---|---:|---:|
| 기존6 도로 균등 평균,98점 | 4.640 | 2.752 |
| 기존6 p95 / p99 | 12.711 / 19.486 | 9.842 / 13.674 |
| 기존6 최대 | 24.301 | 19.261 |
| N2 평균,17점 | 3.360 | 2.608 |
| N2 p99 | 12.981 | 11.445 |

이 subset의 도로별 평균은 기존6 모두 감소했다. 기존6에서 이전 age0 점의 첫 fallback 평균은3.084→0.585m, 이미 aged인 점은6.226→4.693m였다. contact 전/후 subset 평균도 각각5.001→2.865m, 3.119→1.942m였다. 잘못 운반된 초기 상태를 한 interval 식으로 완전히 복구하지는 못했다.

고정 픽셀 순차 replay의 같은 출생 대응 subset에서는 기존6 전체 오차 평균이2.247→0.686m, p99가19.486→6.403m였다. 하지만 잔존 점 수가664→495로 달라지므로 이 값만으로 paired 개선이라 부르지 않는다. 대응에 기반한 중복 point-frame은217→47, age8 평균 오차는10.113→5.129m지만 age8 점 수도15→4였다. lineage의 누적 오차 적분 평균은0.647→0.166m·s였으며, 이 역시 살아남은 point-time 표본 집계다.

반대로 기하 미해결 점까지 포함한 원래 최근접 순차 평균은24.400→25.294m로 나빠졌다. 원래 single fallback 최근접 RMSE도44.439→44.721m였다. 이 수치와 사후 subset의 개선을 함께 기록했다. 나쁜 optical 또는 미해결 검출에서 생긴 큰 오차를 이번 fallback 수정으로 모두 해결했다고 주장하지 않는다.

독립 viewport 기하상 기존6의 장애물 중심이 ROI에 있는 instance378개에서, 대응된 현재 검출이 없는 경우는7개, 현재 검출 없이 보존된 경우는양쪽 모두 같은6개 frame이었다. no-known-track 상한은양쪽1, 실제 누락 하한은0이다. unknown 대응이 있어 누락을 확정할 수 없다. N2 ROI23개에서는 현재 검출 없는 보존 사례가 없었다. 따라서 미검출을 실제 가림으로 간주하지 않으며 **가림 장애물 보존은 미검증**이다.

일부 downstream 변화도 있었다. 단일 interval steering readout은 기존6에서33개, N2의 중복 포함 세 궤적에서6개 입력이 달랐다. 순차 steering은 기존6에서378개, N2에서21개가 달랐다. 이는 고정 픽셀에서 나온 출력 차이다. N2의 첫 계산 명령 차이는66번째였지만 다른 도로에서는 페달이 steering보다 먼저 달라지기도 했다. 333의 steering66 한 번 변경에서 contact68은 같고 지속5→1·damage1→0.2·crash72→생존이었던 국소 증거와 이번 전체 tracker replay를 혼동하지 않는다.

고정 식의 GT motion 진단도 별도로 남겼다. 기존6의 yaw 적분 절대오차 평균은0.00586rad, 횡이동을0으로 둔 오차 평균은0.199m/interval이었다. N2에서는 전방 이동 오차 tail이 커졌다. 이 증거로 식을 조정하거나 속도 평균·lateral 보정·confidence fitting을 추가하지 않았다.

OFF/ON 저장 actor 각1970회, 총3940회이며 actor CPU42.027초, replay evaluator CPU9.392초, 전체 replay wall61.099초였다. 기존 optical pipeline1603회를 재사용했다. affine estimator만의 호출 수는 따로 계측하지 않았고, 새 registration 방법이나 학습 fit은 없다. paired routing310회와 집계 CPU7.228초, 사후 correspondence 감사 CPU1.807초, 독립 saved-evidence·motion 검증 CPU4.721초를 기록했다. 초기 목록화·build·최종 보고 등 미계측 범위도 비용 기록에 명시했다.

다음 최소 closed-loop 검증은 제안만 남겼다. 기존 exact330/331 A72를 재검증해 재사용하고, 새 B 한 번을 fallback-only 정책으로 reset부터 최대72행동 실행하는 계약이다. 캐시의 공통 prefix65와 이후7행동을 모두 비용에 포함한다. 현재 연구 잔여0이므로 별도 연구예산 상한72가 필요하며 예비84000을 쓰지 않는다. A 증거가 불명확하면 새 A72+B72 상한144를 별도 등록해야 한다. 이번 작업에서는 추가 예산이나 native 실행을 등록하지 않았다.

실행 전 OFF·좌표·시간·optical·설정 게이트를 다시 통과하고 가림/대응 범위를 명시한다. 불일치·공식 종료·72 cap·승인 종료 시각에 중단하고 재시도·재시드·sweep을 하지 않는다. 동일/악화는 이 후보의 국소 충분성만 반증한다. damage 증가는 독립 자동 veto가 아니며 first contact·지속·fixture·종료·pose·speed·고유 진행량을 함께 비교한다. 72 생존은 완주나 일반 정책 개선이 아니다.

누적 native1282127·연구 잔여0·최종 예비84000, champion296, TRAIN registry, 원본·사용자 변경, main·backup·Participants와 DEV/HOLDOUT/SEALED를 보존했다. 정적 결과로 승격하지 않았고 자동 horizon 확대도 없다. 비공개 문서·원시 GT·픽셀·모델·private seed는 공개하지 않았다. 승인 종료는2026-10-17 19:01:55 KST이며 자동 연장은 없다.
