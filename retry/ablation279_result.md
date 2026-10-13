# 279 — 276 checkpoint64 출력 제거 TRAIN 진단

새 학습·계수 탐색 없이 276의 고정 최종 checkpoint64 actor·정규화와240 baseline을 사용했다. checkpoint와 ZIP의 actor 계수는 정확히 일치했다. A는 steering residual만0, B는 gas/brake residual만0이며, 나머지 ZIP 파일은 원본과 byte-exact다. 278 checkpoint를 사용하지 않았다.

| 기존 TRAIN | A: steering 제거 | B: pedals 제거 | 저장된276 전체출력 | 저장된240 |
|---|---|---|---|---|
| N0 | 24.50초 완주, damage .4 | 23.70초 완주, damage .2 | 78 action crash | 23.62초 완주 |
| N2 | 166 action off_track, damage .4,70/292타일 | 366 action crash, damage1,277/292타일 | 222 action crash | 21.56초 완주 |

N0는 어느 한 출력군을 제거해도 실패가 해소됐다. B가 A보다 .80초 빨랐고240보다 .08초 느렸다. N2에서는 두 개입 모두 실패했으나 B는 거의 전체 도로까지 진행했다. **다음 학습에서 gas/brake residual 범위 축소를 우선 검토할 약한 근거**는 있다. 다만 steering 제거도 N0를 구했으므로 pedals 단독 원인으로 확정할 수 없다. N2 실패가 남아 두 ablation 모두 승격 근거는 없으며 챔피언240을 유지한다. 단일 checkpoint·알려진 TRAIN 도로·각1회 진단으로 독립 평가가 아니다.

두 도로에서 모두 첫 action부터 명령이 달랐다. 원래 전체출력은 `[−.0003649076,.5209064484,.0186831299]`이고 A는 `[0,.5209064484,.0186831299]`, B는 `[−.0003649076,.5241886973,.0203358755]`다. 차이는 A의 steering `+.0003649076`, B의 gas `+.0032822490`·brake `+.0016527455`다. 첫 action은 이력이 없어 공통 입력이며, 이후 actor 입력·관측은 각 실제 반환 action에 따라 달라지는 closed-loop 개입이다. 동일 궤적 비교로 해석하지 않는다. 저장 관측16쌍과 모든 실제 action에서 제거 공식·steering memory·최근 action 이력 일치를 검증했다.

네 주행만 실행했다. 실제DNF2, 기술 오류0,650상한 검열0. 신규 비용 **1,136 native action**, 학습0·240/276 기준 재주행0이며 승인2,600 이내다. 평가 elapsed62.004초. 누적923,208 + 연구 잔여1,792 + 예비84,000 =1,009,000. HOLDOUT·SEALED·최종예비를 사용하지 않았고 유료 자원 추가0이다. 원시 궤적·ZIP·checkpoint·개별 receipt는 비공개에 보존했다. 다음 실험은 시작하지 않았다.

집계 수치·실측 비용·SHA256은 `ablation279_result.json`, 고정 생성·평가 코드는 `ablation279_prepare.py`, `ablation279_worker.py`, `ablation279_eval.py`에 있다.
