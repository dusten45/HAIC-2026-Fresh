# 575 — source0 양자화 분기 원인 분리

**두 원인을 분리했다.** tail-only에는 실제 고정0인 aux에 이전 bounds의 수치 margin을 부과하는 구현 문제가 있었다. 이를 한 번 수정해489개 허위 constant-row 모순을 없앴다. 그러나 같은 저장 모델의 tail·확장 LP 모두 여전히 infeasible이었다. 확장 모델은 **row margin과 rank branch 없이도 inward box와 원래 force/causal-norm 제약만으로 모순**임을 별도로 확인했다. 새 FD·보정·후보 실행·보호평가·actual은 모두0이다.573 incumbent를 유지한다.

## 사전 한도와 재구성

`algebra575_contract.json`을 첫 계산 전에 등록했다. 실제 LP 최대24회, 계산 프로세스 누적 CPU240초/wall360초, 각 LP wall10초, 구현 수정 최대1회다. 수정 뒤 후보 cut solve는 최대8회다. 원 제약1e-8 검증, exact ratio>1 clipping 판정 및 물리/정책 한도는 바꾸지 않는다. 대수 후보가 생겨도 실행하지 않는 계약이다.

574의 저장264열 Jacobian, seed526행, 보정2개 테이프와 envelope를 읽어 frozen574 코드로23,965행·396변수 행렬을 재구성했다. 활성 component를 다시 탐색하지 않고 저장 support key의 primitive를 사용했다. 저장 행의 geometry·metric 계산만 했으며 source 적분/force 평가 함수와 Native entry는 차단했다. 원래574는 full A를 저장하지 않았으므로 과거 A와의 bitwise 비교를 주장하지 않는다. 동일 입력·코드 해시, matrix summary 일치 및 두 원래 solver 결과 재현을 확인했고 재구성 full matrix는 비공개로 보존했다.

## exact seed와 tube는 서로 다른 집합

두 분기의 정확한 seed는 모든 원래 선형 행·bounds·capsule·exact ratio 검사를 통과한다. 원래 bounds에서는 z=0, causal aux=0이 가능하다. 양자화 tube는 반올림 오차 q를 포함한 norm 행과 inward control box를 별도로 요구한다. 따라서 exact seed가 feasible인 것과 tube가 infeasible인 것은 모순이 아니다. seed의 별도 분기를 그대로 유지했다.

확장 tube의 box 자체는 비어 있지 않지만 **40개 control 좌표에서 z=0을 제외**한다. seed가 물리 domain 끝점인 좌표에서도 uniform q만큼 안쪽으로 이동하도록 요구하기 때문이다. 단순히 모든 row margin을 지우더라도 이 inward box와 원래 경험적 오차/causal-norm 행이 남는다. 이는 지금의 인증 구성에 관한 한계이며 float32 제어 전체의 불가능성을 뜻하지 않는다.

## tail-only 구현 문제와 한 번의 수정

원래 row21202는 선행 control과 aux가 모두0으로 고정돼 좌변이 정확히0이다. 그런데 이전 aux bounds[0,.05]로 계산한 numerical margin **4.4408920985010206e-15** 때문에 우변이 그 음수가 됐다. **한 constant 행과 고정 bounds만으로 0≤−4.44e-15라는 모순**이 성립한다. 이런 행은489개였다. 확장 분기에는 negative constant row가0개여서 동일 문제로 설명할 수 없었다.

`causal575_rounding.py`만 새로 만들어 정확히 고정0인 controls의 q=0과 그 prefix aux=0을 numerical magnitude에도 전달했다. variable-dependent 항이 없는 constant 행의 numerical margin은0이다. 자유 변수에는 원래 유효 box magnitude를 유지하며 inward box의 더 작은 magnitude로 대체하지 않는다. causally 영향을 주지 않는 Jacobian의 정확한0과 fixed q=0은 행별 `abs(A_control) @ q` 및 path radius에서도0으로 남는다.574 원본과 원 제약 checker는 보존했다. 물리 한도/1e-8/clip 기준을 완화하지 않았다.

실제 LP를 호출하지 않는 재현 단위검사 **6개 통과**: old negative RHS, fixed-prefix uncertainty, 미래 변수의 zero-row 영향, 자유 box 보존, constant 행과 양의 scaling, 기존 seed/exact ratio checker 일치다. 테스트의 solver는 입력을 포착하는 stub이며 실제 LP 수에 포함되지 않는다.

## solver status와 독립된 근거

