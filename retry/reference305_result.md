# 305 — target 소실 시 한 프레임 참조의 관측 affine 변환

**실제 행동 변화는 있었지만 성능 게이트는 탈락했다.** 후보와 296 모두 1/2 완주이고 공통 완주 T2954 시간은 27.44초로 같다. 나머지 16 TRAIN·다른 변형·승격·DEV 개봉 없이 종료했다.

260은 live GT pose로 세계 좌표 계획을 유지했고, 261은 알려진 GT 선분의 방향을 기억하며 hull heading으로 새 선분을 정렬했다. 262는 GT로 뒤쪽 target을 판정해 계획을 무효화했고 두 도로가 무진행으로 종료됐다. 이번 후보는 그 계획·heading·속도 모델·장기 방향 기억을 사용하지 않는다. 현재 296의 tracker가 두 실제 영상에서 이미 계산하는 LK/LMEDS affine을 읽기 전용으로 노출한다. 유효한 transform이 없으면 움직임이나 heading을 추측하지 않고 기존 fallback을 유지한다. 과거 171의 tie 내 우회 방향 유지, 253의 road image fusion, 304의 wheel 기준 경로 순위 변경도 하지 않는다.

사전 가설은 새 route가 순간적으로 사라질 때 직전의 관측 참조를 현재 camera 좌표로 변환해 쓰면 stale steering 지속을 줄이고 완주 우선 성능을 개선한다는 것이었다. 변경 요소는 **빈 route의 참조 선택 한 가지**다. 상태는 직전 호출의 새 route·기존 accepted affine·호출별 복구 기록이다. 새 route가 있으면 정확한 296을 사용한다. 없을 때만 직전 새 route를 그 route의 pixel 원점 `(42,63)`과 축척으로 변환한다. Hazard 좌표의 원점과 혼동하지 않는다. 점 순서는 유지하고 전방·routing window 안의 첫 연속 구간을 현재 원래 allowed mask로 표본 검사하며, 원래 lookahead 이상 길이일 때만 사용한다. 잘못된 mask·짧은 참조·변환/기억 부재는 기존 fallback으로 돌아간다. 복구한 route는 새 기억으로 저장하지 않아 연속 소실에서 수명을 연장하지 않는다. 오래된 camera target의 좌표를 그대로 쓰거나 extrapolation하지 않는다.

이는 관측 영상 사이의 국소 변환이지 정확한 ego pose나 전역 트랙 정방향 추정이 아니다. Mask 표본 검사와 기존 origin connector는 연속 차체 footprint의 안전성을 보장하지 않는다. Controller·모델·계수·현재 route 순위·tracker 출력·perception threshold는 유지했다. 새 참조에 따른 feature·nominal·후속 관측 변화는 허용된 폐루프 효과다.

결과 전에 TRAIN T2950/T2954와 정확한 296의 300 저장 대조를 고정했다. 완주 수 증가 또는 동률에서 공통 완주 평균 시간의 엄격한 개선일 때만 원래 순서의 나머지 16 TRAIN을 실행하도록 등록했다. 전체 cap은 6,000 native이며 기술 오류·예산 검열·승인 종료는 확장을 막고 미상으로 남긴다. DEV·HOLDOUT·SEALED·예비·champion 승격은 사용하지 않는다.

| TRAIN | 저장 296 | 305 후보 | 복구 행동 |
|---|---|---|---|
| T2950 | off_track DNF, 315 native, damage 0.2 | off_track DNF, 311 native, damage 0.2 | 186·284 |
| T2954 | 27.44초 완주, 344 native, damage 0 | 전체 기록 동일 | 없음 |

T2950은 첫 변경 전 185개 행동·feature·memory·접촉/종료 기록이 같다. 첫 접촉은 184로, 첫 복구보다 먼저 발생했다. 따라서 이 실행을 첫 충돌 예방의 반증으로 해석하지 않는다. 복구는 두 번 실제 작동했으나 완주를 회복하지 못했다. T2950의 새 route 소실 24개 호출 중 accepted affine은 8개, 직전 새 참조는 3개에 있었다. 그중 2개가 복구되고 1개는 현재 mask/길이에서 거절됐다. T2954는 소실 3개 모두 accepted affine이 있었지만, 2개는 mask/길이·1개는 직전 참조 부재로 거절됐다. 이 한 프레임 규칙의 제한된 적용 범위를 드러내며, 장기 진행 방향 추정이나 모든 참조 복구 방법의 불가능성으로 확대하지 않는다. 새 GT·이미지는 수집하지 않았다.

패키지 비교에서 원래 296의 root를 그대로 보관했고 기존 member 변경은 tracker의 affine 복사 한 줄뿐이다. 좌표 translation·변환 부재·뒤쪽/범위 이탈·빈 기억을 native 없이 확인했다. 실제 655개 행동은 원래 nominal/controller 식과 memory를 검사했고, 기술 오류·검열은 0이며 프로세스가 회수됐다.

실제 비용은 **655/6,000 native**, raw step 2,617 / reset 102 tick, wall 17.483초다. Runner CPU 합계 25.528초·별도 actor CPU 5.467초, 병렬 episode wall 합계 32.431초다. 새 fit·parameter draw·source-model physics·유료 자원은 0이다. 종료 예산은 **누적 1,138,919 + 연구 잔여 7,081 + 최종 예비 84,000 = 1,230,000**이다. Main·Participants·사용자 변경·이전 결과·백업·296 champion·240 rollback과 모든 DEV 봉인을 보존했다. 공개에는 일반 코드와 집계만 포함하며 자동 후속 실험은 없다.
