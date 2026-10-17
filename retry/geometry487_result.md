# 487 — feasibility-first 순위 변경 단독 충분성 기각

**정상 완료한 단 한 번의 반증에서 geometry gate를 통과하지 못했다.** 이 노출 DEV·B16·초기화·194회 예산에서 후보 순위만 바꾸는 것으로 충분하다는 가설을 기각한다. 다른 표현·solver·예산·조건으로 이어서 시도하지 않았다.

| 항목 | 실제 |
|---|---:|
| candidate solver / baseline 재최적화 |1 / 0|
| 목적평가 / 채택 coordinate 단계 |194 / 96|
| profile 호출 / 조건부 repair |195 / 0|
| 최종 최소 clearance |−0.067585978m|
| 최종 aggregate violation |0.006123175333|
| 새 actual/reset/world/tick/seed/P4/prefix |모두0|

원래 함수의 AST에서 scalar score만 정확한 `(violation, time+기존 roughness)`로 바꾸고 관측 callback을 추가했다. callback을 제거한 AST가 이 변경을 제외하고 원본과 동일함을 검증했다. B16·taper·offset bound·초기화·6pass·좌표/방향 순서·194회·거리/곡률/허용잔차·profile 소스는 그대로다. 원래 초기 계수 hash는 첫 목적평가 전에 일치 확인했다. 원래 baseline 함수 호출은 차단했다.

최종 계수·경로·free profile·clearance·위반 합·feasibility가 저장된485 baseline의 해당 값과 canonical hash까지 같다. 원래 scalar 목적값과 새 tuple 자체를 같은 척도로 비교하지 않는다. 원래 baseline의 중간 탐색 기록이 없으므로 두 전체 search 경로까지 같았다고 주장하지 않는다.

장애물 clearance 위반2개가 남았고 곡률·offset 위반 성분은0이다. 잔차가 기존 −0.001m 수치 repair 진입 범위 밖이라 repair를 호출하지 않았다. radius·buffer·tolerance를 늘리거나 줄이지 않았다. 이 결과는 물리적 경로 부재, 모든 B16 해의 부재, feasibility-first 일반 접근의 실패 또는 margin 정책 실패를 입증하지 않는다.

정적 검사16개가 통과했다. 독립 감사 구현은194개 전체 평가의 계수→기하·clearance·곡률·ds·목적 성분·path/profile hash와96개 strict tuple 채택을 확인했다. profile은 목적평가194회와 원래 center profile1회로195회이며, 감사에서 추가 profile·최적화를 호출하지 않았다. 원래 profile 소스와 저장 배열·시간·제약은 인증했지만 원래8pass의 독립 재실행 인증을 주장하지 않는다. 작은 부동소수점 제약 잔차는 진단값이며 새 gate로 쓰지 않았다.

최종 종료 stdout sample은 실측 CPU7.561677초/wall7.115251초, 별도 개발 보수 계상5/5초를 포함한12.561677/12.115251초다. 등록·source/input 검사·초기화·정적 검사·194평가·기록·독립 감사·전체 readback을 포함하고60/90초 상한 안이다. 보수 계상은 실측값이 아니다. 결과 JSON의 앞선 checkpoint는12.141698/11.695044초이며 이후 전체 readback·manifest 비용을 종료 sample과 구분했다.

새 raw는20파일/6,239,857B, 최대 파일616,790B다. 각 평가의 full profile까지 비공개로 남겼다. 전체 출력32파일/8MiB 안에서 코드·집계·출판 기록을 위해9파일/128KiB를 미리 분리했고 raw에는 더 작은23파일/(8MiB−128KiB)를 강제했다. 파일·temp2MiB, 종료2파일·64KiB 및 각 volume512MiB 여유도 생성 전에 검사했다. 기존 raw를 복사·삭제·변환하지 않았다. /tmp 단일 raw는 비영속이며 hash로 유실 내용을 복구할 수 없다.

첫485 조건은 이미 노출된 DEV로 유지하고 둘째 조건은 사용하지 않았다. 485의 실패·동결 이력·원본과 source pins를 보존했다. 연구 잔여26,175·예비84,000/사용0은 그대로다. 원시 좌표·조건 identity·seed·private 입력은 공개하지 않았다. 이 실행으로487을 종료하며 추가 실험은 없다.

[집계 결과](geometry487_result.json) · [등록 계약](geometry486_contract.json) · [실행기](trial487.py) · [독립 감사](audit487.py)
