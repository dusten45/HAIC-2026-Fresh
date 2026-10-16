# 418 — C 첫 가속의 실제 clipping 보정을 통과했다

**고정 C pre119에서 실제 A/B를 한 번씩 실행해 첫 변경 전이와13행동 source fidelity를 확인했다.** B의 새로운 rear clipping26/208표본이 source와 phase별로 모두 일치했다. 실제 exit 이득 bracket도 source와 같은0.04–0.08초였다. 이 보정은417의 승격 기준0.08초 미달 판단을 바꾸지 않으며, 전체 랩이나 정책 승격의 증거가 아니다.

이번 실제 실행은417의 시간 게이트를 낮춘 재시도가 아니라 별도로 승인된 clipping 보정이다. 같은 history118·C pre119·RNG·memory·경로·속도 노드·gain·조향·signed-C·fidelity 기준을 동결했다. A는 nominal, B는 첫 nominal 조향을 유지한 gas1/brake0 한 번 후 같은 C nominal 피드백이다. 공통 exit는 같은 원래 arc+30m, suffix는13행동이다. 새 창·pulse·horizon·재주행·전체 랩은 없다. [동결 실행 코드](calibrate418_run.py), [실제·guardian 코드](calibrate418_actual.py).

A/B는 독립 reset에서 시작했다. 두 arm 모두 기존411 C의 history118 pre/post·nominal·memory를 정확히 재현했고, cached source prefix의 body·wheel·이번에 직접 수집한 full raw hull도 기준을 통과했다. A/B 초기 full state와 fork의 관측 hash·RNG·memory가 정확히 같았다. 실제 A는119 이후까지 포함한131행동의 command와 post sensor도 저장411 C와 정확히 일치했다.

각 suffix 행동 전에 현재 실제 부모를 복원한 독립 forecast 두 개를 확인했다. guardian26회 모두 모델 조회 전후의 접근 가능한 full state·RNG·controller memory hash가 같았다. actual step 전 첫119 query에서도 확인했다. export되지 않는 solver warm-start 내부 전체를 캡처했다는 주장은 하지 않는다. 두 arm 모두 기존411 안전 guardian을 사용했고 추가 neutral-brake 개입은0이었다. B 첫119의 고정 full-gas도 현재 상태에서 별도 중복 forecast를 통과한 뒤 실행했다.

## clipping과 fidelity

| suffix 결과 | A nominal | B full-gas-first |
|---|---:|---:|
| 실제/source clipped wheel 표본 | 0 / 0 | 26 / 26 |
| 전체 wheel 표본 | 208 | 208 |
| phase별 clipping flag 불일치 | 0 | 0 |
| 실제 최대 force ratio | 0.963277 | 1.247783 |
| source 최대 force ratio | 0.963279 | 1.247786 |
| 실제 suffix post 최대 경로 오차 | 0.99946m | 0.99109m |
| 손상·도로/grass·충돌·후진 위반 | 0 | 0 |
| 일치 recipe fidelity | 13/13 | 13/13 |

B의 첫 clipping은 실제/source 모두 **121번째 행동, raw tick3, wheel2**였다. rear wheel 표본26개, front clipping0개다. 첫 가속 요청119에서 즉시 clipping했다고 오해하지 않도록 발생 phase를 따로 기록했다. clipping 자체를 새 안전 거부 조건으로 쓰지 않았다.

첫 변경119의 source B 대비 실제 post 위치 차이는0, 속도 차이3.515×10⁻⁶m/s, yaw 차이0이었다. 그 첫 전이의 wheel omega 최대 차이4.950×10⁻⁶rad/s, force ratio 차이1.591×10⁻⁶였다. B13행동 전체 최대 차이는 body 위치1.599×10⁻⁵m·속도1.533×10⁻⁵m/s·yaw9.046×10⁻⁶rad/s, wheel omega4.234×10⁻⁵rad/s·force ratio8.462×10⁻⁶, raw hull origin 위치1.630×10⁻⁵m였다. 같은 Car.step 계측 phase와 기존 기준을 유지했으며 COM/mass metadata도 일치했다.

