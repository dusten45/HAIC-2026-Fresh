# 271 — 최적 교사 경로와 240 제어기의 GT 호환성 진단

**2/2 무접촉·무손상 완주했지만, 두 도로 모두 240보다 느렸다.** 학습 전 정한 “두 도로 모두 완주하고 각각 시간 개선” 게이트를 통과하지 못했다. 270 pace 전이는 종료하며, 이번 출력의 단순 회귀 학습·pace clamp/gain 조정·추가 주행은 진행하지 않았다. 챔피언240을 유지한다.

| DEV | 기존240 | 이번271 | 240 대비 | 기존258 GT follower | 기존268 GT follower |
|---|---:|---:|---:|---:|---:|
| O0 |23.66초 |**25.16초** |+1.50초 |21.86초 |19.40초 |
| N0 |23.62초 |**24.82초** |+1.20초 |22.12초 |19.90초 |

모두 공식 완주 기록이다. 이번 O0는315행동·326/326 tiles, N0는311행동·325/325 tiles이며 damage0, collision0이다. 실제 DNF0, 예산 censor0, 기술 오류0이다. 각 도로를 한 번씩 실행했고 기존240·258·268 기록은 재사용했다.

## 하나의 경로 교체

258의 고정된 obstacle-feasible free 경로를 사용했다. 268도 같은 경로에 별도 속도 법칙을 적용했던 기록이다. 새 최적화나 중심선 재계산은 없으며, 해당 경로가 전역 최적해라는 보장은 없다. 저장소 검토에서 동일한 “258 free 경로 → 240 ordered path 입력” 대조는 찾지 못했다. 258/268은 전용 global follower, 260–262는 별도 국소 planner/controller를 사용했다.

이전 단순 GT 중심선 대체와 달리, 이번 경로는 장애물·차체 여유·곡률 제약을 포함해 전체 지도에서 최적화됐다. 또한 확인한183·184 기록 자체는 각각 검출된 장애물 중심·반경 보정과 GT ego-motion 전파였으므로, 이를 중심선 대체 결과로 인용하지 않는다.

현재 GT hull pose로 free 경로를 `(오른쪽, 전방)` 미터 좌표로 변환한다. 258의 고정 forward cursor/segment projection에서 시작해 도로 진행 순서로 첫 연속 국소 구간만 잘랐다. 범위는 기존 routing window의 pixel 열3–80·행24–56이며, 기존 변환 `x=(column−42)/1.3608`, `y=(63−row)/1.701`을 그대로 쓴다. 경로는 원래와 같은 `(0,0)` 시작점 뒤에 이어지고, 구간 내 arc 간격은 기존 세로1pixel에 해당하는 최대0.588m다. 좌표를 행별로 재정렬하거나 teacher 속도로 lookahead를 바꾸지 않았다.

이 구간은 현재 화면의 국소 범위에 있으나 가림별 raster ownership을 확인한 픽셀 관측은 아니다. **전체 지도 최적화의 GT foresight가 남는 진단**이며 적법 pixel 모델·제출 후보가 아니다. Actor에는 현재 pixels와 경로 점만 전달하며 GT 속도·목표 속도·도로ID·전역 cursor·speed profile을 보내지 않는다.

원본240 ZIP의 모든 파일은 바이트 그대로다. Actor에서 `nominal238_base.connected_route`가 반환하는 ordered path만 바꿨다. Pixel hazard tracker와 near 판정, 원래 lookahead6–14m, pure-pursuit steering·0.8/0.2 기억, cap45·횡가속24/8·P0.08/0.04, nominal pedal clip, 16개 feature 산식, frozen head, global scales와 최종 clip을 그대로 실행했다. 교사 목표 속도를 별도로 곱하지 않았다. 경로 길이·점 개수·목표점에 의존하는 feature 값은 새 경로에 따라 달라진다.

## 학습 전 검증과 경로 추종

기존 O0/N0 관측을 각각117개씩 순서대로 사용했다. 원래 pixel path를 실제 교체 입력 경계로 다시 전달했을 때 **234쌍의 action·feature·메모리와 cached240이 정확히 일치**했다. 기존 pre-action snapshot8개에서 좌표 역변환·pixel 단위·window bounds·순서와 sampling 간격을 확인했다. 새 physics 호출은 없었다.

실제626개 action도 원래 조향·nominal P·head·scales·clip으로 모두 정확히 재구성했다. 빈 경로 fallback은0회이며, sandbox의 모듈 hash·한 CPU/thread·금지 import/read 검사와 actor 회수를 확인했다.

다음 오차는 모두 **동일한258 free 경로에 대한 pre-action 위치 거리**, 같은 forward cursor/segment projection이다. 240 값도 기존 궤적에서 계산했다. 따라서 240의 자체 pixel 경로 추종 오차라는 뜻은 아니다.

| DEV·제어기 | 평균 / p95 / 최대 오차(m) |
|---|---:|
| O0·240 |2.401 /4.691 /7.738 |
| O0·271 |**0.801 /2.416 /4.524** |
| O0·258 |0.719 /1.740 /2.008 |
| O0·268 |0.731 /1.694 /2.097 |
| N0·240 |2.221 /4.527 /8.224 |
| N0·271 |**0.714 /1.728 /5.531** |
| N0·258 |0.622 /1.695 /2.259 |
| N0·268 |0.683 /1.724 /2.269 |

271은 교사 경로에 더 가깝게 주행했고 완주 호환성은 확인됐다. 그러나 큰 오차는 남았다. O0의 최대는226행동, N0는221행동이며 해당 nominal 목표 속도는15.74/17.30m/s였다. 두 도로의 목표 속도 중앙값은45m/s이고, 전용 GT follower 대비 시간 격차는258에서+3.30/+2.70초,268에서+5.76/+4.92초다.

이는 최적 경로를 국소 waypoints로 넣기만 하면240의 빠른 제어로 전이된다는 가설을 지지하지 않는다. 원래 pure-pursuit의 lookahead·corner cutting, 국소 구간과 origin 연결, cap/near 법칙, 새 경로 feature와 기존 pedal head의 호환성이 함께 남는다. 하나의 원인이나 경로 학습 자체의 불가능성을 입증한 실험은 아니다. 경로 거리 개선만으로 시간 개선이나 단순 teacher-output 회귀 학습을 정당화하지 않는다.

## 비용·보존

새 **626 native**, raw step2500틱·reset102틱이다. 실행 wall29.10초, evaluator CPU26.29초, actor CPU2.87초다. GT slice 계산 합계0.487초, actor 전체 act 중앙값1.60/1.63ms·최대8.48/13.30ms다. Offline preflight는472 actor 호출이며 별도 wall은 측정하지 않아 추정치를 넣지 않았다. 기존 두240 cache 수집의592 native는 과거 비용이고 이번 baseline materialization은0이다.

새 fit·label·geometry solve·model physics·유료 자원은 모두0이다. **B920000 = 누적832770 + 연구3230 + 예비84000(사용0)**. Champion·main·Participants·백업·HOLDOUT·SEALED는 유지했다. Pixels·pose·GT 경로·seed·실행 receipt는 비공개로 보존했다.

완주 결과의 retirement placeholder를 `null`로 고치는 출력 필드 수정을 했다. 실행한 source copy/hash와 원본 endpoint는 비공개로 남겼으며 정책·경로·행동을 변경하거나 주행을 반복하지 않았다.

[집계 결과](path271_result.json) · [국소 경로 변환](path271_geometry.py) · [고정·대조 검증](path271_prepare.py) · [GT actor](path271_worker.py) · [실행기](path271_run.py)
