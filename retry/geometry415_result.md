# 415 — 고정 H2 patch의 형상·source 2×2 검사

**유일한 patch는 형상 및 source 자격을 통과했지만, 형상에 따른 시간 이득을 식별하지 못해 승격하지 않았다.** 네 arm의 독립 반복과 같은 원래 arc의 공통 exit를 검사했다. nominal과 full-gas-first 각각에서 old/new 도착 bracket이 같았고, 수치 시간 interaction은 −0.04~+0.04초로 0을 포함했다. 실제 주행 없이 이 patch를 닫는다. 414의 단일 pulse+O 진행 실패를 H1 전체 실패로, 이번 결과를 H2 전체 실패로 확대하지 않는다.

412에서 정한 30–50% 중 원래 인접 곡률 변화가 가장 큰 노드 하나를 선택했다(원래 arc 약 40.04%, 동률은 앞 노드). 주변 4선분의 두 끝 위치·중앙 secant 단위 접선과 원래 길이로 스케일한 미분값을 사용한 cubic Hermite 하나만 만들었다. 원래 정규화 arc 비율의 5개 노드 중 내부 3개만 바뀌었다. 끝 접선은 기저 cubic의 조건이며, 실제 controller가 사용하는 polyline의 연결부까지 별도로 검사했다. 다른 patch·계수 sweep·수리·새 속도 solver는 사용하지 않았다. 속도 노드는 원래 대응 노드에 고정하고 새 Euclidean ds에서 feed 기울기를 다시 계산했다.

| 정적 검사 | 결과 |
|---|---:|
| patch 길이, old → new | 12.371 → 12.293m |
| 연결부 포함 최대 인접 곡률 변화 | 0.10028 → 0.03224m⁻¹ |
| 새 최대 절대 곡률 / 조향 한계 | 0.07549 / 0.13049m⁻¹ |
| 외곽 rectangle의 도로 경계 최소 거리 | 1.256m |
| 장애물 최소 여유, 추가 0.25m 차감 후 | 28.888m |
| 원래 경로 거리의 sampling 보정 상한 | 0.275m < 3m |
| 유한 양의 ds·비인접 교차·도로 boundary topology | 통과 |

실제 저장 도로 fixture의 공유 edge를 제거해 경계를 구성했다. path translation은 최대 0.025m, 노드의 heading 회전은 최대 0.005rad 간격으로 검사했고, 이동에 의한 최대 오차 0.012501m를 여유에서 차감했다. 차량 외곽 rectangle은 횡 ±1.75m, 종 ±2.9m다. 첫 plan의 ‘조향한 바퀴 외곽에 0.35m 여유 포함’ 문구는 이 rectangle 자체의 여유를 과대 표현했다. source의 joint ±0.4rad에서 wheel 횡 외곽은 1.568m이므로 0.35m 여유에는 rectangle보다 0.168m 추가 확장이 필요하다. 저장한 경계 거리에서 이 확장과 이동 오차를 함께 차감해도 **1.075m 양의 도로 여유**가 남는 보수적 거리 인증을 별도로 기록했다. 새 형상이나 재탐색은 없었다. 이 정적 검사는 실제 타이어 접촉·추종 안전을 보증하지 않는다.

source는 같은 저장된 patch 진입 전 상태에서 시작했다. 첫 78행동 prefix를 원래 actual 명령으로 재생하고 body·wheel·raw hull fidelity를 매 행동 검사했다. 79번째 행동 직전이 entry다. 원래 nominal의 다음 13행동도 같은 계측 phase에서 실제 저장 기록과 대조했다. 위치 최대 차이 0.0000054m, 속도 0.0000103m/s, yaw 0.00000453rad/s, wheel omega 0.0000138rad/s, force ratio 0.00000301로 기존 허용오차를 통과했다. 이산 상태와 COM·질량 metadata도 일치했다.

old/new path × nominal/full-gas-first 네 arm을 동일 상태·memory에서 각각 두 번 독립 복원했다. full-gas-first는 첫 nominal 조향을 유지하고 gas1/brake0 한 번, 이후 자기 상태에서 같은 O 법칙을 사용하는 recipe다. 부모 상태·입력·memory·RNG 불변, 네 arm의 독립 반복, 이후 old nominal 재실행 및 연속 부모의 첫 전이 body/wheel/hull 대조가 모두 통과했다. 진행·3m guard는 새 경로 parameterization이 아닌 원래 reference arc로 계산했다. 공통 exit는 원래 patch 끝에서 10m 뒤이며 보간 시간은 사용하지 않았다.

