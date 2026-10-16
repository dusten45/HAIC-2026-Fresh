382 — 최종 실행 계약 제안과 G5 준비 상태

이 문서는 **계약 제안이며 실행·개봉 권한을 부여하지 않는다.** SEALED16은 열지 않았고 현재 query 허용량0을 유지한다. 새 실험·정책 수정·조건 생성·파일 전송은 없다. 연구 전체 종료나 일정 취소도 하지 않는다.

| 동결 대상 | 제안 |
|---|---|
| 최종 정책 | champion296 하나. ZIP SHA256 `0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937`,18 member hash와 manifest 동일. 최종 결과에 따른 대체 후보 탐색 없음. |
| rollback |240 ZIP SHA256 `ae944d7d9e2fda02fc05936bcf245613a81fade5f2f3edc1f6ead68e9bed8d31`와 기존 manifest 보존. 실행 오류 복구용 보존이지 같은 SEALED에서 더 좋은 후보를 고르는 비교권이 아님. |
| runtime | 현재 지정 cloud의 동일 머신 CPU·독립 clean actor,Python3.11.16·NumPy1.26.0·OpenCV4.8.1.78. 기존 worker/native sandbox와 패키지 module hash 고정. 다른 머신·공식 서버 동등성은 미검증. |
| 정보 | 정책은 reset/act와 float32 `(4,84,84)`·0..1 관측만 수신. seed·info·reward·환경 객체·평가 로그·기대 행동은 supervisor에만 존재. 현재 격리는 메타데이터 syscall 은닉이나 hostile-code 보안 증명이 아님. |
| 조건 | 기존 봉인16개·기존 순서·조건당1회. 재추출·길이/난도/성공률 필터·새 split·추가 seed 없음. 개봉 전에 권한·원장과 기존 manifest 연결을 고정. |
| cap | 공식 로컬 runner 기본값 `max_steps=2000,frame_skip=4`. 조건당 실제 wrapper env.step 최대2000,총32,000. 공식 서버와 동일 horizon이라고 주장하지 않음. |
| 판단 | 동결 정책의 최종 성적 보고. SEALED를 정책 선택·계수/문턱·feature·학습·새 후보의 피드백으로 사용하지 않음. 최종 자료는 관측 후 개발셋으로 재사용하지 않음. |

381의 미실행 제안에서 계산한2,038은 **TimeLimit 내부 수용량**이다. `local_runner.py`는 raw budget을 `2000*4+200=8200`으로 만들고,reset 뒤 TimeLimit elapsed50에서 while-loop를 별도로2000회 제한한다.2000행동을 모두 수행해도 elapsed는8050이므로 내부8200보다 먼저 멈춘다. 첫 reset은 원본 `step(None)`1틱+warmup50틱으로 물리시각1.02초다. TimeLimit elapsed와 raw tick 수를 혼합하지 않는다. **이번 기본값 계약은32,000회이며,381의32,608회 용량 제안을 대체한다.** 예전 문서·측정은 수정하지 않고 이 정정을 덧붙였다.

완주 처리는 공식 소스의 `finish_time_s is not None`을 따른다.95% 방문은 자격이고 정방향 시작선 뒤 영역 진입·중앙 통과·앞 영역 이탈이 필요하다. 시간은확정 tick이나 행동수×80ms가 아니라 `round((finish_time_s-start_time)*1000)`이다. finish가 있으면 raw `truncated=True`여도 완주다. 동시에 damage/종료 flag가 있으면 모두 기록하되 finish 우선이라는 runner 보고를 보존한다. 정상2000 loop cap에서 finish가 없으면 로컬 규칙상 `max_steps` DNF로 보고한다. 임의로 더 짧게 끊은 protocol cap·예산/승인 종료·기술 실패는 별도 censor/미관측이며 정상 DNF로 바꾸지 않는다. `off_track`은 음의 행동구간 보상101회 연속 또는 원본 이탈 등일 수 있고,이 이름만으로 잔디 이탈 원인을 단정하지 않는다.

공식 로컬 소스의 timeout·invalid 규칙과 제안된 자격 중단을 구분한다.

