# RSS Feed Volume Analysis

**Analysis date:** 2026-02-08 (late Saturday night)

## Raw Headline Counts by Time Window

| Feed | 6h | 8h | 12h | 24h |
|------|----|----|-----|-----|
| HN (50+ points) | 1 | 2 | 8 | 16 |
| Politico | 0 | 1 | 4 | 7 |
| TechCrunch | 2 | 3 | 4 | 5 |
| Bloomberg Markets | 0 | 2 | 3 | 14 |
| **TOTAL (4 feeds)** | **3** | **8** | **19** | **42** |

**Extrapolated to 8 feeds:** 6 / 16 / 38 / 84 headlines

## Clustering Estimate

With 8 feeds covering similar events, expect ~30-50% of headlines to cluster together.

| Window | Raw Headlines | Estimated Unique Clusters |
|--------|---------------|---------------------------|
| 6h | ~6 | ~3-4 |
| 8h | ~16 | ~9-12 |
| 12h | ~38 | **~22-30** |
| 24h | ~84 | ~50-67 |

## Recommendation

**12-hour window** is the sweet spot:
- Enough clusters (~22-30) to pick 1-3 good tweets
- Not so many that we're drowning in stale news
- Matches a "morning news digest" + "evening news digest" cadence

**6-hour is too narrow** — on a quiet Saturday night, only ~3-4 clusters available.

---

## Notes

- Saturday night is a low-volume period; weekday volume would be 2-3x higher
- HN has built-in quality filter (50+ points) which reduces volume significantly
- Bloomberg/Reuters generate many more headlines than Politico/TechCrunch
- AP News and Axios (not tested) would add more volume

---

*Analysis based on live RSS feed pulls on 2026-02-07*
