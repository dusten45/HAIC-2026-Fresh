319 — HUD 기반 한 action joint 회피 pilot, 알려진 여섯 TRAIN에서 완주 추가

**후보 6/6 완주 대 296의 5/6으로, T2950 추가·완주 손실 0이었다.** 공통 5개 완주 시간 평균은 **+20ms**로 조금 느렸지만, 사전에 정한 완주 수 우선 기준에서는 개선이다. 현재296은 유지하고 승격·다른 도로·자동 확대는 하지 않았다. 이 결과는 알려진 여섯 TRAIN의 고정 후보 효과이며 안전 보장이나 전체18조건·새 도로 성능을 뜻하지 않는다.

중복 실행·등록·결과가 없음을 확인한 뒤 계획을 고정했다. 185–186의 목표점 단축과286–289의 페달 고정 steering 예측은 반복하지 않았다. 관측·검출·tracker·경로·목표·기존 head·계수는 그대로 두고, **현재 HUD 상태로 예측한 최초 overlap 기회에서 steering·gas·brake를 한 action만 바꾸는 변경 하나**를 시험했다. 원래296 root를 exact base로 보존하고 나머지 기존 ZIP member도 바이트 동일하다. 각 실행의 변경 전 prefix와 개입 입력·base 출력은 저장296과 정확히 일치했다.

모델의 좌표는 현재 hull 원점의 x우측/y전방이다. 현재 카메라 ego 좌표계에서 초기 상대 heading은0이며, 관측된 yaw로 이후 방향을 전파한다. 현재 tracker의 장애물 좌표는 원래296의 물리 픽셀 원점41.542/62.4475를 그대로 소비했다. Nominal road-grid 원점42/63·경로를 이동시키지 않았다. Joint angle은 기존248 HUD front0 decoder의 물리 CCW 부호, action steering의 joint 목표는 **−action**이다. 공식 hull4개·wheel4개의 scaled polygon vertex와 joint anchor를 재사용했고 source polygon skin **0.0099999998m**를 포함했다. 정지/직선80ms 이동과 좌우 반사 yaw·steering·장애물의 clearance 대칭을 확인했다. Source physics는 호출하지 않았다.

다음80ms는 HUD norm speed를 고정하고 횡속도0으로 근사한다. 실제 front0 joint를 초기값으로 쓰며 front1은 같은 angle, rear는0으로 둔다. 기존286 motor 식의 gain50·max3rad/s를 네20ms tick에 적용하고 joint를 tick 안에서 선형 보간한다. 현재 clockwise yaw는−HUD yaw이며, `rate_cw=−HUD_yaw + v/3.24*(tan(−joint)−tan(−initial_joint))`로 조향 변화의 bicycle 증분만 더한다. Midpoint 적분과2.5ms 간격의 **33개 oriented pose**에서8개 fixture와 현재 tracked circle 사이 signed clearance를 계산한다. Tire force·slip·damage·wheel anchor 변형·브레이크 dynamics는 없다. **속도를 고정했으므로 제동 효과를 예측했다고 주장하지 않는다.**

결정은 결과 전에 고정했다. 원래 최종 steering과±0.08 대안을 원래 범위에 clip해 비교하고 실제 float32로 같은 command는 중복 제거한다. 최초 sampled overlap(`<0`)에서 clearance가 엄격히 커지는 대안이 있으면 그 steering·gas0·brake `max(original,.5)`를 한 action 적용한다. 정확한 동률은 original/minus/plus 순서다. 최초 overlap 기회는 latch로 한 번 소비하며 대안이 없더라도 이후 다시 찾지 않는다. 이후에는 현재 상태에서의296 식을 그대로 사용하되 **실제 실행 steering을 nominal memory에 기록**한다. 결과를 보고 threshold·모델·수치·반경을 조정하지 않았다. 0.08과0.5는 기존185·169의 고정값이다.

Sampling 오차 항은 모델 point-speed 상한×반 sample 간격으로 별도 계산했다. Cache의 최대값은 **0.082356m**이며 trigger clearance에서 빼거나 새 문턱으로 쓰지 않았다. 이는 가정한 연속 운동의 표본 간 항일 뿐 모델 오류의 상한이 아니다. 315의 한 action 위치 오차 평균약0.10m·p95약0.21m, 318의 상태 예측 한계·detector/tracker 오차도 남는다. 따라서 음의 sampled clearance는 인증된 실제 충돌 예측이 아니다.

306의 정렬된1,754개 캐시에서 OFF 행동·features·memory는296과 정확히 일치했다. ON 명시적 개입은5개 도로에서각1회, O0는0회였다. 현재 pixel은 고정돼도 실제 steering memory를 갱신하므로 이후296 출력의 일부도 달라져 **총61개 action**이 달랐다. 이를61회 shield 개입으로 계산하지 않았다.

| 캐시 TRAIN | 첫 overlap/개입 | baseline 첫 callback contact | 첫 개입이 앞섬 | 명시적 개입 |
|---|---:|---:|---|---:|
| T2950 | 151 | 184 | 예,33action | 1 |
| T2953 | 59 | 176 | 예,117action | 1 |
| T2956 | 113 | 없음 | 비교 불가 | 1 |
| T2959 | 122 | 241 | 예,119action | 1 |
| O0 | 없음 | 없음 | 비교 불가 | 0 |
| O2 | 45 | 46 | 예,1action | 1 |

