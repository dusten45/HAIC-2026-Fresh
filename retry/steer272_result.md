# 272 — 조향 목표점 선택만 전용 follower 방식으로 교체

**2/2 무손상 완주했지만 조향 목표점 교체만으로 시간 개선이 전이되지 않았다.** O0는271과 동률, N0는0.04초 개선이며 두 도로 모두240보다 느리다. N0 p95 추종 오차도 늘었다. 사전 게이트를 통과하지 못해 해당 부분의 픽셀 전이 실험은 추천하지 않는다. 새 경로/pace 회귀·fit·parameter grid·후속 주행은 없다.

| DEV |240 |271 |이번272 |271 대비 |258 follower |268 follower |
|---|---:|---:|---:|---:|---:|---:|
| O0 |23.66초 |25.16초 |**25.16초** |0.00초 |21.86초 |19.40초 |
| N0 |23.62초 |24.82초 |**24.78초** |−0.04초 |22.12초 |19.90초 |

이번 O0는315행동·326/326 tiles, N0는310행동·325/325 tiles다. 모두 collision0·damage0이며 실제 DNF0·censor0·기술 오류0이다. 후보 하나를 도로별 한 번 실행했고 비교 기록8개는 모두 재사용했다.

## 실제 코드 차이와 선택

| 부분 |240 및271 |258/268 전용 follower |
|---|---|---|
| 조향식 |`atan(3.24×2x/(x²+y²))`, ±0.4 clip, 0.8새값+0.2이전값 |동일한 pure-pursuit 식·clip·기억 |
| 목표점 출발 |차체 원점, ordered path의 origin 연결 포함 |고정 free 경로의 최근접 segment 투영점 |
| lookahead |`clip(4+0.35×pixel_speed,6,14)`m |`clip(3.24+0.22×actual_speed,6,25)`m |
| 속도 |lookahead는 HUD pixel합 보정치, pedal feedback은 기존 HUD signature decode·fallback |GT hull velocity의 norm |
| yaw 상태 |원래240은 body-relative pixel 좌표;271에서는 GT pose로 path 변환 |GT hull angle로 목표점을 body frame에 변환 |
| 종방향 |pursuit 목표점 곡률로 cap45·횡가속24/8, P0.08/0.04, nominal clip0.5, frozen residual head·global scales |같은 free 경로의 curvature·ds로 만든 speed profile, 제곱속도 보간·공간 가속 feedforward+1.5속도오차, source model inverse pedals |

어느 쪽도 yaw-rate·wheel yaw·heading-error PID를 명시적으로 입력하지 않는다. 268은258과 같은 경로/조향/물리 역산 흐름에 고정된 조건별 speed multiplier를 사용한다. 그 속도 변경은 목표 속도뿐 아니라 공간 feedforward에도 반영된다. 따라서 빠른 follower를 단순 pace 또는 steering gain 하나로 설명할 수 없다.

조향식 자체가 같으므로 가장 직접적인 대조로 **목표점 선택기만** 교체했다. 같은258 free 경로에서 원래 follower의 투영점·arc 보간·실제 속도 lookahead를 그대로 사용한다. 이는 하나의 목표점 선택 구성요소 대조이며, 출발점·lookahead law·GT 속도의 개별 원인 효과를 따로 식별하지는 않는다.

271의 국소 ordered path, 원래 route_target과 그 곡률에서 계산하는 longitudinal 목표/P, feature/head/scales·clips는 유지했다. 기존 `action_target`을 한 번 호출한 뒤 nominal steering과 steering memory만 새 목표점으로 교체했다. `x/forward/curvature/target_speed` feature는 **기존271 longitudinal 목표점 기준**이고, nominal steering feature와 다음 행동의 previous-steer feature는 새 명령에 따라 변한다. 따라서 head 산식은 그대로지만 최종 pedals와 폐루프 궤적까지271과 같다는 주장은 하지 않는다.

