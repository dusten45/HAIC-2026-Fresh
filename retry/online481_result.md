# 481 B200: 안전한 수행 구간은 늘었으나 두 부모 모두 미완주

**기존 첫 raw 할당은74행동에서 unsafe, 온라인80ms 선택은125행동까지 안전·진행을 유지한 뒤 query126에서 유효 후보가 없어 종료했다.** 두 whole 모델 부모 모두 자기 공식 finish를 확인하지 못했다. 따라서 완주 시간 차이는 `null`이며 완주 개선으로 승격하지 않는다. 승인된 비교는 한 번 실행했고 추가 probe·실험 재시도·native 실행은0이다.

| whole 모델 부모 | 실제 own 행동 | 종료 | 수행 구간 최대 경로 오차 | 자기 공식 finish |
|---|---:|---|---:|---|
| frozen 첫 raw q* | 74 | UNSAFE: path_error_over3m | 3.740236m | 없음 |
| 매 상태의3명령80ms 선택 | 125 | EMPTY_FINITE_CANDIDATE_DOMAIN | 2.032101m | 없음 |

baseline의74개 행 전체는 저장477과 정확히 일치했다. 두 부모끼리의 완전한 동일 행 prefix는 **2행동**, 첫 명령 차이는 **3번째**였다. 온라인 정책은 자신의 상태에서 계속 재선택했으므로479의 pre69 국소 개입과 같은 상태의 장기 인과쌍으로 해석하지 않는다. 위치·행동 번호 트리거는 없다.

온라인125개 own hold에서 nominal 대비 실제 pedal 감소는 **gas6회·brake6회**, 합12회였다. 선택alias에는 nominal/q*가 같은 명령인 경우가 함께 포함되므로 alias 횟수 합을 행동 수로 읽지 않는다. **brake 감소도 발생했다**는 사실만 확인했으며 그것이 최종 실패나 안전 연장의 원인이라고 확정하지 않는다.

## 126번째 판단에서 유한 후보집합 소진

다음 값은 **cold 예측**이며 부모가 실행한 결과가 아니다.

| 후보 | 예측 M80 | 예측 종료 경로 오차 | 기존 raw guard |
|---|---:|---:|---|
| nominal | 1.953445853 | 4.479845m | path_error_over3m, road_loss_or_grass |
| 첫 raw q* | 1.945574533 | 4.536365m | 동일 |
| 활성 pedal0 | 1.945574533 | 4.536365m | 동일 |

모든 후보가 기존 안전 조건을 위반했다. query126의 선택 반복·부모 own step은 수행하지 않았다. 예측 M80의 작은 차이가 raw guard를 대체하지 않았고 구제 명령을 추가하지 않았다. 실제 부모는 마지막125행의 안전·진행 조건을 유지한 상태로 중단됐다. 이는 **이 세 명령 집합의 소진**이며 전체 제어 불가능성이나200행동 상한 censor가 아니다. M80이 다음 상태·누적 경로 오차·완주 안전을 인증하지 못한다는 한계가 그대로 남는다.

## 게이트와 이력 검증

새 integration의 **17개 zero-world static 검사**를 통과한 뒤 소스·입력·최신 공간·출력 상한을 한 번 동결했다. static에는 실제 SourceC의 pre23/pending phase를 물리 객체 없는 stub에서 확인하는 검사, nominal 1회 경계, full ForecastLedger-before-Stream, 완전한 float32 비트 dedup, 선택 반복/격리 실패의 음성 검사, 원문435 전체 이력과 새 live context/receipt 연결, codec 손상·누락·정확 복원 검사가 포함됐다.

source fixture와 저장435 pending fixture를 먼저 통과했다. pending에서는 원문 전체 역사와 own 확인 raw를 이어 실제 tracker/clock을 재생했고 같은 사건의 모델 확인을 검증했다. 이 fixture의 확인은 whole 온라인 부모의 완주로 세지 않는다. 과거 source35/H13 재적분은0이다.

각 현재 상태에서 SourceC nominal과 frozen476 q*를 한 번 준비하고, shadow는 **after-nominal memory 재사용 경로**로 실행했다. shadow·선택 반복 전후 parent 물리/memory/ledger/RNG/reference/행/status 격리를 확인했다. 선택 명령은 별도 복원의 전체 생성 raw·memory·ledger·status·finish 사건에서 정확히 반복됐고, 부모의 own hold는 기존 source tolerance와 discrete exact 연결을 모두 통과했다. 온라인의 선택 독립 반복은125회다. **미선택 후보는 각 한 번만 평가했으며 전체 순위의 반복 재현성이나 미선택 warm 반사실은 관측하지 않았다.**

기존 recipe whitelist는 수정하지 않았다. 새 `history481.py`는 각 명령을 hash가 고정된 context·allocation 입력/증명·finite 후보·선택 반복 receipt와 연결하고 전체 관측 tracker·memory·ForecastLedger·raw clock을 재검증한다. baseline의 마지막 unsafe 사실도 보존하며 그 뒤의 추가 행동은 금지한다.

