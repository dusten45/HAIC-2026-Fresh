# 535 — footprint 예측으로 모델 실패 회피; 실제 짝은 제한된 pedal 구간에서 안전 정지

**고정533 경로/조향 법칙에12hold 전체 hull/wheel margin≥0.50을 추가해534의 국소 실패를 회피했고, cold/carry 모델 finish15.10/15.52초를 얻었다. 그러나 실제 후보는32actions 뒤 다음 명령을 인증하지 못해 안전 정지·미완주했다.** fresh baseline525는공식18.40초를재현했다. 실제개선은확인하지못했으며18.40초기록을유지한다.262actions/2resets를차감해연구 **23893**,예비 **84000/used0**다.두world 모두정리했고재시험하지않았다.

[최초 계약](footprint535_contract.json) · [고정controller](footprint535_control.py) · [국소 감사](footprint535_local_audit.json) · [비용 중단 보존](footprint535_cost_stop.json) · [유한 기술복구 계약](footprint535_recovery_contract.json) · [완료 모델 gate](footprint535_recovery_result.json) · [native등록](footprint535_native_registration.json) · [실제 짝 결과](footprint535_native_result.json) · [정지 root 진단](footprint535_stop_diagnostic.json) · [선택구간 분류](footprint535_stop_analysis.json) · [최종 비용/보존 감사](footprint535_final_audit.json).

## 단 하나의 제어 가설과 고정 조건

경로는533/534 frozen-paths SHA `98b3eaf4eb335d95a588de33921d54c36ef4e1c2266d648980e6b52c114114d3` 그대로다. 추가경로최적화·다른iterate·조향gain변경0이다.533의최적성미수렴과534cold실패를보존하고최적성주장을하지않는다.

기존528 source-response의 `[BACKUP,HIGH]` signed-pedal구간·9점coarse+0/float32brakelock·조건부16회bisection·firsthold진행량선택을유지했다. 변경은현재root와12hold각raw에서기존 `corner515.margin`의전체 hull/wheel 도로·원형장애물 margin≥0.50을요구하는것과그로인한pedal선택뿐이다. 미래11hold는기존100-reference backup feedback이며actual미래trace가아니다. HIGH를포함한최종명령은cache가아닌fresh rollout으로다시인증했다.

모델0.50/native0.25m는기존기준그대로며추가여유0으로사전고정했다. 기존525실측max한-hold위치오차4.73e-5m/heading3.50e-5rad를참고했지만12hold오차상한이나robust invariance를증명했다고말하지않는다. force0.19불확실성/예측1.06/물리1.25,참조초과5(내부4.85),tracking clipping10%,path3m,launch24gas.32/peak2.5/clip15%,기존sourceTimeLimit/finish/관측·손상/one-hold prediction/force oracle/COM impulse 기준은유지했다.

## 늦은 root와 충분히 앞선 root를 구분한 작은 반증

534의action165·164·153·141 **직전** root를사전지정했다.141과165직전root간거리는24hold=1.92초이며,실제534위반165raw4까지는2.00초다. 각root에서기존528선택과535선택을같은상태/실행clip history로비교하고,535선택이없을때만진단용전체signed범위11점(9균등+brakelock양측)을검사했다. 이는deployed구간확장이아니다.

|저장 root 직전|초기margin|기존선택의기하위반예측|535의12hold명령|진단11점의첫hold/12hold안전개수|
|---|---:|---|---|---:|
|165|0.670754m|4raw 뒤0.437175m|없음|0 / 0|
|164|1.214909m|8raw 뒤0.436180m|없음|6 / 0|
|153|1.228651m|위반없음|HIGH, fresh인증|미실행|
|141|4.970981m|위반없음|HIGH, fresh인증|미실행|

늦은root의유한후보/고정futuretail실패를모든pedal정책의불가능성으로해석하지않았다.141부터535를36hold/144raw실행해원위반지점과그이후를안전통과했다. 최소margin0.500000002m,force peak1.050048,path1.350386m,참조초과0,36개명령모두fresh최종인증이었다.

534와처음달라진명령은action158의pedal이다. 그때조향값은bit-identical이고,그앞68raw의root state도모두같았다. HIGH는33forecast raw 뒤예측margin0.470846m때문에기각됐고선택FINAL은0.500000093m였다. 이후조향값은달라진자기상태를같은feedback법칙에넣기때문에달라질수있으며gain변경은없다. 회복창+두회귀창84개명령전부원래steering법칙·fresh최종인증과일치했다.

두기존위험root의새535회귀도각24hold/96raw안전완료했다. 최소여유는장애물창1.086840m/곡률창0.839017m였다. 완료한534비교창은SHA cache로재사용했다.

## Cold/carry 모델과 비용 상한 복구

|모델gate|535|비교 및판정|
|---|---:|---|
|cold source-style finish|15.10s|52518.40대비3.30s,52818.00대비2.90s|
|carry source-style finish|15.52s|525carry18.64대비3.12s,새528carry18.24대비2.72s|
|cold/carry 최소여유|0.500000002 / 0.501018730m|모델0.50통과|
|cold/carry running force peak|1.059686 / 1.047940|1.06통과|
|cold/carry HIGH비율|89.70% / 89.86%|50%통과|

모두source-style finish·전force/추종/기하/launch/body-domain및사전0.50초(525)/0.10초(528)효과gate를통과했다. **이시간은모델값이며실제기록이아니다.** carry는등록된actual518before47 root/clip0/352였고,535의cold와현재동일fixedpath·controller를사용했다.

