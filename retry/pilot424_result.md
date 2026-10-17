# 424: 12회 현재 상태 재질의의 모델 전용 pilot

**같은 알려진 root의 새 C0/P 모델 실행이 각각12회 결정 뒤 공식 model finish에 도달했다. 남은 시간은 C0 5.62–5.64초/P4.62–4.64초로 모델 이득 [0.98,1.02]초다.** P는1·3·11번째 질의에서 fullgas, 나머지는 nominal을 선택했다. 마지막 선택 witness와 최종 모델 finish bracket은 같아 이후 C nominal continuation에서 이득 상쇄를 관측하지 않았다. 새 실제 실행은0이고 실제 게이트는 닫혔다. 이 결과는 같은 DEV 자료의 모델 양성이며 독립 일반화·11초 가능성·픽셀296의 증명이 아니다.

## 시작 전 계약과 423 재현

계획 SHA-256은 `2ff3783ba4325f46aa9db40f9ab4eadc77d0fcb63c84a8c5d108bb6dab5b9d06`다. 모델 상한131,072 ticks/256 worlds/CPU600초/wall900초/적분 순차1개와 첫 기술·fidelity·정의역·복원·독립 반복·부모/RNG·memory·ledger·비용 오류 중단을 동결했다. baseline guardian 둘 다 불가에서도 중단한다. 제어 horizon13, 세 recipe, gain, projection, signed C, finish witness, 419 선택 규칙은 유지했다. 12회는 연구 적용 범위이며 배포 시점 트리거가 아니다.

모델 시작 전 정적16개 검사가 실제/예측 원장 분리, 저장 receipt 복원·선택 재계산, 종료 경계,12회 질의의 최악 tick 여유와 가까운 상태의 별도 root stamp를 통과했다. 정적 적분은0이었다.

pilot 전에 저장423 C0/P의 실제 fork에서 실제 명령을 고정 입력으로 각각 독립2회 모델 재현했다. C0 71/P63행동의 첫13과 continuation 전체에서 body/wheel/raw hull·phase·clip flag·finish metadata를 통과했고 공식 finish bracket도423과 일치했다. 재현 두 번의 모델 full signature는 같았다. continuation 최대 body 위치 오차는 C0 0.000184m/P0.000277m, raw hull origin 오차0.000187/0.000277m 미만이었고 clip flag 차이0이었다.

이는 저장 명령에 대한 **물리 재현 자격**이다. 모델에서 별도로 다시 계산한 nominal과 실제 nominal의 최대 차이3.50e-6/7.10e-6은 기록했으며, 이를 명령·controller memory 전체의 정확한 폐루프 재생으로 부르지 않는다. root nominal은 정확히 일치했고 phase는 전체 구간에서 같았다. 모델 분기의 memory는 자기 상태에 따라 진전하며 실제 trajectory의 수치 memory를 매번 주입하지 않았다.

실제로 관측했던 P의 세 query current state도 새 모델로 각각2회 복원해 선택 첫 전이와 phase·clip flag를 확인했다. 보유 root 부모·입력 memory·global RNG·불변 실제 ledger는 모든 fork/재현 뒤 보존됐고, 보유 부모의 다음 nominal 전이는 독립 모델의 첫 전이와 맞았다.

이 실제 미래 기록은 별도 자격 함수에서만 사용했다. 자격 완료 뒤 pilot 부모를 root에서 새로 만들었고 선택 입력은 현재 모델 상태와 새 모델 evidence뿐이다. 캐시 lookup/재사용은0이며 모든 world/질의를 새로 계산했다. 가까운 상태·미래 actual 기록의 캐시나 선택열 재생은 없다.

## 12회 선택과 후속 상쇄

C0는12회 모두 nominal을 유지했다. P는 매 선택 후 부모에 첫 명령만 적용하고 다음 현재 모델 상태에서 재질의했다. 분기 memory를 부모에 commit하지 않았다. actual GoalLedger는 불변이며 예측 진행은 별도 ForecastLedger에서만 갱신했다. 두 부모24개의 선택 첫 모델 전이는 독립 선택 child와 비교를 통과했다. P receipt12개 모두 저장·복원 digest와 typed selector 재계산이 일치했다.

