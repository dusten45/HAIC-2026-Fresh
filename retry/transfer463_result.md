# 463 — 첫 명령 한 번의 실제 이전: 14.000 → 13.780초

**두 새 native arm이 각각 자기 공식 finish를 확인했고, Original−SecantOnce는0.220초였다.** 462의 모델 tail 차이[0.20,0.24]초와 방향·크기가 부합한다. 이번 값은 실제 reset부터 측정한 native lap이며 모델 tail을 더해 만든 기록이 아니다. 11초대에는 미달했다. 같은 알려진 DEV에서 whole arm을 각각 한 번 실행한 조건부 결과이고, blind/다른 root/픽셀/서버 일반화는 검증하지 않았다.

|실제 arm|첫80ms|이후 guardian|prefix+suffix 행동|자기 native lap|root 이후 실제 시간|
|---|---|---|---:|---:|---:|
|Original|기존 nominal|nominal50|125+51=176|14.000초|4.000초|
|SecantOnce|462와 exact 같은 secant/fullgas alias|nominal46·neutralbrake1|125+48=173|13.780초|3.780초|

첫80ms의 실제 속도 변화는−7.744/+2.477m/s였다. 첫13행동의 wrapper post 최대 경로오차는0.805/1.178m, clipped wheel sample은2/208와7/208이었다. 초반 명령 변경에 따른 노출 증가를 보존한다. 전체 lap의 wrapper post 최대 경로오차는 양쪽1.448m였고 damage0이었다. 전체 값에는 같은125행동 prefix가 포함되며 raw 전수 최대와 wrapper post 지표를 혼동하지 않는다.

SecantOnce의22번째 query에서는 두 nominal shadow가 각각 완전H13(52 raw ticks) 후 `path_error_over3m` UNSAFE로 거절돼 기존 neutralbrake가 한 번 선택됐다. 실제 부모가3m를 넘었다는 뜻이 아니다. 첫 명령 외에는 두 arm에 같은 guardian 피드백 정책을 적용했지만 각자 상태가 달라 후속 명령열은 다르다. 따라서 관측한0.220초는 단발 명령과 이후 상태/guardian 반응을 합친 효과다. 이 root에서 fullgas와 secant가 같은 명령이므로 sample-hold 원인 식별이나 전체 secant 제어 법칙의 개선 증거는 아니다.

## 게이트와 실제 권위

[통합 계약](design463.json)·[설계](design463.md)·[비용 계산](budget463.py)을 먼저 고정했다. prefix125+suffix70/arm, 행동390/reset2, planned30370ticks/597worlds, hard32768/768, whole CPU1800/wall2400, native exclusive240/480을 유지했다. 첫 고정query1회 뒤 guardian 최대69회이며 모델 부모0이다. unused headroom으로 다른 탐색을 열지 않았다.

physics constructor·step·native를 금지한 정적271개와 저장 감사가 통과했다. 실행 코드·gate는5cc5d8e로 먼저 commit/push했다. fresh source/current/pending1137ticks/35worlds와 pre126 root216/6, 합계1353/41이 통과한 뒤에만 native reset을 열었다. source nominal H13은 저장 실제 factual 검증, fullgas H13은 독립2+held 첫 전이의 모델 자기일관성이다. query의 독립2회는 whole arm 반복2회와 다르다.

두 실제 reset의 initial·prefix125·pre126 root가 저장458P와 exact 일치했다. prefix는250개, 새 선택 첫 전이는99개가 검증됐고 clipping flag 불일치0, 최대 progress model/actual 차이는 약0.0000077m였다. Original 전체 native trace는 저장458P와 exact 일치했다. 실제 관측을 먼저 commit한 다음 모델 첫 전이와 대조했고, 모델 forecast/certificate가 실제 DONE를 대신하지 않았다. Original pending1회는 자기 native 확인으로 끝났고 SecantOnce pending은0이었다. 두 자기 실제 ledger·tracker event·공식 finish를 별도로 확인했다.

## 실측 비용과 회계

