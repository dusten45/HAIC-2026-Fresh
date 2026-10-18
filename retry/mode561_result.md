# 561 — prefix 순서통계 동치·저장기 검증, 새 clipping을 허용한 안전 제안 확인

**clipping count의 잘못된 smooth 미분을 제거했다.** 초기 이력을 포함한 strict count와 prefix 순서통계가 합성81,229건·560의 저장4궤적에서 일치했다. gate 통과 뒤 같은 feasible source 구간에서 두 rank branch와 두 고정 coordinate poll을 검사했다.

첫 제안은 **전역 안전·실제 count·12hold 후속을 통과**했고,고정 plane의 보간 시각 차이는4.284/5.243ms였다. baseline에 없던 clipping4개가 생겼지만5개가 없어져 허용 예산 안이었다. 다만 plane 위치가 baseline과 약1.5m 달라 **사전 handoff aperture를 미달**,incumbent로 수락하지 않았다. 이를 전역 안전 실패로 부르지 않는다. 다른 제안은 실제 안전 위반 또는 시간 손실로 거절됐다. 수락0·최종baseline·누적개선0이다. 개별5ms 미달이 종료 이유가 아니다.

## 정확한 count와 순서통계

초기 clipped/sample 이력을 `C0,N0`,새 prefix ratio 배열 길이를 `n`이라 하면

`K = floor((N0+n)/10) − C0`

이며 조건은 `sum(ratio > 1) <= K`다. `K<0`이면 실패,`K>=n`이면 자동 통과다. 그 외에는 **내림차순 K+1번째 ratio≤1**과 동치다. 정확히1인 값은 unclipped다. >1인 동률은 각각 count되고,동률의 index 선택은 branch에 영향을 줄 수 있지만 순서통계 **값/판정**은 바꾸지 않는다. stable sort는 대표 index를 결정하는 용도이며 smoothness 보장이 아니다.

source history는 **3/160 wheel samples**,새 prefix는 매raw4개 wheel force sample이다. 원 source의 부동소수점 fraction 판정과 정수 floor 판정의 일치는 source 범위와 합성분모≤1e6에서 검사했다. 이보다 큰 부동소수점 분모까지 보편 동치라고 주장하지 않는다. ratio에는 추가 float32 rounding을 강제하지 않는다. float32로 표현된 값은 그 값을 그대로 strict 비교한다.

과학 source 실행 전 단위검사는 다음을 확인했다.

- float64/float32의1 바로 아래/위 nextafter,정확히1,동률,여러 clipped 값,빈 배열·이력/분모10 경계·기존 clipped 예산 소진 등을 포함한 **81,229개** 동치 사례.
- active clipping sample의 identity를 서로 바꾼 배열도 실제 허용 count 안이면 통과함. baseline mask를 전역 금지 조건으로 두지 않음.
- NumPy int/float/bool/array의 JSON 기본형 roundtrip,NaN 입력 시 원파일 보존,exclusive 쓰기 보존,replace 직전 주입 오류에서 원파일/임시파일 정리,예외의 finally에서 비용 보존.

저장560 baseline·세 거절 후보에는 **새model/force/geometry0**으로 모든132prefix를 검사했다. baseline은 통과했고,세 후보는 각각 첫 위반 raw31/27/26에서 actual count와 순서통계가 똑같이 실패했다. 최저 순서통계 slack은 baseline+.000470565,후보−.006270982/−.002669602/−.003990170이었다. 저장 ratio>1과 각 source clipped flag도 일치했다.560 원판정과 CPU 공백을 수정하지 않았다.

## 사전 문제·분기·복구·예산

560의 동일 초기 fullstate·지도·원551 reference·공통 plane을 고정했다.20hold의40제어,고정12hold 후속+1hold 측정 buffer이며 baseline 시간은1.60/2.56초다. 새 baseline132raw가 저장560 전체 root/contact/force와 정확히 일치해야 다음 gate를 열었다. 첫40FD 열은560의 저장 **개별 force ratio/비clip 물리·return 민감도**로 재사용했고,count 미분은 만들지 않았다. 새 source 비용으로 과거 FD를 다시 청구하지 않았다.

