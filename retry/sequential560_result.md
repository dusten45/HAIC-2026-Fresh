# 560 — 순차 feasible 최적화: 첫 방향의 세 제안을 실제 안전 위반으로 거절, incumbent 보존

**559의5ms 미달을 중단 기준으로 쓰지 않았다.** 더 긴 도달 source 구간에서40개 제어를 함께 바꾸는 bounded sequential feasible 최적화를 등록했다. 첫 방향의 세 제안은 시간 이득을 보였지만 **모두 실제 누적 clipping10%를 초과**해 거절됐다.1번은force,2번은footprint도 넘었다. 사전3회 복구 한도에서 멈췄으며 **수락0회·최종 누적 개선0ms**,exact feasible baseline을 보존했다. 더 작은 radius나 다른 방향을 추가 실행하지 않았다.

두 기록 처리 오류가 발생했다. 원실행의 NumPy int64 JSON 직렬화 오류와 첫 복구의 적분/후처리 cap 혼용을 모두 보존했다. 추가 최적화 없이 최종 baseline132raw를 새 검증기에서 확인했고 전체 state/contact/force가 정확히 일치했다. **주실행 CPU/perf-wall 계측값은 유실돼 총CPU600초 준수를 독립 감사할 수 없다.** 이 비용 공백은 아래와 감사 JSON에 명시한다.

## 계산 전 문제·구간·예산

구간 선택은559와 같은 `551 tracking before-action progress>=기존533station37의 첫 행동`으로 고정했다. 행동35부터 **20hold 제어(steer/signed pedal40변수)+12hold 고정 후속+1hold 측정 buffer**,총132raw다. 약204m의 연속 도달 source 궤적이며 임의 합성 주기/목표 시간이 아니다. main/follow 공통 plane은 저장20/32hold endpoint의 위치·속도 방향으로 고정했고 기준 시간은 **1.60/2.56초**다. buffer는 늦어진 경계 측정용이며 목표를 늘리거나 임의 재선택하지 않는다.

33개 node의 독립4raw 전파132개와 연속 baseline132raw가 저장551의 전체 world root·contact·힘에 정확히 일치해야 최적화를 시작하도록 했다. 초기 tracking clipping **3/160 wheel samples**를 보존했다. 정확한 baseline과 매번 수락된 feasible incumbent는 immutable 파일로 남기며 거절된 제안으로 교체하지 않는다.

원 전역 조건은 모든 raw의 force≤1.059,footprint≥.5m,path≤3m,**원551 reference** overspeed≤4.85m/s,모든 hull/wheel<100m/s,실제 prefix 누적 clipping≤10%다. no-new-clip mask·고정 contact 분기·주기성·비교용 yaw 한도는 넣지 않았다. 실제 source에서는 pedal/contact/clipping 분기 변화가 허용되며 그 결과로 안전을 판정한다.

공통 경계의 보간 fullstate는 비교 지표이며 source 중간 도달 상태로 부르지 않는다. main plane aperture≤1m,follow≤.5m,후속 body heading 차이≤.08rad·속도 방향차≤.05rad·속도≥baseline−.5m/s를 **국소 handoff 설계**로 정했다. 이는 물리 필요조건이 아니다. yaw/omega/gas/joint의 baseline 동일성은 요구하지 않고 실제 전체 상태와12hold 후속을 전파·기록한다.

방향마다 현재 incumbent에서40개의 one-sided FD(steer1e−5,pedal1e−4,실제 float32 차이)를 계산하고 평균 두-plane 시간의 LP 방향을 만든다. 선형화는 전역 안전·handoff 제약의75% slack 사용과 양쪽 시간 비악화를 요구한다. trust box는 steer .004×radius·pedal .04×radius,초기radius1·최대2·최소.125다. trust는 수치 장치이며 모든 안전 주행의 필요조건이 아니다.

제안은 **정확한132raw source 재전파**에서 물리/return feasibility와 양쪽 시간 비악화(허용.5µs),평균 이득>1µs를 통과하면 수락한다.5ms 이상의 개별 이득은 요구하지 않는다. 시간 예측 ratio[.25,2]와오차≤max(.5ms,예측최대의50%)를 agreement로 정했고,beneficial feasible mismatch도 incumbent로 수락하되 다음radius를 줄이도록 했다. 접촉/clip분기 변화는 그 자체로 veto하지 않으며 radius 증액을 보류한다.

