# 413 — H1 첫 pedal primitive의 실제 국소 대조

**같은 개발 상태에서 full-gas-first가 원래 기준선보다 공통 exit에0.08–0.12초 먼저 도달했다.** 두 arm 모두 안전·몸체/바퀴 fidelity·진행 조건을 통과해 사전0.08초 bracket 기준에 따라 **다음 GT 단계로만 승격할 근거**를 얻었다. 전체 lap 개선·H1 전체·독립 일반화·픽셀296의 검증은 아니다. 다른 창/pedal/horizon이나 재주행·튜닝은 없었다. [집계·비용](headroom413_result.json) · [동결 실행/계측 코드](headroom413_run.py)

## 사전 규칙과 동일한 진입 조건

412의 규칙 그대로, 알려진 O 개발 기록에서 '현재 pre arc가 공통60–70% 안, nominal brake>0, requested target−speed≥5'인 첫 snapshot을 골랐다. 결과 label은117번째 행동 직전이었다. 미래 tire 표본을 선택 조건으로 쓰지 않았다. 두 recipe는 A:원래 O268 feedback, B:첫 행동만 **원래 조향·gas1·brake0** 후 같은 O268 feedback이다. 첫 조향 request는 둘 다−0.02529711이었다. 이후 같은 법칙이 자기 예측/실제 상태에서 새 조향과 pedal을 계산하며, 저장 미래 명령을 강제하지 않았다. 예측 memory를 실제 memory로 커밋하지 않았다.

source 상한4096tick·64world·CPU30초·wall60초와 실제394wrapper·reset2·CPU60초·wall120초·동시1개를 등록했다. 계획 SHA256은 `2d7ed66cd2a999ecfc1323a49481a4034d51080dd20b2d6b2288d658f54bd9bb`이다. goal3.24m·13행동 deadline, 같은 원래 기준 arc의 **30m 뒤 exit**, horizon13과 기존3m/도로·grass/손상/충돌/후진/domain 조건을 유지했다. 새 raw hull 관측에서도 같은3m bound를 확인했다. source의 두 recipe가 모두 안전·진행 적격이고 같은 exit에 도달하며 자격 게이트를 통과한 뒤에만 실제 reset을 허용했다.

## source 자격과 계측 phase

원래 실제 명령116개를 source에서 재생해 각 경계391 기준과 raw wheel 기준을 확인했다. 새 world의 body/tile/progress/finish 복원을 확인하고, A1 실제 nominal13 재생·A2 독립 반복·B1/B2 독립 반복·B 뒤 A3 참조 반복을 수행했다. 각 분기의 입력 snapshot·controller memory·전역 RNG와 살아 있는 source 부모 snapshot은 변하지 않았다. 마지막에는 source 부모 nominal 한 행동도 fresh A1/저장 실제와 대조했다. 첫 자격 실패에서 뒤 단계 중단하도록 동결했으며 이번에는 모두 통과했다.

관측 위치는 기존과 같은 **Car.step의 `if abs(force)>2*friction_limit` 직전**이다. engine/brake에 따른 omega 갱신 뒤·force vector clip/world.Step 전의 동일 phase에서 joint·omega·lateral/longitudinal slip·force/limit ratio를 비교했다. wheel0에서 raw hull origin/world COM/local COM, COM velocity와 origin점 velocity, angle/yaw·mass/inertia·pre-world clock도 읽기 전용으로 기록했다.

몸체391(위치0.1m·속도0.5m/s·yaw0.05rad/s·이산 상태)과412에서 제안한 wheel 오차(joint0.01rad·omega1rad/s·lateral/long slip0.5m/s·force ratio0.05)를 그대로 썼다. grass/접촉/손상·충돌/종료·시각, COM local/mass/inertia metadata도 대조했다. qclip 자체를 안전 classifier로 바꾸지 않았다.

## 실제 두 arm, 각각 한 번

두 fresh reset의 초기 full 이용 가능 상태·RNG·픽셀이 원래404와 같았고, 각116행동 prefix의 센서·명령·memory·결과가 같았다.117 직전 두 실제 arm의 full 물리/관측/RNG/controller 계산 전후 상태도 정확히 같았다. A의129행동은 저장 O와 명령·post 상태를 재현했다. B는 첫 pedal만 바꾸고 이후13행동 끝까지 같은 nominal 법칙을 자기 실제 상태로 계산했다. **각 arm129wrapper(116+13)**에서 끝내고 exit 뒤에도13행동 검증까지 관측했으며 추가 연장은 없었다.

| 실제 관측 | A nominal | B full-gas-first |
|---|---:|---:|
|첫 행동 후 속도 |35.932m/s |44.768m/s |
|30m 공통 exit 도착 bracket |0.66–0.68초 |0.56–0.58초 |
|처음3.24m 목표 도달, 행동 offset |2 |1 |
|13행동 후 원래 arc 진행 |52.455m |61.574m |
|13행동 post 경계 최대 경로 오차 |0.721m |0.698m |
|손상 / 실제 안전 위반 |0 /0 |0 /0 |
|13행동 rear 최대 force/limit |0.897 |0.957 |
|13행동 rear clip 표본 |0 |0 |

