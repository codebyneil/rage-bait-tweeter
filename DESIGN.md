# Rage-Bait Tweeter — Technical Design

## Overview

An autonomous system that scrapes RSS headlines from tech, finance, and politics sources, transforms them into maximally engaging "rage-bait" tweets via AI, and posts them to Twitter — all without requiring paid API access.

---

## Goals

- **Real-time:** Headlines → tweets in under 30 minutes
- **Volume:** ~1-3 tweets per day (start conservative)
- **Tone:** Snarky pundit persona
- **Guardrails:** No fabrication, no defamation, stays within original headline's facts
- **Tracking:** All tweets mirrored to Slack with full context

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     1. AGGREGATE                            │
├─────────────────────────────────────────────────────────────┤
│  RSS Feeds (8) ──▶ All Headlines (last 12h)                 │
│  bird user-tweets ──▶ Recent Tweets (last 10)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              2. CLUSTER (midtier model)                     │
├─────────────────────────────────────────────────────────────┤
│  "Group these headlines by story/event"                     │
│  Output: [ {cluster_id, headlines[], summary}, ... ]        │
│  Expected: ~20-30 clusters from 12h window                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              3. FILTER (midtier model)                      │
├─────────────────────────────────────────────────────────────┤
│  "Does any cluster match a recent tweet? Drop it."          │
│  Output: surviving clusters                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             4. GENERATE (thinking model)                    │
├─────────────────────────────────────────────────────────────┤
│  For each cluster (serially):                               │
│    "Generate 1-3 rage-bait tweets for this story"           │
│  Output: all candidates                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              5. SCORE (multi-model panel)                   │
├─────────────────────────────────────────────────────────────┤
│  Send all candidates to multiple models:                    │
│    "Rate 1-10 how rage-bait-y is this tweet?"               │
│  Aggregate scores, pick winner                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    [ Tweet winner + Slack ]
```

**Fully stateless.** No database. Twitter is the source of truth for posted tweets.

See `FEED_VOLUME_ANALYSIS.md` for expected cluster counts by time window.

---

## Components

### 1. Aggregator

**Responsibility:** Gather all inputs for the pipeline.

**RSS Poller:**
- Polls all 8 feeds
- Filters to last 12 hours (configurable)
- Emits: `{ headline, url, source, publishedAt, summary? }`

**Recent Tweets:**
- `bird user-tweets @handle -n 10`
- Used by clustering model to filter already-covered stories

**Feeds (8 sources across categories):**

| Category | Feed | URL |
|----------|------|-----|
| Tech | Hacker News (50+ pts) | `https://hnrss.org/frontpage?points=50` |
| Tech | TechCrunch | `https://techcrunch.com/feed` |
| Finance | Reuters Business | `https://feeds.reuters.com/reuters/businessNews` |
| Finance | Bloomberg Markets | `https://feeds.bloomberg.com/markets/news.rss` |
| Finance | AP Business | `https://apnews.com/business.rss` |
| Politics | Politico | `https://rss.politico.com/politics.xml` |
| Politics | Politico Congress | `https://rss.politico.com/congress.xml` |
| Politics | AP Politics | `https://apnews.com/politics.rss` |

See `RSS_FEEDS.md` for detailed analysis. All feeds provide headlines + excerpts (no full content), which is sufficient for tweet generation.

---

### 2. Clustering (Midtier Model)

**Responsibility:** Group headlines by story/event, filter already-covered stories.

**Input:**
```json
{
  "headlines": [...],  // All headlines from last 12h
  "recent_tweets": [...] // Our last 10 tweets
}
```

**Output:**
```json
{
  "clusters": [
    {
      "id": "fed-rate-cut",
      "summary": "Fed signals potential rate cut amid inflation concerns",
      "headlines": [...],
      "already_covered": false
    },
    ...
  ]
}
```

**Prompt Strategy:**
- Group headlines that cover the same underlying story
- Cross-reference with recent tweets to mark already-covered clusters
- Drop clusters that match recent tweets

**Model:** Configured via `models.clustering` (fast, cheap, good at classification)

---

### 3. Generation (Thinking Model)

**Responsibility:** Generate 1-3 rage-bait tweet candidates per cluster.

**Input:** Surviving cluster with headlines + summary