안전/비이득/unbracketed 제안은 incumbent를 유지하고 radius를 절반으로 줄여 **같은 선형 모델**에서 재제안한다. 방향당3제안 모두 실패하면 종료한다. 최대 방향6·수락6·제안18,연속 작은 수락 이득2회(<.02ms)·float32 정체·예측 불일치2회·radius floor·비용/deadline/body domain 중단을 사전 등록했다. 총한도는 **model36,000틱·명시 힘150,000·geometry36,000·CPU600초/wall700초**다. 다음 방향 전에40FD+3trial+final replay의 틱 reserve와 soft CPU480초를 확인한다.

## 실제 첫 방향과 복구 결과

33node 및 연속 baseline 전사는 정확히 통과했다.40FD 뒤 세 LP가 만든 제안은 다음과 같다. 표의 시간은 **거절된 forecast**의 보간값이며 성능 결과가 아니다.

|radius|예측 main/follow 이득(ms)|source main/follow 이득(ms)|force 최고|footprint 최저(m)|prefix clipping 최고|
|---|---:|---:|---:|---:|---:|
|1|8.578 /8.438|5.176 /6.102|**1.063635**|.978374|**11.1842%**|
|.5|5.782 /6.322|2.996 /4.837|1.056319|**.400190**|**11.5132%**|
|.25|2.936 /3.442|1.741 /2.870|1.057741|1.125888|**11.0000%**|

시간 예측 최대 오차는3.402/2.786/1.195ms,실측/예측 평균 ratio는.663/.647/.723이었다. 사전 시간 agreement는 모두 통과했지만 **안전 feasibility는 별개**였다. LP 선형 제약은 각 제안에서 최소0으로 feasible을 예측했으나,source의 prefix clipping은 모두 위반했다.1번은force도,2번은footprint도 실패했다. 세 제안은 handoff position 설계도 미달했으나,그 조건을 제거해도 **독립적인 전역 clipping 위반**이 남는다. 상대 yaw 실패로 거절한 것이 아니다.

|prefix wheel sample|baseline|radius1|radius.5|radius.25|
|---|---:|---:|---:|---:|
|최대 발생 새 raw|35|36|36|35|
|당시 clipped/누적 samples|30/300|34/304|35/304|33/300|
|구간 끝 clipping fraction|4.5058%|5.0872%|5.2326%|4.9419%|

구간 끝 평균이10% 미만이어도 **이미 위반한 prefix를 미래 sample로 상쇄할 수 없다.** no-new-clip mask로 금지한 것이 아니라 실제 이력대로 판정했다. baseline 대비 contact가 달라진 raw는50/36/20개,새 clipped wheel samples는8/6/3개,해제된 clipping은4/1/0개였다. 각 제안에 pedal mode 변화1개·brake-lock 변화0개가 있었다. 반경을 줄여도 footprint/clip이 단조롭게 좋아지지 않았으며,분기 변화가 있는 상황에서 선형 시간 예측만으로 feasibility를 보장할 수 없음을 확인했다.

**세 제안의 실제 안전 실패가 과학적 종료 이유**다. 미세 이득<5ms나 비교 yaw가 이유가 아니다. 수락 단계가 없으므로 후속 방향을 다시 선형화하지 않았다. 사전 방향/수락 상한은 상한이지 반드시 소진할 목표가 아니다.

## 최종 incumbent와 기록 오류 복구

원실행은 세 실패 제안 기록을 저장할 때 boundary count의 NumPy int64가 JSON으로 직렬화되지 않았다. 기존 baseline·40FD·세 trial 원시 기록과 원소스/hash는 보존됐다. 저장된 FD/제어로 J/T·예측/실측·분기 변화·판정을 **새 LP/적분 없이** 복원했다. 세 거절 뒤 중단한다는 원 규칙도 바꾸지 않았다.