| P 질의 | 선택 | 해당 현재 상태의 보장 모델 이득 | root 기준 선택 witness finish ticks |
|---|---|---:|---:|
| 1 | fullgas | 0.58–0.62초 | [251,252] |
| 2 | nominal | 엄격 이득 없음 | [251,252] |
| 3 | fullgas | 0.02–0.06초 | [249,250] |
| 4 | nominal | 엄격 이득 없음 | [249,250] |
| 5 | nominal | 엄격 이득 없음 | [249,250] |
| 6 | nominal | 엄격 이득 없음 | [249,250] |
| 7 | nominal | 엄격 이득 없음 | [249,250] |
| 8 | nominal | 엄격 이득 없음 | [249,250] |
| 9 | nominal | 엄격 이득 없음 | [249,250] |
| 10 | nominal | 엄격 이득 없음 | [249,250] |
| 11 | fullgas | 0.34–0.38초 | [231,232] |
| 12 | nominal | 엄격 이득 없음 | [231,232] |

8·9·10·12번째 질의는 nominal과 fullgas 명령이 이미 같아419의 기존 alias 규칙으로 고유 recipe2개만 계산했다. 나머지는3개였다. 총32개 고유 candidate와 각각의 독립 반복이 모두 finish했다. 실패·검열 tail은 없었으며 그런 tail에 시간을 추정하는 규칙은 추가하지 않았다. 보장0.08초를 보편 선택 기준으로 쓰지 않았다.

서로 겹치는 질의 이득은 합산하지 않는다. 첫 선택 witness [251,252]에서 최종 [231,232]까지 추가 모델 이득은 [0.38,0.42]초였다. 마지막 witness와 최종 bracket은 동일하며 그 차이 bracket은[-0.02,0.02]초다. 최종 공통 root C0와 P의 공식 finish로 전체 모델 이득을 계산했다.

| 새 모델 부모 지표 | C0 | P12 |
|---|---:|---:|
| 결정 수 / 총 모델 행동 | 12 / 71 | 12 / 59 |
| 12회 뒤 C nominal continuation 행동 | 59 | 47 |
| 공식 root 이후 finish bracket | [281,282]ticks | [231,232]ticks |
| 남은 시간 | 5.62–5.64초 | 4.62–4.64초 |
| 확인까지 raw ticks | 283 | 233 |
| 최대 post 경로 오차 | 1.135m | 1.278m |
| 최대 force ratio | 1.114724 | 1.458443 |
| clipped wheel samples | 6/1132 | 43/932 |
| damage / 예측 진행 게이트 | 0 / 통과 | 0 / 통과 |

공식 crossing raw clock을 사용했고 늦은 wrapper 확인 tick으로 대체하지 않았다. P12의 선택 부모 최대 q1.458443은 root 이후45번째 행동 raw2/wheel1에서 나왔다. 모든 미선택 candidate까지 포함한 최대 q는1.782189다. 두 값을 혼동하지 않는다. clip 수가 다른 것은 서로 다른 주행 길이의 표본 수이며 안전성 개선 주장으로 쓰지 않는다. q>1은 기존 규칙대로 독립 veto가 아니다.

423에서 실제 확인한 것은 **이전3회 정책의 공식15.080/14.440초·이득0.640초**다. 이번 새12회 정책의0.98–1.02초는 모델 결과다. 새로운11번째 선택 뒤의 상태, q1.458/미선택 q1.782 영역과 새 전체 carry는 실제 자격을 얻지 않았다. 423 실제 결과나 이번 재현 게이트를 이 영역으로 확장하지 않는다.

## 비용과 보존

| 새 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| 저장423 실제 명령 첫13+continuation 재현 | 533 | 533 |
| 실제 current state3개 첫 전이 복원 | 12 | 12 |
| C0 guardian13 | 624 | 624 |
| P candidate initial13 | 1664 | 1664 |
| 같은 candidate child의 C tail | 5843 | 5843 |