**Output:**
```json
{
  "cluster_id": "fed-rate-cut",
  "candidates": [
    "The Fed is about to make your savings worthless and they're calling it 'good news.' 🙃",
    "Breaking: Powell admits the economy is cooked but hey, at least your 401k looks pretty 📉",
    "Another day, another Fed announcement designed to help banks and screw everyone else"
  ]
}
```

**Prompt Strategy:**
- System prompt establishes snarky pundit persona
- Instructs to maximize engagement (outrage, controversy, hot takes)
- Hard guardrails: must not fabricate facts, must not defame individuals
- Few-shot examples of good rage-bait
- Generate multiple options (1-3) per cluster

**Model:** Configured via `models.generation` (needs creativity + judgment)

---

### 4. Scoring Panel (Multi-Model)

**Responsibility:** Rate all candidates, pick the winner.

**Input:** All tweet candidates from all clusters

**Output:**
```json
{
  "scores": [
    { "tweet": "...", "gpt4o": 8.5, "sonnet": 7.2, "gemini": 8.0, "avg": 7.9 },
    ...
  ],
  "winner": { "tweet": "...", "score": 8.7 }
}
```

**Scoring Prompt:**
```
Rate this tweet 1-10 on "rage-bait-iness" — how likely is it to drive 
engagement through outrage, hot takes, or controversy?

Consider: provocativeness, shareability, emotional punch, clarity.
Do NOT penalize for being controversial — that's the point.

Tweet: {tweet}

Reply with just a number 1-10.
```

**Model Panel:** Configured via `models.scoring` (list of models for multi-model panel)

**Aggregation:** Simple average of all panel scores. Log individual scores for future tuning.

**Threshold:** Average must be ≥ 6.5/10 to post. If no candidates meet threshold, skip this run.

---

### 5. Peak Hours Gate

**Responsibility:** Only run during optimal posting times.

**Peak Hours** are configurable via `peak_hours.windows` in config. Default windows (US Eastern):
- Morning: 7-9 AM ET
- Lunch: 12-1 PM ET
- Evening: 5-8 PM ET
- Late night doomscroll: 9-11 PM ET

**Logic:**
- Scheduler triggers periodically (every 10 min on Cloud Run, or cron locally)
- First check: are we in a peak window? If not, exit immediately (no cost)
- Second check: have we hit daily limit? If yes, exit

---

### 6. Twitter Poster

**Responsibility:** Post tweets using `bird` library (cookie-based, no API key).

**Details:**
- Uses existing Twitter account credentials (cookies)
- Handles rate limits gracefully (back off if throttled)
- Returns tweet URL on success

**Error Handling:**
- Retry transient failures (network, 5xx)
- Alert to Slack on persistent failures
- Skip and log if tweet is rejected (duplicate, content filter)

<!-- TODO: Define retry/backoff strategy for AI API failures across all pipeline stages -->

---

### 7. Slack Notifier

**Responsibility:** Mirror all activity to `#friday-twitter-news`.

**Message Format:**
```
🐦 *New Tweet Posted*

> The Fed is about to make your savings worthless and they're calling it "good news." 🙃

📰 *Original:* Fed Signals Potential Rate Cut Amid Inflation Concerns
🔗 *Source:* Reuters — https://reuters.com/...
🐦 *Tweet:* https://twitter.com/.../status/...
```

**Also notify on:**
- Skipped headlines (with reason)
- Errors/failures
- Daily summary (optional)

---

## Data Storage

**None required.** Fully stateless design:

- **Seen headlines:** Not tracked. We re-evaluate RSS items until they age out of the feed. Acceptable redundant OpenAI calls.
- **Posted tweets:** Read from Twitter via `bird user-tweets @handle` before posting.
- **Tweet queue:** Not needed. Post immediately during peak hours, skip otherwise.
- **Daily count:** Derive from `bird user-tweets` timestamps (count tweets from today).

---

## Infrastructure (GCP) — Simplified

**Language:** Python 3.12+ with `uv` for dependency management

| Component | GCP Service | Trigger |
|-----------|-------------|---------|
| Main Service | Cloud Run | Cloud Scheduler (every 10 min) |
| Secrets | Secret Manager | Twitter cookies, OpenAI key, Anthropic key, Slack webhook |
| Logging | Better Stack | — |

**No database.** Fully stateless.

