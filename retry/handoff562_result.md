# 562 — 고정 suffix는 장애물 실패, 기존 피드백은 안전13.22초 완주·전체 이득0ms

561 첫 후보의 서로 다른 횡상태에서 **기존551/537 피드백 suffix로 안전한 전체 source 완주가 가능했다.** reset부터 저장 prefix+수정 구간+새 피드백을 연결한 공식 source finish는 **13.22초**,저장55113.22초 대비 **0ms**다. 전체 명령 tape를 독립 재전파해 모든 fullstate/force·방문/clip/tracker checkpoint와 finish가 정확히 일치했다. 실제 native 기록13.66초는 바꾸지 않았다.

먼저 실행한 원551 **고정 명령 suffix는5.72초,행동72/raw2에서 장애물 footprint−.036951m**로 실패했다. 기존12hold+buffer의 국소 안전이나 작은 plane 시각 차이를 전체 연결 보장으로 쓸 수 없었다.561의 aperture 미달 판정은 그대로이며,이번은 aperture를 완화한 재시험이 아닌 **후속 정책의 실제 source 연결 가능성** 검사다.

## 사전 두 시도·상태/시간 경계

순서는 계산 전에 다음으로 고정했다.

1. 원551 reset source 상태에서 원 prefix 행동1–34,561 첫 rank 후보의 수정 행동35–54와 원 행동55–67을 전파한다. 총268raw를 원기록과 정확히 비교하고 handoff를 고정한다.
2. 그 변경 handoff에서 원551 저장 명령68–마지막을 **한 번** 전파한다. 첫 전역 위반 또는 finish에서 멈춘다. 마지막 저장 행동은 finish가 아직 없으면4raw까지 허용하며 이후 새 고정 명령은 만들지 않는다.
3. 고정 suffix가 실패한 경우에만 **동일한 변경 handoff checkpoint**에서 기존551profile/backup·structure537 choose를 한 번 실행한다. 실패한 물리 상태나 baseline 상태에서 다시 시작하지 않는다. 새 PP/pedal/gain/안전 한도는 없다.
4. 안전 finish가 있으면 전체 reset→prefix→수정→성공 suffix의 실제 명령 tape를 source로 독립 재전파한다. 정책 selector를 다시 최적화하지 않고 매raw state/force·전체 checkpoint/finish를 비교한다. 양쪽 실패 시에는 두 실패 tape의 첫 위반/마지막 정책 실패 root를 독립 확인하도록 등록했다.

비용 상한은 준비300틱/CPU20초,고정1,000/30초,피드백130,000/1,800초,마지막검증2,500/60초,총 **model133,800·명시 휠 힘618,200·geometry149,000·CPU1,910초/wall2,265초**다. kernel hard200,000은 수정하지 않았다. 실제cap0·새seed/보호평가/예비/다른환경/유료0,독점 STARTED·각 phase finally costFIRST·원자JSON 저장을 적용했다. 모든 forecast body도100 미만을 검사했다.

모든 raw에서 기존 원 전역 기준을 적용한다: footprint≥.5m,path≤3m,tracking force≤1.059·누적clip≤10%,원551reference overspeed≤4.85,모든hull/wheel<100이다. 원 출발24hold는 기존peak2.5/clip15% 규칙을 그대로 재현한다. 비교용 위치 aperture/yaw 차이는 이번 suffix의 veto가 아니다.

finish는 원 `FinishLineTracker`의95% 방문 자격·start departure·정방향 crossing·폭/깊이 확인과 hull/contact sensor를 쓴다. epoch1.02초를 제외한 `finish_time_s`가 source 공식 시간이며,arc/holdcount/국소plane 이득으로 대체하지 않는다. 저장551의 전체 tracker를 saved raw로 재구성해 정확히 일치함을 먼저 확인했다. 원시 source 모델은 기존closure524 rigid-body 근사이며 native Box2D solver 전체 상태의 새 실제 실험이 아니다.

## 재현·이력 보존

원 prefix136raw와 수정 구간132raw의 모든 root/contact/force가 각각551·561 저장 기록에 **정확히 일치**했다. 수정 제어는20hold뿐이다. handoff는 행동67 뒤,elapsed5.36초의 실제 source 전파 상태다.

동일 시각 baseline과 handoff COM 위치 차이는 **1.640058m**,COM 속도 벡터 차이.175695m/s,속도 차이−.136718m/s,yaw 차이+.00009336rad/s,wheel omega 최대차.254032rad/s였다. joint는 이 시점에 동일했지만 모든 wheel/gas/joint/offset 등 상태를 그대로 유지했다. 이 차이 중 어느 하나만으로 정책 회복을 일반화하지 않는다.

새 handoff tracking 이력은 **30/688**이고 baseline31/688로 덮어쓰지 않았다. 방문집합·tracker·elapsed·원 launch 이력도 포함한 checkpoint hash가 고정/피드백 시도의 초기값에서 동일했다. 고정 실패 후피드백은 같은 handoff에서 분기한 **대안 suffix**이며,실패한 가상 branch의 추가 이력을 이중 누적하거나 실제 이력을0으로 만들지 않는다.

## 고정 명령: 원인과 위치

고정 suffix는 행동68부터18raw 뒤,전체source **5.72초**의행동72/raw2에서 첫 `FOOTPRINT` 위반이 발생했다. 그때 force최고.716197,경로거리1.780427m,reference초과1.942860m/s로 해당 기준은 안이었다.

기록된 첫 실패 state만 추가 geometry component2회로 분해했다(model/force0).

