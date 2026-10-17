# 496 — 저장 자료만으로 중복·기전 분리, 후속 실행 없음

**495의 2.29mm 효과는 승격 근거가 아니며, 추가 시뮬레이션은 실행하지 않았다.** 26개 질의는 완전한 인과 상태 기준으로 6개 context, 12개 후보 trace로 줄어든다. 이들은 같은 이미 노출된 DEV 조건의 연속 상태이며 독립 DEV 표본 6개가 아니다. HOLDOUT/SEALED 신규 접근0, reset/world/적분/새 seed/튜닝0이다.

## 중복 제거와 관측 경계

state·before/after nominal memory·ledger·RNG·nominal/qstar·wheel 상태·고정 입력 binding을 정확히 hash했다. arm/반복/label/할당 번호/파일 경로는 provenance로 제외했다. 중복 후보는 파일 경로와 SHA 참조만 제외한 모든 저장 측정값이 같은지 검사했다. 같은 state라도 memory/RNG/ledger가 다르면 합치지 않는다.

80ms guard는 각 preWorld 위치와 hold 반환 위치의 최대 경로 오차를 포함한다. 타이어 힘은 preforce, heading·속도·경로 오차는 지정한 pre/returned 경계에서 읽었다. 경로 왼쪽 법선의 signed error/normal velocity와 차체 오른쪽 lateral velocity를 구분했다. P4 기준 속도도 같은 canonical projection에서 계산했으며 새 profile을 풀지 않았다.

|context|중복 횟수|페달 대비 폭|후보 margin 범위 m|같은 상태 순위 이득 m|시작 상태가 모든 후보 margin 제한|
|---|---:|---:|---:|---:|---|
|C1|6|0.838553|0|0|예|
|C2|4|0.872887|0|0|예|
|C3|4|0.282497|0.009355|0|아니오|
|C4|4|0.278581|0.025555|0|아니오|
|C5|4|0.277928|0.056060|0|아니오|
|C6|4|0.274024|0.002293|0.002293|아니오|

6개 모두 nominal=qstar이고 eligible M80=max(0,force_ratio−1)=0이다. 실제 고유 후보는 각 context에서 nominal/qstar와 zero 두 개다. 순위 불일치는 **고유 상태1개(C6)**다. 495의 4회 불일치는 반복 측정이며 독립 증거4개가 아니다. 같은-state 후보 이득0.002293185m와495 각 arm의 실제 own trajectory 최소 margin 차이0.002293338m는 별도 통계량으로 보존했다.

## 저장 자료가 구별하는 설명

* **작은 명령 차이:** 지지하지 않는다. 페달 폭0.274–0.873이고 C6의 brake/zero 반환 속도도40.625/47.553m/s로 다르다. 조향은 기존 후보 사이에 고정되어 있다.
* **안전한 root의 margin 상한:** C1·C2에서는 시작 오차가 모든 후보의 guard 최대를 결정한다. 전체 H6의 작은 효과를 이것 하나로 설명할 수 없다. C3–C6에서는 상한이 지배하지 않는다.
* **현재 후보와 순위의 구별력:** 힘 초과값이 전부0이므로 기존 force 순위는 동률이고 active pedal tie-break가 작동한다. C3–C5에서는 brake가 zero보다 margin도 좋아 두 순위가 같은 후보를 고른다. C6의 zero만 약2.29mm 유리하다. 이 조건에서 margin-first ranking의 약한 효과는 관측됐지만, 다른 후보 집합·trigger·모든 ranking의 무효를 뜻하지 않는다.

495의 pre speed는 같은 위치 P4 기준보다1.89–5.22m/s 낮고, 모든 후보가 force clipping 없이 통과했다. 반면482의 후기 상태에서는 기준 속도 초과와 앞바퀴 횡력 요구가 커졌다. action122–125의 앞 최대 횡력436→684→1095→1236N은400N friction limit와 비교할 수 있으나, 서로 다른 tick/wheel의 최대 longitudinal force와 벡터 합을 만들어서는 안 된다. 끝 joint 오차 최대3.34e−5rad는 hold 종료 servo 추종 불량 설명을 약화한다. preview/평활화/속도의 인과관계는 아직 분리하지 못했다.

