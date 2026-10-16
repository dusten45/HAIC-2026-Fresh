384 — 최종 계약과 검증 증거의 해시 연결

**준비용 연결 문서이며, SEALED 실행·개봉 권한을 부여하지 않는다.** 382 계약 원본과 296·240 rollback, query 허용량 0, 예비 84,000회를 보존했다. 동일 작업의 기존 384 산출물이 없는 상태에서 메타데이터 준비만 수행했다. 새 실험·inference·환경 생성·관측·성능·지형 조회는 없다.

| 연결 대상 | SHA256 |
|---|---|
|382 계약 원본 |`fa0dbb2e4ff624e5665b87c316d8d1c10d3fd6624b64b0a093e73766c14870d1` |
|296 ZIP |`0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937` |
|296의 18 member hash map |`b25e77a762ea53336e3b5ac63aaab8a1f371f467cd62fbdc71de4d990dac2f55` |
|240 rollback ZIP |`ae944d7d9e2fda02fc05936bcf245613a81fade5f2f3edc1f6ead68e9bed8d31` |
|381 qualification plan |`b5bdf17bad75b6a564f611f190e138f6892b0612faa97b45330ff617e26d33de` |
|381 공개 검증 결과 |`c5a88b4fca514141f0f48f12a8f9a6200cb24232f30b2cff20968fdd1b716f67` |
|원래 split manifest 전체 |`d0fea5b4a96937e5ff9cc9a2c856d8b2b3cc7fc0b6c831caf7bfda0b91977ca7` |
|SEALED16의 순서 있는 identity block |`b650238bc040f6a67f90cf8f99ffcb8d6a2b1053e456289628fd41051d431ba3` |
|383 추가 seed 증거 |`078d5847749155a3c10d3bb2c4820496c9669a288c7ebcdc280d11e432429103` |

identity block은 기존 원본의 `track_id, seed` 16개 목록을 순서 보존한 canonical JSON으로 만들었다. hash 계산 규약은 sort_keys=True, separators=(',',':'), UTF-8이다. seed 값과 원본 조건은 비공개다. 원래 manifest hash가 383의 비교 대상과 같은지 확인했다. 381이 실제 검증한 ZIP도 현재 296과 같고, 로드된 17개 policy module의 hash가 같은 member map에 연결된다. 18개 member에는 LICENSE가 포함되므로 로드 module 수와 모순이 아니다.

현재 interpreter는 **`/workspace/HAIC-2026-Fresh/.venv/bin/python`**로 고정한다. 실행 파일 SHA256은 `ec579de7512e84d960bc642a840de69c785c52d6adf89e3a15f51717b29be40f`이다. 셸의 기본 `python`은 다른 Python/NumPy 환경이므로 사용하지 않는다. 기존 venv의 Python 3.11.16을 확인했으며, 새 환경·패키지 설치·다운로드·외부 전송은 없었다.

| 현재 dependency snapshot | 버전 | 생성된 pyc 제외 파일 수 | content manifest SHA256 |
|---|---|---:|---|
|NumPy |1.26.0 |891 |`47408e99dfb5425572549c3f2031578969b2688bd5935660cd20d49b3509fe9b` |
|OpenCV distribution |4.8.1.78 |128 |`8369056c5dacc0abcb891424bfb87adbccc0f74ca8639ba75bce34bf9813ef04` |

각 배포판의 설치 파일별 내용 hash를 relative-path→SHA256 map으로 묶어 같은 canonical JSON 규약으로 hash했다. 실제 map은 비공개다. **현재 dependency bytes를 동결한 것이며, 381 시점의 전체 dependency bytes를 소급 증명하지 않는다.** 381에는 버전과 정책·worker·source hash가 있지만 이 전체 배포판 hash는 당시 기록하지 않았다. Python과 두 배포판의 snapshot은 전체 OS/shared library image 인증도 아니다. 381은 같은 머신의 독립 프로세스 검증이며, 공식 서버·새 머신 재현은 미검증으로 유지한다.

383은 보수적 노출 가능 seed 339개와 SEALED16의 seed·pair 교집합 0을 확인했다. case 출처 미상 blacklist 값 2개도 상위집합에 포함했고, 확인된 노출/native 단계 224개에 식별자 근거를 연결했다. 등록·반복 기록을 339개 독립 평가로 세지 않는다. 이 증거는 **보존된 메타데이터 범위의 seed/pair 비중복**이다. 다른 seed의 동일 지형 가능성, 미기록 실행, 모집단 독립성이나 정책 일반화를 입증하지 않는다. 382의 과거 seed 교집합 공백은 이 증거로 보완하되 계약 원본을 덮어쓰지 않았다.

집계와 실패 처리는 다음의 동결된 로컬 자격 경로로 연결한다.

