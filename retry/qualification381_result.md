381 — unchanged champion296의 같은 머신 독립 프로세스 자격 점검 통과

**296의 원래 패키지를 관측만 받는 clean worker에서 실행해 저장 TRAIN 237개 행동 전부와 reset 후 첫16개 행동을 정확히 재현했다.** 새 환경·주행·정책 변경·학습 없이 현재 의존성·cold start·RSS·지연을 확인했다. 별도 머신·공식 서버 재현이나 최종 G5 완료는 아니다. Manifest는 갱신하지 않고296을 유지한다.

부모는 방법론24장 전체와 적용계획 전체를 다시 읽었다고 확인하고, 적용계획10절의 입력·초기화·시간·메모리·재현 뒤 manifest 갱신,15절의 후반 회귀·cold start·패키지·롤백 우선,18.2절 G5의 동결 실행물·해시·의존성·정보·runtime·memory·출처·재현 묶음을 전달했다. 이 부모의 전체 읽기와 발췌를 실행 요청의 유효한 출처로 기록했다. **소비 실행기의 직접 원문 확보·완독은 여전히 미확인**이고 원문 전송은 없었다. 원문24장은 모든 방법군 구현 의무가 아니라 검토 근거를 요구한다는 전달에 따라380의 새 가설0개 판단과 닫힌 방향을 유지한다.

| 항목 | 기존 증거·최신성 검토 | 381에서 보완한 결과 |
|---|---|---|
| 동결 패키지 | 296 ZIP과 manifest의 원래18개 member hash 유지.377에서도 동일 ZIP 실행. | ZIP SHA256 `0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937`,18개 member 모두 일치. 외부 model/asset·추가 requirements 없음. |
| 의존성 | 296 기록은 same cloud qualification,377은 현재 버전의 observer 경로. | 현재 clean actor Python3.11.16·NumPy1.26.0·OpenCV4.8.1, 설치 배포판 opencv-python4.8.1.78. 정책 외부 import는 numpy/cv2/heapq뿐이며 나머지는 패키지 내부. Torch/Gym/Box2D는 actor에 필요하거나 로드된 의존성이 아니다. |
| 입력·reset/act | README는 float32 `(4,84,84)`,0..1 픽셀과 길이3 유한 행동,reset/act 각5초·초기화10초·메모리1,024MB. | 실제 요청은 `op, observation` 두 key뿐. reset2회·act253회, 모든 행동 shape·finite·범위 통과.237개 전체 행동 float32 bytes 일치,reset 후 첫16개도 일치. |
| cold start | 과거296/377 수치는 서로 다른 관찰 경로·시점이라 현재 clean 성능으로 대체하지 않음. | 한 독립 actor import/생성·IPC ready 포함 **226.070ms**.1회 측정이며 cold start 분포 보장은 아님. |
| reset 지연 | reset 없는 cold 객체와 episode 후 reset 구분 필요. | IPC 포함 **4.722 / 2.209ms**, 두 번째는237행동 뒤 reset. |
| act 지연 | 377 실제 폐루프 최대 IPC40.060ms는 observer 비용 포함. |253회 compute 중앙/p95/최대 **4.982/10.620/15.646ms**, IPC 포함 **7.449/13.270/19.632ms**.5초 초과0. 저장 입력 한 도로의 관측 범위이며 worst-case 상한 증명은 아님. |
| 메모리·CPU | 기존 runtime의1CPU/thread·주소공간1,024,000,000bytes 제한을 재사용. | ready/응답과 supervisor `/proc` VmRSS/VmHWM 표본의 최대 **45.691MiB**, 제한 이내. actor CPU1.923초,프로세스 회수 확인. 순간 peak의 완전 cgroup 측정·공식 메모리 동등성 인증은 아님. |
| 실제 궤적 재현 | 377이 알려진 TRAIN을 실제237행동으로18.940초 완주하고 기존296 기록과 전체 대조함. | 이 최근 근거를 재사용해 추가 smoke는 실행하지 않음. 이번 저장 픽셀 재생을 새 closed-loop 완주로 세지 않음. |

격리 경로는 기존 native read sandbox와 원래 `clean_pixel_worker.py`를 그대로 썼다. 부모 supervisor만 비공개 저장 프레임·기대 행동을 읽고, actor에는 현재 float32 관측만 pipe로 보냈다. actor argv는 worker/package 경로뿐이며 환경 객체·seed·track ID·info·reward·평가 로그·기대 행동은 보내지 않았다. 별도 `commit`·진단 worker·관측 뒤 GT 호출도 없다. 각 act가 자기 원래 기억을 갱신한다. replay 자료는 clean directory에 복사하지 않았다. 같은 머신 내부에서 실행에 필요한 ZIP member와 worker를 clean directory에 풀었으며 외부 파일 전송이나 새 실행 환경 생성은 없었다.

