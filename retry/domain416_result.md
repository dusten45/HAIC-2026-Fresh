# 416 — 진행 속도의 부호·오차·후진 계약을 분리했다

**C의 positive-target 식은 미소 음수 진행 속도에서도 수학적으로 정의된다. 임의 epsilon이나 clip 없이 signed 값을 유지할 수 있다.** 기존의 의미 있는 후진 안전 중단은 유지해야 한다. 저장5364행의 연산 검증과 C nominal188행 대조를 통과했지만, 정확 vertex의 기존 projection 거부, piecewise 기울기 불연속과 COM/origin 기준점 차이는 남았다. 실행 정책은 변경하지 않았고 새 실제·모델 적분도 없다. 정지 재출발 대수의 성립은 안전한 완주 증거가 아니다.

## 수학·물리·수치 계약

같은 사영 선분에서 edge `e`, 접선 `t=e/|e|`, 기존 COM 선속도 norm `v`, 현재 구현의 진행 속도 `sigma=velocity_COM·t`를 사용한다. squared-speed 보간은 `r=sqrt((1-u)*V_i²+u*V_(i+1)²)`, `f=(V_(i+1)²−V_i²)/(2ds_i)`다. 속도와 위치의 기준점이 같은 내부 선분에서는 `dr/dt=f*sigma/r`이다. 현재 C는 COM 속도와 origin 사영을 섞으므로 이 chain rule을 그대로 exact로 주장할 수 없다는 정정을 아래에 따로 남긴다. 기존 구현의 식은 다음과 같다.

`a_C = f*(sigma/r) + 1.5*(r-v)`

r>0이면 유한 sigma의 양수·0·음수 모두에서 정의된다. 정지에서 v=sigma=0이면 a=1.5r>0이다. ±미소 sigma에서도 연속이며, 음수 부호 자체로 대수 정의역을 막을 이유는 없다. 분명한 후진에서도 식 자체는 계산되지만 제어 허용과 다르다. 기존 `sigma<−0.1m/s` 또는 차체 forward velocity<−0.1m/s의 안전 중단을 유지한다. 0.1은 기존390/413의 물리적 안전 기준이며 수치 오차 epsilon으로 새로 선택한 값이 아니다. 작은 음수도0으로 만들지 않는다.

r=0에는 이 positive-target 식을 확장하지 않는다. 0/0은 미정의이며 기존 LAUNCH·STOP·FINISH_CONFIRM·DONE 계약을 유지한다. 새 launch fallback·분모 epsilon·phase 무시 주기화를 넣지 않았다. [사전 동결 계약](domain416_contract.md)에 유도·게이트·검사 범위를 기록했으며, chain rule의 기준점 전제는 [기준점 정정](domain416_point_contract.md)이 보완한다.

## 414의 음수는 내적 반올림으로 생긴 부호 반전이 아니다

Box2D pose·velocity는 binary32이며 Python float 승격은 정확하다. path·profile·JSON float 및 projection/내적은 binary64, 마지막 action은 binary32다. 감사한5364행의 velocity 모두 binary32 roundtrip이 정확했다. solver에 남은 미소 속도, 입력값의 표현 cell, 그 입력으로 내적을 평가하는 반올림 오차를 구분했다.

2차원 구현의 DAG는 edge 차분2, 제곱2·합1·sqrt1, 정규화 나눗셈2, 내적 곱2·합1의11연산이다. normal·유한·비overflow/underflow 입력에서 `u=2^-53`, `gamma_n=nu/(1−nu)`로 두고 edge/norm/접선 오차를 전파하면 보수적으로 다음 absolute 상한을 얻는다.

`|computed_sigma − exact_binary_input_sigma| <= gamma_16 * sum(|velocity_i*t_i|)`

norm relative error를 gamma_6, 접선 component error를 gamma_10으로 감싸고 마지막 dot의 gamma_2를 더해 gamma_16으로 올려 잡았다. 입력 규모와 연산 구조로 정한 상한이며 관측 오차에 맞춰 정하지 않았다. 각 연산을 양쪽 nextafter로 감싸는 interval DAG도 별도로 계산했다. subnormal 합성 검사는 이 interval을 쓰고 상대오차 상한을 강제하지 않았다. Decimal100자리 재계산 및 Fraction 정확 유리수 numerator의 부호와 대조했다. 전체5364행에서 계산값·고정밀 값의 interval 포함과 gamma 상한을 통과했다. 최대 관측 내적 오차2.113×10⁻¹⁴, 최대 상한1.776×10⁻¹³이었고 각 행의 오차/자체 상한 비율은 최대0.170이었다.

414 final의 결과는 다음과 같다.

