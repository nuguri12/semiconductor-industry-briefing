"""Build and validate an email-ready briefing without sending it."""

from email.message import EmailMessage
from email.utils import parseaddr
import smtplib
import ssl
from urllib.parse import urlsplit

from .delivery import DeliveryUnknown


def build_message(result, body, recipient=""):
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = f"[산업 브리핑] {result['collected_at'].split('T')[0]}"
    message.set_content(body)
    return message


def add_sender(message, sender):
    message["From"] = sender


def validate_message(message):
    errors = []
    if not message.get("Subject", "").strip():
        errors.append("제목이 없습니다.")
    if not message.get("To", "").strip():
        errors.append("수신자가 없습니다.")
    _, address = parseaddr(message.get("To", ""))
    if not address or "@" not in address or address.startswith("@") or address.endswith("@"):
        errors.append("수신자 이메일 주소가 올바르지 않습니다.")
    body = message.get_body(preferencelist=("plain",))
    if body is None or not body.get_content().strip():
        errors.append("일반 텍스트 본문이 없습니다.")
        return errors
    content = body.get_content()
    if "수집 시각:" not in content:
        errors.append("수집 시각이 없습니다.")
    if "기사 " not in content:
        errors.append("기사 건수 정보가 없습니다.")
    for line in content.splitlines():
        if line.startswith("원문: "):
            try:
                url = urlsplit(line.removeprefix("원문: ").strip())
                if url.scheme not in ("http", "https") or not url.hostname:
                    raise ValueError
            except ValueError:
                errors.append("유효하지 않은 원문 링크가 있습니다.")
    return errors


def send_via_smtp(message, host, port, username, password):
    context = ssl.create_default_context()
    smtp = smtplib.SMTP(host, port, timeout=30)
    accepted = False
    try:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(username, password)
        try:
            refused = smtp.send_message(message)
            accepted = not refused
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused,
                smtplib.SMTPDataError) as error:
            raise ValueError("SMTP가 메시지를 거부했습니다.") from error
        except Exception as error:
            raise DeliveryUnknown("SMTP 응답을 확인하지 못했습니다.") from error
        if refused:
            raise ValueError("SMTP가 일부 수신자를 거부했습니다.")
        return None
    except DeliveryUnknown:
        raise
    except (ValueError, smtplib.SMTPException):
        raise
    except Exception as error:
        raise DeliveryUnknown("SMTP 전송 결과를 확인하지 못했습니다.") from error
    finally:
        try:
            smtp.close()
        except Exception:
            if not accepted:
                pass