Python `-I -B`,비밀 환경변수 없는 명시적 env,닫힌 상속 FD,한 CPU/thread,패키지 내부 module origin/hash 검증을 적용했다. worker는 simulator import와 Python 파일 쓰기·허용 root 밖 open·socket·subprocess를 거부한다. 기존 native sandbox hash는377의 동결 hash와 같으며,소스에서 read root 밖 open·네트워크·자식 process·ptrace/process_vm 접근 차단을 확인했다. 허용 read root는 clean directory와 설치 runtime/library 경로다. 따라서 이 실행의 평가 로그·seed 자료 내용은 actor의 허용 read root 밖에 있다. 정책 AST에도 simulator/network/dynamic execution import 및 직접 open/eval/exec/compile 호출이 없다. 실제 actor의 Python audit 거부 이벤트0,simulator module 로드0이다. **메타데이터 syscall은 숨기지 않으며 hostile code에 대한 완전 보안 증명도 아니다.** 이 한계를 '어떤 파일의 존재조차 관측 불가'로 과장하지 않는다.

실행 전 plan에 저장237행동 한 번과 같은 actor reset 후 첫16행동 한 번,act cap253/reset cap2/native cap0을 고정했다. 무결성·입력·행동 parity·시간·메모리·격리·deadline 오류가 있으면 첫 실패에서 중단하고 자동 반복하지 않는 조건이었다. 실제 자격 실행은1회이고 오류0이다. 최초 shell 실행은 Python package 검색 경로 문제로 정책/plan 생성 전에 종료됐으며,소스 변경 없이 `python -m retry.qualification381_run`으로 실행 방식을 바로잡았다. 이 사전 launch 실패는 추가 actor·환경·native 비용0이며 별도 receipt에 남겼다.

새 비용은 **native0,환경 생성/reset/step0,actor act253·actor reset2,기존 affine head 평가253,학습0·source physics0·새 후보0·유료 자원0**이다. 자격 측정 wall2.456초·supervisor CPU0.547초·actor CPU1.923초이며 문서·코드 검토·게시 전체 시간을 포함한 수치는 아니다. **누적1,312,121 + 연구35,943 + 최종 예비84,000 = B1,432,064**, reserve 사용0. 비용은v399와 원장에 한 번만 반영했다. 현재 champion/rollback·365 거부 고정·기존 백업·사용자 변경·main·Participants는 보존했고372 개별 자료와297 case·SEALED identity/trajectory는 읽지 않았다. 기존 SEALED query metadata는 사용0·현재 단계 허용0이며 그대로다.

최종 SEALED 실행 계약은 아래의 **미실행 제안**이다. 이번381은 개봉 허가나 query allowance 변경을 하지 않는다.

1. 후보는 현재296 ZIP·18개 member·의존성·clean worker·native sandbox hash 하나로 동결한다. 현재 manifest와 이 자격 receipt를 연결하되 G5를 완료로 덮어쓰지 않는다.240 rollback ZIP/hash도 보존하고,최종 결과가 나쁘다는 이유로 다른 후보를 SEALED에서 다시 선택하지 않는다.
2. 기존 봉인16개를 그대로 사용한다. 새 split·난도 필터·재추출·추가 seed·중간 점수에 따른 정책/계수 수정은 없다. 실제 개봉 직전에 실행 권한과 기존 봉인 manifest 무결성·중복 배제를 확인하고 별도 실행 계약과 query 원장을 고정해야 한다. 이번에는 identity를 보지 않았다.
3. 후보당 도로별1회,기존 순서로 공식 종료까지 진행한다. 현재 로컬 wrapper의 raw8200/reset 후50/frame skip4 기준으로는 최대2038호출,16개 합계 **32,608 native**이므로84,000 예비 안이다. 이는 현재 로컬 실행기의 용량 산정이며 공식 서버 horizon 동등성 인증은 아니다. 최종 계약에서 사용할 runner/horizon을 소스로 대조·동결하기 전에는 실행하지 않는다.2000 smoke 상한을 공식 DNF 요건으로 대체하지 않는다.
4. 무결성·입력 유출·runtime/memory 초과·기술 오류·승인 종료이면 안전 중단하고 실제 사용만 차감한다. 정상 finish·실제 DNF·공식 truncation·protocol censor·기술 오류를 각각 기록한다. 오류 도로의 자동 재시도/seed 대체/예산 자동 확대는 없다. 부분 평가이면 미관측을 DNF나 통과로 만들지 않는다.
5. 완주 수와 분모를 먼저 보고하고 완주 시간은 완주 집합에 조건부로,damage·접촉·runtime·메모리는 별도로 보고한다. SEALED의 결과는 최종 동결 정책의 평가이며 새 정책 선택·튜닝의 피드백으로 쓰지 않는다. 자료·model·seed·개인 원문은 비공개로 유지하고 공개에는 집계·일반 코드만 둔다.

남은 준비 항목은 이 최종 runner/horizon·봉인 manifest 계약 연결,예비 차감·오류 회계와 종료 보고 경로의 동결이다. 부모 원문 확인의 출처는 기록했지만 이 실행기의 직접 원문 완독과 공식 서버 동등성은 미확인으로 유지한다. 새 머신·별도 자원을 만들어 이 공백을 임의로 메우지 않는다. 이미 실패한 방법은 재개하지 않았으며 연구 승인 마감 이후 새 실험·자동 연장도 하지 않는다.

[사전 등록·독립 프로세스 검증 코드](qualification381_run.py) · [집계·비용](qualification381_result.json)