1. **296 하나·기존 16조건·기존 순서·조건당 최대 2,000 wrapper step·frame skip 4.** 조건마다 독립된 원래 actor와 정상 reset을 사용하고 기억을 carryover하지 않는다. raw TimeLimit 8,200, reset elapsed 50, raw reset 51틱은 서로 다른 시간·비용 층위다. 2,038은 내부 수용량이고 외부 loop cap은 2,000이다. ZIP·계수·입력·정상 출력·원래 기억을 바꾸지 않는다.
2. **finish_time_s 존재를 먼저 판정한다.** finish에 따른 truncated=True도 완주다. lap은 round((finish_time_s-start_time)*1000)이다. 정상 2,000 loop cap에서 finish 없음은 로컬 max_steps DNF이며, 실제 crash/off_track과 기술 오류·승인 종료·임의 protocol 중단·미관측을 구분한다. 가짜 DNF 시간을 만들지 않는다.
3. **16개 계획 분모와 관측·미관측·검열 수를 함께 보고한다.** 완주 수를 먼저 표시하고 lap 평균·중앙값은 완주 조건에만 계산한다. damage·진행·runtime·RSS·invalid는 별도다. 240은 rollback으로만 보존하며 SEALED 비교·사후 후보 선택에 쓰지 않는다. 새 합격 문턱을 만들지 않는다.
4. **381의 동결 clean worker를 따른다.** exact shape (3,), finite, in-range를 요구하며 첫 invalid/runtime/IPC/메모리/무결성/승인 마감 실패에서 전체 batch를 중단한다. 해당 조건과 나머지를 technical·censor·미관측으로 나누고 retry하지 않는다. 새로운 clip·fallback·기억 보정은 추가하지 않았다.
5. **382의 공식 runner 설명과 실제 엄격한 자격 경로를 구분한다.** 공식 로컬 runner에는 flatten·유한 범위초과 clip·no-op·연속 invalid 10회·timeout thread 처리가 있다. 동결 clean worker는 그 예외 분기까지 같지 않다. 범위 초과도 이 worker에서는 자격 실패로 중단될 수 있다. 381은 정상 출력 경로를 검증했으며 이 예외 동등성은 검증하지 않았다. clip 어댑터를 추가한 뒤 같은 정책이라고 가정하지 않는다. 이 구분으로 382의 참조 설명과 실제 동결 경로를 연결했다.
6. **예비 배분은 84,000 중 296 최대 32,000·자동 retry 0·240 비교 0·미배정 보존 52,000이다.** 실제 env.step만 차감하고 actor/reset·warmup/raw ticks·CPU/wall은 따로 기록한다. 개봉 후 포장 오류도 같은 조건 재주행의 독립성을 복원하지 않는다. 내구 기록 복구와 물리 재실행을 구분한다.

기존 측정 기반 예상 시간은 다음과 같다. 새 benchmark는 수행하지 않았다.

| 기존 측정 | native / 측정 wall | 행동당 wall 환산 | 32,000회 사용 시 |
|---|---|---:|---:|
|296 평가 전체 |6,161 / 382.782초 |62.13ms |33.14분 |
|377 unchanged296 |237 / 16.804초 |70.90ms |37.81분 |
|375 fallback 후보 batch |4,799 / 400.776초 |83.51ms |44.54분 |

**최대 행동량을 모두 소모하면 약 33–45분**이라는 동일 머신의 과거 측정 환산이다. 기존 완주 길이와 비슷해 총 4,000–5,000행동이면 약 4–7분이라는 조건부 산정도 가능하지만, SEALED 난도·완주 길이를 미리 안다는 뜻은 아니다. observer·IO·후보 정책이 다르고 현재 최종 clean 경로를 새로 benchmark하지 않았으므로 실제 소요 시간 보장이나 hard wall 상한이 아니다. 기존 elapsed에는 reset/startup이 포함되어 cold start 16회를 다시 더하지 않았다. 실제 실행은 승인 마감과 각 호출 제한을 따르며, 이 추정으로 새 단기 중단창이나 일정 취소를 만들지 않는다.

남은 실질 준비는 두 가지다. **최종 개봉의 명시적 권한과 claim/query·실사용 비용·오류 기록 계약을 이 hash에 묶어 동결**해야 한다. 현재 query 허용 0이며 이 문서는 권한을 활성화하지 않는다. 또한 최종 실행·보고 어댑터가 이 binding의 정확한 interpreter·worker·패키지·manifest와 중단·집계 규칙을 소비하도록 연결하고, 실행 직전 해시 최신성을 확인해야 한다. 이번에는 어댑터를 실행하거나 자격 시험을 반복하지 않았다. 공식 서버·새 머신 미검증은 범위 한계이며 새 자원을 쓰는 추가 실험으로 임의 보완하지 않는다.

원문 출처는 부모의 전체 24장·적용계획 재독과 전달 발췌다. 소비 실행기의 직접 원문 완독은 미확인이다. 개인 원문·추출본·회고·seed는 공개하지 않았다. **새 native/actor/reset/env/model/학습/source physics/관측/성능/지형 조회/유료 자원은 모두 0**, 누적 1,312,121·연구 35,943·예비 84,000·예비 사용 0을 유지했다. 384 메타데이터 hash·산술 비용만 v403과 원장에 한 번 기록했다. 연구 전체 종료·일정 취소는 없다.

[연결·의존성·시간 감사 코드](binding384_review.py) · [binding과 시간 산정 집계](binding384_result.json) · [보존한 382 계약](final382_contract.md) · [383 증거](seed383_result.md)
