# 500 — 미래 제동 scalar envelope 구현·순수 검증 완료; 물리 실행0

한 후보법칙을 [envelope500.py](envelope500.py)에 구현했다. 고정 geometry/P4/SourceC steering을 유지하는 순수 호출 경계이며 새 world/reset/적분/seed/학습/DEV/HOLDOUT/SEALED 노출은0이다. 현재 GT 상태를 받는 진단법칙이며 pixel-only 제출 정책의 자격은 없다. 다음4world 계약은 실행하지 않았다.

## 법칙과 최대 선택

80ms hold에서 `v(t)=v+a*t`, `s(t)=s+sigma*t+a*t²/2`를 쓴다. 시간은 exact rational `k/50,k=1..4`이다. 고정 정확 effective mass는 **29.249793766661764**, rear35.0188778925416, B91.16873397261595다. `a_low=max(-B,-v/tau,-sigma/tau)`와 engine/rear 상한을 사용해 속도·진행속도 비음수를 hold 전체에서 유지한다. 질량을29.24979로 반올림하지 않았다. power map의 `v+2.7` binary64 중간값도 계약에 명시했다.

각 미래 node의 거리d와 속도r에 대해 네20ms 경계에서 미횡단이면 `E=(v+a*t)²-r²-2B(d-sigma*t-a*t²/2)<=0`, 횡단했다면 최초 crossing의 `v-sigma+sqrt(sigma²+2ad)<=r`를 요구한다. 횡단 판정은 `r-v+sigma>=0`와 비음수 discriminant를 함께 검사해 제곱 소거의 가짜근을 배제한다. d=0은 즉시 현재v<=r를 검사한다. seam의 등호는 crossed branch가 소유하며 두 식은 일치한다.

가속도 switch `2(d-sigma*t)/t²`로 algebraic branch를 분할한다. 허용 구간에서 `dE/da=2t(v+at)+Bt²>0`이고 crossing 속도도 단조이므로 각 feasible 집합과 그 교집합은 닫힌 하위 구간 또는 공집합이다. 안정적인 quadratic 큰 근과 crossed 상한의 최소로 real upper cut을 구한다. Decimal80은 근의 seed일 뿐이다. **별도 exact Fraction residual**로 반환 binary64가 feasible이고 바로 위 `nextafter`가 infeasible임을 확인해야 반환한다. 단조성과 합쳐 최대 표현값을 인증하며 grid가 연속 최대성 증명이라고 주장하지 않는다.

정지한 interior 상태는 허용하고 역진·비유한·ambiguous projection·잘못된 node·firstlap 밖은 중단한다. `EMPTY_SET`(연속 공집합), `EMPTY_BINARY64`(실수 feasible이나 binary64 표현값 없음), bounded8ULP 수치 미인증, float32 mapping 미인증을 구분한다. terminal node는 고정된 unwrappedL이다. 이번 hold가L을 넘는 것은 허용하되 마지막 node crossing은 검사하고 launch0으로 wrap하지 않는다. 다음 현재 상태가L 이상이면 자기 tracker의 유효한 기존 terminal handoff 또는 STOP이며 finish를 만들어내지 않는다.

이 법칙은 **네 샘플 경계와 정확한 node crossing**을 검사한다. 감속 중 경계 사이 stopping-envelope의 interior peak까지 모두 검사하는 연속시간 보증은 아니다. 이것을 타이어·조향을 포함한 물리 feasible 인증으로 확대하지 않는다.

## pedal과 검증 증거

원래392 `pedals` 함수만 AST로 분리해 순수 실행한 값과40조합에서 정확히 비교했다. float32 pedal 후 고정 scalar inverse mapping을 다시 계산하고 exact residual을 검사한다. 필요하면 덜 가속하는 인접 pedal로 이동하고 더 가속하는 다음 표현값은 탈락해야 한다. 표현 불가능하면 중단하며 nominal steering bits는 유지한다. 이 inverse는 실제 hold 평균 가속도나 wheel/tyre 힘의 측정값이 아니다.

- 최종 counterexample 검사 **60 fixtures /15,552 grid points**, feasible44/empty16, 반례0. 독립 direct-trajectory Decimal400 검증기를 사용했다.
- 고정된 과거472 상태 **17개 모두 scalar feasible**였다. 자기 후속 상태를 적분한 결과가 아니며 안전 궤적·완주·기록 개선을 뜻하지 않는다. 개별 입력/계산값은 비공개에 남겼다.
- float32 scalar mapping 최대 오차 **4.47131141357e-06m/s²**, 최대 인접 pedal 보정1ULP였다. 오차를0으로 취급하지 않았다.
- [경계·저장 tests](test_envelope500.py) **18개 통과**: closed endpoint/root-on-node, exactly crossing seam,0 인접 subnormal, interior rest, reverse/nonfinite, terminal no-wrap, exact singleton, binary64 없는 singleton, pedal 표현 불가, signedzero, quota·dedup·immutable readback·closing reserve.

첫 독립 Decimal100 검사는0 바로 위 `5e-324`를 허용오차로 놓쳤다. Fraction oracle이 이를 잡았고 검증기만 Decimal400/더 작은 구별 한계로 수정했다. seam fixture는1.8의 binary64와 exact0.8을 혼동해 고쳤다. singleton fixture도 실제로 앞선20ms 경계를 위반한다는 점을 확인해 정확한 dyadic fixture로 교체했다. 법칙/gain/P4를 결과에 맞춰 조절하지 않았다. 이후 표현값 없는 집합의 typedSTOP과 public helper의 signedzero 소유를 명시했고 소스·오류·모든 실행 로그를 보존했다. 8ULP 보정 실패를 실제 공집합의 증명으로 합치지 않는다.

