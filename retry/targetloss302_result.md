# 302 — target-loss 한정 throttle veto의 코드·저장 기록 분석

**좁은 조건은 구조상 가능하고 저장 기록에도 존재한다.** 301의 T2954 활성13개는 모두 유효 target 구간이어서 좁은 조건은 이들을 제외한다. 다만 T2950의 성공을 만든 조건으로 입증되지 않았고, 원래296의 두 도로에는 좁은 조건이 각각3개씩 있어 성공/실패 분류기가 아니다. 실행 가능한 미검증 반증 가설로만 유지하며 새 native 주행은 하지 않았다.

**정확한 feature 의미와 실제296 코드:** feature0은 현재 `route_target`이 None이면1, target이 있으면0이다. 물리적 도로가 사라졌거나 충돌했다는 flag가 아니다. near는 routing 전에 별도로 계산한다. feature8은 safe lateral branch 사용 여부이며 현재296의24/8 공통 배수에서도 두 값이 달라 near와 일치한다. feature14/15는 affine head·global scale·301 guard 이전의 nominal gas/brake다.

```python
near = not getattr(self, "warming_fixed_reference", False) and any(
    y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius
    for x, y, radius in obstacles)
self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
target = route_target(path, speed, LOOKAHEAD_SCALE)
if target is None:
    nominal = self.controller.action(None, speed)
    x = forward = curvature = target_speed = 0.0
    feedback = speed
```

원래 fallback의 실제 반환은 다음과 같다. steering은 기존 memory를 유지하며 nominal gas=0, brake=0.25다.

```python
if far_x is None:
    return np.array([self.previous_steer, 0, 0.25], dtype=np.float32)
```

따라서 **target 없음 + near + nominal gas0**은 가능하고, target 없음에서 gas0 조건은 원래 fallback에 의해 자동 성립한다. target-loss의 goal0은 sentinel이며 물리적 정지 목표라는 뜻이 아니다. 유효 target에서 feature4는 template HUD feedback, target 없음에서는 legacy image speed(feature3)를 사용한다. feature12는 뒤쪽·ghost를 포함한 전체 tracked obstacle의 최소 hypot(없으면100)이며 GT 거리나 가장 가까운 전방 장애물 거리로 동일시하지 않는다.

| 기록 | broad near+nominal gas0 | 그중 유효 target | 좁은 target-loss 조건 | 첫 broad / 좁은 native |
|---|---:|---:|---:|---|
| 300 / T2950 | 49 | 46 | 3 | 69 / 184 |
| 301 / T2950 | 48 | 47 | 1 | 69 / 191 |
| 300 / T2954 | 63 | 60 | 3 | 21 / 82 |
| 301 / T2954 | 13 | 13 | 0 | 21 / 없음 |

301/T2950의 좁은 조건은native 191 한 번이고, T2954는 0번이다. 반면300의 원래296에서는 T2950의184/201/288, T2954의82/105/106에 관측됐다. 301에서 target 유무별 활성 범주를 구분한다는 제한된 사실은 확인되지만, 이 조건이 유해한 제어를 인과적으로 구분한다는 결론은 아니다.

**최초 활성 전후:** T2950은300/301 모두69에서 첫 broad 조건이 성립했다. 그 직전68까지 행동·legal feature·memory prefix는 정확히 같고,69의 legal feature도 일치한다. target은68~70 모두 있음(0), near는0→1→1, nominal gas/brake는0/0.5다. 301의 final gas는0.462→0→0, final brake는0.081→0.103→0.104, HUD는53.75→53.75→48.75m/s, steering은0.178→0.218→0.288rad, tracked 최소거리는19.99→16.65→12.89m였다. memory는 각 반환 steering과 float32 정밀도로 일치했다.

