387 — 정산 전·후 요약과 CLI/query 상태의 불일치 수정

**정산 전 요약에서 성공을 게시하던 결함을 수정했다.** 기존43개와 새 보고 회귀21개, 총64개 검증 및 읽기 전용 metadata preflight를 통과했다. 386의 실행 준비 판정은 이 수정본으로 대체하며, 382·384 계약과296·240 artifact는 그대로 보존했다. SEALED 개봉·관측·성능·지형 조회나 실제 backend 실행은 없다.

| 단계 | 게시 규칙 |
|---|---|
|실행 종료·정산 전 |`summary-provisional-private.json` / `summary-provisional-public.json`만 생성한다. summary_phase는 PROVISIONAL_PRE_SETTLEMENT, accounting_status는 PENDING_SETTLEMENT이며 batch_qualification_passed=False다. 실행 자체의 성공 여부는 별도 execution_qualification_passed에 남긴다. 최종 파일 이름과 final marker는 아직 없다. |
|정산·query 종료 후 |정산 결과와 query 상태를 합친 FINAL_POST_SETTLEMENT 요약을 게시한다. 정산이 CONFIRMED이고 query도 closed_completed일 때만 성공을 허용한다. reconciliation과 정산 예외는 최종 실패로 표시한다. |
|최종 파일 |private/public의 immutable version 파일과 canonical summary-private/public.json을 쓴 뒤 summary-finalized.json을 마지막에 게시한다. marker에는 두 파일과 실제 query snapshot hash를 묶는다. |
|최종 소비·CLI |read_final_summary가 marker·파일·query hash를 확인한다. 원시 alias만으로 성공을 판정하지 않는다. 정상적으로 반환된 결과에 한해 CLI emitter는 같은 최종 redacted payload와 성공0·실패2를 사용한다. 정산이 예외를 다시 raise하면 실제 __main__은 emitter에 도달하지 않으므로,그 경로의 JSON·exit2는 보장하지 않는다. 예외 전파 규칙은 유지한다. |

정상·원장 drift fixture는 정산 반환값과 최종 파일·query 상태를 비교하고,그 반환값을 emitter에 전달한 JSON·0/2 반환 코드의 일치를 검증했다. 실제 CLI subprocess를 실행한 검증은 아니다. 정산 예외 fixture는 예외를 잡아 실패 파일과 query 종료를 확인한 뒤,파일의 결과를 emitter에 수동 전달했다. 따라서 예외 경로의 실제 __main__이 JSON을 출력하거나 exit2로 끝난다는 증거는 아니다. 원장 drift에서는16개 실행 결과가 정상이어도 accounting_status=RECONCILIATION_REQUIRED와 batch_qualification_passed=False가 최종 파일에 반영되고,query는 closed_aborted_no_retry·허용0으로 끝난다. 이전 prior에 기반한 전체 잔액을 게시하지 않는386의 규칙도 유지한다.

최초 provisional 파일은 이력으로 보존하고 최종 파일과 이름을 분리했다. 최종 public에는 조건별 행과 원시 예외 상세를 넣지 않는다. 정산 예외에서도 query 종료를 시도한 뒤 실패 요약을 게시하도록 연결했다. 게시 과정의 강제 종료·저장소 실패는 다중 파일의 동시 쓰기를 보장할 수 없으므로,최종 소비자는 last marker와 query snapshot을 검증해야 한다. canonical 파일 변조가 검출돼 성공으로 소비되지 않는 회귀도 통과했다. 파일 손상이나 미완료 게시를 자동 재실행으로 복구하지 않는다.

새 adapter SHA256은 `b9a21e0ff6d142eb2a5bc6caa8d96964aed7c015b3e58d536a716f53022efd0c`,revision387 준비 plan SHA256은 `d0ea124f0c4a29b4135089b257a817855f82b46cbd43630f99b9a7b112140a64`다. 진입점은 preparation_stage=387만 허용하고,새 template도 authorized=False·승인 참조 없음으로 유지한다. 이전385·386의 template과 보고서를 몰래 갱신하지 않았다.

준비 스크립트에 복사된 이전386 출력 경로 오류를 metadata preflight가 감지했다. 아직 커밋하지 않은386 공개 결과 파일을 보호 snapshot과 일치하는 HEAD bytes로 복원하고,387의 별도 출력 경로로 수정했다. 실행된 source와 원래 plan·수정 receipt를 보존했다. 완료된64개 검증과 비용 원장은 반복하지 않았으며,수정된 hash 연결로 metadata preflight만 다시 확인했다. 이전386 파일은 최종 git diff에 변경이 없다.

현재 stale success라는 알려진 기술 결함은 해소됐다. 388 문서 정정에서 actual exceptional CLI와 수동 emitter fixture의 보장 범위를 구분했으며 동작은 바꾸지 않았다. 실제 평가를 시작하려면 명시적 최종 개봉 권한과revision387의 정확한 hash·원장·예산 연결이 필요하다. 이번에는 활성 권한·실제 final 출력·개봉 marker를 만들지 않았다. SIGKILL·전원 종료·반복 interruption·저장소 실패에서의 내구 prefix 복구 한계,같은 머신 검증과공식 서버/새 머신 미검증의 구분은 그대로다.

새 native/actor/reset/env/model/학습/source physics/관측/성능/지형 조회/유료 자원은 모두0이다. 누적1,312,121·연구35,943·예비84,000·예비 사용0을 보존했다. 387 비용은v406·원장에 한 번 기록했다. 원문·개인 자료·seed·비공개 조건은 공개하지 않았고 연구 종료·일정 취소도 없다.

[수정 어댑터](final385_adapter.py) · [보고 일관성 회귀](final387_regression.py) · [revision387 준비 코드](final387_prepare.py) · [검증 집계](final387_result.json)

예외 CLI에 대한 현재 계약과 검증 한계는 [388 정정](final388_cli_scope.md)을 따른다.
