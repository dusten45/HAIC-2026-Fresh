# 491 — 정확한 공유 endpoint 분류 source 회귀 통과

**공유 endpoint 태그 오류를 새 opt-in source에서 수정했고, synthetic와 두 저장 경로의 유한 pose 검사가 통과했다.** 원래397/417 코드·호출자와490 실패 기록은 바꾸지 않았다. 새 physics/reset/world/step/profile/P4/경로 변경·seed·둘째 DEV 조건 접근은 모두0이다. N1은 이미 성공 이력이 있는 기존 저장 reference의 source-level 회귀용이며 새 조건을 뽑거나 해당 주행을 재적분하지 않았다.

## 원인과 제한된 수정

원래 투영은 `u=clip(dot(pos-a,edge)/(norm(edge)**2),0,1)`을 사용한다. 끝점 query라도 `sqrt`와 제곱의 반올림 때문에 `ds*ds`와 `dot(edge,edge)`가 다를 수 있다. 분모가 조금 크면 u는1보다 작다. 그런데 `a+u*edge`의 float64 저장 좌표는 정확히 끝점과 같을 수 있다. 원래 source는 u가 정확히1일 때만 incoming vertex tag를 붙여, 동일한 끝점의 outgoing tag와 interior −1 tag가 최소 거리 tie에 함께 들어가면 ambiguity로 거부했다.

현재 line에서 ds²/dot 불일치158개 중 끝점 quotient<1이57개, N1에서는112개 중56개였다. source 전체의 분모를 dot으로 바꾸는 수리는 하지 않았다. 진짜 interior의 기존 산술과 선택을 보존한다.

새 `projection491.canonical_projection`의 순서는 다음과 같다.

1. finite 입력과 computed intermediate, 양의 ds/분모를 검사한다. 중복 numeric 좌표를 가진 서로 다른 vertex ID는 입력 미지원으로 거부한다. +0과−0은 같은 기하 값으로 비교하지만 vertex ID를 합치지 않는다.
2. 일반 query는 원래 ds² 분모로 u/foot을 계산한다. clip 전에 quotient의 finite를 검사한다. query가 해당 edge의 **자기 저장 endpoint와 정확히 같으면** 그 owner의 endpoint/u0·1을 사용한다.
3. 계산된 foot이 그 edge의 자기 start/end와 **정확히 같은 numeric 값일 때만** 해당 vertex로 분류하고 원래 owner 좌표/u0·1로 정규화한다. 다른 vertex를 검색해 가까운 점에 붙이지 않는다. 입력 line bytes는 불변이다.
4. 정규화한 feet로 원래 float64 제곱거리를 재계산한다. 최소 tie 전원이 같은 vertex ID이며 모두 그 vertex의 incident edge여야 한다. interior tag 혼합·비인접·서로 다른 최소점은 계속 fail-closed다.
5. 일반 vertex는 outgoing, node0의 LAUNCH는 arc0/outgoing, FIRST_LAP·FINISH_CONFIRM은 arcL/incoming인 기존 phase 규칙을 유지한다.

이는 binary64 query/foot identity 규약의 수정이다. exact-rational 최근접 투영과의 동일성을 주장하지 않는다. 임의 epsilon·isclose·nearpoint snapping·nearestvertex fallback을 쓰지 않았다. ds/분모의0 붕괴와 비유한 중간값을 거부하지만 모든 subnormal underflow를 감지한다고 주장하지 않는다.

새 `CoherentExecutor491`는 원래 signed417 `act` bytecode/defaults와 다른 메서드를 그대로 두고, opt-in class의 canonical lookup만 수정본에 연결한다. 원래 global은 변경하지 않는다. 기존490 입력·미래 계약을 몰래 이 source로 승격하지 않았다.

## 검증 결과

