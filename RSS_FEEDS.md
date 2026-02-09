# RSS Feed Analysis

## Summary

**TL;DR:** No major news outlet provides full article content via RSS. All feeds give headlines + excerpts. For rage-bait generation, this is actually *fine* — we're rewriting headlines, not summarizing articles.

---

## Feed-by-Feed Breakdown

### ✅ Free / No Paywall

| Source | RSS URL | Content Level | Notes |
|--------|---------|---------------|-------|
| **Hacker News** | `https://hnrss.org/frontpage` | Title + link + points/comments | HN is just links anyway; can filter by points (`?points=100`) |
| **TechCrunch** | `https://techcrunch.com/feed` | Headline + excerpt | Free site; Open RSS (`openrss.org`) offers full-text alternative |
| **AP News** | `https://apnews.com/{category}.rss` | Headline + excerpt | Free site; categories: `politics`, `technology`, `business` |
| **Politico** | `https://rss.politico.com/politics.xml` | Headline + summary | Free site; also `/congress.xml`, `/defense.xml` |
| **Axios** | `https://api.axios.com/feed/` | Headline + excerpt | Free site; updates every 15 min |

### 🔒 Paywalled (Subscription May Help)

| Source | RSS URL | Content Level | Paywall Behavior |
|--------|---------|---------------|------------------|
| **Reuters** | `https://feeds.reuters.com/reuters/businessNews` | Headline + summary | Soft paywall; many articles free |
| **Bloomberg** | `https://feeds.bloomberg.com/markets/news.rss` | Headline + truncated | Hard paywall; RSS is promotional only |
| **NYT** | `https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml` | Headline + excerpt | Hard paywall; no authenticated RSS exists |
| **WSJ** | `https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines` | Headline + summary | Hard paywall; must click through |
| **FT** | `https://www.ft.com/?format=rss` | Headline + summary | Hard paywall; subscriber extraction is spotty |

---

## Recommended Feed Set

For rage-bait generation, we only need **headlines** — the excerpt is bonus context. Here's my recommended starter set:

### Tech (2-3 feeds)
```
https://hnrss.org/frontpage?points=50    # HN front page, 50+ points (quality filter)
https://techcrunch.com/feed              # Startup/tech news
```

### Finance (2-3 feeds)
```
https://feeds.reuters.com/reuters/businessNews     # Reuters business (mostly free)
https://feeds.bloomberg.com/markets/news.rss       # Bloomberg markets (headlines only)
https://apnews.com/business.rss                    # AP business
```

### Politics (2-3 feeds)
```
https://rss.politico.com/politics.xml              # Politico main
https://rss.politico.com/congress.xml              # Politico Congress
https://apnews.com/politics.rss                    # AP politics
```

**Total: 8 feeds** — within the 4-9 range.

---

## What About Paywalled Full Content?

Even with a subscription, NYT/WSJ/FT/Bloomberg don't offer authenticated RSS feeds with full text. Options:

1. **Ignore full content** — Headlines are sufficient for tweet generation (recommended)
2. **Scrape on-demand** — When we need more context, fetch the article URL with cookies (complex, fragile)
3. **Use Google News RSS** — `https://news.google.com/rss/search?q=site:nytimes.com+when:1h` gives recent headlines with links

**Recommendation:** Stick with free feeds + Reuters. If tweet quality suffers from lack of context, we can add article fetching later.

---

## Feed URLs to Verify

These should be tested before deployment:

```bash
# Quick validation
curl -s "https://hnrss.org/frontpage?points=50" | head -50
curl -s "https://techcrunch.com/feed" | head -50
curl -s "https://feeds.reuters.com/reuters/businessNews" | head -50
curl -s "https://apnews.com/politics.rss" | head -50
curl -s "https://rss.politico.com/politics.xml" | head -50
curl -s "https://api.axios.com/feed/" | head -50
```

---

## Alternative Approaches

If we want more sources without RSS headaches:

1. **Google News RSS** — Create custom feeds for any source:
   ```
   https://news.google.com/rss/search?q=site:wsj.com+when:1d&hl=en-US
   ```

2. **Open RSS** — `openrss.org` generates full-content feeds for many sites

3. **NewsAPI** — Paid service but gives structured access to 80k+ sources

---

*Last updated: 2026-02-07*
