# 579 — reachable beam pilot 정상 종료, A 게이트 통과 없음

**결과: `A_FINITE_SEARCH_NO_PASS`.** 계약된 한 번의 source DEV pilot을 실행했다. A는 깊이25에서 live가 모두 terminal이 되며 정상 종료했다. 안전하게 s200을 통과한52개 terminal 모두 정수 시간 게이트를 실패했다. **예산 소진이나 기술 실패가 아니다.** 따라서 B·독립 replay·whole·native는 실행하지 않았고 기존13.20초 incumbent를 보존했다. 이 결과는 고정된 행동 집합과 진행도 우선 폭4의 유한 탐색에 한정되며, 물리적100ms 개선의 전역 불가능성이나 다른 표현의 기각이 아니다.

## 실행 전 고정과 구현 검사

578의 분석·`PROPOSED_NOT_EXECUTED` 계약과 commit `498c7ae0293ad6a18c6c74e74da85a65bbdcd05c`를 보존했다. [579 계약](beam579_contract.json)은 source 실행 전에 등록됐으며 SHA256은 `4a36258b5ea0d4cc7851941ad01d6b2e8bd67df1be516b522d9ee42a7935ad39`다. STARTED의 계약 hash와 종료 후 값이 일치했다.

- 실제 import 파일707개의 dependency manifest와 구현·테스트 hash를 고정하고 시작/종료에 검사했다. `brake506_geometry`, `brake508_corridor`, `brake510_common`, `drive519_control`을 포함한다. 초기 static root·path·577 tape·ledger 전체 입력 hash 및 `initial_visited`의 별도 hash도 고정했다. 공개물에는 원시 입력을 넣지 않았다.
- [구현](beam579_model.py)과 [순수 beam 연산](beam579_math.py)은 A factual 부모도 최대13개 행동으로 확장한다. 그 부모의 정확한 factual successor 하나만 보호하며 변경 행동은 다른 부모의 자식과 세 슬롯을 경쟁한다. factual byte identity는 행동 중복 제거 뒤에도 보존된다. factual crossing 뒤 슬롯은 동결한다.
- visited·tracker·launch/tracking history는 분기마다 복제한다. 공유 root/roads는 frozen dataclass·tuple 하위 구조를 확인했고, 부모·형제 fingerprint **21,872회**를 확장 전후 비교했다. 상태 병합은 실행 전 **NO_MERGE**로 고정했다. 578에서 상속된 ranking 설명의 조건부 bit-identical dedup 문구 대신579의 명시적 deduplication 규칙을 적용한다. successor cache는 사용하지 않는다.
- 최초 crossing을 고정하고 crossing hold의4raw 모두 안전한 뒤 terminal을 live pruning 전에 저장한다. 같은 고정 world plane, 기존 progress ±10m와 path corridor를 사용한다. 속도는 velocity vector를 보간한 다음 norm으로 계산한다.
- 시간 판정은 A `192−candidate_after_raw≥5`, B `247−candidate_after_raw≥4`의 정수 비교다. epsilon은 없다. body/domain/integrity/IO/cost는 전체 중단, 일반 source 부적격 child만 즉시 prune하도록 구분했다.

[단위 검사](../tests/test_beam579.py) **13개가 source/native 호출 없이 통과**했다. 최초 검사에서는 factual signed-zero fixture의 예상이 잘못돼1개가 실패했고, 실패 출력과 사용량을 보존한 뒤 fixture를 수정했다. 별도 읽기 검토에서 발견한 roads 객체 ID 기반 독립 checkpoint 비교도 실행 전에 내용 비교로 수정했다. 이 수정과 실패 비용은 최종 freeze 전에 반영했다. [검사 비용·시도 기록](beam579_tests.json)에 두 시도를 모두 남겼다.

## 실제 경계와 상태

기존 launch24 holds의96raw 재구성 및 **별도의4raw identity probe**에서 저장 상태·힘·이력·tracker·clock 필드가 모두 일치했다. probe를 search successor로 재사용하지 않았다.

| 구분 | 실제 결과 |
|---|---|
| A 깊이 | 25/최대28, 이후 live0으로 정상 종료 |
| 평가한 search children | 1,258회, 상태 no-merge이므로 고유 물리 상태 수라는 뜻은 아님 |
| 안전 terminal | 52개, 모두 crossing hold 완료 후 저장 |
| A crossing raw bracket | **192→193**, 52개 전부 동일 |
| A crossing clock bracket | 약3.84→3.86초, 원래 absolute episode clock 유지 |
| A crossing COM 속도 | **77.88594~79.40601m/s** |
| 속도 기준 | ≥79.25600518m/s, 16/52 통과 |
| 시간 기준 | candidate-after≤187, **0/52 통과** |
| A 동시 통과 | 0/52 |
| B crossing/80ms 유지 | A 실패로 미실행·미관측 |
| 초기 상태부터의 최종 독립 replay | 새 통과 계획이 없어 미실행; 일치 성공으로 주장하지 않음 |

