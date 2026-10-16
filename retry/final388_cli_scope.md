388 — exceptional CLI 검증 주장과 계약 범위 정정

**문서 정정만 수행했으며 동작은 변경하지 않았다.** 387에서 stale success 결함은 해소됐다. 다만 정산 예외 fixture가 실제 CLI의 JSON 출력·exit2까지 증명한다는 주장은 과했다. 아래 구분이385·387 보고서의 포괄적인 CLI 표현을 정정하며,382·384 원본 계약은 보존한다.

| 경로 | 실제 동작 | 검증 범위 |
|---|---|---|
|정상 정산으로 결과가 반환됨 |__main__이 emit_cli_summary에 도달한다. 같은 최종 redacted payload를 출력하며 성공0을 사용한다. |synthetic fixture는 반환값·최종 파일·query 상태와 수동 emitter의 JSON·코드를 비교했다. 실제 CLI subprocess 검증은 아니다. |
|원장 drift를 reconciliation 결과로 반환 |실패 최종 파일·query 종료 후 결과가 반환된다. __main__은 emitter에 도달해 실패 JSON·exit2를 사용한다. |fixture는 이 반환 경로와 emitter 함수를 확인했다. 실제 프로세스의 전체 CLI 실행을 시험하지 않았다. |
|정산 예외를 실패 파일 게시 후 다시 raise |settle_live가 실패 요약 게시와 query 종료를 시도한 뒤 예외를 다시 전달한다. run_live도 반환하지 않으므로 __main__은 emitter에 도달하지 않는다. |fixture가 예외를 잡아 파일·query를 확인한 뒤 emitter를 **수동 호출**했다. 이는 저장된 실패 결과를 emitter가 표현할 수 있다는 검증이며,실제 exceptional CLI의 JSON·exit2 보장은 아니다. |

일반 미처리 예외의 실제 CLI는 Python 예외 전파·stderr traceback·비성공 종료 경로를 따른다. 모든 예외를 JSON·exit2로 정규화하는 계약은 없다. SystemExit·KeyboardInterrupt의 기존 전파 규칙도 별개이며,그 모든 경로의 exit code를2라고 주장하지 않는다. stderr의 원시 traceback은 redacted public summary와 다르므로 공개 결과 파일로 취급하지 않는다. 공개 저장소에는 이를 옮기지 않았다.

정산 예외 fixture가 실제로 입증한 것은 실패 private/public 요약 게시,query의 실패 종료와 허용0,저장된 결과에 대한 수동 emitter의 표현이다. 실제 __main__ 예외 경로에서 emitter 호출·JSON 출력·정확한 exit2는 검증하지 않았다. 실제 subprocess 실행이나 새 fixture를 수행해 주장 범위를 넓히지도 않았다.

현재 확인된 기술적 결함은 stale success였고387에서 수정·회귀 검증됐다. 여기서 정정한 exceptional CLI 표현은 **명시적인 계약·검증 한계**이며,안전한 실패 파일과 예외 전파를 새 동작으로 바꿔야 할 결함으로 재분류하지 않는다. 비성공 결과를 성공으로 해석하지 않아야 하며,기계 판정은 최종 marker·파일·query 검증을 기준으로 한다. 최종 파일 게시 자체가 완료되지 않은 강제 종료·저장소 실패의 내구 prefix 복구 한계도 유지한다.

실행 준비의 코드 연결과 기존64개 synthetic 검증·387 metadata preflight 이력은 유지한다. 이64개는 함수·fixture 검증이며 actual exceptional CLI의 end-to-end JSON·exit2 인증으로 세지 않는다. 이번에는 코드·해시 연결·비활성 권한·query·예산을 변경하지 않았고 기존 검증을 재실행하지 않았다. 알려진 미해결 기술 차단 항목을 새로 확인한 것은 아니며,실제 개봉에는 별도 명시적 권한이 필요하다.

**SEALED 미개봉·새 native/actor/env/model 실험0**,연구35,943회·예비84,000회·예비 사용0을 보존했다. 문서 작업에 새 실험 비용 줄이나 예산 버전을 만들지 않아387의 비활성 hash 연결도 유지된다. 연구 종료·일정 취소는 없다.

[정정된387 보고서](final387_result.md) · [실행 어댑터](final385_adapter.py) · [fixture source](final387_regression.py)
