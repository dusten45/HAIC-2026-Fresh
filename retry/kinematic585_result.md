# 585 — 빠른 상태의 회복 불가능성은 미확인, 방향 준비 부족은 관측됨

**새 source·law·native·FD·optimizer 실행 없이 저장 증거만 분석했다.** parent25가 본질적으로 회복 불가능한 상태였다는 증거는 없다. 관측된 것은 581 정렬 중 경로에 필요한 방향 변화가 줄고, 584의 제한된 조향으로는 누적된 방향 지연을 corridor margin 소진 전에 보충하지 못했다는 사실이다. 버린 느린 sibling의 미래는 미관측이다. 다음은 더 이른 reachable prefix의 steering·pedal 공동 계획을 우선하는 **한 개의 비교 실험 제안**이며 이번에는 실행하지 않는다.

## 같은 raw124: fast parent25, 진짜 matched sibling, feasible factual

580의 raw124/hold31 종료 상태14개 중10개가 ranking에서 버려졌고, 그중8개는 parent25보다 느렸다. 서로 다른 직전 부모가 섞여 있으므로 모두를 동일 조건 sibling으로 취급하지 않았다. 가장 직접적인 비교는 edge274(parent25)와 edge275다. 두 상태는 직전 parent21과 그 이전 전체 경로, 이번 hold 조향·gas를 공유하고 **이번 hold의 brake만 다르다**. 같은 직전 부모에서 안전한 자식은3개였고275만 width-pruned였다. 아래 factual577은 같은 clock의 검증된 feasible 경로지만 초기 상태가 다르므로 matched causal arm은 아니다.

| raw124 지표 | 유지 fast274/parent25 | 버린 slow275 | factual577 |
|---|---:|---:|---:|
| progress(m) |121.2475|121.0858|120.5734|
| COM 속도(m/s) |53.6011|50.4483|49.5319|
| path 왼쪽 signed 위치(m) |+1.2134|+1.2170|+1.4491|
| path 왼쪽 횡속도(m/s) |−0.7910|−0.9151|−1.2170|
| body 전방 /velocity heading(rad) |0.6432 /0.6618|0.6376 /0.6585|0.6294 /0.6520|
| 경로 tangent 대비 velocity 방향 지연(rad) |0.01476|0.01814|0.02457|
| body yaw(rad/s) |2.1580|2.0458|2.0555|
| 두 앞 joint(rad) |0.13730|0.13730|0.14116|
| 전체 footprint margin(m) |4.3444|4.3360|4.0778|
| 누적 tracking [clip,samples] |[0,112]|[0,112]|[0,112]|

세계좌표 COM velocity는 fast(42.284,32.942), slow(39.901,30.869), factual(39.371,30.056)m/s다. 앞 wheel 전방 heading은 각각0.78055/0.77485/0.77053rad이고 뒤 wheel은 body 전방과 같다. fast의 두 앞 wheel 속도 방향과 wheel heading 차이는−0.04565/−0.05698rad, slow는−0.04279/−0.05425rad로 서로 다른 준비 상태지만 clipping 이력은 같다.

slow275는 progress0.16169m를 양보하고 속도3.15279m/s, yaw0.11225rad/s를 줄였다. 위치 차이는0.00361m, margin 차이는−0.00835m에 불과했다. 같은 경로 node 곡률에서 일정 속도 추종의 (v^2|\kappa|) proxy는 fast129.91, slow115.08, factual110.94m/s²다. **빠름이 요구하는 회전 부담은 커졌지만, fast의 위치·heading·margin이 이미 나빴던 것은 아니다.** slow의 이후 안전성·시간 이득은 기록되지 않았으므로 “느린 sibling이면 회복됐다”라고 결론 내릴 수 없다. progress 차이를 시간 이득으로 환산하지 않았다.

## 581의8raw 동안 줄어든 방향 변화

