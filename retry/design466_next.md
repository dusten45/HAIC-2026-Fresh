# 466 — H2A 저장 분석과 한 번의 다음 반증 설계

**새 physics/native 적분·world/reset·seed·학습·HOLDOUT·SEALED·예비·유료 자원 사용0이다. 압축 writer를 구현하거나 실행하지 않았고 기존 파일 삭제·이동·변환0이다.** 최신 종료는2026-10-20 19:01:55 KST다.465의 사전 승격 미통과와 낮은 감속 부채/횡력 노출 trade-off를 유지하며 전체 secant 불가능성으로 확대하지 않는다. 기존 최선13.760초,463의13.780초·0.220초 이득을 보존한다.

## 같은 위치의 요구와 원본 tyre 한계

동일 segment 위치u에서 squared speed는 `q=q0+u(q1−q0)`, 경로 곡률은 **가정상** `κ=κ0+u(κ1−κ0)`, 요구 접선 가속도는 `a=(q1−q0)/(2ds)`로 둔다. 이는 현재 discrete path curvature를 선형 연결한 점질량/rolling proxy이며 실제 polyline 꼭짓점·steering 추종 κ를 정확히 푼 것이 아니다. `qκ`가 이차식이므로 endpoints와 내부 정지점 모두 검사한다. 서로 다른 위치의 최대 종력과 최대 횡력을 합쳐 위반을 만들지 않는다.

세 비교를 분리한다.

- 총 병진 접촉력 proxy: `Fx=M*a`, `Fy=M*q*κ`, `hypot(Fx,Fy)/1600`.
- 후륜 구동/equal-axle proxy: `Fx_rear=(M+2I/r_w²)*a`, `Fy_rear=Fy/2`,800N 원형과 비교한다. 양의a에만 적용한다.
- 엔진/rolling 등가 proxy: `M_eff*a`와 `80000/(sqrt(q)+2.7)` 비교다. `M_eff`를 실제 접촉 종력 질량으로 쓰지 않는다. 가속 중 continuous engine ratio는 같은segment의 높은q 위치에서 최대다.

원본 Car는4개 바퀴마다 현재 road/grass·grip에 따른400N 기본 마찰 한계를 계산하고, wheel omega·gas ramp·brake·slip에서 얻은 종횡력 벡터를 공동 clipping한다. 균등 축 횡력·무슬립 rolling·전후 바퀴 배분은 근사다. 저장442/458/463에서 관측 friction_limit는400N/wheel이지만 미래 reference 추종 상태의 접촉·slip·force 배분을 인증하지 않는다. preclip ratio>1은 요청 clipping이지 실제 적용 힘의 한계 초과가 아니다. reference proxy 위반 개수와 관측 tyre clipping 개수는 다른 지표다.

## 고정4회 후보: 무엇을 바꾸었는가

frozen268을 곱한 현재 nodes를 상한으로 두고 **원래 racing258_plan의 backward B / forward A(v_left) 전달을 정확히4회** 적용했다. line·곡률·차량 model·원래 A/B·초기node0·자유 finish를 유지했고 재탐색·추가수렴 반복·새 gain/pace 학습은0이다. 이 후보는 종방향 원래 이산 근사의 재투영이며 공동 tyre 제약을 직접 투영한 후보가 아니다.

|진단|원래 scaled reference|고정4회 재투영|
|---|---:|---:|
|reference clock|10.027245초|12.260072초|
|squared-speed gradient/2 최솟값|−223.401575m/s²|−91.168734m/s²|
|최댓값|106.921373m/s²|35.018878m/s²|
|총 병진 원형 proxy 초과 segment|42|8|
|총 병진 원형 최대비|1.404426|1.052567|
|후륜/equal-axle proxy 초과 segment|168|34|
|후륜 proxy 최대비|2.442727|1.254905|
|continuous engine-equivalent 초과 segment|163|94|
|continuous engine 최대비|4.176570|1.035458|

239nodes 중222개가 낮아졌다. 기존 이산 forward/backward squared-speed 잔차는 최대약1012/994에서2.7e−12/2.4e−12로 줄어, 검증 roundoff1e−8 기준을 통과했다. 이것은 실제 물리 tolerance를 바꾼 값이 아니다. forward 전달이 왼쪽 속도만 쓰므로 통과해도segment 끝까지의 엔진 요구가 약3.55% 남을 수 있다. 총 접촉력/후륜 공동 proxy도 남았다. **재투영 결과를 실제 feasible reference라고 부르지 않는다.**

변경은 일부위치 pulse가 아니라 전역 reference 구조다. pre23+60–120m reference clock은0.539748→0.743424초,120–180m는0.417411→0.596526초,510–570m는0.577701→0.645338초,630–690m는0.554160→0.690749초다. 정확한공간 clock은각경계 적분으로 계산했고 gradient segment 수의 bin은segment midpoint 규약이다. 전체 bin/잔차는 [집계](structural466_result.json)와 비공개 node/segment 자료에 있다.

## 현재 상태 접합과 시간 목표

기존pre126에서 실제 속도81.032m/s, 원래target101.780m/s, 재투영target89.547m/s다. projected future nodes와 원래B로 계산한 backward 접합 ceiling91.152m/s보다 현재속도가 낮고, 남은 lower nodes의 최대 필요한감속/B proxy는0.152113이다. 이는 이산 근사에서 즉시 접합을 배제할 이유가 없다는 결과이며 실제 미래 tyre/경로/안전 자격은 아니다. 실제 속도를 강제로target으로 바꾸거나 root를 이동하지 않는다.

