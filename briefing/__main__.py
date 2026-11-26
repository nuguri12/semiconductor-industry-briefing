import argparse
from datetime import datetime, timezone, timedelta
from itertools import zip_longest
import html
import json
import os
from pathlib import Path
import sys
import time
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .email import add_sender, build_message, send_via_smtp, validate_message
from .delivery import DeliveryLedger, dispatch

ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
MSIT_RSS = "https://www.msit.go.kr/user/rss/rss.do?bbsSeqNo=94"
MOTIR_RSS = "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/rss"
KST = timezone(timedelta(hours=9))


def load_dotenv(path=".env"):
    try:
        with open(path, encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    except FileNotFoundError:
        pass


def retry_delay(value):
    if not value:
        return 5
    try:
        if value.isascii() and value.isdigit():
            return max(5, int(value))
        deadline = parsedate_to_datetime(value)
        if deadline.tzinfo is None:
            raise ValueError("timezone missing")
        return max(5, (deadline - datetime.now(timezone.utc)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return 5


def collect(query, hours, limit, window_end=None):
    options = dict(query=query, mode="artlist", format="json", sort="datedesc", maxrecords=limit)
    if window_end is None:
        options['timespan'] = f'{hours}h'
    else:
        end = window_end.astimezone(timezone.utc)
        options.update(startdatetime=(end - timedelta(hours=hours)).strftime('%Y%m%d%H%M%S'),
                       enddatetime=end.strftime('%Y%m%d%H%M%S'))
    params = urlencode(options)
    request = Request(ENDPOINT + "?" + params,
                      headers={"User-Agent": "briefing-prototype/0.1"})
    for attempt in range(2):
        try:
            with urlopen(request, timeout=45) as response:
                body = response.read(5_000_001)
            break
        except HTTPError as error:
            delay = retry_delay(error.headers.get("Retry-After"))
            error.close()
            if error.code not in (429, 502, 503, 504) or attempt == 1:
                raise
            if delay > 60:
                raise ValueError(f"서버가 {delay:.0f}초 대기를 요청했습니다. 자동 재시도를 중단합니다.") from error
            print(f"HTTP {error.code}: {delay:.0f}초 후 한 번 재시도합니다.", file=sys.stderr)
            time.sleep(delay)
    if len(body) > 5_000_000:
        raise ValueError("응답 크기가 5 MB를 초과했습니다.")
    try:
        return json.loads(body)
    except (ValueError, UnicodeError) as error:
        raise ValueError("GDELT가 JSON 응답을 반환하지 않았습니다. 잠시 후 재시도하세요.") from error


def clean(value):
    return " ".join(html.unescape(value).split()) if isinstance(value, str) else ""


def normalize(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise ValueError("articles 배열이 없는 응답입니다.")
    articles, rejected = [], 0
    for row in payload["articles"]:
        if not isinstance(row, dict):
            rejected += 1
            continue
        title = clean(row.get("title"))
        url = row.get("url", "")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            valid = (parsed and parsed.scheme in ("https", "http") and parsed.hostname
                     and parsed.port != 0 and parsed.username is None
                     and "\\" not in url
                     and not any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url))
        except ValueError:
            valid = False
        if not title or not valid:
            rejected += 1
            continue
        observed = None
        try:
            stamp = row.get("seendate", "")
            if not isinstance(stamp, str) or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", stamp):
                raise ValueError("invalid observation timestamp")
            observed = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=timezone.utc).astimezone(KST).isoformat()
        except (ValueError, TypeError):
            pass
        articles.append(dict(title=title, url=url, source=parsed.hostname,
                             provider="GDELT", observed_at=observed, published_at=None,
                             language=clean(row.get("language")) or None))
    return articles, rejected


def collect_msit_rss(query, hours, limit, now=None):
    return collect_rss(MSIT_RSS, "MSIT RSS", "과학기술정보통신부", query, hours, limit, now)


def collect_motir_rss(query, hours, limit, now=None):
    # The ministry's RSS button submits an empty POST to this endpoint.
    return collect_rss(MOTIR_RSS, "MOTIR RSS", "산업통상부", query, hours, limit, now, data=b"")


def collect_rss(endpoint, provider, publisher, query, hours, limit, now=None, data=None):
    request = Request(endpoint, data=data, headers={"User-Agent": "semiconductor-industry-briefing/0.1"})
    with urlopen(request, timeout=30) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError(f"{provider} response exceeds 2 MB")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise ValueError(f"{provider} returned invalid XML") from error
    atom = "{http://www.w3.org/2005/Atom}"
    if root.tag not in ("rss", f"{atom}feed"):
        raise ValueError(f"{provider} returned an unsupported feed")

    now = now or datetime.now(KST)
    cutoff = now - timedelta(hours=hours)
    terms = [term.strip(" ()\"'") for term in re.split(r"\s+OR\s+", query, flags=re.I)]
    terms = [term for term in terms if term]
    entries = root.findall(".//item") or root.findall(f".//{atom}entry")
    articles, rejected = [], 0
    for row in entries:
        title = clean(row.findtext("title") or row.findtext(f"{atom}title"))
        url = row.findtext("link") or ""
        if not url:
            atom_link = row.find(f"{atom}link")
            url = atom_link.get("href", "") if atom_link is not None else ""
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            valid = (parsed and parsed.scheme in ("https", "http") and parsed.hostname
                     and parsed.port != 0 and parsed.username is None and "\\" not in url
                     and not any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url))
        except ValueError:
            valid = False
        if not title or not valid:
            rejected += 1
            continue
        date_value = (row.findtext("pubDate") or row.findtext(f"{atom}published")
                      or row.findtext(f"{atom}updated") or "").strip()
        date_only = bool(re.fullmatch(r"\d{4}[.-]\d{2}[.-]\d{2}", date_value))
        try:
            try:
                published = datetime.fromisoformat(
                    date_value.replace(".", "-") if date_only else date_value.replace("Z", "+00:00"))
            except ValueError:
                published = parsedate_to_datetime(date_value)
            if published.tzinfo is None:
                published = published.replace(tzinfo=KST)
            published = published.astimezone(KST)
        except (TypeError, ValueError):
            rejected += 1
            continue
        in_window = (cutoff.date() <= published.date() <= now.date() if date_only
                     else cutoff <= published <= now)
        if not in_window:
            continue
        haystack = title.casefold()
        if terms and not any(term.casefold() in haystack for term in terms):
            continue
        articles.append(dict(title=title, url=url, source=publisher,
                             provider=provider, observed_at=None,
                             published_at=published.date().isoformat() if date_only else published.isoformat(),
                             published_precision="date" if date_only else "datetime", language="ko"))
        if len(articles) >= limit:
            break
    return articles, rejected


def collect_sources(query, hours, limit, window_end=None):
    sources = {"GDELT": "failed", "MSIT RSS": "failed", "MOTIR RSS": "failed"}
    source_details = {}
    batches, rejected, limit_reached = {}, 0, False
    try:
        payload = (collect(query, hours, limit) if window_end is None
                   else collect(query, hours, limit, window_end=window_end))
        batches["GDELT"], bad = normalize(payload)
        rejected += bad
        sources["GDELT"] = "ok"
        source_details["GDELT"] = dict(count=len(batches["GDELT"]), rejected=bad)
        limit_reached |= len(payload["articles"]) >= limit
    except (OSError, ValueError) as error:
        print(f"GDELT: {type(error).__name__} {getattr(error, 'code', '')}", file=sys.stderr)
        batches["GDELT"] = []
        source_details["GDELT"] = dict(count=0, error=type(error).__name__,
                                       http_status=getattr(error, "code", None))

    for provider, collector in (("MSIT RSS", collect_msit_rss), ("MOTIR RSS", collect_motir_rss)):
        try:
            batches[provider], bad = (collector(query, hours, limit) if window_end is None
                                      else collector(query, hours, limit, now=window_end.astimezone(KST)))
            rejected += bad
            sources[provider] = "ok"
            source_details[provider] = dict(count=len(batches[provider]), rejected=bad)
            limit_reached |= len(batches[provider]) >= limit
        except (OSError, ValueError) as error:
            print(f"{provider}: {type(error).__name__} {getattr(error, 'code', '')}", file=sys.stderr)
            batches[provider] = []
            source_details[provider] = dict(count=0, error=type(error).__name__,
                                           http_status=getattr(error, "code", None))

    seen = set()
    for provider in sources:
        unique = []
        for article in batches[provider]:
            if article["url"] in seen:
                continue
            seen.add(article["url"])
            unique.append(article)
        batches[provider] = unique
    articles = [article for pair in zip_longest(*(batches[p] for p in sources))
                for article in pair if article is not None]
    return dict(articles=articles[:limit], rejected=rejected, sources=sources,
                source_details=source_details,
                limit_reached=limit_reached or len(articles) > limit)


def read_snapshot(payload):
    """Validate saved normalized output without reinterpreting it as GDELT data."""
    if not isinstance(payload, dict):
        raise ValueError('Snapshot must be an object')
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported briefing snapshot version")
    for key in ("collected_at", "query"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError(f"Invalid snapshot {key}")
    if datetime.fromisoformat(payload["collected_at"]).tzinfo is None:
        raise ValueError("Snapshot collection time requires a timezone")
    if type(payload.get("rejected")) is not int or payload["rejected"] < 0:
        raise ValueError("Invalid snapshot rejected count")
    if type(payload.get("limit_reached")) is not bool:
        raise ValueError("Invalid snapshot limit flag")
    sources = payload.get("sources")
    if (not isinstance(sources, dict) or not sources
            or any(not isinstance(k, str) or not k or k != clean(k)
                   or v not in ("ok", "failed") for k, v in sources.items())):
        raise ValueError("Invalid snapshot source states")
    details = payload.get("source_details", {})
    if not isinstance(details, dict):
        raise ValueError("Invalid snapshot source details")
    for provider, detail in details.items():
        if (provider not in sources or not isinstance(detail, dict)
                or type(detail.get("count")) is not int or detail["count"] < 0):
            raise ValueError("Invalid snapshot source count")
    rows, bad = normalize(payload)
    if bad or len({a["url"] for a in rows}) != len(rows):
        raise ValueError("Invalid or duplicate snapshot articles")
    for row in payload["articles"]:
        for key in ("title", "source", "provider"):
            if not isinstance(row.get(key), str) or not row[key].strip() or row[key] != clean(row[key]):
                raise ValueError(f"Invalid snapshot article {key}")
        if row.get("published_precision") not in (None, "date", "datetime"):
            raise ValueError("Invalid publication date precision")
        if sources.get(row["provider"]) != "ok":
            raise ValueError("Article belongs to an unsuccessful source")
        for key in ("observed_at", "published_at"):
            value = row.get(key)
            if value is None:
                continue
            if not isinstance(value, str):
                raise ValueError("Invalid article timestamp")
            stamp = datetime.fromisoformat(value)
            if key == "published_at" and row.get("published_precision") == "date":
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError("Invalid date-only timestamp")
            elif stamp.tzinfo is None:
                raise ValueError("Article timestamp requires a timezone")
    expected = ("invalid_records" if payload["rejected"] and not rows else
                "partial" if payload["rejected"] or any(s != "ok" for s in sources.values()) else
                "ok" if rows else "empty")
    if payload.get("status") != expected:
        raise ValueError("Snapshot status conflicts with its records")
    if 'schedule' in payload:
        from .schedule import validate_plan
        plan = validate_plan(payload['schedule'])
        if payload['query'] != plan['query'] or payload.get('hours') != plan['hours']:
            raise ValueError('Snapshot query/window differs from its plan')
    return payload


def render(result):
    lines = ["반도체·자동화 장비 산업 브리핑", f"수집 시각: {result['collected_at']}",
             f"조회: {result['query']}", f"기사 {len(result['articles'])}건 / 제외 {result['rejected']}건",
             "GDELT 관측 시각은 원문 발행 시각과 다를 수 있습니다."]
    if 'schedule' in result:
        plan = result['schedule']
        lines.append(f"고정 조회 구간: {plan['window_start']} ~ {plan['window_end']}")
        if any(a.get('published_precision') == 'date' for a in result['articles']):
            lines.append("날짜만 제공된 자료는 조회 날짜와 겹치는 항목이며 정확한 시간 포함 여부는 확인할 수 없습니다.")
    for provider, status in result.get("sources", {}).items():
        count = result.get("source_details", {}).get(provider, {}).get("count")
        lines.append(f"{provider}: {status}" + (f" (수집 {count}건)" if count is not None else ""))
    if result.get("status") == "partial":
        lines.append("일부 소스 수집 실패 또는 유효하지 않은 항목 제외: 확인된 기사만 포함합니다.")
    if result["limit_reached"]:
        lines.append("조회 상한에 도달했습니다. 전체 기사 목록이 아닐 수 있습니다.")
    if not result["articles"]:
        lines.append("모든 수집 항목이 검증에서 제외됐습니다." if result["rejected"]
                     else "표시할 기사가 없습니다.")
    for index, article in enumerate(result["articles"], 1):
        published = article.get("published_at")
        timestamp = published or article.get("observed_at")
        time_label = "발행 시각" if published else "관측 시각"
        if article.get("published_precision") == "date":
            time_label = "발행일"
        lines.extend(["", f"{index}. {article['title']}",
                      f"수집 소스: {article.get('provider', 'GDELT')}",
                      f"출처: {article['source']}",
                      f"{time_label}: {timestamp or '확인 불가'}",
                      f"원문: {article['url']}"])
    return "\n".join(lines) + "\n"


def main():
    load_dotenv()
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="GDELT 메타데이터 수집 및 정규화")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--query", help='예: (Infineon OR ASE OR HYUNDAI OR MOBIS)')
    source.add_argument("--input", help="저장한 브리핑 JSON 또는 GDELT 샘플 경로")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--json", action="store_true", help="정규화 JSON 출력")
    parser.add_argument("--email-check", action="store_true",
                        help="이메일 제목·수신자·본문·링크를 검증하고 미리보기 출력 (발송 안 함)")
    parser.add_argument("--send", action="store_true", help="이메일 실제 발송 (SMTP 설정 필요)")
    parser.add_argument("--to", help="수신 이메일 주소; --send와 함께 필수")
    parser.add_argument("--delivery-id", help="중복 방지용 안정적인 발송 ID; --send와 함께 필수")
    parser.add_argument("--delivery-db", default=".briefing-deliveries.sqlite3",
                        help="발송 상태 SQLite 파일")
    parser.add_argument("--store-db", action="store_true",
                        help="저장한 정규화 JSON을 PostgreSQL에 보존하고 해당 DB로 발송 이력 관리")
    args = parser.parse_args()
    if args.send and (args.email_check or args.json):
        parser.error("--send는 --email-check 또는 --json과 함께 사용할 수 없습니다.")
    if not 1 <= args.hours <= 72 or not 1 <= args.limit <= 250:
        parser.error("hours는 1~72, limit는 1~250 범위입니다.")
    try:
        snapshot = None
        if args.input:
            with open(args.input, encoding="utf-8") as stream:
                payload = json.load(stream)
            if isinstance(payload, dict) and any(k in payload for k in ("schema_version", "collected_at", "sources")):
                snapshot = read_snapshot(payload)
            articles, rejected = normalize(payload)
            unique = {}
            for article in articles:
                unique.setdefault(article['url'], article)
            articles = list(unique.values())[:args.limit]
            sources = {"GDELT": "ok"}
            limit_reached = len(payload["articles"]) >= args.limit
        else:
            if not args.query.strip():
                parser.error("검색어를 입력하세요.")
            collected = collect_sources(args.query, args.hours, args.limit)
            articles, rejected = collected["articles"], collected["rejected"]
            sources, limit_reached = collected["sources"], collected["limit_reached"]
        result = dict(collected_at=datetime.now(KST).isoformat(),
                      query=args.query or "합성/저장 응답",
                      articles=articles, rejected=rejected,
                      sources=sources,
                      status=("invalid_records" if rejected and not articles else
                              "partial" if rejected or any(s != "ok" for s in sources.values()) else
                              "ok" if articles else "empty"),
                      limit_reached=limit_reached)
        result["schema_version"] = 1
        if not args.input:
            result["source_details"] = collected.get("source_details", {})
            result["hours"] = args.hours
        if snapshot is not None:
            result = snapshot
        postgres_id = None
        if args.store_db:
            if snapshot is None:
                raise ValueError("--store-db requires a versioned snapshot via --input")
            from .db import PostgresStore
            store = PostgresStore(os.environ.get("DATABASE_URL"))
            message = build_message(result, render(result))
            postgres_id = store.save(result, str(message['Subject']), render(result))
            saved, subject, body = store.load(postgres_id)
            if saved != result or subject != str(message['Subject']) or body != render(result):
                raise ValueError("Stored briefing differs from the reviewed snapshot")
        sys.stdout.reconfigure(encoding="utf-8")
        output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result)
        if args.email_check:
            message = build_message(result, render(result), args.to or "review@example.invalid")
            errors = validate_message(message)
            print("이메일 메시지 검증: " + ("통과" if not errors else "실패"))
            print("--- 이메일 미리보기 (실제 발송 없음) ---")
            print(message.as_string())
            if errors:
                for error in errors:
                    print(f"검증 오류: {error}", file=sys.stderr)
                return 2
        elif args.send:
            if not result['articles']:
                print('발송 보류: 유효한 기사가 없습니다.', file=sys.stderr)
                return 2
            if not args.to or not args.delivery_id:
                parser.error("--send에는 --to와 --delivery-id가 필요합니다.")
            message = build_message(result, render(result), args.to)
            sender = os.environ.get("SMTP_FROM", "").strip()
            host = os.environ.get("SMTP_HOST", "").strip()
            username = os.environ.get("SMTP_USERNAME", "").strip()
            password = os.environ.get("SMTP_PASSWORD", "")
            try:
                port = int(os.environ.get("SMTP_PORT", "587"))
            except ValueError:
                parser.error("SMTP_PORT는 정수여야 합니다.")
            if not all((sender, host, username, password)) or not 1 <= port <= 65535:
                parser.error("SMTP_FROM, SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD 및 유효한 SMTP_PORT 설정이 필요합니다.")
            add_sender(message, sender)
            errors = validate_message(message)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 2
            if args.store_db:
                from .db import PostgresLedger
                ledger = PostgresLedger(os.environ.get("DATABASE_URL"), postgres_id, args.to)
            else:
                ledger = DeliveryLedger(Path(args.delivery_db))
            outcome = dispatch(ledger, args.delivery_id, message,
                               lambda msg: send_via_smtp(msg, host, port, username, password))
            print(f"이메일 발송 상태: {outcome.status}")
            return 0 if outcome.status == "sent" else 3
        else:
            print(output, end="\n")
        return 1 if all(status == "failed" for status in result['sources'].values()) else 0
    except (OSError, URLError, ValueError) as error:
        print(f"수집 실패: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
