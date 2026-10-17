# 426: 종료 인증 정적 수정과 첫 실패에 따른 승격 차단

**첫 동결 정적 검사에서 양성425 사례가 실패해426 모델·실제 단계는 열지 않았다.** 원실패를 보존한 별도 수정본은 같은 양성·음성 대조28개를 통과했다. 이 수정본은 정적으로만 검증됐고 마지막 snapshot의 독립 모델 확인·P12 실제 재현은 미실행이다. 새 실제/모델 적분·reset·학습·SEALED·예비 사용은0이다.

사용자의426 지시인 “첫 정적 실패면 모델/실제 단계는 열지 마세요”를 적용했다. 별도 수정본의 정적 통과로 이 첫 실패 gate를 다시 열지 않았다. 실행 경로는 원래 `static-result.json`의 실패 판정으로 차단된다.

## 첫 실패와 원인

동결 계획 SHA-256은 `bf70cf64c5d2abb7028e6d4b31ff8d4b142690dd159caf7d5863fdcf26473ee9`다. 첫425 양성 사례는 `TechnicalStop: guardian_finish_confirmation_metadata`로 실패했으며 완료된 check는0개였다. 이때 모델·실제 함수는 호출되지 않았다.

초기 수정에서 확인 완료 후에도 tracker에 후보 필드가 남는다고 잘못 요구했다. 실제 `FinishLineTracker`는 완료 확인 시 `finish_time_s`에 crossing 시각을 옮기고 `candidate_crossing_time_s=None`, `crossing_from_back=False`로 정리한다. 저장425의 실패 model child도 이 정상 완료 형태였다. 현재 root의 후보와 완료된 model tracker를 서로 다른 단계의 증거로 처리해야 했다.

원래 [guardian426.py](guardian426.py), [static426.py](static426.py), 실패 결과·계획/hash는 보존했다. private 사본도 원 hash와 같게 남겼다. 425의 원실패·365 실제 행동 비용·P 공식 finish 미관측 판정과420–425 파일 전체는 변경하지 않았다.

## 별도 정적 수정본

[guardian426_confirmed.py](guardian426_confirmed.py)는 완료된 tracker의 정리된 형태와 official model timestamp를 확인한다. 현재 root에 등록된 후보가 같은 event이고 기존 phase/corridor가 유효한 경우에만 AT_ROOT 또는 BEFORE_ROOT의 pending confirmation을 구분한다. 새 AFTER_ROOT event는 관측 model raw clock의 양의 미래 event여야 한다. 임의의 과거 event나 qualification 이전 event는 받아들이지 않는다.

guardian certificate에는 **planner 순위 시간·Evidence·실제 DONE 권한을 부여하지 않는다.** planner는 기존 `Child`/419의 양의 미래 finish 비교와 음수/zero-event 순위 거부를 그대로 사용한다. signed C·명령 계산·phase·confirmation corridor·gain·recipe·horizon13·projection은 유지했다. 실제 DONE은 실제로 발행한 native action의 완료 row가409 계측 계약을 통과할 때만 허용하는 별도 조건이다.

정적 수정 계획 SHA-256은 `1b154dbb5c3036bbe546f1a1653a4e1fed02520bf7c560ce2b69686881f9b645`다. [static426_recheck.py](static426_recheck.py)는 원래 동결된 assertions를 유지하고 수정 모듈·입출력 경로만 분리했다. **동일 대조28개가 통과**했다.

| 대조 범위 | 확인 결과 |
|---|---|
| 저장425 AT_ROOT, 등록된 BEFORE_ROOT 후보 | model confirmation만 인정, actual DONE/순위 권한 없음 |
| 저장423 정상3raw partial·AFTER_ROOT event | 기존 완료 계약 유지 |
| 과거408/409 | 정상 partial 표본 계약 통과, 원408 실패 판정 보존 |
| 미래 timestamp·등록되지 않은 미래 event | 거부 |
| 불일치/STOP phase·corridor 위반 | 거부 |
| qualification·from-back 확인 없는 crossing | 거부 |
| 임의 과거 event·qualification 이전 event·model metadata 불일치 | 거부 |
| 이미 actual official finish가 있는 root의 새 query | 거부 |
| 실제 미발행 행동·model certificate의 actual DONE | 거부 |
| 미래 native finish·표본 누락·짧은 비종료 action | 거부 |
| planner 음수 bracket·zero-event 순위 | 기존대로 거부 |
| 저장 planner 선택·guardian Evidence 차단·최악 비용 | 유지 |

이는 저장 자료와 synthetic 음성 대조의 **정적 자격**이다. 새 모델 종료 확인이나 실제 완주 결과로 확대하지 않는다. 수정 모듈은 별도 파일이며 이번에 모델·실제 실행 경로에 적용해 재개하지 않았다.

## 미실행 단계와 비용

계획했던 마지막425 snapshot의 보유 모델 부모+nominal 독립2회 확인과 이후 P12 한 번 실제 재현은 첫 정적 실패 gate로 미실행이다. C0를 다시 실행하지도 않았다. 425 P의 공식 finish는 여전히None이고 새 lap/gain은 없다. 미래 재현 시 C0 15.080초는425의 **과거 대조**여야 하며 새 동시 pair로 부를 수 없다.

처음 계획한 전체 최악 모델 비용129,890tick/795world는 승인131,072tick/1000world 안에 있었다. 실제 상한310wrapper/reset1/모델 제외 CPU90초/wall180초, 모델 CPU600초/wall900초, 정적 CPU60초/wall120초/순차 적분1개를 동결했지만 모델·실제 비용은 소비하지 않았다.

첫 정적 측정 CPU/wall **0.514/0.514초**, 별도 수정 정적 측정 **1.453/1.858초**, 측정 구간 합계 **1.967/2.372초**다. 각 정적 프로세스에도 absolute process CPU/wall 중단을 설정했다. 진입 전 import·준비·보고/git 전체 비용은 완전 계측하지 않았다. 초기 동결까지 준비 wall **165.964초**는 초기 읽기·설계 제외의 부분 구간이고 준비 CPU와 이후 수정 준비 전체 시간은 미측정이다.

원장v446은 **연구 잔여28,621 + 최종 예비84,000 + 실제 누적1,319,443 = 운영 상한1,432,064**를 그대로 유지한다. 425의 실제365/model25,933 비용은426에 재청구하지 않았다. 새 actor·학습·SEALED·예비·추가 유료 자원은0이다. 공식 main·Participants·사용자 변경·296·rollback·보호 자료와 비공개 map/seed/state/RNG/receipt 보존 조건을 유지했다.

남은 blocker는 수정본의 **독립 모델 확인과 실제 P12 재현 자격 미실행**이다. 별도 승인된 후속 단계에서 먼저 저장425 root의 모델 확인·부모 무영향을 검증해야 한다. 이번426에서는 새 적분·실제 재실행·독립 실험·자동 연장을 시작하지 않았다.

[기계 판독 결과·음성 대조·비용](recovery426_result.json) · [425 원실패](carry425_result.md)
