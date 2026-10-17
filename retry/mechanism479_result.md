# 479: 단일 80ms 기전 검사 완료

**pre69에서 첫 raw 최적 q*보다 활성 페달 0의 80ms 실제 부모 결과가 개선됐다.** 이것은 같은 조향·reference·활성 페달 branch를 유지한 세 명령의 국소 비교다. 완주 정책·native·픽셀 성능으로 승격하지 않았다. 추가 실험이나 재시도는 실행하지 않았다.

## 사전 계약과 실행 경계

478 계약을 그대로 적용했다. 명령은 원래 nominal, frozen476의 첫 raw minimax q*, 활성 페달 +0뿐이며 각각 기존 80ms hold/4raw20ms를 유지했다. 기존 raw 안전·진행·FIRST_LAP 조건을 통과한 후보에서 M80을 정확히 최소화하고 정확한 동률은 큰 페달을 선택했다. M80은 전체 4raw×4wheel의 `max(0, force_ratio−1)` 최댓값이며 차체 안전 기준을 대체하지 않는다.

새 integration 소스·입력·현재 디스크·출력 상한을 한 번 등록했고 AST와 읽기 전용 병렬 검토 후 단 한 번 실행했다. nominal은 prefix68+pre69의 **69회**만 호출했다. pre47의 nominal/q*는 준비한 before/after-memory와 함께 재사용했다. fresh shadow/held47은 **준비된 after-memory 경로**이며 별도 nominal 호출이 아니다. full ForecastLedger를 observer Stream 생성 전에 복원했다.

같은 pre23에서 재생한 **prefix68의 모든 행이 기존477과 정확히 일치**했다. 두 root×세 명령×독립 반복2의 전체 cold trace/기억/상태가 정확히 일치했고, 부모 물리·memory·ledger·RNG·reference의 격리를 확인했다. q* 첫 raw source force는 정확히 일치했다. cold→기존 warm q* 및 선택 cold→held own은 기존 tolerance와 raw discrete flag 정확 일치를 통과했다. 복원에서 broadphase의 구조적 `source_world_contacts` 진단값만 물리 identity 비교에서 제외했다. 기존 constructor body/tiles/progress/finish, 실제 wheel/body/contact/안전 플래그 검사는 그대로 유지했다.

## 결과

| fixture | nominal cold M80 | q* cold M80 | pedal0 cold M80 | 선택 | held own M80 |
|---|---:|---:|---:|---|---:|
| pre47 양성 대조 | 1.174397255 | 0.496377861 | 0.496377861 | q* (정확한 동률에서 큰 q) | 0.496377861 |
| pre69 늦은 hold 성장 | 1.180958099 | 1.053017955 | 0.528171822 | pedal0 | 0.528171822 |

pre47은 알려진 q* 반응과 안전·진행을 유지했다. pre69의 같은 cold root에서 q* 대비 차이는 **0.524846133**이다. 기존 두 trace의 force_ratio tolerance로부터의 보수적 차이 불확실성 0.10보다 크다. 이 0.10은 optimizer epsilon이나 완화된 안전 기준이 아니다. 실제 source/held force_ratio 최대 오차는 각각 약2.23e−6/2.06e−6이지만 사전 경계를 사후 축소하지 않았다.

**주 판정은 cold 점수가 아니라 같은 prefix의 warm 부모가 직접 수행한 결과다.** 기존477 warm q*69의 M80 **1.053018935** 대비 새 held69 own **0.528171822**, 차이 **0.524847112 (49.84%)**다. 실제 raw 안전·진행 조건을 모두 통과했고 종료 경로 오차는 기존0.612916m 대비0.538496m였다. 따라서 사전 정의한 `MECHANISM_LOCAL_OWN_HOLD_IMPROVED` 판정이다. M80이 여전히0보다 크므로 힘 제한 초과를 해소했다는 뜻은 아니다. 이후 구간·완주·일반화·제동 변경의 효과는 검사하지 않았다. pre47/pre69는 진단 fixture이며 위치를 쓰는 정책 트리거가 아니다.

## 비용과 보존

- 정확히 **14worlds / 328 positive ticks / charged328 / 82 wrapper transitions**. constructor의 zero-time Step은 최대14회 범위다. allocator는69회, 집계 CPU0.411초/wall0.422초로 30/60초 상한을 지켰고 호출당0.25/0.5초 제한도 통과했다.
- 등록 준비와 입력/소스 검증, constructor, prefix, shadow, 반복, held, 증명, 최종 전체 readback을 합산해 **CPU16.772초 / wall15.980초**, 사전180/300초 이내다. 준비 프로세스 CPU1.677초/wall1.300초를 포함한다. 구현·검토 작업시간은 실행시간과 별도다.
- 새 raw **250파일 / 36,442,244B**, /tmp 단일 사본이며 모든 파일을 두 번 읽어 길이·SHA·JSON을 확인했다. 최종 control record 변경 후 해당 해시를 갱신했다. workspace에는 계획·full pre23 입력/RNG/P4 geometry·소스·집계·manifest·재현 조건을 보존했다. 새 archive·workspace raw 복사·과거 파일 삭제/이동은0이다. /tmp 유실 시 해시로 raw를 복구할 수 없고 재실행은 승인되지 않았다.
- actual/native/reset/HOLDOUT/SEALED/예비 사용은 모두0. 최선 native **13.640초**, 연구 잔액 **26,175**, 예비 **84,000/사용0**을 유지했다. 공식 Participants, 보호18파일, 기존 백업과 main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`를 보존했다.

실행 계획 SHA256: `4462dd76dc3faab89fd8528f815ef47010958256cb0344e1bc76e793b659a0fb`. 원시 입력/trace는 공개 저장소에 포함하지 않는다. 공개 집계는 `mechanism479_result.json`, 재현 진입점은 `compare479.py prepare|run <private-root>`이며 once marker가 재실행을 막는다.

## 남은 범위

이번 결과는 첫20ms 목적값만으로80ms 명령 hold를 고르는 한계의 국소 증거다. 장기 경로 오차, 이후 조향/속도 이력과 완주 성능은 미검증이다. 후속 실행·새 root·추가 명령·horizon 변경은 하지 않았다. 다음 판단은 이 국소 증거를 검토하는 것이며, 별도 후속 계약 없이 실험을 자동 진행하지 않는다. 명시적 연장 기록에 따른 종료는 **2026-10-20 19:01:55 KST**이고 자동 연장은 없다.
