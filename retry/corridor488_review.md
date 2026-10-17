# 488 정적 독립 검토: lattice 표현과 구간 증명

현재 검토는 source와 수식만 읽었다. 저장 map의 grid 계산·sampling·탐색, 새 경로·후처리, profile·solver·최적화, seed·reset·world·step은 실행하지 않았다.

기존 SourceC는 B16 계수 자체를 주행 입력으로 소비하지 않는다. 최종 `line`, 그 선의 `free_profile.ds`, 길이가 한 개 더 긴 speed-node 배열, 질량 모델과 pace/reference를 소비한다. 따라서 lattice의 최종 polyline을 직접 표현하는 것은 가능하다. B16 계수를 가짜로 채우거나 기존 실패선의 ds·곡률·속도 노드를 복사해서는 안 된다. 이후 별도 승인 단계에서 같은 최종 선에 대한 reference를 만들어야 한다. 488의 현재 설계 검토는 profile 계산을 허용하지 않는다.

소비자의 추가 조건도 남는다. `canonical_projection`은 길이0인 segment와 서로 다른 비인접 투영의 정확한 동률을 거부한다. lap reference는 launch node0이0이고 이후 노드는 양수여야 한다. SourceC의 기존 point cursor는 현재 index 주변의 제한된 window를 사용한다. 따라서 원래의 obstacle·offset·3점 곡률 gate만 통과했다고 projection·cursor·tracking이 자격을 얻는 것은 아니다. 기하 입력 후보와 후속 source/실행 자격을 분리해야 한다.

## 구간 offset의 정확한 의미

station 중심을 `c_i`, source 단위 normal을 `n_i`, 선택한 signed offset을 `d_i`, 출력 점을 `P_i=c_i+d_i n_i`라고 하자. executor가 소비하는 선은 각 점을 직선으로 잇는다. 구간 내부 `0≤t≤1`에서 다음 식이 정확하다.

```
P(t) = (1-t) P_i + t P_{i+1}
C(t) = (1-t) c_i + t c_{i+1}
V(t) = P(t)-C(t) = (1-t)d_i n_i + t d_{i+1} n_{i+1}
||V(t)|| ≤ (1-t)|d_i| + t|d_{i+1}| ≤ B
```

단위 normal과 endpoint bound가 성립하면 normal이 회전해도 마지막 Euclidean displacement bound는 성립한다. 이는 corresponding center-segment interpolation과의 거리 bound다. 실제 road polygon 안에 차체가 들어간다는 증명은 아니다.

반면 `V(t)`를 보간한 scalar offset과 보간한 normal의 곱으로 대체하면 일반적으로 다른 곡선이 된다. `d_lin=(1-t)d_i+t d_{i+1}`, `n_lin=(1-t)n_i+t n_{i+1}`에 대해 차이는 다음과 같다.

```
V(t) - d_lin(t)n_lin(t)
    = t(1-t)(d_i-d_{i+1})(n_i-n_{i+1})
```

`n_lin`을 normalize해도 이 등식 차이는 사라지지 않는다. 반대 방향 normal에서는 `n_lin` 자체가0일 수도 있다. 따라서 scalar-normal 표현을 실제 출력 segment와 같다고 가정해서는 안 된다. certificate는 위의 실제 affine vector `V(t)`를 대상으로 해야 한다.

노드에서 `|d_i|≤B τ_i`라면 `||V(t)||≤B((1-t)τ_i+tτ_{i+1})`까지 증명할 수 있다. 다만 endpoint taper의 선형보간은 원래 smoothstep `τ(s)`의 구간 전체와 같지 않다. 기존 계약의 station taper와 constant bound를 유지하는지, 추가로 선형보간 taper bound를 인증하는지 명시해야 한다. smoothstep의 연속 bound를 새로 요구하려면 별도의 분석식 검증이 필요하다.

원래 도로 조건은 `40/6−1.4−0.35`의 normal-offset proxy다. 장애물에 쓰는 2.9m 원형 envelope를 도로에도 적용하거나 swept car/road-polygon containment를 새로 요구하면 조건을 바꾸는 것이다. 그 더 강한 물리 조건은 별도 계약 없이 기존 gate와 동일하다고 부를 수 없다.

## DP의 폐곡선 조건과 완전성 범위

root0을 원래 center0으로 고정하고 첫 successor `r`를 상태에 보존하면, 다음 조건이 모두 local predicate일 때 pair state `(r,a,b)`로 폐곡선 feasibility를 전달할 수 있다.

- 새 edge `b→c` 전체에 대한 기존 inflated-obstacle segment 검사를 한다.
- 새 triple `(a,b,c)`의 가운데 node 곡률을 검사한다.
- 마지막 edge의 closure와 마지막 node의 triple을 검사한다.
- 마지막으로 `(last,root0,first-r)`의 root 곡률을 검사한다.

양의 edge 길이도 소비자 schema에 필요하다. exact-bit dedup은 offset label만이 아니라 실제 생성된 최종 점의 bit identity에 적용해야 한다. 같은 상태가 합쳐질 때 tie/predecessor 순서를 고정하고, 탐색 실패·자원 중단·후속 자격 미달을 구분해야 한다.

기존 `free_feasible`는 각 곡률이 exact 한계 이하라는 조건과 같지 않다. clearance 최솟값 ≥−1e−6와 obstacle 제곱 위반·100배 곡률 제곱 위반·offset 위반의 **전체 합 ≤1e−8**을 사용한다. triple마다 곡률 residual0을 요구하고 edge마다 clearance≥0을 요구하는 DP는 이 계약보다 보수적인 하위 family다. 그렇게 설계할 수는 있지만 그 family의 완전 탐색만 주장해야 하며, 원래 residual 허용 family 전체의 실패로 확대하면 안 된다. 원래 aggregate 허용을 그대로 탐색하려면 누적 곡률 비용과 장애물별 전체 최소 clearance 등 충분한 상태/비용 정보를 보존해야 한다.

self-intersection·비인접 근접 투영 같은 nonlocal 소비자 제약도 pair state만으로 보존되지는 않는다. 합쳐진 상태의 한 prefix를 나중에 이 이유로 기각해도, 소실된 다른 prefix까지 모두 부적격이라는 뜻은 아니다. 따라서 기존 local DP의 완전성 범위를 넘는 추가 후검사는 별도 qualification으로 보고해야 한다.

## 출력과 후처리

가장 작은 계약은 선택된 lattice 점을 순서 그대로 출력하고 smoothing·shortcut·재샘플링을 하지 않는 것이다. 변경한다면 변경 전 certificate는 새 결과로 이전되지 않는다. 최종 출력 전체에 대해 좌표/hash, 양의 길이, 모든 원래 obstacle segment 거리, 원래 3점 곡률·aggregate residual, endpoint offset proxy, 시작/종료 seam과 위 연속 displacement 의미를 다시 인증해야 한다.

근거: `retry/racing258_plan.py`의 `geometry`, `basis`, `obstacle_clearance`, `curvature`, `profile`, `solve`; `retry/executor397.py`와 `retry/signed417_executor.py`의 profile/projection 계약; `retry/pace269_run.py`의 cursor·preview 식; `retry/terminal410_run.py`와 `retry/paired417_common.py`의 SourceC 입력 연결. 공개 문서에는 map 좌표나 identity를 포함하지 않았다.
