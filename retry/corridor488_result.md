# 488 — centerline-normal lattice 방법군의 최소 경로 구성 계약

**새 방법군의 설계만 완료했다. grid·경로·탐색·최적화·profile·물리·seed 실행은 모두0이다.** 첫485의 노출된 저장 지도 한 개에서 시간 최적화 없이 기하 자격을 갖춘 reference 후보 하나를 만들 수 있는지가 다음 실험의 목적이다. 둘째 조건은 사용하지 않는다. 표현·탐색·증명을 함께 바꾸는 방법군 비교이며, 한 요소만 바꿔야 한다는 제약을 두지 않는다.

연결 해제 알림 뒤 같은 환경에서 `pwd`, git 및 저장 입력/결과 읽기를 확인했다. 환경 전환 없이 계속했고 마지막 확정 실행은487이다. 기존 main·Participants·backup·485~487 자료와 연구 잔여26,175·예비84,000/사용0을 보존한다. 최신 종료는2026-10-20 19:01:55 KST이며 자동 연장은 없다.

## 경로 표현과 고정 resolution

원래 `geometry(snapshot)`의 road-index 순서 center `c_i`, normal `n_i`, centerline arc `s_i,L`을 사용한다. 저장 자료의 차원은321 stations·6 obstacles이며 이 숫자만 읽었다. 새 grid 좌표는 계산하지 않았다.

offset 기본값은 `0,+0.5,−0.5,…,+4.5,−4.5,+B,−B`의21개다. `B=40/6−1.4−0.35`는 원래 source float 결과를 고정한다. 0.5m는 계산량을 제한하기 위한 사전 resolution이며 충분성 보장은 없다. 양쪽 회피를 모두 포함하고 boundary 두 값도 남긴다. 지도에 맞춰 resolution·회피측을 고르지 않는다.

node는 원래 sampled10m smoothstep taper `τ_i`를 써 `p_i=c_i+n_i(τ_i q)`로 만든다. actual float64 point bits를 기준으로 중복을 제거하고 위 canonical 순서의 첫 값을 남긴다. 시작·첫 이웃·마지막 station은 아래 연속 offset 증명 때문에 원래 center bytes를 직접 사용한다. `c+n*0`로 다시 만들지 않아 ±0 alias도 제거한다. 출력은 N개 station이며 폐곡선 endpoint를 중복 append하지 않는다.

## taper·전체 선분·closed seam의 증명

최종 표현은 이 node를 연결한 직선 polyline이다. 실제 segment와 center chord의 차이는

`P(t)−C(t)=(1−t)(p_i−c_i)+t(p_j−c_j)`

이다. 이를 `보간 offset × 보간 normal`로 바꾸지 않는다. normal이 회전하면 두 식은 다르다.

동결된 source arc 숫자를 정확한 상수로 놓은 해석적 `τ_ref(s)`를 정의한다. smoothstep의 이 함수는 `[0,L]`에서 증가·plateau·감소하므로 각 edge label 구간의 최소는 양 endpoint 중 작은 값이다. 마지막 edge는 `s_last→L`로 풀며 `τ_ref(L)=0`이다. 새 경로의 runtime arc와 혼동하지 않는다.

각 edge의 `τ_min`에 대해 두 endpoint의 **actual serialized displacement**가 `||p−c||≤Bτ_min`인지 확인한다. 그러면 norm의 볼록성으로 전체 segment에서 `||P−C||≤Bτ_min≤Bτ_ref(s)`가 성립한다. 각 node에는 양 incident edge 중 작은 bound를 적용한다. 첫·마지막 edge의 최소 taper가0이어서 첫 이웃과 마지막 node도 center로 고정된다.

이는 rounding까지 명시한 보수적 충분조건이다. `Fraction.from_float(p)−Fraction.from_float(c)`로 차이를 만들며 float 차이를 먼저 뺀 뒤 Fraction으로 바꾸지 않는다. frozen B·arc·L도 같은 정확한 상수 체계로 다룬다. sampled taper와 해석적 taper의 rounding 차이는 epsilon 보정 없이 fail-closed 처리한다. 실제 도로 polygon 안에 차체가 있다는 증명으로 확대하지 않는다. 원래 도로 gate는 normal-offset proxy다.

모든 graph edge에서 여섯 장애물 각각과 **전체 직선 구간** 사이 최소거리를 검사한다. 원래 physical radius+2.9+0.25 inflation을 유지한다. endpoint만 검사하거나 원래 buffer·허용잔차를 완화하지 않는다.

## curvature 상태와 유한 탐색

층별 상태는 `(이전 node rank, 현재 node rank)`다. pair의 실제 두 점이 incoming heading을 보존하므로 별도 heading 각도 양자화는 하지 않는다. 다음 node를 연결할 때 원래 세 점 curvature 식을 middle node에서 검사한다. 추가로 incoming/outgoing edge의 dot product>0을 요구해 denominator floor가 숨길 수 있는 collinear 역전 연결을 막는다.

dot 조건은 chord 회전을90° 미만으로 제한하는 추가 construction 조건이며 source 고유 요구나 실제 차량 heading 자격이 아니다. closing/root를 포함한 모든 triple에 적용한다.

탐색은 시간·길이 score가 없는 한 번의 layered reachability DP다. 시작 pair는 두 center node 하나다. 각 target pair의 가장 작은 canonical predecessor rank를 남기고, 종료 때 lexicographically 가장 작은 valid terminal pair를 택해 경로 하나만 복원한다. candidate 선택 후 다른 goal을 재시도하지 않는다.