첫 복구는 등록한 최종 baseline132raw를 계산했으나,적분 cap을 geometry 후처리에도 적용하는 구현 오류로 저장 전에 멈췄다. 그132틱도 비용에 포함하고 실패를 보존했다. 별도 사전 finalization 계약에서 **동일 baseline 검증만132raw**,추가CPU≤10초/wall≤20초·geometry133회로 제한했다. 적분/geometry guard를 분리하고 매raw를 보존했다. 방향/FD/LP/후보 재실행은0이다.

마지막 새132raw는 baseline의 모든 worldstate/contact/force와 정확히 일치했고 전체 안전을 통과했다. main/follow 경계 **1.60/2.56초**,누적 이득 **0/0ms**,fullstate 차이0이다.12hold 후속과1hold buffer도 동일하게 확인했다. 최종 footprint1.156639m,path1.325267m,원reference overspeed4.849744m/s,force1.058954,body95.424332m/s,clipping 최고10%·끝31/688이다. baseline이 매 거절과 두 기록 오류 중에도 보존됐음을 확인했다.

## 비용·감사 한계·다음 판단

총 **model6,204틱** =원실행5,940(노드132+baseline132+FD5,280+제안396)+첫복구132+최종검증132다. 명시 휠 힘 **24,816회**·적분 내부24,816회,body검사6,204·geometry **5,985회**다. 원 모델/힘/geometry 한도 안이다. rejected forecast3raw의force위반·최고1.063635와모든 body최고95.425435도 저장·계상했다.

**주실행의 process CPU/perf-wall 숫자는 직렬화 오류로 유실되어 복원할 수 없다.** 원CPU600초 타이머가 적용됐으나 이를 총CPU600초 준수의 독립 감사로 바꾸지 않는다. 등록→failure파일 timestamp 차이는약81.552초의 **wall 추정값**일 뿐 measured CPU가 아니다. 첫복구CPU.777177초/wall.778677초,최종검증CPU1.873916초/wall1.874008초는 직접 측정했다. 따라서 총 measured CPU는 null,계측 완결성은 false로 남긴다. 원시 과학 판단/모델 비용을 다시 측정하려고 재실행하지 않았다.

읽기 전용 **증거 감사20항목**이 hash/독점STARTED·정확한 전사·고정 구간·예측/실측 복원·세 실제 안전 실패·반경복구·incumbent 불변·비교yaw/mask/주기 조건 없음·새 최종fullstate·공통공간/후속·모든model/force/geometry 비용·오류 보존·CPU 공백·main을 확인했다. **전체 요청 계측 완료는 false**다. 감사의새source/force/geometry 평가0이며 이 구분을 생략하지 않는다.

누적 최적화의 이번 결과는 “시간 개선이 불가능”이 아니라 **clipping count를 미분한 선형 모델이 실제 prefix feasibility를 회복하지 못함**이다. 시간 예측이 agreement를 통과해도 clip 분기 제약은 틀릴 수 있었다. 다음 새 근거는 이런 prefix clip 경계를 fidelity 있게 표현하는 방식이어야 한다. 예를 들어 초기 이력을 포함한 허용 개수에 대응하는 prefix force order statistic은 새 clipping을 무조건 금지하는 mask와 다르다. 이 표현의 유효성은 이번에 시험하지 않았고,단순 방향/반복/반경 추가로 넘어가지 않았다.559의 판정·558 실패와 실제13.66초는 보존한다. 실제/전체 랩 승격은 하지 않았다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·다른환경·유료0,연구 **22,758**·예비 **84,000/사용0**이다. 지도/개별fullstate/명령/gate/FD/접촉/실패는 저장소 밖 비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·기존 백업을 보존한다. 개인 원문은 parent의 완독·허용 전달 범위로 적용하고 직접 원문 접근이나 파일 요청/전송을 주장하지 않는다. 종료 **2026-10-20 19:01:55KST**,자동 연장 없음이다.

[원 사전계약](sequential560_contract.json) · [원실행기](sequential560_model.py) · [첫복구 기록](sequential560_result.json) · [최종검증 계약](sequential560_finalization_contract.json) · [최종 집계](sequential560_summary.json) · [증거 감사·CPU 공백](sequential560_audit.json)
