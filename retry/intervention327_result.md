# 327: 실제 동일 pre-state의 한 행동 반증 수집

**12개 endpoint를 모두 수집했다. 큰 제동의 속도 반응 예측은 개선됐지만 통합 반응 게이트는 실패했다.** O0/O2에서 ridge는 제동 속도 감소를 잘 잡았으나 yaw·joint 반응 MAE가 기존 motor 기준보다 컸다. 모델·입력·정규화·threshold·계수는 변경하지 않았고 fit·controller 승격·MPC·완주 실험은 없다.

인덱스는 결과 전에 해소했다. 요청의 명시적 비용식과 ‘64개 prefix’를 따라 **64개 행동을 완료한 뒤, 0-based64 = 65번째 한 행동**을 개입했다. 도로3×arm4×65 = **780 native**를 등록했고 잔여395에 차이385만 추가했다. 임의로 다른 state나 step을 고르지 않았다.

O0/O2에는325의 해당 도로 제외 LORO 모델을 그대로 사용했다. N0은325 학습 도로에 없고 N0 LORO·full fit도 실제로 없다. 새 fit 금지 조건에 따라326에서 이미 정의한 여섯 기존 모델의 고정 평균을 N0 보조 비교로 사전 등록하고 사용자에게 알렸다. N0을 별도 LORO fit으로 꾸미거나 세 도로의 서로 다른 모델 정의를 합산하지 않았다.

네 arm은 baseline, 최종 steering+0.08, 최종 steering−0.08, 원래 steering+gas0+brake max(original,0.5)다. Steering만±0.4로 clip하며 다른 채널은 해당 arm 정의대로 유지했다. 실제 steering clipping은 **0/6**이었다. 새 joint arm이나 선택된 후속 행동은 없다.

각 arm을 같은 case의 독립 reset에서 시작해296의 원래 act→commit→step을64번 실행했다. Native state clone·GT runtime·다른 궤적 endpoint 대체는 없다. 각 도로의65개 prefix 관측(reset부터64번째 행동 후),64개 실행 명령, 전체 prefix hash, 개입 전 full 픽셀, 정책 객체 hash·controller/tracker/history 상태, baseline act 뒤 상태·특징·원래65번째 명령이 네 arm 모두 정확히 일치했다.

사전 OFF 검증은 기존306 O0 캐시의65개 행동·특징을 두 별도 actor에서 재현한130쌍이다. 두 actor의 정책 객체·상태 hash도 정확히 일치했고, post-observation peek가 원래 정책 상태를 바꾸지 않음을 검증했다. 제출296 ZIP은 그대로이고 worker는 상태 receipt만 확장했다. Peek가 반환한 다음 명령은 실행하지 않았다.

모든 arm이65번째 실제 한 행동 뒤 endpoint에 도달했다. 원래float32 `(4,84,84)` 관측66개와 실행/base 명령65개·시각·직접 collision flag·공식 종료 flag·정책 상태를 소비 실행기의 비공개 캐시에 저장했다. 마지막 raw post 픽셀을 포함해80ms 전이를 직접 검증했으며 decoder fallback은0이었다. **12개 모두 계획된 protocol stop**이고 공식 조기 종료·기술 오류·누락 endpoint는0이다. 이를 미완주12개나 DNF12개로 집계하지 않는다.

| O0/O2 주 비교, baseline 대비 반응 MAE (6 pair) | Speed m/s | Yaw rad/s | Joint rad |
|---|---:|---:|---:|
| Persistence | 4.16667 | 0.67163 | 0.05596 |
| 고정 ridge | 0.63289 | 0.32267 | 0.01148 |
| 기존 motor/kinematic | 4.16667 | 0.19281 | 0.00263 |

세 채널의 반응 MAE가 persistence와 motor 모두보다 낮아야 한다는 사전 진단 게이트는 통과하지 못했다. 주 비교의 실제 비영 반응 부호는 ridge가 speed2/2·yaw4/5·joint4/4, motor가0/2·4/5·4/4였다. 관측0인 분모는 speed4·yaw1·joint2로 별도 남겼다. 서로 다른 단위를 한 점수로 합치거나0 반응을 부호 정답으로 부풀리지 않는다.

