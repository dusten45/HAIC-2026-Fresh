# 509 — wrapper 제동 adapter 순수 gate 통과, DEV reset identity 미확정

[Adapter](brake509_adapter.py)와 [7개 테스트](test_brake509.py)를 구현했고 모두 통과했다. 실제 world/action/reset/track seed 생성0이다. 검사 실행 wall0.114643s, unittest 보고 시간0.045s이며 CPU 실측값은 따로 기록하지 않았다. 연구26027·예비84000/used0 유지.

확인하고 반영한 연결 사항:

- source `CarRacing.step`은 `car.steer(-action[0])`를 호출한다. 후보 target에 이 부호를 반영하고, 실제 action의 nominal steering/gas float32 값은 그대로 둔다.
- body origin인 `hull.position`, hull COM, assembly COM을 구분한다. 속도/질량/lever arm은 현재 body들의 COM과 실제 mass에서 구성한다.
- 현재 road 계수에는 **현재 grip을 곱하고**, grass 하한도 `400*actual_grass*grip`으로 구성한다. source의 `max(grass,road)` 이후 grip 순서와 일치한다. 실제 reset의 track variables는 constructor grass 값을 덮어쓰므로 합성508의0.35를 고정 사용하지 않는다. 현재 source 기본 track grass는0.6이다.
- engine/steering multiplier를 현재 car에서 읽는다.32개 actual-source force/effect 조합×4휠과 fake body frame으로 확인했다. source `Car.gas/brake/step`만 AST로 추출해 실행했으며 Box2D constructor/적분은 호출하지 않았다.
- 실제 `CarEnvironment` 메서드를 fake raw env에서 호출해 reset의 초기1+warmup50, action의4rawcalls, collision damage 효과가4회가 끝난 뒤 적용되는 순서를 확인했다. 이는 **실제 native reset 실행**이 아니다. sensor phase는 source hash가 같은507 물리 검증을 재사용한다.
- reference를 한 번만 호출하고 그때 갱신된 memory를 adapter가 바꾸지 않는지 검사했다. float32 action 값이 wrapper의 float64 변환 뒤에도 보존됨을 확인했다. 가속/조향은 passthrough이며 exclusive braking만 바꾼다. 동시 gas+brake·비양수 forward target·지원되지 않는 frame skip은 명시 중단한다.

한 가설의 제동 요청 해석은 nominal brake를 기존 steady-torque/effective-mass 규약의 감속으로 읽어4tick 목표를 만드는 것이다. PixelAgent 내부 HUD 목표속도 자체와 같다는 인증이 아니다. 공개 `PixelAgent(adaptive=True)`를 새 짧은 진단용 동결 참조로 준비했고 합성 pixel 입력에서 단일 호출을 확인했다. 유실된 과거 champion116 archive를 재현한 것으로 표시하지 않는다.

## 실제 짝 비교를 실행하지 않은 구체적 이유

현재 공개 README의 seed는 설치 예시이며 DEV 등록을 보증하지 않는다. 공개 DEV 집계는 `DEV_index`/익명 condition 번호를 제공하지만 **정확한 `(track_id,seed)` 및 reset 설정의 연결**을 제공하지 않는다. `retry/evaluate.py`는 이 쌍을 private case에서 읽고, `retry/README.md`도 그 private plan 형식을 명시한다. 사용자 지칭 초기 DEV 조건의 정확한 쌍을 이번 접근 범위에서 확정하지 못했다. 숫자 label을 seed나 track_id로 바꾸어 추정하거나, geometry를 생성해 identity를 탐색하지 않았다.

base/wrapper 코드와 새 참조 코드는 이용 가능하므로 전체 연구를 유실 기록 복구에 묶지는 않는다. 이번에 막힌 것은 이 짧은 native trial의 **DEV case identity binding**뿐이다. unrelated raw/이전 연구 archive 복원은 adapter의 선행 조건으로 추가하지 않았다.

[사전 조건부 예약](brake509_contract.json)은2arms×32actions=64,2resets, action256rawticks+reset102rawticks=**358**이다. reset 중 재귀 reset·첫 source/effect/contact/prediction/safety 위반이면 해당 arm을 중단하고 시도한 실제 action만 call 전에 차감해야 한다. 완전 사용 시 잔액25963이며 이번에는 **64회 모두 미사용**이다. 실제 native 성능·속도/진행/여유 개선·기록·11초대 주장은 없다. [결과](brake509_result.json).

초기 넓은 파일명 검색에 보호 평가의 공개 집계가 포함되는 범위 오류가 있었다. 적어도 한 집계가 출력됐으며 파일 읽기 총수를 단정하지 않는다. 이를 case/참조/기준 선택에 사용하지 않았고 이후 명시DEV 근거로 범위를 제한했다. 새로운 보호 평가0이며, 이번 턴을 단순히 보호자료 조회0이라고 보고하지 않는다. 보호 case의 seed/identity를 조회해 DEV를 선택하지 않았다. 상세 보호 수치는 새 보고서에 옮기지 않는다.
