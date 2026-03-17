import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
from textwrap import shorten

import requests
import anthropic
import feedparser


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


def fetch_rss_items():
    """
    Optionally fetch richer articles from RSS feeds.
    RSS_FEEDS should be a comma-separated list of feed URLs.
    """
    feeds_raw = os.environ.get("RSS_FEEDS")
    if not feeds_raw:
        print("RSS_FEEDS not set; skipping RSS fetch.")
        return []

    urls = [u.strip() for u in feeds_raw.split(",") if u.strip()]
    # Hard cap to avoid very long runs if many feeds are configured
    max_feeds = 10
    urls = urls[:max_feeds]
    print("RSS_FEEDS urls (capped):", urls)
    items = []
    for url in urls:
        try:
            parsed = feedparser.parse(url)
            entries = getattr(parsed, "entries", [])
            source_title = getattr(parsed, "feed", {}).get("title", url)
            print(f"Parsed RSS url={url!r}, entries={len(entries)}")
            # Cap items per feed to keep Claude context and runtime reasonable
            max_items_per_feed = 5
            for entry in entries[:max_items_per_feed]:
                title = entry.get("title", "No title")
                summary = entry.get("summary") or entry.get("description", "") or ""
                link = entry.get("link", "")
                items.append(
                    {
                        "title": title,
                        "source": {"name": source_title},
                        "url": link,
                        "summary": summary,
                    }
                )
        except Exception as e:
            print("RSS fetch exception for", url, ":", repr(e))

    return items

def summarize_with_claude(raw_text: str, section_label: str) -> str | None:
    """
    Optionally send the headlines through Claude for a concise,
    human-sounding financial summary with market implications.
    Controlled by ANTHROPIC_API_KEY and ANTHROPIC_MODEL env vars.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    # Trim context to avoid huge payloads
    prompt_text = shorten(raw_text, width=6000, placeholder="...")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1_200,
            temperature=0.3,
            system=(
                "You are a calm, expert macro and markets analyst. "
                "Given a batch of recent news headlines, you:\n"
                "1) Summarize the key themes in global markets and the economy.\n"
                "2) Explain the likely implications for major macro asset classes "
                "(rates, FX, rates options, fx options) in intuitive terms.\n"
                "3) Briefly highlight any useful trading concepts or intuition "
                "a discretionary trader should internalize.\n"
                "Avoid sensationalism; be concise, concrete, and educational."
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Section: {section_label}\n\n"
                                "Here is a list of recent news headlines with sources and URLs. "
                                "First, summarize the key themes in 3–6 bullet points. "
                                "Then add a short 'Market implications' paragraph and "
                                "a short 'Trading intuition' paragraph explaining how a "
                                "discretionary trader might think about these moves.\n\n"
                                f"{prompt_text}"
                            ),
                        }
                    ],
                }
            ],
        )
        texts = [block.text for block in message.content if block.type == "text"]
        content = "\n".join(t.strip() for t in texts if t.strip())
        return content or None
    except Exception as e:
        print("Claude summarize exception:", repr(e))
        return None

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


def send_telegram(body: str):
    """
    Optionally send the summary to a Telegram chat.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to be set.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    max_len = 4000  # Telegram hard limit per message

    # Split into multiple messages if needed
    chunks: list[str] = []
    text = body
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split on a double newline or single newline for readability
        split_point = text.rfind("\n\n", 0, max_len)
        if split_point == -1:
            split_point = text.rfind("\n", 0, max_len)
        if split_point == -1 or split_point < max_len * 0.5:
            split_point = max_len
        chunks.append(text[:split_point].rstrip())
        text = text[split_point:].lstrip()

    for idx, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                print("Telegram send failed (chunk", idx, "):", resp.status_code, resp.text)
        except Exception as e:
            print("Telegram send exception (chunk", idx, "):", repr(e))

def main():
    all_sections: list[str] = []

    # Build section purely from RSS feeds (richer content)
    rss_items = fetch_rss_items()
    if rss_items:
        rss_header = "RSS News Summary"
        # Include human-readable headlines section
        rss_section = build_summary(rss_items, header=rss_header)
        all_sections.append(rss_section)

        # Followed by the Claude summary for intuition/implications
        rss_claude = summarize_with_claude(rss_section, section_label=rss_header)
        if rss_claude:
            all_sections.append("")
            all_sections.append("AI Summary (Claude, RSS)")
            all_sections.append(rss_claude)
    else:
        all_sections.append("No RSS items found. Please check RSS_FEEDS in your secrets.")

    summary = "\n".join(all_sections)
    subject = "Your Morning News Summary"
    send_email(subject, summary)
    send_telegram(summary)


if __name__ == "__main__":
    main()

