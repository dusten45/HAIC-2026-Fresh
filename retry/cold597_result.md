597 — 새 cold feedback 정책 전체 source 13.22초, 독립 재생 일치

**577 명령1..39 뒤40부터 원537 feedback을 유지하는 정책이 전체 strict safe official finish를 얻었다.** 공식 candidate raw661,확인 raw662이며,원래 초기 상태에서 조건부 독립 명령 tape 재생662행이 모두 정확히 일치했다. 52에서 고정 tape로 돌아가지 않았다. 이 결과는 지정 DEV case의 source 정책 결과다. native13.66초 기록·기존577source13.20초 incumbent와593~596 기록/비용은 유지한다.

|공식 integer finish 비교|candidate raw|source 시간|597의 차이|
|---|---:|---:|---:|
|저장577source|660|13.20초|1raw/20ms 느림|
|새597source|661|13.22초|기준|
|저장541source|683|13.66초|22raw/440ms 빠름|

597의 확인 raw662/13.24초와 candidate raw661/13.22초를 구분했다. tracker가 candidate crossing 때 기록한 clock으로 integer raw를 구했고,보간 hull/COM 시간이나 path 여유 회복을 성능 향상으로 세지 않았다. 저장577보다 빠르지 않으며 11초대 목표도 달성하지 못했다. source541 대비 시간 차이는 native 이득을 관측한 결과가 아니다.

실행과 선행 게이트

[동결 계약](cold597_contract.json),[사전 확인](cold597_preflight.json),[순수 검사9개](cold597_tests.json)를 전체 실행 전에 기록했다. 정책/551 candidate·backup/reference/cap/gains/원 finite31trial+freshFINAL/동역학/strict 기준은 그대로다.596 계측을 재사용하고 새 초기화·범위·비용/재생 예약만 추가했다. pin된 원래 post-reset/warmup source root,initial visited와 원 tracker_for(carry=False)에서 한 번 시작했다. native/world/reset은 만들지 않았다.

원 코드와 승인 case의 TimeLimit1224raw,wrapper warmup50raw를 확인해 **정책 적용 최대1174raw**로 동결했다. reset 내부1틱은 TimeLimit 계수 밖이며,이미 저장된 reset+warmup51physics raw의 시작 clock은1.02초다. TimeLimit._elapsed_steps는 reset에서0,wrapper warmup env.step50회가50을 소비한다. skip_frames4와 원 종료 검사 순서를 유지했고 1174raw 뒤 적용하지 않는다. 이 실험은 초기 상태를 읽었으므로 새 warmup/reset physics는0이다.

전체 실행의 첫156raw는 새로 계산하고,저장577의 매 raw before/after root·힘 vector/ratio/clipped·launch/tracking 이력·clock·full tracker·progress/geometry/body와 정확히 대조했다. 저장 contact와 initial visited로 재구성한 full visited 집합도 매 raw 일치했다. prefix의 재계산을 읽기 비용으로 숨기지 않았다. prefix39 뒤 source root는 원 source trajectory의 상태이며,596이 사용한 actual native raw156 checkpoint와 혼동하지 않는다.

127feedback chooser·2679certificate를 계산했다. 모든 chooser에서 actual checkpoint가 바뀌지 않았고 모든 trial은 당시 실제 이력에서 독립적으로 시작했다. 원537의2679개 summary가 수동 계측과 정확히 일치했다. 선택된 새 FINAL의 첫4틱 중 실제로 적용한506raw는 root/force/history가 모두 일치했다. 마지막 hold는 official 확인 raw662에서2틱만 적용했다. forecast는 원537의12hold 그대로이며 finish 이후를 가정해 horizon을 줄이지 않았다.

certificate945개 안전,1096개 FORCE_PEAK·3개 CLIP_HISTORY·534개 REFERENCE·101개 FOOTPRINT 거절이었다. 이는 원 정책의 내부 유한 탐색 결과다. 적용662raw는 실패 없이 official 확인에서 종료했다. 첫 strict/no-safe-action/domain/기술/IO/integrity/비용/기간 실패 중단 및 재시도 금지를 사전 동결했고,실패한 전체 실행을 replay하는 분기는 없다.

전체 안전 완주 뒤에만 같은 원래 source 초기 상태를 다시 읽어 기록된 float32 명령을 한 번 독립 재생했다. replay의 chooser는0이다. 전체662행의 before/after root·힘·양쪽 이력·full visited/tracker·clock·각 checkpoint SHA·official finish와 최종 checkpoint가 일치했다. 새 source 적분662틱으로 비용에 별도 계수했다. 최종 checkpoint SHA는 `22e98a041b424b7b4f1f01d5e442fe048a76b2a9e7ef9e1ba403dadb4ae0d542`다. 명령 재생의 결정론 검증이며 native solver 재현이나 pixel 정책 검증은 아니다.

