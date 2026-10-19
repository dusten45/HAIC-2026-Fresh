586 보존 기록 종료 보고

국소 s300 연속 통과 시간은 12.782μs 개선됐지만 전체 검증은 raw312의 REFERENCE 위반으로 실패했다. 사용할 수 있는 새 완주 정책이나 승격 결과는 없다. 최적화는 호출 예산에 걸려 중단됐으므로 수렴, 최적성 또는 설계 공간 전체의 불가능성을 뜻하지 않는다.

승인 시간의 미해결 차이: 현재 전달된 요청은 2026-10-16 19:01:55 KST에 승인이 끝나며 자동 연장을 금지한다. 보존된 586 계약은 2026-10-19에 등록됐고 deadline을 2026-10-20T10:01:55Z로 기록한다. 현재 확인 가능한 요청만으로 이 연장을 입증할 수 없다. 이 보고는 기존 파일의 종료 정리이며 추가 시뮬레이션, FD, 최적화, replay를 실행하지 않았다. 아래 과학 결과와 계산량은 이미 존재하던 기록의 집계다. 계약 원본의 날짜는 수정하지 않았다.

실험 계약과 선행 게이트

577의 검증된 명령열을 기준으로 hold25..49의 조향과 signed pedal을 각각 열어 50좌표를 구성했다. hold당 4raw이며, raw96의 독립 전체 checkpoint에서 시작해 변경 구간 이후 hold50..63은 577 그대로 유지하고 raw252까지 확인했다. 초기 상태에서 실행한 positive control 252raw의 전체 행과 checkpoint가 저장된 기준 기록과 정확히 같았다는 감사 결과가 있다. 관측된 부분 궤적만으로 합격시키지 않았고 최초 엄격 안전 위반에서 각 후보를 중단했다.

SLSQP maxiter3, ftol1e-9, 좌표 scale 조향0.02/pedal0.1, 정규화 FD 간격0.001, 물리적 float32 경계, 실제 명령 bytes 기준 cache를 실행 전에 고정했다. 원래 표현 가능한 seed를 유지했다. 제약은 156행×11성분과 terminal2개이며 미관측 성분은 불합격 residual이다. exact source 안전 판정이 최종 자격을 결정한다. 목적은 고정 s300 평면의 첫 유효 전진 통과 시각이고 통과 hold 전체의 안전을 요구했다. 개선 비교의 32ULP는 수치 분해능이며 성능 승격 기준을 대신하지 않는다.

국소 개선 후보 하나에만 초기 상태부터 고정 잔여 명령을 사용한 전체 검증을 허용하고, 전체 안전 완주에만 독립 replay를 허용했다. DEV 작업이며 HOLDOUT/SEALED/native는 0이다.

실제 탐색과 관측

예약 슬롯128 중 최초 계측 오류로 소비된 슬롯1을 유지해 실제 suffix127개를 평가했다. FD114개, 공동 제안13개였고 완전 안전·유효 후보는81개였다. 실패는 PATH25, FORCE14, CLIP_HISTORY1, FOOTPRINT6개였다. Jacobian 두 개의 50열과 세 번째의14열을 계산했으며 초기 source 이전 중단 batch도 기록에 남았다. cache 요청151개 중 hit22개, 예약된 miss128개와 마지막 cap 차단 요청1개를 구분한다.

최선 case23은 50좌표 중 signed pedal 한 좌표만 바뀌었다. 최대 절대 pedal 변화는 0.00010000169277191162, 조향 변화는0이다. 전체50좌표 벡터는 저장소 밖 비공개 `coordinate-changes-private.json`에 보존했다(SHA256 `41c1515ca8d9661a3f14f46501f79de4ac70a0437d4e9adf9c80327aee4a2e56`). 원시 상태와 명령열도 비공개로 유지했다.

초기 hold25..34는 선택 후보에서 전혀 바뀌지 않았다. raw100/112/120/124/128/132/136의 yaw, lateral, joint, rear angular velocity, pedal, clip, margin 차이는 모두0이었다. 따라서 더 이른 준비 동작을 개선했다는 증거가 없다. 공동 제안은 최대40좌표를 바꿨지만 안전 제안은3개이고, 그중 최선 case114의 s300 시각4.947291276779136초는 기준보다 약0.476036ms 느렸다. 이 예산 내 결과를 공동 계획 전체의 불가능성으로 확대하지 않는다.

| 관측 평면 | 기준(초) | 선택 후보(초) | 개선 | 기준/후보 raw bracket |
|---|---:|---:|---:|---|
| s200 | 3.851288680188803 | 3.8512794384258977 | 9.242μs | 모두 [192,193] |
| s300 | 4.946815240723051 | 4.946802458348053 | 12.782μs | 모두 [247,248] |

