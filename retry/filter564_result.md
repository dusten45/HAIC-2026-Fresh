# 564 — 실제 위반점에서 재선형화한 복구는 residual을 줄였으나 exact feasibility 미달

**안전한 새 유한 제안0,새 실제 피드백 continuation0,승격0**이다.두 번의 복구로 최대 정규화 위반은.363573→.0596315→.000523247로 감소했다.마지막 제안도 프로그램 힘1.059005232>1.059,누적 clipping최고11%>10%이므로 채택하지 않았다.사전 방향당3회 제안 상한에서 멈췄다.이는 이 유한 실행의 결과이며 순차법 전체의 불가능성이나 수학적 정체를 뜻하지 않는다.

기존 source 성공13.22초와 실제 native13.66초를 유지한다.새 incumbent가 없어562전체 정책 성공·563독립662raw 재생 증거를 재사용하고,불필요한 전체 정책 실행/전체 재생을 하지 않았다.

## 사전 수치 알고리즘과 비용 경계

정확한 feasible seed는561 첫 전역 안전 후보이며,당시 aperture 탈락 판정은 보존한다.그 상태에서562의 기존551/537 피드백은 전체 안전13.22초를 확인했다.원551prefix1–34와 tracking3/160,20변수hold35–54,고정55–67,원551reference와 고정54/66/75 plane을 유지했다.terminal은 실제 사용할 기존 피드백12hold68–79를 새로 계산한 행동75 plane 도착 시각이다.원54/66 시각도 기록하지만 개별 비악화나5ms 승격 문턱은 없다.

초기 신뢰 영역은 steer.003/pedal.03으로 정규화한 radius1이다.40개의 새 float32 유한차분 열로 시간 목적·모든 물리 slacks·개별 force ratio를 선형화하고,prefix별 상위K를 제외한 충분 rank 제약을 만든다.미분용12hold tape는 현재 안전 incumbent의 실제 저장 피드백이며,**frozen-policy surrogate일 뿐**이다.

시간 LP가 nonlinear source 검사에서 거절되면 그 거절점에서40열을 다시 계산한다.관측된 force 위반 표본·위반 prefix·rank상1 이하로 복구해야 할 표본을 기록하고,elastic LP로 정규화 최대 residual eta를 최소화한다.그 eta 안에서 시간 목적을 다시 푼다.복구 이동은 거절점 주변.75radius 및 안전 incumbent 주변radius의 교집합이다.재구성 방향을 실제 source로 검증한다.위험한 수치 복구점은 미분 중심일 뿐 policy incumbent가 아니다.

복구점의 다음 재선형화는 residual20% 이상 감소와 frozen terminal시각 incumbent+5ms 이내의 수치 filter를 요구한다.이5ms는 unsafe 중심의 수치 탐색 제한이며 승격 문턱/안전 허용치가 아니다.진척이 없으면 radius를.5배 줄여 안전 incumbent에서 새로 선형화하고,.125 미만이면 중단하도록 등록했다.이번 실행에서는 복구 감소가 충분해 radius1을 유지했다.

최대3주요방향·5선형화/FD200열·3복구선형화·12제안·실제피드백4회·방향당3제안을 고정했다.작은 안전 시간 개선1μs 초과는 새 incumbent가 될 수 있다.두 번의 수락 이득.02ms 미만/예측 불일치에도 중단한다.프로그램 전역 안전을 통과한 제안만 새 피드백을 실행하며,그 실제 continuation까지 안전하고 terminal시간이 개선돼야 채택한다.예측 이득이나 안전하지 않은 제안은 채택하지 않는다.

전체 model223,900틱·CPU3,300초/wall4,000초를 등록했고,최종 새 후보만 수행하는 whole feedback120,000틱/CPU1,600초와 독립 tape검증1,600틱/CPU40초를 별도 보존했다.모든 단계의 actual/reset/world 상한0,보호/예비0이다.원 물리 안전 허용치는 바꾸지 않았다.

## 초기 기술 오류와 중복 없는 복구

처음 prefix136raw 뒤 메모리 root의tuple과 저장JSON list를 그대로 비교해 AssertionError가 발생했다.최적화/FD/새제안 전이었다.원 실행기·계약·실패 결과·비용·private traceback을 그대로 보존했다.136raw의 저장 JSON fullstate/force가551원기록과 정확히 같음을 읽기 전용으로 확인했다.

같은564 안에서 별도 복구 계약을 등록하고 저장 checkpoint를 복원해 다음 seed 전파부터 진행했다.원136raw를 다시 계산하지 않았다.복구는 canonical JSON 비교와 상태 복원·기록 경로·누적비용 처리만 바꿨고,evaluate/linearize/solve/room/violation의 수치 알고리즘 AST가 원 실행기와 같은 것을 감사했다.기존1.366405 CPU초/136틱을 전체 비용에 포함했다.최종 성공으로 초기 오류 기록을 덮어쓰지 않았다.

## 유한 복구 결과

원 prefix136raw,seed program132raw+저장피드백48raw의 모든 상태/힘이 원 기록과 정확히 일치했다.변경 handoff의 전체 checkpoint와 tracking30/688도562와 같았다.새 선형화3회/FD120열,프로그램+frozen tail 제안3회,그중 복구2회였다.

