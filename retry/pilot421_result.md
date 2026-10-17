# 421: 증거 저장 복구 뒤 모델 폐루프 비교 완료

같은 418 실제 fork에서 C0와 P가 각각 현재 모델 상태를 세 번 갱신한 뒤 같은 signed C nominal로 이어져 공식 finish에 도달했다. **P의 남은 시간 이득은 모델상 [0.62, 0.66]초**다. 실제 실행 게이트는 닫혀 있으며 실제 성능·안전·픽셀 정책 승격을 뜻하지 않는다. 추가 실행 없이 종료했다.

## 선행 게이트와 복구 범위

모델 시작 전 실제 크기의 전체 receipt 구조(220,515 bytes)를 사용한 정적 검사 12개를 통과했다. bytes 무손실 복원, canonical digest, parent/state/memory/RNG bytes, typed selector 재계산, 부모 불변, 기존 target 보존, 부분 write·publish 실패 정리, 기존 불완전 tmp 보존, 지원하지 않는 타입·비유한수의 파일 생성 전 거부를 확인했다. 실행 중 세 receipt(220,480/220,368/220,379 bytes)도 저장·복원 digest와 선택 재계산이 일치했다.

`receipt421_io.py`는 메모리 직렬화 후 임시 파일을 flush/fsync하고 비덮어쓰기 link로 게시한다. 실패 시 자체 임시 파일을 정리한다. 420의 원실행 코드·오류·불완전 tmp·부분 비용은 전체 파일 hash manifest로 보존했다. 잃어버린 420 실행 당시 global RNG token은 복구했다고 주장하지 않는다. 정적 fixture에 사용한 token은 별도로 재구성한 것이다.

419 selector, 세 recipe, gain 규칙, horizon, projection, signed C, 실제/예측 ledger는 유지했다. 시작 전 동결한 계획 SHA-256은 `4c5155a4f7c474fa5497f14bcb835d82bbff3384ee17da5565a4b663dbf5772c`다. 첫 기술 오류에 전체 중단, 미완료 tail 시간 추정 금지, 모델 최대 32,768 ticks/64 worlds/CPU 150초/wall 240초/순차 step 1개를 유지했다.

418의 저장된 실제 nominal/fullgas 각 13행동과 새 모델의 body·wheel·raw hull·phase 대조, 복원, 독립 반복, 현재 nominal 일치, 살아 있는 모델 부모·memory·RNG 비간섭 및 첫 전이 게이트를 통과했다. 최대 body 위치 오차는 nominal 1.38e-5m/fullgas 1.60e-5m, wheel omega 오차는 1.86e-5/4.24e-5rad/s 미만이었다. 이 자격은 해당 root의 A/B 13행동에 한정된다.

## 완료된 비교

| 지표 | C0 | P |
|---|---:|---:|
| 세 상태 기반 선택 | nominal ×3 | fullgas → nominal → fullgas |
| 공식 finish raw bracket, root 이후 | [281,282] | [249,250] |
| 남은 모델 시간 | 5.62–5.64초 | 4.98–5.00초 |
| 부모 모델 행동 / 세 선택 이후 continuation | 71 / 68 | 63 / 60 |
| 최대 post path error | 1.135m | 1.179m |
| 최대 force ratio | 1.1147 | 1.4073 |
| clipped wheel samples | 6/1132 | 44/1000 |
| damage / 진행 게이트 | 0 / 통과 | 0 / 통과 |

공식 finish event를 사용했으며, 뒤늦은 wrapper 확인 tick(C0 283/P 250)을 finish 시간으로 바꾸지 않았다. 세 질의는 갱신된 현재 모델 상태에서 수행했다. P 첫 질의의 fullgas witness 이득은 [0.58,0.62]초, 두 번째는 bracket이 겹쳐 nominal 유지, 세 번째는 [0.02,0.06]초다. 보장 이득 0.08초를 보편 기준으로 쓰지 않았다. 모든 9개 recipe pair는 첫 13행동과 같은 child의 nominal tail, 독립 반복을 완료했다.

420의 첫 질의 단일 witness [0.58,0.62]초와 이번 완료된 정책 비교 [0.62,0.66]초는 별개다. 420은 P 부모 행동 0개에서 중단됐으며 그 판정을 변경하지 않는다.

## 비용과 한계

| 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| root 실제13 대조 | 104 | 104 |
| C0 guardian | 156 | 156 |
| P recipe initial13 | 468 | 468 |
| P 같은 child tail | 1825 | 1825 |

여기에 qualification 부모 4, C0/P 세 번 전진 각 12, 최종 tail 271/238을 더해 **5,643 ticks/31 worlds**다. 예약·확정 tick은 같고 미확정 0, zero-time contact setup 31, 최대 동시 보유 world 7/실제 step 순차 1이다. whole worker CPU 17.030초, 실행 wall 16.377초로 상한 이내다. 전체 CPU에는 import·제어·hash·I/O·정리가 포함된다. tag별 CPU/wall은 constructor/step 구간만 측정했으므로 전체 비용으로 대체하지 않는다. 실행 wall에는 import 구간이 완전히 포함되지 않는다.

정적 preflight CPU/wall 0.096/0.100초, 저장 후 분석 0.049/0.049초다. 측정된 준비 wall 구간은 125.541초이나 초기 읽기·설계는 제외되고 준비 CPU와 보고·git 전체 비용은 완전 계측하지 않았다. 420의 2,387 ticks/19 worlds/CPU 7.150초/wall 6.475초는 별도 보존하며 이번 비용에 중복 계상하지 않는다.

새 실제 wrapper/reset/actor/학습/SEALED/예비 사용/유료 자원은 모두 0이다. 원장 v441은 연구 잔여 29,618, 최종 예비 84,000/사용 0, 실제 누적 1,318,446을 유지한다. DEV의 알려진 root 연구이며 HOLDOUT/SEALED를 열지 않았다. 원자료·map·seed·state·RNG·전체 receipt는 비공개 경로에만 보존했다.

P의 최대 force ratio 1.407은 418 실제 보정 범위 약 1.248을 넘는다. 새 상태·neutral·긴 tail의 실제 물리 일치와 미래 전체 guardian 정책은 자격을 얻지 않았다. nominal C tail은 해당 선택의 witness이며 이후 전체 guardian 정책을 인증하지 않는다. 특권 상태 prototype 결과로 픽셀 관측 성능·질의 실시간성·독립 일반화를 주장하지 않는다.

후속은 별도 승인과 사전 동결을 전제로 한 제한된 실제 C0/P 보정만 제안한다. 실제 현재 상태에서 선택을 재계산하고, 초기/fullfork/prefix·부모/RNG·복원/반복·첫 변경 전이와 대응 구간 body/wheel/raw hull·clipping·guardian·진행·비용 중단 게이트를 먼저 검사해야 한다. 짧은 실제13 보정만으로 모델 finish 이득 전체를 인증할 수 없다. 이번 결과로 실제 실행이나 자동 연장을 시작하지 않는다.

기계 판독 집계: [pilot421_result.json](pilot421_result.json). 이전 중단: [420](pilot420_result.md). 고정 선택 계약: [419](planner419_result.md). 실제 보정 범위: [418](calibrate418_result.md).
