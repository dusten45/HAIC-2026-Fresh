# 420 — C0 모델은 완료했으나 planner 증거 저장 오류에서 중단했다

**420은 첫 기술 실패 중단 조건에 따라 미완료로 닫았다.** 기존418 실제 구간 자격과 C0의 세 decision·nominal C continuation finish는 통과했다. P는 첫 질의의 세 recipe tail과 독립 반복을 계산했지만, 증거의 immutable bytes를 JSON으로 저장하지 못했다. **P 부모는0행동이며 세 decision 폐루프 비교·그 이득은 없다.** 모델을 재개하지 않았고 actual gate도 열지 않았다.

오류는 `TypeError: Object of type bytes is not JSON serializable`다. immutable parent 입력을 `asdict(ctx)`로 변환하면 bytes가 남는데 저장 코드를 이에 대응하지 않고 작성했다. 선택·복원·물리 계산 후 증거를 쓰는 경계에서 발생했다. 실패 traceback·부분 `.tmp`·모든 source branch와 실행 원본을 보존했다. 공개 runner에는 lossless bytes codec만 적용했고 정적4개 테스트를 통과했다. selector·gain·horizon·projection·C·ledger를 바꾸거나 모델을 다시 돌리지 않았다. [수정된 runner](pilot420_run.py), [codec·정적 테스트](pilot420_json.py), [테스트 코드](test_pilot420_json.py).

## 먼저 통과한 자격

418 actual fork의 같은 physical·C 계산 직전 memory·RNG·clock에서 시작했다. 실제 환경·actor는 만들지 않았다. root nominal float32 명령은 actual418과 정확히 같았다. 새 nominal13/full-gas-first13을 실제 body·wheel·raw hull과 대조하고 각각 독립 반복했다. 살아 있는 모델 부모의 snapshot·memory·RNG 불변 및 부모 첫 전이와 fresh nominal의 비교를 통과했다.

B13에서 실제 대비 최대 차이는 body 위치1.599×10⁻⁵m, 속도1.533×10⁻⁵m/s, wheel omega4.234×10⁻⁵rad/s, force ratio8.462×10⁻⁶, raw origin 위치1.630×10⁻⁵m였다. phase와 기존 허용오차를 유지했다. **실제 fidelity 범위는 이 root의 A/B13뿐**이다. neutral root·그 뒤 모델 상태·긴 tail을 실제 인증으로 표시하지 않았다.

actual root `GoalLedger`는 immutable로 보존했다. 모델 부모와 child는 별도 ForecastLedger를 갱신했다. 현재 planner receipt용 ledger view도 예측 상태의 읽기 전용 값이며 actual ledger의 commit이 아니다. 세 decision은 pilot 반복 범위로만 쓰고 absolute 행동 번호·arc 구간·seed를 선택 트리거로 넣지 않았다.

## 완료·중단된 범위

| 대상 | 부모 decision 갱신 | 이어진 C nominal | 공식 model finish bracket |
|---|---:|---:|---:|
| C0 | 3회, 모두 nominal 선택 | 68행동 | [281,282]tick = 5.62–5.64초 |
| P | **0회** | 실행 안 함 | 없음 |

C0 부모는 총71 model 행동에서 finish했고 손상0, 최대 post 경로 오차1.135m, 진행 조건을 통과했다. finish score는 root부터 기록된 **official finish event** raw clock을 찾은 값이다. confirmation 뒤 마지막 wrapper 시간을 finish로 대신 쓰지 않았다.

P 첫 질의의 초기13과 continuation은 각각 같은 child에서 이어 적분했다. 필수와 독립 반복을 별도로 셌고, 각 세 recipe의 전체 반복은 정확히 일치했다. 추가308 cap·13 이하 checkpoint·원래 경로 안전/진행·phase·정의역·419 선택 규칙을 유지했다. 이 첫 질의에서는 projection·수치·복원·부모/RNG·fidelity 문제가 없었고, 이후 JSON 저장에서 중단됐다.