GT velocity는 목표점 선택에만 쓰고 pedal feedback이나 teacher speed profile로 전달하지 않는다. 현재 actual speed에는 이미 적법 HUD proxy가 있지만 이번에는 GT를 사용해 selector 차이를 확인했다. 실제 주행에서 GT speed와 HUD feedback의 절대 차이 중앙값은0.64/0.65m/s, p95는1.20/1.19m/s였다. GT projection·path·pose는 적법 pixel 값으로 검증된 것이 아니다. 전체 지도 최적화의 foresight가 남는 **privileged 진단**이다. 이번625개 새 조향 목표점은 모두271의 국소 routing window 안에 있었으나 pixel occlusion 검증은 하지 않았다.

## 검증과 추종 결과

교체를 끈 저장 관측32쌍에서271 action·feature·memory가 정확히 재현됐다. 기존 snapshot8개에서258 arc 목표점 공식과 원래 nominal gas/brake 보존을 확인했다. 실제625개 행동에서도 기존271 longitudinal route_target·cap/P, frozen head/scales/clip과 새 조향식을 모두 정확히 재구성했다. 제어기 호출은 행동당1회이며 빈 경로 fallback0, steering 교체625회다. 원본240 archive의 모든 byte, loaded module hash, actor 경계와 회수를 확인했다.

| DEV·정책 |같은258 free 경로까지 평균 / p95 / 최대 거리(m) |
|---|---:|
| O0·240 |2.401 /4.691 /7.738 |
| O0·271 |0.801 /2.416 /4.524 |
| O0·272 |**0.793 /2.191 /4.725** |
| O0·258 /268 |0.719 /1.740 /2.008 · 0.731 /1.694 /2.097 |
| N0·240 |2.221 /4.527 /8.224 |
| N0·271 |0.714 /1.728 /5.531 |
| N0·272 |**0.697 /1.810 /5.766** |
| N0·258 /268 |0.622 /1.695 /2.259 · 0.683 /1.724 /2.269 |

거리는 동일한 pre-action projection 방식이다. 240의 자체 pixel 경로에 대한 오차는 아니다. 새 lookahead 중앙값은13.74/13.90m, 최대15.35/15.25m였고 기존 lookahead 중앙값은 모두14m였다. 최대 오차는 두 도로 모두 개선되지 않았다.

사전 게이트는 두 도로 모두 완주·271보다 빠름·damage 증가 없음·p95 오차 증가 없음이었다. O0는 시간 동률, N0는p95 악화로 각각 실패했다. 240 대비는+1.50/+1.16초다. 단일 주행의0.04초를 견고한 개선으로 확대 해석하지 않는다.

경로만 또는 pace만 전이한 과거 실패와 이번 결과는, 전용 follower의 조향 목표점 선택만 유지하면 빠른 제어가 전이된다는 근거를 제공하지 않는다. 특히 이번에는 종방향 곡률 목표를271에 고정했으므로 새 조향 목표점과 longitudinal 제한의 정합성을 함께 고친 실험은 아니다. 전용 follower의 path curvature·speed profile·feedforward·실제 속도 feedback 결합은 여전히 구분되지 않은 차이다. 이를 유일한 원인으로 확정하거나 controller 전체 교체·추가 회귀를 시작하지 않는다.

## 비용·마감

새 **625 native**, raw step2498틱·reset102틱이다. 평가 wall30.61초, evaluator CPU27.85초, actor CPU2.83초다. GT geometry/target 계산 합계0.585초, full Agent act 중앙값1.66/1.56ms·최대7.91/8.49ms다. Offline78 actor 호출·9.14초이며 새 physics0이다. 기준선 재주행·새 label/fit·geometry solve·model physics·유료 자원은 모두0이다.

**B920000 = 누적833395 + 연구2605 + 예비84000(사용0)**. 챔피언240·main·Participants·백업·HOLDOUT·SEALED를 보존했다. Raw pixels·pose·GT 경로·seeds·실행 receipt는 비공개로 남겼다. 이번 대조는 종료했고 픽셀 전이 후속은 추천하지 않는다.

[집계](steer272_result.json) · [목표점 선택](steer272_target.py) · [GT actor](steer272_worker.py) · [고정·대조 검증](steer272_prepare.py) · [실행기](steer272_run.py)