|구간|model raw ticks|worlds|실제 wrapper 행동|
|---|---:|---:|---:|
|fresh qualification|1353|41|0|
|Original|4602|102|176|
|SecantOnce|4420|98|173|
|합계|**10375**|**241**|**349**|

reset2와 reset raw102 ticks를 별도 기록했다. 실제 행동 raw1391·reset 포함1493ticks다. 모델 reserved10375와 observer post10375개/stream241개가 일치했다. worker whole CPU380.681초/wall383.720초, model exclusive234.979/235.667초, native exclusive145.628/147.839초였다. 정적24.622/24.577초, 저장 감사15.881/16.787초는 별도다. import·source확인·제어·physics·observer·proof·hash·IO·cleanup을 worker에 포함했지만 전체 개발/보고/Git overhead를 완전 측정하거나 순수 solver 시간으로 부르지 않는다.

실제 호출 전에 fsync charge journal→v475→stage budget 순서로 차감했다.351개 기록(행동349+reset2)과 확인된 native fact349개가 일치했고 미확인 행동0, 재시도0이다. v474를 보존하고 같은 v475를 추가 차감0으로 CLOSED 처리했다. 연구 잔액26346, 실제 누적1321718, 예비84000/사용0이다. 역사적 누적 장부의 과거 raw 전수 감사가 완전하다는 주장은 하지 않는다.

PID180103은2026-10-17 20:18:53 KST에 exit0으로 종료했다. worker가10분 전에 끝났으며 [최종 진행 기록](transfer463_progress.json)과 private 단계/행동 checkpoint를 보존했다. [집계 JSON](transfer463_result.json)과 [입력 hash](transfer463_inputs.json)에 검증·비용을 남겼다. 기존 실패·censor·보호18파일의 해시, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants와 기존 원본/백업을 보존했다. 새 seed·학습·HOLDOUT·SEALED·예비·새 유료 자원 사용0이다.

## 저장과 남은 판단

시작 전 최신462의83723.18010403121B/tick, world고정768619B 별도 가산,25% 경험적 여유, 각 볼륨 종료512MiB를 포함해 모델4.425GB/native1.299GB를 계산했다. 기존 /tmp·workspace 가용4.563/1.620GB 안에 들어가 새 raw를 각각 직접 저장했고 기존 파일 이동·삭제0이다. 추정은 보증 상한이 아니므로 실행 중 두 볼륨 reserve를 검사했다.

새 model raw1970파일890158797B와 native1764파일537578277B를 보존했다. 최초 archive 시도는 streaming tar API의 `compresslevel` 인자 오류로 중단됐고 실패 manifest·부분 archive·[실패 집계](transfer463_retention_attempt1.json)를 남겼다. 실험 재실행 없이 지원되는 gzip API로 별도 recovery 경로에 복사했다. 모델112828867B/native38447814B의 private archive 모든 member와 원본 SHA256을 검증했다. 복구 후처리 CPU14.106초/wall14.670초, 최초 실패2.180/2.216초이며 적분0이다. [보존 집계](transfer463_retention.json)를 제공한다. private full plan은 workspace에도 남겼고 raw/seed/RNG/좌표·개인 자료는 공개하지 않았다. /tmp 공유·영속성이나 공개 hash만으로 private 입력 복원을 가정하지 않는다.

이번 게이트가 뒷받침하는 판단은 **고정된 첫 명령 한 번의 실제0.220초 이득**까지다. 남은 약1.8초 이상 격차를 이 pulse 하나로 해결했다고 보지 않는다. 다음 연구 판단은 나머지 제어 구간의 시간 손실과 지속 제어 변경의 비용·안전 자격에 별도 반증 계약이 필요한지다. 이번 비교의 추가 root·전체 secant·후속 실험은 열지 않았다. 최신 승인 종료는2026-10-20 19:01:55 KST이며 이후 새 실험·자동 연장 없음이다. 초기에 과거10월16일 문구를 잘못 적용한 종료 응답은 명시적 연장 승인 확인으로 정정했다.