시간 이득은 **[A earliest−B latest, A latest−B earliest]=[0.08,0.12]초**다.20ms raw hull 표본으로 crossing bracket을 잡았고 중간 시각을 보간하지 않았다. source의 두 bracket도 실제와 같았다. 부동소수점 하단0.0799999999999983은 동결 코드의1e−8초 시각 허용오차 안에서0.08초로 판정했다. 이는 한 deterministic pair의 시간 해상도 구간이며 통계적 신뢰구간이 아니다.

공통 exit는 같은 원래 reference progress threshold이지 같은 종료 pose/속도라는 뜻은 아니다. crossing 양끝의 COM 속도는 A약54–55m/s, B약60–61m/s였고 경로 오차는 A0.08–0.11m, B0.32–0.36m였다. B의 yaw도 그곳에서 더 컸다. 둘 다 기준 안이지만 후속 감속·조향 상태가 다르므로 이번0.08–0.12초를14.78초에서 바로 빼 전체 lap 이득으로 만들지 않는다.

## 첫 바뀐 전이와13행동 fidelity

두 실제 arm의 prefix 및13행동 전부가 몸체·wheel·raw hull 기준을 통과했다. 특히 B의 바뀐 첫 전이는 body 위치3.81e−6m·속도3.91e−6m/s·yaw1.49e−8rad/s, raw wheel force ratio8.03e−7 이하의 오차였다.

|13행동 최대 오차 | A | B |
|---|---:|---:|
|post body 위치 m |4.77e−6 |1.55e−5 |
|post 속도 m/s |1.62e−5 |1.55e−5 |
|post yaw rad/s |8.37e−6 |1.36e−5 |
|raw joint rad |4.77e−7 |9.54e−7 |
|raw omega rad/s |1.91e−5 |2.15e−5 |
|raw lateral slip m/s |3.25e−5 |4.60e−5 |
|raw longitudinal slip m/s |2.16e−5 |3.27e−5 |
|raw force/limit ratio |4.33e−6 |7.08e−6 |

raw hull origin/COM 위치·두 점의 속도·yaw·시각과 COM/mass metadata도 통과했다. local COM은 origin에서약0.08253m 떨어져 있었고, 두 점의 속도 벡터 차이는 이 suffix에서 최대 A0.134·B0.153m/s였다. 따라서 position과velocity의 기준점을 분명히 기록했다. 이전412의 경계 장부를 새 전체 raw 경로 계측으로 덮어쓰지는 않았다.

## 지연·계측 비용과 원장

| source 분기 | CPU / wall ms |
|---|---:|
|A1 nominal |118 /121 |
|A2 nominal 반복 |127 /126 |
|B1 full-gas-first |130 /131 |
|B2 반복 |107 /106 |
|A3 사후 nominal 참조 |116 /121 |

단일13행동 forecast의 실측이며 native 실행 지연이나 실시간 정책의p95로 바꾸지 않는다. native에서 매 행동 source 최적화를 새로 실행한 것은 아니며, 동결된 primitive/nominal feedback을 실행하면서 기존 source 예측과 대조했다.

source는 **728tick·6world**, CPU2.203초·wall1.496초였다. 실제는 **258wrapper·reset2**, raw step1032tick·reset102tick, CPU16.808초·wall16.844초였다. 실제 arm별 CPU는 별도 계측하지 않았다. 전체 worker CPU19.011초이며 미확인 wrapper/model 예약은0이다. source3368tick·실제136wrapper를 쓰지 않았다.

기록된 callback payload CPU0.091초·wall0.150초는 따로 남겼다. 전체 tracer dispatch overhead는 분리 계측하지 않았고, 별도 uninstrumented 비교 주행도 하지 않았다. source parent 한 행동의4tick은 fidelity 요약을 보존했으나 raw 전체/해당 callback payload는 별도 보존하지 않았다. 나머지 source raw hull724개, 실제 raw hull1032개와 wheel4128개는 비공개로 기록했다. 이는 계측비용과 재현 기록의 범위이며 전체 overhead를 payload 비용으로 대체하지 않는다.

사전 구현 wall143.854초는 추론/도구 지연을 포함한 별도 구간이고 구현 CPU는 완전 계측하지 않았다. 읽기 전용 사후 감사 CPU0.157초·wall0.158초는 별도다. 문서/git 전체 시간은 계측하지 않았다.

원장v433에 실제258회를 한 번 차감했다. 누적 실제 wrapper **1,317,988**, 연구 잔여 **30,076**, 최종 예비 **84,000·사용0**이다. actor·학습·SEALED·유료 자원·예비 사용은0이다.296·240 롤백·공식 main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·보호 자료·SEALED16·원래408 실패·승인 종료2026-10-20 19:01:55 KST를 유지했다. 상세 raw 상태·seed·지도/profile·명령열은 git 밖에 둔다.

**해석은 한 상태의 timing headroom을 지지하는 국소 양성 결과까지다.** 몸체뿐 아니라 새 pedal의 실제 바퀴 반응도 맞았고 공통 exit 이득이 사전 기준을 통과했다. 다음 GT 검증으로 승격할 수 있으나, 더 긴 진행에서 이득이 남는지·상태 기반 연속 선택/속도 planner가 잘 되는지·독립 상태·픽셀296은 미검증이다. H1 전체를 검증/반증했다고 하거나 H2를 자동 실행하지 않았다.
