# Israel HW Job Radar

A small job-monitoring bot tuned for **hardware / silicon / low-level student and early-career roles in Israel**.

It watches official employer career pages first, deduplicates by stable job ID/URL in SQLite, enriches new postings from the official detail page, scores fit, and sends only new relevant matches to Telegram.

The project is a tailored derivative inspired by the MIT-licensed [Esteban-PG/Job-alert-bot](https://github.com/Esteban-PG/Job-alert-bot). It keeps the useful ideas — direct ATS polling, persistent dedupe, source-health checks, dry runs, and Telegram notifications — but replaces the original market/profile with an Israel hardware/chip/quantum profile.

## What it prioritizes

**Tier A**

- RTL / Logic / Digital Design
- ASIC / SoC / Chip Design
- DFT / ATPG / Scan
- Design Verification / Formal Verification
- FPGA / Emulation

**Tier B**

- Silicon / Post-Silicon Validation
- Embedded / Firmware / low-level C/C++
- Hardware-software integration
- Computer architecture / microarchitecture

**Tier C**

- Hardware lab / board / system validation when it is genuinely close to silicon or low-level development

Senior/Staff/Principal/Manager roles are heavily penalized. Explicit 3+ year experience requirements, GPA cutoffs above ~84, and requirements for 3–4+ semesters remaining are flagged and penalized.

## Companies monitored

The audited configuration contains **24 enabled sources** and **44 watchlist entries**. Counts include parent/legacy brands and are not unique employer counts. Element Labs was removed at the user’s request. See [COMPANY_COVERAGE.md](COMPANY_COVERAGE.md) for the full roster, official references, acquisition aliases, and verification limitations.

New coverage includes all requested names: Chain Reaction, NeuroBlade, Majestic Labs AI, Exaware, ColorChip, Newsight Imaging, Weebit Nano, RAAAM (RAAM) Memory Technologies, HiveWare, VisIC, Articron, Quantum Transistors, Qarakal, Q-Factor, and the five parent/legacy pairs. Articron remains conditional because Israel presence was not verified.

**No current vacancies is not a source failure.** Valid empty structured feeds remain enabled. HTML extraction that could not be validated and failing endpoints are preserved disabled and listed for manual review in `config/watchlist.yaml`. Watchlist entries are not automatically scanned and do not generate alerts. Live audit evidence is in `SOURCE_AUDIT.json`; counts are before student/early-career relevance filtering.

## Why official ATS first?

LinkedIn and aggregators are useful discovery layers, but reposts and stale listings make them poor primary monitors. This bot prefers official Workday / Amazon / Eightfold / Ashby / Greenhouse / Lever feeds or official career pages. A job is deduped by source job ID when available; official URL hash is the fallback.

## Local setup

Requires Python 3.11+ (3.12 recommended).

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py --dry-run --no-seed -v
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py --dry-run --no-seed -v
```

The first real run **seeds silently by default** so you do not receive dozens of alerts for jobs that already existed. Use `--no-seed` only when you intentionally want current matches treated as new.

Useful commands:

```bash
# Preview everything without changing state
python run.py --dry-run --no-seed -v

# Test one company/source
python run.py --dry-run --no-seed --source NVIDIA -v
python run.py --dry-run --no-seed --source "Quantum Machines" -v

# Normal run
python run.py
```

## Telegram alerts

1. In Telegram, open **@BotFather** and create a bot with `/newbot`.
2. Send one message to the new bot.
3. Obtain the bot token and your chat ID.
4. Put them in local `.env`:

```env
TELEGRAM_TOKEN=123456:abcdef...
TELEGRAM_CHAT_ID=123456789
```

For GitHub Actions, add the same names under:

**Repository → Settings → Secrets and variables → Actions → New repository secret**

Never commit the token to the repository.

## GitHub Actions — Israel local schedule

Every day, in **Asia/Jerusalem**:

- Every 10 minutes, 24 hours a day, at :07, :17, :27, :37, :47, :57.
- No other automatic schedule triggers: **144 wall-clock slots/day**, 4,320 in 30 normal days or 4,464 in 31 normal days; DST transition days differ.

Each cron entry uses GitHub's native `timezone: Asia/Jerusalem`, including automatic summer/winter time handling. There is no all-night polling runner or UTC-offset maintenance. The workflow must be on the default branch with Actions enabled. Manual `workflow_dispatch` remains available for deliberate tests outside these slots.

GitHub scheduling is best-effort: actual starts may be delayed or dropped; the cron configuration cannot guarantee execution at the exact wall-clock minute. If exact actual execution times are essential, use a scheduler with that guarantee. See [GitHub timezone support](https://github.blog/changelog/2026-03-19-github-actions-late-march-2026-updates/).

The SQLite database persists through the Actions cache. Run counts are **not a guarantee of billed minutes**: duration, retries and manual runs affect usage. Check your plan's allowance for private repositories.

## Configuration

Main config:

```text
config/sources.yaml
```

Watch-only companies:

```text
config/watchlist.yaml
```

Each source supports a `priority` bonus. Higher priority is used for companies/roles particularly relevant to chip design.

Example Workday source:

```yaml
- type: workday
  name: NVIDIA
  tenant: nvidia
  dc: wd5
  site: NVIDIAExternalCareerSite
  countries: [Israel]
  priority: 12
```

Example Ashby source:

```yaml
- type: ashby
  name: Arago
  company: arago
  countries: [Israel, Tel Aviv]
  priority: 9
```

## How scoring works

The score is intentionally not an LLM-only decision. Hard signals are evaluated first:

- strong boost: `RTL`, `DFT`, `ATPG`, `Design Verification`, `Formal`, `Digital/Logic Design`
- boost: `ASIC`, `SoC`, `FPGA`, `microarchitecture`, `post-silicon`, `firmware`, `embedded`
- boost for `student`, `intern`, `graduate`, `junior`, `entry-level`
- bonus for `SystemVerilog`, `UVM`, `Verilog`, `VHDL`, `C++`, `Python`, `Linux`, `RISC-V`
- large penalty for `Senior`, `Staff`, `Principal`, `Manager`, etc.
- penalty/warning for explicit experience requirements and student-semester/GPA constraints

This prevents a senior RTL role from outranking a genuine student verification role merely because it contains more hardware keywords.

## Important limitations

- Career sites change. Source-health tracking warns after repeated adapter failures.
- Some sites are JavaScript-heavy and may require a dedicated adapter later; the generic HTML adapter is intentionally a fallback.
- Workday can temporarily respond with anti-bot HTML instead of JSON. The bot treats that as a source failure rather than silently assuming there are no jobs.
- `config/watchlist.yaml` is discovery-only. It exists specifically to avoid scraping the wrong company or pretending an unofficial listing is an official opening.
- GitHub scheduled workflows are best-effort. For strict sub-hour timing, a self-hosted runner or an external scheduler triggering `workflow_dispatch`/`repository_dispatch` is more deterministic.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## License / attribution

MIT. The repository preserves the copyright notice from the upstream `Esteban-PG/Job-alert-bot` project and adds attribution for this derivative.

### One-time catch-up

In Actions → Israel hardware job radar → Run workflow, enable `include_existing` to send all currently matching open jobs, including previously seen postings. Leave `dry_run` unchecked to deliver Telegram alerts. The option defaults to false, so subsequent scheduled runs continue sending only new matches. Locally: `python run.py --include-seen`.

### Telegram labels

The main badge groups student/internship roles together as 🟢, also used for explicitly part-time junior/entry-level roles. Explicitly full-time junior/entry-level roles use 🔵. Junior/entry-level roles with unknown or conflicting hours use ⚪. A separate hours line always shows full-time, part-time, conflicting, or unspecified, including for student/internship jobs. Career track is detected conservatively from the title; hours use explicit wording in the title/description. Student/internship never implies part-time. Existing messages are unchanged.

### Mandatory no-experience filter and location preferences

Only postings with a student/intern/junior/entry-level/graduate title and explicit no-prior-experience eligibility (including a zero-year minimum) pass the notification filter. Positive experience requirements and unclear eligibility are blocked regardless of score. Student/junior titles alone are insufficient. This conservative filter may omit suitable jobs when their pages do not state eligibility clearly.

A separate location badge uses 🟢 for the Tel Aviv/Herzliya/Raanana/Petah Tikva/Hod Hasharon/Kfar Saba area, 🟠 for Haifa/Jerusalem/Rehovot/Beer Sheva, and ⚪ for other or unclear locations. Mixed central/orange locations are marked unclear. This labels location preferences without excluding cities.

Entry filter update: student, intern, internship, graduate, junior and entry-level titles with a retrieved description may qualify without an explicit no-experience sentence. Positive experience requirements still reject the posting. Empty descriptions are rejected.

Coverage/filter correction: Workday country facets are traversed recursively, including locationHierarchy1, before paging. A Junior/Graduate title is no longer mandatory; relevant non-senior engineering roles with complete descriptions and no detected mandatory prior experience may qualify. Preferred experience is distinct from mandatory requirements. Numeric experience checks remain conservative.
