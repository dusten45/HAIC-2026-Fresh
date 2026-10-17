# 438 canonical 복구 통과 — 실제 첫 전이 ledger 정확 일치에서 중단

**snapshot 표현 복구는 정적·새 live adapter에서 통과했지만 실제 paired 완료 검증은 중단됐다.** C0의 새 reset·공통 prefix118·pre119 full state/memory/clock/RNG 일치를 확인했다. 첫 suffix nominal 실제 전이의 body/wheel/raw hull·clipping·memory 검사 뒤 `BoundaryStop: selected_first_actual_ledger_mismatch`가 발생했다. 첫 오류 규칙대로 **119행동/reset1**, P reset0, 추가 actual 재시도0으로 종료했다. 양쪽 완료가 없으므로 lap time·전체 실제 이득은 `null`이다.

기존 `plain()`은 dict key 문자열 변환, list/tuple 재귀, ndarray `.tolist()`, numpy scalar `.item()`을 지원한다. 그대로 쓰면 key 충돌이나 빈 ndarray의 뒤쪽 차원을 잃을 수 있어 변환 전 strict 지원 타입·문자열 key·유한 숫자를 검사했다. 객체/complex 배열 등 미지원 타입은 거부한다. 그 뒤 기존 `plain()`을 적용하고 태그가 있는 canonical 구조에서 scalar 타입/값·signed zero·필드·배열 차원을 정확히 비교한다. tuple/list나 같은 값을 보존하는 numpy 표현만 정규화하며 숫자 반올림·허용 오차는0이다. 빈 배열의 `(0,2)`와 `(0,3)`, bool/int/float, 필드 누락·순서·좌표·시각·tracker·RNG·memory 변조, 양쪽 NaN/Inf를 숨기지 않는다.

비공개 mismatch 기록은 양쪽 원본 pickle, 양쪽 normalized 구조와 필드별 diff를 저장하고 readback한다. pickle은 numpy dtype/shape와 NaN/Inf도 원형 보존하며 신뢰된 자체 기록에만 사용한다. actual adapter는 snapshot뿐 아니라 별도로 읽은 live memory/RNG와 complete_state의 memory/RNG도 비교한다. 모델 완료는 actual DONE 권한을 갖지 않으며 기존437 dispatch ticket·공식 tracker·actual ledger 채널을 유지했다.

정적 **144개 통과**, source/terminal/environment/Box2D world 생성0회다. 저장437 경계의 body/road/fixture/wheel/joint/metadata를 읽기 전용 Python stand-in으로 만들어 실제 `live_proxy → snapshot → source capture`와 `complete_state`를 호출했다. 물리 capture를 mock하지 않았고 solver/env를 만들지도 않았다. 생성자 `center/forward` tuple은 AST로 확인했고 저장 경계의 raw 비교는 이 두 표현에서 다르며 canonical 비교는 일치했다. 좌표·시각·필드·배열 길이/차원 변조는 거부됐다. 이는 저장 fixture 검증이며 **기존437 live proxy 원본이 없으므로 그 차이가 이것뿐이었다고 소급 단정하지 않는다**.

정적 복구 이력은 보존했다. 첫134개 실행은 stand-in의 `isSensor`/`sensor` 속성 연결 오류로 중단했고 fixture 속성만 수정했다. 두 번째137개 실행은 비유한 값 진단의 중복 `reason` keyword 오류로 중단했고 하위 사유를 `detail` 필드로 분리했다. 두 원계획·원소스·실패 로그를 보존했고 비교 acceptance·물리·임계값·예산은 바꾸지 않았다. 모델 시작 이후에는 코드를 고치지 않았다.

기존436/437 결과·source를 먼저 확인하고 선행 재현·복원·pending 게이트를 새로 통과했다. 저장423C0/427P 모델 replay 각각2회,12개 실제 state의 첫 전이 각각2회,425 pending 및435 저장 pending의 독립 모델 확인을 포함해 **1,137 ticks/35 worlds**였다. 기존 물리 오차 기준 이내이며 observer 결과는 archived unobserved433와 정확히 같았다. 저장 실제 physics와 bitwise exact라는 뜻은 아니다.

사전 worst-case는 그대로 **518,426 model ticks/883 worlds**다. planner64×3 recipes×(13+308)×4×독립2 =493,056, guardian116질의×2 recipes×13×4×독립2 =24,128, 선행 보수적1,242 ticks를 포함한다. actual 전이를 model parent로 중복 적분하지 않는다. model cap524,288 ticks/1,024 worlds/CPU1,800초/wall2,400초/순차 적분1, actual cap416 wrapper actions/reset2/독립 CPU180초/wall360초를 유지했다. C0 suffix80/P suffix100, P 적격 planner64 후·pending/FINISH_CONFIRM은 guardian만 허용하며 recipe·gain·H13/tail308·strict bracket·조향·경로·안전/진행 조건은 그대로다.

