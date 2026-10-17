# 480: 온라인 80ms 모델 정책의 단일 전체 비교 계약

**제안은 B200 하나다: 후보마다 한 번 예측하고, 선택된 후보만 별도 복원에서 다시 실행한 뒤 같은 모델 부모에 적용한다.** 같은 full pre23/P4에서 기존 첫 raw 할당 부모와 비교하며 양쪽 모두 자기 공식 완주·기존 안전/진행 중단·200행동 상한까지 진행한다. 이번480은 저장 자료와 소스 읽기·정확 비용 산술만 수행했다. 새 physics/world/positive tick/native/reset/allocator 실행은 **모두0**이다. 온라인 정책·새 meter·pending 이력 검증기는 아직 구현하지 않았고 실행을 승인하거나 시작하지 않았다.

## 먼저 계산한 두 방식과 선택

최악 계산은 세 명령이 모두 다르다고 가정하며 dedup·조기 중단·기존 baseline의74행동 실패를 비용에서 미리 빼지 않았다. source와 pending fixture 각각에 held 부모까지 포함했다.

| 설계 | 부모별 상한 | 후보 검증 | charged ticks | worlds | /tmp 전체 필요 | 현재 공간 대비 |
|---|---:|---|---:|---:|---:|---:|
| A250 | 250 | 세 후보 각각 독립2회 | 8,056 | 1,516 | 2,999,142,901B | 869,845,493B 부족 |
| B250 | 250 | 세 후보 각1회＋선택 후보만 독립 반복1회 | 6,040 | 1,012 | 2,301,109,951B | 171,812,543B 부족 |
| **B200 제안** | **200** | **세 후보 각1회＋선택 후보만 독립 반복1회** | **4,840** | **812** | **1,968,560,547B** | **160,736,861B 여유** |

현재/tmp 가용2,129,297,408B를 사용했다. 두 부모의200행동은 pre23 이후 각16초, 물리 시각2.78초에서 최대18.78초까지다. 이는 자기 완주를 시도할 상한이지 완주 보장이 아니다. 상한에 도달하면 `SCOPE_CENSORED`이며 짧은 구간 이득을 완주 이득으로 대체하지 않는다. 250행동 설계와 동일한 관측 horizon이라고 표현하지 않는다.

B200의 모든 슬롯은 다음과 같다.

| 구성 | worlds | wrapper 슬롯 | charged ticks |
|---|---:|---:|---:|
| 기존 첫 raw 할당 모델 부모 | 1 | 200 | 800 |
| 온라인 재선택 모델 부모의 own 적용 | 1 | 200 | 800 |
| 매 현재 상태의 후보3회＋선택 반복1회 | 800 | 800 | 3,200 |
| pre23 source fixture: 후보3＋선택 반복＋held own | 5 | 5 | 20 |
| 저장435 pending fixture: 같은 구조 | 5 | 5 | 20 |
| **합계** | **812** | **1,210** | **4,840** |

constructor zero-time Step도 최대812회이며 world를 constructor 전에 과금한다. 각 wrapper는 적분 전에4ticks를 예약한다. 원래 source의 공식 finish/termination으로1∼4raw에서 끝날 수 있지만 이후 샘플을 만들거나 terminal 뒤 추가 적분하지 않는다. 이 경우 실제 생성된 전체 raw와 정확한 길이를 반복 비교하며, 최악 비용에는4를 유지한다. source fixture와 pending fixture는 각 한 hold 안의 게이트이며 실패 시13행동으로 자동 연장하지 않는다. 과거 source35/H13/pending 재적분은0이고 retained 증거를 해시로 연결한다.

allocator와 nominal은 **기존 부모200＋온라인 부모200＋fixture2 = 최대402회**, 선택 query는 **202회**다. shadow/선택 반복/held는 준비된 nominal과 q*를 재사용하고 새 검색·nominal 호출을 하지 않는다. 두 whole 부모의 별도 episode 반복이나 추가 warm q* probe는 없다. fixture 둘을 먼저 통과한 뒤 baseline, 온라인 부모 순서로 실행하는 향후 계약이다. baseline의 알려진 물리적 실패는 상태 비교 결과로 남기고 온라인 부모는 독립된 원래 root에서 시작한다. baseline 재생은 저장477의 동일 명령/행과 연결해 source drift와 실제 정책 차이를 구분해야 한다.

## 위치 트리거 없는 정책

각 모델 부모의 **현재 상태**에서 기존 SourceC를 한 번 호출한다. 같은 frozen P4/reference/preview·steering 법칙·phase 전이·80ms hold를 유지한다. 서로 다른 전체 정책이 다른 상태에 도달하면 steering의 피드백 값도 달라질 수 있으며, 명령을 비교하는 **같은 현재 root 내부에서는** 세 후보의 steering을 nominal과 정확히 같게 둔다. pre47/pre69나 행동 번호를 런타임 조건으로 쓰지 않는다.