같은root의 gradient는−210.662→+29.917m/s²로 바뀐다. 같은 point-FF 식 `f*sigma/r+1.5(r−v)`의 raw는−136.559→+39.839m/s², 기존pedal clamp의 명령 가속도는−91.169→+35.019다. 따라서 목표속도를 낮췄어도 이 위치에서는 오히려 brake 대신 fullgas가 된다. 이는 reference의 급한 기울기 구조가 제어 신호를 지배할 수 있다는 판별 근거다. 새 궤적이 빨라진다는 계산은 아니다.

11초대 목표를 유지한다. reference clock이2.233초 늘고12.260초가 되는 사실은 이 보수 후보의 성능 기대에 불리하다. 완벽히그profile을따르기만하면11초대를 설명하지 못하므로 기본 champion/안전 목표로 채택하지 않는다. 반면 기존 reference는 actuating 근사와 불일치한 과도한 FF·제동을 만들 수 있어, 명령 효율 회복이 target 감소의 손해보다 큰지 작은 모델 반증으로 판단할 정보가 있다. 현재root 이후 reference clock도3.084→3.560초로 늘어 이 위험을 숨기지 않는다. clock은 실제 lap 하한도,11초대 불가능성 증명도 아니다.

저장 상태의 대안 명령 변화는442P57개/171개,458P51/174개,463PulseOnce55/172개다. 자기 낮아진 target 기준 under-target braking 감소만으로 성과를 만들지 않는다. **같은 원래 target보다 느린데 새 식이 제동하는 경우도33/36/33개 남는다.** 저장 위치/속도는 그대로라 추종기 개선·시간 이득을 평가한 자료가 아니다.

## 선택한 최소 반증 계약 — 공통 첫 fullgas 뒤 reference만 교체

현재고정root를유지한다. 양쪽첫전체float32명령을이미본같은fullgas로고정한뒤, 이후12행동은 **Original reference point-FF 대 Projected4 reference point-FF**다. secant·feedback·line·steering·pedal map·80ms hold는 바꾸지 않는다. 현재 projected 첫 natural 명령이 fullgas와exact 같고, 저장463PulseOnce의 첫명령뒤4·9·10번째 대안 명령이 달라 개입 유효성 gate를 통과했다. 원래nominal과projected를그대로대조하면 이미알려진첫pulse 이득을 새 H2A의 지속 이득으로 다시 셀 수 있어 이공통첫명령을택했다.

미래 adapter는 SourceC를같은fixed/pace/memory에서만들고, 행동 전에 policy.nodes를동결projected vector로명시적으로 주입한다. node0=0에서새pace비율을나누거나body상태·memory를reset하지 않는다. immutable nodes SHA·policy digest·source manifest를 각 arm 증거에 묶고, 매경계 C.act1회와prepared_before/prepared_nominal을 검사한다. source qualification은원래policy에서먼저통과하고, Original-Pulse H13의nativephysical calibration/첫current와bitwise명령동일prefix를분리한다. Projected의첫명령physical counterpart 이후에는model자기일관성이다. 기존3recipe/oldguardian certificate로위장하지 않는다.

두 arm은각 H13독립2회와held첫전이1회다. 같은네trajectory에서자격검사와반증을계산하고별도main·guardian·tail·root검색0이다. old source/current/pending/parent1242ticks/35worlds +두arm108/3씩 = **최대1458ticks/41worlds**. hard2048/64·wholeCPU180초/wall300초·순차1,actual/reset0이다. 이 문서와 [계약JSON](design466_next.json)은 실행 승인을 부여하지 않는다.

원래reference의공통root+60m clock을양쪽에같게적용하며, 주지표는그경계의raw20ms통과bracket차이다. 동일1.04초종료진행을같이본다. **strict양의시간bracket+양의종료진행+모든source/반복/정의역/안전gate**를다음전체model설계의조건으로둔다. 자기낮은target에대한tracking오차감소·clip감소만으로승격하지않는다. 음수/overlap/미도달이면그대로보존한다. unknownearlyprogress·fidelity/RNG/권위/numeric/IO/resource는전역중단,typedphysical거절은기존뜻대로다. joint proxy 잔존을통과한실제안전증명으로부르지않고native이전0이다.

최신465관측91890.089431B/tick과world고정상한770314B,hard2048·25%·41world·metadata16MiB·plan2MiB·512MiBreserve로미래모델몫약822.6MB,workspacefullraw보존몫약886.8MB다. 현재workspace약904MB라여유가좁고미래source증가분은아직모른다. 실제시작직전두볼륨free·새manifest·전체보존비를다시검사해야하며안들어가면적분0으로닫는다. 저장제약을가설실패로판정하지않는다.

## 기록 방식 조사와 현재 종료

[미래gzip기록의호환성·검증비용](compression466_review.md)을별도로정리했다. 파일최초출력부터gzip으로쓰되기존모든field·JSONcodec·현재readback/barrier의순서를유지하는명시적adapter가가능하다. 현재reader에그대로꽂을수있는형식은아니다. 구현·압축benchmark·기존file변환은0이며, 새IO의무적분검증계약을먼저통과해야한다. 압축으로전체guarded최악계획의workspace복사까지이미해결됐다고주장하지않는다.

현재순수수치4검사와저장분석은constructor/step/native금지상태로통과했다. 첫결과저장은NumPy정수JSON직렬화오류로중단됐고실패folder·gate를그대로남겼다. 타입정규화만고쳐별도recovery경로에서수치분석을완료했다. physics/압축구현재시도는없다. 원본·보호18파일·v475연구26346/예비84000사용0·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants를유지하며자동후속실행0이다.