T2954의 첫 broad 활성은21이다. 직전20까지 같은 prefix였고21의 legal feature가 일치한다. target은20~22 모두 있음, near는0→1→1이다. nominal gas는0, nominal brake는0.278→0.5→0.5, 301 final gas는0.429→0→0, brake는0.068→0.071→0.090이다. HUD는48.75m/s, steering은−0.0246→−0.0296→−0.0951rad, 최소 tracked 거리는100→12.29→9.21m였다. memory 역시 실제 반환 steering을 따른다. 이 최초 활성 이후 두 정책의 state를 같은 native index로 맞추지 않았다.

**T2954의 접촉 전후와 해제:** 301의 79에서는 near=0, 80~85에서는 near=1·nominal gas=0이며 target은 계속 존재했다. 따라서 83의 첫 접촉을 포함한 이 구간은 좁은 veto에서 전부 제외된다. nominal brake는 80~83에서 0.5, 84/85에서 약 0.01866이며 final brake는 약 0.043~0.150이다. HUD는 48.75→46.25→43.75→38.75→6.25→6.25m/s, tracked 거리는 16.15→12.65→8.90→5.72→3.81→3.79m였다.

86에서 near는 1·target은 있지만 nominal gas가 0.1396으로 양수가 되어 301 guard가 해제됐다. final gas 0.4338·brake 0.1153·HUD 3.75m/s·steering 0.2411인 그 native 구간에 두 번째 접촉이 기록됐다. 이후 최종 gas가 양수인 채 off_track으로 종료했다. 이 순서가 해제의 인과 효과를 입증하지는 않으며, GT 위치/wheel 없이 충돌 후 정지 기하를 복원하지 않았다.

**저장 이미지와 공간 비교의 한계:** 300/301의 해당 디렉터리에는 관측 image/video/npz가 없다. 300의 pixel path와 GT geometry는 이미지가 아니며 301에는 GT pose/wheel도 없다. 이미지를 직접 확인했다거나 301 위치를 재생·복원했다고 주장하지 않는다. 모든 guard 시작/해제 및 접촉 전후의 feature 0/8·nominal/final pedal·HUD·steering·tracked 거리·memory window는 비공개 JSON에 정리했다. 공개는 간결한 사건 집계만 포함한다.

**다음 한 가지 반증 개입 — 미실행:** 정확한 296에서 `feature8==1 and feature14==0 and feature0==1`일 때 최종 gas만 0으로 한다. brake·steering·head·memory는 유지하며 latch·해제 지연·추가 계수는 없다. 301의 191행 상태를 가져다 쓰는 것이 아니라, 원래 296에서 처음 성립하는 T2950/184와 T2954/82부터 결과가 달라질 수 있는 새 고정 정책이다. 기존 296 기준을 재사용한 matched 두 도로에서 원래 prefix 일치·첫 발동·접촉·완주를 검증한다. T2950 회복이 사라지거나 T2954 완주를 잃으면 좁은 fix라는 주장을 기각한다.

236은 전역 gas/brake 크기 비교로 작은 채널을 제거했고, 246은 다른 244 정책의 추가 brake residual을 전역 240으로 되돌렸으며, 301은 target이 유효한 구간까지 폭넓게 gas를 잘랐다. 제안은 296의 target-loss fallback 구간에만 한 채널을 veto하므로 이들과 다르다. 구조상 불가능하거나 301의 두 범주가 관측상 완전히 같은 안은 아니어서 즉시 폐기하지 않았지만, 성공 효과를 보존한다는 근거도 없다. 별도 한정 반증 실험이 필요하다.

추가 native·환경 reset/step·정책/model·renderer 호출은 **0**이다. 저장 분석 wall 0.435초/CPU 0.438초를 측정했다. 누적 1,137,085 + 연구 잔여 8,915 + 최종 예비 84,000 = B 1,230,000을 유지한다. champion296·240 rollback·DEV 12개 봉인·HOLDOUT·SEALED·main·Participants·기존 백업과 사용자 변경을 보존했다. 일반 분석 코드와 집계만 공개하고 원시 window·identity·model parameter는 비공개로 보관했다.