후보는 nominal 활성 페달 q0, frozen476 첫 raw minimax q*, 활성 페달 +0뿐이다. inactive pedal은0이며 새로운 제동 branch를 만들지 않는다. 양쪽 pedal이0이면 동일한 완전 명령 하나다. 전체 IEEE754 float32 명령 비트가 동일할 때만 alias를 deduplicate한다. 가까운 수치나 다른 조향을 합치지 않고, 절약은 실행 시 실제 계수로만 보고한다.

모든 실제 생성 raw의 기존 물리 안전·원래 ForecastLedger 진행/기한·FIRST_LAP/FINISH_CONFIRM 조건을 통과한 후보에서 M80을 정확히 최소화한다. M80은4raw×4wheel의 `max(0,force_ratio−1)` 최댓값이며 각 입력의 finite/nonnegative를 먼저 확인한다. 정확한 동률은 원래 활성 페달이 큰 명령을 택한다. epsilon·새 가중치·구제 명령은 없다. 후보가 모두 탈락하면 `EMPTY_FINITE_CANDIDATE_DOMAIN`이다.

**M80은 hold 이후 경로 안전, 누적 heading/횡속도 오차나 완주를 인증하지 않는다.** 매 단계 다시 선택해도 이후 unsafe·진행 실패·유한 후보집합 소진이 가능하다.

## 반복·source·pending의 검증 범위

세 후보를 각 한 번 평가한 뒤 선택 명령만 별도 cold 복원에서 반복한다. 선택 명령의 전체 raw/명령/memory/phase/RNG/full ledger/status/finish event와 생성 길이가 정확히 같아야 한다. **미선택 후보는 독립 반복되지 않으며 전체 후보 순위의 재현성을 검증했다고 표현할 수 없다.** 모든 후보가 독립2회였다는 주장을 하지 않는다.

parent의 full 물리/memory/ledger/RNG/reference/행/status를 각 shadow 전후 정확히 비교한다. fresh shadow는 준비된 after-nominal memory 경로이며 row의 before-memory는 원래 값을 유지한다. full ForecastLedger를 Stream 생성 전에 복원한다. 예측이 parent나 actual DONE을 commit하지 않는다. 선택 반복 통과 후에만 같은 live 모델 부모가 prepared nominal로 own hold를 수행한다. row의 after-nominal memory와 공식 own finish 후의 적법한 after-DONE memory를 구분한다.

첫 raw 힘은 현재 wheel 입력과 원래 source 순서로 정확히 검증한다. 선택 cold→own은 기존 position0.1m/speed0.5m/s/yaw0.05rad/s/joint0.01rad/omega1rad/s/slip0.5m/s/ratio0.05/raw time1e−8 경계와 clipped/grass/contact/damage/collision 등 discrete 정확 일치를 유지한다. broadphase `source_world_contacts` 진단값을 제외하는 복원 identity 경계 외에는 물리 입력 확인을 생략하지 않는다.

각 query에서 모든 단일 평가 점수·유효성·최상위 간격/q* 간격·선택 반복 exact 여부·선택 own 오차를 남긴다. warm-start impulse/contact/island history는 export에 빠져 있다. 새로운 root에서는 선택 명령만 warm own counterpart가 있으므로 **미선택 q*의 warm 반사실이나 전체 live 순위는 관측하지 않는다.** 479의 두 trace 조건부0.10 경계를 이 정책 전체의 순위 보장·optimizer epsilon으로 전용하지 않는다. 작은 점수 차이를 완주 개선 근거로 확대하지 않는다.

pending 경계에는 구현 선행 조건이 있다. 기존 `PendingParent436`의 과거 nominal/fullgas/neutralbrake whitelist는 새 q*/zero 이력의 권한이 아니다. 새 integration은 각 own action을 frozen 정책·nominal/q* 증명·후보 명령 ID·선택 반복 receipt와 연결하고 **전체 tracker/ledger/memory/raw clock 이력과 기존 FINISH_CONFIRM corridor 조건**을 검증해야 한다. whitelist를 무조건 풀거나 과거435 lap을 재인증하지 않는다. 공식 event가 현재 shadow root 이전/동시인 경우 기존 guardian 확인 의미를 유지한다. whole 부모는 원래 pre23부터의 clockmap/관측 이력으로 실제 own event와 confirmation을 따로 기록한다. 예측 finish는 parent finish가 아니다.

source/hash/복원/phase/numeric/RNG/격리/선택 반복/own 연결 오류는 dependent 실행 전체의 기술 중단이며 부분 과금을 보존한다. 재시도·tolerance 확대·추가 probe는 없다. 실제 unsafe/진행 실패/empty-domain은 그 물리적 결과로 구분한다.