**Single Cloud Run service** handles everything in one invocation:
1. Check if we're in peak hours → exit early if not
2. Check daily tweet count via `bird user-tweets` → exit if at limit
3. **Aggregate:** Poll RSS feeds (last 12h) + fetch recent tweets
4. **Cluster:** Group headlines by story/event (midtier model)
5. **Filter:** Drop clusters that match recent tweets (midtier model)
6. **Generate:** Create 1-3 rage-bait candidates per surviving cluster (thinking model)
7. **Score:** Multi-model panel rates all candidates, pick winner if ≥ 6.5/10
8. Post winner via `bird tweet`
9. Notify Slack

<!-- TODO: Add retry/backoff strategy for AI API failures (OpenAI, Anthropic, Google) -->

**Cost Estimate:** ~$5/month (compute only, no storage)

---

## Configuration

```yaml
# config.yaml
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

twitter:
  handle: "@rage_takes"  # TBD
  cookies_secret: projects/xxx/secrets/twitter-cookies

models:
  clustering: gpt-4o-mini              # Group headlines, filter duplicates
  generation: claude-sonnet-4-5-20250929  # Generate rage-bait candidates (with thinking)
  scoring:                              # Multi-model panel
    - gpt-4o
    - claude-sonnet-4-5-20250929
    - gemini-2.0-flash

slack:
  webhook_secret: projects/xxx/secrets/slack-webhook

limits:
  max_tweets_per_day: 3
  headline_window_hours: 12            # Look back 12h for headlines
  min_score_threshold: 6.5             # Skip if best candidate < 6.5/10

peak_hours:
  timezone: America/New_York
  windows:
    - { start: "07:00", end: "09:00" }
    - { start: "12:00", end: "13:00" }
    - { start: "17:00", end: "20:00" }
    - { start: "21:00", end: "23:00" }
```

---

## Open Questions

1. ~~**Twitter account:** Which account? Need to extract cookies via `bird` setup.~~ → Deferred
2. ~~**Final RSS feed list:** Confirm sources — any paywalled feeds to handle?~~ → Done, see `RSS_FEEDS.md`
3. ~~**Slack notifications:** Webhook to this channel, or use OpenClaw's native Slack?~~ → Separate webhook
4. ~~**Cluster volume:** How many clusters per run?~~ → Done, see `FEED_VOLUME_ANALYSIS.md` (~22-30 in 12h window)
5. ~~**Scoring aggregation:** How to combine multi-model scores?~~ → Simple average of 3 models
6. ~~**Rage-bait threshold:** How "rage-bait-y" must a tweet be to post?~~ → Minimum 6.5/10 average; skip run if nothing qualifies
7. **Monitoring/Alerting:** Just Slack errors for now? Or Better Stack alerting?
8. **Analytics:** Track engagement metrics later? (Would require API access or scraping)

---

## Next Steps

1. ~~Neil confirms feed list + Twitter account~~ → Feeds done, Twitter deferred
2. [x] Evaluate design docs + initialize git repo
3. [ ] Build Python project with `uv`
4. [ ] Implement RSS aggregator (feed polling + headline extraction)
5. [ ] Build headline clustering (midtier model)
6. [ ] Build duplicate/similarity filter (midtier model)
7. [ ] Build rage-bait generator (thinking model)
8. [ ] Build multi-model scoring panel
9. [ ] Implement peak hours gate
10. [ ] Integrate `bird` for reading + posting
11. [ ] Wire up Slack webhook notifications
12. [ ] Test in "dry run" mode (Slack only, no Twitter)
13. [ ] Deploy to Cloud Run + Scheduler (later)
14. [ ] Connect Twitter account + go live

---

---

## Changelog

- **v0.6** (2026-02-08): Reconciled Infrastructure section with 5-stage pipeline; made models, peak hours, and feeds configurable; updated model IDs; fixed component numbering; fixed Politico feed URL; updated Next Steps
- **v0.5** (2026-02-07): Finalized scoring — simple average, 6.5/10 threshold; design doc complete
- **v0.4** (2026-02-07): Multi-stage pipeline with clustering, generation, and multi-model scoring panel; 12h headline window; feed volume analysis complete
- **v0.3** (2026-02-07): Fully stateless — no Firestore, use `bird` to read recent tweets, Haiku for similarity check, 1-3 tweets/day
- **v0.2** (2026-02-07): Finalized RSS feeds, simplified to single Cloud Run service, Python/uv, separate Slack webhook
- **v0.1** (2026-02-07): Initial draft

*Author: F.R.I.D.A.Y.*
