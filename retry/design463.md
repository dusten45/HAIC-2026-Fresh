# 463 — 고정 첫 명령 한 번의 native 이전

승인된 동일 DEV 비교를 한 번만 실행한다. 최신 승인 종료는 2026-10-20 19:01:55 KST다. 462는 모델 결과이며 이번 native lap과 혼합하지 않는다. 저장458P의 prefix125를 두 새 native reset에서 정확히 재현한 뒤 pre126에서 Original은 nominal, SecantOnce는 462와 같은 전체 float32 fullgas 명령을 한 번만 적용한다. 첫 명령은 독립2회·완전H13 고정 query를 통과해야 하며 fallback은 없다. 이후 각자의 현재 실제 관측에서 기존 guardian만 최대69회 적용한다. 전체 secant 제어·새 root·학습·다른 seed·HOLDOUT·SEALED는 열지 않는다.

단일 설정은 design463.json이다. 각 arm prefix125+suffix70=195, 합계390 wrapper 행동·reset2다. qualification을 포함한 계획 최대30370 model raw ticks/597worlds, hard32768/768, whole worker CPU1800초/wall2400초다. native exclusive CPU240/wall480 제한도 보존한다. 모델 부모는0이다. 1458ticks/41worlds qualification(기존 source1242/35+root216/6), 첫 고정query208/4, 나머지138 guardian query28704/552를 모두 포함한다. unused headroom은 추가 탐색 권한이 아니다.

선행 게이트는 constructor/step/native 금지 정적 suite와 저장 audit, source/current/pending qualification, 고정 root의 nominal factual H13 및 fullgas 모델 자기일관성이다. native actual GoalLedger와 모델 ForecastLedger 권위를 분리하고, source/clock/restore/geometry/phase/first-transition/fidelity/pending/own-native-finish 검사를 유지한다. 기존 label은463실행 권한을 대신하지 않는다. prefix 저장자료는 replay 대조에만 사용하고 새 실제 dispatch를 별도 차감한다.

중단: 첫 기술·안전·진행·권위·해시·시간·공간·IO 오류는 전역 중단한다. Original이 자기 공식 native finish를 완료해야 두 번째 arm을 연다. 195행동 내 미완료는 censor하고 추가 tail/재시도/수정 재실행하지 않는다. 승격: 두 arm이 자기 native 공식 finish와 모든 fidelity 검증을 통과할 때만 직접 lap 차이를 보고한다. 한 번의 같은 DEV 비교이므로 일반화·원인 식별·전체 secant 법칙 또는 배포 승격은 주장하지 않는다. 음수/overlap/개선없음도 그대로 보존한다.

저장: 기존 파일 삭제·이동·새 환경 없이 새 모델 raw는 기존 /tmp 볼륨, 새 native raw는 기존 workspace 볼륨에 직접 쓴다. 462에서 관측한83723.18010403121B/tick 이상, world고정768619B를 별도 가산,25% 경험적 여유와 종료512MiB를 포함한다. native는 관측최대1563574.582010582B/action·25%·512MiB다. 예측 약4.425GB/1.299GB이며 보증 상한은 아니다. 두 볼륨 각각512MiB 미만이면 새 constructor/step/native charge 전에 중단한다. 사후 archive는 실제 여유가 허용할 때만 새로 복사하고 원본을 보존한다.

회계: immutable v474의 연구26695/누적1321369/예비84000·사용0을 기준으로 새 wrapper 호출 전에 v475와 private fsync charge journal에 즉시 차감한다. reset은 별도 기록한다. 차감했으나 확인되지 않은 시도는 보수적으로 유지하고 환불하지 않는다. worker PID·단계·arm별 실제행동·modelticks/worlds·exclusive/whole시간을 checkpoint한다.10분 이상이면10분 상태를 보고한다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants, 사용자 변경, 기존 보호자료/백업을 보존한다. 공개에는 코드·집계·hash만 포함한다.