| 실제 관측 | C0 | P |
|---|---:|---:|
| reset / prefix / suffix |1 /118 /1|0 /0 /0|
| 상태 |첫 suffix 전이 후 ledger 정확 일치 중단|미시작|
| 공식 완료 / lap time |미확인 /null|미관측 /null|
| 손상 |0|미관측|
| 최대 post 경로 오차 |1.37915m|미관측|
| 전체 최대 force ratio |1.23199|미관측|
| suffix 최대 force ratio |0.60158|미관측|
| 전체 clipped wheel samples |38 /1,904|미관측|
| suffix clipping 불일치 |0|미관측|

새 live canonical 비교는1회 통과했고 두 nominal guardian 모델은13행동씩 독립 반복이 일치했다. suffix 첫 전이는 body 위치 오차 **7.629395×10⁻⁶m**, 속도 오차3.517393×10⁻⁶m/s, yaw 오차2.384186×10⁻⁷rad/s였으며 wheel/raw hull/phase/COM metadata도 기존 기준을 통과했다. memory before/after는 정확히 같았다. 실제 prefix118은 저장423과 정확히 같고 새 첫 suffix 실제 행도 사후423 기록과 정확히 같았다. 이 과거 비교는 종료 후 분석이며 선택 입력이 아니다. 새 높은 force 영역이나 P 명령 조합은 관측하지 않았다.

하지만 `progress_m`과 새 `goal_m`은 각각 **model−observed = −6.979243948990188×10⁻⁶m**였다. age·clock·deadline·DONE는 같고 양쪽 모두 같은 root goal을 넘었다. body 기준의 비영 오차를 통과해도 원래437의 추가 ledger 정확 일치 조건은 실패했다. 값을 반올림하거나 허용 오차를 완화하지 않았고 model 값으로 actual ledger를 대체하지도 않았다. 실제 전이는 진행됐지만 commit 전 검사에서 중단해 actual ledger는 pre119 값/done=false로 남았다. 실제 pending/DONE 경로는 관측되지 않았다.

중단 뒤 저장 root context/model first frame/actual native row와 변경 없는 ledger 함수를 이용해 양쪽 후보 ledger를 순수 재구성했다. 원본 frame·row·context·후보 ledger 두 개, canonical diff의 `/goal_m`·`/progress_m`를 비공개로 저장하고 readback했다. 후보 ledger는 모두 미commit이다. 추가 model/world/actual/reset은0이다.

**같은 차이는 저장된433·436 C0 qualification model과423 actual 첫 전이에도 이미 있었다.** 438 선행 replay에서도 같은 값이었다. reset 전에 exact ledger 조건을 이 fixture와 대조하지 못했다. 이번119행동은 새로운 물리 실패/성능 개선의 증거로 삼지 않는다. 다음 장애물은 기존 허용 오차가 있는 물리 충실도와 정확 ledger 조건의 충돌이다. 후속 정적 계약 검토에서는 실제 관측만 actual ledger를 갱신한다는 원칙과 예측 비교 조건을 분리해야 한다. 이번 실행에서는 조건 변경·추가 actual 시도를 하지 않았다.

실제 비용은 **119 wrapper actions/reset1**, prefix raw472+suffix raw4+reset raw51 = **527 raw ticks**다. actual exclusive CPU **11.835초**/wall **11.977초**다. 모델은 선행1,137+첫 질의104 = **1,241 ticks/37 worlds**, CPU **47.299초**/wall **51.254초**다. 미확인 호출/tick0, 최대 model world2개·동시 적분1개다. worker 전체 CPU 59.236초/wall 63.330초, region 밖 overhead CPU 0.102130초/wall 0.099380초도 기록했다. 정적 세 실행 합계 CPU 39.242초/wall 40.439초, 저장 분석 CPU 0.066초, ledger 진단 함수 CPU 0.020초, 과거 ledger 읽기 CPU 0.067초, 정리 검증 CPU 20.907초는 별도다. 준비·보고·Git·저장 분석 import 비용은 완전 계측하지 않았다.

v458 연구 잔여는 **28,326→28,207**, 누적 실제 **1,319,738→1,319,857**, reserve **84,000/사용0**이다. 437의118행동 비용과 실패를 그대로 유지했고 과거 비용을 다시 청구하지 않았다. 기존 기록 **14,537개**, 보호 archive·source·이전 보고서·main/Participants·백업·사용자 변경을 보존한다. 원문 지도/seed/state/RNG/명령/receipt는 비공개다. 새 actor·학습·HOLDOUT/SEALED·seed·reserve·유료 자원 사용은0이다.

438은 첫 오류로 종료했고 새 actual paired 재시도나 자동 후속 실험은 없다. 종료2026년10월20일19:01:55 KST 및 비자동 연장을 유지한다.

Plan SHA256: `a03c70f2a7a81fd503794d2bdfbd0e501869d27dec137fac848f5adaf2153eae`.

[기계 판독 결과](paired438_result.json) · [canonical 비교](canonical438.py) · [437 원실패](paired437_result.md).