선형 보간한 연속 crossing 진단에서 최대 이득은 **5.747µs**, 최저는 약−0.402ms였다. 이는 채택 기준이 아니며100ms 개선의 증거가 아니다. 동일 raw bracket 안의 미세 차이를 공식 시간 개선으로 환산하지 않는다.

도달한 가장 앞선 안전한 **완료 hold 상태**는 raw196/hold49, episode3.92초, progress **205.55138609m**, COM 속도 **81.61094581m/s**였다. 같은 raw의 baseline progress보다 약 **2.032mm** 앞서며 baseline 대비 달라진 hold는48 하나다. 이 상태의 최초 s200 crossing도192→193raw였고 속도79.39474906m/s였다. 여기까지의 안전 prefix라는 뜻이며, 이후 안전 완주·성능 개선·native 적합성은 검증하지 않았다. 최대 진행도 부분 prefix도 같은 완료 지점에 도달했다.

## Pruning과 실제 비용

| 이유 | 횟수 | 해석 |
|---|---:|---|
| FORCE | 313 | 적분 전 원래 peak predicate 거절 |
| CLIP_HISTORY | 4 | 적분 전 원래 누적 clipping predicate 거절 |
| REFERENCE | 191 | 적분 후 원래 reference 여유 거절 |
| BEAM_WIDTH | 602 | 안전 child를 진행도·forward 속도·고정 동률 규칙으로 탈락 |
| TERMINAL_GATE | 52 | 안전 crossing이나 시간/속도 승격 기준 미충족 |

source 부적격 child는508개였다. 안전 완료 child750회는 다음 live 배치96회, 폭 제한 탈락602회, terminal52회로 구분된다. 보존된 journal의 force event 연결과 raw verdict를 독립 집계해 이 숫자를 재확인했다. 18,899개 event의 hash chain이 유효했고, 정상 stage 종료였으므로 terminal·pruning 지역 기록도 빠짐없이 저장됐다.

| 비용 항목 | 실제 사용 | 계약 상한 |
|---|---:|---:|
| attempted raw | **3,965** | 11,000 |
| 완료 model tick | **3,648** | 11,000 |
| 외부 force wheel 호출 | **15,860** | 44,000 |
| 내부 적분 wheel 호출 | **14,592** | 44,000 |
| force 합계 | **30,452** | 88,000 |
| geometry 검사 | **3,648** | 11,000 |
| runtime CPU | **100.7285s** | 400s |
| runtime wall | **105.6358s** | 540s |
| 읽기 전용 후속 감사·마감 charge 포함 CPU | **102.3173s** | 400s |
| 읽기 전용 후속 감사·마감 charge 포함 wall | **107.2262s** | 540s |

외부/내부 force는 서로 다른 wrapper에서 **실제 wheel response 호출을 각각 계수**했다. 3,965−3,648=317 pre-force 거절은 FORCE313+CLIP_HISTORY4와 일치한다. 외부는4×3,965, 내부는4×3,648이며, 비용 정의를 수정했을 뿐 물리 판정은 바꾸지 않았다.

단계별 runtime CPU/wall은 준비4.653/2.563초, prefix·identity2.127/2.321초, search92.785/99.584초, runtime audit1.164/1.168초다. 준비에는 실패를 포함한 두 테스트 시도의 실측과 등록·hash 준비 보수 charge가 포함된다. 후속 읽기 감사와 최종 기록·검증 charge까지 합친 audit도 약2.752/2.759초로10/15초 한도 안이다. 완료 tick당 총 runtime CPU는 약27.61ms지만 실패 child·준비·감사가 섞인 이번 pilot의 비용 평균이며 범용 kernel 처리량은 아니다.

[원 실행 결과](beam579_result.json) · [원 비용](beam579_cost.json) · [읽기 전용 감사](beam579_analysis.json) · [감사 재현 코드](beam579_analyze.py)

## 해석과 종료

이 탐색은 도달 가능한 결합 제어를 검사했으나 첫 코너에서 사전100ms 게이트를 넘지 못했다. 이는 선택된13행동 이하·폭4·진행도 우선 ranking의 실패다. 폭·깊이·행동·step을 바꾸거나 다른 A 상태로 재시작하지 않았다. B는 실행하지 않았으므로 특정 A continuation의 실패조차 주장하지 않는다. 여전히1초 회수 가능성을 검증한 증거는 없다.

추가 optimizer·FD·보정·숨은 rollout·whole·native·자동 후속 실험은 없다. HOLDOUT·SEALED·native 사용은 모두0, research 잔여22,758, reserve84,000/사용0, 별도 유료 자원0이다. 지정 클라우드만 사용했고 승인 종료2026-10-20 10:01:55 UTC 전에 끝났다. 결과를 반환하며 다음 실험은 시작하지 않는다.

공개물은 기술 코드·계약·집계뿐이다. 원시 상태·계획·journal·실패 출력·비공개 원문은 저장소 밖에 보존했다. main 기준 `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, 공식 Participants·사용자 변경·기존 백업과 이전 결과는 보존한다.
