# Morning News Summary

Python script and GitHub Actions workflow that fetch top news headlines every day at 8 AM SGT (00:00 UTC) and emails a simple text summary.

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
2. Add the following *Repository secrets*:
   - `NEWSAPI_KEY`: your News API key
   - `EMAIL_USER`: sender email
   - `EMAIL_PASS`: email app password / SMTP password
   - `EMAIL_TO`: recipient email
   - `NEWS_COUNTRY`: (optional) country code for headlines, e.g. `us`, `sg`, `gb`

The workflow file `.github/workflows/morning-news.yml` is configured to run at 00:00 UTC every day, which corresponds to 8:00 AM SGT.