사전 등록 뒤 JSON scalar gate를 먼저 실행했다. numpy int/uint/float/bool·array/0차원 array·signed-zero roundtrip과 NaN/Inf 거부를 검증했고 같은 변환기를 모든 결과/오류/체크포인트에 사용했다. **synthetic13개가 통과**했다. 반올림 재현·seam3phase·일반공유 vertex·signedzero 외에 서로 다른 비인접 최소점, crossing interior, 인접하지만 서로 다른 feet, duplicate vertex, overflow/퇴화 분모, 원래 interior 출력 및 opt-in code/global 분리를 포함한다.

| 저장 경로 | 유한 pose | 원래 오류 | 수정본 오류 | 정확한 endpoint로 증명한 복구 |
|---|---:|---:|---:|---:|
| 현재489 line(321 stations)|3,210|165|0|165|
| 기존 N1 line(238 stations)|2,380|153|0|153|

vertex를 세 phase로 반복하므로 오류 수는 독립 조건 수가 아니다. 각 복구는 원래 최소 feet 전부가 같은 저장 vertex와 정확히 같고, 원래 최소 edge ID가 그 두 incident edge 안에 있다는 별도 검사를 통과했다. 따라서 이 회귀에서 서로 다른 branch 최소점을 합친 복구는0이다.

기존에 허용된 pose의 index/u/arc/sigma/path-error/side 변경은 두 경로 모두0이었다. tie 개수 메타데이터만 현재6/N1 15건 바뀌었다. 일반 interior 출력은 그대로다. 두 경로의 정확한 시작점은 세 phase의 index/u/arc 검사를 모두 통과했다.

pose는 모든 vertex3phase와 midpoint normal shift0,±0.25/1/3m다. 실제 rollout이 아니다. sample별 old/fixed 상태·index/u/arc와 cursor gap을 비공개로32개마다 저장해490의 기록 손실을 반복하지 않았다.

## 남은 cursor·연속성 경계

기존 nearest-vertex cursor는 수정하지 않았다. 해당 cursor와 수정 canonical을 비교한 유한 pose 중 현재981/2,568건, N1 768/1,904건에서 index 또는 arc가 달랐다. 최대 arc gap은 각각3.500000239m/3.506775687m였다. index가18개 stale인 midpoint 진단에서는303/321 및227/238건의 불일치가 남았다. 이 gap은 lateral path-error나 실제 주행 오차가 아니다.

유한 pose의 수정본 ambiguity0은 전체 off-reference tube에 유일하고 연속인 projection이 있다는 뜻이 아니다. synthetic의 실제 다중 최소점은 계속 거부됐고 near-tie·vertex tangent/gradient 변화·cursor window·unwrap·hold 동안의 source/동역학 문제는 별도다. 490에서 발견한 engine/combined/rear force proxy 초과도 그대로 남는다. 동적 안전·native source/warm·완주 자격은 승격하지 않았다.

## 비용·보존·출판

등록 상한은 CPU45초/wall60초·RSS256MiB·retained8MiB/32파일·file/temp1MiB·volume별512MiB reserve였다. 원래 canonical12,000회/수정 canonical12,000회/cursor10,000회/별도 terms audit12,000회를 제한하고 선차감했다. 실제 원래5,597회·수정6,162회·cursor5,031회·terms321회다. synthetic 비용도 포함된다.

전체 worker는 import·등록/source/input 검사·JSON/synthetic·저장 pose·증명·출력·전체 readback을 포함해 **CPU5.918695624초 / wall5.890265469초 / 최대 RSS34,537,472B**였다. raw는11파일635,848B다. code/report/publication도 같은 global quota로 최종 검증한다. 원래 line/raw/명령을 복제하지 않았고 좌표·pose 상세·입력 owner 경로는 비공개로 유지한다.

main·Participants·backup·기존485~490·연구 잔여26,175·예비84,000/사용0과 최신 종료2026-10-20 19:01:55 KST를 보존한다. 자동 후속 실행은 없다. 이후 source 채택이나 물리 계약은 수정 source digest와 남은 미자격 경계를 별도로 검토해야 한다.

[수정 source](projection491.py) · [등록](projection491_registration.json) · [집계](projection491_result.json) · [독립 검토](projection491_review.md)