|제안|프로그램 힘 최고|프로그램 누적 clipping 최고|180raw surrogate 최대 정규화 위반|채택|
|---|---:|---:|---:|---|
|시간 LP|1.060546909|11.6667%|.363572813|거절|
|첫 재선형화 복구|1.058999602|11%|.059631484|거절|
|둘째 재선형화 복구|1.059005232|11%|.000523247|거절|

첫 복구는 힘 한도 안으로 들어왔지만 clipping에서 탈락했다.둘째 복구는 힘을5.23247×10⁻⁶ 초과했다.프로그램의 prefix order-stat 최소 여유는−.003635728→−.0000974550→−.00000382027로 줄었지만 여전히 음수다.최고 clipping은35/300→33/300→33/300이며,끝 이력은36/688→34/688→34/688이다.끝 비율이 낮아도 중간 prefix의10%를 넘으면 안전하지 않다.

마지막 제안은 행동39/raw2에서 먼저 FORCE를 위반했고,원시 force 표본70/91이 한도를 넘었다.중간 clipping은 행동43/raw3의33/300이다.새 clipping은seed대비6→4→4개,해제는모두0개다.엄격한 `ratio>1`이므로1에 가까운 양의 residual을 수치 오차라는 이유로 unclipped로 바꾸지 않았다.

복구 중심1에는 force위반3표본·위반prefix24개·rank복구 표본5개,중심2에는 force위반0·위반prefix16개·복구 표본3개가 관측됐다.각 중심에서 미분을 새로 계산했다.복구 후 incumbent기준 제어 방향과 직전 거절 방향의 cosine은.984865/.996750으로,동일 방향의 단순 축소가 아니었다.

**rank 집합의 한계도 명시한다.**각 중심에서 rank를 재계산했지만 최종 union nonexempt 표본692개의 membership은 초기와 같았다.새 rank 분기로 이동한 실험이라고 주장하지 않는다.실제 validator는 새 clipping 자체를 금지하지 않고 원 누적한도로 판정했다.미분/예측이 달라진 같은 충분 rank 분기에서의 복구를 검사한 것이다.

surrogate 위반에는 프로그램 이후 저장된 frozen 피드백의 footprint/reference도 포함된다.첫/둘째 surrogate footprint slack은−.0165514m/−.00596315m,마지막은+.0000170112m였다.이들은 새 실제 피드백의 안전/실패 관측이 아니다.세 프로그램 자체가 모두 탈락해 새 피드백을 실행하지 않았다.예측 terminal이득12.343/11.958/11.914ms도 실제 성능으로 채택하지 않았다.

## 판단과 남은 장애물

실제 unsafe 상태에서 갱신한 gradient와 elastic 복구는 위반을 크게 줄였다.그러나 exact feasible 유한 제안에는 도달하지 못했고,따라서 새 실제 feedback continuation의 누적 시간 개선도 아직 관측하지 못했다.세 번째 제안 뒤 사전 횟수 상한으로 중단했으므로,CPU예산 소진·알고리즘 수렴·보편적 정체로 표현하지 않는다.

구체적인 남은 문제는 경계에 도착하는 LP의 작은 nonlinear residual이 엄격한 clipping 표본 수를 계속 초과시키는 점이다.이번 분기의 비clipping 선형 목표는 중심의ratio>=1 표본에서1 경계에 놓였고,별도 엄격 내부 목표를 두지 않았다.같은 union rank membership이 유지된 것도 검사 범위의 한계다.다음 설계는 이 두 원인을 구분해 다뤄야 하며,안전 허용치 완화나 예측 이득 채택으로 해결해서는 안 된다.이번564에 사후로 복구 횟수/방향 상한을 늘리지는 않았다.

## 비용·검증·보존

|범위|model틱|CPU초|wall초|
|---|---:|---:|---:|
|원 prefix(초기 오류 전,재사용)|136|1.364108|1.386683|
|seed180+FD120×180+제안3×180|22,320|273.447003|273.608506|
|초기 실패+복구 실행기 총계|**22,456**|**275.125421**|**275.449909**|

명시 휠 힘89,824회·적분 내부 힘89,824회,geometry/body검사각22,456회다.모든 body 최고95.287268m/s<100,모든 사전 cap 안이다.전체CPU/wall은 초기 실패와 복구 실행의 누적 계측 범위이며 둘 사이 사람/편집 대기·초기 로딩·Git까지의 end-to-end시간은 아니다.원자 비용-FIRST 원장에 보존했다.기존560 비용 계측 공백은 그대로다.

읽기 전용 감사22항목 통과,model/force/geometry0이다.새 실제 피드백/새 whole suffix/수락에 대한 조건부 검사 대상0건을 `scope_counts`/`not_exercised`로 명시했다.새 incumbent가 없어 기존whole성공 증거를 재사용했고 동일662raw 재생을 반복하지 않았다.

실제 행동/reset/world·새seed·HOLDOUT/SEALED·예비·유료/별도 환경0이다.연구22,758·예비84,000을 유지한다.원시 지도/상태/FD/명령은저장소밖비공개다.main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자 변경·기존 실패/백업을 보존했다.사용자 대화의 연장 승인에 따른 종료2026-10-20 19:01:55KST와 자동 연장 금지를 유지한다.

[원 계약](filter564_contract.json) · [원 오류/비용](filter564_result.json) · [복구 계약](filter564_recovery_contract.json) · [복구 실행기](filter564_recovery.py) · [최종 결과](filter564_recovery_result.json) · [누적 비용](filter564_recovery_cost.json) · [감사](filter564_audit.json)
