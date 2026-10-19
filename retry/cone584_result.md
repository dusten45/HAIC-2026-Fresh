# 584 — force cone로 제한한 경로 조향: force wall을 피한 뒤 경로 안전 실패

**결과는 `ACTUAL_SAFETY_FAILURE`: hold35 raw4/global140에서 첫 `FOOTPRINT` 실패와 동시 `PATH` 위반으로 중단했다.** 초기 상태에서581의132raw를 새로 재구성했고 전체 row·최종 root·visited·tracker·launch/tracking 이력·clock이 정확히 일치했다. 그 상태 하나에 동결한 새 법칙 하나만 적용했다. 추가8raw를 적분했으며 엄격히 안전한 구간은 첫7raw다. 48raw 성공 조건을 통과하지 못했으므로 독립 replay는0회다. 다른 law·gain·parent·baseline 재실행은 없고 후속 whole/native도 시작하지 않는다.

## source 전에 확인한 메커니즘

[저장583 분석](cone584_forensic.json)은64개 pre-force 입력과43개 완료 적분을 읽어 원 engine→brake→force 및 servo→yaw 수식을 대조했다. 새 force/kernel/model 호출은0이다. force/vector 최대 절대 오차는1.14e−13, yaw·joint 갱신 오차는0이었다.

- **현재 방향과 첫 force:** 새 `steer`는 현재 joint/wheel heading을 즉시 바꾸지 않는다. 첫 pre-force는 현재 접지 이력·wheel 속도·omega와 pedal로 정해진다. 강한 제동 후보6개는 raw1에서 실패했다. 그중4개는 rear wheel2의 큰 종방향 제동 성분,2개는 lock으로 생긴 front wheel1의 큰 종방향 성분이 peak였다.
- **servo와 지연된 force wall:** 원PP 목표 joint0.363064rad는 현재0.057724rad에서 motor3rad/s를 지속시켜 joint를0.117724→0.177724→0.237724rad로 증가시켰다. 나머지15개 후보는 raw3의2개와 raw4의13개가 front wheel1에서 실패했다. raw4 실패들은 lateral 성분만으로도 ratio1.1397~1.3653이었다. pedal만 바꿔도 이 조향 전이를 제거하지 못했다.
- **접지와 yaw 반작용:** 이64평가에는 접촉 membership4종이 있지만 저장 friction은 전부400N이었다. 이 사례의 force wall을 grass 진입으로 설명할 근거는 없다. 직접 servo 관성 항은 약−0.002335rad/s인 반면 타이어 torque의 yaw 증분은−0.06536~+0.76079rad/s였다. 힘→yaw→wheel velocity offset의 변화가 크며 COM 속도 방향만 맞추는581 alignment와 경로 목표를 그대로 적용하는583PP 양쪽에 한계가 있다.

## 동결한 단일 법칙과 검증 범위

[실행 전 계약](cone584_contract.json)에 수식·부호·동률·퇴화·단계/총 예산·성공과 실패를 고정했다. source 없는 검사10개가 통과했고 독립 읽기 검토도 통과했다. 첫 단위검사 실행에서 발견한3개 기대치 오류와 그 비용을 보존했다. 과학 실행은 한 번이다.

매 hold 시작 실제 상태에서 원537 `nominal`의 경로 조향·pedal을 순수 수식으로 한 번 계산한다. pedal은 float32 byte 그대로 유지한다. `choose`, `backup`, forecast는 호출하지 않는다. 각 앞바퀴에 대해 (v_i=v_{COM}+offset_i), (V_i=\|v_i\|), φ_i=atan2(−v_ix,v_iy), (u_i=0.54,\omega_{braked,i}), body angle θ로 두고 다음 정적 joint 집합을 만든다.

\[
Q_i=\{q\in[-0.4,0.4]:82^2[u_i^2+V_i^2-2u_iV_i\cos(\theta+q-\phi_i)]\le f_i^2\}.
\]

(f_i)는 **현재 저장 friction**이며 engine·gas memory·brake 순서를 반영한다. 이는 ratio≤1.0의 물리적 비포화 target 선택 제약이고, 실제 실행의 원1.059·누적 clipping 안전 계약은 유지한다. 음의 rolling은 cone 중심을π 이동하고, zero rolling/velocity는 heading 독립 all-or-empty로 처리한다. 각도 wrap 구간 합집합을 모두 취한다.

(Q_0\cap Q_1) 안에서 원 경로 joint 목표에 가장 가까운 float32 target을 고른다. 동률은 작은|q|, 이어 작은q다. 끝점은 안쪽으로 반올림하고 원 full-force 식을 재확인하며, 최대8ULP의 고정된 수치 보정 외에 탐색하지 않는다. 빈 집합·표현 불가·비정상 수치는 정해진 중단이며 다른 행동으로 교체하지 않는다. action steer=−q를4raw 유지한다.

