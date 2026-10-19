591 기술 검토 — 577 source13.20초의 native 개선 여부는 미검증

**577 한 후보의 별도 검증 질문을 제안하며, 새 실행은 하지 않았다.** 541 actual13.66초와577 source13.20초의 차이460ms는 서로 다른 실행 영역의 수치 차이다. native460ms 개선을 관측한 것이 아니며, 예전500ms 선택 문턱을 통과했다고 소급 주장하지 않는다. 이번 질문은 고정577 명령열이 기존 DEV native에서 엄격한 안전·재현성을 유지하며 양의 cold 개선을 내고 carry를 악화시키지 않는가다.500ms는 물리 안전 조건이 아니므로 새 계약의 필수 개선량으로 사용하지 않는다.

[새 제안 계약](validation591_proposed_contract.json)은 미실행·실행 승인 아님으로 표시했다. [현재 파일 확인 증거](validation591_evidence.json)와 [source0 읽기 도구](validation591_review.py)를 남겼다. 동역학/source·force·geometry 질의·FD·native 행동/reset/world 생성은 모두0이다. 일반 파일 읽기·해시·저장 행 대조만 했으며 그 읽기 검토 비용은 CPU0.279초/wall0.285초다. 문서 작성·Git 시간을 시뮬레이션 비용으로 주장하지 않는다.

확인한 증거와 증거의 한계

현재 실행기에서577 원시 tape에 직접 접근했다.5,606,751byte,166명령·661raw이며 SHA256은 `bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6`으로590 사전 pin과 일치한다. 명령 인덱스1..166, 모든 저장 raw의 global/index/4raw 관계와 명령 일치, 원래 strict 실패 flag 부재, 독립 exact/checkpoint_exact, 현재 source 코드·입력 pin을 확인했다. 전체8필드 checkpoint(root,visited,tracker,elapsed,global_raw,progress,launch,tracking)를 보존하고 있다. 원577 감사도 통과 기록이다. 새 force/기하 판정이나 tracker update를 실행한 것은 아니다.

[577 원 보고서](direct577_result.md)에서 독립 initial-source full replay는 공식 timestamp raw660/13.20초, confirmation raw661이고 선택된 계획과 root·force·이력·clock·visited·tracker·최종 checkpoint가 정확히 같다. 원시여유는 footprint0.501688531m, path2.999942798m, reference excess4.849999620m/s, tracking force1.058989978, body96.929067754m/s다. 이 매우 작은 여유는 native·섭동·pixel 일반화 인증이 아니다. 이후590 positive는304raw prefix의 일치를 추가 확인했을 뿐, whole cold native나 carry를 추가 검증하지 않았다.590의 새 형상 후보는 시간 비개선으로 닫은 상태를 유지한다.

이 근거가 현재 접근 가능하고 입력·구현이 일치하므로 **577 full cold source를 단순 중복 실행할 필요는 없다.** 후속 실행 직전에도 같은 pin·안전·661행·complete checkpoint와 기존 journal 등록을 먼저 확인한다. 유실·불일치가 생기면 무결성 blocker로 멈추며, 이를 새 cold 실행으로 조용히 대체하지 않는다. 원시 journal의 전체 chain을 이번에 다시 계산하지는 않았고, 기존577의71,713-event chain 감사와 현재 tape·구현·입력 확인을 구별한다.

541의27개 private input pin은 현재 모두 존재하고 hash가 맞는다. 실제 raw1,496개·행동 charge349개가 현재 남아 있으며 기존541 감사는 `SAVED_RECORD_AUDIT_PASS`다. 이번에는 이1,496행 전체의 force/기하 및 옛 감사 전체를 재실행하지 않았다. 검사 범위의 유실은 발견하지 않았으나 옛 감사의 모든 검증을 새로 했다는 뜻은 아니다. legacy518의 prefix1..47 기록도 모두 있고 before47 root는46 after root와 정확히 같다. 원시 자료의 존재·개수 확인과 과거 완전 감사의 권위를 나눠 보고한다.

541과577의 실행 계약 차이

