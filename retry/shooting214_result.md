214 — 고정32 후보의 매 재계획 확장

**F2 단일 reset 결과: off_track, 270/289, damage0.2.** 저장211은92/289 off_track·damage0.8,213의 일회 개입은79/289 off_track·damage0이었다. 알려진 DEV의 더 넓은 후보군 GT 연구이며 적법 픽셀 챔피언·실시간 성능·순수 알고리즘 효율 개선으로 주장하지 않는다.

211의 C/E/N/R·방향 이진키·contiguous/newtile 순위·접촉 veto 제거·terminal/나머지 조건·horizon12/replan3·210 접촉 이력 수정을 고정했다.212의 동일32개 float32 명령열을 재계획마다 추가했고 새 후보에도 동일한 적격 조건과 순위를 적용했다. command-difference 키는 현재 nominal에 대한 두 구간 steering offset이다. S 선택 뒤의 suffix는 기존 R로만 유지하며 원래12행동 만료를 갱신하지 않는다. R의 모든 실제 사용에서 남은 구간≥3·원래 만료를 검증했다. 재샘플링·CEM·새 후보군은 없다.

최초 선택 변경은1행동의 N→S12이며, 최초 실제 명령 분기는1행동이다. 두 후보 모두 정방향·contiguous/newtile6개·damage0·비terminal이었고, 끝 속도43.19m/s의 S12가 N의42.15m/s보다 높아 기존 속도 순위에서 앞섰다. 세부 예측 점수와 공통 prefix 범위는 익명JSON에 기록했다. S 선택 재계획52회/156행동, R 선택28회/84행동이고 그중 S에서 유래한 R은18회다.

최종 방문270/289, 정지0행동, 최장 무진행101행동, 마지막 새 타일 행동300이다. 완주 실패와 자원상한 censor를 구분했고 실패/종료 뒤 추가 도로나 재시도는 하지 않았다.

같은 전체 명령 prefix·4틱의 기존 forecast 비교: selected 390/390건, fallback 4/11건. selected 손상/물리 terminal 불일치0/0건, fallback은0/0건이다. raw collision·접촉 ID·타일·위치 오차와 미비교 행동은 JSON에 따로 기록했다. 부분 finish 틱·명령이 다른 fallback을 정확하다고 세지 않았고 비교를 위한 새 모델 질의는0회다. 모델에 없는 FinishLineTracker·warm-start/solver 이력까지 보장하지 않는다.

온라인 비용: 재계획당 질의 중앙값43개, 모델 batch 중앙값1057.7ms/p951984.1ms. actor/feedback 포함 재계획 중앙값1110.1ms/p952049.6ms다. 저장211의 모델37,768틱과 비교할 때 후보 수와 궤적 모두 다르므로 비용 증가와 결과를 분리해 해석한다.

비용: **native401/700·모델5,758질의/272,032틱·wall191.66초**. 모델CPU157.91초는 evaluator CPU186.48초에 포함되고 actor CPU4.84초는 별도다. 누적735,526+연구잔여474+예비84,000(사용0)=B820,000.

원문4.10/P4의 후보 범위·상태 복구·실제/모델 비용 구분을 유지했다. 지정 클라우드만 사용했고 새 유료 자원·HOLDOUT/SEALED·챔피언 변경·자동 후속 실험은 없다. main·Participants·기존 백업·사용자 변경을 보존했다.

[익명 결과·비용](shooting214_result.json)
