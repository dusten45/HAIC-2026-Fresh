# 374 champion 296의 fallback-only T2950 최소 반증

**H1 OFF·fallback ON·birth-routing OFF인 별도 동결 후보가 T2950에서 공식 완주했다.** 318행동, 공식 lap **25.400초**, 진행338/338, 접촉·DAMAGE0이다. 기술 오류·실제 DNF·protocol censor·재시도는 없다. 알려진 TRAIN 한 조건의 구제 feasibility만 통과했으며 champion296 유지·자동 후속 실행 없음·승격 없음이다.

등록 전 374 디렉터리·원장 항목·실행 프로세스가 없음을 확인했다. 기존 연구41,600회에서 최대2,000행동·reset1회만 등록하고 공식 완주·은퇴·상한·승인 종료·기술/합법성/무결성 오류 중 먼저 도달하면 멈추도록 고정했다. 추가 배정·예비 사용·새 대조군·캐시 actor·새 split·372 자료 사용은 없다.

| 항목 | 역사적 champion296 | 이번 fallback374 |
|---|---:|---:|
| 공식 결과 | off_track DNF | **완주** |
| 실제 행동 | 315 | 318 |
| 공식 lap | 미정의 | **25.400초** |
| 진행 | 208/338 | 338/338 |
| DAMAGE | 0.2 | 0.0 |
| 이번 비용에 포함 | 아니오 | 예 |

후보 ZIP은 `919832e8ed5d280e65c9b75719c4dcfc494a51198131dc29f71079089a00b04b`다. 원본296 ZIP은 `0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937`이며 그대로 보존했다. 원본에서 바뀐 기존 멤버는 **retry/temporal_agent.py 하나**, 추가 파일은 기존334와 같은 고정 **retry/hud248_features.py** decoder 하나뿐이다. root agent·원래 head/model·controller·계수·nominal·routing·검출·dedup·age·expiry와 나머지 원본 멤버는 바이트 동일하다. H1 wrapper·selector·모델 모듈, birth-routing·support/history helper는 포함하지 않았다.

373에서 미측정으로 확인한334 H0/F1/R0의 정책 동작을, 사용하지 않는 H1 wrapper·모델 자산 없이 원본296 위에 구성했다. 334의 disabled wrapper 안의 base는 원본296 root와 정확히 같았고, 선택기 OFF는 원래 반환값을 그대로 돌려준다. 실제 변경 temporal과 decoder도 기존334 파일과 바이트 동일함을 확인했다. 새 공식·gate·threshold·계수·fit은 없다.

변경한 식은 optical 변환이 거부되거나 없을 때만 `Δψ=.08×(이전 yaw+현재 yaw)/2`, `p_next=R(-Δψ)(p_old−(0,현재 HUD speed×.08))`로 retained 점을 운반하는 것이다. 승인 optical은 원래296 계산을 유지한다. norm speed의 전방 이동·횡이동0 가정과 양자화·slip의 한계는 남으며 정확한 ego-motion이나 안전성 인증으로 해석하지 않는다.

패키지·worker·환경·런타임·등록 조건·중단·판정 기준을 첫 reset 전에 hash로 동결했다. 현재 worker는 기존334의 수동 관측기에 **실제로 routing에 전달한 전체 hazard 인자 기록·일치 assertion**만 추가했다. 점을 선택하거나 명령을 바꾸지 않는다. 실제 로드 모듈 hash와 H1/support 모듈 부재를 확인했고 Python3.11.16·NumPy1.26.0·OpenCV4.8.1, CPU1개·단일 thread·1,024,000,000 byte 제한·기존 호출 제한을 유지했다. 공식 서버·새 머신 동등성까지 증명한 것은 아니다.

새 reset은 기존 T2950의 초기 영상·등록 도로 기하·물리 장애물 hash와 일치했다. 정책에는 float32 `(4,84,84)` 흑백 영상만 전달했다. 자신의 관측에서 나온 **전체 반환 제어·정상 명목 기억**을 실행했고 저장 명령·관측·프레임 번호를 강제로 넣지 않았다. GT는 평가기에서 읽기 전용 캡처·사후 진단에만 사용했으며 제어·특징·선택 조건에 전달하지 않았다.

