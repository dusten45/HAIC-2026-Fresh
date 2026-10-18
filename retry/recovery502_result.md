# 502 복구 조사 — 파일 실행 복구, 원시 자료는 미복원

이 문서는 복구 조사 당시의 범위다. 이후 사용자 지시로 연구를 재개했으며 [제동 응답 후보 시험](brake502_result.md)을 별도로 수행했다. 아래 원본 복원 조건은 원래35전이 사후분해에 대한 조건이며, 새 합성 제어 연구의 선행 조건으로 적용하지 않는다.

2026-10-18 UTC 조사. **502의 저장35전이 속도 오차 분해는 미수행이다.** 새 world/reset/적분/seed 생성/튜닝/과거 실험 재실행은 전부0이다. 이번 산출물은 복구 가능성과 재현 범위 조사뿐이다. 환경 시작 실패 기록과 기존501 실패 결과를 대체하지 않는다.

같은 환경에서 명령 실행이 돌아왔지만 초기 체크아웃은 `work`/main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`이었다. 원격 연구 HEAD `e0755373b9b4dfd6ae87c762e2e21bf846db4938`를 확인한 뒤 해당 커밋을 fetch하고 같은 연구 브랜치를 체크아웃했다. 저장소 재초기화/reset/파일 삭제/다른 환경·작업 생성은 하지 않았다. 원격의 기존 커밋을 부모로 하는 통상적인 추가 커밋만 만든다.

[497 정정 기록](diagnostic497_correction.md)과 [501 계약](screen501_contract.json)에서 유효 종료 **2026-10-20 19:01:55 KST**를 확인했다. 과거10월16일 표기는 현재 종료 근거가 아니다. 공개 정정 기록을 읽은 것과, 누락된 비공개 승인 원문·ID를 복원한 것은 구분한다. 새로운 인간 중단 지시는 확인되지 않았다.

## 실제 보존·접근 상태

| 대상 | 보존 근거와 현재 확인 | 실제 복원 범위 |
|---|---|---|
| 공식 main | 로컬 main과 원격 main 모두 위 `dfb7a2d…` | 원래 공개 시뮬레이터·entrypoint 복원 가능. 연구 입력이나 기록을 제공하지는 않음 |
| 연구 코드·계약·공개 집계 | 원격 `e075537…` fetch 성공. 501의 frozen code8개 및 공개 파일10개의 길이/해시 검사가 모두 일치 | 구현·정적 규칙·공개 결과·한계를 다시 읽고 검사 가능. 과거 실행 재검증과 다름 |
| 501 원시 기록 | [당시 보고서](screen501_result.md):1147파일/86,200,874B, fullstate186·rawtick734·hold bundle184. 당시 `/tmp` 한 벌만 보유, 새 archive/외부 보관 기록 없음. 현재 등록된 raw 디렉터리 없음 | 복원 안 됨. 후보35전이·140틱의 시간별 force/omega/속도 대조 불가 |
| 501 private control·입력·retention map | 등록된 private 상위 디렉터리 없음. 고정 line/model·pace·P4 nodes·source manifest·logical alias/version map·private 원장에 접근 불가 | public digest로 내용이나 참조 파일을 생성할 수 없음 |
| 472/473 receipts·root·RNG | [472](transfer472_retention.json), [473](compare473_retention.json)는 원본 검증 당시의 집계이며 새 archive0·workspace raw copy0을 명시. 해당 private 경로 없음 | 기존 source/root 자격을 새 입력에 이전하거나 298 native receipt를 재검증할 수 없음 |
| 463의 과거 private 압축 백업 | [retention receipt](transfer463_retention.json)는 당시 두 archive 합151,276,681B와 전체 member 검증을 기록 | 공개 receipt만 접근 가능. 현재 접근 가능한 archive 또는 지속 파일ID를 식별하지 못함. archive bytes를 복원했다고 주장하지 않음 |
| 현재 작업의 첨부용 로컬 경로 | `/workspace/library-files`, `/workspace/scratch`, `/workspace/shared/downloads`에 파일0 | 현재 제공된 첨부 원본 없음. 이 경로명 자체가 영속 보관을 보증하지 않음 |
| 같은 GitHub 저장소의 Actions artifact·Release | 공개 API 각각 HTTP200, artifact `total_count=0`, release 목록0; 기준 커밋에 workflow 파일0 | 해당 두 저장 방식에는 현재 검색 가능한 보관본 없음. 다른 계정·비공개 서비스까지 없다는 뜻은 아님 |
| ChatGPT Library/Project 첨부 등 계정 보관본 | Library의 영속 파일 기능은 안내되어 있으나 이번 세션에는 Library `list/search/read/prepare_materialize` 도구가 노출되지 않음. 기존 파일ID·첨부 참조도 전달되지 않음 | **존재 여부 미확인**. 임의 ID나 다른 실행기 경로를 만들어 접근하지 않았으며, 현재 조회 불가를 계정 전체의 부재로 단정하지 않음 |

Actions와 Release 조회는 같은 기존 저장소의 `/repos/dusten45/HAIC-2026-Fresh/actions/artifacts?per_page=1`, `/releases?per_page=1`에서 수행했다. raw 파일 전송·첨부·업로드·다운로드는0이다. 공개 코드 fetch와 비공개 원시 파일 전송은 구분한다. 기존에 확인한 전체 경로 검색은 반복하지 않았고, 위 등록 경로와 첨부용 경로만 확인했다. 시스템·다른 사용자·다른 실행기 경로는 탐색하지 않았다.

## 공개 자료만으로 가능한 재구성과 불가능한 재현

남은 코드로 float32 명령 매핑, `Car.step`의 엔진→제동→접촉력→회전 반작용 순서,4×20ms hold, canonical projection, codec/content/chunk 형식, 원래 source binding 검사와 중단 규칙을 정적으로 확인할 수 있다. 공개501 집계의 factual149holds 통과와 candidate35holds 뒤 exactEMPTY_SET도 **과거 보고된 결과**로 보존할 수 있다. 이러한 읽기·해시 검사가 같은 물리 결과를 다시 검증한 것은 아니다.

`run501.py`는 private frozen line/model·pace·projected nodes를 읽는다. `law473.root_inputs473`는 과거 native pre23의 full state/controller/ledger와 global RNG pickle 및 factual 명령을 요구한다. 이들은 private receipts/계획에 있으며 공개 소스의 생성 규칙은 그 실현값을 담고 있지 않다. line 계산에도 geometry snapshot·model 계수, pace 계산에도 동결된 private 학습 계수, P4 계산에도 해당 원래 입력이 필요하다. 일부 물리 상수나 집계 scalar가 남았다는 사실로 이 입력들을 대체할 수 없다.

따라서 코드·입력 생성 알고리즘·집계·receipt hash만으로 **원래 실험 identity/seed/root/RNG/경로/명령 전이를 복원할 수 없다.** SHA는 나중에 찾은 파일을 인증하는 값이며 소실된 bytes를 되살리는 백업이 아니다. 같은 seed를 나중에 찾더라도 그것만으로 controller history/root ledger/RNG·warm-start/broadphase 이력까지 동일하다고 할 수 없다. 원래 snapshot에도 solver warm-start/broadphase 미복원이라는 기존 한계가 있었다.

원래502를 저장 분석으로 이어가는 데 필요한 최소 복원 묶음은 후보35전이의 authority/fullstates,35 hold bundles와140 direct posts/해당 tire·hull 관측, 모든 codec content/chunk/state 참조의 닫힌 집합, logical→physical version map 및 길이/SHA manifest, source/input binding, 고정 line/model·pace·P4 입력이다. 원래 source scope를 재확인하는 receipt도 필요하다. 실제 복구본은 먼저 read-only 인증한다. 이 저장 분석 자체에는 새 seed 추첨이나 RNG를 사용한 시뮬레이션이 필요 없다. 반면 기존 물리 실행을 다시 만드는 일은 별개이며 원래 root/RNG bytes 없이는 불가능하다.

501의 첫-world marker도 private 기록과 함께 접근 불가다. **marker가 현재 없다는 이유로 `run501.py`를 다시 실행하거나 재시도 권한이 생기는 것은 아니다.** 501 패키지는 이미 닫힌 상태를 유지한다. 502의 마지막0.847159m/s·최대2.130529m/s 오차는 남은 공개 집계일 뿐이며, 이를 원인별 수치나 새 오차 상한으로 분해하지 않았다. 후속 물리 후보 선정 역시 이번 조사로 완료했다고 하지 않는다.

## 원본을 찾지 못할 경우의 최소 계획 — 제안만

1. 사용자가 기존 대화/Project/Library/본인 백업에서 **실제 archive 또는 첨부 파일**을 찾을 수 있는지 확인하고, 지원되는 경로로 직접 제공한다. Codex가 파일을 대신 전송·첨부하지 않는다. 원본 묶음이 돌아오면 기존 reader와 capture/writer를 그대로 사용해502의 CPU120초/wall180초/파생16MiB 계약으로 저장 분석만 재개할 수 있다. native action 연구 차감0이다.
2. 원본이 없으면 원래501/502의 재현이 아닌 **새 DEV source 재구축**으로 별도 등록해야 한다. 최소 전제는 사용자가 확인 가능한 DEV case identity와 동결 controller 입력을 제공하거나, 이들을 새로 만드는 범위를 별도로 정하는 것이다. 원래 private 원장과 split 노출 기록을 대조하기 전에는 공개 잔액으로 새 원장을 만들어 집행하지 않는다. 사라진 HOLDOUT/SEALED 목록을 추측하거나 열지 않는다.
3. 위 입력이 공급될 때의 작은 source smoke 제안은 native reset1회, prefix22actions 뒤 root를 저장하고 factual suffix16actions를 수집하는 **native 최대38actions**, 같은 새 root에서 기록 명령16holds를 재생하는 **model1world/64ticks**다. 기존 source 비교 허용오차·시간/이산/ledger 검사를 재사용하고 첫 identity·비용·필드·모델 불일치에 즉시 중단한다. retry·튜닝·추가case·완주/승격 주장은 없다. response 수집에는 휠의 각 raw tick 방향·속도·omega를 엔진/제동 전후와 force 반작용 전후로 구분하고, applied/clipped force 및 hull/assembly COM 시점을 명시해야 한다. 과거 누락을 새 측정으로 채웠다고 하지 않는다.

비용은 조건부이며 승인·실행이 아니다:

| 제안 단계 | 연구 action 예상/상한 | 별도 물리·계산·저장 상한과 한계 |
|---|---:|---|
| 원본 복원 후 원래502 saved-only |0|CPU120s/wall180s/파생16MiB, 새 물리0. 전송은 사용자 직접 |
| 입력이 제공된 새 source smoke |최대38|native reset1회·최대203rawticks(51reset tick 포함), model1world/16holds/64ticks. CPU120s/wall180s·새 raw128MiB·free reserve512MiB를 제안; 실측 완료시간 약속이 아님 |
| case/frozen profile/학습 계수까지 모두 새로 생성 |**현재 신뢰성 있게 산정 불가**|다수 과거 실험을 재실행하는 계획은 만들지 않음. 위38actions에 입력 생성·탐색·전체 완주 비용이 포함된 것으로 해석하면 안 됨 |

기존472 회계에서 연구 차감 단위는 시도한 native wrapper action이며 reset·model tick은 별도 집계다. 공개 최종 잔액26027에서 조건부38action을 전부 차감하면 **25989**, 예비84000/used0을 유지한다. 이번 조사에서 실제 차감은0이다. 원래 v495 원장 bytes는 복원되지 않았으므로 이것은 공개 잔액에 대한 제안 계산이며 원장 정합성 재검증 결과가 아니다.

source smoke raw 저장 추정은 공개 [471 metadata](design471_next.json)의 과거 native392413.371B/rawtick·model93191.314B/tick에 `(203*native+64*model)*1.25+16MiB`를 적용한 약123,807,415B다. writer/schema 차이로 보장되지는 않으며128MiB를 넘기기 전에 중단해야 한다. CPU/wall은501의 계측 IO 비용과 구분한 상한 제안이다. model.step 단독 시간을 전체 작업 시간으로 외삽하지 않았다.

## 앞으로의 비공개 영속 보관

`/tmp`뿐 아니라 현재 `/workspace`에만 둔 archive도 호스트 복구 뒤 존재가 보장된 것으로 취급하지 않는다. 다음 작업 전에는 사용자가 지원되는 비공개 Library/Project 첨부 UI 또는 본인 관리 저장소에서 보관·재다운로드를 실제로 확인할 수 있는 경로를 정해야 한다. UI가 지원하는 형식·크기에 맞춘 archive/분할 파일로, raw 참조의 전체 닫힌 집합과 private 입력/identity/RNG/ledger·source snapshot·실행 계약·logical map·member 길이/SHA를 함께 보관하는 방식이다. 이것은 지원 방법에 대한 제안이지 기존 보관본의 발견 또는 업로드 성공 보고가 아니다.

Codex는 허용된 로컬 묶음·manifest 준비까지만 수행하고 **전송·첨부는 사용자가 직접** 한다. 영속 보관 완료는 사용자 제공 파일ID/버전 또는 첨부 참조와 실제 업로드 성공·재다운로드 SHA 검증으로 확인해야 한다. 로컬 tar 생성·fsync·해시 검증만으로 완료 처리하지 않는다. 짧은 단계별 묶음을 보존해 호스트 수명에만 의존하는 긴 실험열을 피한다. raw/seed/state/RNG/개인 원문·회고는 공개 Git에 올리지 않는다. 공개 Git에는 코드·계약 요약·집계·검증 상태만 둔다.

## 이번 조사 검증

[정적 inventory 코드](recovery502_inventory.py)는 연구 모듈을 import하지 않으며 고정 공개 receipt와 명시한 경로만 읽는다. [실제 inventory](recovery502_inventory.json): frozen code8개와 공개 receipt10개 모두 일치, 필요한 private 경로10개 전부 부재, main ref 불변. inventory 자체 CPU0.007158s/wall0.018108s이며 대화 전체·Git/network 조사 비용의 실측이 아니다. 새 산출물은 이 보고서·inventory 코드·JSON뿐이다. 과거 source/결과/실패기록은 변경하지 않는다. 완료하지 않은502 오차 분석을 commit했다고 주장하지 않는다.