| 사건 | 공식 로컬 runner의 동작 | 최종 제안의 기록·재실행 |
|---|---|---|
| 유한 행동·범위 초과 | shape를 flatten해 길이3 확인 후 조향±1·페달0..1 clip,valid로 취급. | 기준 경로와 동일하게 처리하고 원값·실행값 기록. 정책 계수나 내부 기억을 임의 교정하지 않음. |
| 예외·비유한 값·잘못된 shape | `safe_act`는 no-op `[0,0,0]`와valid=False. 성공 시 counter0,실패 시+1.10번째 연속 invalid는 **그 no-op을 env.step하기 전에** invalid_action으로 중단. | 독립 actor 어댑터의 이 예외 경로 동등성은381의 정상 입력 검사만으로 증명되지 않았다. 이 계약 제안은 첫 invalid에서 자격 실패로 전체 평가를 안전 중단하고,관측되지 않은 공식 invalid_action DNF를 만들어내지 않는다. 자동 재실행 없음. |
| act5초 초과 | 로컬 thread join이 끝나 no-op invalid를 반환하나 daemon thread는 살아 있을 수 있음. | 독립 actor를 종료·회수하고 technical/time-limit 실패와 censor로 기록. thread를 방치한 로컬 경로와 같은 후속 상태/점수라고 주장하지 않음. 이 차이를 숨긴 동등성 인증 금지. |
| import/생성10초·reset5초·메모리 초과 | README 제한과 local runner 구현 범위는 다름. 로컬 reset 예외/timeout은 전파되고 공식 subprocess의 내부 회복은 제공 소스로 확인 불가. | 현재 qualification limits로 중단,부분 결과·미실행·실제 비용·회수 기록. 재시작·같은 조건 재평가 없음. |
| 환경/IPC/파일 무결성·의존성·저장 오류·승인 마감 | 정상 완주/리타이어와 다른 오류. | 첫 오류에서 남은 최종 실행 중단. 내구 기록만 복구하며 불확실한 step은 별도 비용 범위로 조정 전 확정하지 않음. 같은 episode를 reset부터 다시 달리지 않음. |
| 정상 finish/crash/off_track/max_steps | 실제 공식 결과. | 성공·실패를 보고하고 사전 순서의 다음 조건으로 진행. 실패했거나 승패가 명확해 보인다는 이유로 남은 정상 평가를 생략하지 않음. |

정상 입력 경로의237행동 전체·reset 후16행동 재현과 지연/RSS는[381](qualification381_result.md)에서 통과했다. invalid/timeout 발생 경로를 새로 시뮬레이션하거나 fault injection하지 않았다. 첫 자격 실패에서 중단하는 엄격한 로컬 평가를 제안하므로,문제 발생 시 부분 최종 성적과 공식 서버 성적의 차이가 남는다. 이 계약으로 공식 서버의 오류 처리까지 인증했다고 표시하지 않는다.

포장 오류는 **개봉 전** 기존 hash·member·경로·dependency·cold start/입력 기록으로 처리한다. 실행 어댑터 경로·기록 오류라도 source/계약 hash 변경과 범위를 남기고,정책 ZIP byte나 의미가 바뀌면296 검증을 그대로 이전하지 않는다. **개봉 후** 이름/경로 수정이라도 재주행이 발생하면 같은 조건의 반복 노출이다. '포장만 고쳤다'는 이유로 독립성을 복원하거나 허용량을 초기화하지 않는다. 우선 중단·노출 기록 후 사용자의 별도 판단 대상이며,추가 실행은 이 계약에 포함하지 않는다. 로그를 읽고 동일 결과 파일을 복구하는 bookkeeping은 물리 재실행과 구분한다.

예비84,000회 제안 배분은 **296 SEALED16의32,000 / 자동 retry0 / rollback 비교0 / 미배정·미사용52,000**이다. reserve 총량은 감액하지 않고 실제 env.step 호출만 차감한다. actor act/reset·raw warmup/step ticks·CPU·wall·RSS는 별도 원장에 남긴다. actor만 호출한 실패는 native0일 수 있고,10번째 invalid처럼 act와env.step 수가 다를 수 있다. 동작이 성공한 뒤 기록이 끊기면 중복 주행 대신 내구 기록으로 사용량을 조사한다.52,000은 retry권이나 새 정책 탐색비가 아니다. 현재 연구 잔여35,943도 최종 비교용 자동 전용·확대하지 않는다.

봉인 노출·중복 메타데이터의 확인 범위는 다음과 같다.

