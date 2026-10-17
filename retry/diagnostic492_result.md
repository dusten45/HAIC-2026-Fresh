# 492 — 첫 source raw 스키마 오류로 중단, 정책 판정 없음

**491 opt-in을 고정490 입력에 연결한 단 한 번의 진단은 native root와 두 witness 확보 뒤 첫 source raw 비교에서 중단됐다.** `KeyError: 'damage'`이며 source/warm gate는 미통과, H6·allocator 호출은0이다. 효과의 성공·기각으로 해석하지 않는다. 수정 후 재시도·대체 root·다른 조건·후속 실행은 하지 않았다.

## 승인·입력·선행 게이트

최신 명시적 연장 종료는2026-10-20 19:01:55 KST다. 이번492는 이미 노출된 첫485 DEV만 사용했다. 첫 case 객체가 끝나는 지점까지만 읽어 둘째 case의 내용은 읽지 않았다. 원래 identity digest·노출 이력을 보존했고 새 DEV 표본으로 세지 않는다. HOLDOUT/SEALED, 새 seed, geometry/profile/P4 재계산과 경로 tuning은0이다.

별도 `retry492` import graph에만491 canonical/CoherentExecutor를 연결했다. 원래397/417 globals·파일과 과거490 실패를 보존했다. 실제/source/history/candidate/selected/own의 가져온 canonical 별칭71개 모듈을 감사했고 입력 manifest·line·P4·491/runtime SHA를 고정했다. NumPy 배열은 RAM에서 Python list로 컨테이너만 바꾸고 float64 bytes를 재검증했다. legacy pace 대입 뒤 최종 P4 nodes를 다시 묶고 readonly로 유지했다. 실행하지 않은 경로의 별칭 검사는 그 경로의 동적 자격을 뜻하지 않는다.

물리 진입점을 poison한 무적분 gate7개가 통과했다: phase별 exact seam, actual/source의 LAUNCH·FIRST_LAP·FINISH_CONFIRM 명령/메모리/P4 일치, full snapshot·bytes codec roundtrip/변조 거부, 저장 전 oversize 거부, native4종 선차감 cap. 고정 owner/source/protected/budget 해시와 디스크 하한을 reset 전에 확인했다. 이 gate에는 native/model raw-post 스키마의 교차 검사가 빠져 있었다.

## 실제 진행과 중단 원인

같은 첫485 identity로 reset1회만 했다. 초기 도로·물리 장애물 해시와 **초기 관측 SHA가 저장485와 일치**했다. 자연 P4 prefix의 action72 뒤 최초 FIRST_LAP 1/4 root를 동결했다. root는 witness1 이전이며, 다음 두 자연 nominal hold를 action73·74로 관측했다. prefix의 안전·진행·phase 게이트가 통과했고 native 종료 뒤 body332→0·joint4→0을 확인했다. native 사실은 source-qualified root authority로 승격되지 않았다.

첫 cold source world는 원 root·메모리·RNG를 복원해 nominal 한 hold/4ticks를 실행했다. `ledger.compare_first` 다음의 `online481.raw_flags`에서 native post의 `damage` 키를 조회하다 중단됐다. 실제 native post의 키는 position/velocity/progress/time/tracker_after/collision/wheel_road_contacts이며, model comparator는 damage/collision/grass/wheel_road_contacts/phase를 요구한다. damage·grass·phase가 native post schema에 없다. row나 다른 관측에서 값을 추정해 채우거나 검사를 생략하지 않았다. 스키마 오류는 물리 불일치의 증거도, source 통과의 증거도 아니다.

첫 source 최종 snapshot/관측과 traceback을 저장하고 world를 닫았다. 두 번째 cold copy·실제 warm copy·root 전체 history authority·H6 두 정책 비교는 실행하지 않았다. ranking opportunity·root domination·margin 효과의 판정은 모두 없다. 기존 cursor·off-reference 연속성·engine/combined/rear force proxy 문제도 해결됐다고 주장하지 않는다.

## 비용·보존

| 항목 | 실제 | 등록 상한 |
|---|---:|---:|
| native actions / resets |74 / 1|129 / 1|
| native raw reset / action ticks |51 / 296|64 / 516|
| model worlds / charged ticks |1 / 4|113 / 536|
| model wrapper holds / allocator |1 / 0|134 / 26|
| worker CPU / wall |49.925785223s / 50.769790283s|900s / 1200s|
| native exclusive CPU / wall |44.541740458s / 45.106153319s|240s / 360s|
| model exclusive CPU / wall |1.219727998s / 1.223597564s|480s / 600s|

worker 비용은 import·source/input 등록·static gate·native·source·cleanup·전체 raw readback을 포함한다. 최대 RSS94,871,552B다. raw 저장량·파일 수는 결과 JSON의 최종 실측을 따른다. 각 charge는 dispatch 전에 append-only prefix journal와 새492 장부를 fsync했다. 실패분 환불은 없다. 연구 잔여26,175→26,101, reserve84,000/사용0이다. 기존485 장부는 변경하지 않았다.

전체 raw/codec 파일을 두 번 읽고 hash·스키마·decoded digest를 확인했다. native/model 모두 live0으로 종료했고 원본·보호·과거 기록3,223개 해시를 재확인했다. 지정 main·Participants·기존 backup은 보존했다. source/contract/code/요약만 연구 브랜치에 통상 commit/push하며 seed·좌표·전체 state·개인 문서는 비공개에 남긴다.

현재492는 **CLOSED_NO_RETRY**다. 다음 기술 과제는 무적분 raw schema 계약 검증이지만, 이 결과에서 소스를 고치거나 새 실험을 자동으로 시작하지 않는다.

[등록 계약](diagnostic492_contract.json) · [기계 판독 결과](diagnostic492_result.json) · [실행기](compare492.py)
