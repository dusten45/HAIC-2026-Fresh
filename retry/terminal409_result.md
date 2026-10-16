# 409 — 정상 terminal action repeat와 표본 누락을 구분

**408의 마지막3 raw tick·12 wheel sample은 공식 종료에 따른 정상 조기 종료와 일치했다.** 별도로 교정한 계측 계약에서는 저장189행 모두 통과했다. 그러나 **408의 원래 `QUALIFICATION_OR_TECHNICAL_STOP`·`completed_safe=False`와 원래 파일은 그대로 보존**했다. controller `mark_done` 검증도 사후 실행하지 않았다. 공식15.08초·손상0 관측은 유지하며 O+268의14.78초보다0.30초 느렸다. [검사 결과](terminal409_result.json) · [순수 계측 계약](terminal409_contract.py) · [저장 자료 대조 코드](terminal409_audit.py)

## 소스와 저장 증거

[wrapper](../env_wrapper.py)는 최대4회 raw step을 실행하되 `terminated or truncated`면 즉시 반복을 끝낸다. [core](../core/vendor/car_racing.py)는 매 raw tick의 물리 적분 뒤 finish tracker를 갱신하고, 공식 finish가 생기면 `new_lap`에 따라 `truncated=True`를 반환한다. 즉 정상 terminal action은1–4 raw tick일 수 있다.

[finish tracker](../core/finish_line.py)는 중앙선 통과 후보 시각을 저장하고 앞쪽 경계를 벗어났을 때 그 시각을 공식 finish로 확정한다. 따라서 공식 crossing timestamp가 확인 시각보다 앞서는 것은 허용된다.408의 마지막 pre는16.06초, finish timestamp는16.10초, 마지막 post는16.12초였다. 이0.02초 차이를 누락 sample로 판단하지 않았다. raw 내부의 각 위치는 저장되지 않았으므로 특정 substep의 기하 통과를 별도로 재생한 것은 아니다.

| 저장 대조 | 확인 결과 |
|---|---:|
|비종료 action |188개, 각4 raw tick·16 sample |
|정상 종료 action |1개,3 raw tick·12 sample |
|전체 raw tick / wheel sample |755 / 3,020 |
|wrapper elapsed counter 증가 |805−50 =755 |
|raw clock 증가 |16.12−1.02 =15.10초 =755/50 |
|공식 lap |16.10−1.02 =15.08초 |

모든 action 경계의 시계가 이어졌고, 각 raw tick의 wheel0–3이 순서대로 한 번씩 기록됐다. 앞선 action에는 종료 flag가 없고 마지막 action만 공식 finish와truncated가 있었다. finish qualification timestamp≤공식 crossing timestamp≤최종 시각도 확인했다.15.10초의 관측 구간을 공식 lap으로 대체하지 않았다.

## 별도 교정 계약과 대조 검사

비종료 action은4 tick, 종료 action은1–4 tick을 허용하되 `Δt=n/50`, 정확한 `4*n`개 wheel sample 및 `(raw_tick,wheel)` 전체 순서/coverage를 모두 요구한다. 행 단위 검사는 선언된 metadata의 일관성을 검사하며 결승선 기하 자격을 새로 증명하지 않는다. 이번 감사에서는 저장된 최종 tracker의 qualification/finish metadata도 별도로 대조했다. 종료 flag 하나만으로 공식 완주라고 분류하지 않는다. 공식 finish flag·유한한 과거/현재 timestamp가 있어야 하며, 다른 terminal은 별도로 분류한다. finish timestamp를 post 시각과 같다고 강제하지 않는다.

원본188번째와189번째 행의 복사본은 각각 정상 비종료/정상 공식 종료로 통과했다. 다음8개 **합성 record 훼손**은 모두 거부됐다: wheel sample1개 삭제, raw tick 한 묶음 삭제, 같은 개수의 wheel 중복, tick 라벨 훼손, 시계만1 tick 전진, 종료 flag 없는 짧은 action, 미래 finish timestamp, 완주 flag가 있으나 finish timestamp 누락. 별도 합성 비완주 terminal은 계측상 통과하되 공식 lap으로 분류되지 않았다. 이는 새 실제 주행을 한 검사가 아니다.

새 계약이 통과했다는 사실은 기존408의 실패를 덮어쓰지 않는다. 기존 실패는 항상4 tick을 요구했던 동결 검사에 대한 기록으로 남는다. 이번 검사는 정상 프로토콜 조기 종료와 실제 누락/불일치를 판별하는 별도 근거다.

## 상태 기반 개입 설계와 비용

[현재 상태 기반13행동 위험·진행 개입 설계](state409_design.md)는 행동번호91·실패 arc·track/seed를 트리거에서 배제한다. nominal이 안전·진행 적격이면 항상 통과시키고, 불적격일 때만 기존 pulse recipe의 적격을 평가하는 방식이다. 현재 source의 finish 지원 부재·GT와 픽셀 관측 차이·반복 개입과 fallback·계산비용·성공 O의 오탐 검증이 선행 조건이다. 설계와 기존406 결과의 논리 대입만 했으며 새 rollout은 없다.

저장/source 감사 CPU0.067초·wall0.067초였다. 설계 산식·문서·git 전체 시간을 포함한 계측은 아니다. wrapper/reset·actor·source 적분·학습·SEALED·유료 자원·예비 사용은 모두0이다. 연구30,892·예비84,000·사용0·296·240 롤백·공식 main·Participants·보호 자료·SEALED16·승인 종료2026-10-20 19:01:55 KST를 유지한다. 새 설계/미래 비용 제안은 실행·예약하지 않았다.
