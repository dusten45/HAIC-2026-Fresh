# 573 — 제한된 float32 양자화 처리 검증

**구현 장벽 복구 성공.** 저장된572 LP에서 행별 float32 반올림 오차를 선반영한 첫 solve가 대수 게이트를 통과했다. 허용 잔차1e-8과 물리 안전 한도는 그대로다. 새 source 후보는 한 개만 실행했고 안전 완주했다. 보간 시간13.194600470168 → 13.193602510361초, 실제 개선 **0.997960ms**다. 점수 시간은660 raw / **13.20초**, confirmation661로 같아 공식 승격은 없다. Native13.66초는 별도이며 변경되지 않았다.

## 재사용 방법과 정확한 seed

`rounding573.py`의 `solve(problem)`은 임의 개수 제어의 원래 행렬 A·b, objective, float32 seed x0, scale, bounds, 선택적 finite-segment capsule을 받는다. 제어 구간의 최대 float32 half-ULP와 float64 표현 오차를 q로 감싸고, candidate LP에 행별 `abs(A_z) @ q`와 작은 이진64 연산 오차 한계를 선반영한다. 제어 box는 q만큼 안쪽으로 잡는다. norm 행도 함께 처리해 t가 반올림된 제어 이동의 infinity norm을 감싸게 한다. 반올림 뒤에는 **모든 원래 행·trust/domain bounds·capsule**을 원래1e-8 기준으로 다시 검사한다. alpha 재시도나 힘/도로 한도 완화는 없다.

정확한 zero-step seed `(z,t)=(0,0)`는 rounding tube와 **별도 disjunct**로 유지한다. seed 분기에는 고정 반올림 margin을 부과하지 않는다. 반환할 새 점이 없더라도 기존 seed가 사라졌다고 해석하지 않는다. 후보 tube가 infeasible해도 seed가 그대로 feasible인 경계 단위검사가 포함돼 있다. 이는 frozen algebra의 양자화 인증이며, 기존 경험적 L*t 모델을 보편적인 물리 오차 한계로 만드는 것은 아니다.

## 먼저 고정한 게이트와 검사

`quant573_contract.json`을 구현 실행 전에 등록했다. 실제 후보 최대1, replay 최대1, LP 최대8, 추가FD·보정주행·alpha sweep·source 복원0이다. 테스트10 CPU초, 대수15 CPU초, 후보10 CPU초/134틱, replay30 CPU초/662틱; 합계65 CPU초/110 wall초/796틱이다. seed와 테스트를 통과하고 예측 개선1µs 이상인 반올림 점만 source로 진행한다. 실제 strict 안전 완주·개선1µs 이상·candidate raw≤660인 새 후보만 독립 replay한다. 성공 여부와 무관하게 두 번째 source 제안은 없다.

경계·실패 주입 **7개 통과**: binade/음수/halfway tie/subnormal의 rounding enclosure, force·road·trust를 함께 검사하는 합성 행렬, robust 분기 불가능 시 exact seed 보존, 잘못된 rounder 주입 거부, 거짓 solver 주입 거부, nonfinite/nonexact seed 거부,1e-8 허용 경계 유지. 실행 명령과 코드 해시는 `quant573_tests.json`에 있다. 소스 적분 없는 검사다.

등록 파일 갱신에서 create-only atomic writer가 기존 파일을 거부한 선행 I/O 오류가 한 번 있었다. STARTED·LP·source 이전이며 모두0회였다. budget·수학·한도는 바꾸지 않고 등록 파일의 구현 해시를 원자적으로 갱신하도록 고쳤다. 원래 오류와 부분 파일은 비공개로 보존했고 `quant573_prestart_failure.json`에 집계를 남겼다. 테스트와 선행 시작 실패에는 합계2 CPU/wall초를 보수적으로 차감했다. 반복 실험이나 모델 파라미터 탐색은 하지 않았다.

## 실제 결과와 비용

- 저장572 precheck와 정확히 같은 원래 행렬을 추출했다. 당시 실패 잔차는 사후 재구성값이라는 한계를 유지한다. 원래 실패 테이프를 source로 재실행하지 않았다.
- LP **1회**, 대수 CPU0.468953초. 반올림 후 force·reference·road support·trust bounds·capsule 위반 **모두0**. seed exact feasible과 fallback이 유지됐다. 예측 개선0.996600ms, 실제 개선0.997960ms다.
- 변경 명령의 strict 검증133틱은 원래565 raw528 checkpoint 및 unchanged prefix certificate를 사용했다. 이후 새 안전 계획의 **독립 initial-source replay661틱**에서 원래 prefix528과 변경 tail 전부의 root·force·누적 history·finish tracker 및 최종 checkpoint가 정확히 일치했다.
- 전체 적분 **794틱 /796**, force **3176개 /3184**, geometry794회. 후보 CPU3.420751초, 독립 replay CPU16.770111초. 전체 예산 차감은 CPU **23.296428/65초**, wall **24.171060/110초**이며 테스트·선행 실패의 보수적2초를 포함한다. 읽기 전용 감사 CPU 합계0.921485초는 별도로 기록했다. 간접 의존 소스 해시와 단계별 상한도 확인했다.
- 전체 독립 테이프의 footprint 최소0.501688076346m, path 최대2.999942798380m, tracking force 최대1.058989978341, reference overspeed 최대4.849999404802, body 최대96.929065927455, tracking clip 비율 최대0.100000000000. launch의 별도 한계도 통과했고 모든 원래 실패 flag는 비어 있다. 작은 여유는 Native·섭동 강건성 인증이 아니다.
- 4,240개 로그 이벤트의 해시 체인, 소스·입력·검사 해시, tick·force 비용, 기존 상한이 모두 일치한다. 실제 행동·Native reset/world·새 seed·HOLDOUT·SEALED·유료 자원 사용0. 연구22,758 / 예비84,000 / 예비사용0을 유지했다.

source 후보와 독립 검증까지 끝내고 종료했다. 후반 미세조정 반복이나 더 넓은 궤적 연구는 시작하지 않았다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants·사용자 변경·백업·과거 실패는 보존했다. 공개 가능한 기술 코드와 집계만 일반 commit/push하며 원시 명령·상태·로그는 저장소 밖에 둔다. 승인 종료는2026-10-20 19:01:55 KST다.