## factual replay의 정당한 범위

473 paired native pre23 before-nominal full snapshot이 exact하고472/453의 첫22 rows와 pre23 memory가 exact함을 저장 자료만으로 확인했다. 기존473 source/Original factual 자격은 유지한다. Original의13행동 native 허용오차 대조와 처음3명령 exact 범위, P4의 독립 model 반복,472의 늦은P4 actual 범위는 서로 다르며 earlyP4 native factual은0이다. 495 C4 자격을 이전하지 않는다.

| 경계 | 실제 저장된 비교 가능 증거 | 한계 |
|---|---|---|
| 전체472 trace |171행/682ticks, 명령·memory·wrapper sensors·ledger/finish·raw tire/hull | 새 trajectory나 독립DEV가 아님 |
| tracker 직후 |position/velocity/progress/time/tracker/collision/wheel-road-contact | 직접 damage/phase 없음 |
| wrapper return |full physical/controller/RNG/elapsed/tracker, damage | tracker-post damage 실측으로 대체 불가 |
| 기존 routing |row.damage 복사, hold phase 할당 | derived임을 표시; 직접 측정으로 승격 금지 |

500에서 after23/126/171 schema와 생성 소스를 확인했고 다음 실행 전에는149개 필요한 receipt/manifest/field 범위를 전부 고정한다. 전체 factual replay는 **관측 궤적의 calibration**이며 미래472 명령을 사용하는 온라인 baseline이 아니다. 후보는 현재 자기 상태와 고정P4만 읽는다. 새 모델 directcapture가 과거 누락을 복원하지는 않는다.

이 제한된 model screening을 위해 새 native 수집이 꼭 필요한 것은 아니다. 직접 tracker-post damage/phase의 native 일치까지 주장하려면 별도 승인 native directcapture가 필요하다. 형식이 새로 생겼다는 이유만으로 과거 source 자격 전체를 무효화하지 않았다. 새 후보 상태 전역의 모델 정확성은 아직 인증되지 않았다.

## 256MiB 저장 계약과 다음 gate

[Store500](storage500.py)는 codec 이후 실제 직렬화 bytes를 쓰기 전에 검사한다. 최대160MiB fullstate+28MiB directtick+28MiB holdbundle+16MiB 기타=**232MiB** final이다. 최대4MiB atomic temp와 합쳐236MiB이며256MiB 안이다. 최대2687 finalfiles+1temp이고 closing용8 metadatafiles/256KiB를 미리 남긴다. 320 fullstate×512KiB,1792tick×16KiB,448bundle×64KiB, 기타 aggregate16MiB·개별4MiB를 적용한다. worst-case metadata는127files이다. 모든 observer/child/common/manifest/header/log/control 출력이 이 분류 안에 들어가야 한다.

실제495 저장본의 tick432개 최대2619B, bundle108개 최대32197B이고 stat-only fullstate25개 최대492658B였다. bundle의 partial capture 중복도 포함했다. 표본을 미래 상한의 보장으로 바꾸지 않는다. fullstate는 손실 없이 exact intern하고 quantize/truncate하지 않는다. 합계·개별 크기 초과는 즉시 중단한다. 기존 raw 복사·변환·삭제0이다.

스토어의 순수 admission/실제 작은 synthetic immutable write 테스트는 완료했다. **모든 legacy runtime writer를 이 스토어로 연결한 것은 아니다.** 다음 실행의 선행 gate는 기존481 semantic codec/reference roundtrip, 모든 writer의 최종 bytes 경로, metadata chunking, failed/temp/closing 포함 한도와512MiB free reserve를 physics poison 아래 확인하는 것이다. 우회 writer나 누락 출력이 있으면 world 생성 전 STOP한다.

다음 계약은 **4world/448holds/1792chargedticks,CPU600/wall900,256MiB** 그대로다. factual replay1world가 먼저 통과해야 후보 cold whole2개와 held first1개를 실행할 수 있다. 안전 finish·정확 반복·held 일치·episode upper<=13.14초를 모두 요구해도 model screening이다. 11.99초 목표, 실제 완주 개선, 독립DEV/HOLDOUT/SEALED 승격을 대체하지 않는다. 현재는 미실행이다.

## 비용·보존

최종 수치 worker CPU4.990895초/wall4.994503초다. 모든 성공 수치 worker, 최초 실패 상한, 독립 source parser와 보수 준비·경계·마감 allowance를 포함한 workload 회계는 **CPU31.072973초/wall40.473185초**, cap180/240초 이내다. 대화·구현 전체 경과시간의 실측은 아니다. 최종18개 경계·저장 tests는0.020초였고 allowance에 포함했다. 파생물16MiB 이내, 연구26027·reserve84000/used0 불변이다. 개인 raw/state/RNG/명령과 상세 source receipts는 비공개에 남겼다.

승인 종료2026-10-20 19:01:55 KST, 자동 연장/후속 실행 없음. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·기존 사용자 변경/백업을 보존한다.

[수치 결과](envelope500_result.json) · [source/storage/cost 집계](envelope500_closeout.json) · [다음 미실행 계약](envelope500_contract.json)