| 항목 | 값 |
|---|---:|
| 저장 속도 norm | 5.777×10⁻¹⁵m/s |
| NumPy sigma | −3.2834064722633844×10⁻¹⁶m/s |
| 고정밀 sigma | −3.2834064722633852…×10⁻¹⁶m/s |
| exact numerator 부호 | 음수 |
| gamma16 상한 | 4.647×10⁻³⁰m/s |
| 실제 평가 오차 | 8.211×10⁻³²m/s |
| 입력 velocity half-ULP cell의 sigma 범위 상한 | 1.062×10⁻²²m/s |

interval 전체도 음수였다. 따라서 이 부호를 계산 반올림으로 설명해0으로 바꾸는 것은 정당하지 않다. 반면 크기는 의미 있는 후진 기준에 훨씬 못 미친다. half-ULP cell은 가능한 입력 반올림 범위일 뿐 solver의 물리 상태 오차 전체를 인증한 값이 아니다. 기록된 미소 음수와 물리적으로 중요한 후진을 같은 거부 사유로 묶을 필요는 없다.

같은 r=64.023, f=−206.014에서 O raw 요구는 −109.980/brake0.3, signed C 대수는 +96.035/brake0이다. 현재 executor는 여전히 `sigma<0`에서 거부한다. 416은 해당 실행 파일을 바꾸지 않았으며 정적 제안만 검증했다.

## COM 속도와 origin 사영의 기준점 차이

기준점 검사에서 현재 연결의 또 다른 한계를 확인했다. hull origin을 O, COM을 C, local COM offset을 c라 하면 `C=O+R*c`, `v_O=v_C−omega*J(R*c)`다. origin 사영 arc의 시간 미분은 `t·v_O`인데 현재 C는 `t·v_C`를 사용한다. 이 차이를 내적 반올림으로 취급해서는 안 된다. 원 사전 계약의 무조건적인 chain-rule 설명을 정정하되 실행 법칙은 유지했다.

저장413A/B·414 raw hull1816표본에서 local COM offset은 약−0.082531m였다. 저장 COM/origin 속도의 최대 sigma 차이0.08404m/s, 같은 raw C 식의 해당 항만 비교한 차이0.14711m/s², clamp 후 pedal 성분 차이0.0003541이었다. 이 subset에서 기존 진행 후진 안전 분류가 바뀐 표본은0이었다. 새로운 상태·trajectory를 계산한 것이 아니다. 수치 인증은 현재 COM sigma 식에 유효하며 origin arc의 정확한 미분 인증으로 확대하지 않는다. [유도·범위 정정](domain416_point_contract.md), [저장 기준점 검사 코드](domain416_point_audit.py).

## 저장 자료에서 달라지는 판단

| 저장 자료 | 검사 행 | 현재 strict-negative 거부에 걸리는 행 |
|---|---:|---:|
| 390 O0/N1 pre | 506 | 34 |
| 393 같은 상태의 기존 계산 | 506 | 34 |
| 410 저장 forecast post | 3523 | 0 |
| 411 O/C pre | 374 | 0 |
| 413 A/B pre | 258 | 0 |
| 414 pre + final | 197 | 8 |
| 합계 | 5364 | 76 |

390·393은 같은 상태의 중복 비교이고 source forecast들도 독립 에피소드가 아니다. 76행은76개의 독립 증거를 뜻하지 않는다. 서로 다른 `(sigma,r,f,v)` 입력 tuple은19개였다. 이76행의 최대 속도는1.220×10⁻⁶m/s, 최대 |sigma|는5.554×10⁻⁸m/s로 모두 기존 의미 있는 후진 조건 안이다. signed 식으로 평가한 제동은 모두0이었다. 393은 이미 음수에서도 대수를 계산했던 자료이므로 기존393 pedal 값을 바꾼다는 뜻이 아니라 현재 runtime의 strict-negative 판단과 구분한 것이다. 같은393 식 재계산 차이는0이었다.

나머지 nonnegative 영역의 기존 식과 signed 제안은 연산 순서·노드·clamp·pedal mapping이 같다. 저장411 C의 FIRST_LAP nominal188행은 독립 재계산한 float32 gas/brake와 모두 정확히 일치했다. 선택된 실제 guardian pulse와 nominal을 혼동하지 않았다. 연산 interval이0을 포함한6행은390/393의 중복된 정확한 zero numerator3개였고, 부호를 임의로 바꾸지 않았다.

393의 원래 보류3개(출발 arc 영역, 조기 profile lap 분기, 초기 projection tie)는 그대로 보류했다. 현재 FIRST_LAP의 node0 incoming 사영으로 계산한 positive target을 LAUNCH 명령 자격으로 해석하지 않았다. 410 post-state는 runtime phase/memory가 충분하지 않으므로 대수 범위만 검사했다. r=0과 lifecycle의 정의역 구멍을 signed-sigma 확장으로 숨기지 않았다. 고정 합성7개는 sigma=0, ±2^-40, ±1, ±최소 binary64 subnormal이며 유한성·부호 인증과 분명한 후진 안전 분류를 확인했다.

