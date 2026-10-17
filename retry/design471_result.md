# 471 — 단일 P4 native 이전 계약, 공간 미통과로 실행0

**모델·native call·reset·예산 차감 모두0으로 종료했다.** 단일 후보의 계약과 비용을 정리했지만 `/tmp`의 raw+archive 동시 보존 공간이 부족했다. 압축률 가정을 추가하거나70행동/H13/독립 반복을 줄여 맞추지 않았다. 기존 자료 삭제·이동·압축본 변환도0이다. 10분 이내 checkpoint에서 비용·소스 장애와 적분0 상태를 보고했다.

같은 native 시작에서 저장458/463 prefix125를 commands/state/memory/RNG/관측/actual ledger까지 exact 재현한다. 이125구간에는 기존 controller를 유지하고, native126의 C.act 전에 immutable P4 nodes를 주입한다. 새로운 강제 fullgas alias는 suffix 첫 행동126에서 한 번만 넣고 이후는 P4 point-FF·SourceC phase·자기 terminal target·자기 tracker를 유지한다. 실제 한도는125+70=195 actions/reset1회다. 과거463의13.780초는 참고값이며 fresh pair·새 인과 이득·통계 승격의 비교값으로 쓰지 않는다.

P4를 적용하는 suffix의 매 실제 행동 전 최대70번, 현재 actual state/memory/RNG와 read-only GoalLedger에서 **동일 P4 nodes/digest의 독립 H13 두 개**가 모두 valid이어야 한다. 첫 shadow 이후12개도 P4이며 old nominal로 돌아가지 않는다. 각 query의 local action0에서 pulse를 다시 넣지 않는다. 마지막 query의 H13은 고정 법칙을 가상 suffix82까지 예측할 수 있으나 actual70 이후 dispatch 권한은 없다. native 사실이 관측된 뒤 첫 shadow 전이와 물리·memory·node·ledger 일치를 확인하고 실패하면 다음 dispatch를 막는다. 모델 DONE은 actual DONE을 commit하지 않는다.

| 모델 구간 | 최대 ticks | worlds |
|---|---:|---:|
| 기존 source/current/pending/parent-pending qualification | 1242 | 35 |
| P4/Original root H13 독립2+held각1 | 216 | 6 |
| 최대70 current P4 queries×독립2×H13×4 | 7280 | 140 |
| **등록한 필수 합계** | **8738** | **181** |
| hard cap | 9216 | 185 |

35world에는 기존 pending/held/parent own transition이, root6에는 각 arm held가 포함된다. live actual parent는 model world를 새로 만들지 않고 readonly adapter로 읽으며 매 actual 첫 전이를 두 shadow와 비교하므로 추가 held0이다. 남은478ticks/4worlds는 새 실행 권한이 아니다. 추가 P4 물리 pending/held qualification이 필요하다고 판명되면 적분 전 다시 비용에 넣어야 한다. CPU900초/wall1200초·순차1·research26346만사용·reserve84000사용0이다.

이 계산의 H13 대상은 **P4 suffix70회**다. prefix125까지195회 모두 P4 H13 두 개를 요구한다는 해석이라면 선행1458+195×104=21738ticks/431worlds로 hard를 넘으므로 그 계약으로는 실행할 수 없다. prefix는 아직 P4를 주입하지 않은 exact 재현 구간이라는 경계를 명시했다.

기존 `Query463`는 첫 행동 뒤 old nominal/neutral guardian으로 돌아가므로 그대로 재사용할 수 없다. 기존 `law470`의70행동 driver도 current shadow local0 pulse나 horizon index 처리를 그대로 가져오면 잘못된다. adapter/memory에는 nodes가 없으므로 실제 controller와 **모든 current/future/pending shadow**의 별도 readonly nodes/source digest를 묶어야 한다. P4 FIRST_LAP→FINISH_CONFIRM→own nodes[-1]→자기 native finish의 통합 fixture와 production adapter는 아직 구현·통과하지 않았다. 공간 gate가 실패했으므로 이를 완료한 것처럼 표시하지 않았다.

실제 call은 기존 `NativeAuthority439`의 **차감→dispatch→관측 사실 commit→forecast 비교** 의미를 유지한다. 시도된 wrapper env.step 전에 research를 차감하고 reset은 별도 한도로 센다. 실제 사실은 비교 실패에도 보존하며 환불·재시도·위험 거절 우회는 없다. planned 최대195를 모두 쓰면 연구잔액26151이고 이번에는 차감0으로26346을 유지했다.

공간은 최신 모델 최대93,191.3141168B/tick, 최신 world header778,235B와185worlds, 새 manifest119B+4KiB 여유,1.25배를 적용했다. native는 감사한453/458/463 중 최대1,563,574.582B/action 및392,413.371B/raw tick을 사용했다. prefix500+suffix280+reset51=**831 native raw ticks**의 산정과 action 산정 중 큰 값을 선택하고 native fixed16MiB·metadata32MiB도 별도로 배정했다. 원자료와 최악 archive1.1배+32MiB, temp32MiB, reserve512MiB를 `/tmp`에 동시에 포함했다. 이전 압축률을 안전 공간으로 간주하지 않았다.

| `/tmp` 동시 보존 항목 | bytes |
|---|---:|
| model raw | 1,241,782,147 |
| native raw | 457,951,038 |
| 전체 raw | 1,699,733,185 |
| 전체 archive 예산 | 1,903,260,936 |
| temp32MiB+reserve512MiB 포함 필요량 | **4,173,419,465** |
| 사전 실제 free | **3,255,185,408** |
| **부족량** | **918,234,057** |

source 증가0·reset 별도 여유를 줄인 더 낙관적인 하한에서도4,077,628,750B가 필요해822,443,342B 부족하다. workspace는 code/입력/privateplan/full manifest/재현조건64MiB+reserve512MiB=603,979,776B 요구에 free866,295,808B로 통과했다. 산식·최종 bytes 올림은 독립 검토와 정확히 일치했다. [전체 계약·산식](design471_next.json)·[재현 코드](design471.py).

raw와 검증 archive는 실행된다면 같은 지정 실행기의 `/tmp`에 둘 다 유지하고 모든 member SHA/readback과 원본 SHA를 확인할 계약이다. workspace에는 두 번째 raw archive를 만들지 않는다. `/tmp`의 공유·영속성을 가정하지 않으며 소실 시 exact raw 재검증은 불가능하고 hash로 raw를 복원할 수 없다. 이번에는 새 raw/archive 자체를 생성하지 않았다.

보호18파일·v475·누적actual1321718·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·원본/백업을 보존했다. 기존 사용자 연장 근거와 최신 종료 **2026-10-20 19:01:55 KST**를 계약에 유지한다. 이번 결과는 적분 전 자원 중단이며 새 native 성능·정책 반증·승격 결과가 아니다.
