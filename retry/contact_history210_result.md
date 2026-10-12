210 — F2 손상 과소예측과 fallback 접촉 오탐 분리

**손상 공식이나 명령·4틱 범위 차이가 아니라, 복제 세계의 접촉 시작/종료 이력 복원 누락이었다.** 최초 오류 직전pre85를 고정하고 저장 F2명령223행동 prefix를 한 번 재생했다. pre85/pre223 상태와 실제 raw 접촉 이벤트를 같은 실행에서 기록했다. 추가 전체lap·후보 평가·재생은 없다.

85~87은 pre85에서 예측한 같은 N 명령3개였고 각각4틱이다. 초기damage0.2는 같았다. 실제는0.4→0.6→0.6, 기존 모델은0.2→0.4→0.4였다. 실제85의1틱에서 기존 차륜-장애물 접촉이 끝나 hit를false로 지웠다. 복제 세계의 현재 기하에는 그 기존 접촉이 없어 EndContact가 빠졌고 hitTrue가 남았다.4틱의 새 차륜 접촉 Begin은 양쪽에 있었지만 모델은 새 손상 충돌로 세지 않았다.86의 다음 End/Begin은 양쪽에 발생했고87은 새 충돌이 없으므로 누락된0.2가 이어졌다. 이후pre88 재계획은 실제damage를 다시 읽었다.

기존 selected 비교의 `predicted_collision`은 raw collision과 접촉 ID의 OR였다.85는 모델도 접촉 ID가 있어 이 합친 지표가 일치했지만 damage 갱신 플래그는 달랐다. 이번 검증은 **raw collision·접촉 ID·damage를 따로** 비교했다.

fallback223은 초기damage0.8, 같은 실제 anchor 명령1개·4틱·물리 terminal 예측이었다. 실제 유지 중인 hull 접촉은 새 Begin이 없었다. 복제 모델은 zero-time 초기 구축의 Begin을 다시 기록해 접촉 ID를 만들었다. hitTrue라 손상은 늘지 않았으므로 손상 과소예측과 다른 오류다.

최소 수정은 `capture`에 실제 touching 장애물-차체 fixture쌍을 저장하고, 첫 양의 시간 collision phase에서 새 기하에 없는 기존쌍의 End bookkeeping을 복원하며 이미 유지 중인 쌍의 초기 Begin 재기록을 억제하는 것이다. hit를 모든contact에 적용하거나 damage를 임의 보정하지 않았다. 공식 환경·CollisionDamage·물리 파라미터·순위·horizon·tolerance는 변경하지 않았다. 옛 snapshot에 이력이 없으면 기존 동작을 유지한다.

| 동일 실제 명령 검증 | 수정 후 |
|---|---|
| 85~87 damage | 실제와 같은0.4→0.6→0.6 |
| 223 접촉 ID/충돌 | 실제와 같은 없음/false |
| raw collision·접촉 ID·damage·타일·물리 terminal 불일치 | 각0건 |
| 최대 위치오차 | 두 경계 모두0m |
| 최대 속도오차 | 85:1.83e−6m/s,223:1.33e−7m/s |

85~87의 물리 terminal은 여전히false지만 예측 손상 여유가0.2만큼 줄어 잘못 남긴 충돌1회 여유를 제거했다.223의 접촉risk는true→false로 바뀌고 damage0.8·terminalTrue는 그대로여서 해당 N은 terminal 조건으로 계속 제외된다. **전체 후보 순위/실제 정책 선택은 재평가하지 않았다.** F2 탈출이나 완주 개선을 주장하지 않는다.

warm-start·manifold/broadphase·solver 순서의 완전 복원은 여전히 없다. 이번 두 경계4행동의 검증으로 모든 접촉의 미래 이벤트 순서를 보장하지 않는다. 이번 이력은 같은 재생 경계에서 저장한 trace로 보충했으며 기존 상태 필드는 모두 그대로였다. 이후 `capture`는 이력을 직접 포함한다.

비용: **native223/600·모델4질의/32틱·native wall13.84초·모델 wall0.201초**. 모델CPU0.200초는 이번에는 offline 비교여서 evaluator CPU11.16초 바깥이다. actor CPU2.63초는 별도다. 누적734,714+연구잔여1,286+예비84,000(사용0)=B820,000.

지정 클라우드만 사용했고 비용 상한 조정·새 유료 자원·챔피언 변경·HOLDOUT/SEALED·자동 후속 실험은 없다. main·Participants·기존 백업·사용자 변경을 보존했다.

[익명 원인·검증·비용](contact_history210_result.json)