사전 gate는 실제 action 변화와 **첫 적용 trigger가 cached 첫 contact보다 앞서는 사례 하나 이상**이었다. 네 도로가 충족해 native를 진행했다. 이 선후관계가 동일 장애물의 정확한 contact 예측이나 충분한 회피 시간이라는 뜻은 아니다. 첫 trigger action에는 모두 같은 action의 실제 callback contact가 없었다.

OFF의 각 원래 입력에서 sampled overlap과 **동일 action의 실제 callback event**를 비교하면 **TP3·FP27·FN2·TN1,722**다. 계속되는 기하 overlap과 새로운 callback event는 다른 개념이고, FP에는 이후 접촉보다 이른 warning도 포함될 수 있다. 이를 실제 geometric overlap의 정답 confusion으로 주장하지 않는다. false warning·missed event가 많다는 한계를 보존했으며 결과 뒤에 threshold를 맞추지 않았다. 캐시의1,590개 운동학 sequence·50,880개 수치 substep은 source physics가 아니다.

캐시 gate 후 후보 하나를 고정해 기존 여섯 TRAIN을각 한 번 실행했다. 비교는 완주 수 우선·동률일 때 공통 완주 평균의 엄격한 개선이며 damage veto·최소 개선폭은 없다. Baseline은 검증된296 캐시를 사용했다. 임의 wrapper 길이를 정상 DNF로 만들지 않고 공식 ended/truncated만 terminal로 사용했다. 전체 예산2969와 pending 도로의 기존 측정 비용을 확인했으며 추가 예산·검열·미관측 없이 모두 공식 종료했다.

| TRAIN | 296 | 후보 | 공통 시간 차이 | damage 기준→후보 | 실제 개입 |
|---|---:|---:|---:|---:|---:|
| T2950 | 미완주 | **26.72초** | 비교 불가 | 0.2→0 | 151회1action |
| T2953 | 23.80초 | 24.24초 | +0.44초 | 0.2→0.4 | 59회1action |
| T2956 | 23.32초 | 23.64초 | +0.32초 | 0→0 | 113회1action |
| T2959 | 21.18초 | 21.32초 | +0.14초 | 0.4→0 | 122회1action |
| O0 | 24.32초 | 24.32초 | 0 | 0→0 | 0 |
| O2 | 22.36초 | **21.56초** | −0.80초 | 0.2→0 | 45회1action |

추가1·손실0, 공통5개 차이 합계+0.10초·평균+0.020초다. 후보의 첫 실제 contact는 T2953의177이며 다른 다섯 도로는 contact0이었다. O0는 전체304개 action·features·memory가 baseline과 정확히 같았다. 나머지 도로의 실제 개입 전 prefix도 모두 exact였고, 개입 이후에는 각자의 바뀐 관측/메모리로296을 실행했다. DNF0·기술 오류0·검열0·미관측0이며 모든 actor를 회수했다.

예측상 선택 대안의 최저 clearance는 다섯 개입 모두 여전히 음수였다. T2950의 예측 개선은 약 **0.000177m**로 sampling·모델 오류보다 작다. 실제 완주 추가를 숨기거나 사후 최소폭으로 무효화하지 않지만, 이를 정확한 기하 예측이 회피를 만들었다는 인과 설명으로 바꾸지 않는다. Joint steering/brake/gas pulse·그 이후 memory·궤적 변화의 효과를 이번에 분리하지 않았다. 모델 경고의 품질과 실제 정책 효과는 별도의 증거다.

비용은 **native1,776/2,969**, 기대 baseline1,754보다22개 많았다. Raw step7,095·reset306틱, native wall133.607초·runner CPU97.855초·actor CPU32.425초다. Cache preflight wall79.104초, ON actor p95는24.19~48.98ms·max238.58ms, IPC max244.72ms였다. 새 source physics·fit/PPO·유료 자원·파일 전송/첨부는 없다. 실행 준비·정리·게시 시간을 native wall에 합쳤다고 주장하지 않는다.

V325 원장에 실제 비용을 반영해 **누적1,264,996 + 연구 잔여1,193 + 예비84,000 = B1,350,189**이다. 예비 사용0·추가 예산0이다. 296·rollback·main·Participants·기존 backup·개인 원문·317 실패·318 결과를 보존한다. 일반 코드·집계만 현재 연구 브랜치에 커밋·push하며 model/ZIP·pixel·GT·개별 trace는 비공개다. DEV/HOLDOUT/SEALED·승격·자동 확대는 없다. 과거310의6개 screen 개선이 전체18에서 유지되지 않았던 증거도 보존하며, 이번6/6을 다른12개·새 조건의 성공으로 확대하지 않는다.

[기하 모델](shield319_geometry.py) · [한 action/latch·실행 memory](shield319_agent.py) · [등록·캐시 gate·실행](shield319_stage.py) · [집계·비용](shield319_result.json)
