# External scheduler setup (not activated yet)

Create one job in https://console.cron-job.org with these settings:

- URL: https://api.github.com/repos/nm585/israel-hw-job-radar/actions/workflows/job-alerts.yml/dispatches
- Method: POST
- Time zone: Asia/Jerusalem
- Custom schedule: `7,17,27,37,47,57 * * * *`
- Header `Accept`: `application/vnd.github+json`
- Header `Content-Type`: `application/json`
- Header `Authorization`: `Bearer YOUR_DEDICATED_GITHUB_TOKEN`
- Body: `{"ref":"main","inputs":{"dry_run":false,"include_existing":false}}`

Create a fine-grained GitHub token limited to this repository with Actions read/write permission. Enter it only in the scheduler's private configuration, never commit it. Do not use the Telegram token here. Set an expiry and renew before it expires.

Test the request: HTTP 204 means GitHub accepted it, not that the scan completed. Verify the new run in GitHub Actions and its conclusion. After a real scheduled trigger is verified, remove the native `on.schedule` section from the workflow (do not disable the workflow itself). Update the schedule tests accordingly. Until then the native GitHub schedule remains enabled.

Request-success notifications do not detect a later scan failure. GitHub run status remains the source for scan success. External dispatch avoids GitHub's native cron scheduler, but runner queues may still delay execution.