| arm | 원래 공통 exit 도착 bracket | 13행동·안전·진행·exit |
|---|---:|---|
| old path / nominal | 0.58–0.60초 | 통과 |
| old path / full-gas-first | 0.46–0.48초 | 통과 |
| new path / nominal | 0.58–0.60초 | 통과 |
| new path / full-gas-first | 0.46–0.48초 | 통과 |

네 arm 모두 적격이므로 `(new gas−new nominal)−(old gas−old nominal)`의 시간 interaction을 −0.04~+0.04초로 해석할 수 있다. 음수는 새 경로에서 가속 이득이 더 크다는 부호다. 같은 pedal끼리 geometry 효과는 각각 −0.02~+0.02초로 분해능 안에서 미식별이다. new full-gas가 old nominal보다 0.10–0.14초 빠른 결과만으로 geometry의 추가 이득을 선언할 수 없다. old path에도 같은 pulse 이득 bracket이 있기 때문이다. 사전 0.08초 이득 기준을 geometry 효과로 충족하지 못했다. 실패 arm 시간 추정은 없었으며, 새 조향의 실제 반사실 fidelity·전체 랩·독립 일반화·픽셀 정책에 대한 주장은 없다.

full-gas 두 arm의 최대 force ratio는 old/new 1.141/1.138, clipped wheel 표본은 각각 18/208이었다. nominal 두 arm은 약 0.906, clip 0/208이었다. 네 arm 모두 grass 표본 0, 도로·손상·충돌·후진 위반 0이었다. 단순 미포화 가정으로 가속을 허용한 검사가 아니며, q>1도 독립 안전 거부 기준으로 쓰지 않았다. 자세·속도·타이어 상태는 arm별로 달라진다.

414 정지 상태의 부가 검사는 기존 O268/C268 식 대입만 했다. 초기 정적 결과는 generic C의 기본 1.5배 노드를 사용한 연결 오류가 있어 보존하되, `executor(fixed, frozen268)`의 실제 C268 노드로 정정한 결과가 이를 대체한다. 같은 segment·노드에서 r=64.023m/s, f=−206.014다. O의 `f+1.5(r-v)`는 −109.980으로 brake=0.3이고, C의 `f*(sigma/r)+1.5(r-v)`는 +96.035로 대수상 brake=0이다. 속도·진행 속도가 정확히 0인 기호 대입에서도 C의 음의 feed 항은 사라진다. 그러나 저장된 signed sigma는 −3.28×10⁻¹⁶m/s라 기존 C runtime의 음의 진행 정의역에 걸린다. 값을 반올림하거나 floor하지 않았으며 **실제 C 명령·재출발·안전·완주를 자격 부여하지 않았다.** 새 rollout이나 수정식 탐색은 없었다.

정적 분석 CPU 2.253초/wall 2.183초, source는 **784 tick·10 world**, CPU 1.515초/wall 1.528초로 각각의 30/60초 상한 이내였다. source 구성은 prefix 312tick, 8개 반복 arm 416tick, post-reference 52tick, 연속 부모 검사 4tick이다. 복원 world 10개의 zero-time contact setup도 별도로 셌다. 준비 wall은 최초 시작부터 source 실행 전까지의 timestamp 구간에서 정적 실행 시간을 뺀 142.653초다. 준비 CPU는 미계측이며, 뒤늦게 적은 source 준비 시작 marker의 180초 추정값은 비용 측정에서 폐기했다. 계측 payload의 저장된 합 CPU 0.0199초/wall 0.0461초는 전체 tracer dispatch overhead와 부모 마지막 한 전이 payload를 포함한 완전한 overhead 측정이 아니다. 보고·git 전체 비용도 별도 미계측이다.

원장 v435에서 **native/reset·학습·SEALED·예비·새 유료 자원 사용은 모두 0**, 연구 29,880행동과 예비 84,000행동(사용 0)을 유지했다. champion 296/rollback 240·보호 자료·408 원기록과 승인 기한을 유지했다. 개인 seed·지도·raw 상태·trace는 저장소 밖에 두었다. 추가 실험 없이 코드·집계 결과·비용을 기록하고 이 단계를 종료한다.

[기계 판독 결과와 비용](geometry415_result.json). 정적 plan SHA256 `f213067b20dfd3176e8a0a80afd87b0849cc669ba66fceb73492761e242a8b2c`, source plan SHA256 `567c46ddcafd2ecd484d0a92e73ba4a4012460beccf2ecd2ffad1f35f74ece5d`.