매 실제 selected 첫 전이의 fresh source 예측도 두 arm 모두 통과했다. cached source 명령과 byte 단위로는 A11행/B12행에서 차이가 있었지만 최대 차이는 각각1.788×10⁻⁷/4.061×10⁻⁷로 동결한1e−6 명령 게이트 안이었다. 자기 상태의 수치 차이이며 guardian에 의한 recipe 변경은 없었다. 따라서 이번에는 원래 recipe의13행동 fidelity와 실제 정책 결과를 함께 대조할 수 있었다. guardian override 이후까지 원래 recipe fidelity를 확대하는 구현이나 해석은 하지 않았다.

## 시간 판정과 범위

| 원래 공통 exit | 실제 A | 실제 B |
|---|---:|---:|
| raw tick bracket | [25,26] | [22,23] |
| 경과 시간 bracket | 0.50–0.52초 | 0.44–0.46초 |

두 실제 bracket은417 cached source bracket과 정확히 같다. 실제 이득은[2,4]rawtick=[0.04,0.08]초이며 보장 이득은2tick이다.417이 요구한4tick 보장 이득을 충족하지 않는다. 보간 시간·중간값을 확정 도착 시간으로 쓰지 않았고,417의 기록·탈락 판정도 그대로 보존했다.

이 결과는 한 알려진 개발 상태와 q 최대약1.248의 관측 clipping 영역에서 모델의 실제 전이를 확인한 국소 보정이다. 새로운 조향/접촉 전역, C tail 전체 랩, 정지 재출발, 미소 음수 영역의 실제 안전, 독립 일반화·픽셀296 성능은 검증하지 않았다. 공식 완주·DNF는 관측되지 않았으며 두 arm은 정상적으로13행동에서 끝냈다.

## 실제 비용과 보존

실제 **262wrapper/reset2**(arm별118+13), raw step1048/reset tick102를 사용했다. 실제 CPU15.664초/wall15.662초는 모델 구간을 제외한 값이다. guardian의 새 모델 사용은 **2808tick/54world, CPU7.479초/wall7.558초**다.26개의 nominal 중복 query와 B 첫 full-gas 중복 검증을 포함하며 neutral fallback query는 없었다. 모델과 실제 CPU/wall·step 계정을 중복 청구하지 않았고417의784tick은 재사용 기록으로만 남겨 다시 청구하지 않았다. 모든 지정 상한 이내다.

worker 실행 CPU23.233초/wall23.306초, 마지막 직렬화 전 worker 전체 CPU23.955초, 저장 결과 분석 CPU0.173초/wall0.174초를 기록했다. 준비의 파일 복사·작성·compile·동결 tool 구간만0.389초로 계측됐으며 앞선 읽기·설계·reasoning과 전체 준비 CPU/wall은 미계측이다. 이를 전체 준비 시간으로 제시하지 않는다. 실제 trace payload의 저장 합 CPU0.109초/wall0.090초는 전체 tracer dispatch overhead나 모든 모델 trace 비용의 완전한 측정이 아니다. 보고/git 전체 비용은 미계측이며 비계측 재주행은 하지 않았다.

원장v438: 연구 잔여 **29,618행동**, 예비84,000(사용0), 실제 누적1,318,446이다. actor·학습·SEALED·예비·새 유료 자원 사용0, champion296/rollback240·보호 자료·408 원기록·공식 main·승인 기한을 유지했다. 개인 seed·지도·상태·trace·RNG·명령열은 저장소 밖에 보관했다. 추가 실험 없이 보정 결과를 정리했다. [집계 결과·오차·비용](calibrate418_result.json), [저장 자료 분석 코드](calibrate418_analyze.py).

동결 plan SHA256: `362656b3bedc9bba16a8294bf26e4a1c4c3c1f93e3b180e3f9fd8697885e087d`.
