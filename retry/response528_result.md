# 528 — source 응답 pedal 결정: 국소 부족 감소, 전체 추가0.10초로 연구선 전환

**cold 모델은 안전 완주18.00초였지만525 실제 baseline18.40초 대비0.40초로 사전0.50초 승격 기준에 미달했다.**527 모델18.10초 대비 추가 개선은0.10초다. carry/native/action/reset0, 실제 기록18.40초 유지. 같은 제동량 미세조정을 반복하지 않고 다른 구조적 병목으로 전환할 근거를 남긴다.

[사전 계약](response528_contract.json) · [수치 제어기](response528_control.py) · [모델 실행](response528_model.py) · [모델 결과](response528_model_result.json) · [저장 감사](response528_audit.py) · [감사 결과](response528_audit.json).

## 한 후보와 안전한 수치 선택

527과 같은 backward80 참조·경로·조향·source forward·top80·가속 map·524 전파·12hold horizon·미래backup100 primitive를 사용했다. HIGH가 인증되지 않으면 현재 상태의 **첫 pedal만** 계산해 coarse backup의 불필요한 감속을 줄인다. force 여유0.19/예측1.06/물리1.25, clipping10% 누적 이력, 실제/전체 참조 초과5m/s, launch 구분은 유지했다.

signed pedal u>=0은gas, u<0은brake다. HIGH와 기존BACKUP 사이의 닫힌 구간에서 서로 배타적인 float32 명령을 만든다. 두 끝점이나 보간 명령이 안전하다고 가정하지 않고 **각 시험 명령을 현재 root에서12hold source 모델로 전파**한다. 고정9표본에 gas/coast/brake 경계0과, 구간 안에 있으면 source brake-lock0.9 직전/직후 float32를 추가한다. lock 이웃을 명시했지만 이번 실제 탐색 구간은0.9에 도달하지 않았다.

큰u→작은u 표본에서 safe 다음unsafe가 나오면 비단조로 표시하고 단조 이분 탐색을 건너뛴다. 그렇지 않으면 처음 unsafe/safe bracket에서 최대16회 float32 중간점 및 인접 float32를 검사한다. 이 표본 검사가 연속 구간 단조성의 증명은 아니다. 인증된 표본 중 첫 hold의 예측 progress가 가장 큰 명령을 선택하며 전역 최소 brake/최적성은 주장하지 않는다. 출력할 새 명령은 **캐시 없이 같은12hold를 다시 인증**한다. HIGH 정상 분기는 기존처럼 첫 전체 인증으로 바로 반환한다. 최대32certification/개입이며 값/horizon/gain 성능 sweep이 아니다. 아무 점도 인증되지 않으면 호출 전 중단한다.

수치 경계에 붙는 해의 작은 예측 오차를 피하려고 기존 native 속도 예측 허용오차0.15m/s를 내부 여유로 사용해 계획에서는 참조 초과<=4.85를 요구했다. 실제·전체 평가의5 기준을 느슨하게 하지 않았다. 이는 전체 position/solver 오차의 보편적 상한이 아니다. 기존527의203개 선택 인증은 모두4.6483 이하라 이 여유만으로 기존 저장 선택을 거절하지 않았다. 새명령의 탐색·검증용 여유이며 조정하지 않았다.

## 사전 선택 공유-root 반증

527 저장 own-model root75 경계, 가장 이른 별도 FORCE_PEAK BACKUP 중 종료 부족>=0.5인root38, 정상root70을 후보 결과 전에 고정했다. 기존 coarse 명령의4raw label은 재사용했고 새 정책은 현재 root/그때까지의 이력만 받았다. 새 첫 명령4raw 실행 안전과 두 개입의 부족 감소각>=0.10m/s·평균>=0.50m/s, 경계 부족50% 이상 감소, 정상HIGH bit 동일을 요구했다.

|공유 root|기존 종료 참조 부족|새 부족|감소|새 mode|
|---|---:|---:|---:|---|
|경계75|2.514989m/s|0|2.514989m/s|RESPONSE|
|별도force-trigger38|8.207199m/s|7.275443m/s|0.931756m/s|RESPONSE|
|정상70|0.385055m/s|동일|0|HIGH|