세계 전방 heading은 body angle+π/2, velocity heading은 atan2(vy,vx)로 구분했다. path 왼쪽 normal을 양수로 쓴다. path tangent는 고정 polyline의 해당 segment 방향이며, vertex에서 불연속이다. 아래 “필요 방향 변화”는 **그 경로 tangent를 따라간다는 기준의 변화량**이지 corridor 안의 모든 가능한 경로에 대한 하한은 아니다.

| raw124→132,0.16초 | factual577 | fast→581 alignment |
|---|---:|---:|
| 경로 tangent 변화(rad) |0.439585|0.439585|
| 실제 velocity 방향 변화(rad) |0.431018|0.209422|
| body 방향 변화=Σyaw·dt(rad) |0.407938|0.223155|
| velocity 방향 변화의 tangent 대비 부족(rad) |0.008567|0.230163|
| sideslip heading 변화(rad) |+0.023080|−0.013732|

581의 관측 velocity 회전은 factual보다0.221595rad(12.70°), body 회전은0.184783rad(10.59°) 적었다. 첫 상태·속도·위치가 다르므로 이 차이 전체를 alignment만의 인과효과로 부르지 않는다. 반면 581 내부에서 앞 joint가0.13730→0.08599→0.05772rad, yaw가2.158→1.448→1.003rad/s로 줄고 앞 wheel의 frozen lateral 성분 ratio가0.483/0.657→0.141/0.176으로 줄어든 것은 저장값으로 확인된다. **slip 완화와 함께 corner를 돌던 방향 변화도 약해졌다.** frozen lateral 성분은 저장 상태의 분해값이지 새 force/kernel 평가나 미래 안전 인증이 아니다.

raw132의 COM은 path에서 불과+0.14406m였으나 velocity heading0.87126rad 대 path1.11618rad로0.24492rad(14.03°) 늦었다. COM velocity(29.891,35.521)m/s를 path에 분해하면 전방45.039·왼쪽−11.257m/s다. 앞 wheel 전방0.92412rad, body 전방0.86640rad, yaw1.00336rad/s였다. 같은 raw의 factual은 velocity heading1.08304rad, yaw2.81192rad/s, path position+1.5032m·왼쪽속도−1.3921m/s였다. **중심선에 가까운 위치 하나가 미래 추종 준비를 뜻하지 않는다.**

## 583/584: force wall 이후 남은 공간과 회전

583의 가장 이른 거절6개는 같은 raw132 상태에서 시도 raw133의 제동 force 실패다. 원 nominal pedal과 맞춘 후보는 raw135 상태까지 적분한 뒤 **시도 raw136 전에** force peak1.365652로 거절됐다. 따라서 실패 raw136을 완료된 pose처럼 취급하지 않았다. 그 저장 raw135의 velocity/body/wheel-front heading은0.99969/0.96678/1.20451rad, path heading1.42336rad였다. 더 큰 joint0.23772rad로 회전을 재개하려 했지만 앞 wheel lateral 성분이 한도를 넘었다.

584는 같은 raw132에서 더 작은 joint target으로 force 안전을 유지했지만, 추가 방향 변화0.341712rad에 비해 경로 tangent 변화는0.602070rad였다. raw132→140의 body 회전은0.313095rad, sideslip 변화는+0.028617rad였다.

| 584 관측 | raw132 시작 | raw136(첫 hold 안전) | raw139(마지막 안전) | raw140(첫 실패) |
|---|---:|---:|---:|---:|
| path 왼쪽 위치(m) |+0.1441|−1.3405|−2.6170|−3.0746|
| path 왼쪽 속도(m/s) |−11.2569|−18.3959|−24.7686|−22.8788|
| velocity heading(rad) |0.8713|1.0210|1.1654|1.2130|
| path tangent heading(rad) |1.1162|1.4234|1.7183|1.7183|
| body yaw(rad/s) |1.0034|1.8470|2.3489|2.5039|
| 앞 wheel 전방 heading(rad) |0.9241|1.1354|1.3145|1.3646|
| footprint margin(m) |3.9335|2.1695|0.51765|0.05828|