| 첫 실패 지표 | 값 |
|---|---:|
|도로 여유|4.881245m|
|장애물 여유|**−.036951m**|
|같은 시각 baseline 전체 여유|1.486333m|
|baseline 대비 COM 위치 거리|1.680751m|
|COM 속도 벡터 차이|.213171m/s|
|body 방향/yaw 차이|−.001978rad /−.002165rad/s|

즉 최초 실패는 비교 aperture/yaw가 아니라 실제 source geometry의 **장애물**이었다. 방향·속도 차이가 작아도 횡위치가 다른 경로에 기존 명령을 무반응으로 유지하면 충돌 여유가 보존되지 않았다. 원자료를 보지 않고 실제 native 충돌/손상을 관측했다고 주장하지 않는다.

## 기존 피드백: 안전 완주와 독립 전체 검증

고정 suffix 실패 뒤,동일 변경 handoff에서 기존551/537가 현재 fullstate·progress·실제tracking history로 명령을 다시 계산했다. 선택 행동은 매번 새 `FINAL`12hold 인증을 통과했다. 이99개 source 행동은 원 저장suffix와 모두 조향이 달랐고,pedal이 달라진 것은61개였다. 어느 변경 하나만이 성공 원인이라고 분리 주장하지 않는다.

피드백 suffix394raw가 안전 finish에 도달했다. 전체는 **166source행동/662raw**,finish확인 시각13.24초이며 tracker의공식 crossing 시각은 **13.22초**다. local4.284/5.243ms를 합산/차감하지 않았다.

| 연결한 전체 source | 결과 |
|---|---:|
|공식 finish /551 대비|**13.22s /0ms**|
|최소 footprint|.543878m|
|최대 path 거리|2.085368m|
|최대 tracking force|1.058994|
|최대 body 속도|96.932332m/s|
|누적 tracking clipping 최고|9.6667%|
|끝 clipping history|81/2,264|
|원 reference 초과 최고|4.849804m/s|

launch는 원prefix와 같은peak2.403901·기존15% 규칙 안이었다. selected/rejected forecast를 포함한 모든 모델 body 최고는97.003938m/s로100 미만이다. tracking force/reference는 내부한계에 매우 가깝고 실제 footprint여유도 넓다고 주장하지 않는다.

성공 tape를 reset부터 새로662raw 전파한 마지막 검증에서 **모든 fullstate/force,전체 tracker/visited/launch·tracking history/elapsed와 동일finish가 정확히 일치**했다. 새actual환경이나 재선택한 피드백 trial은 아니다.561 원aperture 실패를 과거 통과로 바꾸지 않았으며,이번source 완주도 실제native13.66초 개선으로 부르지 않는다.

## 다음 handoff 정의에 대한 판단

이 한 변경 상태는 baseline위치와1.6m 달라도 기존 피드백으로 안전완주에 연결됐다. 따라서 baseline위치 일치를 **이 상태의 피드백 연결에 필요한 물리 조건**으로 삼을 근거는 없다. 반면 고정 suffix는 진짜 장애물에서 실패했으므로 “12hold후속이 안전했음”만으로 나머지 주행을 보장할 수도 없다.

다음 최적화의 handoff는 baseline pose복사보다 **변경된 전체 상태/이력에서 실제 사용할 정책의 인증·안전 continuation과그 시간 비용**으로 정의하는 편이 이 증거에 맞는다. 해당 정책의한번12hold 인증이 모든미래상태의 재귀가능성을 보장한다는 뜻은 아니며,최종 후보에는 전체suffix 확인이 필요하다. 이번전체시간은동률이므로 국소plane 목적만으로전체finish 개선을 주장할 수 없다. 보편적횡위치허용폭·terminal set·픽셀정책 일반화도 얻지 않았다. 이번 단계에서는추가최적화하지 않았다.

## 비용·감사·보존

|phase|model틱|CPU초|
|---|---:|---:|
|prefix/수정 재현|268|3.652200|
|고정suffix|18|.295243|
|피드백suffix(실제394+forecast40,715)|41,109|511.146718|
|독립 전체검증|662|11.134578|
|합계|**42,057**|**526.228739**|

명시 휠 힘 **171,932회**·적분내부168,228회,geometry **44,185회**·body검사42,057회다. 추가 첫실패 진단은 geometry component2회/model·force0,CPU.049375초/wall.049524초다. timed phase+진단 CPU합 **526.278114초**,wall합526.526849초다. wall은작은동시진단을포함한범위합이며,end-to-end작업시간이아니다. 초기로딩/저장tracker재생·편집·Git까지완전계측한총비용을주장하지않는다. 모든사전상한안이다.

읽기전용 감사 **21항목**이 source/입력/STARTED·finally비용·동일prefix/명령/변경handoff·실제장애물실패·기존피드백FINAL·전체글로벌안전·직접측정finish/시간차·독립마지막fullstate·forecast몸체/모든비용·기존561판정·main을확인했다. 감사model/force/geometry0이다. 원자JSON ledger로이번CPU/wall이보존됐으며560의기존계측공백은별도로유지한다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·예비사용·다른환경·유료0,연구 **22,758**·예비 **84,000**이다. 원시지도/상태/명령/방문/정책보고/실패와tape는저장소밖비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자변경·기존실패/백업을보존한다. 개인원문의직접독해나파일요청/전송을주장하지않는다. 종료 **2026-10-20 19:01:55KST**,자동연장없음이다.

[사전계약](handoff562_contract.json) · [실행기](handoff562_model.py) · [원결과/finish](handoff562_result.json) · [첫실패분해](handoff562_diagnostic.json) · [phase비용](handoff562_cost.json) · [독립감사](handoff562_audit.json)
