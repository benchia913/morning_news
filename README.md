# Morning News Summary

Python script and GitHub Actions workflow that fetch finance-focused news headlines, optionally runs them through an LLM (Claude) for a human-sounding summary and trading intuition, and sends the result by email and/or Telegram on a fixed schedule.

## Setup

1. Create a repository on GitHub and push this project directory to it.
2. Get an API key from a news provider such as `https://newsapi.org` and note the value.
3. Decide which email account will send the summary (for example, a Gmail account). You will need:
   - `EMAIL_USER`: the sender email address
   - `EMAIL_PASS`: the app password or SMTP password for that account
   - `EMAIL_TO`: the recipient email address (can be the same as `EMAIL_USER`)

## Configure GitHub Actions secrets

In your GitHub repository:

1. Go to **Settings → Secrets and variables → Actions**.
2. Add the following *Repository secrets* (at minimum):
   - `NEWSAPI_KEY`: your News API key
   - `EMAIL_USER`: sender email
   - `EMAIL_PASS`: email app password / SMTP password
   - `EMAIL_TO`: recipient email

3. Optional **news scope** secrets:
   - `NEWS_COUNTRY`: single country code for headlines, e.g. `us`, `sg`, `gb`
   - `NEWS_COUNTRIES`: comma-separated list of countries, e.g. `us,sg,jp`
   - `NEWS_CATEGORY`: single category, e.g. `business`
   - `NEWS_CATEGORIES`: comma-separated list of categories aligned with `NEWS_COUNTRIES`
   - `NEWS_QUERY`: keyword filter, e.g. `markets OR stocks OR finance`

4. Optional **Telegram delivery**:
   - Create a bot with `@BotFather`, then obtain:
     - `TELEGRAM_BOT_TOKEN`: token from BotFather
     - `TELEGRAM_CHAT_ID`: numeric chat ID (from `getUpdates`, can be negative)

5. Optional **Claude (Anthropic) summaries**:
   - `ANTHROPIC_API_KEY`: your Anthropic API key
   - `ANTHROPIC_MODEL`: (optional) e.g. `claude-3-5-sonnet-latest`

6. Optional **RSS feeds for richer content**:
   - `RSS_FEEDS`: comma-separated list of RSS feed URLs, e.g.
     - `https://www.reutersagency.com/feed/?best-topics=business-finance`
     - `https://feeds.a.dj.com/rss/RSSMarketsMain.xml`
   - The script will pull recent items from these feeds and:
     - Include them as an extra "RSS News Summary" section
     - Pass that text through Claude for an additional AI summary if configured

## Schedule

The workflow file `.github/workflows/morning-news.yml` is configured to run on a daily schedule (in UTC) that corresponds to several SGT times (for example 7:30 AM, 12 PM, 6 PM, 10 PM SGT). You can adjust the `cron` expressions in the `on.schedule` block to change when summaries are sent.