COM velocity는 raw136(24.545,40.049), raw139(18.603,43.342), raw140(16.554,44.272)m/s였다. nearest boundary는 raw124의 앞 wheel 제한에서 raw132 이후 앞 hull/bumper 제한으로 바뀌었다. raw132에서 가장 가까운 road edge의 inward normal은(−0.9973,+0.0733), raw136~140에서는(−0.9721,−0.2345)이다. latter edge에 대한 COM closing 속도는 raw136의33.25→raw139의28.25→raw140의26.47m/s로 줄었으나 이미 차체의 공간 여유가 소진됐다. 현재 회전까지 포함한 critical hull point의 closing은 각각31.46/25.11/22.81m/s였다.

raw140의 **같은 실제 boundary segment를 고정해** factual과 비교해도 차이는 남는다. factual의 finite-body support line gap은 raw132/136/140에서6.713/5.261/4.804m, 584는4.875/2.169/0.058m였다. 이 segment를 무한 직선으로 연장한 값은 공통 좌표 진단이며 전체 곡선도로의 장벽으로 취급하지 않았다.

공통 world plane s132에서도 factual은 raw135→136, 새 경로는134→135에 건넜지만 velocity 방향 지연은 각각0.1083 대0.4410rad, crossing 후 margin은4.1583 대2.5886m였다. 더 이른 공간 도달이 회복·완주·시간 이득을 뜻하지 않는다. raw140 margin은 여전히 양수이므로 관측한 것은0.5m 계약 여유 및3m path 한도 실패이며 충돌·차체 penetration은 아니다.

## 정적 상한으로 회복 불가능성을 인증할 수 없는 이유

원 source 상태의 linear mass는 **7.30191997kg**이고 이 map의 friction 상한은 wheel당400N이다. clipped 적용 force의 합만 보는 source COM 가속 norm 상한은 (4\times400/7.30191997=219.12045)m/s²다. 모든 힘 방향을 원하는 normal로 쓸 수 있다고 보는 매우 낙관적 상한이다. 실제 steering·rolling·제동·yaw torque·미래 contact·clipping 이력·reference·body 한도와의 동시 달성을 보장하지 않으며 native 차량에 대한 인증도 아니다.

path node 곡률 proxy는 raw124 약0.04522, raw132 약0.06743, raw136 약0.08391rad/m이고 새 경로의 일정 속도 normal 가속 proxy는129.91→145.32→185.13m/s²였다. 이 proxy들은219.12보다 작다. **이 느슨한 상한만으로 parent25나 raw132 상태의 회복을 배제할 수 없다.** 반대로 실제로 그 가속을 달성할 수 있다는 증거도 아니다. polyline node 곡률을 순간적인 물리 yaw 요구나 가능한 모든 corridor 경로의 최소 곡률로 쓰지 않았다.

현재 critical point 속도와 nearest edge를 얼리는 일차 근사 ((margin-0.5)/closing)는 raw132 약0.133초, raw139 약0.000703초다. 관측된 실패는 raw132로부터0.16초 뒤였다. 이는 관측 law의 여유가 급격히 줄었다는 진단이며, 미래 회전·normal·차체 자세가 변하는 실제 이탈 시각/불가능성 증명은 아니다. point의 normal 정지거리 (v_n^2/(2a_{max})) 역시 평평한 고정 wall·점질량·완전한 가속 배분이라는 조건부 낙관식으로만 기록했다. 유한 차체의0.5m footprint 조건을 대체하지 않는다. sideslip이 변하므로 (v/yaw)를 COM 회전 반경으로 사용하지 않았고, servo3rad/s를 body yaw 상한으로 사용하지 않았다.

## 다음 제안 하나 — 같은 유한 공동 계획의 시작 시점 비교, 미실행

**더 이른 reachable prefix에서 steering과 pedal을 함께 계획하는 방향을 우선한다.** 이를 parent25 회복 문제와 구별하도록, 동일한 유한 joint-program 표현·parameter 수·후보 cap을 쓰는 한 개의 paired 실험을 제안한다.

