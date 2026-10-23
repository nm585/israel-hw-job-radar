# Validation — 2026-10-23

- 13 automated tests passed: scoring, HTML Israel filtering, Ashby filtering, configuration coverage, schedule, and manual catch-up followed by normal deduplication.
- Schedule expands to exactly 61 unique daily slots: 08:31–23:01 every 15 minutes, plus 23:31 and 00:01, Asia/Jerusalem.
- UTC mapping checked for winter, summer, and both 2026 Israeli DST transition dates.
- 50 candidate source adapters were checked live without Telegram messages. Detailed results are in SOURCE_AUDIT.json. 24 sources remain enabled; failures and unvalidated HTML extraction are retained for manual review.
- Zero vacancies are not treated as proof of failure: valid empty structured feeds remain active. Job counts are before relevance filtering and do not imply suitable openings.
- Watchlist is manual only. No complete-market coverage or exact GitHub execution timing is promised.
- No Telegram credentials, local databases, environment files or dependency environments are included in the package.
