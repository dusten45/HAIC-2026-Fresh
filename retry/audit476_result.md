# 476 순수 산술 할당 구현·검증

새 physics/native/world/reset/actor 호출은 모두 **0**이다. 후보는 실제 source-order 첫 raw clipping 초과량 `M(q)=max_w max(0,norm_w(q)/limit_w−1)`을 최소화하고, 정확한 동률이면 가장 큰 float32 pedal을 선택한다. 실수 근의 반올림이나 epsilon을 사용하지 않는다. 궤적을 새로 만들거나 저장 명령을 실제로 전달하지 않았다.

## 확보된 상태와 q0 재현

추가 탐색으로 native 533개 결정의 full before 파일을 찾았다. 473 모델 궤적에는 시작 root 두 개만 full before가 있어 독립 재구성 가능 범위는 **535/665 결정**이다. 나머지 모델 130개 결정은 full wheel before-state가 없으므로 telemetry 기반 조건부 분석으로 남겼다. 475가 이 추가 파일 범위를 아직 검증하지 않았던 한계를 이번에 해소했다.

저장 wheel angle에서 libm sinf/cosf로 방향 벡터를 만들고 wheel의 저장 linearVelocity와 내적했다. hull 속도나 추정 wheel 속도를 사용하지 않았다. 원래 source는 wheel COM linearVelocity를 사용하므로 임의 hull 점 속도 보정도 하지 않는다. 저장 wheel tile 목록·road friction·grass multiplier와 damage→grip/engine 식으로 마찰 한계를 재구성했다. **535개 모두 vf/vs·마찰 한계·q0 gas/omega/종횡력이 첫 raw telemetry와 정확히 일치했다.** 이는 이 저장 표본에서 cached rotation 재구성이 확인된 범위이며 모든 Box2D 상태의 보편적 동일성 주장이 아니다. 미래 adapter는 살아 있는 wheel의 GetWorldVector/linearVelocity를 직접 읽는 계약이다.

전체 665개 결정의 첫 raw 2,660 휠 표본에서도 기존 명령 q0 산술이 오차0이었다. 모델 후속 입력은 직전 저장 omega의 원래 clipping/reaction 항등식으로 연결한 조건부 재현이다. 전체 solver 궤적의 독립 복원이 아니다. 모든 실제 저장 상태는 damage0이다.

## 구현과 검증 범위

`allocator476.py`는 비음수 float32 bit rank의 정수 구간을 사용한다. 고정 상태에서 signed 종력이 증가/감소/상수인 경우를 구분하고, 영점 양옆과 양쪽 경계를 찾아 wheel별 허용 구간을 교차한다. 실제 `excess<=threshold` 판정을 사용하고 float64 threshold rank를 이진 탐색한다. 최소 threshold의 바로 직전 값은 불가능하며 선택 q 다음 값도 불가능함을 별도로 검사했다. rank↔실수 값과 바로 직전 threshold 관계도 독립 검사했다. 전수 float32 탐색은 없다.

현재 NumPy **1.26.0**, Python float 상태, 명목 float32 명령의 native32/model64 전달 경로에서 검증했다. 양의 engine/limit과 유한 중간 연산을 요구한다. NaN·overflow·잘못된 scalar dtype·비양수 limit·wheel 중복·none 분기의 비영 q0는 기술 중단으로 분리한다. square의 유한 underflow가 만드는 실제 반올림 plateau는 허용하며 실수 산술 최적해라고 주장하지 않는다.

**36개 fixture 통과**, 그중 34개 유한 구간은 총 **2,786개 명령값을 독립 source 식으로 전수 대조**했다. 생산 검색 전체를 사용하는 subnormal 작은 영역, 일반 구간의 제한된 rank 창, 서로 반대인 rear 요구력, ±0, 내부 최적점, gas ramp 경계·plateau, 일반 brake·zero clamp·lock 및 `.9` 인접 float32를 포함했다. 제한된 창의 전수 결과를 전체 float32 영역의 전수 검증이라고 부르지 않는다. synthetic engine .8 분기는 산술로 검사했지만 실제 손상 차량의 동적 검증은 없고 기존 damage 안전 중단을 유지한다.

`adapter476.py`는 float32 명령을 복사해 활성 pedal만 바꾼다. 조향과 비활성 pedal을 보존하고 controller/reference/memory/hold 인터페이스에 접근하지 않는다. 별도 네 저장 사례에서 입력 불변과 등록 검색 결과 일치를 검사했다. 실시간 환경 wiring은 아직 없으며 이번 성공을 physics qualification으로 승격하지 않는다.

최초 독립 verifier의 −0 rank 기대값 오류로 한 번 중단했다. production solver는 이미 +0으로 정규화했으므로 검색 알고리즘 변경 없이 verifier만 수정했다. 원래 소스·계획·실패 로그를 보존하고 별도 등록 recovery 출력으로 진행했다. 독립 검토의 입력 dtype/wheel identity/none 검사는 실행 등록 전에 반영했다.

## 사전 고정한 대표 40개 결정

각 실행에서 첫3개, 25/50/75% 인덱스, 마지막2개를 분석 전에 고정했다. 26개는 full before 독립 입력, 14개는 telemetry 조건부 입력이다. 저장 상태마다 따로 계산했으며 결과를 다음 상태로 전파하지 않았다.