- EARLY: parent25의 실제 조상 raw112(s106.363m)까지 원 초기 상태부터 재구성하고 raw113부터 공동 계획한다.
- LATE: 같은 prefix를 parent25 raw124(s121.247m)까지 재구성하고 raw125부터 공동 계획한다. 581 정렬을 끼우지 않아 alignment가 만든 상태를 parent25 자체와 혼동하지 않는다.
- 각 arm 최대16개의 **전체 steering/pedal 프로그램**을 미리 고정한다. 실제 basis·수치 범위와 모든 검사 비용은 향후 source 전에 별도 동결해야 한다. 이번585는 새 프로그램을 만들거나 실행하지 않았다. 자동 후보 증가·chooser 확장·fallback은 없다.
- 공통 공간·시간 경계는 기존579의 고정 **s200 plane**, 검증된577 factual의 crossing bracket raw192→193, crossing hold 완료 raw196이다. strict 안전·진행±10m/path corridor 안에서 first forward crossing과 그 hold 전체 안전을 검사한다. source episode3.86초/hold 끝3.92초의 기존 clock을 유지한다. 별도100/80ms 이득은 요구하지 않으며, 이 기한 밖 회복까지 불가능하다고 확대하지 않는다. partial 결과로 whole 승격하지 않는다.

모든 후보를 초기 상태부터 최대196raw 실행하고 각 arm의 새 안전 선택에만 독립 tape replay1회를 허용하면 최악 source는 (32\times196+2\times196=6,664)attempt/완료틱, 실제 외부·내부 force각26,656회, raw geometry6,664회다. 현재 상태 geometry32회를 더한6,696회까지 포함한다. 제안 hard cap은6,700attempt/완료틱·외부/내부26,800각·합53,600·geometry6,800·CPU240초/wall320초다. forecast/FD/optimizer/whole/native는0인 제안이며, 구현에 숨은 rollout이 추가되면 이 계산을 실행 전에 다시 고쳐야 한다. CPU/wall은 완료 보장이 아닌 중단 한도다.

EARLY만 성공하면 이 finite 표현과 incumbent 기한에서 **일찍 공동 준비하는 가치**를 지지한다. LATE가 성공하면 그 범위에서 parent25 회복 불가능성은 반박된다. 둘 다 성공하면 기존 짧은 표현/patch의 한계를 지지하고, 둘 다 실패하면 intrinsic 회복 부족과 표현 부족을 여전히 구분하지 못한다. 어느 경우도 실패 후 cap을 자동 확대하지 않는다. [제안 집계](kinematic585_proposal.json)는 미실행 상태다.

## 재현·보존

[분석](kinematic585_analysis.json), [추가 감사](kinematic585_audit.json), [source0 계약](kinematic585_contract.json)에 input·원 수식·코드 hash와 비교 조건을 남겼다. dynamics import 없이 표준 라이브러리·저장 geometry만 사용했다. 정적99개 상태의 finite-body 도로 margin을 재계산해 저장값과 최대1.42e−14m 오차로 일치시켰고, yaw 적분합은 저장 body 방향 변화와 일치했다. full per-raw 파생값은 비공개다.

첫 읽기 분석은 plane metadata key를 `normal`로 읽어 종료했다. 실패 파일·첫 계약을 보존하고 실제 key `forward_normal`로 고친 source0 복구 분석을 수행했다. 실패 CPU/wall, 보조 읽기와 보수 writer charge까지 합계 **CPU6.511초/wall6.515초**다. 새 source·force kernel·forecast·law·native·FD·optimizer·학습·whole·HOLDOUT·SEALED는 모두0이다. incumbent actual13.66/source13.20, 연구잔여22,758, reserve84,000/사용0은 유지했다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·이전 성공/실패·원문·백업을 보존했다. 원시 상태·명령·journal은 저장소 밖 비공개에 남긴다. 종료2026-10-20 10:01:55UTC를 연장하지 않았으며 제안은 실행하지 않고 반환한다.
