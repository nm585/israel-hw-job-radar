# Validation — 2026-10-23

- 43 automated tests passed: scoring, HTML Israel filtering, Ashby filtering, configuration coverage, schedule, and manual catch-up followed by normal deduplication, strict no-experience eligibility, and notification/location labels.
- Schedule expands to 144 unique daily wall-clock slots: every 10 minutes at :01/:11/:21/:31/:41/:51 around the clock, Asia/Jerusalem.
- UTC clock mapping checked for winter, summer, and both 2026 Israeli DST transition dates (138/150 matching instants on 23/25-hour dates; service execution is not guaranteed).
- 50 candidate source adapters were checked live without Telegram messages. Detailed results are in SOURCE_AUDIT.json. 24 sources remain enabled; failures and unvalidated HTML extraction are retained for manual review.
- Zero vacancies are not treated as proof of failure: valid empty structured feeds remain active. Job counts are before relevance filtering and do not imply suitable openings.
- Watchlist is manual only. No complete-market coverage or exact GitHub execution timing is promised.
- No Telegram credentials, local databases, environment files or dependency environments are included in the package.
