601 — 정확한 margin 재사용으로 단일 core 7.963→6.934초, 여전히5초 초과

저장598 hold148만 사용했다. 실제 choose는 **계측1회·정상 최적화1회,합2회**이며 추가 후보·반복 튜닝·재호출은 없다. 원537 trial 수/horizon/정밀도/문턱/정책/동역학/숫자 연산 순서를 유지했다. 원kernel200000·choose max_ticks180000과 모든 body/force/clip/geometry/비용 gate도 유지했다.

첫 cProfile 호출은CPU21.440597/wall21.459842초였다. 이는 **계측 오버헤드를 포함하므로 정상 latency나 속도 향상의 기준으로 쓰지 않는다**. 기록된 함수 self 시간의 분류는 아래와 같다. builtins 등은 별도이며,core와self합계의1.924초 차이를 미배분으로 남겼다. 따라서 이 표는 정상 호출 시간을 완전히 분해한 추정치가 아니다.

|계측 함수 self 시간 분류|기록된 시간|
|---|---:|
|geometry·path query|12.203s|
|상태 복사·dataclass 할당|1.241s|
|물리·body|0.168s|
|정책·report·admission|0.080s|
|identity·계측·budget|0.762s|
|builtins 등 기타|5.081s|

가장 큰 비용은 full body/road/obstacle margin 계열이었다.919회 margin의 누적16.288초(road margin15.770초),point_segment4485256회의 누적4.974초는 **서로 겹치는 계측 시간**이다. asdict6283회 누적1.441초와report result31회 self0.000060초도 저장했다. 물리 wheel_response7176회는 누적0.076초였으며 호출·budget 계측 시간과 구분한다. 원시 profiler 기록은 비공개다.

선택한 변경은 [단일 호출 안의 정확한 margin 결과 재사용](reuse601.py) 하나다. polygons가 읽는center·angle·levers·wheel headings 전체를 finite binary64/type/signedzero 보존 키로 만들고,roads/boundary/obstacles 문맥을 별도 불변 tuple로 소유한다. miss에서는 원 margin을 원래 순서로 계산하고,hit에서는 같은 불변 float를 반환한다. 논리 query와후속 안전 gate는 매번 실행·청구한다. cache에는 root/action/history/report를 저장하지 않고 종료 시 모두 비운다. 순수 검사8개가 원본 mutable 입력과의 별칭 분리·중첩 불변성·signedzero·다른 trial/호출과의 격리·잘못된 문맥 거절·정리를 확인했다.

정상 최적화 호출은 **CPU6.931312/wall6.933844초**였다.919개의 margin query 중145회를 재사용하고774회 실제 margin 계산을 했다.600의정상 wall7.962848초 대비 한 표본 차이는1.029004초/12.92%다.601에는전체 wheel 반환값 보관과aggregate guard 장부가 추가되어 있어 동일 계측의 반복 paired 추정은 아니며,일반적인 속도 향상률로 확대하지 않는다. 계측21.46초와의 비율도 사용하지 않는다.

두 호출 모두600의action bytes·전체report/trials/FINAL과906시도888완료·geometry2641을 재현했다. **각 호출의4538개 전체 raw 진단 JSON은600과파일SHA까지 동일**하다.888개 post-tick 상태·body/force비율·projection/footprint 진단도 포함한다.추가로 외부3624·내부3552의전체 wheel_response 반환값7176개가 계측 원본과최적화 사이에서파일SHA까지 동일했다.600은전체 wheel 반환값을 기록하지 않았으므로,그 부분의 비교 기준은이번 계측 원본이다.기존600 raw 상태/힘 진단 일치와이를 구분한다. 이 정확성 범위에서 최적화 helper를 채택하되 주행 incumbent/일반정책으로 승격하지 않는다.

합계model1812시도/1776완료,외부force7248·내부7104·합14352,geometry5282로사전상한3072/3072·force24576·geometry10000 이내다. 준비·감사까지CPU44.808501/wall43.251329초(각 phase 보수5초 포함),최종요약용5초를더해도240/300 이내다.순수 검사14개와읽기 전용 감사30항목을통과했다. native/world/reset/행동/solver/FD/새seed/HOLDOUT/SEALED는모두0이다.

재사용 가능한 근거는 불변 geometry 문맥과 완전한 의존성 키 아래에서 원시 결과를 그대로 보존하면서145회의비싼계산을제거했다는 점이다. 이 한 입력의core도여전히5초를넘으므로pixel·상태추정·thread/marshalling·실제Agent.act전체준수를주장하지 않는다.11초대주행가설은미검증,기존단일privileged cold DEV13.22초는그대로다. 잔액22211·reserve84000/사용0·승인종료2026-10-20 19:01:55KST와 main/Participants를 보존한다. 후속 실험은 실행하지 않았다.

[계약](profile601_contract.json),[최적화 사전 동결](profile601_optimized_contract.json),[계측 집계](profile601_profile_result.json),[정상 검증 집계](profile601_optimized_result.json),[감사](profile601_audit.json),[실행 코드](profile601.py)를 보존한다.입력/명령/좌표/전체report/원시힘·상태/profiler는Git밖비공개이며기술코드·집계만커밋한다.