| 저장 실행 | 표본 | pedal 변화 / M 엄격 감소 | 최적화 후 M>0 |
|---|---:|---:|---:|
| 473 Original | 8 | 2 | 2 |
| 473 P4 | 8 | 1 | 2 |
| 472 native P4 | 8 | 1 | 0 |
| 442 native C0 | 8 | 0 | 0 |
| 442 native P | 8 | 0 | 0 |

40개 중 **4개 변화·4개 첫 raw M 감소**, 35개는 원래 M=0이어서 최대-q 동률 규칙으로 불변, 1개는 양의 M 동률로 불변이었다. 변화한 세 모델 표본도 clipping이 남았다. 이 세 가스 명령은 실제 부동소수점 plateau의 최대값 때문에 정확한0 대신 약1.8e−15∼4.2e−15가 선택됐다. 임의 epsilon으로0을 대신한 것이 아니다. native 변화 한 건은 기존 guardian 제동0.3 표본이므로 자연 P4의 성능 증거로 보지 않는다.

대표 표본에서 관측된 모델 변화는 늦은 구간이다. 초기에 경쟁을 줄여 발산을 예방한다는 동적 가설은 아직 검증되지 않았다. 미선택 결정의 빈도로 외삽하지 않는다. 최악 wheel M 감소는 다른 wheel 모두의 개선을 보장하지 않는다. 첫 raw가 같은 gas plateau도 나머지 hold에서 다르므로 **첫20ms 최적성을80ms 안전으로 확장하지 않는다**.

## 실측 CPU·IO와 다음 비교 계약

성공 분석 전체 CPU **4.918초**, wall **4.997초**에 source hash·535 before 읽기·fixture·40검색·독립 검증을 포함했다. 검색만 CPU 합계 **0.174초**, 최대 **0.020001초/결정**, wall 최대0.021330초였다. 독립 검증 CPU 합계0.0321초, 별도 adapter 네 사례 CPU0.244초였다. 최초 실패 process CPU와 준비/보고 CPU는 별도 완전 계측하지 않았으므로 합계를 완전 계측값으로 가장하지 않는다. 600CPU/900wall 상한보다 충분히 작았다.

압축하지 않은 compact 증명은 총45,224 B, 최대1,738 B였다. 실제 pretty JSON query 파일은72,099 B다. 성공 실행의 명시적 source/input 파일 읽기 길이 합계는1,230,535,642 B였다. 이는 import/system 파일 등을 제외한 논리적 읽기 회계이며 물리 디스크·cold-cache IO 측정이 아니다. 출력 상한16MiB, 증명당8KiB, /tmp와 workspace 각각512MiB reserve를 등록했다. 새 원본 복제·압축·기존 파일 삭제/이동은 없다.

단일 후속 계약은 `audit476_model_contract.json`이다. **실행 승인이나 실행 결과가 아니다.** 같은 pre23/P4에서 기존 법칙 대 할당 법칙을 각 최대250회 한 번 비교한다. source35 world/1,242 ticks, 세 root법칙 cohort9/324, candidate pending3/108을 포함해 최대 계획 **3,674 positive ticks /49 worlds**, 별도 zero-time constructor step 최대49회다. 미확인 호출 보존용 전역 charged cap4,096은 추가 행동/world 허가가 아니다. allocator는 root27+pending27+whole250=최대304회다. native/reset은0이다.

전체 hard CPU600초/wall900초, 할당·검증 집계120/180초, 호출당 input/search/검증/직렬화0.25CPU/0.5wall초, kernel100,000 wheel evaluations로 제한한다. 실측 최대에서304회 검색은 약6.08CPU초지만 미관측 상태의 최악 시간 보장은 아니다. source/일치/독립성/시간/IO/인증 오류는 즉시 기술 중단이며 재조정하지 않는다. 기존 경로3m·road/grass·collision·damage·reverse·진행·완주 조건을 유지한다. candidate safe own-finish가 후속 조건이며 censored baseline에 가상 완주 이득을 부여하지 않는다.

후속 model raw 예산536,491,719 B, allocator 입력/증명 추가16MiB, temp32MiB, reserve512MiB를 합한 **/tmp 필요1,123,694,279 B**다. 산정 당시 여유2,325,483,520 B로 충족했다. workspace 필요603,979,776 B, 여유859,734,016 B도 충족했다. 입력4KiB+증명8KiB×304는3,735,552 B로 추가 예산 안에 포함된다. 경험적 최대 byte/tick+25%와 최신 header/manifest 증가를 사용했고 raw 예산을 넘으면 삭제·축약하지 않고 중단한다. 실제 integration 코드·현재 공간·pending/source fixture를 한 번 등록한 뒤 고정 비교로 진행하는 계약이며 반복적 미세 게이트나 조정 탐색은 없다.

기존 raw·백업·공식 Participants·main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·보호18파일·원장은 보존한다. HOLDOUT/SEALED를 열지 않았다. 최신 명시적 연장 종료는 **2026-10-20 19:01:55 KST**, 근거 SHA `3b0dc9c16c5356e107e73dbd8a8f88e75a2434f9e24f046358783fbde8307078`를 계약에 연결했다. 자동 연장은 없다. /tmp 유실 시 해시만으로 raw를 복원할 수 없다.
