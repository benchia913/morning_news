import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

import requests

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"


def fetch_top_headlines(country: str = "us", page_size: int = 10, category: str | None = None, query: str | None = None):
    api_key = os.environ["NEWSAPI_KEY"]
    params = {
        "apiKey": api_key,
        "country": country,
        "pageSize": page_size,
    }
    # Filter more towards finance/business headlines
    if category:
        params["category"] = category
    if query:
        params["q"] = query
    resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", [])


def build_summary(articles, header: str | None = None):
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    title_line = header or "Morning News Summary"
    lines = [f"{title_line} - {today}", ""]

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
    # Comma-separated lists allow multiple markets/categories, e.g.:
    # NEWS_COUNTRIES="us,sg" and NEWS_CATEGORIES="business,business"
    countries_raw = os.environ.get("NEWS_COUNTRIES") or os.environ.get("NEWS_COUNTRY", "us")
    categories_raw = os.environ.get("NEWS_CATEGORIES") or os.environ.get("NEWS_CATEGORY", "business")

    countries = [c.strip() for c in countries_raw.split(",") if c.strip()]
    categories = [c.strip() for c in categories_raw.split(",") if c.strip()]

    # If only one category provided, reuse it for all countries
    if len(categories) == 1 and len(countries) > 1:
        categories = categories * len(countries)

    query = os.environ.get("NEWS_QUERY", "markets OR stocks OR finance")

    all_sections: list[str] = []
    for idx, (country, category) in enumerate(zip(countries, categories)):
        articles = fetch_top_headlines(country=country, category=category, query=query)
        header = f"Morning News Summary ({country.upper()} / {category})"
        section = build_summary(articles, header=header)
        if idx > 0:
            all_sections.append("")  # blank line between sections
            all_sections.append("-" * 60)
            all_sections.append("")
        all_sections.append(section)

    summary = "\n".join(all_sections)
    subject = "Your Morning News Summary"
    send_email(subject, summary)


if __name__ == "__main__":
    main()

