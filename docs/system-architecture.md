# 데일리 브리핑 시스템 아키텍처

> **2026-11-27 최신 선택:** DB는 Supabase Free, 예약은 GitHub Actions schedule부터 검증한다. workflow_dispatch는 수동 실행에 사용한다. 지연·누락 문제가 확인될 경우 Cloudflare Cron으로 트리거를 이전하되 runner 큐 지연은 별도로 진단한다. 아래 Neon 권고는 이전 설계이며 현재 연결·트리거 계약은 [DB 연결 준비](database-setup.md)를 따른다. 클라우드 자원과 트리거는 아직 배포하지 않았다.

> **현재 MVP 우선 적용(2026-11-26):** 현재 실행 구조는 단일 로컬 Python CLI → GDELT·MSIT RSS → 제목·출처·링크·관측 시각/발행일 정규화 → 기존 SMTP 발송이며, SQLite 파일로 발송 ID와 결과를 보존한다. 정상 기사 1건 이상이면 일부 실패 경고와 함께 발송한다. 기사 본문·RSS 설명·GPT는 사용하지 않는다. Gmail 앱 비밀번호의 합성 메일 수신은 확인했다. 아래 Neon·GitHub Actions·외부 감시·복구 설계는 **후속 확장안**이며 지금 구축할 필수 요소가 아니다. Gmail API/OAuth 추가 구현도 필요하지 않다. 현재 동작은 [README](../README.md)와 [실행 안내](collection-test.md)가 우선한다. 임시 클라우드 실행기에 옮길 때는 SQLite 이력의 영속 보존을 먼저 해결해야 한다.

상태: 배포 세부안은 권고안이며 서비스 계정, 리전, 예산 또는 운영 자원은 아직 확정되지 않았다. **현재 구현은 GDELT DOC API와 과기정통부 RSS를 사용하는 로컬 Python MVP**다. DeepSearch는 제거했고 NAVER는 권한 확인까지 보류한다. 기준 문서는 [기획안](cron-job-plan.md), [개발 계획](development-plan.md), `project_memories/`다.

## DB 구축 실행안 — 2026-11-26

상태: 사용자 요청에 따른 세부 설계. 클라우드 프로젝트·DB·계정·스케줄은 아직 생성하지 않았다. 이 절은 아래 기존 권고안의 DB/전달 관련 TBD를 구체화하며 충돌 시 이 절을 우선한다. 로컬 MVP 완료 기준은 변경하지 않는다.

### 공급자와 위치

