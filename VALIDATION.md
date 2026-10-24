# Validation — 2026-10-23

- 43 automated tests passed: scoring, HTML Israel filtering, Ashby filtering, configuration coverage, schedule, and manual catch-up followed by normal deduplication, strict no-experience eligibility, and notification/location labels.
- Schedule expands to 144 unique daily wall-clock slots: every 10 minutes at :07/:17/:27/:37/:47/:57 around the clock, Asia/Jerusalem.
- UTC clock mapping checked for winter, summer, and both 2026 Israeli DST transition dates (138/150 matching instants on 23/25-hour dates; service execution is not guaranteed).
- 50 candidate source adapters were checked live without Telegram messages. Detailed results are in SOURCE_AUDIT.json. 24 sources remain enabled; failures and unvalidated HTML extraction are retained for manual review.
- Zero vacancies are not treated as proof of failure: valid empty structured feeds remain active. Job counts are before relevance filtering and do not imply suitable openings.
- Watchlist is manual only. No complete-market coverage or exact GitHub execution timing is promised.
- No Telegram credentials, local databases, environment files or dependency environments are included in the package.

Entry filter update: student, intern, internship, graduate, junior and entry-level titles with a retrieved description may qualify without an explicit no-experience sentence. Positive experience requirements still reject the posting. Empty descriptions are rejected.

Coverage/filter correction: Workday country facets are traversed recursively, including locationHierarchy1, before paging. A Junior/Graduate title is no longer mandatory; relevant non-senior engineering roles with complete descriptions and no detected mandatory prior experience may qualify. Preferred experience is distinct from mandatory requirements. Numeric experience checks remain conservative.

Update 2026-10-24: Google is now polled through official paginated Israel careers results (83 Israel cards in live validation); Microsoft Israel through its official local careers listings and detail pages (18 extracted relevant-title cards). These two companies have been removed from the manual watchlist. Student/intern/part-time matching covers English and Hebrew, including description evidence. Junior/Jr/ג׳וניור titles are temporarily excluded from notifications at the user’s request. Other unverified watchlist entries are still manual; they have not been silently enabled.
