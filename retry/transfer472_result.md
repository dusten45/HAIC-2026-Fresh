# 472 — 단일 P4 native 이전 완료, 13.640초; 11.99초 목표 미달

**등록한 후보 한 개가 실제 공식 finish와 actual ledger DONE으로 완료됐다.** 같은 native 시작에서 기존458/463 prefix125를 full state·픽셀·RNG·메모리·관측 ledger까지 exact 재현한 뒤 native126의 C.act 전에 P4 nodes를 불변 주입했다. suffix46개 모두 현재 actual state/memory/RNG/GoalLedger에서 독립 P4 H13 두 개를 통과한 뒤 실제 첫 전이와 비교했다. 조기 model finish 이후 H13을 채우지 않았으며 model DONE으로 actual DONE을 commit하지 않았다. 새 강제 fullgas alias는 global126에서 한 번뿐이고 이후 자연 point-FF 행동을 유지했다. guardian/neutral rescue·랭킹·재시도·추가 실행은0이다.

공식 event/confirmation의 물리 시각은14.66초이고 reset 완료1.02초를 뺀 **episode13.640초**다. 171 wrapper actions, action raw682ticks+reset51ticks이며 prefix125/suffix46 모두 verified, 확인되지 않은 action0이다. damage0·모든 실제 row의 safety flag0, 최대 post 경로오차1.549090m, tyre clipping 불일치0, 최대 모델/실제 progress 차이0.000014605m다. force ratio 최대1.818339와 clipped92/2728 wheel samples도 그대로 남겼다. 경로오차 수치는 post 기준이며 force/clipping을 별도 무결점 인증으로 해석하지 않는다. live pending route는0회였고 current/terminal/pending fixture는 정적 단계에서 검증했다.

과거463의13.780초는 참고값일 뿐 fresh pair·새 인과 이득·통계 승격의 근거가 아니다. 이전470의 model remaining finish bracket[3.62,3.64]초와 이번 같은 pre126 이후 native3.64초를 동일 시간 경계로 비교할 수는 있으나 다른 seed나 일반화 검증으로 확장하지 않는다. **11.99초 목표와 HOLDOUT/SEALED 승격 기준은 통과하지 않았다.**

정적63검사+저장 감사가 CPU17.209068초/wall17.270893초로 통과한 뒤 실행했다. fresh source1137ticks/35worlds+root216/6=1353/41, current pairs4108/92, 총 **5461ticks/133worlds**다. 계획8738/181·hard9216/185 이내이며 undeclared auxiliary world0이다. whole worker CPU256.956679초/wall257.198949초(상한900/1200), 모델 exclusive CPU141.487597초/wall141.214833초, native exclusive CPU115.050127초/wall115.364553초다. cleanup 후에도 전체 상한을 재검사했다. 원장 journal172개를 전수 대조해 v476 CLOSED,171행동을 한 번만 차감했고 연구잔액 **26175**, 예비84000사용0이다. v475·누적 과거 기록을 수정하거나 환불하지 않았다.

이전471의 공간 실패와 기록은 보존하고472 새 계약을 등록했다. 새 source manifest 증가1079B와 모든 world header, raw1.700266GB·검증temp32MiB·reserve512MiB를 포함한 `/tmp` 필요량은2270691329B, 사전 free3255185408B였다. workspace metadata64MiB+reserve512MiB 필요603979776B도 free865927168B 안이었다. 기존 raw/archive의 삭제·이동·변환은0이며 새 archive도0이다.

새 원본 raw **2086파일/766497369B**를 같은 실행기의 `/tmp/haic-retry-stage472-private`와 `/tmp/haic-retry-stage472-native`에 한 벌 유지했다. 모든 파일을 별도 두 차례 다시 열어 전체 길이·SHA·finite JSON/JSONL·중복 key 금지·lossless bytes codec 또는 UTF8 text 구조와 manifest 일치를 확인했다. 보존CPU21.622246초/wall21.699400초다. workspace 비공개 영역에는 전체 plan1617858B·입력674900B·전수 manifest·코드·환경 version pins·RNG/실행 조건을 유지했다. 새 raw의 workspace 복사본0이다. **`/tmp`가 소실되면 exact raw 재검증은 불가능하고 hash로 raw를 복원할 수 없다.** 공유·영속성을 가정하지 않는다.

등록 source/input9078개와 보호18개를 종료 후 다시 hash 확인했다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·기존 사용자 변경/백업을 보존했다. DEV만 사용했고 HOLDOUT·SEALED·새 seed/학습·별도 유료 자원 사용0이다. 시작10분 이내 적분0 checkpoint를 남겼다. 원 위임문의 종료일을 재전달된 취소로 오인한 opening 안내는 기존 명시적 연장 증거(stage441)를 확인해 적분 전에 정정했으며 최신 승인 종료2026-10-20 19:01:55KST를 적용했다. 이번 단일 실행은 추가 실험 없이 닫았다.

[상세 집계](transfer472_result.json) · [gate](transfer472_gate.json) · [raw 보존 검증](transfer472_retention.json)
