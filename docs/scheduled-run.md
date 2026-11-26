# 고정 구간 실행과 GitHub Actions dry-run

2026-11-27 구현. Supabase 설정 없이 수집·미리보기·검증을 실행할 수 있다. workflow는 로컬 파일로 준비했으며 원격 실행이나 예약 활성화를 완료한 상태가 아니다.

## 로컬 실행

```powershell
python -m briefing.job --scheduled-for 2026-11-26T08:10:00+09:00 --query '(반도체 OR 장비 OR 자동차)' --hours 24 --limit 5 --output output/scheduled
```

예정 시각의 정시를 조회 종료 시각으로 삼는다. 위 예시는 11월 25일 08:00~26일 08:00 KST를 조회한다. 실제 시작이 지연돼도 구간은 변하지 않는다. 명시한 예정 시각이 미래이면 실행하지 않는다. 위 날짜는 검증 예시이며 운영 때는 의도한 날짜를 지정한다.

결과는 `snapshot.json`, `preview.txt`, `report.json`이다. report에는 예정 시각·실제 시작·완료·지연 초·기사 수·소스 상태·실행 키를 기록한다. 본문은 기사 메타데이터만 포함하고 수신자·자격 증명은 artifact에 넣지 않는다. 모든 소스가 실패하면 실패 종료, 정상 빈 결과는 empty로 기록하고 발송하지 않는다.

GDELT에는 상대 timespan 대신 UTC `startdatetime/enddatetime`을 전달한다. RSS에도 같은 종료 시각을 전달한다. 정확한 시각이 있는 항목은 시작 포함/종료 제외로 다시 필터링한다. 날짜만 있는 RSS는 조회 날짜와 겹치면 포함하므로 실제 발행 시각이 cutoff 전인지 확인할 수 없다는 문구를 미리보기에 표시한다. RSS 최신 목록은 과거 구간 전체를 복원하는 아카이브가 아니다. [GDELT 공식 파라미터](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/amp/)

## GitHub Actions

`.github/workflows/briefing.yml`은 **dry-run 전용**이다. DB/SMTP secret을 주입하지 않으며 `--send` 경로도 없다.

- `workflow_dispatch`: timezone을 포함한 `scheduled_for`, 검색어, 24/72시간을 입력한다.
- `schedule`: 예시 시각 08:10 KST (`10 23 * * *` UTC). 저장소 변수 `BRIEFING_SCHEDULE_ENABLED=true`를 설정하기 전에는 예약 job을 건너뛴다. 시간은 운영 활성화 전에 확정한다.
- 기본 브랜치 반영 후 수동 실행을 먼저 검증한다. 각 실행은 15분 제한, 읽기 권한, 중복 실행 직렬화, 공식 action 커밋 고정 및 7일 artifact 보존을 사용한다.
- GitHub API에서 현재 run의 원래 `created_at`을 읽어 runner 재실행 시에도 같은 날짜 기준을 사용한다. 생성 시각 이전의 가장 가까운 08:10 KST 슬롯을 추정하며 차이가 6시간을 넘으면 자동 추정을 거부한다. 수동 실행에 정확한 날짜를 넣어 복구한다.
- 이 추정은 원래 cron 이벤트 발생 시각의 증거가 아니다. 하루 이상 늦게 생성되거나 아예 누락된 실행은 이 규칙만으로 복원할 수 없다. `slot_inferred_from_workflow_creation`을 report에 표시한다. 전체 누락 감지는 별도 감시 작업으로 남는다.
- report의 `workflow_creation_delay_seconds`는 추정 슬롯 대비 workflow 생성 지연, `runner_delay_seconds`는 생성부터 Python 작업 시작까지의 시간이다. 후자에는 runner 대기뿐 아니라 checkout·설치·테스트 준비 시간도 포함되므로 순수 큐 대기라고 해석하지 않는다.

DB 없는 dry-run은 같은 실행 키로 다시 수집할 수 있다. 네트워크 호출/내용의 중복 방지를 보장하지 않으며 실발송이 없으므로 전달 중복도 발생하지 않는다. DB를 연결한 경로에서만 저장된 본문을 재사용한다. GitHub concurrency만으로 영속 중복 방지를 대신하지 않는다.

## Supabase 연결 이후

1. 기존 001을 수정하지 않고 `002_scheduled_runs.sql`을 추가했다. `python -m briefing.db --migrate`가 번호 순서로 적용하고 checksum 변경은 거부한다.
2. 런타임 역할에 기존 권한 외 `GRANT UPDATE (status, source_results) ON briefing.runs TO briefing_app;`를 부여한다. SQL·권한·동시성 실통합은 아직 미검증이다.
3. `briefing.job`에 `--store-db`를 붙이면 수집 전에 실행권을 선점한다. 동일 완료 실행은 수집 없이 저장된 snapshot/본문을 재사용한다. collecting/failed 행은 자동 해제하지 않는다.
4. 실발송은 별도 명시적 `--store-db --send --to <수신자>` 조합에서만 가능하다. 고정 구간·설정 해시·수신자로 발송 키를 계산한다. DB 없이는 발송하지 않고, unknown/sending/failed를 새 키로 우회하지 않는다.
5. 수집 실패/중단 상태의 재개는 먼저 실행 종료와 발송 여부를 확인한 뒤 운영 절차로 처리한다. 아직 자동 재수집·대량 backfill·stale claim 해제를 구현하지 않았다.

Cloudflare로 이전할 경우에도 동일 예정 시각·검색 조건·구간을 전달해 같은 실행 키를 유지한다. 데이터 저장과 전송 로직은 교체하지 않는다.

## 검증 결과

- `python -m unittest discover -s tests`: 70개 중 65개 통과, 실제 PostgreSQL이 필요한 5개 보류.
- actionlint v1.7.12: `.github/workflows/briefing.yml` 검사 통과. 공식 release 체크섬을 확인한 도구는 Git 제외 `output/tools/`에만 저장.
- 경계 시각, UTC/KST 변환, 지연 실행, 변조된 plan, 수신자별 고정 키, 중복 수집/발송 차단, unknown 재시도 차단, DB 선점/저장 실패 시 무발송, 미래 슬롯 거부, source 전체 실패 처리, Actions 입력 검증을 모의 환경에서 확인.
- 실제 소스 dry-run: 11월 27일 06:20 KST경 수동으로 11월 26일 08:10 슬롯을 지정했다. GDELT HTTP 429, MSIT 정상 0건, MOTIR 정상 1건. DB/SMTP 호출 없이 미리보기 생성. 날짜 정밀도 항목이므로 정확한 08:00 이전 발행은 확인 불가. 증거: `output/scheduled-live-check/`.
- 부수 수정: 저장한 all-source-failed snapshot을 CLI로 재실행할 때 원래 소스 상태로 종료 코드를 계산하도록 수정하고 회귀 테스트 추가.

아직 하지 않은 것: GitHub hosted runner 실제 실행, Supabase 실접속/SQL 동시성/권한, 예약 실발송, SQLite 이관, 백업·정리·누락 알림. 이번 단계는 설정 없는 로직과 dry-run 검증이다.