| 첫 질의의 보존된 model witness | 초기 / 추가 행동 | model finish bracket | 최대 force ratio |
|---|---:|---:|---:|
| nominal | 13 / 58 | [281,282] = 5.62–5.64초 | 1.115 |
| full-gas-first | 13 / 51 | [251,252] = 5.02–5.04초 | 1.338 |
| neutral-brake-first | 13 / 51 | [253,254] = 5.06–5.08초 | 1.349 |

읽기 분석으로 같은419 bracket 규칙을 적용하면 첫 질의의 순위는 full-gas이고 nominal 대비 [29,31]tick=[0.58,0.62]초다. 원래 `choose` 호출은 저장 예외 전에 완료됐다. 이 값은 **첫 상태의 단일 model witness 순위**이며 P가 세 상태를 갱신한 정책 이득이 아니다. 실행 당시 RNG token을 새로 만들어 인증한 것처럼 취급하지 않았다. 긴 tail의 q 범위도418에서 실제 보정한13행동 범위를 넘으므로 실제 성능·안전으로 확대하지 않는다.

## 비용과 원기록

| 모델 비용 구분 | raw tick |
|---|---:|
| 실제418 구간 자격, 필수 | 104 |
| 같은 자격의 독립 반복 | 104 |
| 자격용 부모 첫 전이 | 4 |
| C0 guardian 필수 / 반복 | 156 / 156 |
| C0 부모 갱신 / 마지막 C tail | 12 / 271 |
| P 첫 질의 초기13 필수 / 반복 | 156 / 156 |
| 같은 child의 C tail 필수 / 반복 | 634 / 634 |
| 합계 | **2387** |

새 world19(confirmed19), zero-time contact setup19, 미확인 tick0이다. 동시에 보관한 world는 최대7개였으나 step은 항상 하나씩 순차 실행했다. 초기13을 다시 적분해 continuation에 이중 청구하지 않았다. model CPU는 import·검증·로그·정리까지 포함한 worker7.150초, 실행 wall6.475초다. 각각150/240초와32768tick/64world 상한 안이다. constructor/step CPU·wall 태그도 저장했지만 나머지 제어·hash·snapshot·로그 overhead를 태그별로 완전히 나누지는 않았으며 총 worker 비용에는 포함했다.

중단 후 bytes codec 검사4개와 저장 자료 분석만 했고 CPU0.134초/wall0.109초였다. 모델 호출은0이다. 구현 marker 이후 준비277.584초는 별도이며 그 전 읽기·설계·전체 준비 CPU·복구 준비·보고/git 전체는 완전 미계측이다. 원 실행의 plan SHA256은 `fe639bddff820adbeaa3d52d8e1b3fc0178d772009c0b3ef7e9534104025489e`다. 실행 runner SHA는 `2ab1ab440b4986c7ecd1c2a2c00fbf06c4f07b0bbc7f7621e74a8e10da9bead6`로 private archive에 보존했고, 공개 runner의 수정 hash와 차이를 별도 기록했다. 실행 당시 원본과 수정 코드를 혼동하지 않는다.

## 남은 조건

P의 세 실제 모델 상태 갱신과 마지막 C continuation이 미완료다. 직렬화 수정을 포함해 새로 등록한 모델 pilot에서 root actual13·현재 nominal·복원·독립 반복·부모/RNG·phase·진행·비용 게이트부터 확인해야 한다. 양쪽 부모가 모두 공식 model finish에 도달하고 완성된 폐루프 bracket에서 엄격한 이득을 확인하기 전에는 정책 비교 양성이라고 할 수 없다. 그때도 long tail의 실제 fidelity는 별도이고 actual 실행은 자동으로 열지 않는다. 이번 중단 후 재개·새 창·새 recipe·새 actual은 없었다.

원장v440: actual/reset·actor·학습·SEALED·예비·유료 자원 사용0, 연구 **29,618행동**·예비84,000(사용0)·실제 누적1,318,446 유지다. 296/rollback240·보호 자료·408 원기록·419 selector·417 판단·공식 main·기한을 보존했다. 개인 seed·지도·상태·trace·RNG·원본 실패 자료는 저장소 밖에 뒀다. [결과·단계별 비용](pilot420_result.json), [읽기 전용 복구 분석](pilot420_readonly.py), [계측 backend](pilot420_backend.py).