실제 318개 행동·319개 영상과 act/commit·raw tick을 대조했다. 모든 반환 명령과 실행 명령, float32 조향과 정상 기억이 일치했다. 공식 중심 통과 finish_time26.420초에서 post-reset 시작1.020초를 빼서 lap25.400초를 계산했다. 전체 tiles 방문이나 종료 확인 clock으로 lap을 대신하지 않았다. collision event·raw collision flag·샘플 fixture touching·새 obstacle hit는 모두0이다. 이는 raw20ms 관측 범위이며 숨은 solver 접촉의 완전 관측을 뜻하지 않는다.

모든 tracked hazard가 routing에 포함됐고 birth filter는 없다. 사후 원형 fixture 출생 라벨로 알려진 직접 지원 **61개 문맥**, 출생 지원 retained **23개 문맥**에서 누락은 각각 **0/0**이다. 출생 GT 누락 직접/retained도0/0이며 **미해결 출생 18개**는 false-positive 정답으로 바꾸지 않았다. 의미적 재질·실제 가림·미검출 안전성의 보증은 아니다. positive_history 전파를 사용하는 후보가 아니므로 그 전이 성능을 새로 주장하지 않는다. 기존365의 반례·미해결 사항과 탈락 상태는 그대로다.

전체318개 tracker 갱신을 고정334 식으로 재구성한 최대 수치 차이는 **7.11e-15**였다. retained 점이 있는 fallback interval은 **38개**, 그 점 운반은 **59개**, 승인 optical interval은 **110개**다. 이 재구성은 source physics rollout이나 새 정책 호출이 아니다.

비교 한계는 분명하다. 역사적296은 같은 등록 TRAIN·정책·초기 관측/기하 자격의 대조이며 새 동시 paired arm은 아니다. 과거 전체 RNG·actor state·물리 접두를 이번 관측자 seed374와 같다고 증명하지 않았다. 373의 고정 픽셀 첫 차이28/149를 실제 분기 시점으로 강제하거나 확인했다고 쓰지 않는다. 원본296에는 완주 lap이 없어 시간 개선량을 계산할 수 없다. 널리 연구·선택된 T2950 한 번의 성공은 전체18조건 보존이나 새 도로 일반화·원인의 고유 식별을 보증하지 않는다.

실제 비용은 **318/2,000 wrapper 행동**, act/commit 각각318회, 환경·actor reset 각각1회다. Raw step **1,271 tick**, reset **51 tick**이며 추가 source rollout·캐시 actor·학습·튜닝·유료 자원은0이다. episode 벽시계 **26.845초**, runner CPU **23.519초**, actor CPU **3.348초**다. simulation/render 10.152초·상태 캡처 10.905초를 포함하며 코딩·등록·마감·git 전체 시간은 아니다.

실제318회만 차감해 누적 wrapper **1,306,782회**, 연구 잔액 **41,282회**를 v392에 기록했다. 최종 예비 **84,000회 전액 보존**, reserve 사용0, 운영 상한1,432,064회는 그대로다. 남은1,682의 미사용 episode 상한을 비용으로 차감하지 않았다.

다음 미해결은 T2954 등 기존 완주의 보존과 넓은 TRAIN 회귀다. 이번에는 이 검증을 실행·예약하지 않았고 후보를 수정하지 않았다. champion296·365 탈락 잠금·별도 미개봉 SEALED16·main 기준·공식 Participants·사용자 변경·기존 백업을 보존했다. 372 디렉터리와297 조건 파일을 읽지 않았으며 새 split은 열지 않았다. 공개 범위는 일반 코드·집계 결과뿐이고 ZIP·모델·조건·seed·관측·GT·개인 자료는 비공개에 보관한다.