| 큰 제동의 baseline 대비 실제 / ridge 예측 속도 변화 | 실제 HUD 변화 | Ridge 예측 |
|---|---:|---:|
| O0 | -12.50 | -14.24519 |
| O2 | -12.50 | -14.16578 |
| N0 | -12.50 | -13.70725 |

큰 제동에서 세 도로의 실제 HUD speed 변화는 모두−12.5m/s였다. Persistence·고정속도 motor는 모두0을 예측했다. Ridge는 학습에서 없던 gas0·brake0.5의 감소 방향과 대략적인 크기를 잡았다. 이는 이번 세 상태에서 새로 얻은 유효한 부분 증거다. 다만 제동 arm의 joint 관측 변화는 모두0인데 ridge는−0.00966/−0.01760/−0.00729rad를 예측했다. O2 제동의 yaw 실제 변화는+0.05594인데 예측은−0.35409rad/s로 부호도 달랐다. N0에서도+0.50722 대−0.26704로 달랐다. 속도 반응의 부분 성공을 전체 상태·폐루프 성능으로 확대하지 않는다.

| 절대 next-HUD MAE | Speed | Yaw | Joint |
|---|---:|---:|---:|
| O0/O2 Persistence | 3.12500 | 0.50372 | 0.04307 |
| O0/O2 고정 ridge | 0.55497 | 0.24200 | 0.00877 |
| O0/O2 기존 motor/kinematic | 3.12500 | 0.14847 | 0.00331 |
| N0 보조 Persistence | 3.12500 | 0.53146 | 0.05847 |
| N0 보조 고정 ridge | 0.45021 | 0.24626 | 0.00726 |
| N0 보조 기존 motor/kinematic | 3.12500 | 0.45797 | 0.00754 |

N0 보조의 baseline 대비 반응 MAE는 ridge `[0.46188,0.46073,0.00809]`, persistence `[4.16667,0.64148,0.05362]`, motor `[4.16667,0.61063,0.00028]`였다. Yaw는 motor보다 좋지만 joint는 더 나빠 같은 게이트를 통과하지 못했다. 세 도로 각각 세 pair이며 독립 pre-state는 **3개**뿐이다. 다른 arm의 반복 prefix를 독립 상태 표본으로 세지 않는다. 개별 실제/예측 변화·크기·부호·action 변경·clip·RMSE·bias·max는 집계JSON에 보존했다.

65번째 endpoint의 직접 collision flag는 **12개 모두 false**였다. O2는 개입 전 동일 prefix의46번째 행동에서 접촉1회가 있었고 다른 두 도로 prefix는0회였다. 이 이력도 네 arm에서 같았다. 새 endpoint contact 표본은0이므로 contact 전이의 정확성을 검증했다거나 안전을 보장한다고 주장하지 않는다. HUD 양자화 때문에 관측0이 실제 물리 반응0을 뜻하지 않고, 제동의−12.5도 양자화된 norm speed 변화다. GT 물리 상태를 추가로 읽어 이 한계를 덮지 않았다.

비용은 등록한 **780/780 native**, 실제 step3,120 tick·reset612 tick이다. 수집 wall64.44초, runner CPU51.46초·actor CPU12.09초였다. 별도 캐시 preflight wall11.41초는 native0이며 분석 wall/CPU0.454/0.453초다. 추가 source forecast physics·fit·PPO·유료 자원은0이다. 원래 기준296·모든 과거 실패·사용자 파일·main·Participants·백업을 유지했다.

추가 연구385를 한 번 등록했고 비용도 한 번 닫았다. 누적 **1,274,701 + 연구 잔여0 + 최종 예비84,000 = B1,358,701**이다. 예비 사용0, DEV/HOLDOUT/SEALED·champion 변경0이다. 원시 pre/post 픽셀·전체 정책 상태·실행 추적·모델·개인 원문은 비공개에만 저장했다.

판단은 이 고정 모델의 **통합 동역학/MPC 확대 보류**다. 고속의 실제 큰 제동 속도 반응에 유효한 증거는 보존하되 yaw·joint의 잘못된 교차 반응과 작은 표본을 함께 남긴다. 원래 모델을 결과에 맞춰 수정하거나 새 주행·학습·승격을 시작하지 않았다.