## 공간·시간·보존 계약

최신479까지 포함한 실측 최대는 **111,104.402439B/tick**이다. 이전93,191.314만 사용하지 않았다. 이 비율×1.25, world당 보수적 header829,464B, 별도 metadata18MiB로 계산한 B200 model raw 상한은 **1,364,580,771B**다. 여기에 allocator 증명16MiB＋선택 요약16MiB＋temp32MiB＋reserve512MiB를 별도로 포함했다.

402개 allocator 입력/증명은 최대 **4,939,776B**(각4KiB/8KiB), 202개 결정 요약은 최대 **13,238,272B**(각64KiB)다. 각각의 별도16MiB 안이다. constructor/first-step/input은 각2MiB, 기타 atomic 파일32MiB, 추가 integration manifest 성장8KiB를 제한한다. workspace는 full pre23 입력/RNG/P4 geometry·계획·소스·집계·manifest·재현 조건64MiB와 reserve512MiB, 합603,979,776B 대비 가용855,531,520B로 충족한다.

CPU/wall 제안 hard cap은 **900/1,200초**다. allocator는 호출당0.25/0.5초, 합110/220초, kernel wheel 평가100,000/호출과 최대402호출이다. 준비/수입/소스 확인/모든 constructor·fixture·후보·선택 반복·own 적용·증명·종료·두 번의 전체 readback·최종 집계를 포함하고, 별도 프로세스 비용도 합산하거나 미계측 한계를 명시한다. 479 실측을 raw 상한에 비례하면 CPU약628초, 추가25%면약785초이나 이는 예측일 뿐이다. hard cap/절대 종료 중 먼저 도달하면 중단한다. 순차 실행·최대 live worlds2, query/own action마다 checkpoint와 최소10분마다 workspace checkpoint를 둔다. 지정 클라우드만 사용한다.

source manifest의312개 항목은 pretty JSON38,164B였고 runtime-link/observer/final에 같은 전체 map이 반복됐다. constructor369,060B와 first-step369,376B에는 그 map이 없으며 full state가 큰 비중이다. 새 기록에서 immutable authority 원본 한 개와 digest reference를 쓰는 것은 가능하지만, 정확한 map/Authority 복원과 입력·constructor·step binding 확인이 선행돼야 한다. **이 제안은 기존 inline manifest를 유지하는 비용이며 intern·압축·dedup 절약을0으로 계산했다.** 구현·예전 증거 변환·삭제는 하지 않았다.

누적 pending history를 query마다 통째로 복제하는 quadratic 출력은 허용하지 않는다. 완전한 부모 stream은 한 번 보존하고 각 결정은 인증된 이력 prefix에 연결하며 전체 이력 검증을 유지한다. metadata 상한 초과 시 증거를 버리는 대신 중단한다. 새 raw는/tmp 단일 사본, archive0, 기존 파일 삭제/이동0, 모든 새 파일 두 번의 길이/SHA/JSON readback과 최종 control record 해시를 유지한다. stdout이 manifest 확정 뒤 raw 파일을 바꾸지 않게 한다. /tmp 유실은 해시만으로 복구할 수 없고 자동 재실행은 없다.

## 결과 판정과 현재 상태

두 부모 모두 자기 공식 완주를 확인했을 때만 conservative event TickBracket 차이 하한>0으로 엄격한 모델 시간 개선을 판단한다. 한쪽만 완주하고 다른 쪽이 unsafe/censored이면 완주 가능성·상태 차이만 보고하며 숫자 완주 시간 이득을 만들지 않는다. 양쪽 미완주는 완주 이득 없음이다. native/픽셀/HOLDOUT/SEALED·일반화로 승격하지 않는다.

이번480은 설계만 완료했다. 저장 분석의 physics 금지 import guard 시도0, 보호18파일·원장 해시를 확인했고 새 파생 raw3파일63,258B를 두 번 읽어 보존했다. 첫 사전등록의 시간 추정 문구만 분석 실행 전에 최신 비율로 갱신했으며 원래 소스/계획도 비공개 snapshot으로 보존했다. source/meter/phase/pending-history/nominal-once/output cap integration이 실제로 구현·정적 검증된 뒤 최신 공간과 소스를 한 번 동결해야 향후 별도 승인된 실행이 가능하다.

최선 native **13.640초**, 연구 잔액 **26,175**, 예비 **84,000/사용0**, 공식 Participants·main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·기존 백업을 유지한다. 최신 종료는 **2026-10-20 19:01:55 KST**, 자동 연장 없음이다. 정식 기계 판독 계약은 `online480_contract.json`, 이번 저장 분석 결과는 `online480_result.json`이다.