세 검사 모두 통과했다. root75의 예측 참조 초과4.849990/힘 peak0.080844, root38의 초과0/peak0.764883, 전체 차체·바퀴 여유각5.2575/4.1148m였다. 수치 인증 호출은28/27회로32 이내다. 정상 상태는 action을 바꾸지 않았다. 끝점이 안전하다는 보간 가정 대신 최종 source certification으로 안전을 확인했다.

## cold 전체 안전 통과, 효과 미달

525의 SHA 동일 모델 cold18.40/carry18.64를 재사용했고 새 후보 cold가 안전 source-style finish·0.50초 개선·HIGH>=50%일 때만 같은actual518 before47 root의 carry를 허용했다. native는 두 full model gate 후 한 쌍만 허용하도록 준비했으나 실행하지 않았다.

새 cold는900raw/225actions, source-style finish 추정 **18.00초**였다. 최소 sampled 전체 차체/바퀴 여유0.934400m, 최대 path1.702909m, 참조 초과3.583466m/s, running peak1.059999999<=1.06, clipped26/3216이었다. launch/source/projection/TimeLimit/finish 조건도 통과했다. HIGH186/RESPONSE12/BACKUP3, HIGH92.54%였다.

그러나525 대비 **0.40<0.50초**여서 carry0/native0으로 종료했다. 실제18.00초 기록으로 말하지 않는다.527 대비는 같은backward80·524 모델·미래backup100·경로에서 response 수치 선택을 바꾼 모델 비교로 **0.10초** 추가 이득이다. 내부0.15 여유도 명시적으로 포함된528 알고리즘 차이이며 별도 제거 ablation을 하지 않았다. 모든 차이를 이상적인 제동량 개선의 독립 인과 효과로 단정하지 않는다.

225개 float32 명령의 pedal 배타성·현재 상태 steering 불변과15개 수치 선택의 fresh 최종12hold 인증을 저장 자료로 확인했다. 최종 인증 호출수 최대28회였다. coarse 비단조 사례는 이번에0개였지만 전역 단조성의 증명으로 쓰지 않았다. 원527/526 실패와525 실제 baseline은 그대로다.

## 미세 제동 연구를 더 반복하지 않을 근거

국소 참조 부족은 크게 줄었는데 full cold 추가 효과는0.10초뿐이었다. 따라서 같은 제동 dose 수치 조정을 더 이어가지 않는다. 남은 모델18초의 배타적 reference 활성 분류는 launch1.92/source-forward8.48/backward80 3.58/top80 1.58/곡률·전이2.44초다. 이 표는 현재 궤적의 label이며 회수 가능한 손실이나 시간 이득 상한이 아니다.

현재 참조 경로995.445m를11.5초에 주행하려면 산술 평균86.56m/s가 필요하다. 이는 실제 COM 경로 길이나 공식 거리와 같다고 가정한 최적 하한이 아니지만, nominal top80·고정 출발·경로 길이를 유지한 채 미세 제동만 바꿔11초대로 가려는 접근의 구조적 한계를 보여 주는 비교다. 다음 연구선은 **속도 상한 또는 경로 길이/곡률**을 하나씩 검증하는 방향이다. 특히 source-forward 활성8.48초와 top80 활성1.58초의 차이도 함께 고려해야 하며 top80만 올리면 반드시 큰 효과가 난다고 단정하지 않는다. 이번에 새 cap/경로 후보는 실행하지 않았다. scalar reference clock17.250273초도 실현 가능한/최적 하한으로 사용하지 않았다.

## 비용·보존

새 모델 **20875ticks** = 공유-root 실행12 +cold900 +forecast19963. 적분 내 wheel force83500회, 별도 explicit force84740회. cache baseline body1668+planning18915ticks는 새 적분이 아니다. 저장 감사 추가 적분/force0.

worker CPU32.020802+0.257839=**32.278641초**, wall32.285165초. 준비/publication allowance3CPU/3wall는 별도다. source/input SHA를 확인했다. native/action/reset/world0, 연구 **24155**·예비 **84000/used0**, 실제18.40초 유지. 같은 지정 cloud/기존DEV/단일 작업, HOLDOUT/SEALED·새 seed·보호 평가·별도 유료 자원0. raw state·지도·pedal trials·명령·RNG·case는private, 코드/집계만 공개. main·Participants·사용자 변경·기존실패/백업 보존. 승인 종료 **2026-10-20 19:01:55 KST**다.
