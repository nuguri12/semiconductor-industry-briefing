# PostgreSQL 연결 준비

## 현재 선택 — Supabase Free (2026-11-27)

사용자가 Supabase로 진행하기로 결정했다. 이전 Neon 권고안을 대체한다. PostgreSQL 스키마와 psycopg 코드는 재사용하며 실제 Supabase 프로젝트 생성·접속 검증은 아직 수행하지 않았다. IPv4 실행 환경에서는 shared **session pooler**를 기본 연결로 사용하고 TLS verify-full 및 인증서 구성을 확인한다. Supabase REST API 키가 아니라 PostgreSQL 접속 문자열이 필요하다.

사용자의 최신 결정에 따라 우선 GitHub Actions `schedule`로 예약하고 `workflow_dispatch`로 수동 실행한다. Python 수집·정규화·SMTP 실행도 GitHub Actions, 영속 상태는 Supabase가 담당한다. Cloudflare는 지연·누락 개선이 필요하다고 관측된 경우의 후속 이전안이다. 어느 트리거도 아직 배포하지 않았으며 정확한 시각의 이메일 도착을 보장하지 않는다.

공통 트리거 계약: 예정 실행 시각에서 고정된 `scheduled_for`, `window_start`, `window_end`, `run_key`를 계산한다. 재호출은 같은 키를 유지하며 실제 job 시작 시각으로 조회 구간을 바꾸지 않는다. 예정 시각·workflow 생성·작업 시작·발송 완료를 구분해 기록한다. `briefing.job`, `briefing.schedule` 및 migration 002로 계약과 collecting 선점을 구현했다. 실제 DB 검증은 대기 중이며 실행법과 한계는 [예약 실행 안내](scheduled-run.md)를 따른다.

검증 순서: 수동 dry-run → Supabase 통합 및 실제 수신 검증 → 예약 dry-run 관찰 → 예약 실발송. 초기 관찰은 7회 실행을 제안하고 허용 지연·누락 기준은 운영 설정에서 확정한다. 기준 초과가 확인되면 원인이 schedule 이벤트 지연인지 runner 큐 대기인지 구분한다. 전자라면 Cloudflare Cron → workflow_dispatch로 이전하고, 후자라면 실행 환경도 별도로 검토한다. Cloudflare 이전 시 기존 schedule을 먼저 비활성화하고 동일 run_key와 DB 중복 방지 규칙을 유지해 이중 발송을 막는다.

