# Project Memory

## 목적

`semiconductor-industry-briefing` 개발 시 `bicycle_road_event_alarm` 저장소에서 검증된 개발·운영 원칙만 참고한다. 기존 자전거 알림 서비스의 도메인이나 인프라를 그대로 복사하지 않는다.

## 현재 결정된 입력 소스

- GDELT API: 글로벌 뉴스 검색
- NAVER API HUB Search API: 국내 뉴스 검색
- 검색 키워드는 아직 정하지 않는다. 키워드 필터가 구현 단계에서 필요해지면 사용자에게 확인한다.
- 무료 환율·주가지수 데이터 소스는 아직 선정하지 않았다.

## 재사용할 원칙

1. **소스별 수집기를 분리하고 공통 기사 형식으로 정규화한다.** 각 수집기는 제목, 출처, 발행시각, 요약문, 원문 링크를 공통 형식으로 반환한다. 한 소스가 실패해도 다른 소스 결과는 계속 처리하고, 소스 장애와 실제 무기사를 구분해 기록한다.
2. **외부 API 호출에 시간 제한과 제한적 재시도를 둔다.** 일시적인 `429`, `5xx` 응답만 재시도하며, 모든 실패가 성공이나 무기사로 오인되지 않게 한다.
3. **규칙과 데이터가 사실의 기준이고 GPT는 요약을 담당한다.** GPT에는 필요한 구조화 필드만 전달하고, 제공된 기사에 없는 주장을 만들지 않도록 지시한다. 요약마다 출처와 원문 링크를 보존하고, 빈 응답·형식 오류에는 결정적인 fallback을 둔다.
4. **수동 검증과 실제 발송을 분리한다.** 처음에는 dry-run을 기본으로 하고, 실제 cron 발송은 수집과 메시지 검증이 안정된 후 활성화한다. 겹치는 배치 실행을 방지하고, 발송 중복을 추적할 수 있는 실행 기록을 남긴다.
5. **테스트는 네트워크에 의존하지 않게 만든다.** API 응답 fixture와 fake HTTP/GPT 클라이언트로 수집, 정규화, 중복 제거, 요약 검증을 확인한다. CI는 테스트와 린트·타입·포맷 검사를 실행한다.
6. **비밀값은 코드에 넣지 않는다.** API 키와 발송 자격 증명은 환경 변수 및 저장소 secret으로 관리한다.

## 뉴스 브리핑에 맞게 추가할 점

- 발행시각은 시간대가 명확한 형태로 저장하고, 수집 시간 창은 KST 기준으로 적용한다.
- 정규화된 URL을 우선해 중복을 합치고, URL이 다를 때는 제목·출처·발행시각으로 보조 판정한다.
- 소스별 이용 조건을 확인하고, 허용된 범위의 필드만 저장·GPT 전달·팀 배포한다. API 검색 결과라고 해서 기사 전문의 저장이나 재배포 권한이 자동으로 생기는 것은 아니다.
- 기사와 별도인 환율·지수 데이터는 제공자와 기준시각을 표시한다. 무료 데이터의 사용권과 사내 배포 조건을 확인한 뒤 연결한다.

## 지금 가져오지 않을 구성

Supabase 스키마와 마이그레이션, Telegram 발송기, Cloudflare Worker와 이중 스케줄러, 자전거 공지 전용 정규화 규칙은 현재 요구에 필요하지 않다. 저장소·발송 인프라는 실제 운영 요구가 생기면 가장 단순한 구성을 선택한다.

## 참고 저장소 위치

- 다중 소스 수집과 소스별 실패: `src/bicycle_road_event_alarm/crawler/multi_source_ingestion.py`
- HTTP timeout 및 재시도: `src/bicycle_road_event_alarm/crawler/http.py`
- GPT 요약 검증과 fallback: `src/bicycle_road_event_alarm/messaging/service.py`
- 구조화된 GPT 입력과 출처 제한: `src/bicycle_road_event_alarm/messaging/openai_generator.py`
- dry-run, 동시 실행 방지, CI 단계: `.github/workflows/manual-batch.yml`
- CI workflow 계약 테스트: `tests/unit/test_github_actions_workflow.py`
