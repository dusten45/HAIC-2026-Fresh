386 — 최종 개봉 전 정적 검토 결함 다섯 가지 수정

**다섯 결함을 수정했고 기존22개 검증·신규 회귀21개, 총43개 항목과 metadata preflight를 통과했다.** 385의 준비 완료 판정은 이 수정본으로 대체한다. 382·384 계약과296·240 artifact는 그대로이며, SEALED 개봉·관측·성능·지형 조회나 실제 backend 실행은 없다.

| 결함 | 수정 | 회귀 증거 |
|---|---|---|
|dependency map을 비우면 검사 생략 |384 binding의 distribution 이름 집합·버전·파일 수·canonical digest를 먼저 비교한다. 모든 map 검증이 끝난 뒤 설치 파일 resolver를 호출하고 실제 file hash를 검사한다. |빈 map·누락·버전 변경·동일 개수의 다른 경로 map을 resolver 접근 전 거부. 정상 map과 실제 설치 파일 변조도 확인. |
|마지막 cap step 확정 뒤 terminal 기록 전 중단 |batch_prepared의 per_case_cap과 연속된 확정 step1..cap을 사용해 max_steps DNF를 복구한다. 미확정 intent는 cap 완료로 간주하지 않고 finish_time_s가 있으면 완주를 우선한다. |terminal 없는 cap 확정은 DNF,동일 시점 finish는 완주,마지막 intent만 있는 경우는 검열·pending 유지. |
|act 도중 승인 마감 경과 후 step 시작 |act의 검사·반환 metadata를 기록한 뒤 step_intent 직전에 마감·원장 drift를 다시 검사한다. |synthetic act 안에서 시계를 만료시키면 env.step0·native 상한0. 기존 actor 응답·지연·호출 기록은 유지. |
|원장 drift 뒤 이전 prior로 전체 잔액 게시 |공유 비용 원장의 lock 안에서 baseline bytes와 prior budget hash·내용을 다시 검증한다. 이미 기록한 자신의 정확히 일치하는 FINAL385 줄만 제외해 멱등 검증한다. 불일치이면 독립 비용 영수증과 RECONCILIATION_REQUIRED만 남긴다. |동시 원장 추가·prior budget 변경에서 root/output 전체 잔액이 생성되지 않고 다른 줄도 보존됨. settlement가 query 허용을0으로 닫고 qualification을 실패 처리. |
|KeyboardInterrupt/SystemExit에서 정산·query 종료 생략 |run_live는 run_with_settlement의 finally에서 journal 기반 회계와 query 종료를 수행한다. run_batch도 두 예외의 중단 기록·cleanup·부분 summary를 남긴 뒤 원래 예외를 전파한다. 회계 실패 자체가 나도 query 종료를 시도한다. |두 예외 모두 claim1 유지·허용0·비용 receipt를 확인. KeyboardInterrupt의 native0와 SystemExit 도중 미해결 step1 점유를 구분하고 SystemExit code도 보존. |

의존성 digest는 384와 같은 canonical JSON(sort_keys=True,separators=(',',':'),ensure_ascii=False,UTF-8)으로 산출한다. 독립적인384 binding과 대조하므로 dependency file map 자체의 이름·버전·개수·digest를 함께 조작하는 방식으로 검증을 비울 수 없다. 이 hash 검사는 현재 파일과 소스에 대한 것이며 공식 서버·새 머신 인증으로 확대하지 않는다.

원장 정합성이 깨졌을 때의 `cost-independent.json`에는 이번 journal로 확인한 native와 미해결 상한만 있다. 이전 prior를 합산한 프로젝트 전체 잔액은 게시하지 않고,공유 원장에 FINAL385 줄도 추가하지 않는다. 별도 reconciliation receipt에는 기대·관측 원장/예산 hash와 조정 필요 상태를 남긴다. 알려진 step을 재실행하거나 미해결 비용을 임의로 확정하지 않는다. 동일한 정상 journal의 metadata 복구는 중복 차감 없이 동작한다.

catchable interruption과 강제 종료는 다르다. 한 번의 KeyboardInterrupt/SystemExit는 finally를 거쳐 정산·query 종료 후 전달하도록 구현하고 synthetic fixture로 검증했다. **SIGKILL·전원 종료는 finally를 실행하지 않는다.** 이 경우 이미 fsync된 정상 journal prefix와 marker·claim을 보존하고 별도의 metadata 복구가 필요하다. 반복 신호·정산 중 디스크/OS 실패도 즉시 정산을 막을 수 있다. 그런 경우에는 새 평가·reset·step으로 복구하지 않고 남은 prefix와 독립 receipt로 상태를 판단한다. 실제 전원/강제 종료 실험을 수행했다고 주장하지 않는다.

변경된 adapter SHA256은 `c4d7f0fad2bf2c4e6cc3d6dce4467afc27d0dcd06caeaff8cea56967f6024116`,revision386 준비 plan SHA256은 `9f9f8b35c6c732e4123c6fc49e60cacb73d4b6dd68b45023b2aa7fdd0c259e54`이다. 수정 전385 source는 비공개386 디렉터리에 보존했다. 기존385 계약·보고서도 덮어쓰지 않았다. 실행 진입점은 이제 **preparation_stage=386**만 허용하며,옛385 권한 template은 수정본을 활성화할 수 없다.

새386 template도 authorized=False·사용자 승인 참조 없음이다. 수정된 source·환경 core·현재 artifact/query snapshot·384 binding·budget·공유 원장 hash에 묶었다. metadata preflight는 이 비활성 template으로 읽기 전용 검사만 수행했다. Agent·numpy·OpenCV·Gym·Box2D·core module은 검증 프로세스에 로드되지 않았고 실제 live 진입점·조건 해석은 호출하지 않았다.

**현재 알려진 다섯 기술 결함은 해소했으며,추가로 확인된 기술적 차단 항목은 없다.** 실제 평가를 시작하려면 최종 개봉의 명시적 승인과 revision386의 정확한 권한·hash 연결이 필요하다. 이번 작업은 그 권한을 부여하거나 자동 활성화·예약하지 않는다. 같은 머신의 기존381 정상 actor 검증과 공식 서버·새 머신 미검증의 구분도 유지한다.

새 native/actor/reset/env/model/학습/source physics/관측/성능/지형 조회/유료 자원은 모두0이다. 누적1,312,121·연구35,943·예비84,000·예비 사용0,최종32,000/미배정52,000 제안을 유지했다. 등록된 두 synthetic subprocess wall은0.510초,metadata preflight는0.938초이며 개발·검토·게시 전체 시간이 아니다. 비용은v405·원장에 한 번 기록했다. 원문·개인 문서·seed·비공개 조건은 공개하지 않았고 연구 전체 종료나 일정 취소도 없다.

[수정 어댑터](final385_adapter.py) · [기존22개 검증](final385_dryrun.py) · [신규 회귀 fixture](final386_regression.py) · [revision386 준비 코드](final386_prepare.py) · [검증 집계](final386_result.json)
