# 565 — empirical interior 여유로 exact-safe continuation 두 건, whole-source 이득0ms

564에서 남은 양의 clipping/order-stat 잔차를 처리하기 위해, 임의 buffer를 탐색하지 않고 **단 하나의 오차 기반 내부 여유 규칙**을 frozen design에 고정했다. 이 목표로 두 개의 exact-safe finite trajectory와 각각 새 실제 feedback continuation을 통과시켰다. 채택 terminal 이득은 **7.3083ms와 추가 4.0270ms**, 누적 **11.3353ms**다. 이 값은 행동75 fixed-plane까지의 finite feedback 성적이다.

최종 후보의 whole feedback suffix는 안전하게 source 완주했다. 공식 전체 source 시간은 **13.219999999999807초**, 기존561/562/563과 **동률, 이득0ms**다. 새로운 662raw 독립 재생도 fullstate/힘/checkpoint 및 finish가 정확히 일치했다. 실제 native 기록은 **13.66초 그대로**이며 실제 행동/reset은0이다. finite 11.3353ms를 whole lap이나 실제 native 향상으로 올려 말하지 않는다.

## 내부 여유 규칙의 사전 고정

설계 도구는565 source 모델을 시작하기 전에 보존된564의 **마지막 두 복구 이동**과 각 방향의 40열 Jacobian만 읽었다. source tick·힘·geometry 호출은0이다. 이동2의 ratio 선형화 최대 양의 과대예측은0.00188146849, prefix order-stat 과대예측도0.00188146849였다. 이동3은 각각6.00242×10⁻⁶과3.72323×10⁻⁶이었다. 대응하는 전체 float32 control ULP를 각 constraint Jacobian으로 전달한 최대 ratio 변화는4.49510×10⁻⁷이었다.

사전 고정한 단일 규칙은 각 표본/제약별로 `margin = 2 × (마지막 두 이동에서의 최대 양의 slack 과대예측 + 최대 Jacobian 전파 float32 control ULP + 4 binary64 ulp)`이다. 똑같은 margin 배열을 전체565에서 고정했다. 각 prefix의 충분 rank branch는 상위K 표본을 제외한 모든 ratio가 `1 − 해당 prefix margin` 이하가 되게 했다. 표본이 여러 prefix에 비면 적용 margin의 최댓값을 사용했다. 개별 물리 slacks에도 같은 규칙을 적용했다.

결과적으로 clip ratio 내부 margin의 최댓값은0.00376322, prefix 목표 margin은1.43937×10⁻⁹~0.00376384였다. 예를 들어 가장 큰 내부 force 목표는1.05523678, clipping 대상표본의 큰 쪽 ratio 상한은0.99623678이 된다. 이는 선택한 연구 단계의 수치 목표이지 물리 상수나 보편적 오차 보증이 아니다. 공식 안전 한도 `force<=1.059`, 엄격한 `ratio>1` clipping count/10%와 모든 geometry/reference/body 조건은 바꾸지 않았다. 양의 작은 값을0으로 반올림하지 않았다. 설계 입력·코드·배열 해시는 frozen contract에 기록했다.

## bounded 복구와 관측

출발점은 정확히 재현된561 feasible seed와 마지막564 복구점이다. 마지막564점의 180raw 상태/힘을 새로 적분해 저장된564 기록과 일치시킨 후에만 선형화를 시작했다. 초기 40열 elastic feasibility LP에서 내부 목표를 먼저 맞추고, 그 뒤 정규화 L1 이동을 줄였다. exact-safe actual policy가 생긴 뒤에는 terminal-time 목적 LP를 사용했다. 내부 목표는 모든 복구에서 고정했다.

상한은 선형화8회/FD320열, 복구6회, source 제안10개, fresh finite feedback4회, 안전 수락2회로 사전 등록했다. 정체는 두 번 연속 10% 미만 residual 감소, 신뢰 영역은.125 미만에서 멈춘다. 새 후보 없이 과거 whole replay를 반복하지 않는다. 실제로는3선형화/120열, 복구2회, 제안3개에서 두 안전 수락 한도에 도달했다. 이 중간 종료는 내부 여유의 수렴 또는 연구 전체 정체를 뜻하지 않는다.

|제안|프로그램 검사|실제 fresh feedback12-hold|결과|
|---|---|---|---|
|trial00, restoration|모든 원 안전 게이트 통과; clipping 최고10%, 힘 최고1.05898532, footprint 최소.747657m|전 구간 안전; 힘/clip 최종 history31/880|채택, terminal gain7.308295ms|
|trial01, terminal-time|행동52/raw1에서 PATH 3.00407m>3m|실행 안 함|거절|
|trial02, restoration|모든 원 안전 게이트 통과; clipping 최고10%, 힘 최고1.05898998, footprint 최소.518589m, path 최고2.99994280m, reference overspeed 최고4.84966263|전 구간 안전; 힘/clip 최종 history30/880|채택, 추가 terminal gain4.027048ms|