[541 계약](joint541_contract.json)·[native 실행기](joint541_native_recovery.py)·[source carry 실행기](joint541_model.py)·[기존 감사](joint541_audit.py)를 읽었다.541은540 launch+539 cap90+537 full-state feedback 후보와538 baseline의 새 native cold 비교다. 새 baseline14.22초/후보13.66초,349행동 차감으로 연구23,107→22,758이었다. carry14.46초는 legacy before47에서의 **source 회귀 결과**다.541 native에 carry arm은 없었다. 따라서 “마지막 actual carry14.46”이라는 표기는 피해야 한다.

|항목|577의 현재 source 증거|541식 native에서 필요한 별도 확인|
|---|---|---|
|제어|166개 float32 고정 명령열, 시간 인덱스 open-loop|candidate는 같은 고정 명령만 재생; raw 관측으로 수정 금지.541 baseline은 원래 full-state feedback 유지|
|관측|저장 full root/contact/force와 모델 tracker/visited|live hull/wheel/joint·actuator/contact·force·RNG·tracker/clock/visited·pixels/damage/effects 진단. 기존 privileged DEV 권한이며 pixel-only 제출 결과 아님|
|초기 상태|515에서 수집한 source root·초기 visited·tracker|승인된 같은 DEV reset 내부1raw+warmup50raw=51raw 후 full identity 확인. source CP를 live world에 주입하지 않음|
|명령 전달|source에서 부호/actuator를 모델링|wrapper float32→float64, 매 raw steer(-a0)→gas(a1)→brake(a2), rear gas 상승≤0.1/raw, car.step(.02)→Box2D(.02,180,60)→clock/contact/공식 tracker→render|
|hold|동일 명령4raw,661에서 source 확인 종료|기본4raw 반복; 실제 종료/TimeLimit 발생하면 마지막 hold가 짧아짐. 이를664raw 강제 실행하거나 잘못된 tape 시각으로 보정하지 않음|
|완주|재구성 hull origin/velocity·visited로 동일 FinishLineTracker 법칙 적용|live 공식 hull/velocity·visited·tracker와 info.finished 필요. timestamp와 확인 raw를 분리하고 arc/chord 시간으로 대체 금지|
|안전|strict tracking1.059/reference4.85/footprint.50, 기타 원 조건|원 예측 게이트 및 실제 force1.25/reference5/footprint.25, clip·collision/damage·body·oracle·COM impulse·예측 오차 모두 확인|

541의 uncertainty.19와 internal buffer.001은 `1.25−.19=1.06`, 내부 admission1.059 관계다. 새 tape에 맞춰 이 여유를 줄이거나 oracle 오차를 안전 문턱 상향 근거로 쓰지 않는다. source oracle vector≤.05N, COM impulse≤.01m/s,4raw 예측 position≤.10m/speed≤.15m/s/angle≤.02rad/yaw≤.05rad/s/force ratio error≤.19, sensor phase·friction·payload·damage effect 일치도 유지한다. 실제 매 raw를 trace해 힘을 확인하고 첫 위반에서 멈춘다. 단, global hold1..24는 원 launch force2.5·clipping15%(hold24 완료 시 검사)를 적용하고 reference 초과는 진단만 한다.25부터 tracking force1.059·prefix clipping10%·reference4.85를 적용한다. 미래12hold 인증이24→25를 걸치면 실제 prefix의 launch/tracking 이력을 분리해 각 global hold의 원 기준으로 검사한다. 첫 launch를 tracking 문턱으로 잘못 거절하지 않는다. source13.20초와 native 공식 시간을 섞는 산식은 없다.

carry에 적용할 단일 정책과 선행 blocker

현재577을 일반 carry feedback 정책으로 부를 수 없다. 제안에서는 **같은 episode global hold index i에 tape[i]를 반환하는 유한 정책** 하나를 정의한다. cold는i=1, 정확한 legacy carry는i=47에서 시작한다. carry에서 tape를1로 다시 시작하거나 progress로 정렬하지 않는다. 조향·pedal 보정·fallback·사후 feedback 패치·마지막 명령 연장·새167번째 명령은 없다. 조건이 맞지 않는 carry는 정책 적용 범위 밖으로 멈춘다. 이는 두 고정 초기화에서의 좁은 명령 프로그램 검증이지 임의 carry에 유효한 정책 주장이 아니다.

