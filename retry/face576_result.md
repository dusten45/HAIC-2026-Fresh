# 576 — 지정40좌표 active-face의 source0 종료

**지정한 한 면에서도 현재 양자화 tube는 모순이므로 source로 진행하지 않았다.**573의 점수660 raw/13.20초와 보간13.193602510361초를 유지한다. 고정 좌표를 바꾸거나 경험적 오차계수를 줄이지 않았다. 실제 source 안전 실패는 없으며, 결과는 저장된 보수적 모델의 제한된 분기에 관한 것이다.

## 단일 분기와 사전 게이트

574의 저장 FD·보정 및575의 재구성 행렬/수정된 causal rounding을 사용했다. 연구한 집합은575에서 inward box가 z=0을 제외한 **동일40좌표를 정확한 float32 seed 값으로 고정한 한 면**이며, 전체 feasible set 탐색이 아니다. 나머지224좌표만 자유다. 새 FD·보정·다른 endpoint 조합·오차계수 변경은 없다.

분류를 확인하니40개 모두가 물리 domain 끝점인 것은 아니었다. **33개는 정확한 끝점이고7개는 끝점 바로 안쪽의 인접 float32 값**이다.7개도 binade 경계에서 uniform q 및 작은 산술 여유 때문에 inward box가0을 제외했다. 최초의 “정확한 endpoint40개” 판정은 실제33개를 발견하고 LP0/source0에서 멈췄다. 이 실패와 원래 코드·계약·결과를 비공개로 보존하고 공개 집계를 `face576_classification_failure.json`에 남겼다. 이후 식별을575의 저장된40-mask와 정확히 일치시키도록 바로잡았다. 다른40개 조합을 선택한 것이 아니다.

첫 계산 전에 LP최대8회/각5 wall초, 전체 후보1개/662틱, 독립 replay1개/662틱, 합계1,324틱·CPU120초·wall180초를 정했다. 대수35 CPU초/50 wall초, strict·replay 각각30 CPU초/45 wall초다. 원 행·bounds·capsule1e-8과 exact clipping/rank 기준은 유지했다. 정확한 원 대수 검증 및 예측1µs 개선을 통과한 점만 초기 source 상태부터 전체 strict 평가하고, 새 안전 개선안만 독립 replay하도록 구현했다. 게이트를 통과하지 못해 이 두 단계는 실행하지 않았다.

## seed와 rounding 검증

고정40좌표의 실제 rounding 오차와 제어 이동은 정확히0이다. 자유224좌표 각각에서 interval 끝·내부·float32 인접값/tie를 포함한 **6,720개 scalar 검사**가 enclosure 안에 있었다. 최대 실제오차/q는0.999999970206이다.573의 analytic half-ULP+binary64 enclosure는 변경하지 않았다. 자유 inward 구간에는 모두0이 포함된다. seed는 원래23,965행·bounds·capsule·exact ratio 검증을 모두 통과하며, 기존처럼 tube와 별도 disjunct로 남는다. seed가 tube 자체의 원점에서도 feasible이라고 주장하지 않는다. 분기 식별·인접값·보통 interior·실패 count 단위검사 **4개 통과**다.

## 최종 저장 오류와 증거의 범위

분기 대수 계산은 정상 경로에서 새 점을 반환하지 않았다. 다만 최초 분류 결과 파일을 별도 보존한 뒤 기존 공개 결과 파일을 옮기지 않아, create-only 최종 writer가 `FileExistsError`로 끝났다. 이는 피할 수 있었던 결과 저장 실수다. source journal·후보·ERROR case는 생성되지 않았고 finally 비용은 저장됐다. 계산을 반복하지 않았다.

이 때문에 **세부 solver status와 정확한 호출 횟수는 복구할 수 없다.** status2나 실제1회를 추정해서 적지 않는다. 실행 코드의 hard loop/count 한계로 실제 LP는최대8회이며, closeout의 추가 LP는0회다. 이 기록 한계와 stdout을 보존했다. 아래 별도의 직접 모순 증거로 대수 기회가 없음을 확인했으며, solver status에 의존하지 않는다.

## 직접 모순: 자유 좌표에도 남는 rounding norm 하한

physical row2893(raw458, wheel2 force slack)의 제어 계수를a, causal norm 계수를L, 해당 prefix norm을t라 하자. 이 행에는 이후 제어의 Jacobian이 정확히0이다. 고정 좌표의 기여는0이고 자유 좌표의 tightened norm 행 및 인과 단조성은 `|z_j|+q_j <= t`를 요구한다. 따라서 다음 완화 하한이 성립한다.

`L*t+a*z >= (L-sum_free|a|)*max_free(q) + sum_free(|a|*q)`

여기서L=1,020.138151384, 자유 계수의 L1합=0.470894155220, 양의 차이=1,019.667257228이다. 자유 rounding에 따른 t하한은4.96705389119e-6이다. 이로부터 **좌변≥0.005064989441724**, tightened 우변은 **0.000114916783545**다. 엄격한 모순 차이 **0.004950072658179**가 보수적 산술오차 여유3.13129e-15보다 크다. 이 증명은 box·다른 물리 행·rank/capsule 제약을 추가로 사용하지 않는 완화 집합에서도 성립한다. 세부 계수 집계와 식은 `face576_algebra_certificate.json`에 있다.

즉,40좌표의 강제 이동은 제거됐지만, 자유 좌표의 uniform rounding tube가 양의 t를 요구하고 큰 경험적 L*t가 여전히 force 여유와 충돌한다. exact seed의 실제 rounding 오차0은 별도 seed 분기에서 유지된다. 이는 이 tube 구성의 보수성 증거이며 실제 궤적의 불가능성·강건성·전역 최적성 증거가 아니다. 새 양자화 후보와 예측 개선은 없고 seed의 예측 개선은0이다.

## 비용·종료·보존

전체 source/force/후보 strict/독립 replay/actual/Native/HOLDOUT/SEALED/새 FD/보정/유료 자원은 모두0이다. 누적 차감 CPU **9.498345/120초**, wall **9.484225/180초**다. 최초 분류 실패·검사·읽기 전용 진단을 포함하는 보수적7초와 후처리 probe/시작 비용1초, 마지막 직접 증명/해시 감사가 포함된다. 연구22,758·예비84,000·예비사용0을 유지한다.

실행 시 고정한 소스·입력 해시와 저장40-mask가 일치한다. 최초 실패·저장 오류·원시 명령/상태/행렬은 저장소 밖에 보존한다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·이전 실패를 유지하며 공개 기술 코드와 집계만 일반 commit/push한다.576은 이 분기에서 종료했으며 추가 solve·다른 면·새 source 연구로 전환하지 않았다.