전체footprint계산비용때문에최초전처리실행은완료한국소/회귀/cold/528carry를저장한뒤후보carry도중원600CPU상한에서종료됐다. 원예외/입력/단일MODEL_STARTED를보존했다. 미완료carry의최종tick/force카운터를저장하지못한한계도숨기지않았다.

완료한결과는재계산하지않고,같은경로·controller·초기root로 **미완료후보carry만** 수행하는별도유한기술복구계약을계산전에등록했다. 추가600CPU/720wall/120000ticks/600000explicit force 한도를두고,에러시정확한counter저장·진행비용checkpoint를추가했다. 새정책/parameter sweep가아니며535의native한짝1000actions/2resets상한을늘리지않았다. 후보carry는새23334ticks/244.08CPU초에완료했다.

## 허용된 실제 한 짝: 후보는안전정지, 승격없음

|동일DEV fresh actual|525 baseline|535 후보|
|---|---:|---:|
|결과|OFFICIAL_FINISH|NO_ADMISSIBLE_ACTION|
|공식lap|18.40s|없음|
|실행wrapper actions|230|32|
|최소실제margin|0.988258m|3.828414m|
|running실제force peak|1.057017|0.780091|
|최대한-hold예측위치오차|4.73e-5m|2.21e-5m|

후보는실행된32actions의모든guard를통과했지만action33을출력하지않았다. sourcefinish·실제gain은null이다. sourceinitial identity는양쪽모두일치했고,baseline의finish/margin/path/force/mode집계는기존525actual과정확히같았다. 경로가다른두arm의launch action/obs prefix가같아야한다는잘못된조건은두지않고각prefix를별도보존했다.

모든262attempt를 `env.step` 전에차감했다.2resets·1150actualraw(시도=완료)·2world를사용했고,양쪽finally `env.close` 뒤body/joint0 assertion을통과해closed2를확인했다. source-force oracle/COM impulse/센서phase/payload/관측·손상및모든실제action flag는정상이었다. 실제안전위반이나충돌때문에중단한것이아니며,재시험하지않았다.

native사전검토에서forecast geometry context가track-hash지역변수로가려질수있는이름충돌을발견했다. 등록초안은보존하고active entry의변수명과cost사전reserve만수정해첫world전에SHA로별도등록했다. controller/경로/threshold변경이나추가native시도는없다.

## 정지 root의 작은 사전등록 진단: footprint가직접원인이아님

추가world/reset/action0의별도계약으로저장된actual/model의action32·33직전root4개만같은535선택기로비교했다. actual33에서만기존force-only선택기와같은11점진단grid도검사했다. 실제미래trace입력·후속명령실행·native재시도는없다.

- actual/model root32는모두RESPONSE를fresh인증했다. root33에서는actual의등록된9개구간후보가모두 `FORCE_PEAK`로실패했고,**footprint를제거한기존528force-only선택기도없음**이었다. 당시여유는충분했으며footprint기준완화로해결할문제로보지않는다.
- actual33시험의최소예측peak1.060003722는1.06을넘었다. 대응model33의시험최소1.059999382는통과했다. root33의위치차이2.56e-5m/velocity-vector차이5.30e-5m/s처럼작은상태차이에도선택가능성이바뀌었다.1.06이나0.19여유를사후완화하지않았다.
- **전체signed 진단grid에서는2개가12hold전조건을통과했다. 둘다BACKUP보다강한제동쪽으로원래source-response구간밖이었다.** 그두예측의최대force peak1.048031,최소footprint여유1.816517m였다. 실제로실행하지않았으며실제안전·완주를증명한것은아니다.

따라서이번결과를“고정조향에서안전명령이전혀없다/조향·경로변경이필수”라고말할수없다. **현재제한된pedal구간과force경계에민감한유한선택기가실제정지를일으켰고,밖의강한제동예측은가능했다**는범위로한정한다. 구간안도9개coarse후보실패이지연속공간전체불가능성증명이아니다.535의국소footprint회피는성공했지만package의실제빠른완주는미검증·미승격이다.

## 비용·계상·보존

원600CPU상한실행의완료저장분은읽기재구성으로64714ticks(1820execution+62894forecast),explicit force261620,forecastgeometry45711회였다. 미완료carry부분카운터는알수없으므로전체원실행을**등록상한120000ticks/600000explicit force/130000geometry로보수계상**한다. 정확한사용량으로꾸미지않았다.

후속실측은carry복구23334ticks,그native단계추가12692ticks,정지진단2876ticks로38902ticks다. 전체수학적적분사용량은 **103616~158902ticks**,별도explicit force는 **422680~761060회**로경계계상한다. 적분내wheel force는tick당4회로별도다. 실제Box2D1150raw는이수학적모델tick과다르다.

후속worker CPU는carry244.077849초/native72.305265초/정지진단22.739449초다. 초기준비·국소감사·순수구간분류·최종감사는별도실측으로JSON에남겼다. 최초600초는cap도달값이며정확한최종CPU계측값과혼동하지않는다. 준비/registration/publication allowance5CPU/5wall는별도다. 예산복구와미완료카운터한계는실제action차감에영향이없다. **연구24155−262=23893,예비84000미사용**이다.

공개물은코드/계약/집계뿐이며지도·좌표·root·원시명령/궤적/관측·seed/RNG/case는비공개다. 지정cloud 단일작업/기존DEV만사용했고HOLDOUT/SEALED·새seed·보호평가·별도유료자원0이다. 원533미수렴·534실패·535비용중단·실제미완주를보존했고main지정SHA/Participants/사용자변경/기존백업을유지한다. 승인종료2026-10-20 19:01:55KST를자동연장하지않는다.
