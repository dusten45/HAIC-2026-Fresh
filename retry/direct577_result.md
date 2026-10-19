# 577 — 6기저 전체 source 직접 탐색

**원래 안전 기준을 통과한 미세 개선을 얻었다.**573 계획에서24개 실제 float32 후보를 초기 source 상태부터 전체 strict 평가했다.14개가 안전 완주하고10개는 탈락했다. 안전 개선4개를 학습용 incumbent에 누적해 전체 보간 시간 **13.193602510361 → 13.193588066798초**, 실제 개선 **14.443563µs(0.014443563ms)**를 얻었다. 최종 새 계획만 독립661틱 replay했으며 상태·force·이력·visited·tracker·clock·최종 checkpoint가 정확히 일치했다. 공식 tracker는660 raw / **13.20초**, confirmation661로 같아 공식 승격은 없다. Native13.66초는 별도이며 변경되지 않았다.

## 실행 전에 정한 방식

`direct577_contract.json`에6기저·최대2회차·양방향24후보·최종 독립 replay1회를 등록했다. 최대 source 비용은25×662=16,550틱, force66,200회, 전체 CPU600초/wall720초다. 평가 단계15,888틱·CPU480초, 최종검증662틱·CPU30초를 따로 예약했다. 개별 source case는CPU25초/wall35초이며 다음 후보 전에 전체 case와 최종 replay/감사 여유를 확인한다. 초과 시 새 후보 없이 중단한다.

holds1–34는 고정하고35–166을22hold씩6개 시간 구간으로 나눴다. 각 구간44개 steer/signed-pedal 좌표에서 저장574의 음의 시간 gradient를, slack/row norm 기준으로 고른 최대8개 독립적인 물리·rank·signed-support 제약의 tangent에 투영했다.∞norm1로 정규화한6개 기저는 첫 source 이전에 동결했다. 큰 전체 FD나 새 보정은 하지 않았다. 경험적 L*t와 uniform rounding tube는 **후보 생성/거부에 사용하지 않았다.** 기존 Jacobian의 시간·물리 예측은 진단으로만 기록했다.

좌표별 두 방향은 동일한 직전 안전 incumbent에서 평가하고 둘 중 실제 안전 개선1µs 이상·candidate raw≤working인 최선만 선택했다. 초기 normalized step은0.004다. 첫 회차에 채택0일 때만 다음 회차0.002로 줄이고, 채택이 있으면0.004를 유지하도록 고정했다. 완전한 무개선 회차2회면 정체로 종료하며 최대2회차가 끝나면 개선 중이어도 멈춘다. 두 회차 모두2개씩 채택돼 step 축소는 실행되지 않았다. 도메인과 seed 주변 normalized∞radius0.012 안의 실제 representable float32로 제어를 만들며, 예측 개선이 음수여도 원래 source 안전 검사를 실행했다. 중복/quantized-zero slot을 대체하는 추가 탐색은 없다.

## 직접 검사 결과

| hold 구간 | 평가 | 안전 완주 | 학습용 채택 |
|---|---:|---:|---:|
|35–56|4|0|0|
|57–78|4|2|0|
|79–100|4|0|0|
|101–122|4|4|0|
|123–144|4|4|2|
|145–166|4|4|2|

모든 후보는 frozen prefix 이후 tail만 평가한 것이 아니라 **초기 source root·tracker·visited·clock·launch/tracking 이력부터 같은 전체 명령열**을 실행했다. 원551 reference, strict ratio>1 prefix clipping, force≤1.059, footprint≥0.5m, path≤3m, body<100, projection 및 원래 FinishLineTracker를 그대로 적용했다. launch의 별도 원 기준도 유지했다. 안전 실패 시 첫 위반에서 멈추며 진단 continuation이나 실패 상태의 incumbent 채택은 없다.

force 실패4개는 raw155/159에서 각각 peak1.059094945063·1.059000909781로1.059를 넘었다. 두 회차에서 같은 앞부분 실패가 반복됐지만 전체 후보의 후반 명령은 서로 달랐다. footprint 실패6개는raw632에서0.490666–0.498813m로0.5m를 밑돌았다. **실패10개 중8개는 선형 물리 slack 예측이 모두 비음수였고**, 전체24개 중18개는 예측 시간 개선이 비양수였는데도 실제 평가했다. 이는 surrogate가 실제 안전의 인증도 후보 veto도 아니었음을 보여준다. unsafe 후보는 모두 incumbent에서 제외했다.

holds101–122의 한 방향은 각 회차 약0.142µs 개선했지만 사전1µs 기준 미만으로 채택하지 않았다. 실제 채택은123–144와145–166의 각 plus 방향2회씩이다. 전반 기저4개에서 채택이 없었다는 사실은 해당 구간이나 전체 제어공간의 개선 불가능성을 뜻하지 않는다. 시간 gradient의 tangent 투영과 도메인 clipping 뒤 방향은 제한적이며, 이번24개 직접 평가의 결과다. 큰 시간 개선이나 수렴을 주장하지 않는다.

## 독립 검증과 실제 여유

마지막 새 안전 계획 하나만 initial-source에서 독립 replay했다. 원래 prefix의 명령도 유지됐고 전체661행의 before/after root·force·누적 이력·visited count·clock·공식 tracker와 최종8필드 checkpoint가 정확히 일치했다. 실제 독립 테이프에서 footprint 최소0.501688531347m, path 최대2.999942798380m, tracking force 최대1.058989978341, reference overspeed 최대4.849999620498, body 최대96.929067754309다. tracking prefix clip 비율 최대0.10, 검사 대상 launch clip 비율 최대0.147849462366≤0.15이며 launch force 최대2.403901474801≤2.5다. 모든 원래 실패 flag가 비어 있고 ratio>1과 clipped identity도 일치한다. 이 작은 여유는 Native·pixel·feedback 전환·섭동 강건성 인증이 아니다.

## 비용·기록·종료

총 **14,331틱 /16,550**, force **57,340 /66,200**, geometry/body 각14,331회다. 후보 평가13,670틱과 최종검증661틱이며, pre-force에서 실패한4개 case의 force16개도 tick과 구분해 차감했다. kernel hard cap200,000은 변경하지 않았다. runner의 비용은CPU386.448371초/wall409.243674초이고, source 없는 후처리 감사CPU0.646576초/wall0.648912초 및 마지막 writer/해시 비용의 보수적1초를 포함한 전체 예산 차감은 **CPU388.094946/600초, wall410.892586/720초**다. 검사/시작 비용5초도 runner에 이미 포함돼 있다. 단계별 상한이 모두 통과했다.

71,713개 fsync/hash-chain journal 이벤트,24개 case·계획·결정의 원자 기록, source/input 해시 및 tick/force 산술이 일치했다. 도메인/신뢰범위·unsafe 채택 배제·6기저 단위검사3개와 읽기 전용 구현 검토를 source 시작 전에 마쳤다. 이전576과 달리 이번에는 모든 실제 후보 수·실패·결정·최종 결과가 저장됐고 실행 오류가 없다. actual·Native reset/world·새 seed·HOLDOUT·SEALED·새 FD/보정·LP·유료 자원은 모두0이다. 연구22,758·예비84,000·예비사용0을 유지한다.

원시 명령·기저·state·journal은 저장소 밖 비공개 경로에 보존하고 공개 기술 코드/집계만 일반 commit/push한다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·과거 실패를 보존했다.577은 예정된 두 회차와 새 계획의 독립검증까지 끝내고 종료했다. 추가 step sweep·새 연구·tube 수리로 전환하지 않았다.
