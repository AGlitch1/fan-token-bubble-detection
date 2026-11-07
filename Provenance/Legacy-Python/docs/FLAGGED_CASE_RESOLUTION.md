# Resolution of the four flagged data cases

**Review date:** 20 September 2026  
**Decision rule:** retain an observation when an independent exchange series or multiple independent sources support the direction and approximate magnitude of the move. Preserve every automatic flag and the original provider value. Do not delete, replace, or winsorize a supported market event.

## Resolution summary

| Case | Automatic flag | Evidence-based decision | Status |
|---|---|---|---|
| OG recent cross-source comparison | CoinGecko p95 difference above 15% | Keep Yahoo as the primary series; the CoinGecko divergence is source-specific | Resolved |
| OG, 23 December 2020 | +120.62% daily log return | Keep as a genuine event-driven move | Resolved |
| ACM, 24 February 2021 | +112.91% daily log return | Keep as a genuine listing-day move | Resolved |
| ALPINE, 1 October 2025 | -131.84% daily log return | Keep as a genuine market crash | Resolved |

## 1. OG cross-source validation review

The automatic Yahoo-versus-CoinGecko comparison remains marked `REVIEW` because its 95th-percentile absolute relative difference is 55.1%, above the 15% threshold. That flag correctly identifies a provider disagreement; it does not establish that Yahoo is wrong.

An independent comparison against official Binance `OGUSDT` daily closing prices covers 361 matched days from 24 September 2025 through 19 September 2026. Yahoo and Binance have a correlation of **0.999997**, a median absolute relative difference of **0.090%**, a 95th-percentile difference of **0.336%**, and a maximum difference of **0.856%**. The disagreement is therefore localized to the CoinGecko series.

**Decision:** `KEEP_YAHOO_PRIMARY`. Retain the Yahoo OG series, retain the automatic `REVIEW` label for transparency, and mark the manual review `RESOLVED`.

Primary evidence:

- Binance daily klines: <https://api.binance.com/api/v3/klines?symbol=OGUSDT&interval=1d&startTime=1758672000000&endTime=1789862400000&limit=1000>
- CoinGecko range endpoint: <https://api.coingecko.com/api/v3/coins/og-fan-token/market_chart/range>

## 2. OG extreme return on 23 December 2020

Yahoo records a move from a prior close of **$2.762308** to **$9.228279**, equivalent to a **+120.62% log return** (about +234% as a simple return). The candle also records a high of $10.174978 and volume of 1,927,957.

CoinGlass independently identifies 23 December 2020 as OG's largest one-day gain, at 233.65%. Binance published its OG/ATM/ASR Launchpool and listing announcement on the same date. An independent academic fan-token study also dates OG explosive-price episodes immediately after this event.

**Decision:** `KEEP`. The observation is a genuine event-driven market move. Keep the raw value and extreme-return flag.

Primary evidence:

- CoinGlass OG historical data: <https://www.coinglass.com/currencies/OG/historical-data>
- Binance Launchpool/listing announcement: <https://www.binance.com/si-LK/support/announcement/detail/2d09f64f2f9649ae93c111fc0096b361>
- Independent academic study: <https://iris.ru.is/ws/files/193795749/SSRN-id4408621.pdf>

## 3. ACM extreme return on 24 February 2021

Yahoo records a move from a prior close of **$5.944448** to **$18.385660**, equivalent to a **+112.91% log return**. Official Binance `ACMUSDT` data records a closing price of **$17.822** on the same date, only about **3.16%** below Yahoo, and an intraday high of $25.46.

Binance's official announcement states that ACM spot trading opened on 24 February 2021 at 11:00 UTC after a token sale priced at approximately $4.875 and reported as 1,484 times oversubscribed.

**Decision:** `KEEP`. The observation is a genuine listing-day market move. Keep the raw value and extreme-return flag.

Primary evidence:

- Binance daily klines: <https://api.binance.com/api/v3/klines?symbol=ACMUSDT&interval=1d&startTime=1613952000000&endTime=1614643200000&limit=1000>
- Binance ACM listing announcement: <https://www.binance.com/en/support/announcement/detail/af83f5b390a54a05a076b7fbe83c70d9>

## 4. ALPINE extreme return on 1 October 2025

Yahoo records a move from a prior close of **$6.615793** to **$1.770193**, equivalent to a **-131.84% log return** (about -73.2% as a simple return). Official Binance `ALPINEUSDT` data records a close of **$1.764**, only about **0.35%** below Yahoo, with an intraday range of $1.302 to $6.725. CoinGecko's adjacent UTC observation and contemporaneous reporting independently confirm the crash.

**Decision:** `KEEP`. The observation is a genuine market crash rather than a bad tick. Keep the raw value and extreme-return flag.

Primary evidence:

- Binance daily klines: <https://api.binance.com/api/v3/klines?symbol=ALPINEUSDT&interval=1d&startTime=1758844800000&endTime=1759795200000&limit=1000>
- CoinGecko range endpoint: <https://api.coingecko.com/api/v3/coins/alpine-f1-team-fan-token/market_chart/range>
- Contemporaneous report: <https://www.svsport.it/2025/10/01/leggi-notizia/argomenti/altri-sport-1/articolo/alpine-fan-token-crolla-del-73-scendendo-sotto-i-2-dollari.html>

## Final data treatment

All four cases are resolved. The pipeline makes **zero price replacements, zero deletions, and zero winsorization adjustments**. It carries the original observations into the analysis-ready panel, preserves the automatic flags, and attaches the evidence, decision, reviewer status, and review date to the generated audit tables.