주 LP는 각prefix의 topK를 허용 집합으로 둔 local rank branch를 선택하고 나머지 **개별 선형화 force ratio≤1−buffer**를 제약한다. buffer는 min(1e−5,기존 양의1−ratio slack의25%)로0방향을 불필요하게 배제하지 않는다. 전역force1.059 등은 별도 유지한다. 이 branch는 exact 순서통계의 **국소 충분조건/근사**이며 전체 feasible set이 아니다. 실제 nonlinear source가 다른 활성 집합을 만들더라도 **exact count/순서통계와 원 안전으로 다시 판정**한다.

최초 branch가 실패하면 **한 번만** 거절 제안의 순위로 exemption을 재구성한다. 기존 clip을 해제하고 새 identity를 허용하도록 바뀔 수 있다. 이번 최초 branch의 union exemption28개는 데이터상 baseline clipped mask28개와 우연히 같았다. 이 사실을 숨기지 않는다. 재구성에서는 membership8개가 바뀌고 원 baseline-unclipped4개가 exempt가 됐다. 실제 첫 source 제안도 newclip4/freed5를 전역 안전 통과로 인정했다. 따라서 baseline no-new-clip mask를 전역 수락 조건으로 되돌린 것이 아니다.

두 branch가 수락을 얻지 못하면 사전 **최대2poll**만 한다. 하나는 시간 gradient가 큰 coordinate의 하강 방향,하나는 critical order-stat force를 줄이는 coordinate다. amplitude는steer.0005/pedal.005로 고정했고 기존 행동 bounds만 적용한다. LP trust는steer.004/pedal.04로 고정하며 scalar반경 축소 반복은 하지 않았다.

각 제안은 실제132raw의 footprint≥.5,path≤3,**원551reference** overspeed≤4.85,force≤1.059,body<100,실제 prefix clipping≤10%를 모두 검사한다. main aperture≤1m/follow≤.5m,body방향차.08/속도방향차.05rad·follow속도≥baseline−.5m/s라는 기존 **handoff 설계**도 유지한다. 이 비교 조건들은 물리 필요조건이 아니다. 상대yaw·wheelomega/gas/joint baseline동일성·주기성·고정contact는 요구하지 않는다.

실제 feasible+양쪽 시간 비악화(.5µs tolerance)+평균 이득>1µs면 수락한다. 개별5ms 기준은 없다. 최대 방향4·수락4·LP branch8·poll8·source제안16·freshFD120,두작은수락/예측불일치 정체와 방향 무수락 중단을 등록했다. **model20,000틱·힘85,000·geometry20,000·CPU400초/wall480초**,preflight≤20/30초를 전체 안에 포함했다. accepted incumbent는 불변 저장,거절은 교체하지 않는다.

## 네 제안의 관측과 분리 판정

|방향/복구|예측 main/follow(ms)|source plane 시각 차이(ms)|전역 안전|사전 수락 실패|
|---|---:|---:|---|---|
|최초 rank branch|7.704/7.544|**4.284/5.243**|**통과**|handoff 위치|
|순위 재구성|8.294/8.122|4.911/5.794|실패|force·clip 및handoff 위치|
|시간 coordinate poll|1.211/.918|.740/.686|실패|force·reference·clip|
|clip-relief poll|−.190/−.210|−.189/−.215|통과|시간 손실|

첫 제안132raw는 footprint최저 **.935340m**,path최대2.085368m,원reference overspeed4.712971m/s,force최고1.055912,누적clip최고 **9.6667%**,body95.286728m/s로 모두 전역 한계 안이었다. 끝clip30/688이며 new4/freed5,contact변화42raw,pedal mode변화1개다. exact순서통계 최저+.005947692도 통과했다. **활성 집합 변화가 있어도 허용 count 안이면 안전으로 인정**했다는 실제 source 증거다.