두 수락 후보는 각각 모든 새 제어에서 실제 계산한 original551/537 feedback을 사용했다. 최종 12-hold 상태의 조향은 각 후보에서 frozen tape와12개 모두 달랐다. clipping count는 매 raw strict `ratio>1`로 세고, 저장된 초기3/160 history에서 이어 계산했다. 두 번째 후보의 path/reference/force/clipping 여유는 좁으므로 넓은 안전 margin이라고 해석하지 않는다. 최종 whole suffix는 별도의 global 검사를 통과했다.

첫 안전 후보 뒤 시간 목적 제안은 경로 한도 때문에 떨어졌다. 안전 후보를 보존한 채 frozen feedback state/history와 유한 제어를 다시 선형화·복구한 세 번째 제안은 두 번째 안전 수락으로 이어졌다. 563의 두 재계산 복구에서 충분 rank membership은 `[0,0,1]` 항목만 달랐다(각 중심의 seed 대비 대칭차 크기). 따라서 첫 두 계산은 membership 변화가 없었고 마지막에서 한 항목이 바뀌었다. 새 mode 전체를 탐색했다고 확대 주장하지 않는다.

두 실제 feedback continuation은 모두 safe했고, 실제 terminal 도착 이득7.308295/4.027048ms였다. frozen-policy 예상 terminal 이득은11.818427/4.964500ms였고, 실제와의 오차는4.510133/0.937452ms다. 수락 판단은 새 feedback terminal 결과를 사용했다. 예측은 수락 판단에 쓰지 않고 오차는 기록했다. 첫 변화 후 전체 source feedback은 기존 tuner가 현재 fullstate·progress·tracking history를 사용해 매번 새로 선택했다.

## whole source와 독립 재생

마지막 finite incumbent에서 기존551/537 full feedback suffix를 한 번 실행했다. 394raw 뒤 tracker의 공식 whole finish는13.219999999999807초, 확정 확인 시각은13.24초다. whole/global checker는 source 안전으로 끝났고, 최대 forecast body는 전체 phase에서97.002107m/s<100이었다. 독립 reset replay는 전체662raw였으며 모든 fullstate/force, final tracker/visited/launch·tracking history·elapsed checkpoint와 finish가 정확히 같았다.

551 기준 whole source13.22초와 동률이다. 안전한 새 whole trajectory이나 finite plane 이득이 원실제 13.66초 기록을 바꾸지 않는다. 실제 source 모델은 기존 rigid-body 근사이며 native Box2D의 새 기록이 아니다.

## 비용·감사·보존

|단계|model tick|CPU초|wall초|
|---|---:|---:|---:|
|내부 여유 산출(저장된 data만)|0|.134394|.136014|
|prefix/seed/starting state +120 FD +제안 3개|22,500|275.309301|275.411030|
|fresh finite feedback 2회|8,026|96.482220|96.506324|
|최종 whole feedback|42,363|511.580968|511.666013|
|독립 whole-tape 재생|662|10.247175|10.339072|
|실행기 합계|**73,687**|**895.679696**|**896.130592**|

명시 휠 힘298,988회·적분 내부 휠 힘294,748회·geometry76,269회·body검사73,687회다. 합계 CPU/wall에 내부 여유 계산을 더하면 **895.814090초 / 896.266606초**다. phase별 모델·힘·geometry·body·CPU/wall 모두 고정 상한 아래였다. 편집·Git까지 포함한 end-to-end 시간을 뜻하지 않는다.

읽기 전용 감사 **30항목 통과**; 감사 model/force/geometry 호출0, 자체 CPU/wall 약.28초다. 감사는 frozen margin hash,원 prefix/seed/마지막564점 재현, 새 proposal gate, 같은 handoff에서 fresh feedback,실제 수락,최종 whole safety/시간,독립 replay,누적 비용·보존 상태를 확인했다. 처음 생성한 감사는 PATH 위반 분류를 빠뜨려 실패했지만, 저장된 row의 원래 `path_error>3`도 탈락 사유로 세도록 읽기 전용 코드를 고쳐 재실행했고 결과가 통과했다. 모델을 다시 돌리지는 않았다.

실제 행동/reset/world·새seed·HOLDOUT/SEALED·예비·다른 환경·유료0이다. 연구22,758·예비84,000, baseline13.66, main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants와 기존 사용자 변경/실패/백업을 보존했다. 원시 지도·상태·명령·FD/tape는 저장소 외부 비공개 디렉터리에 남겼다. 종료는 연장 승인2026-10-20 19:01:55KST이며 자동 연장은 없다.

[내부 여유 사전 설계](interior565_design.py) · [고정 설계 기록](interior565_design.json) · [계약](interior565_contract.json) · [실행기](interior565_model.py) · [결과](interior565_result.json) · [비용](interior565_cost.json) · [감사 코드/결과](interior565_audit.py) · [감사 JSON](interior565_audit.json)