## segment 경계에 남은 문제

같은 vertex의 r>0에서 양쪽 raw 차이는 `(f_R*sigma_R−f_L*sigma_L)/r`다. 접선과 f가 바뀌므로 양측 도함수가 일반적으로 같지 않다. 정지 v=sigma=0에서는 양쪽 raw가 같았지만 이동 중에는 기존 piecewise profile의 점프가 남았다. 고정 두 geometry·세 profile의802개 vertex에서 정지/정방향/후진2406개 probe를 검사했다. 같은 geometry를 profile만 달리 중복 검사한 경우를 구분했다.

- 비seam 정지에서 양쪽 raw 차이 최대0.
- 각 노드 target 속도로 정방향 이동시키는 정적 probe에서 기존 raw 차이 최대304.24m/s², clamp 후 pedal 성분 차이 최대1.0. 비seam119개 profile-vertex에서 pedal 차이가0이 아니었다. 실제 발생 빈도나 새 주행 결과는 아니다.
- 정확 vertex에서 현재 canonical projection이519개 방향 probe,173개 path/profile-vertex를 거부했다. 중복 geometry를 제거하면564개 vertex 중122개 위치다. 모두 인접한 두 segment의 같은 exact endpoint였으며 진짜 서로 다른 사영 위치를 새로 발견한 경우가 아니었다.

예를 들어 길이를 sqrt 후 제곱한 분모의 반올림 때문에 incoming 선분 u가 정확한1 대신1보다 작게 계산돼도 foot은 끝점으로 반올림될 수 있다. 현재 구현은 그 선분을 interior(`vertex=-1`)로 태깅하고, outgoing의 같은 vertex와 묶어 `Distinct_or_nonadjacent_projection_ambiguity`를 낸다. 정확한 endpoint identity로 설명되는 수치 분류 구멍이다. 이 단계에서 epsilon·tie 제거·projection 수리를 구현하지 않았다. node0의 비주기 출발/결승 속도 차이는 별도 phase 문제로 유지했다.

첫 검사기는 이 예상 가능한 boundary 거부를 uncaught 예외로 받아5364행 검사 뒤6개 vertex probe에서 멈췄다. 원기록을 보존하고 완료한 상태의 수치 검사를 반복하지 않았다. 남은2400개 경계 probe에서 거부를 명시적 보류 결과로 기록하고 저장 행을 집계했다. 경계 구멍을 통과로 바꾼 복구가 아니다. 최종 상태는 ‘signed 대수 검증, 경계 구멍 잔존, 정책 변경 없음’이다.

## 다음 최소 대조와 비용

[다음 후보 설계](domain416_next_design.md)는 실패한 O tail 대신 기존 자격 C0와 시간 이득 selector Ctime을 같은 진입 상태에서 비교하는 제안이다. 저장411 C의 현재값 규칙으로119번째 행동 직전을 고정하고, nominal과 첫 gas1/brake0 후 C feedback의 두 recipe만 source 게이트로 검사하는 범위다. 실제 대조는 게이트 이후 같은 prefix118+suffix13의 두 arm, 최소262 wrapper/reset2이지만 지금 실행·예약하지 않았다. 실제 guardian의 추가 예측 비용과 명령 변경은 별도로 산정해야 한다. 국소 이득 뒤에는 C tail carry 검증이 다시 필요하다.

정적 CPU 합계5.185초/wall5.191초로60/120초 상한 이내다. 초기 실행3.452/3.458초, 복구 집계0.922/0.922초, 기준점 검사0.811/0.811초를 모두 포함했다. 최초 준비 wall144.526초와 초기 결과~복구 실행 사이 준비 구간95.973초는 별도다. 완료 결과부터 기준점 검사 실행 전까지의 준비·재검토·보고 구간253.522초도 별도 기록했다. CPU 합계는 세 worker의 분석 계측 구간이며 프로세스 시작/import CPU는 포함하지 않은 미계측 범위다. 준비 CPU 및 후속 보고·설계·git 전체 비용은 미계측이며 추정치로 채우지 않았다.

원장v436: 연구29,880행동·예비84,000(사용0), 실제 누적1,318,184로 변함없다. 새 actual/reset/model적분/world/actor/학습/SEALED/예비/유료 자원은 모두0이다. champion296/rollback240·보호 자료·408 원기록·기한을 보존했고 실행 제어 코드는 변경하지 않았다. [기계 판독 결과·비용](domain416_result.json), [원 검사 코드](domain416_audit.py), [저장 결과 집계·경계 검사 완료 코드](domain416_complete.py).
