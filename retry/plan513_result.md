# 513 — 공통 조향 검증 통과, 제동거리 후보는 엄격한 계획 경계에서 중단

512를 변경하지 않고 새 계약으로 진행했다. **공통 조향의 모델·native 안전 gate는 통과했다. scalar는 목표 지점을 통과했고 response는 다음 명령 선택에서 멈췄다.** 이번 response 패키지는 실질적 효과 gate 미통과이며 방법군 전체를 기각하지 않는다.

## 동결한 변경과 선행 검증

[사전 계약](plan513_contract.json) · [공통 제어](plan513_control.py) · [모델 상태/형상](plan513_model.py) · [선행 실행](plan513_preflight.py).

공통 steering은 현재 지도 직선축의 `현재 station+max(12m,0.4s×COM속력)`을 추적하는 pure pursuit다. hull 방향과 목표 벡터의 cross로 곡률을 계산하고 wheel target=`atan(3.24m×곡률)`, ±0.15rad 제한 후 source 부호에 맞춰 float32 action을 만든다. 한 파라미터 설정만 사용했고 sweep은 없다. 두 arm 모두 reset 직후부터 같은 feedback을 쓰며, 첫24holds의 gas0.32/brake0은512의 가속 일정과 같다. 미래 실제 명령이나 관측을 replay해 prefix를 운전하지 않는다. response의 가상 최대제동 rollout에서도 같은 steering을4tick 경계마다 갱신한다. 이 부분은 공통 steering 변경에 필요한 예측 일관성 변경이다.

512의 gate 산출법, 물리 속도목표30±0.5m/s, 공유 planning node29.85m/s, 페달 범위, scalar500 법칙, response coarse bracket/18bisections와 실질적 효과 기준은 유지했다. 후보가 목표에 안전하게 도달하면서 scalar 계획 중단/과속을 피하거나, 양쪽 통과 시 crossing 시간 bracket으로0.08초 이상 빨라야 승격한다. pixel reference 호출은 memory bookkeeping일 뿐 실제 조향/첫24가속을 정하는 pixel 제출 정책이 아니다.

저장 reset에는 전체 planar/joint snapshot이 없었다. 관측 State·위치·접촉을 사용하고 trigger의 rigid 배치를 reset rear heading으로 돌려 시작 상태를 **재구성**했다. yaw/rates/momentum의0 설정과 배치는 재생 검증 대상이며 exact 복사 snapshot으로 표시하지 않았다. trigger는 저장된 full model 입력을 복사했다. 모델에는 solver warm-start impulse·broadphase history가 없고 rigid planar/joint 근사를 쓴다.

먼저512 실제 명령을 재생해 calibration만 수행했다. 허용치는 위치0.10m, 속도0.15m/s, road margin 차이0.10m, trigger 경계 방향0.02rad/yaw0.05rad/s, 유효마찰 불일치0이었다. factual 미래 명령·실측 접촉은 이 대조에만 사용하고 이후 후보 계획에는 전달하지 않았다.

| 저장 재생 | ticks | 최대 위치 오차 | 최대 속도 오차 | 최대 margin 차이 |
|---|---:|---:|---:|---:|
| 재구성 시작, 첫24holds |96|0.00009992m|0.00023657m/s|0.00006944m|
| 복사 trigger, 다음4holds |16|0.00003031m|0.00012143m/s|0.00002083m|

trigger 방향 오차0.00000125rad, yaw 오차0.00000592rad/s, 유효마찰 불일치0이었다. 시작 상태의 누락된 yaw/angle 관측 일치는 주장하지 않았다.

이어 **시작/trigger × scalar/response 네 개의 자기 예측 궤적**을 각각 실행했다. 모두 측정 지점에 도달했고 full hull/wheel sampled margin의 최소값은 시작 기준5.091973m, trigger 기준4.858307m였다. 최대 횡오차는 각각0.177060m/0.422951m였다. 한 nominal 속도 궤적의 통과를 양쪽 안전성으로 대신하지 않았다. 이 검사는 해당 네 모델 궤적의 qualification이며 보편적·연속시간 안전 보증이 아니다. 모델상 raw 종료 시각 차이는 약0.02초로0.08초 효과 기준에 못 미칠 가능성도 미리 보고했다.

[모델 결과](plan513_preflight_result.json). 순수5tests가 source 엔진/후륜 ramp, 기존 무가스 예측, pedal/gate 범위, 상태 roundtrip·feedback 부호를 확인했다.

## 실제 DEV 짝 비교

[실행 계약](plan513_execution_contract.json) · [native 실행](plan513_run.py) · [실행 결과](plan513_result.json).

같은 기존 DEV identity를 확인했고 두 reset의 full model-input/관측/RNG fingerprint 및 action25 trigger가 일치했다. 첫24action·관측도 두 arm에서 exact였다. 이후에는 자기 현재 상태의 같은 steering feedback을 쓰므로 명령 숫자가 계속 같아야 한다고 요구하지 않았다. 미래 실제 상태·접촉·보호 평가 조회는 후보 입력에 없다.