마지막에는 closing edge뿐 아니라 `(마지막 전 node,마지막 node,p0)`와 `(마지막 node,p0,p1)`의 곡률을 검사한다. 따라서 N개 edge와 seam을 포함한 N개 vertex가 모두 검사된다. source arc는 `0=s0<…<s_last<L`이고 L>0인지 먼저 확인한다.

graph는 clearance≥0, 원래 curvature target 이하, 위 dot 연결 조건과 연속 tube 증명을 쓰는 **보수적 subfamily**다. 기존 `free_feasible`의 작은 aggregate 잔차 허용까지 모두 탐색한다는 주장은 하지 않는다. 완료 DP의 no-goal은 이 고정 graph의 실패일 뿐, 다른 resolution·원래 허용 graph·연속 경로·물리 simulator에서 경로가 없다는 뜻이 아니다.

## 독립 source gate와 executor 경계

검색 코드와 별도 checker가 원본 입력·source·actual point bytes·q/offset·전체 edge·seam·곡률·mask/parent 기록을 다시 확인한다. 원래 acceptance는 그대로 `minclearance≥−1e−6`와 `V≤1e−8`이다. V의 장애물·곡률·offset 성분을 원래 연산 정의로 재계산하고 새 연속 tube certificate도 요구한다. 검색의 cached pass 값만 신뢰하지 않는다.

이 계약에는 smoothing·resampling·waypoint shortcut·사후 rounding이 없다. 인증한 최종 bytes의 직선들을 executor에 넘겨야 한다. 장애물과 offset은 segment 전체를 인증하고, 곡률은 원래3점 proxy를 모든 corner에서 인증한다. **polyline corner의 고전적인 연속 C² 곡률이 유한하다는 증명은 아니다.** 그 강한 요구가 필요하면 smooth curve 표현과 별도 연속 곡률 증명이 필요하다. 이후 보간·변환이 생기면 certificate를 재사용하지 않고 실제 최종 경로 전체를 다시 인증해야 한다.

기존 executor는 B16 계수가 아니라 `line(M,2)`, `ds(M)`, `speed(M+1)`, model을 소비한다. 따라서 polyline은 표현할 수 있지만 이번 최소 탐색은 아직 완전한 executor 입력을 만들지 않는다. ds>0·closure 중복 부재·finite schema를 확인하고, 이후 속도/pace/P4는 같은 최종 line에서 새로 만들어야 한다. 485의 노드를 복사하지 않는다. profile·P4·SourceC act·native/model witness는 이번 시험에 포함하지 않는다.

선택된 경로의 duplicate·adjacent backtracking·nonadjacent intersection/overlap과 on-reference projection 조건도 별도 compatibility 결과로 남긴다. 기존 cursor window와 off-reference projection·tracking은 여전히 자격 미확보다. 사후 compatibility 실패 시 pair merge로 다른 prefix가 사라졌을 수 있으므로 모든 compatible 경로가 없다고 주장하지 않고 종료한다.

## 고정 비용과 판정

| 항목 | 저장 지도 차원의 상한 | 전체 hard cap |
|---|---:|---:|
| stations / node rank |321 / 21|512 / 21|
| node 후보 |6,741|10,752|
| pair states·edge 검사 |141,561|225,792|
| 전체 obstacle-distance pairs |849,366|1,354,752|
| triple 검사 |2,972,781|4,741,632|

독립 감사의 predicate 재계산에도 같은 별도 상한을 둔다. parent는 uint8 sentinel 포함으로 기록하고, triple predicate는 층별로 stream해 `N×K³` float 배열을 만들지 않는다. 층별 reachability/predecessor·edge margin/mask·packed triple bits·source hash·복원 경로와 certificate를 비공개로 보존한다.

전체 CPU60초/wall90초, RSS256MiB, retained16MiB/40파일, 파일·temp2MiB, 종료2파일·64KiB 및 각 volume512MiB 예비를 강제하도록 제안한다. 코드·집계·출판 기록도 하나의 global quota에서 미리 예약한다. import·등록·rational 검사·탐색·독립 감사·전체 readback을 모두 포함한다. 이는 실측 benchmark나 완료 보장이 아니다. 상한에 닿은 부분 탐색은 no-path 판정이 아니라 불확실로 끝낸다.

성공은 독립 원래 source gate와 연속 tube certificate를 통과한 geometry 후보 하나이며 compatibility를 별도 표시한다. 속도·추종·native·pixel·완주 승격은 없다. 완결 DP에 goal이 없으면 이 한 지도에서 고정 방법의 충분성을 기각한다. source/checker 불일치·자원/입력/수치 실패는 기술적 불확실이다. geometry 후보가 compatibility를 못 맞추면 그 경계의 미자격으로 기록하고 다른 goal을 고르지 않는다.

별도 승인 후 구현·synthetic 무탐색 fixture·현재 입력/source/상한을 등록한 뒤에만 시작할 제안이다. 488에서는 어떤 grid나 탐색도 실행하지 않았다. 해상도 확대·새 방법·조건 대체·자동 후속은 없다.

[상세 계약](corridor488_contract.json) · [정적 독립 검토](corridor488_review.md) · [metadata 설계 소스](design488.py)
