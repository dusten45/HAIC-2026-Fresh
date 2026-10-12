234 — 빨라진 페달 정책의 목표점 미리보기 단일 변경

**후보 1/2 완주, 기준 2/2 완주.** 현재챔피언232를유지하며후보추가튜닝·승격은없다.

| DEV | 기준232 | 1.25배후보 | 후보−기준 공동완주 | damage 기준/후보 |
|---|---|---|---:|---|
| F0 | 27.40초 | 27.50초 | +0.10초 | 0.2/0.2 |
| F1 | 25.40초 | DNF crash | 비교제외 | 0.6/1.0 |

실제제출코드의route_target은원래경로상arc-length `clip(4+0.35*speed,6,14)m`만큼의목표점을선택한다. 이번은그계산거리에1.25를곱한7.5~17.5m 목표점을최종조향에만사용했다. 같은232단일head의동일변경기록은없었다. 경로추출·gain3.24·rawclip±0.4·0.8/0.2smoothing·별도hazard근접거리·속도설정·pedalhead/정규화는그대로다.

nominal목표점으로16개특징·nominal명령·controller기억·보정pedal을먼저계산했다. 동일경로의별도1.25목표점조향을기존nominal이전steer로평활화해마지막출력의steer만교체했다. 변경steer를nominal기억에주입하지않았다. cached368관측에서기준특징/nominal/페달/기억은정확히일치하고최종조향은331관측에서달랐다. 실제후보모든행동에서도저장특징/동결head로페달을재계산해bit-exact와nominal기억연속성을확인했다.

실제주행은변경된조향으로다음관측이달라지므로도로간실제feature/pedalstream을동일하게고정한실험은아니다. 같은현재관측에서원래/변경조향과거리·목표점·특징을비공개진단으로기록했다.

실행순서는F0후보→F1기준232→F1후보, 공유native1,200상한이며임의도로별상한은없다. F0는동일232archive·조건·geometry/실제장애물검증·공식reset51틱/frame4/source인기존232smoke를재사용했다. 과거232의전체reset상태/관측hash는저장되지않아그기록의bytewise일치를새로검증했다고주장하지않는다. 새F0초기hash는같은knownDEV221resethash와정확히일치했고과거232의동일source/조건provenance를확인했다. F1기준은없어232를한번실행했고후보와초기관측·물리상태·geometry·장애물hash가일치했다. 230LOO head나233GT는기준으로쓰지않았다.

| DEV후보 | 같은관측 조향차이 행동 | raw포화 원래/변경 | 출력포화 | 조향부호변화 | 역방향tangent/정지행동 |
|---|---:|---|---:|---:|---|
| F0 | 221/344 | 0/0 | 0 | 30 | 0/0 |
| F1 | 132/199 | 3/1 | 0 | 18 | 0/0 |

raw포화는atan출력이기존±0.4clip에걸린횟수, 최종출력포화는|steer|≥0.4−1e−6 진단이다. 부호변화는연속명령의sign변화횟수이며nearest-road tangent 역방향은speed≥1에서의진단이다. 공식완주/방향은원래FinishLineTracker가결정한다. 새승인기준이나damage장벽은없다.

비용: **native861/1,200, wall37.366초**, evaluatorCPU30.512초·actorCPU6.890초, rawstep/reset3,443/153틱. 전체Agent계산/IPC분포는JSON에분리했고최대act IPC31.396ms·reset IPC4.033ms다. 공식reset/act5초제한·완주규칙은변경하지않았다. F0과거공식runner의Thread포함시간과현재격리actor의IPC시간은정의가달라계산성능차이로단정하지않는다. 모델질의·새학습0회.

검열0, 미실행[], 기술오류None. 누적757,557+연구잔여443+예비84,000(사용0)=B842,000. H24확장은종료했으며horizon sweep·H24학생학습·챔피언변경·HOLDOUT·SEALED·추가유료자원·자동후속실험은없다. 지정클라우드·main·Participants·백업·사용자변경·마감2026-10-16 19:01:55 KST를보존한다.

[후보Agent](lookahead234_agent.py) · [일회실행](lookahead234_run.py) · [재현builder](lookahead234_build.py) · [익명결과·비용](lookahead234_result.json)
