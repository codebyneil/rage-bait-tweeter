# Rage-Bait Tweeter

An autonomous AI system that scrapes news headlines from RSS feeds, clusters them by story, generates provocative "rage-bait" tweets using a thinking model, scores them with a multi-model panel, and posts the best one to Twitter — all without requiring paid Twitter API access.

## How It Works

```
RSS Feeds (8 sources)          Recent Tweets (via bird)
       │                              │
       ▼                              ▼
┌─────────────────────────────────────────────────┐
│  1. Peak Hours Gate                             │
│     Exit early if outside posting windows       │
├─────────────────────────────────────────────────┤
│  2. Aggregate                                   │
│     Poll RSS feeds (last 12h) + fetch tweets    │
├─────────────────────────────────────────────────┤
│  3. Daily Limit Check                           │
│     Exit if we've hit max tweets today          │
├─────────────────────────────────────────────────┤
│  4. Cluster (midtier model)                     │
│     Group headlines by underlying story/event   │
├─────────────────────────────────────────────────┤
│  5. Filter                                      │
│     Drop clusters matching recent tweets        │
├─────────────────────────────────────────────────┤
│  6. Generate (thinking model)                   │
│     1-3 rage-bait candidates per cluster        │
├─────────────────────────────────────────────────┤
│  7. Score (multi-model panel)                   │
│     3 models rate each candidate 1-10           │
├─────────────────────────────────────────────────┤
│  8. Post                                        │
│     Tweet the highest-scoring candidate         │
├─────────────────────────────────────────────────┤
│  9. Notify                                      │
│     Mirror to Slack with full context           │
└─────────────────────────────────────────────────┘
```

