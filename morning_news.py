import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

import requests

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"


def fetch_top_headlines(country: str = "us", page_size: int = 10):
    api_key = os.environ["NEWSAPI_KEY"]
    params = {
        "apiKey": api_key,
        "country": country,
        "pageSize": page_size,
    }
    resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", [])


def build_summary(articles):
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    lines = [f"Morning News Summary - {today}", ""]

    if not articles:
        lines.append("No top headlines found today.")
        return "\n".join(lines)

    for i, article in enumerate(articles, start=1):
        title = article.get("title") or "No title"
        source = (article.get("source") or {}).get("name") or "Unknown source"
        url = article.get("url") or ""
        lines.append(f"{i}. {title} ({source})")
        if url:
            lines.append(f"   {url}")
        lines.append("")

    return "\n".join(lines)


def send_email(subject: str, body: str):
    from_addr = os.environ["EMAIL_USER"]
    to_addr = os.environ.get("EMAIL_TO", from_addr)
    password = os.environ["EMAIL_PASS"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(from_addr, password)
        server.send_message(msg)


def main():
    country = os.environ.get("NEWS_COUNTRY", "us")
    articles = fetch_top_headlines(country=country)
    summary = build_summary(articles)
    subject = "Your Morning News Summary"
    send_email(subject, summary)


if __name__ == "__main__":
    main()