두 통과 hold는 국소 평가에서 전체 안전했다. raw248의 기준 대비 변화는 progress +0.0011723921, speed +0.0004810325, lateral +0.0014479019, yaw −0.0000012535, joint0, rear angular velocity +0.0008907992, margin +0.0021797655, clip0이었다. 작은 연속 시간 이득에도 정수 raw bracket은 그대로다.

전체 검증과 승격 판정

선택 후보만 초기 상태부터 한 번 전체 검증했다. raw97..252는 선택 suffix의 전체 행과 정확히 일치했다. raw312(hold78의4번째 raw)에서 reference overspeed가 4.850088865525279m/s로 엄격한 상한4.85m/s를 0.000088865525279m/s 초과했다. 저장된 기준의 동일 raw 값은4.849662631665311m/s였다. 실패 시 margin5.133982598494977m, path error0.2931205220921774m이며 다른 실패 판정은 없었다. 이는 변경 상태에 고정577 잔여 명령을 적용한 검증의 실패다. 피드백으로 회복할 수 없다는 판정은 아니다.

전체 안전 완주 게이트를 통과하지 못해 독립 replay는0회다. 실제 incumbent13.66초와 source incumbent13.20초를 유지했고 자동 승격은 없다. 새 학습·새 world·별도 유료 자원 사용도0으로 기록됐다. 연구 잔액22,758, reserve84,000/사용0의 기존 집계는 변경하지 않았다.

비용과 검증 증거

| 항목 | 실제 | 고정 상한 |
|---|---:|---:|
| attempted raw | 17,154 | 22,000 |
| completed model ticks | 17,139 | 22,000 |
| geometry checks | 17,268 | 22,500 |
| external force calls | 68,616 | 90,000 |
| internal force calls | 68,556 | 90,000 |
| total force calls | 137,172 | 180,000 |
| 정리 포함 CPU | 496.809303452초 | 900초 |
| 정리 포함 wall | 536.070255589초 | 1,200초 |

source 단계는 positive252, suffix attempted16,590/completed16,575, whole312이며 replay0이다. geometry에는 completed 외 초기 root 검사129개(positive1+후보127+whole1)가 포함된다. 테스트·toy solver·등록·오류·복구·감사 비용을 누적했다. runtime CPU491.647537834초/wall530.900503375초에 source0 정리 및 보수적 보조 비용을 더했다. 전체 audit CPU10.429209256초/wall10.439385288초로 단계 상한15/25초 이내다. 다른 단계 상한도 보존 감사에서 모두 통과했다. 보존된 테스트 최종 시도는11개 통과이며 실패한 첫 시도의 비용도 남아 있다.

두 journal의120,518개 이벤트, 연결 hash, force/적분/geometry 계수, 원본 수학 의존성, 복구 구현, seed와 positive identity, private vector 분리 검사가 모두 통과했다. 별도 읽기 검토에서도 결과 해석과 계수의 치명적 불일치는 없었다. 정리 시 main은 `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`이며 Participants와 기존 추적 파일에 대한 변경은 없다.

기술 오류와 보존

연결 점검은 source 이전이었다. 이후 첫 실행은 positive252 이후 첫 FD source 및 첫 과학 QP 이전에 journal의 `kind` 인자 충돌로 중단됐다. 메타데이터 필드 두 곳만 바꾼 복구가 원래 입력·checkpoint·의존성·journal 연결을 입증하고 동일 초기화 지점에서 재진입했다. positive와 suffix source를 중복 실행하지 않았으며 소비된 슬롯과 첫 실행 비용을 보존했다. 원래 코드와 실패 집계도 남겼다.

과학 실행과 runtime audit 이후 최종 집계 게시가 기존 파일 때문에 FileExistsError로 실패했다. 원시 후보/whole/journal/비용은 보존됐으며 임시 집계 파일은 정리되어 남지 않았다. `shoot586_closeout.py`가 보존 자료로 집계만 재구성했고 result에 `publication_technical_error`와 `final_aggregate_reconstructed_source0`를 명시했다. 이 과정의 추가 source/FD/solver는0이다.

주요 자료는 `shoot586_contract.json`, `shoot586_recovery_contract.json`, `shoot586_result.json`, `shoot586_analysis.json`, `shoot586_cost.json`, `shoot586_events.json`이다. 실패 원본과 게시 오류는 별도 파일로 보존했다. 다음 조치는 종료 기록 보존이며 새 실험을 자동으로 시작하지 않는다. 승인 기간 차이는 미해결 관리상 제약으로 남긴다.