**Fully stateless.** No database. Twitter is the source of truth for posted tweets. The pipeline re-evaluates fresh RSS data on every run, compares against recent tweets to avoid duplicates, and only posts if a candidate scores above the configured threshold.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [bird](https://github.com/soxoj/bird) CLI for Twitter access (cookie-based)
- API keys for at least one LLM provider (see [API Keys](#api-keys))

### Installation

```bash
git clone https://github.com/codebyneil/rage-bait-tweeter.git
cd rage-bait-tweeter
uv sync
```

### Configuration

Edit `config.yaml` to set your Twitter handle, models, feeds, and Slack webhook. Then set your API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
```

### Running

**Dry run** (no Twitter posting — recommended for testing):

```bash
uv run rage-bait-tweeter --dry-run
```

**Verbose dry run** (debug logging):

```bash
uv run rage-bait-tweeter --dry-run --verbose
```

**Live mode** (actually posts to Twitter):

```bash
uv run rage-bait-tweeter
```

**With a custom config file:**

```bash
uv run rage-bait-tweeter -c /path/to/config.yaml --dry-run
```

You can also run via module:

```bash
uv run python -m rage_bait_tweeter --dry-run
```

## Configuration

All behavior is driven by `config.yaml`. No hardcoded models, feeds, or thresholds.

```yaml
# RSS feeds to poll for headlines
feeds:
  - url: https://hnrss.org/frontpage?points=50
    category: tech
  - url: https://techcrunch.com/feed
    category: tech
  - url: https://feeds.reuters.com/reuters/businessNews
    category: finance
  - url: https://feeds.bloomberg.com/markets/news.rss
    category: finance
  - url: https://apnews.com/business.rss
    category: finance
  - url: https://rss.politico.com/politics.xml
    category: politics
  - url: https://rss.politico.com/congress.xml
    category: politics
  - url: https://apnews.com/politics.rss
    category: politics

# Twitter account to post from
twitter:
  handle: "@rage_takes"
  cookies_secret: ""          # For Cloud Run: Secret Manager path

# LLM models for each pipeline stage
models:
  clustering: claude-haiku-4-5-20251001       # Fast, cheap — groups headlines
  generation: claude-opus-4-6                  # Creative — writes the tweets
  scoring:                                     # Multi-model panel — rates candidates
    - gpt-5.2
    - claude-sonnet-4-5-20250929
    - gemini-3-flash-preview

# Slack notifications
slack:
  webhook_secret: ""          # Slack incoming webhook URL

# Pipeline limits
limits:
  max_tweets_per_day: 3       # Hard cap on daily posts
  headline_window_hours: 12   # How far back to look for headlines
  min_score_threshold: 6.5    # Minimum avg score (1-10) to post

# Only run during high-engagement windows
peak_hours:
  timezone: America/New_York
  windows:
    - { start: "07:00", end: "09:00" }   # Morning commute
    - { start: "12:00", end: "13:00" }   # Lunch break
    - { start: "17:00", end: "20:00" }   # Evening
    - { start: "21:00", end: "23:00" }   # Late night doomscroll
```

### Models

Models are referenced by their API model IDs. The system auto-detects the provider from the model ID prefix:

| Prefix | Provider | Examples |
|--------|----------|----------|
| `gpt-`, `o1`, `o3`, `o4`, `chatgpt-` | OpenAI | `gpt-5.2`, `gpt-4o`, `o3-mini` |
| `claude-` | Anthropic | `claude-opus-4-6`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001` |
| `gemini-` | Google | `gemini-3-flash-preview`, `gemini-3-pro-preview` |

You can swap any model at any stage by changing the config. No code changes needed.

### Feeds

Add or remove RSS feeds freely. Each feed needs a `url` and a `category` (used as the source label in headlines). The pipeline handles feed errors gracefully — if one feed is down, the rest still work.

### Peak Hours

The peak hours gate prevents wasted API calls during low-engagement times. In dry-run mode, peak hours are bypassed so you can test anytime.

## API Keys

The system requires API keys for whichever providers your configured models use. Set them as environment variables:

| Variable | Required When |
|----------|--------------|
| `OPENAI_API_KEY` | Any `gpt-*`, `o1`, `o3`, `o4`, or `chatgpt-*` model is configured |
| `ANTHROPIC_API_KEY` | Any `claude-*` model is configured |
| `GOOGLE_API_KEY` | Any `gemini-*` model is configured |

With the default config, all three keys are required (clustering uses Anthropic, generation uses Anthropic, scoring uses all three providers).

## Architecture

### Project Structure

```
rage-bait-tweeter/
├── config.yaml                          # Pipeline configuration
├── pyproject.toml                       # Project metadata and dependencies
├── src/rage_bait_tweeter/
│   ├── __init__.py
│   ├── __main__.py                      # CLI entry point (argparse)
│   ├── config.py                        # YAML config loading + dataclasses
│   ├── types.py                         # Shared data types (Headline, Cluster, Candidate, ScoredCandidate)
│   ├── models.py                        # Unified LLM client (OpenAI / Anthropic / Google)
│   ├── pipeline.py                      # 9-stage pipeline orchestrator
│   ├── aggregator.py                    # RSS feed polling + bird tweet fetching
│   ├── clustering.py                    # LLM-based headline clustering + dedup filter
│   ├── generator.py                     # Rage-bait tweet candidate generation
│   ├── scorer.py                        # Multi-model scoring panel + winner selection
│   ├── gate.py                          # Peak hours gate + daily limit check
│   ├── twitter.py                       # Tweet posting via bird CLI
│   └── notifier.py                      # Slack webhook notifications
├── tests/
│   ├── test_aggregator.py
│   ├── test_clustering.py
│   ├── test_config.py
│   ├── test_gate.py
│   ├── test_generator.py
│   ├── test_models.py
│   ├── test_pipeline.py
│   └── test_scorer.py
├── DESIGN.md                            # Detailed technical design document
├── RSS_FEEDS.md                         # Feed research and analysis
└── FEED_VOLUME_ANALYSIS.md              # Headline volume data backing the 12h window
```

### Pipeline Stages in Detail

#### 1. Peak Hours Gate (`gate.py`)

Checks the current time against configured windows (timezone-aware via `zoneinfo`). Exits immediately if outside peak hours to avoid wasting API calls. Skipped in dry-run mode.

#### 2. Aggregate (`aggregator.py`)

Polls all configured RSS feeds using `feedparser`. Filters headlines to the configured time window (default 12 hours). Also fetches the last 10 tweets from the configured Twitter account via the `bird` CLI — these are used in clustering to avoid posting about the same story twice.

Handles feed failures gracefully: if a feed is down or returns errors, the remaining feeds are still processed.

#### 3. Daily Limit Check (`gate.py`)

Guards against exceeding the configured daily tweet limit (default: 3/day). Currently a placeholder that always allows posting — full implementation will parse tweet timestamps from `bird` output.

#### 4. Cluster (`clustering.py`)

Sends all headlines + recent tweets to a midtier LLM. The model groups headlines by underlying story/event and marks clusters that overlap with recent tweets as `already_covered`. Returns structured JSON with cluster IDs, summaries, and headline mappings.

#### 5. Filter (`clustering.py`)

Removes clusters marked `already_covered` by the clustering model. This prevents the system from tweeting about the same story multiple times.

#### 6. Generate (`generator.py`)

For each surviving cluster, sends the cluster summary and headlines to a thinking model with a snarky pundit persona prompt. Generates 1-3 tweet candidates per cluster, enforcing the 280-character limit. Candidates over the limit are dropped with a warning.

The generation prompt:
- Establishes a snarky political/tech/finance pundit persona
- Requires sticking to facts from the news publications
- Maximizes for outrage, hot takes, and controversy
- Enforces 280-char limit, no hashtags

#### 7. Score (`scorer.py`)

Every candidate is sent to each model in the scoring panel independently. Each model rates the tweet 1-10 on "rage-bait-iness" — provocativeness, shareability, emotional punch, and clarity. Scores are parsed from free-text responses via regex. The final score is a simple average across all panel models.

If a scoring model fails or returns an unparseable response, that score is skipped and the average is computed from the remaining models.

The highest-scoring candidate above the threshold (default 6.5/10) wins. If nothing meets the threshold, the run is skipped.

#### 8. Post (`twitter.py`)

Posts the winning tweet via `bird tweet <text>`. Returns the tweet URL on success. In dry-run mode, logs what would be posted without actually tweeting.

#### 9. Notify (`notifier.py`)

Sends a Slack message via incoming webhook with the tweet text, story context, score breakdown by model, and tweet URL. Also notifies on skipped runs (with reason) and errors.

### Unified LLM Client (`models.py`)

A single `complete(model_id, prompt)` function dispatches to the correct provider based on model ID prefix. Supports:

- **OpenAI:** Chat completions API with optional JSON mode
- **Anthropic:** Messages API with 4096 max tokens
- **Google:** Generative AI API with optional JSON MIME type

Also provides `extract_json(text)` which handles the common case where LLMs wrap JSON responses in markdown code fences (`` ```json ... ``` ``).

### Data Types (`types.py`)

| Type | Fields | Description |
|------|--------|-------------|
| `Headline` | `title`, `url`, `source`, `published`, `summary` | A single RSS headline |
| `Cluster` | `id`, `summary`, `headlines`, `already_covered` | A group of related headlines |
| `Candidate` | `tweet`, `cluster_id`, `cluster_summary` | A generated tweet candidate |
| `ScoredCandidate` | `tweet`, `cluster_id`, `cluster_summary`, `scores`, `avg_score` | A scored candidate with per-model breakdown |

## Twitter Access

This project uses `bird`, a CLI tool that accesses Twitter via browser cookies — no paid API required. `bird` reads cookies from Safari, Chrome, or Firefox on the local machine.

To set up:
1. Log into [x.com](https://x.com) in Safari, Chrome, or Firefox
2. Install `bird`
3. Test: `bird user-tweets @your_handle -n 5`

The system uses two `bird` commands:
- `bird user-tweets @handle -n 10` — fetch recent tweets for deduplication
- `bird tweet "text"` — post a new tweet

If `bird` is not installed or cookies are missing, the pipeline continues without recent tweet data (clustering still works, but can't filter already-covered stories).

## Testing

Run the full test suite (53 tests):

```bash
uv run pytest
```

With verbose output:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest tests/test_scorer.py
```

All tests use mocks — no API calls or network access required.

### Test Coverage

| File | What's Covered |
|------|----------------|
| `test_config.py` | Config loading, YAML parsing, defaults |
| `test_models.py` | JSON extraction, provider detection, markdown fence handling |
| `test_gate.py` | Peak hours logic, timezone handling, window matching |
| `test_aggregator.py` | RSS date parsing, bird CLI integration, error handling |
| `test_clustering.py` | Headline clustering, JSON response parsing, filter logic |
| `test_generator.py` | Candidate generation, 280-char enforcement, prompt formatting |
| `test_scorer.py` | Score parsing, multi-model averaging, threshold filtering, winner selection |
| `test_pipeline.py` | Full pipeline flow, stage ordering, dry-run behavior, error paths |

## Example Run

A typical dry-run produces output like:

```
2026-02-08 23:06:42 [INFO] Loaded config: 8 feeds, models: clustering=claude-haiku-4-5-20251001
    generation=claude-opus-4-6 scoring=['gpt-5.2', 'claude-sonnet-4-5-20250929', 'gemini-3-flash-preview']
2026-02-08 23:06:42 [INFO] Starting rage-bait pipeline (dry_run=True)
2026-02-08 23:06:42 [INFO] Feed https://hnrss.org/frontpage?points=50: 13 headlines
2026-02-08 23:06:42 [INFO] Feed https://techcrunch.com/feed: 6 headlines
2026-02-08 23:06:42 [INFO] Feed https://feeds.bloomberg.com/markets/news.rss: 27 headlines
2026-02-08 23:06:45 [INFO] Total headlines: 46 (from 8 feeds)
2026-02-08 23:06:59 [INFO] Found 31 clusters
2026-02-08 23:06:59 [INFO] 31 clusters after filtering
2026-02-08 23:07:03 [INFO] Cluster 'ai-impact': generated 3 candidates
               ...
2026-02-08 23:09:57 [INFO] Total candidates generated: 93
               ...
2026-02-08 23:29:48 [INFO] Winner (8.7): A solo dev put real-time 3D shaders on a Game Boy
    Color while AAA studios need 3,000 employees and $200M to ship a broken update. The
    entire gaming industry is a jobs program for middle managers.
2026-02-08 23:29:48 [INFO] DRY RUN — would post: [same tweet]
2026-02-08 23:29:48 [INFO] Pipeline complete
```

46 headlines from 8 feeds, clustered into 31 story groups, 93 tweet candidates generated, scored by 3 models, winner selected at 8.7/10.

## Deployment

Currently designed to run locally. Cloud Run deployment is planned:

| Component | Service | Details |
|-----------|---------|---------|
| Pipeline | Cloud Run | Triggered by Cloud Scheduler every 10 min |
| Secrets | Secret Manager | API keys, Twitter cookies, Slack webhook |
| Logging | Better Stack | Structured logging |

Estimated cost: ~$5/month (compute only, no storage).

## Design Documents

- **[DESIGN.md](DESIGN.md)** — Full technical design document (v0.6) with architecture diagrams, component specs, and config reference
- **[RSS_FEEDS.md](RSS_FEEDS.md)** — Research on RSS feed availability, content quality, and selection rationale
- **[FEED_VOLUME_ANALYSIS.md](FEED_VOLUME_ANALYSIS.md)** — Data analysis backing the 12-hour headline window decision

## Known Limitations

- **Daily limit counting is a TODO** — `check_daily_limit()` currently always returns `True`. Needs to parse tweet timestamps from `bird` output.
- **No API error retry** — LLM API failures are caught and logged but not retried. A transient 500 from one scoring model means that candidate gets fewer scores (gracefully degraded, not fatal).
- **Sequential scoring** — Candidates are scored one at a time across all models. With ~90 candidates and 3 models (~270 API calls), a full run takes ~20 minutes. Could be parallelized.
- **Clustering granularity** — Different clustering models produce very different cluster counts (GPT-4o-mini: ~8, Claude Haiku: ~31). More clusters = more candidates = longer scoring time.
- **No programmatic content filter** — Guardrails are prompt-only. No post-generation check for prohibited content before posting.
- **`bird` dependency** — Cookie-based Twitter access is unofficial. If Twitter changes auth flows, `bird` may break with no fallback.