| 분리 검사 | tail-only | 확장 |
|---|---|---|
| 원 대수·원 bounds | feasible | feasible |
| 원래 tube | infeasible | infeasible |
| numerical margin만 제거 | infeasible | infeasible |
| rounding row margin만 제거, numerical/inward 유지 | feasible | infeasible |
| 양의 row scaling | — | infeasible |
| rank branch 제외 | — | infeasible |
| 모든 row margin 제거, inward만 유지 | — | infeasible |
| 한 번 수정한 tube | infeasible | infeasible |

위 표의 feasible/infeasible은 solver 보고값이며 margin 제거는 원인 분리용으로만 사용했다. 특히 old tail의 rounding margin 제거 실험에는 작은 constant 모순이 남는데도 solver가 status0을 보고하므로 엄밀한 feasibility 인증이 아니다. 이 허용오차 효과와 별도로 seed의 원 행 직접 검증 및 아래 모순 증거를 사용한다. 수정 후 negative constant row는 양쪽 모두0이다. 따라서 tail 구현 문제는 실제였지만574 전체 실패의 충분한 설명은 아니다. clipping rank branch 역시 확장 실패에 필수인 제약은 아니었다.

별도 scaled phase-I에서 얻은 비음수 가중치를 원 행에 적용한 뒤, solver와 독립적으로 longdouble 가중합과 유효 box의 최소 좌변을 계산했다. cancellation residual을0으로 간주하지 않고 box 하한에 포함했다. 원래 행보다 적은 행으로 줄인 증거는 다음과 같다.

| 모순 증거 | 행 수 | box 최소좌변−가중우변 | 보수적 연산오차 여유 |
|---|---:|---:|---:|
| 수정 tail tube |29|2.08489665e-7|1.15454030e-13|
| 수정 확장 tube |116|2.52034338e-8|1.61691597e-13|
| 확장 원 행+inward만 |139|1.26809650e-8|1.68863826e-13|

모두 엄격한 양의 차이가 연산오차 여유보다 크다. row ID·비음수 weights·가중 RHS·box 하한은 `algebra575_recheck.json`에 있다. 최소 IIS나 정확한 유리수 Farkas certificate를 주장하지 않으며, 저장된 이진 부동소수점 행렬/box에 대한 보수적 수치 모순 검증이다.

확장은 더 단순한 원인 증거도 있다. **원래 physical row2893(raw458, wheel2의 force slack)**만 남기고 `t>=max(abs(z[:162]))`와 inward box로 완화해도, piecewise-linear 최소 좌변은 **0.00202584106690309**로 우변 **0.000115164012061575**를 넘는다. 차이0.00191067705484는 보수적 연산오차3.08214e-11보다 크다. 실제 최소 t는1.98682155181e-6이다. 각 t에서 제어 box와[-t,t]의 교집합에 선형 최적점을 넣고 유한 breakpoint122개를 검사한 닫힌 계산이며 새 LP나 source 평가가 아니다. 같은 방법의 row2426은 모순을 만들지 않았다는 음성 결과도 보존했다. 이로써 특정 force 행의 경험적 오차 패널티와 inward domain 이동의 충돌이 충분조건임을 확인했다.

## 종료·비용·보존

수정 재검사에서 대수 후보는0개다. 새 점의 예측 개선이나 반올림 후 원 행 통과를 주장하지 않는다. 정확한 seed의 예측 개선은0이며 원 행 검증은 통과한다. 보간13.193602510361초, 점수660 raw/13.20초, Native13.66초는 그대로다.

실제 LP **18/24회**, 계산 CPU **20.878063/240초**, 누적 wall **20.855186/360초**를 사용했다. 단위검사/시작 비용의 보수적5초와 마지막 행렬/소스 해시 감사도 포함한다. source/force/새 FD/새 보정/후보 실행/actual/Native/HOLDOUT/SEALED/유료 자원 모두0이다. 연구22,758·예비84,000·예비사용0을 유지한다. 원래574 소스와 저장 입력 해시가 일치한다. 원시 state·명령·행렬·상세 테이프는 저장소 밖에 보존하고 기술 코드와 집계/증거만 일반 commit/push한다. main·Participants·사용자 변경·백업을 유지한다.

575는 여기서 종료했다. 다음 판단에 필요한 장애물은 보수적 경험적 오차모델과 uniform inward tube의 결합이며, 원래 제어 공간이나 실제 물리의 한계로 일반화할 수 없다. 두 번째 구현 수정·추가 solve·새 source 단계로 전환하지 않았다.