legacy handoff는46행동/184drive raw 완료, episode3.68초, tracking[0,352]다. before47 checkpoint SHA는 `f214ec85a254121a332a5c4347b61efda6fb00cdbbed2bd9a716038dcca701b0`이다. 옛518 첫 arm 종료 raw1,149+둘째 reset51+46×4에서 **raw1384**를 식별했고, 실제 clock4.699999999999988초·visited43·오류0과 전체 tracker 필드가 저장돼 있음을 확인했다. 원 root·wheel gas/omega/joint·contact·clock·visited·tracker를 보존한다.541 source는 `tracker_for(...carry=True)`로 departure 상태를 재구성했으므로, 이를 옛 live tracker 전체의 exact clone으로 부르지 않는다. 새 carry 계약은 저장 실제 tracker와 ledger visited를 고정해 사용하고 이 차이를 명시한다.

새 source carry는 이 handoff에서 같은 tape47..166만 최대480raw 검사한다. 안전·공식 완주를 확인한 경우에만 같은 시작에서 독립 carry replay480raw 이하를 한 번 허용하고 full rows/force/history/visited/tracker/clock/CP exact를 요구한다. tape는166에서 끝나므로 전체 episode horizon은13.28초다.14.46초까지 명령을 임의로 늘리는 권한이 아니다. horizon 전에 완료할 수 있는지조차 미검증이며, 못 하면 이 후보의 carry 적용은 실패로 닫는다. 의미 있는 인덱스·handoff 매칭이 안 되면 simulation 전 blocker이며 feedback 패치로 해결하지 않는다.

native carry가 나중에 선택되면 새 reset 뒤 **옛518 명령1..46을 실제로 재생**하고 모든 상태·관측·actuator/contact·tracker/history가 저장 handoff와 일치해야 한다. 이 준비 prefix도 각 arm에서 행동46개/raw184개를 차감한다. 서로 다른 cold577 prefix의 after46을 legacy handoff라고 바꾸거나 source 상태를 teleport하지 않는다. prefix는 옛518 reference/안전 계약으로 검증하고47부터 각 arm의 등록 reference를 적용하며 새 기준을 과거 prefix에 소급하지 않는다.

제안한 순차 게이트·중단·승격

1. 기존 유효 full cold source 증거를 읽기로 재사용하고 정책·handoff·현재 hash를 고정한다. 새 carry source 한 번과, 성공 시에만 독립 carry replay 한 번을 한다. 모든 strict 안전과 공식 episode 시간≤14.46초를 요구하며500ms 개선을 요구하지 않는다.
2. 모든 source 게이트와 별도 native 실행 지시를 받은 뒤에만 새541cold→577cold→541legacycarry→577legacycarry 네 arm을 순서대로 수행한다. 이전 arm 실패·비개선·무결성/비용 중단이면 뒤 arm을 시작하지 않는다. 이번591은 이 네 arm을 실행하지 않는다.
3. fresh541cold가 등록 identity와 공식683raw/13.66초를 안전하게 재현해야 한다. 다르면 drift/incomparable로 멈추고 반복하지 않는다.577cold는 실제 공식 raw가 이 fresh baseline보다 작아야 한다. 따라서 양의 최소 관측 단위는1raw=20ms이며, 부동소수점 잡음이나 source 보간 개선은 native 개선이 아니다.500ms 문턱은 없다.
4. fresh541carry는 **새 native baseline**으로 측정한다.577carry는 이 baseline보다 악화하지 않고 episode≤14.46초도 충족해야 한다. 후자는 옛 source carry에서 가져온 명시적 보수적 목표이지 옛 native 관측값이 아니다. 실패·미완주·unsafe면 combined 승격은 없고 cold 개선이 있더라도 별도 결과로만 남긴다.
5. candidate는 actual root/history에서 다음12hold의 **앞으로 저장된 tape 명령**을 순서대로 새 인증하고 직전4raw 예측을 남긴다. 반복 상수 행동의 forecast나 chooser의 다른 action으로 검증 대상을 바꾸지 않는다. 끝에서는 남은 tape까지만 인증하고 완주 전 고갈이면 실패다. baseline541은 기존 chooser/FINAL을 유지한다. 첫 strict 실패·no certificate·source domain/body·실제 안전·기술/IO/무결성·시간/작업 상한 중 먼저 도달하면 전 과정을 멈춘다.