그러나 main/follow plane의 baseline 위치 차이가 **1.513256/1.562055m**로 사전 aperture를 넘었다. follow body방향차.001057rad,yaw차−.001151rad/s는 진단값이며 거절 원인이 아니다. 고정 longitudinal plane의 통과 시각 차이와 서로 다른 lateral 상태를 함께 기록하며,동일 fullstate 점대점 개선이나 전체 랩 이득으로 바꾸지 않는다. 이 제안을 뒤늦게 수락하도록 aperture를 완화하지 않았다.

재구성 제안은force1.063182·clip10.5263%,시간poll은force1.062533·원reference overspeed4.884635·clip10.3333%로 실패했다. clip-relief poll은 물리/return feasible이고도 보간시간이 늦어 거절됐다. 각각 exact source 결과다. 방향1회·두 branch·두poll 뒤 수락이 없어 등록 종료 규칙을 적용했고,다음 방향/freshFD를 열지 않았다.

## 최종검증·비용·해석

최종 incumbent는 baseline이다. 새132raw의 모든 state/contact/force가 baseline과 정확히 일치하고12hold 후속을 포함한 전체 안전도 통과했다. 최종 main/follow **1.60/2.56초**,누적개선 **0/0ms**다. footprint1.156639m,path1.325267m,reference4.849744m/s,force1.058954,clip최고10%·끝31/688,body95.424332m/s를 유지했다. 고정raw bracket은[1.58,1.60]/[2.54,2.56]초다.

구조적 검사 결과는 긍정적이다. strict count와 정확한prefix예산을 보존했고,560의 세 실패를 올바르게 재분류했으며 새 clipping identity를 가진 **전역 안전한 finite rollout**도 찾았다. 다만 이번 전체 handoff 문제는 미해결이며 수락/누적 개선은 없다. 그 제한은 clipping 실패와 비교 aperture 실패를 구분해 판단해야 한다. 순서통계/선택branch를 smooth 또는 모든 안전 경로의 필요조건으로 부르지 않는다. 실제/전체랩1초 개선·원루트 도달성/픽셀정책 승격은 미검증이며 추가 실험하지 않았다.

비용은 **6eval×132=model792틱**,명시휠힘 **3,168회**·적분내부3,168회,body792·geometry **798회**다. 저장40FD는재사용/freshFD0,LP2·poll2·source제안4다. **CPU13.205196초/wall13.205654초**에preflight와기록비용을 포함했고 과학 실행 이후 편집/Git 총비용 주장은 아니다. 거절forecast6raw의force위반·최고1.063182와 모든model body최고95.459437도 계상했다.

비용은 매eval finally와 outerfinally에서 JSON 기본형으로 원자 저장하고,**독립 cost ledger를 풍부한 결과보다 먼저 확정**했다. 본 실행의 CPU/wall·모델비용은 완전하게 보존됐다. 감사 stdout에서 남은 NumPy bool 변환 누락은 고쳤고,그때도 원자 저장된 감사/결과/비용은 정상 보존돼 source 재실행0이었다. **560의 기존 CPU계측 공백은 그대로**이며 이번 측정으로 과거를 복원했다고 주장하지 않는다.

읽기 전용 감사 **22항목**이 hash·저장기/동치 gate·네 과거궤적·새원시count/순서통계 일치·cachedFD계보·분기재구성/신규clip허용·전역/설계실패 분리·immutable incumbent·새최종후속·전비용/CPU한도·main을 확인했다. 감사source/force/geometry0이다.

실제 행동/reset/world·새seed/HOLDOUT/SEALED·예비사용·다른환경·유료0,연구 **22,758**·예비 **84,000**이다. 원시 지도/상태/제어/FD/순위집합/접촉은 저장소 밖 비공개다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자변경·560판정/계측공백·백업을 보존한다. 개인 원문 직접독해나 파일 요청/전송을 주장하지 않는다. 종료 **2026-10-20 19:01:55KST**,자동 연장 없음이다.

[사전계약](mode561_contract.json) · [순서통계·저장기](clip561_core.py) · [단위검사·재분류](mode561_preflight.json) · [원결과](mode561_result.json) · [원자cost](mode561_cost.json) · [감사](mode561_audit.json)
