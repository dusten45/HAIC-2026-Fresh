# 동결 HUD 페달 후보의 fresh HOLDOUT (120)

113과 동결116을 새 HOLDOUT4조건에서 paired 비교했다. 기존 자격·정확 archive 재현 검증과 `frozen_paired_evaluation.py`를 재사용했고, 새 초기 관측·상태·road·obstacle identity를 paired 확인했다. 이전 HOLDOUT 상세와SEALED는 열지 않았으며, 실패 trace나 frame은 저장하지 않았다.

완주:113 2/4,116 3/4. 완주 상실 0, 신규 완주 1, 공통 완주 2, 공통DNF 1. 공통 완주 중앙 시간 차이(B−A): -1800.0ms, 평균 시간비: 0.9686505862830844.

사전 기준은 전체 cohort 유효성→완주 상실 여부→공통 완주 시간 순이다. 완주 상실이 없고 등록 시간 방향 기준을 통과하면 채택한다. Damage는 별도 경고이며0.6을 자동 탈락값으로 만들지 않았다. 이 batch의 총 damage(A/B): 1.200/1.800. 노출 시간·완주가 달라질 수 있는 기술 통계다.

판정: `COMPARISON_PASS_COMPLETION_GAIN`, 결정: `ADOPT_FROZEN116_LOCAL_CHAMPION`. 113 manifest와 ZIP 및 기존 rollback chain을 보존하고 로컬 챔피언을 동결116으로 갱신했다. 새 머신·공식 서버 동등성과 최종SEALED는 아직 확인하지 않았다.

현재 세션4CPU·16GiB, 최근 실측24.6~26.8행동/초, 승인잔여 약114.7시간을 확인한 후 B를16,000 증액해698,000/연구잔여22,288로 실행 전에 기록했다. 최악16,000행동은 약11분(native),25%계획여유 약13.6분이었다. 승인기간 연장이 아니다.

실제 계산 4,246native행동, wall 174.82초, evaluatorCPU 147.07초, actorCPU 27.95초. 추가 저장 정책 재생0회. 연구잔여 18,042, reserve84,000 사용0. 설정·seed·endpoint는 비공개120계획과결과에 보관하며 공개 파일에는집계만 남긴다.