보유 자격 부모4tick과 C0/P 부모 진전·최종 tail516tick을 더해 **17,872 ticks/101 worlds**다. 자격 총1094tick, C0 guardian1248tick, P 질의15014tick, 부모516tick을 분리했다. initial13과 tail은 같은 child를 이어 적분했으며 초기 구간 재적분·이전 모델 비용 중복 청구·캐시 hit은0이다. 예약·확정 tick은 같고 미확정0, zero-time contact setup101, 최대 보유world7/적분 순차1개였다.

whole model worker CPU **56.048초**, 실행 wall **55.320초**다. CPU에는 import·제어·snapshot·hash·I/O·정리가 포함된다. tag별 constructor/step 시간만으로 전체 비용을 대체하지 않으며 실행 wall에는 import가 완전히 포함되지 않는다. 정적 CPU/wall0.173/0.177초와 저장 분석 CPU0.834초는 별도다. 준비 wall134.025초는 초기 읽기·설계 제외의 부분 구간이고 준비 CPU·보고/git 전체 비용은 미측정이다.

새 실제 wrapper/reset/actor/학습/SEALED/예비/추가 유료 자원은 모두0이다. 원장v444는 연구 잔여28,986·최종 예비84,000/사용0·실제 누적1,319,078을 유지한다. 공식 main·Participants·사용자 변경·champion296·rollback·보호 자료와420–423 전체 파일 manifest를 보존했다. HOLDOUT/SEALED는 열지 않았다. 원 map/seed/state/RNG/명령·전체 receipt는 비공개 경로에만 보존했다.

## 다음 실제 전이 보정 제안 — 미실행

새11번째 선택(이 연구 root의 suffix11, history 기준129)과 그 후속 전이가 첫 새 검증 범위다. 최고 q는 suffix45에 있으므로 첫13만 실제 보정하면 새 최고 clipping 영역을 놓친다. 별도 승인 시 **같은 C0/P 두 arm을 각각 prefix118+최대 suffix58행동**으로 한 번씩 제한하는 보정을 제안한다. 58은 모델의45번째 최고 q 이후 기존13행동 진행 구간까지 포함하는 실험 상한이며 실제 선택 트리거나 제어 horizon 변경이 아니다.

P 첫12 선택은 실제 현재 상태에서 재계산하고 이후 기존 guardian만 사용한다. 예상11번째 선택을 고정 재생하지 않는다. 마지막 기존 명령 일치까지423을 대조하고 첫 새 선택·매 현재 선택 전이·일치 initial13 witness·후속 clipping/phase·부모/RNG/memory/실제 ledger를 확인한다. guardian이 명령을 바꾸면 원래 nominal witness 대조와 실제 정책 결과를 분리한다. 첫 오류에서 전체 중단하며 공식 finish가 관측되면 기록하고, 상한에 이르면 남은 시간 없이 검열한다.

계획량은 **352 wrapper/reset2**, 실제 상한400/모델 제외 CPU120초/wall240초를 제안한다. 모델 상한은131,072ticks/512worlds/CPU600초/wall900초/순차1개다. 12회 최악 고유3recipe 질의92,448tick + guardian104회 양쪽 recipe 최악21,632tick + 현재 자격 여유1094tick =115,174tick, 최대499world로 상한 안에 둔다. 이 수는 비용의 보수적 상한이며 성능·실행 시간 예측이 아니다. 연구 잔여는 계획352 사용 시28,634, 실제400 상한 모두 사용 시28,586이며 예비는 쓰지 않는다.

이 제안은 **실행하지 않았다**. suffix58 보정도 미관측 공식 finish 이득 전체를 인증하지 않으며 새 전체 actual carry는 별도 증거와 승인이 필요하다. 독립 실험·실제 실행·자동 연장은 시작하지 않는다.

[기계 판독 결과·제안](pilot424_result.json) · [423 실제 carry](carry423_result.md) · [419 고정 선택 규칙](planner419_result.md)