|전체 적용 안전 집계|실측|원 기준|
|---|---:|---:|
|최소 footprint(m)|0.535227596|≥0.50|
|최대 path error(m)|1.606957310|≤3|
|최대 tracking force ratio|1.058989823|≤1.059|
|최대 launch force ratio|2.403901475|≤2.5|
|최대 tracking prefix clip|9.868421%|≤10%|
|검사 대상 launch prefix clip 최대|14.784946%|≤15%|
|tracking reference excess 최대(m/s)|4.849942507|≤4.85|
|forecast+적용 body 속도 최대(m/s)|97.003531970|<100|

path 여유가 커도 최소 footprint의 기준 위 여유는35.227596mm,tracking force 여유는약1.01769e−5,reference 여유는약5.74928e−5m/s다. 전체 환경/초기화 섭동에 대한 오차 bound는 얻지 않았다. 특히594/595가 보인 작은 물리 root 차이의 전파 때문에,source 통과와 exact tape replay만으로 native 전이를 인증할 수 없다.

비용과 감사

|계수|실제597|사전 전체 상한|
|---|---:|---:|
|model 시도 /완료|54,017 /52,918|각120,000|
|main 적용 /독립 replay|662 /662|각 최대1174|
|forecast 시도 /완료|52,693 /51,594|위 총량에 포함|
|외부 /내부 wheel force|216,068 /211,672|각480,000|
|force 합계|427,740|960,000|
|geometry 전체|155,713|400,000|
|main CPU /wall(초)|726.689160 /807.924529|1000 /1200|
|조건부 replay CPU /wall(초)|13.737896 /15.350674|60 /90|
|준비·검사·등록·분석·감사 CPU /wall(초)|63.260588 /62.657499|100 /150|
|전체 CPU /wall(초)|803.687643 /885.932702|1200 /1500|

model 시도−완료1099는 FORCE/CLIP의 tick 전 거절과 일치한다. prefix·거절 trial·새 FINAL·전체 재생까지 모두 새 계산으로 계수했다. geometry155713은 초기화4+forecast footprint54273+forecast projection51594+내부 nominal/steering projection47194+적용/replay footprint/projection2648이다. high-level query pack 기준이며 source 적분 내부 contact 계산 비용은 model tick에 포함한다. 원 kernel200000은 그대로이고 이 실험의 전역120000이 더 강한 상한이다.

각 main hold 전에 feedback 최대1540model/12320force/4526geometry(고정 prefix는4/32/8)와 **전체 조건부 replay1174model/9392force/2350geometry**를 선예약했다. main 시작에는1000CPU/1200wall+replay60/90+cleanup30/45를 예약했고,다음 hold45CPU/60wall와 replay/cleanup 여유도 매번 확인했다. 사전 읽기·순수 검사 등 보수적10초와 모든 import/hash/serialization/분석 측정을 포함한다. [읽기 감사](cold597_audit.json)의21.758143CPU/21.774971wall 및 보조3초도 합계에 추가했다. 문서·Git 대기를 물리 비용으로 주장하지 않는다.

읽기 감사25개가 모두 통과했다.275,033event hash chain,모든 입력·runtime/code pin,원summary·FINAL·prefix·full replay·원시 비용·TimeLimit·안전/이력·조건부 재생·미승격·보호 파일을 확인했다. 감사의 새 physics/force/geometry/native는0이다. [실측 결과](cold597_result.json)를 함께 보존했다.

native/world/reset/행동·새 seed/HOLDOUT/SEALED/carry·FD/solver·유료/다른 환경0이다. 연구 잔액22,548·reserve84,000/사용0,main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·기존 백업/사용자 변경을 유지한다. 원문·raw·좌표·전체 명령/상태/tracker/visited/journal은 지정 클라우드 Git 외부 비공개다. 공개는 기술 코드·hash·집계뿐이다. 승인 종료10월20일19:01:55KST를 유지하며 후속 자동 실행은 없다.

다음 검증의 가치와 한계

[미실행 후속 검토](cold597_next_review.json)에 하나의 cold native 진단만 제안했다. 고정577의594 인증 거절을 피할 새 feedback 정책이 전체 source를 거의 같은 시간(+20ms)에 안전 완주했고 source541 대비22raw 빠르므로,실제 native 초기/중간 상태를 읽어 다시 선택할 때도 게이트를 유지하는지 검증할 가치가 있다. fresh541 baseline 게이트 뒤 같은 승인 DEV case의 이 정책 한 개만 시험하고,실제 official integer raw가 baseline보다 작고 모든 native 안전 기준을 만족할 때만 native 이득을 인정하는 별도 계약이 필요하다. 아직 native 실행/등록/원장 차감은0이다.

계측·fsync를 포함한 main wall807.9초와127chooser는 실제 Agent.act의5초 제한 충족을 증명하지 않는다. full-state/map 기반 source/native 진단과 pixel 입력의 제출 가능 정책도 구분해야 한다. 현재는11초대 달성·다른 track/seed·carry·HOLDOUT/SEALED를 검증하지 않았으며,이 방향을 바로 더 깊게 최적화하거나 native 성공을 추정하지 않는다.
