# 469 — 두 whole arm 후속 설계, 공간 gate 미통과로 적분0

**qualification·whole arm·model/world·actual/reset 모두0으로 종료했다. 남은 구간의 이득 지속 여부는 아직 측정하지 않았다.** 기존 파일 삭제/이동·기존 압축본 변환·새 환경·유료 사용도0이다. 467 gzip adapter를 끼워 넣거나 reserve/보존 범위를 줄여 맞추지 않았다.

같은 pre126에서 Original/P4의 공통 첫 fullgas 뒤 기존 point-FF 고정 법칙을 각각 자기 model finish 또는 최대70행동까지 한 번 비교하는 계약을 정했다. SourceC의 phase·자기 tracker를 유지하고 P4 FINISH_CONFIRM도 자기 projected nodes[-1]을 target으로 사용한다. query guardian·neutral 구제·랭킹은0이다. raw tick의 기존 물리·진행·numeric 기준을 완화하지 않으며 unsafe는 그 고정 법칙의 결과로 종료하고 허용되지 않은 정의역은 기술 중단한다. cap70에서 pending이면 확인 행동을 추가하지 않는다.

기존 통합 source/root qualification의1458ticks/41worlds(선행35+두 arm의 독립 H13/held6)를 그대로 포함하고, 새 whole parent 두 개의70×4×2=560ticks/2worlds를 더해 **계획2018ticks/43worlds**다. hard2048/43·CPU180초/wall300초·actual/reset0 안에 들어가며 여유는30ticks/0worlds다. 새 held·capture·probe world는0이고 관측은 같은 parent에서 한다. source/root 반복 통과를 whole arm 반복 성공으로 표기하지 않는다. H13 cohort에 이어 쓰거나 observer tail barrier를 우회하지 않는다. whole parent의 initial_count0 관측 경로와 generic H13 observation을 사용할 설계다.

공간 판정은 최신468의 full raw126,087,848B/1353ticks=**93,191.31411677753B/tick**을 적용했다. hard2048ticks에1.25배, 모든43world의 최신 header 합777,215B(자기 reference proof 포함), 새 manifest 증가119B의3배, world당16KiB, plan2MiB/raw metadata16MiB를 넣었다. 미작성 생산 모듈의 manifest를 위해4KiB 추가 여유를 구분했다. workspace에는 전체 raw1.1배+metadata32MiB+plan2MiB+reserve512MiB를 배정했고 압축 이득은0이다. bytes는 유리수로 계산한 뒤 최종 필요량을 올림했다.

사전 gate에서 실제 free는 **tmp3,412,004,864B / workspace874,176,512B**였다.

| workspace 산정 | 필요한 bytes | 부족 bytes |
|---|---:|---:|
| 더 낙관적인 옛 header770314·source 증가0 | 892,921,857 | 18,745,345 |
| 최신 header·현재 source 증가 반영 | 893,265,161 | 19,088,649 |
| 미래 manifest4KiB 여유까지 포함한 등록 상한 | **893,846,383** | **19,669,871** |

등록 상한의 tmp 요구량은828,983,537B로 부족0B다. **workspace만 미통과**이며 새 source를 추가하지 않는 낙관적 하한도 부족하다. 따라서 실행 코드를 억지로 구현하거나 qualification을 시작할 이유가 없다. 전체 산식과 최종 올림은 독립 검토에서도 세 경우 모두 정확히 일치했다. [설계·수치 계약](design469_next.json), [재현 계산 코드](design469.py).

향후 공간이 충족되는 별도 실행에서는 각자의 tracker event가 같은 parent에서 확인된 finish bracket이 주 지표다. 양쪽 모두 안전하게 완료한 경우에만 Original−P4의 전체 남은 구간 bracket을 계산하며, 기존+60m 이득을 더하지 않는다. 미완료 시 censor·common root+60m 간격의 관측 경계·최초 실패·종료 progress/speed/phase와 각자/공통 원래 reference 감속부채를 분리한다. 첫 위반 이후를 안전한 관측으로 인정하지 않는다. fixed-root 모델 결과를 native나11초대 달성으로 외삽하지 않는다.

보호18파일·v475 예산·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·기존 원본/백업은 유지했다. 최신 종료 **2026-10-20 19:01:55 KST**와 실제 사용자 연장 근거의 SHA를 계약에 함께 남겼다. 이번 결과는 정책 반증 실패가 아닌 적분 전 자원 중단이며 새 실행 권한을 발행하지 않았다.