예산·원장·중복 없는 복구

[JSON 계약](validation591_proposed_contract.json)에 별도 source/native/internal/external/actual wheel 계수를 고정했다. 준비·감사 비용도 예약한다. 아래는 **후속 미실행 최대 예약량**이며 이번591의 사용량은0이다.

|항목|후속 source carry+조건부 replay|후속 native 네 arm|합계 상한|
|---|---:|---:|---:|
|model tick|960|195,000|195,960|
|external model force|3,840|900,000|903,840|
|internal model force|3,840|780,000|783,840|
|model force 총합|7,680|1,680,000|1,687,680|
|geometry pack|962|215,000|215,962|
|CPU / wall|60 /90초|6,000 /6,600초|준비·감사120/180 포함6,180 /6,870초|
|native 행동/reset/world instance/raw|0|1,332 /4 /4 /4,900|동일|

native arm별 행동 상한500/166/500/166=1,332다. raw는 각 world 최대1,225(원 TimeLimit1,224+내부 reset raw1)로 합4,900이며 warmup51×4도 포함한다. 실제 wheel response는 별도로 최대19,600회이며 model force에 숨기지 않는다. 기존 kernel hard cap200,000을 늘리지 않고 전체 model195,960을 적용한다. 이는 넉넉한 상한이지 완주 비용 예측이 아니다. 실제 남은 시간·예산으로 온전한 다음 단계와 cleanup을 예약할 수 없으면 시작하지 않는다. FD/solver/profile 생성0이다.

연구 잔액22,758, reserve84,000/사용0을 유지한다. native에서는 baseline·candidate·carry 준비 prefix를 포함한 모든 **시도한 env.step을 호출 전에 fsync 차감**하고 실패·부분/종료 행동도 환불하지 않는다. 최악1,332행동 후 연구 잔액21,426이며 reserve를 쓰지 않는다. reset/world/raw 시도는 별도 precharge하고 source preforce 실패·completed tick 및 external/internal kernel도 분리한다. 과거541349행동이나 재사용577 증거는 다시 차감하지 않는다.

각 phase/world는 배타적 STARTED를 먼저 저장하고 명령·pre-force·raw attempt·카운터를 내구 기록한다. 미확정 outcome도 시도 비용을 유지하고 이후 arm을 막는다. 실패 후에는 저장 증거를 읽어 정리하고 finally close/body·joint0을 확인하며 새 world/reset으로 재실행하지 않는다.541의 import 복구는 **STARTED/world/reset/action/raw 전부0임이 확인된 import 실패**였고 과학 재시도 선례가 아니다. 같은 조건이 입증된 경우에만 원 실패를 보존한 별도 등록을 제안할 수 있다. action 후 예외를 counter reset·같은 arm 재실행으로 복구하지 않는다.

남은 blocker와 보존

현재577carry 증거와 nativecold/carry 증거는 없다. 위 유한 정책의 carry 유효성·완주 가능성은 미검증이다. 후속 runner·fixed-future-tape 인증 구현과 전체 runtime/dependency hash 등록도 아직 없으므로, 이 문서만으로 native 실행 가능한 상태는 아니다. 이들은 이번591에 요청되지 않은 실행 준비·실험이며 자동 수행하지 않는다.

기술 검토와 제안 계약만 연구 브랜치에 보존한다. 지정 클라우드만 사용했고 원시 명령·geometry·seed·상태·영상·RNG·개인 자료는 공개하지 않는다. DEV 기존 조건만 대상으로 하며 HOLDOUT/SEALED/new condition/별도 유료 자원0이다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·기존 실패·백업과590 종료 판정을 유지한다. 승인 종료2026-10-20 10:01:55UTC를 연장하지 않는다.
