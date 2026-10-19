# 569: 유한 선분 벡터 제약과 실제 feedback 완주

568 저장 데이터만으로 설계를 먼저 검증했다. 11,256 raw에서 중심선 반대편 이동 53회, nearest segment 전환 32회, endpoint 투영 28회를 확인했다. 곡선 경로는 선분 capsule의 합집합이므로 하나의 무한 signed strip으로 대체할 수 없다. Signed lateral의 절대값은 선분 내부 투영일 때 거리와 같지만, endpoint에서는 종방향 잔차를 빠뜨렸다. 저장자료 설계 검사는 소스 실행 전에 통과했다. 실행 후 회귀용 기하 단위검사 5개도 통과했다. 저장자료 파싱 오류 1회는 소스 실행 전에 수정하고 비공개 기록으로 보존했다.

새 path 모델은 affine 위치 벡터에서 **고정된 유한 선분까지의 정확한 거리**를 계산한다. LP의 선분 support cut 뒤에도 capsule 거리를 직접 재검사한다. 고정 선분이 원래 progress window에서 eligible이면 이 거리는 원래 최소 경로거리의 상한이다. 실제 minimizing segment일 때만 동치이고, segment가 바뀌면 보수적일 수 있다. 고정 선분이 ineligible이면 그 함의를 주장하지 않는다. 후보의 실제 source projection, sign, active segment와 원래 path<=3 조건을 항상 재검사했다.

고정 양수 margin을 clip하지 않았다. 모든 tightening을 `L * 정규화 이동크기`로 정의해 정확한 float32 seed에서 0이 되게 했다. 위치 벡터 예측의 저장 보정 최대 오차는 약 0.02255m였다. 각 LP 전에 seed 포함과 유한 계수, path radius 3, force slack 1.059, body slack 100, reference slack 84.85, rank slack 1 및 모든 scalar의 유한 local-box attainable upper bound를 검사했다. 이 계수는 두 보정 방향에서 얻은 경험적 예산이며 전 방향 보증이 아니다. Footprint scalar의 큰 오차 계수도 잘라내지 않았다.

정확한 565 raw 528, launch55/384와 tracking64/1728을 재사용했다. 동일 seed와 제어·소스에서 이미 얻은 FD40열과 보정2회를 재사용해 중복 소스 계산을 피했다. 두 새 제안은 모두 모델, strict program, 기존537 feedback 완주를 통과했다. 새 소스의 strict 구간에서 active segment 전환 18회를 재검사했고, 고정 선분 ineligible과 path 실패는 없었다. 최소 footprint는 각각 0.56187m와 0.55375m, 최대 path distance는 1.34272m와 1.35828m였다. 힘·reference·정확한 clipping·body 전역 기준도 유지했다.

| 제안 | 모델 예측 gain | 실제 저장-tail gain | 실제 feedback gain | 공식 candidate/확인 raw |
|---|---:|---:|---:|---:|
| 1 | +5.191ms | +5.119ms | -5.820ms | 661 / 662 |
| 2 | +3.431ms | +3.399ms | -3.891ms | 661 / 662 |

같은 altered handoff에서 저장 tail과 다시 계산한 feedback을 비교하면 후자는 각각 10.939ms, 7.290ms 늦었다. 이후 14개 hold 모두 steering이 달라졌고 pedal은 각각 9개, 7개 달라졌다. 이 범위에서는 frozen-tail 시간 모델의 개선이 실제 feedback으로 전달되지 않았다. 두 비개선이라는 사전 중단 기준에서 끝냈다. 후보는 채택하지 않았고, 소스상 공식 incumbent는 raw661/13.22초 그대로다. 새 실제 주행 기록은 없다.

사용자의 최종 확인 요구에 따라, 채택하지 않은 새 안전 후보 중 더 나은 두 번째 후보를 예약된 verification 예산으로 독립 재생했다. 기존 seed의 whole replay는 반복하지 않았다. 새 후보의 전체 662 raw에서 상태·힘·누적 이력·tracker와 최종 checkpoint가 정확히 일치했다. 검증기는 정책 탐색을 재실행하지 않았다.

다른 내부 모델의 한계도 분리했다. 두 새 방향에서 위치 벡터 오차 예산은 지켜졌지만 scalar 예산은 force 최대 약 5.37e-6, footprint 약 6.67e-5m, reference 약 0.01943m/s 등 일부 작은 초과를 보였다. 이는 보정 두 방향이 전 방향 오차 보증이 아님을 보여준다. 실제 source 전역 기준은 모두 통과했고, 초과값을 margin 완화나 안전 판정 변경에 사용하지 않았다. 이번에는 568의 수학적 모순이 재발하지 않았으며, 다음 주제는 실제 feedback continuation의 값 예측과 방향별 오차 검증이다.

총 소스 비용은 독립 검증 662틱을 포함해 **11,605틱, 힘 평가47,792회, 기하 검사12,154회, CPU206.30초, wall221.01초**였다. 저장자료 설계는 소스0틱/CPU1.33초, 읽기 전용 분석도 소스0틱이다. 새 FD/보정 소스 실행은 0회, feedback은 2회였다. Native 행동·reset·보호 평가·새 seed·유료 자원·예비 사용은 모두0이며 연구22,758/예비84,000은 유지했다. 567·568·main·Participants를 보존했고 원시 상태와 원문은 공개 저장소에 올리지 않았다.