경로 normal velocity는 차체 횡미끄럼과 같지 않다. 예를 들어495 C6 nominal 반환의 두 값은−6.729/−0.687m/s다. 접선이 바뀌는 polyline에서 heading/normal 급변만으로 새로운 불안정 trigger를 정하면 안 된다. 482의 단순 threshold는 조기 회복 구간에서도 넘었으므로 경보 성능이 검증되지 않았다.

483의 +0.5525m는 사후 선택한 후기 위험 root, 495의 +0.00229m는 자연 quarter root다. map/line/prefix/state와 선정 절차가 달라, 이 차이를 조기 trigger의 효과나 일반화 증거로 쓸 수 없다.

## 두 가설과 하나의 후속 제안

H1은 **종방향 후보 집합/순위의 예방 효과**다. 저장 자료는 자연 quarter에서 현재 집합의 구별력이 작음을 보여준다. 현재 후보는 같은 활성 pedal을 줄이는 방향뿐이므로 더 강한 제동/반대 branch나 자연적 위험전 trigger의 효과는 미검증이다. 이를 동시에 추가하면 원인 분리가 되지 않는다.

H2는 **조향 명령 법칙의 횡응답 기여**다. servo 종료 추종은 양호하지만 preview/평활화 자체가 적절한지는 미검증이다. 최고 정보량 후속안은 이미 안전한495 C4 저장 root에서 평활화 한 연산만 제거하는 H6 비교다. C4는 저장된 조향 변화의 절댓값이 최대인 상태로 사후 선택했으며, 자연 trigger나 독립 DEV로 취급하지 않는다. 위험 후기483 root와 달리 현재495 capture/history 연결을 재사용할 수 있다는 장점이 있다. 어느 arm의 미래 H6 안전도 아직 보장하지 않는다.

[497 제안 계약](diagnostic497_proposal.json)은 **실행되지 않은 안**이다. 2arms×(독립 H6 cold2+held-first1), 최대6worlds/26holds/104ticks, native/reset/allocator0, 전체CPU180s/wall240s, private64MiB/512파일 상한을 제안했다. source/root/단일 코드 차이 gate가 먼저다. 별도 검증 world를 숨기지 않고 첫 counted control hold를 저장 trace와 비교한다. 온전한 기록과 cleanup도 상한에 포함한다.

성공 기준은 같은 시간에 progress +0.25m 이상, minimum margin 손실0.25m 이내, H6 안전 및 정확한 반복성이다. 단기 margin 이득만으로 승격하지 않는다. 더 일찍 unsafe가 되거나 margin 보상 없이 progress0.25m 이상 잃으면 이 개입의 국소 반증이다. 나머지는 NO_INFORMATION, gate/한도 실패는 TECHNICAL_STOP이다. 11초 목표는 이후 별도 사전등록 자연 DEV·실제 완주·미노출 HOLDOUT/SEALED를 통과해야 하며, 이 진단은 그 성과를 주장하지 않는다.

## 비용·재현·승인 종료

분석 worker CPU **9.013681초**, wall **9.003110초**, RSS **76,488,704B**. 이는 저장 자료 분석 비용이며 새 시뮬레이션 비용0이다. 기존495 model exclusive CPU183.48초 중 실제 step/trace8.22초와 큰 검증/기록 비용의 차이는 유지한다. ticks만 비례해서 다음 wall 비용을 보장하지 않는다. 연구 잔액 **26,027**, reserve **84,000/사용0**, 기존 최선 **13.640초**가 그대로다. 새 완주 결과는 없다.

이번에 전달된 명시적 승인 종료는 **2026-10-16 19:01:55 KST**다. 과거 산출물과 분석 v1에 있는10월20일 표기는 이번 지시의 연장 근거로 쓰지 않는다. 현재는 종료 후 정리만 하며 제안 실행·자동 연장은 없다. 분석 v1은 당시 SHA와 private에 보존했다. 공개 분석기는 의미 없는 assertion과 오래된 deadline check만 정리했고 수치 분석은 재실행하지 않았다.

원시 state/좌표/seed/명령열·입력별 SHA·실행 원본은 private에 보존한다. 공개 범위는 분석 코드·기술 집계·보고서·미실행 계약이다. main 지정 SHA와 기존 Participants·backup은 변경하지 않는다.

[분석 코드](analyze496.py) · [집계 JSON](diagnostic496_result.json) · [495 결과](diagnostic495_result.md) · [482 근거](diagnostic482_result.md) · [483 근거](diagnostic483_result.md)
