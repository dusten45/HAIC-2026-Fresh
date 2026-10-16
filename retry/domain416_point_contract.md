# 416 기준점 정정 — 현재 C는 COM 속도로 origin 사영을 평가한다

사전 계약의 chain rule 설명에는 ‘속도와 사영 위치의 기준점이 같음’이라는 전제가 빠져 있었다. 현재 `sensor`/`canonical_projection` 연결은 hull origin 위치를 사영하면서 Box2D `hull.linearVelocity`, 즉 COM 속도를 받는다. 따라서 현재 sigma_COM 식의 수학적 정의·signed 확장·부동소수 인증과, origin의 정확한 arc 시간 미분은 구분해야 한다. 원 사전 계약·검사 기록을 보존하고 이 정정을 추가한다. 실행 C는 바꾸지 않았다.

origin을 O, COM을 C, local COM offset을 c, 회전을 R, yaw rate를 omega, 90도 회전 행렬을 J라 두면 `C=O+R*c`, `v_O=v_C−omega*J(R*c)`다. 사영 segment 내부에서 origin arc의 시간 미분은 `sigma_O=t·v_O`이고 `dr/dt=f*sigma_O/r`이다. 현재 구현은 `sigma_C=t·v_C`를 대입한다. 차이는 `sigma_C−sigma_O=omega*t·J(R*c)`이며, 반올림 오차 허용치로 없앨 항이 아니다. feedback의 speed norm v도 현재 COM 기준으로 유지한다. 이 단계는 기존 법칙의 기준점 의미를 명시하며 origin-only 새 법칙을 제안·적용한 것이 아니다.

저장413A/B·414 raw hull1816표본에서 local COM은 약 `(1.48e−9, −0.082531)m`였다. `GetLinearVelocityFromLocalPoint((0,0))`의 저장 origin 속도와 저장 COM 속도를 비교했다. 최대 진행 속도 차이는0.08404m/s, C raw 가속에서 이 항만 바꾼 차이는0.14711m/s², clamp 후 pedal 성분 차이는0.0003541이었다. 이는 동일 저장 상태의 입력 기준점 비교이며 다음 상태를 생성하지 않았다. 이1816표본에서 기존−0.1m/s 진행 후진 분류가 달라진 표본은0이었다.

float64 삼각함수로 재구성한 기구학 origin 속도와 Box2D가 binary32로 반환한 저장 origin 속도의 차이는 최대1.596e−5m/s였다. 이 값을 새 허용치로 채택하지 않았다. 현재 COM sigma의 Decimal/Fraction/interval 검증은 그대로 유효하지만 origin arc의 exact chain-rule 인증으로 확대하지 않는다. 다음 C0/Ctime 최소 대조는 두 arm에 같은 기존 COM 의미를 유지해야 하며, 기준점 수정과 시간 선택의 효과를 섞지 않는다. 실제 안전·완주·기준점 수정의 성능은 미검증이다.