empty-domain에서 호출된 마지막 nominal의 **미dispatch after-memory**와 실제 controller digest를 별도로 보존했다. committed own 이력의 마지막 memory는 query126 준비 전까지라는 scope를 명시했다. memory rollback·가짜 own 행·예측의 parent DONE commit은 없다.

## 실제 비용과 보존

| 구성 | worlds | charged ticks | positive ticks |
|---|---:|---:|---:|
| source fixture | 4 | 16 | 16 |
| pending fixture | 4 | 16 | 4 |
| baseline whole 부모 | 1 | 296 | 296 |
| 온라인 whole 부모 own | 1 | 500 | 500 |
| 온라인 후보와 선택 반복 | 382 | 1,528 | 1,528 |
| **합계** | **392** | **2,356** | **2,344** |

원래 source가 pending 확인에서1raw로 끝나도 wrapper당4 charged ticks를 유지했다. 총 wrapper 슬롯은589개이며 allocator/nominal은 **202회**다. 등록된 hard4,840/812/402 이내다. 최악 비용에서 dedup·조기 중단을 미리 차감하지 않았다. 실제 중복 명령을 제거한 계수와125행 후 중단 때문에 사용량이 줄었다.

등록·통합 static·모든 constructor·fixture·예측·선택 반복·부모·증명·필수 전체 readback 포함 **CPU501.161초 / wall500.558초**로 hard900/1,200초 안이다. allocator 집계 CPU3.984초/wall3.932초이며 호출별0.25/0.5초와 집계110/220초 제한을 통과했다. budget의 constructor 구간 CPU합은2.993초, source step 및 그 안의 observer 구간은1.891초다. 이 수치는 순수 Box2D만 분리한 시간이 아니며 나머지 검증·기록·직렬화 비용도 whole 비용에 포함된다.

별도 사후 읽기·감사·요약의 측정분을 합한 CPU는 약504.75초다. 사후 감사에서 기본 Python reader import 한 번의 CPU가 미계측돼 지정venv로 읽기를 완료했고, 실패 import·startup에 **보수적인100CPU초/5wall초를 별도 계상**해도 전체 계상값은 CPU604.75초/wall508.08초다. 이 추가 계상은 실측 시간이 아니다. 물리 실험을 재시작하지 않았다.

소스 manifest 증가는 **953B**로 등록8KiB 안이었다. source manifest는 inline으로 유지했다. 새 raw의 동일 full state만 한 번 저장하는 `io481.py`의 lossless reference codec을 사용했고, state object SHA와 원래 decoded payload SHA를 모두 검증했다. 입력·fullstate·memory·RNG·ledger 정보를 생략하지 않았다. 기존 파일은 변환하지 않았다. 승인된 model raw cap1,364,580,771B를 늘리지 않았고 새 형식의 별도 강제 상한은1,119,518,720B다.

새 raw는 **4,350파일 /329,731,405B**, /tmp 단일 사본이다. worker가 전체 파일을 두 번 읽어 길이/SHA/JSON과 decoded state를 확인했고, 독립 감사에서도 파일 목록·길이·SHA 오류0을 확인했다. 마지막 control record 갱신 후 manifest 해시를 확정했다. workspace에는 full pre23 입력/RNG/P4 geometry, 계획·코드·집계·manifest·재현 조건이 있다. 전체 명령열·full state·원시 trace는 비공개다. archive·workspace raw 복제·기존 파일 삭제/이동은0이다. /tmp 유실은 해시로 복구할 수 없고 재실행은 승인되지 않았다.

실행 계획 SHA256: `01a88dd5e1f7d3f9203e28f406b0671934008ada21763db98a577b899399d721`. `compare481.py`가 등록/단일 실행, `io481.read`/`load_receipt`가 lossless raw 읽기, `summarize481.py`가 저장된 결과의 실패 원인·개입 집계 재현 진입점이다. once marker가 started 비교의 재실행을 막는다. 체크포인트는 각 query/own 행동과 workspace에 주기적으로 보존했다.

## 남은 판단 범위

이번 결과는 **안전한 own 수행 구간의 연장과 후속 유한 후보집합 소진**을 보여준다. 완주·완주 시간 이득·미선택 warm 순위·픽셀·native·일반화는 확인하지 않았다. 후속 실험이나 추가 horizon/명령/구제는 시작하지 않는다.

actual/native/reset/HOLDOUT/SEALED/예비 사용은 모두0이다. 최선 native **13.640초**, 연구 잔액 **26,175**, 예비 **84,000/사용0**, 보호18파일·공식 Participants·기존 백업·main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`을 유지했다. 최신 종료는 **2026-10-20 19:01:55 KST**, 자동 연장 없음이다.