DB/SMTP 비밀값은 GitHub 실행 환경에 둔다. 향후 Cloudflare로 이전할 때만 저장소 Actions 권한으로 제한한 GitHub 토큰을 Worker secret에 설정한다. 공개 HTTP 트리거는 추가하지 않는다. Cloudflare cron은 UTC이며 설정 전파 중 누락될 수 있어 이전 시 수동 검증을 수행한다. [Cloudflare Cron](https://developers.cloudflare.com/workers/configuration/cron-triggers/), [GitHub dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)

## Supabase Free 적합성 확인 — 2026-11-27

판정: 현재 제목·링크 중심의 일일 브리핑을 저장하는 DB로 사용 가능하다. 공급자 변경·프로젝트 생성은 아직 수행하지 않았다. 앱 DB 부하 기준 판단이며 실행기·SMTP 비용과 무중단 운영을 보장하지 않는다.

- 공식 무료 한도: 프로젝트 DB 500 MB, egress 5 GB, 활성 프로젝트 2개. Object Storage 1 GB는 DB 500 MB에 합산되는 공간이 아니다. [가격](https://supabase.com/pricing)
- 규모 가정: 하루 1회, 최대 25건, 소수 수신자. 실제 1건 표본 JSON은 975 bytes였다. 여유 있게 JSON+메일 본문을 회당 100 KB로 가정하면 한 달 약 3 MB, 1년 약 36.5 MB다. 시스템 테이블·인덱스·발송 이력은 별도이며 실제 DB 사용량으로 확인한다. 기사 원문·첨부파일·벡터 저장은 가정에서 제외한다.
- 연결: 현재 psycopg/SQL/JSONB를 재사용할 수 있다. IPv4 환경은 무료 shared session pooler를 우선 사용하고 TLS verify-full/CA 구성을 검증한다. transaction pooler를 선택하면 prepared statements 및 session 제약을 따로 확인한다. [연결](https://supabase.com/docs/guides/database/connecting-to-postgres)
- 일시 정지: 7일간 낮은 DB 활동은 정지 대상이 될 수 있다. 공식 문서는 보통 하루 몇 번의 요청이 충분하다고 설명하지만 일일 배치만으로 정지 면제를 보장하지 않는다. 작업 실패·소유자 경고 메일을 확인한다. [정책](https://supabase.com/docs/guides/platform/free-project-pausing)
- Free에는 자동 백업과 uptime SLA가 포함되지 않는다. 공식 권고대로 정기 dump와 외부 백업·복구 연습이 필요하다. 백업 다운로드도 전송량 예산에 포함한다. [백업](https://supabase.com/docs/guides/platform/backups)
- 적용 전 남은 검증: 실제 프로젝트 슬롯, TLS/권한, migration, 동시 선점, DB 저장 실패 차단. 본문 30일 정리는 아직 미구현이며 현재 schema의 NOT NULL과 맞추는 migration이 필요하다. 공급자만 변경하면 이 작업들이 완료되는 것은 아니다.

2026-11-26: 사용자가 Neon 계정이 아직 없다고 확인했다. 스키마·명시적 연결 경로·모의 검증까지 구현했으며 실제 migration/TLS/권한/동시성 검증은 대기 중이다. 로컬 SQLite 경로는 그대로 유지한다.

## 현재 구현 범위

- `requirements.txt`: psycopg binary 3.3.4.
- `migrations/001_briefing.sql`: runs, briefings, deliveries. `002_scheduled_runs.sql`: 예약 plan, collecting/failed 상태 추가. 준비된 Supabase 프로젝트에 순서대로 적용한다.
- `python -m briefing.db --migrate`: `DATABASE_MIGRATION_URL`의 direct 연결, migration checksum과 트랜잭션 잠금. 실패 시 롤백. 정상 실행 명령에는 migration 권한을 주지 않는다.
- `--input <snapshot.json> --store-db`: 버전 있는 저장 결과를 DB에 불변 저장. `--email-check`와 함께 사용 시 run/briefing만 생성하며 delivery/SMTP 호출은 없음.
- `--store-db --send`: 같은 DB에서 발송 선점·결과 관리. DB 실패 시 SQLite로 자동 우회하지 않음.
- 연결은 TLS `verify-full`과 15초 timeout을 강제한다. 오류에 접속 문자열을 출력하지 않는다.

## 계정 생성 후 순서

1. 사용자 소유 Supabase Free 프로젝트를 만들고 테스트는 별도 프로젝트 또는 격리 테스트 DB에서 수행한다. 무료 활성 프로젝트 슬롯과 생성 가능한 리전을 확인한다. 기존 Neon 테스트 브랜치 가정은 적용하지 않는다.
2. migration 소유자 접속 문자열을 로컬 `.env`의 `DATABASE_MIGRATION_URL`에 저장한다. IPv6가 가능하면 direct, IPv4만 가능하면 session pooler를 사용한다. 채팅·Git에는 넣지 않는다.
3. `python -m pip install -r requirements.txt`, `python -m briefing.db --migrate` 실행.
4. Supabase에서 별도 로그인 역할 `briefing_app`을 만들고 비밀번호는 비밀 설정으로 관리한다. 소유자 접속으로 다음 최소 권한을 적용한다.

```sql
REVOKE ALL ON SCHEMA briefing FROM PUBLIC;
GRANT USAGE ON SCHEMA briefing TO briefing_app;
GRANT SELECT, INSERT ON briefing.runs, briefing.briefings TO briefing_app;
GRANT UPDATE (status, source_results) ON briefing.runs TO briefing_app;
GRANT SELECT, INSERT, UPDATE ON briefing.deliveries TO briefing_app;
```

5. `briefing_app` session pooler URL을 `.env`의 `DATABASE_URL`에 저장한다. pooler의 사용자명 형식을 확인하고 런타임에서 DDL 및 본문 UPDATE가 거부되는지 검증한다. 전용 briefing 스키마를 공개 Data API에 노출하지 않는다.
6. 격리 테스트 DB의 migration 소유자 URL만 `BRIEFING_TEST_DATABASE_URL` 환경변수로 지정해 `python -m unittest discover -s tests -p test_db_integration.py -v` 실행한다. 테스트는 전용 query로 만든 자기 행만 정리하지만 운영 DB에서는 실행하지 않는다.
7. 실제 수집 JSON을 `output/`에 UTF-8로 저장한 뒤 다음을 실행한다.

```text
python -m briefing --input output/live.json --store-db --email-check
```

실발송은 검토한 동일 입력에 `--store-db --send --to <승인된 수신자> --delivery-id <고정 키>`를 사용한다. SQLite와 PostgreSQL 사이에 발송 이력이 자동 공유되지 않으므로 이미 SQLite에서 보낸 표본을 새 DB에서 다시 발송하지 않는다.

## 후속 단계와 제한

수동 snapshot key는 수집 시각·검색어·hours를 사용한다. 새 예약 경로는 고정 조회 구간·config hash를 사용하며 DB 선점과 완료 결과 재사용을 구현했다. 예약 workflow는 dry-run 전용이고 실제 DB 통합 검증 전 실발송을 연결하지 않는다.

보존 정리, SQLite 이관, 백업/복원은 후속 migration과 검증 대상이다. 이관 전에 클라우드 실발송을 활성화하지 않는다. delivery key와 briefing/recipient가 다르면 오류로 막고, 같은 briefing을 새 key로 우회 발송하는 것도 UNIQUE 제약으로 차단한다.

실제 Postgres가 없는 상태에서 모의 테스트 통과를 SQL·동시성·권한 검증 완료로 표현하지 않는다. 연결 준비 완료와 클라우드 배포 완료는 구분한다.
