# 485 — 신규 DEV 준비 gate에서 종료

**승인된 단 한 번의 시도는 `PREPARATION_INELIGIBLE`로 종료했다. 순위 가설의 검증 결과는 NO_INFORMATION이다.** 첫 조건의 동결된 geometry solver가 feasible 경로를 만들지 못해 공통 quarter-root, source gate, 두 arm 비교에 도달하지 못했다. 조건 교체·seed 재추출·위치 구제·상한 완화·추가 실행은 하지 않았다. 두 번째 조건은 identity만 동결했고 native 준비를 시작하지 않았다.

## 실제 수행과 비용

| 항목 | 실제 |
|---|---:|
| 동결한 신규 DEV / native로 연 조건 |2 / 1|
| actual wrapper 행동 / reset |0 / 1|
| reset raw / action raw ticks |51 / 0|
| native world / model world |1 / 0|
| model charged ticks / 비교 query |0 / 0|
| geometry solve / objective 평가 |1 / 194|
| HOLDOUT / SEALED query |0 / 0|

solver wall은 0.861972초였다. 최소 clearance -0.067585978m가 기존 −0.001m 수치 수리 범위를 벗어나므로 projection 수리는 하지 않았다. objective 평가는 분석적 geometry 비용이며 물리 model tick으로 세지 않는다. P4·native prefix·witness도 생성하지 않았다.

등록·정적 검사·선정·worker·raw readback 측정은 CPU 19.189318초/wall 17.538791초다. 별도의 개발 보수 계상 CPU60초/wall60초를 더한 전체 계상은 79.189318/77.538791초이며 2,400/3,000초 상한 안이다. 보수 계상은 실측값이 아니다. 이후 결과 렌더·독립 감사·출판은 별도 무적분 관리 작업으로 기록한다.

연구 잔여26,175·예비84,000/사용0은 그대로다. actual 행동 차감0과 reset1/51raw 비용을 구분해 새 v485 원장과 선호출 charge journal에 남겼다. 기존 v476 및 보호 원장은 수정하지 않았다.

## 실행 전 gate와 보존

기존 483의 고정121행동 root 전용 실행기를 수정하지 않고 485 전용 구현을 추가했다. generic native-prefix 권위는 case·P4·실제 관측 GoalLedger·RNG·witness·charge journal·새 source gate를 연결한다. 같은 context의 같은 eligible 후보에 두 순위를 적용하며, 검증된 기각 증거가 root ceiling보다 우선한다. 두 cold 반복을 독립 DEV 수로 세지 않는다.

파일 quota는 native3,264/model3,596 파일, native648,961,335B/model392,471,929B, 별도 proof·decision·temp·workspace와 종료 기록 예비를 생성 전에 예약한다. actual/model 선차감, 내부 reset 재시도 차단, CPU·wall·최신 deadline, 512MiB volume 예비와 world header829,464B도 실행 경로에 연결했다.

constructor·reset·step을 금지한 통합 무적분 검사 **48개가 통과**했다. identity 감사는 source2,749개와 이후 노출46단계의 기록 연결을 확인했다. 미기록 역사 geometry까지 완전하다는 주장은 하지 않는다. source hash를 선정 직전에 다시 확인한 뒤 최초 두 identity를 동결했으며 충돌 대체는0이었다. 보호 조건의 성능/raw는 읽지 않았다.

새 raw는 64파일/1,092,726B이며 전량 파일 hash·길이·JSON/decoded receipt를 다시 확인했다. native 정리 후 body0/joint0이다. 원본·실행 소스·계약·selection·준비 실패·정리·원장·재현 manifest는 비공개에 보존했다. 공개물에는 seed·identity·geometry 좌표·개인 원문·raw를 포함하지 않는다. /tmp raw 단일 사본은 비영속이며 hash로 유실 데이터를 복구할 수 없다.

## 해석과 종료

이번 결과는 margin-first의 성공이나 기각을 입증하지 않는다. 동결된 준비 recipe가 배정된 첫 신규 조건을 지원하지 못한 결과다. 같은 조건을 더 조정하거나 다른 조건으로 바꾸지 않는다. 485 실행 권한은 이 시도로 종료됐고 후속 실험은 시작하지 않았다. 비교 경로의 실제 물리 동작과 새 지도 state/header 상한도 이번 시도에서는 검증되지 않았다.

[상세 집계](independent485_result.json) · [선행 계약](independent484_contract.json) · [실행기](compare485.py)