- 기존 최초 계약은 DEV8/HOLDOUT8/SEALED16의 pair·seed 교집합0이라고 기록했다. stage16의 기존 source-only 검토는 보호분할을 포함한 메타데이터48개와 seed 계보/geometry 제외를 기록했다. 이는 당시 기록의 확인이며 이번에 원래16조건을 생성·읽거나 geometry를 재계산한 결과가 아니다.
- 현재 champion은 `G5_SEALED=PENDING_CLOSED`,query 원장은 episodes_used0·현재 단계 허용0이고 `SEALED*.opened` marker는 없다. 원래 조건 파일은 stat만 확인했고 내용·seed·geometry·성능을 읽지 않았다. 기존 HOLDOUT.opened는 존재하므로 모든 보호셋이 미개봉이라는 주장은 하지 않는다.
- 296의12 DEV는 이미선택에 사용됐다.295의 `sealed295`라는 내부 그룹명도 공식SEALED를 뜻하지 않는다. 같은 도로의 반복 관측·서로 겹치는 fold를 독립 조건 수로 늘리지 않는다.372 개별 자료는 읽지 않았다.
- **최초16조건과 이후 모든 실행 사이의 현재 중복0을 이번 감사만으로 확정하지 못했다.** 원래 봉인 항목별 opaque identity/geometry fingerprint와 최신 노출 원장을 직접 연결하는 독립 메타데이터 receipt가 여기에는 없다.296 exclusion snapshot의 존재·항목 수만으로 완전 무중복을 주장하지 않는다. 개봉 전 담당 경계에서 비공개 identity를 정책에 노출하지 않고 교집합 개수/범위/출처 hash만 반환하는 검토가 필요하다. 이 단계에서 새 seed·환경·좌표 생성으로 대신하지 않는다. 중복이 발견되면 원래 세트를 몰래 교체하지 않고 계약을 다시 판단한다.

이 때문에 현재 상태는 **패키지/같은 머신 정상 경로 자격 통과,최종 개봉 계약은 조건부 제안**이다. 새 머신·공식 서버 미검증은 명시된 범위 한계이며 임의의 새 자원을 요구하는 추가 gate가 아니다. 원래16조건의 현재 노출/중복 receipt와 최종 실행 권한·원장 연결이 남은 실제 준비 항목이다.

| G5 항목·부모 원문 전달 근거 | 현재 근거 | 남은 범위 |
|---|---|---|
| 해시·의존성·입력·runtime·memory,적용계획10절/18.2 |296 manifest,381독립 clean process,기존377실제 TRAIN 재현 | 최종 실행물/runner/원장 계약 hash 연결;공식 서버/새 머신 미검증 구분 |
| SEALED·노출,적용계획9절 | query0·허용0·marker없음,과거 분할/반복 기록 | 현재 opaque 중복 receipt와개봉 권한;성능/조건 미개봉 유지 |
| 실패·중단,적용계획11절 |380방법군표·실제 음성 결과·이 계약의 fail-stop/no-retry | 실제 최종 실행이 있으면 부분 결과·censor·실사용 비용 추가 |
| 후반 회귀·cold start·패키지·롤백,적용계획15절 |377/381·240 archive/manifest hash 보존 | 결과에 따른 후보 재선택 금지,bookkeeping과재주행 구분 |
| 원문15장 hybrid/P8 |380전체방법군·374/375부품실험·319/320단계확대 | 국소 transport 이득을hybrid상호작용/속도효과로 확대하지 않음. 전체 factorial·속도맞춤 대조가 없으면 미분리로 표시 |
| 원문 추적·사용자 학습 설명,적용계획18.2G5 |부모의24장·적용계획 전체 재독 및 발췌 전달,아래사용자 설명 | 소비 실행기의 직접 원문 확보·완독은 미확인.원문/추출본/개인 회고는공개하지 않음 |

부모의 전체 재독과 전달 발췌를 유효한 출처로 연결했으며,원문24장은 모든 방법군 구현 의무가 아니라 검토 근거를 요구한다는 전달을 따른다. 원문15장의 부품효과와 단순 감속 분리 요구 때문에,고속 운전에서 일부 lap/충돌 변화만으로 새 구조의 우월성을 선언하지 않는다. 원문을 공개문서에 재현하거나 소비 실행기의 직접 완독을 주장하지 않는다. 이 계약의 권한 범위 밖에서 SEALED를 열거나 새로운 연구선을 확대하지 않는다.

[사용자용 연구 설명](research382_explanation.md) · [메타데이터·소스 감사](final382_review.py) · [집계·비용](final382_result.json)
