# 491 endpoint identity 보정에 대한 독립 정적 검토

이 검토는 합의된 알고리즘과 수치적 의미에 한정한다. 지도 좌표 열람, 함수 import·호출, 테스트, 투영 평가, 경로 생성·변환, 프로파일 및 물리 실행은 하지 않았다. 원본 `signed417_executor.py`와 `executor397.py`는 보존한다. 새 projection491 및 명시적으로 선택하는 CoherentExecutor491만 사용하며, 기존 act 소스는 projection 전역 binding 교체 외에 동일하게 유지한다. 본 문서는 구현 검증이나 실행 승인이 아니다.

## 합의된 처리 순서

1. 입력 형상과 finite binary64 좌표를 검사한다. 서로 다른 vertex ID가 numeric equality로 같은 좌표를 가지면 입력을 거부한다. 이때 +0과 -0은 같은 수로 취급한다. 경로 중복 제거·정렬·좌표 변경으로 수리하지 않는다.
2. 각 directed edge에 대해 원본 차분·norm·`ds*ds` 분모·dot·clip 순서로 u와 foot을 계산한다. computed edge, ds, denominator, u, foot과 이후 제곱거리도 finite여야 한다. 양의 변 길이/분모를 잃는 underflow 또는 overflow는 unsupported domain으로 거부한다. 분모 floor, 재스케일, epsilon 보정은 하지 않는다. endpoint 보정에 해당하지 않는 interior의 원래 연산과 결과를 보존한다.
3. query 좌표가 해당 edge의 **own stored start 또는 end**와 정확한 numeric equality이면 그 endpoint의 원본 owner bytes를 foot에 사용하고 u를 0 또는 1로 설정한다. 따라서 정확한 stored query endpoint에서는 양쪽 incident edge가 같은 저장 꼭짓점으로 귀착한다. 이 override는 의도된 변경이며 모든 query에서 원본 투영 산술과 동일하다고 주장하지 않는다.
4. 그 후 foot이 해당 edge의 own stored start/end와 numeric equality인지 판정한다. u가 원래 interior였더라도 rounded foot이 own endpoint와 같다면 해당 vertex ID를 태그하고 owner bytes/u0·1로 정규화한다. own endpoint가 아닌 다른 stored vertex 좌표와 같다는 이유로 태그하지 않는다. 그 외에는 interior 태그를 유지한다. 이 분류는 unique-interior 조기 반환보다 먼저 한다.
5. 정규화된 feet로 원본 binary64 제곱거리를 다시 계산한다. 최소군은 원래처럼 정확한 거리 equality로 정한다. 유일한 interior 최소는 기존 결과를 유지한다. endpoint 최소군은 모든 태그가 같은 canonical vertex ID여야 하고, 최소군 edge ID 전부가 그 vertex의 incident 집합 `{v-1 mod N, v}` 안에 있어야 한다. interior 태그가 섞이거나 서로 다른 vertex ID/비인접 edge가 포함되면 거부한다. 전역 duplicate-vertex 거부와 이 tie 검사는 서로 대체하지 않는다.
6. endpoint의 선분 선택은 기존 phase 규약을 따른다. 일반 꼭짓점은 outgoing edge/u0, FIRST_LAP 또는 FINISH_CONFIRM의 node0은 incoming terminal edge/u1이다. 선택된 원본 edge로 tangent·sigma·arc를 계산한다. 새 near-tie tolerance, isclose, snapping, cursor fallback 또는 임의 tie-break는 추가하지 않는다.

## 의미와 한계

이 규약은 **binary64에서 표현된 endpoint identity**를 일관되게 다루는 수치적 연산자 보정이다. rounded interior foot이 저장 endpoint와 같을 때의 one-sided 선분 선택을 명시적으로 바꾼다. exact-rational 최근접점과의 동일성이나 모든 실수 좌표에서의 정확한 기하 투영을 증명하는 것은 아니다. 최소 tie 자체도 binary64 제곱거리 semantics를 유지하므로 rational distance tie와 일치한다고 주장하지 않는다.

정확한 query endpoint override와 own-foot endpoint 정규화는 비인접 분기 모호성을 허용하는 근거가 아니다. 다른 vertex ID, interior/endpoint 혼합 최소, 비인접 incident 관계는 계속 fail-closed이다. 비자교 polyline이라도 off-reference Voronoi 경계에서 최근접 arc가 바뀔 수 있으며 이 보정은 그 불연속을 제거하지 않는다. 꼭짓점의 tangent·sigma·feedforward gradient도 기존 one-sided 규약에 따라 바뀔 수 있다. near-endpoint 안정성, 전체 tube의 투영 연속성, steering·가감속 추종, warm/native fidelity 또는 안전 완주는 별도 검증 대상이다.

새 모듈의 source gate는 원본 보존, interior 산술의 동일성, act 전역 binding 이외의 소스 동일성, 명시적 opt-in을 확인해야 한다. 검증 전에는 알려진 490 seam 실패가 해결되었다거나 입력·주행이 승격되었다고 분류하지 않는다. 후속 시험과 비용은 별도 등록·승인 범위를 따른다.