| 실제 결과 | scalar | response |
|---|---:|---:|
| dispatch한 actions |36|35|
| 첫 제동 action / 제동 actions |31 / 6|31 / 5|
| 종료 이유 |GATE_CROSSED|RESPONSE_STOPPING_SET_EMPTY|
| gate 통과 시간 bracket |[2.86,2.88]s|없음|
| gate 보간 시간 / 속력 |2.869674s / 29.657578m/s|없음|
| 최소 raw hull/wheel 여유 |5.091974m|5.091974m|

두 world 모두 안전/source/관측/마찰/payload 오류0이었다. response의36번째 명령은 dispatch하지 않았다. 동일35actions·2.8초에서 response station은 scalar보다0.506683m 앞섰지만 공식 타일 진행률 차이는0이고, response의 목표 지점 통과가 없어 시간 이득이나 성공으로 승격하지 않는다. 양쪽 모두 공식 finish가 없으며 과거13.640초와 직접 비교하지 않는다.

## 저장 상태로 좁힌 중단 원인

[저장 진단 코드](plan513_saved_diagnosis.py) · [진단 집계](plan513_diagnosis.json). 새 native 없이 사전 고정한 두 평가(현재 최대제동, 직전 명령 예측 다음 상태의 최대제동)만 수행했다. 별도 모델 상한2048ticks/CPU30/wall45초와 전체 모델200000tick 상한 안이다. 명령 선택 재시도·gain/목표/허용치 변경은 없다.

중단 시 gate까지1.708008m였다. 직전35번째 명령의 예측 다음 상태에서 최대제동 gate 속력은29.84999387m/s로 planning node 아래였다. 실제 다음 상태를 모델 입력으로 한 최대제동 예측은 **29.85000547m/s**, node보다 **0.00000547m/s 높아** 엄격한 feasible 검사가 탈락했다. 실제−예측 COM 위치 차이0.00000360m, 속력 차이+0.00000188m/s였다.

이는 단순 binary64 마지막 비트 비교 오류로 취급할 수 없다. 모델과 native 상태의 비영점 차이가 있고 후보가 거의 최대 brake로 제동거리 경계에 붙어 있었다. 작은 평균 예측 오차만으로 다음 상태의 feasible 집합 유지를 보장하지 못했다. **물리 목표30±0.5m/s가 불가능하다는 증거는 아니며**, 최대제동 예측을 실제 통과 측정으로 바꾸지도 않는다. 이번 패키지의 무여유 nominal feasibility 처리에 대한 제한된 반증이다. 사후 허용치 완화나 실제 rescue 없이 멈췄다.

다음 검토 대상은 상태/모델 오차 아래에서의 재귀적 가능성과 물리 목표구간의 일관된 사용이다. 그 수정 자체를 시간 성과로 취급하지 않고, 이번 접근 구간의 예측 시간 이득도 작았다는 점을 함께 본다. 효과 규모가 확인되기 전에 pixel 추정 연구나 추가 native 소비로 확대하지 않는다.

## 비용·오류 복구·보존

[검증/비용 집계](plan513_summary.json). 실제 **71actions·2resets·386rawticks=reset102+action284**를 전수 확인했다. charge71개 연속, 모든 action4ticks·reference1회 호출이며 두 world 모두 body/joint0으로 닫혔다. 연구 **25875→25804**, 예비84000/used0이다. 상한400/2/1702를 소진하지 않았다.

모델은 preflight5244+native 예측2602+저장 진단10=**7856 runtime ticks**다. 순수5tests 한 번의 integrator 호출67ticks를 별도 계수했고, 이번 단계의 동일 suite5회(준비·preflight·실패한 native 준비·native 실행·비용 검증)의 fake fixture335ticks까지 합쳐 **8191 model ticks**다. 실제 world를 만든 테스트는 없다. worker·비용 검증·실패/준비 보수 allowance 합계CPU13.284436초/wall13.316363초이며240/360초 이하이다. native worker만CPU6.247493초/wall6.275997초다. child tests와 실패1CPU/1wall·준비1CPU/1wall allowance를 포함하지만 구현·최종 출판까지 대화 전체 시간을 완전히 계측한 값은 아니다. private555files/5,133,917B로64MiB/3000files 이하이며 raw/model 입력과 명령은 private에만 있다.

최초 native 준비에서 preflight와 같은 immutable `pure-tests.json`에 쓰려 해 FileExistsError가 났다. 당시 world/reset/action0이었다. 원본 runner·실패 기록과 원래 계약을 보존하고 native 전용 파일명만 수정한 실행 계약을 등록했다. 모델·제어·목표·판정 기준은 그대로이며 preflight와 실제 물리는 재실행하지 않았다. 기존512 결과·실패·백업도 그대로다.

main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, 공식 Participants·사용자 변경·기존 백업 보존 조건을 유지했다. 새 seed·HOLDOUT/SEALED 조회0, 지정 cloud만 사용했다. 승인 종료는2026-10-20 19:01:55 KST이며 자동 연장이나 추가 실제 실험은 하지 않았다.
