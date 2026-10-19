# 574 — 전 구간 264변수 모델의 선행 게이트 중단

**새 후보 없이 종료했다.** 독립 검증된573 계획에서 holds1–34를 고정하고 holds35–166의 steer·signed pedal 264개를 함께 다뤘다. 첫 중심의 새 FD264열과 보정2회를 완료했지만, tail-only와 확장 LP 모두 양자화 인증 분기에서 solver status2(infeasible)로 끝났다. 두 번째 중심·후보 source 평가·strict 평가·독립 replay는 실행하지 않았다. 기존573의 보간13.193602510361초와 점수660 raw / **13.20초**를 유지한다. Native13.66초는 별도이며 변경되지 않았다.

## 계약과 측정 경계

실행 전에 `wide574_contract.json`에 최대2중심·보정4회·진단/strict6쌍·안전 채택2회와 중단/승격 기준을 등록했다. 전체 한도는160,000틱, CPU4,800초, wall6,000초다. 예측·실제 개선1µs 이상, 원래 strict 안전 완주, 기존보다 늦지 않은 candidate raw를 모두 충족한 새 계획만 채택하고 전체 독립 replay한다. 점수 승격은 raw<660일 때만 허용한다. 양자화/무결성/도메인 문제를 우회하는 추가 실험이나 alpha sweep은 없다.

변경 전 상태는 raw136이며 tracking clipping 이력은[3,160], launch는[55,384]다. 목적과 실행 모두 고정 prefix 및 같은264개 명령으로 전체 완주를 계산한다. 변하지 않는 tail을 목적에 쓰고 실제로 새 feedback을 붙이는 불일치는 없다. FD·보정은 raw662까지의 진단 suffix526틱을 사용하며, 이는 안전 후보의 strict 평가와 구분한다.

저장된573의661행을 source 적분 없이 재구성해132개 pre-hold의 root·visited·tracker·clock·progress·누적 이력 및 최종 checkpoint를 확인했다. 이어 각 pre-hold에서 실제 source 다음1틱을 저장 행과 비교해132개 모두 정확히 일치했다. clock을 raw*.02로 재계산하지 않고 누적 이진64 값을 보존했다. 각 FD 열은 자신의 pre-hold에서 시작하며, 영향을 받지 않는 prefix의 g·force·order·위치·vertex 미분이 모두 정확히0인지 검사했다.

## 새 모델과 검사

중심당 FD 비용은 `sum(h=35..166) 2*(662-4*(h-1)) = 69,696틱`이며 실제도 정확히 일치했다. 공통 raw136부터 모든 열을 재적분하는138,864틱 대비 절반이다. 앞 구간의 민감도와 반대 방향 보정2회를 새로 측정했다. 과거 tail의 경험적 오차계수를 전체 구간의 보편 한계로 재사용하지 않았다.

오차항에는 각 raw까지의 실제 제어 prefix 이동 norm을 사용했다. 132개 causal norm 보조변수를 포함한396변수·23,965행 모델에서 finite-segment capsule, 각 활성 도로/장애물 component의 모든 vertex signed support, 물리 한도 및 clipping의 직접 nonexempt force branch를 함께 검사했다. 경험적 오차모델은 측정한 국소 자료에 근거한 것이며 전역 물리 인증은 아니다.

573의 float32 enclosure와 행별 `abs(A_control) @ q`, inward bounds, 정확한 zero-step seed의 별도 분기를 확장했다. 반올림된 원래 제약·bounds·capsule은1e-8을 유지하고, 예측 clipping은 정확한 `ratio>1`과 prefix count로 추가 확인한다. 경계/실패 주입 단위검사 **9개 통과**: causal norm, FD 비용, clock/clone 독립성, clipping/rank branch, joint rounding, 거짓 solver/rounder 거부, zero-causal 오차 무결성 및 실제396열 seed 행렬이다. 검사·설계의 source 적분은0이며 보수적 CPU/wall5초를 전체 비용에 포함했다.

## 결과와 한계

동일한 새 Jacobian·오차모델에서 holds133–166만 허용한 tail LP와 전체264변수를 허용한 LP를 각각1회 풀었다. 둘 다 `CERTIFIED_BRANCH_LP_FAILED`, status2였다. 정확한 seed는 두 경우 모두 feasible이며 fallback으로 보존됐다. 반환된 새 양자화 점과 실제 후보 개선량은 없다. 이 결과는 해당 보수적 인증 분기의 실패이며, 원래 설계 공간의 개선 불가능성이나 전역 최적성 증거가 아니다. 별도 infeasibility/dual certificate를 얻지 않았으므로 원인을 특정 제약 하나로 단정하지 않는다.

읽기 전용 검토에서 source 안전 판정을 바꾸는 오류는 발견되지 않았다. 다만 tail-only LP는 선행 aux를0으로 고정한 뒤에도 numerical margin 산정에 원래 aux bounds가 남아 일부 zero norm 행에 약1e-15의 모순이 생길 수 있다. solver 허용오차와 최종 원 제약 검사는 구분해야 한다. 따라서 tail 결과를 엄밀한 feasible-set 인증으로 해석하지 않는다. 확장 LP에도 별도로 status2가 기록됐다. 실행 중 구현을 수정하거나 이를 복구하는 추가 solve/source를 시작하지 않았다.

## 비용과 보존

총 **70,881틱**, force283,524개, geometry/body 각70,881회다. 구성은 seed 연장1 + checkpoint 증명132 + FD69,696 + 보정1,052틱이다. 후보·strict·독립 replay는0틱이다. 전체 CPU **2,055.453200초**, wall **2,196.102722초**로 모든 단계별·전체 한도 안이다. runner의 journal 감사 CPU19.583702초/wall19.586753초도 포함했고, 감사 전 원장은 `finally_first_total`로 보존했다. source 없는 후처리 감사는 CPU0.007094초로 별도 기록했다.

425,953개 journal 이벤트의 해시 체인, tick/force 수, source/input/test/design 해시와 사전 비용 산술이 일치한다. 실제 행동·Native reset/world·새 seed·HOLDOUT·SEALED·유료 자원은 모두0이다. 연구22,758 / 예비84,000 / 예비사용0을 유지했다. 원시 명령·상태·FD·보정·journal은 저장소 밖 비공개 경로에 보존하고 공개 가능한 코드와 집계만 commit/push한다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·과거 실패는 보존했다.

574는 등록한 선행 게이트에서 끝났다. 후속 판단에는 저장된 모델의 보수성·양자화 분기를 먼저 구분해야 하며, 이번 실행에서 새 source 연구나 반복 복구는 시작하지 않았다.