- 기본안: **Neon Free 관리형 PostgreSQL, AWS Singapore (`aws-ap-southeast-1`)**. 사용자 소유 Neon 계정에 `semiconductor-industry-briefing` 프로젝트, 운영 `production` 브랜치, `briefing` 데이터베이스를 만든다. 운영 데이터가 없는 독립 테스트 브랜치에서 먼저 검증한다. 사용자가 EC2/VM을 관리할 필요는 없다.
- 한국에서 직접 점검하기 편한 아시아 리전을 선택한 제안이다. GitHub hosted runner와 DB의 최단 거리라고 주장하지 않는다. 생성 전 실제 runner의 TLS 연결·응답 시간을 측정하고 프로젝트 생성 화면의 가용성을 확인한다. 리전 변경은 새 프로젝트로 이관해야 하므로 데이터가 쌓이기 전에 결정한다. [공식 리전](https://neon.com/docs/introduction/regions)
- 2026-11-26 공식 Free 안내는 프로젝트당 100 CU-hours/월, 1 GB 저장소, 카드 없이 시작 가능이다. 이를 무제한 운영 보장으로 해석하지 않는다. 한도의 70%에서 보존량·쿼리·실행 시간을 검토하며 자동 유료 전환은 하지 않는다. [가격](https://neon.com/pricing)
- Supabase는 PostgreSQL이므로 대안이 된다. 무료 DB 500 MB 및 낮은 활동량에 따른 일시 정지를 고려해야 한다. IPv4 연결에는 shared pooler를 사용할 수 있다. 이미 쓰는 Supabase 조직이 있다면 이전 비용이 낮은 대안이지만, 현재 프로젝트에서 계정이 준비됐다는 증거는 없다. [가격](https://supabase.com/pricing), [연결](https://supabase.com/docs/guides/database/connecting-to-postgres), [일시 정지](https://supabase.com/docs/guides/platform/free-project-pausing)
- Cloudflare D1은 SQLite SQL을 사용하는 관리형 DB이며 Worker/HTTP API로 접근할 수 있다. Python에서 사용 불가능한 것은 아니지만 HTTP 인증·상태 저장 코드를 작성해야 한다. 이번 PostgreSQL 계획에서는 선택하지 않는다. 현재 코드에도 psycopg가 구현된 것은 아니며, Neon 선택 시 드라이버 추가가 필요하다. [D1](https://developers.cloudflare.com/d1/)

### 실행 위치와 연결

GitHub Actions의 짧게 실행되는 Python job이 GDELT/MSIT → Neon → Gmail SMTP 순서로 처리한다. DB에는 PostgreSQL TLS 연결, SMTP에는 STARTTLS를 사용한다. DB/SMTP 비밀값은 GitHub Environment secrets에 두고 로그·Git·DB 테이블에 기록하지 않는다.

- 런타임: `DATABASE_URL` pooled endpoint, `sslmode=verify-full`, 연결 timeout 15초. DB 오류 시 SQLite로 자동 전환하지 않고 발송을 차단한다.
- migration/백업: direct endpoint를 별도 자격 증명으로 사용한다. 런타임 역할에는 DDL/전체 DB 관리 권한을 주지 않는다.
- 역할: `briefing_migrator`는 전용 스키마 소유 및 migration, `briefing_app`은 필요한 SELECT/INSERT/UPDATE만, 정리·백업은 별도 작업 자격 증명으로 실행한다. `public` 기본 권한을 점검하고 스키마명을 명시한다.
- Neon pooler는 transaction 모드이므로 세션 advisory lock에 의존하지 않는다. UNIQUE 제약과 조건부 UPDATE를 사용하며 네트워크 요청 중 DB 트랜잭션을 열어두지 않는다. [연결 제한과 direct 용도](https://neon.com/docs/connect/connection-pooling)

### 최소 테이블과 데이터 계약

업무 테이블은 3개이며 migration 버전 관리 테이블은 별도다. ID는 UUID, 시각은 `timestamptz`로 저장하고 표시만 KST로 한다.

| 테이블 | 주요 필드 및 제약 | 역할 |
|---|---|---|
| `runs` | `id`, `run_key UNIQUE`, `trigger`, `window_start/end`, `config_hash`, `status`, `source_results JSONB`, `started_at/finished_at`, `error_code` | 한 조회 구간의 실행 소유권과 수집 결과. `run_key`는 구간·검색/설정 버전으로 계산하며 실행 시각 난수를 넣지 않음. |
| `briefings` | `id`, `run_id UNIQUE REFERENCES runs`, `schema_version`, `payload JSONB`, `content_hash`, `subject`, `body`, `created_at` | 검증된 정규화 결과와 메일 본문을 불변으로 저장. 제목·링크·소스 상태·날짜 정밀도 보존. 원문·RSS 설명·비밀값 제외. |
| `deliveries` | `id`, `briefing_id REFERENCES briefings` (이관 기록은 NULL 허용), `delivery_key UNIQUE`, `recipient`, `status`, `attempted_at/finished_at`, `error_code`, `message_id`, UNIQUE(`briefing_id`, `recipient`) | 받는 사람별 발송 선점 및 결과. 이관 기록은 기존 delivery key를 그대로 유지. |

상태는 CHECK 제약으로 제한한다. run은 `collecting/ready/empty/failed`, delivery는 `sending/sent/failed/unknown`이다. 실패 원문에는 비밀값이 섞일 수 있으므로 오류 종류·코드만 기록한다. 기사별 테이블, ORM, 큐는 이번 단계에 추가하지 않는다.

### 중복 방지와 재실행

1. 고정 조회 구간·설정으로 `runs` 행을 INSERT하고 충돌 시 기존 상태를 조회한다. 이미 ready인 구간은 새 수집으로 본문을 바꾸지 않고 저장 결과를 재사용한다.
2. 수집·검증 후 briefing 저장과 run ready 전환을 하나의 트랜잭션으로 커밋한다. 빈 결과는 empty로 기록하고 발송하지 않는다.
3. dry-run은 briefing까지만 저장하며 deliveries 행과 SMTP 호출을 만들지 않는다. 이는 기존 로컬 dry-run의 무발송 의미를 유지한다.
4. delivery 행을 `sending`으로 선점·커밋한 실행만 SMTP를 호출한다. 같은 키 충돌 시 sent/failed/unknown/sending 모두 자동 재전송하지 않는다.
5. SMTP 수락 후 sent로 전환한다. 응답불명은 unknown. SMTP 성공 후 DB 기록 실패는 sending으로 남을 수 있으므로 stale 상태를 자동 해제하지 않고 수신함과 대조한다.
6. 수집 중 중단된 collecting 행은 운영자가 기존 실행 종료를 확인한 뒤 조건부 상태 갱신으로 재개한다. 발송 중단과 수집 재개를 같은 자동 재시도 규칙으로 취급하지 않는다.

### 트리거와 전환 순서

1. **계정·연결 준비:** 사용자 소유 Neon 프로젝트와 GitHub 저장소 환경을 연결한다. 생성 화면에서 Free 한도·싱가포르 가용성 확인. 관리자 접속 문자열은 채팅 대신 로컬 비밀 설정 또는 GitHub secrets에 저장한다.
2. **스키마:** `migrations/001_briefing.sql`과 최소 버전 적용 스크립트 작성. 테스트 DB에 적용하고 런타임 역할의 DDL 거부·TLS 검증 확인.
3. **Python 연결:** psycopg를 버전 고정해 추가하고 `briefing/state.py`에서 저장·선점 기능 구현. 기존 수집·정규화·이메일 렌더러를 그대로 사용하고 delivery 저장 계층만 PostgreSQL에 연결한다.
4. **통합 검증:** 두 프로세스 동시 실행 시 하나만 선점, 같은 구간 재실행 시 같은 본문, DB 장애 시 발송 0건, SMTP unknown 재시도 0건, 저장 payload 왕복 일치, 복구 후 발송 차단을 확인한다. 모의 SMTP를 우선 사용한다.
5. **기존 SQLite 이관:** 로컬 실발송을 중지하고 이력을 백업한다. 기존 delivery key·status·message_id를 가져오며 없는 수신자/briefing은 추측하지 않는다. 새 클라우드 메일만 새 키를 사용한다. 건수·키·상태 대조 후 클라우드를 유일한 실발송 경로로 지정한다.
6. **Actions 수동 dry-run:** `.github/workflows/briefing.yml`을 `workflow_dispatch`로 연결한다. secrets 누락은 시작 전에 실패시키고 전체 실행 timeout 및 concurrency를 둔다. concurrency만 중복 방지 수단으로 사용하지 않는다.
7. **실제 기사 수동 수신 검증:** 현재 M1 수집 차단이 해소되면 DB에 저장된 동일 briefing으로 수신을 확인한다. 이 단계가 통과해야 예약 실발송으로 넘어간다.
8. **예약 운영:** 제안 시각은 매일 08:10 KST, 조회 구간은 전일 08:00~당일 08:00 KST다. 아직 확정 일정이 아니며 schedule은 비활성 상태로 준비한다. job 시작이 지연돼도 조회 구간은 고정한다. 현재 GDELT 상대 timespan 방식은 실행 시각에 따라 결과 구간이 달라지므로 예약 활성화 전 절대 구간 조회 계약을 공식 API 문서로 확인·구현한다. RSS 날짜만 있는 항목은 날짜 단위 중첩 가능성을 명시한다.

### 보존·백업·비용

- 초기 제안: 기사 payload·이메일 본문 30일, 수집 상세 상태 90일. 기간 종료 시 payload/subject/body 및 상세 필드를 비우고 FK가 참조하는 ID·내용 해시·중복 방지 키와 최소 상태 행은 서비스 운영 동안 유지한다. 해당 내용 필드는 정리 후 NULL을 허용하며 삭제된 본문을 재발송하지 않는다. 미해결 sending/unknown은 자동 정리하지 않는다. 이 정책은 권리 검토 및 보존 설정 확정 후 활성화한다.
- 하루 25건 × 1건 2 KB × 30일이면 기사 JSON 약 1.5 MB라는 추정이다. 인덱스·본문·시스템 데이터와 백업은 별도이며 실제 DB 크기/사용량을 측정한다.
- 무료 서비스의 복구 기능을 영구 백업으로 가정하지 않는다. direct 연결의 `pg_dump`를 매일 암호화해 비공개 GitHub Actions artifact에 7일 보관하는 초기안을 사용한다. 암호화 복구 키는 DB/백업과 분리해 사용자 비밀 저장소에 보관한다. 실제 artifact 비용·보존 한도는 계정에서 확인한다.
- payload 보존 정책과 맞춰 백업에도 최대 7일의 삭제 지연이 있음을 기록한다. 복구 연습을 먼저 수행하고 목표 RPO 24시간, RTO 1영업일을 측정한다. 목표값이며 현재 보장값이 아니다.
- DB 복원은 백업 이후 발송 이력을 잃을 수 있다. 복원 직후 SEND_ENABLED를 끄고 받은편지함/발송 증거와 대조하기 전 자동 발송을 재개하지 않는다. 자동 backfill은 하지 않는다.

### 구축에 필요한 사용자 측 정보

Neon 계정/프로젝트의 소유 조직, GitHub 운영 저장소와 secret 설정 권한이 필요하다. 한국 내 데이터 보관 의무가 있으면 싱가포르 기본안을 재검토해야 한다. DB 접속 비밀번호는 채팅으로 받지 않는다. 일정·보존 기간은 위 제안으로 구현 가능한 상태까지 준비한 뒤 운영 활성화 시 확정한다.

## 목표와 MVP 경계

합성·권리 확인 자료로 오프라인 브리핑을 먼저 완성하고, 이후 소스 수집, 요약, 상태 저장·전달, 예약 dry-run 순으로 확장한다. 정상 운영은 승인된 설정으로 자동 실행한다. 예외만 요약해 대응 담당자에게 보낸다. 상시 서버, 큐, 별도 웹서비스, RLM은 일일 배치 규모에 불필요하다.

팀 활용 가설은 원문 확인·수정 포함 자료 준비 시간과 수동 목록의 중요 기사 누락 건수로 평가한다. 자동 요약은 조사 범위를 좁히는 출발점이며 중요한 영업·투자 판단은 원문을 확인한다. 두 소스·검색어가 놓치는 뉴스가 있을 수 있다. GPT/API 비용 및 예외 처리 시간을 절감 효과와 함께 측정한다.

## 배포 권장안

무료 우선 원칙을 DB·실행·감시 인프라에도 적용한다. DB 권장 요금제는 Neon Free다. 2026-11-20 공식 가격 페이지 확인값은 프로젝트당 월 100 CU-hours와 저장 공간 1 GB이며 카드 없이 시작할 수 있다. 이전 블로그 수치와 달라 실제 생성 시 콘솔 한도를 재확인한다. [Neon 가격](https://neon.com/pricing)

Supabase Free도 PostgreSQL 후보이며 DB 500 MB를 제공한다. 낮은 활동량에 따른 일시 정지와 무료 자동 백업 미포함을 운영 부담으로 고려했다. Cloudflare D1 Free는 일 500만 행 읽기·10만 행 쓰기와 총 5 GB를 제공한다. SQLite 기반 HTTP 접근이므로 현재 psycopg·PostgreSQL 설계의 상태 저장 계층을 변경해야 한다. 이 변경은 충분히 가능하며 무료 한도와 운영 부담을 함께 비교한다. [Supabase 가격](https://supabase.com/pricing), [일시 정지](https://supabase.com/docs/guides/platform/free-project-pausing), [D1 가격](https://developers.cloudflare.com/d1/platform/pricing/), [D1 구조](https://developers.cloudflare.com/d1/)

Neon 추천의 근거는 PostgreSQL 직접 연결과 짧은 일일 배치에 맞는 무료 사용량이다. 실제 사용량은 미측정이다. 예시로 0.25 CU에서 하루 15분 활성화가 30일 지속되면 1.875 CU-hours이며, idle 시간과 추가 작업은 별도 합산한다. 부하 시험에서 실제 compute·저장·전송량을 측정해 무료 한도 안에 드는지 확인한다. 유료 업그레이드와 유료 감시·백업은 사용자 비용 승인 대상으로 둔다. 한도 초과 예상 시 보존량·호출량 조정 또는 다른 무료 구성을 검토한다.

| 구성 | 권장 선택 | 선정 이유와 전제 |
|---|---|---|
| 언어/런타임 | Python 3.12 이상, 표준 라이브러리, HTTPX, psycopg 3, OpenAI 공식 Python SDK | 배치·시간 처리에 적합. 구현 시작 시 지원 버전을 확인하고 lockfile로 고정한다. |
| 스케줄·실행 | GitHub Actions `schedule` + `workflow_dispatch`, GitHub hosted Ubuntu runner | 별도 상시 호스트 없이 저장소에서 예약·수동 실행 및 이력을 관리한다. 기본 브랜치에 workflow가 있어야 한다. 예약은 지연되거나 누락될 수 있어 외부 감시가 필수다. |
| 상태 DB | Neon 관리형 PostgreSQL, pooled TLS endpoint | 짧은 작업이 쓰는 관리형 DB로 단일 VM 운영을 피한다. Neon 선택은 조건부 권고이며 조직 계정·리전·예산·약관을 확인하지 않았다. 영속 실행 선점과 조건부 발송 상태를 활용한다. |
| 전달 | 조직이 승인한 팀 메시징 API 어댑터, 현재 TBD | 플랫폼과 수신 대상 미정. 전송 결과 조회 또는 idempotency 지원 여부가 배포 전 선택 조건이다. |
| 비밀값 | GitHub Actions Environment secrets, 최소 권한 | 런타임에 필요한 값만 job에 노출하고 로그 마스킹을 적용한다. DB는 전용 역할로 제한한다. |
| 누락 감시 | GitHub workflow 실행 이력/실패 알림 + 승인된 외부 uptime/check monitor | workflow 자체가 시작되지 않은 경우 workflow 내부 알림이 불가능하므로 외부 감시가 필요하다. 모니터 서비스/수신자 TBD. |

**네트워크 토폴로지:** Actions runner는 작업 시간 동안만 실행되는 외부 호스트다. DB는 Neon 프로젝트/브랜치의 한 리전에 둔다. GitHub-hosted runner의 outbound IP는 동적·공유이므로 고정 IP allowlist가 필요한 DB 방화벽 구성과 맞지 않는다. MVP는 TLS로 보호된 DB public endpoint와 강한 인증을 사용하되, DB 제공자의 IP 제한 기능이 이를 막으면 다음 중 하나를 다시 선택한다: 고정 outbound IP를 지원하는 GitHub larger runner, DB가 위치한 클라우드의 스케줄 작업, 또는 private networking. self-hosted VM은 운영 부담 때문에 우선하지 않는다. DB public endpoint는 인터넷에서 접근 가능하므로 네트워크 경계 대신 TLS, 비밀값, 역할 권한, 필요 시 공급자 IP 제어로 방어한다. 비밀값 유출 시 영향이 걱정되는 조직 정책이라면 public endpoint를 전제로 진행하지 않는다.

리전은 우선 한국의 업무·지원 위치와 서비스 공급자가 실제 제공하는 리전 중 선택한다. 지원 리전, 데이터 보관 위치, DB/runner/GitHub/LLM 간 왕복 지연, 법무·조직 데이터 위치 규칙, 비용을 비교한다. 특정 서울 리전의 가용성이나 데이터 주권 적합성을 전제하지 않는다. PostgreSQL과 API 연결은 TCP 5432 또는 공급자 connection string 포트, TLS 인증서 검증 필수다. 외부 API는 HTTPS TCP 443이며 각각의 발급 토큰/API key로 인증한다. 임의 inbound 포트는 열지 않는다.

### 배포 구성도

```mermaid
flowchart LR
  Mon[외부 실행 감시<br/>서비스 TBD] -->|HTTPS 443<br/>GitHub API 또는 check URL| GH[GitHub Actions<br/>schedule / manual / rerun]
  Op[운영자<br/>repo write 권한] -->|HTTPS 443<br/>workflow_dispatch| GH
  GH -->|runner job| Job[Python batch<br/>ephemeral hosted runner]
  Job -->|HTTPS 443 + provider auth| G[GDELT]
  Job -->|HTTPS 443 + RSS| Msit[과학기술정보통신부 RSS]
  Job -->|HTTPS 443 + API key| AI[OpenAI API<br/>허용 필드만]
  Job -->|HTTPS 443 + API key| Msg[팀 채널 API TBD]
  Job -->|TCP 5432 + TLS<br/>DB credential| DB[(Neon PostgreSQL<br/>리전 TBD / pooled endpoint)]
  GH -. secrets 주입 .-> Job
```

**현재 콘텐츠 권리 경계:** GDELT 결과는 제목·도메인·관측시각·원문 링크를 발견하는 데만 사용하며, 연결된 언론사 기사 본문은 가져오거나 LLM에 보내지 않는다. 과기정통부 RSS 설명은 RSS 항목에 KOGL 제1유형/Type 1 표시가 있는 경우에만 요약 필드로 사용할 수 있다. 공공기관 피드라는 이유만으로 모든 항목을 허가된 것으로 간주하지 않는다. NAVER Search API의 상세 권한은 나중에 확인하며 그 전에는 호출하거나 이메일에 포함하지 않는다.

## 트리거와 실행 프로토콜

1. **예약:** GitHub Actions `schedule`이 기본 브랜치의 마지막 커밋으로 실행한다. KST 일정은 승인 후 UTC cron으로 표현하거나 IANA timezone 지원 시 그 기능을 검증해 쓴다. 시간 정각의 과부하를 피하는 분을 고른다. KST overnight window는 런타임 설정의 IANA `Asia/Seoul` 구간으로 계산하며 경계·날짜 정책은 TBD다.
2. **수동 실행:** 기본 브랜치에 둔 `workflow_dispatch`를 GitHub UI에서 운영자(write 권한)만 실행한다. 입력은 `dry_run`(기본 true), 선택적 승인된 business date, 제한된 사유 문자열로 한정한다. 일반 재실행은 신규 발송을 만들지 않도록 기존 logical delivery identity를 재사용한다.
3. **실패 재실행:** 동일 구간의 재실행은 동일 논리적 브리핑 키를 사용한다. 성공 기록이 있으면 발송 단계를 건너뛴다. 결과 불명은 조회/대조 전 재전송 금지다. 재발송은 기존 건을 조정 가능한 담당자가 확인하고 명시적으로 새 재발송 식별자를 승인한 경우에만 허용한다.
4. **동시성:** Actions concurrency group은 실행 중복을 줄이는 1차 방어다. PostgreSQL 영속 실행 선점이 실행 단위의 최종 경합 방지다. 저장소/DB 연결이 안 되거나 lock을 얻지 못하면 발송을 포함한 작업을 fail-closed로 중단한다.

### 실행 시퀀스

```mermaid
sequenceDiagram
  actor O as 운영자
  participant GH as GitHub Actions
  participant W as 외부 감시
  participant J as Python job
  participant DB as PostgreSQL
  participant S as 승인된 소스/API
  participant D as 전달 API TBD
  W->>GH: 예상 실행/완료 이력 조회
  GH->>J: schedule 또는 workflow_dispatch
  J->>DB: TLS 연결, 설정 버전 읽기, UNIQUE run key로 실행 선점
  J->>DB: run row 생성, 권리/모드/필수 설정 gate 확인
  J->>S: HTTPS 수집 (권리 승인된 연결만)
  S-->>J: 데이터/상태
  J->>J: 정규화, 정책 필터, 근거 검증, fallback
  J->>DB: digest와 delivery intent 저장, UNIQUE 충돌 확인
  alt dry-run 또는 승인된 정책상 발송 보류
    J->>DB: 억제 사유와 run 결과 기록
  else 승인된 운영 발송
    J->>D: HTTPS 전송 + provider auth/idempotency key 지원 시 사용
    alt 명확한 성공
      D-->>J: 성공 및 message ID
      J->>DB: delivered와 영수증 저장
    else timeout/응답 불명
      J->>DB: delivery_unknown 저장, 재전송 금지
      W->>O: 승인된 예외 경로로 확인 요청
    end
  end
  J->>DB: 종료 상태 기록
  W->>O: 실행 누락/실패만 알림 (채널·기준 TBD)
```

## 네트워크·인증·접근 통제

| 연결 | 출발지 → 목적지 | 프로토콜/포트/TLS | 인증·통제 |
|---|---|---|---|
| 트리거 | 운영자 브라우저 → GitHub Actions | HTTPS 443, TLS | GitHub 계정 MFA 및 저장소 write 권한. 운영자 승인군은 조직이 결정한다. |
| 소스 | ephemeral runner → GDELT DOC API / 과기정통부 RSS | HTTPS 443, TLS | GDELT 공개 endpoint와 공식 RSS. 응답 크기·timeout·호출 상한을 둔다. NAVER는 권한 확인 전 제외. |
| LLM | runner → OpenAI API | HTTPS 443, TLS | 요약 기능은 미구현. 추후 권리 허용 자료만 최소 입력으로 전송하고 출력 길이를 제한한다. |
| DB | runner → managed PostgreSQL endpoint | TCP 5432, TLS verify-full | 전용 `app_runtime` 계정, 강한 secret, DB 권한 최소화. 공용 hosted runner라 고정 IP를 가정하지 않는다. |
| 전달 | runner → 채널 API TBD | HTTPS 443, TLS | 봇/앱 토큰은 승인된 환경 secret. 수신 대상 제한. idempotency/조회 API 지원 확인. |
| 비밀 주입 | GitHub Environment → runner job | GitHub 내부 secret 제공 | protected environment/branch 조건으로 prod secrets를 제한한다. 수동 workflow 입력에 비밀값을 받지 않는다. |
| 누락 감시 | monitor → GitHub API/check endpoint | HTTPS 443, TLS | read-only GitHub token 또는 비밀 없는 health endpoint; provider 요금·인증 조건 TBD. |

Neon pooled endpoint는 transaction pooling을 사용하므로 영속 claim과 짧은 트랜잭션으로 소유권을 관리한다. 마이그레이션은 별도 direct endpoint를 사용한다. [Neon pooling](https://neon.com/docs/connect/connection-pooling)

## DB 모델과 트랜잭션

PostgreSQL은 실행 상태와 delivery intent/receipt만 영속화한다. 기사 전문·API 원본 payload·GPT prompt/output을 장기 보존하는 저장소로 쓰지 않는다. 허용되는 데이터와 보존기간은 별도 승인 전 기록하지 않는다.

| 테이블 | 최소 컬럼 및 제약 |
|---|---|
| `schema_migrations` | `version` PK, `applied_at`; 배포용 migration role만 기록 |
| `runs` | `run_id` UUID PK, `logical_key` text, `config_version`, `mode`, `window_start/end` timestamptz, `status`, 시작/종료 시각, 단계 상태/건수 JSON(콘텐츠 금지), 오류 코드 |
| `deliveries` | `delivery_id` UUID PK, `logical_key` text UNIQUE, `run_id` FK, `status`, `payload_hash`, `provider_message_id` nullable, 시도 수, 갱신 시각, 안전한 오류 코드 |
| `run_events` (선택) | `event_id` bigserial PK, `run_id` FK, 시각, 단계, 상태, 안전한 요약; 상세 로그는 권리·보존 검토 전 생략 가능 |

logical_key의 구성은 업무 정책으로 결정한다. runs에는 UNIQUE run_key, owner_token, heartbeat_at, status를 둔다. INSERT ON CONFLICT DO NOTHING RETURNING의 반환 행이 있는 작업만 실행한다. heartbeat와 종료 갱신에는 소유자와 현재 상태 조건을 포함한다. 만료만으로 실행을 탈취하지 않는다. 이전 runner 종료와 전달 상태를 대조한 뒤에만 실패 실행의 소유권을 원자적 조건부 갱신(CAS)으로 변경한다.

발송은 UNIQUE logical_key의 prepared 행을 생성하고 prepared에서 sending으로 조건부 UPDATE RETURNING에 성공한 작업만 수행한다. 반환 행이 없으면 보내지 않는다. 기존 sending/sent/unknown을 prepared로 덮어쓰는 upsert는 금지한다. 외부 호출 전에 트랜잭션을 커밋한다. 성공은 sent와 영수증을 기록한다. timeout 또는 sending 중 중단은 unknown으로 대조하며 확인 전 재전송하지 않는다. 확정 실패만 안전한 재시도 조건과 승인된 상한 안에서 동일 키와 새 시도 식별자로 선점한다. DB 기록 실패는 외부 호출 전 중단한다.
별도 migration role은 DDL을 실행하고 runtime role은 필요한 테이블의 SELECT/INSERT/UPDATE만 가진다. 런타임에서 임의 DDL을 실행하지 않는다. migration은 수동 또는 protected 배포 job에서 한 번 적용하며 lock/버전 테이블로 동시 실행을 막는다. DB 계정·비밀값은 분리한다.

## 실패·비용·운영 복구

소스별 timeout과 제한 재시도는 transient 오류에만 적용한다. 빈 결과와 장애는 구분한다. 인증·권리·필수 설정이 해결되지 않으면 소스 호출/GPT 전송/발송을 진행하지 않는다. 한 뉴스 소스 실패가 다른 소스 데이터를 지우지는 않으며 부분 결과 발송은 승인 정책이 있을 때만 한다. NAVER 권리 차단은 수집 오류처럼 재시도할 항목이 아니다.

GPT 오류/검증 실패에는 허용된 입력으로 결정적 fallback을 시도한다. 필수 근거가 없으면 발송을 보류한다. 시장 데이터 선택 전에는 지표를 만들거나 빈 숫자를 채우지 않고 미수집 상태만 표현한다. 호출 수, 페이지 수, 입력 기사 수, 토큰, 재시도와 총 비용에 운영 승인 상한을 둔다. 임계 초과 시 다음 단계/GPT/발송을 중단하고 기록한다. 수치는 측정 후 TBD를 채운다.

**실행 누락 감시:** GitHub `schedule`은 정각 부하에서 지연 또는 드물게 누락될 수 있고 workflow 내 실패 알림은 시작되지 않은 실행을 찾지 못한다. 외부 monitor가 GitHub Actions API의 최근 실행을 주기적으로 확인하거나, 작업이 성공 시 monitor에 heartbeat를 보내 일정 허용 시간 내 없으면 예외 알림을 낸다. monitor 제품, 주기, 시간 허용치, 수신자, 비용은 TBD다. 기본 분 경계를 피해 예약한다.

**백업/복구:** DB 공급자의 자동 백업/PITR 가능 여부, 보존·복구 시점·복구 시간, 비용을 계정 생성 전 공식 문서/플랜에서 확인한다. 사용 전 운영 기록 보존에 필요한 최소 백업을 설정하고 주기적 복구 연습을 계획한다. 백업에 기사 payload는 넣지 않는다. Actions workflow, 설정 및 migrations는 Git 이력에서 복구한다. 복구 후 delivery 상태와 외부 message receipt를 대조하고 `sent`/`unknown`을 재조정하기 전 발송을 재개하지 않는다. 실제 RPO/RTO와 복구 담당자는 TBD다.

**중단/재개:** 긴급 중단은 production environment의 send-enabled 설정/secret을 비활성화하거나 발송 job을 수동 disable하고, reservation schedule과 DB 기록은 유지한다. 수집만 계속할지 전체 중단할지는 운영 선택이다. 재개 전 credential·권리·설정 버전, 마지막 성공 run, pending/unknown delivery, DB 상태와 누락 구간을 대조한다. 미확정 delivery를 처리한 후 운영자가 재개를 승인한다. 대량 자동 backfill이나 새 발송은 하지 않는다.

## 설정과 비밀값

`.env`는 로컬 합성 개발에만 쓰고 저장소에 커밋하지 않는다. GitHub production secrets는 protected environment에 두며 production branch/job에만 노출한다. 비밀이 아닌 정책값은 검토 가능한 YAML/TOML 설정 파일이나 승인된 DB config version으로 관리하고 hash/version을 각 run에 기록한다. 설정 누락·잘못된 값은 기본값으로 고치지 않고 fail-closed한다.

| 변수/설정 키 | 민감도 | 용도 / 제공 조건 |
|---|---|---|
| `APP_ENV`, `DRY_RUN`, `CONFIG_VERSION` | 비밀 아님 | 실행 모드·승인 설정 버전. `DRY_RUN` 기본 true. |
| `DATABASE_URL` | 비밀 | Neon pooled endpoint와 사용자 인증. TLS 검증 포함. runner 전용 secret. |
| `OPENAI_API_KEY` | 비밀 | 허용된 데이터만 전송하는 단계에서 주입. 권리 조건 미충족 시 해당 API 호출 금지. |
| `GDELT_*` 인증/endpoint 설정 | 조건별 | GDELT endpoint는 설정, 인증이 필요하면 secret. endpoint/쿼리는 합의 후 고정. |
| `MSIT_RSS` | 비밀 아님 | 공식 RSS endpoint. 인증키 불필요. |
| `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | 비밀 | 상세 권한 확인 후 별도 승인되기 전까지 발급·주입·호출하지 않음. |
| `MARKET_DATA_*` | TBD | 지표 공급자 확정 전 정의하지 않음. |
| `DELIVERY_API_TOKEN`, `DELIVERY_TARGET_ID` | 비밀/민감 | 채널 승인 후 production environment에만 주입. target은 로그 마스킹. |
| `ALERT_*` | TBD | monitor/예외 수신 경로 승인 뒤 정의. |
| `MAX_*`, `WINDOW_*`, `QUERY_*`, `SEND_ENABLED` | 비밀 아님 | 승인된 제한·키워드·window·발송 gate. config version 통제. |

## 구현 경로와 의존 순서

아래 경로는 제안이며 현재 코드가 있다고 가정하지 않는다. 앞 단계가 통과하지 않으면 뒤 단계로 진행하지 않는다.

| 순서 | 실제 제안 경로/산출물 | 선행 조건 | 완료 검증 |
|---|---|---|---|
| 1 | `briefing/models.py`, `briefing/render.py`, `briefing/__main__.py`, `tests/fixtures/` — 합성 자료 기반 샘플 | 키워드·외부 권리 불필요 | 한 건 및 빈 입력 출력, 링크/기준 시각 필드, 외부 네트워크 0회·발송 호출 0회 |
| 2 | `briefing/__main__.py`의 GDELT 및 RSS adapter | 현재 구현에 반영됨. RSS 설명은 항목 권리표시가 확인된 경우만 허용. NAVER는 보류 | GDELT/RSS 소스 독립 상태, 시간 필터, URL 중복 제거. 향후 별도 adapter 모듈 분리는 필요가 확인될 때 검토 |
| 3 | `briefing/summarize.py`, `briefing/validate.py`, `briefing/market.py` | 각 필드의 GPT 이용 권리, 모델·예산, 지표 승인 | 잘못된 기사 ID/근거/URL 거부, fallback, 비용 상한, 시장 누락 상태 |
| 4 | `briefing/state.py`, `briefing/delivery.py`, `migrations/` | PostgreSQL 계정·리전·접속/비용, channel API, logical key 및 partial policy 결정 | DB 통합: concurrent lock, unique conflict, rollback; mock delivery: sent/confirmed fail/unknown 재실행에서 중복 없음 |
| 5 | `.github/workflows/briefing.yml`, 설정 검증기, `scripts/check_run.py` | GitHub plan/repo, protected environment, secrets, DB public/private 경로, 권리·쿼터 확인 | schedule/manual/dry-run 경로, prod secret 분리, event/commit 고정, 외부 monitor 누락 감지, logs에서 secret/content 미노출 |
| 6 | `docs/operations.md`, 운영 체크 및 복구 절차 | 예외 수신자, 시간·비용 목표, backup/RPO/RTO 결정 | 모의 전달, unknown reconciliation 및 복구 연습, 수동 목록 대비 준비 시간·누락 비교, 최초 운영 활성화 승인 |

## TBD 및 선행 승인

**기술적 확인값:** GitHub 조직/plan과 runner 네트워크, Neon 계정·실제 지원 리전·요금·pooler 제한·백업, 외부 monitor, public endpoint 허용 여부, DB 보존/RPO/RTO, 공급자별 현재 호출 제한, API/모델 예산. 특정 계정, 호스트, IP, 리전 또는 계약이 준비됐다고 간주하지 않는다.

**업무 정책 TBD:** 검색 키워드와 관련성, KST 실행 시각과 overnight window 경계·timestamp 누락 처리, 시장지표와 제공자, 부분 결과 규칙, 발송 채널·대상, 콘텐츠 이용 및 보존 권리, URL/제목 중복 기준, 논리 delivery identity와 의도적 재발송 절차, dry-run 성공 기준·관찰 기간, 비용/시간 목표, 예외 알림 수신자·담당자. 이 미결 값 때문에 기술 연결 설계를 비워두지 않는다. 설정 지점과 안전한 기본 동작은 정하되 운영 활성화 전 반드시 값과 승인을 채운다.

## 공식 서비스 문서

- GitHub Actions schedule: UTC/IANA timezone, 기본 브랜치 조건, 지연·누락 주의 [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- 수동 실행 권한과 기본 브랜치 조건: [manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- GitHub-hosted runner 동적 IP 및 allowlist 주의: [GitHub IP addresses](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses)
- environment secrets 및 protection availability: [deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments), [environment REST API plan notes](https://docs.github.com/en/rest/deployments/environments)
- 임시 클라우드 자격 증명 대안: [GitHub OIDC](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers)
- 과기정통부 [RSS 안내](https://www.msit.go.kr/contents/cont.do?mId=173&mPid=147&sCode=user) 및 [저작권 정책](https://msit.go.kr/contents/cont.do?mId=161&mPid=147&sCode=user)
- 산업통상부 [보도·참고자료 RSS 게시판](https://www.motir.go.kr/kor/article/ATCL3f49a5a8c)과 [저작권 정책](https://www.motir.go.kr/kor/contents/81). 게시판은 KOGL 제1유형을 안내하나 구현용 RSS endpoint는 아직 확인이 필요하다.
- NAVER 검색 API 권한은 보류 중이며 상세 조건은 [NAVER API 이용약관](https://developers.naver.com/products/intro/terms/terms.md)에서 다시 확인한다.
- GDELT dataset 및 이용 안내: [GDELT about](https://gdeltproject.org/about.html)

Neon의 현재 가격, 리전, pooled endpoint와 TLS/backup 조건은 실제 project 및 선택 플랜에 종속되므로 계정 생성 단계에서 [Neon 공식 문서](https://neon.tech/docs/introduction)로 확인한다. 이 초안은 특정 Neon 기능·가격이나 고정 리전 지원을 보장하지 않는다.