정상 steering multiplier1에서 servo는 (q_i^+=q_i+clip(q-q_i,\pm0.06))라 overshoot 없이 target으로 움직인다. **현재 joint와 target이 같은 허용 연결 구간에 있을 때, wheel 상태를 고정한다면** 그 선분은 cone 안에 남는다. 실제 body angle·yaw·offset·omega·friction 변화의4raw 안전을 보증하는 식은 아니다. 이 불확실성을 실제 strict source에서 검사했다. 초기 경로 목표0.363064rad는 현재 공통 cone[−0.061542,0.140949]rad에 투영돼0.140949056rad로 제한됐다.

## 실제 반증 결과

hold34는4raw 모두 안전했다. 저장583의 **같은 부모·동일 pedal 후보**와 비교하면 첫 두 raw의 물리 입력과 전체 force가 정확히 일치한다. 이후 새 target이 joint/servo 전이를 바꿔 원 후보의 raw4 peak1.365652 대신 이번 첫 hold의 최대 peak는0.766161이었다. 새 baseline을 실행한 비교가 아니다.

| 추가 첫7raw의 엄격 안전 구간 | 관측 |
|---|---:|
| progress |129.479644→134.871647m (+5.392003m)|
| COM 속도 |46.424205→47.165583m/s|
| yaw |1.003365→2.348851rad/s|
| 두 앞 joint |0.057724→0.185123rad|
| wheel force ratio 최대 |0.998542|
| clip /tracking 이력 |0 /[0,144]→[0,172]|
| footprint margin 최소 |0.517647m|
| path error 최대 |2.617014m|
| reference 초과 최대 /body 속도 최대 |−2.865751 /50.355449m/s|

8번째 raw/global140에서 footprint margin0.058283m<0.5m, path error3.074590m>3m가 함께 발생했다. 원 순서상 primary failure는 `FOOTPRINT`다. 당시 네 wheel ratio는[0.527774,0.789506,0.472080,0.434488], 적용 force norm은[211.109,315.802,188.832,173.795]N이고 clip은0이었다. speed47.265249m/s, yaw2.503931rad/s, 두 앞 joint0.185123rad, 누적 tracking[0,176]이다. 실패 raw를 안전한 진행량에 포함하지 않았다.

**현재 tyre force에 맞는 target만으로는 상속된 COM 이동·yaw 속에서 도로 corridor 유지가 보장되지 않는다.** 이번 법칙은583의 즉시 force wall을 피했지만48raw local viability·경로 유지 가설은 반증됐다. 모든 제어의 불가능성, 완주, 시간 이득을 주장하지 않는다. 581의 기존8raw 결과와 source13.20/actual13.66초 incumbent는 그대로 보존했다.

## 비용·감사·보존

실행 전에 최악 source132+48+180=360attempt/완료틱·geometry360회, 실제 외부/내부 force각1,440회를 산출했다. 순수 force·cone 계산은 최대168회/선택×12와 사전370회를 별도 계수하고 **외부 force 예산에도 합산**해 최악3,826≤4,000회, 내부1,440≤4,000회, 합계5,266≤8,000회로 예약했다. replay·audit CPU/wall 여유도 매 law 이전과 intervention 내부에서 보존했다.

| 실제 사용 | 값 |
|---|---:|
| prefix /intervention attempt·완료틱 |132 /8 (합계140)|
| forecast /새 baseline /replay |모두0|
| 실제 외부 /내부 wheel 호출 |560 /560|
| geometry |140|
| 순수 force·cone 계산 사전 /런타임 |370 /16|
| 순수 계산 포함 외부 /force 합계 |946 /1,506|
| 준비·검사·실행·감사·보수 writer charge 총 CPU /wall |9.510 /7.446초|

모든 단계·총 예산 이내다. [결과](cone584_result.json), [비용](cone584_cost.json), [사후 읽기 감사](cone584_analysis.json)는984event hash-chain, 전체 prefix identity, 모든 입력·dependency·구현 hash와 비용 계수의 일치를 확인한다. raw state·command·journal은 저장소 밖 비공개로 보존했다.

main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·기존 백업·이전 실패를 보존했다. 연구잔여22,758·reserve84,000/사용0은 유지한다. FD·optimizer·학습·새 world·native·whole·HOLDOUT·SEALED·별도 유료 자원은 모두0이다. 지정 클라우드에서만 진행했으며 종료2026-10-20 10:01:55UTC를 연장하지 않았다. 이번 단일 반증을 정리해 종료한다.
