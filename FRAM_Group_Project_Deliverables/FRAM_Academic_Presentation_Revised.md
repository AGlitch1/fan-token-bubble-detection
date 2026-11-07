# 01. Bubble Detection and Dating in Fan Tokens

**Why this matters:** Fan-token price swings create financial risk. This study examines whether unusual price dynamics persist and how return risk changes.

**Recursive explosive-root tests, return change points, and Bayesian local price dynamics**

- Financial Risk Analytics and Management · Group G07
- Study universe · 20 sports fan tokens and three cryptocurrency benchmarks

---

# 02. Research Question and Study Objectives

**Why this matters:** A sharp price move alone gives an incomplete picture. These objectives connect detection with duration and economic interpretation.

**Research question**  
To what extent do daily fan-token prices exhibit persistent explosive dynamics, and how do those dynamics relate to changes in return risk?

- **Detection.** Identify whether any admissible window in each token’s log-price history exhibits a right-tailed ADF statistic above the published reference level.
- **Dating.** Measure the duration of consecutive daily BSADF threshold exceedances and apply the study’s 30-day persistence criterion.
- **Regime characterization.** Determine whether the return mean or volatility proxy changes over time, and assess daily Bayesian support for a positive local ADF slope.
- **Economic interpretation.** Compare the statistical signals with the direction of realized prices, benchmark assets, and the change in evidence after extending the sample.

---

# 03. Institutional Context and Literature

**Why this matters:** The rights attached to fan tokens and the existing research help explain why we examine their price dynamics.

- Sports fan tokens are tradable digital assets that may provide limited voting rights, rewards, or access to fan experiences. They confer no equity ownership or claim on club earnings.
- Demand can reflect fan engagement, speculation, and broader cryptocurrency conditions. Prior research reviewed in the report associates some return movements with sporting information and attention.
- Assaf, Demir, and Ersan (2024) report explosive behavior in 13 of 20 fan tokens. That study motivates testing how the frequency and duration of signals vary under this project’s sample and decision rules.
- Recursive right-tailed tests assess explosive dynamics in the price process. An economic bubble interpretation also requires evidence about persistence, price direction, and the relationship between price and fundamentals.
- Heavy tails, volatility shifts, and differences in listing histories complicate comparison across assets. The project evaluates the price signal alongside return and local-model diagnostics.

---

# 04. Sample Construction and Observation Periods

**Why this matters:** The assets and observation dates determine which episodes the study can detect and how broadly its findings apply.

- The study fixes a universe of **20 sports fan tokens** using a CoinGecko category snapshot dated 20 September 2026. FIGHT was excluded because its accessible price history was limited. BlockchainSpace was excluded on classification grounds. The Portugal National Team Fan Token was included.
- Each asset enters the unbalanced panel on its first valid trading date. Fan-token histories begin between **22 April 2020** and **27 November 2022**.
- The primary sample ends on **30 June 2026** and contains **37,662 fan-token prices**. Histories range from 1,312 to 2,261 prices per token.
- The extension ends on **19 September 2026** and contains **39,282 fan-token prices** and **39,262 fan-token returns**. The same 20 assets are used at both cutoffs.
- Bitcoin (BTC) and Ethereum (ETH) provide broad crypto comparisons. Chiliz (CHZ) provides a benchmark associated with the fan-token ecosystem.

---

# 05. Data Preparation and Validation

**Why this matters:** Data errors can resemble explosive price moves. Validation helps establish whether extreme observations reflect actual trading.

- The primary input is the **daily adjusted USD close** from archived Yahoo Finance histories. Dates are aligned to a UTC trading calendar.
- Standardize field types, verify one record per asset-date, and screen nonpositive prices. Preserve missing dates in the calendar and compute daily returns only across consecutive valid days.
- Cross-check recent price histories against CoinGecko. Investigate flagged observations using exchange candles and, where applicable, contemporaneous market records.
- For OG, a divergence between Yahoo Finance and CoinGecko prompted a Binance comparison over **361 overlapping dates**. The Yahoo–Binance correlation was **0.999997** and the median absolute relative price difference was **0.090%**.
- Retain verified large moves in OG, ACM, and ALPINE. Retain **233 zero-reported-volume token-days** where closing prices remain valid. Reported volume was used diagnostically because vendor definitions vary.
- The cleaning procedure uses no forward-filling or winsorization. The report records continuous valid price histories for the 20 retained tokens from their first usable dates to the extension cutoff.

---

# 06. Variable Definitions and Transformations

**Why this matters:** Each method uses a different transformation of the same prices. These definitions explain what each result measures.

| Variable | Construction | Application |
|---|---|---|
| Adjusted close, Pₜ | Daily closing price in USD | Economic interpretation and price-path figures |
| Log price, yₜ | ln(Pₜ) | Recursive ADF tests and Bayesian local ADF model |
| Daily log return, rₜ | 100 × [ln(Pₜ) − ln(Pₜ₋₁)] | Return statistics, correlations, and mean-change segmentation |
| Annualized rolling volatility | Standard deviation of the latest 30 daily log returns × √365 | Descriptive comparison of risk over time |
| Log-squared return | Log transformation of squared daily returns | Separate change-point fit for the volatility proxy |

- A return expressed as 100 times a log-price change differs from the simple percentage price change reported for the September intervals.
- Interval price changes are calculated from the first and last USD closes, as 100 × [(ending price ÷ starting price) − 1].

---

# 07. Distributional Properties of Fan-Token Returns

**Why this matters:** Large outliers and clusters of volatile days affect risk measurement and motivate the separate volatility analysis.

- Mean daily log returns across the September panel ranged from **−0.229% for LAZIO** to **+0.043% for VATRENI**. Daily return standard deviations ranged from **3.666% for AFC** to **10.224% for VATRENI**.
- Excess kurtosis ranged from **15.54 for AFC** to **108.28 for ACM**. Skewness ranged from **−2.260 for ALPINE** to **4.164 for ACM**, indicating substantial differences in the direction of return asymmetry.
- Median annualized 30-day rolling volatility ranged from **48.26% for NAP** to **131.23% for VATRENI**.
- Lag-one autocorrelation ranged from **−0.135 to 0.075** for signed returns and from **0.241 to 0.476** for absolute returns. The consistently positive absolute-return correlations indicate volatility clustering.
- These properties motivate examining volatility regimes separately and interpreting published explosive-root reference levels with care.

---

# 08. Return Co-Movement and Benchmark Selection

**Why this matters:** Benchmark comparisons help assess how much fan-token returns move with the wider crypto market.

Correlation measures how closely daily returns move together. Values near +1 indicate stronger movement in the same direction.

| Comparison | Mean return correlation |
|---|---:|
| Fan tokens with Bitcoin (BTC) | 0.314 |
| Fan tokens with Ethereum (ETH) | 0.338 |
| Fan tokens with Chiliz (CHZ) | 0.421 |

**Main finding:** CHZ has the strongest average relationship with fan-token returns among these benchmarks. Correlation alone cannot establish causation.

---

# 09. What Each Method Contributes

**Why this matters:** We need separate evidence about unusual price dynamics, signal duration, and changes in risk.

| Method | Question it answers | Output |
|---|---|---|
| SADF / GSADF | Did an explosive price window occur? | Maximum test statistic and reference comparison |
| BSADF dating | How long did the signal last? | Daily statistics and interval dates |
| Return segmentation | When did return behaviour change? | Break dates and counts |
| Bayesian local ADF | Does the local model support explosiveness? | Daily slope and reset probabilities |

**Reading order:** Examine the June results first, then the September extension. The following slides explain each method.

---

# 10. SADF and GSADF: Detecting Explosive Price Dynamics

**Why this matters:** Explosive behaviour can occur briefly within a long price history. Searching different windows helps locate that evidence.

The right-tailed augmented Dickey–Fuller (ADF) test compares a random-walk benchmark with an explosive price process.

- **SADF** keeps the starting date fixed and moves the end date.
- **GSADF** moves both dates, helping detect separate episodes later in the history.
- **Output:** Each method returns one maximum statistic per token. A statistic above its published reference flags evidence of explosiveness somewhere in that history.

**Interpretation:** This comparison alone gives no duration for the signal. Slide 11 explains the dating procedure.

---

# 11. BSADF Dating: Measuring Signal Duration

**Why this matters:** A history can contain an extreme statistic even when the signal lasts only a few days. Dating measures that persistence.

BSADF finds the largest ADF statistic across eligible windows ending on each date.

- **Output:** A daily sequence, compared with an approximate 95% dating reference.
- **Dating rule:** Count consecutive days above that reference. Retain intervals lasting **at least 30 days**.
- **Reported information:** Start date, duration, and whether the interval remains open at the sample cutoff.

**Interpretation:** Duration measures persistence of the statistical signal. The actual price path establishes whether prices rose or fell.

---

# 12. Change Points: Identifying Changes in Return Risk

**Why this matters:** Risk can change materially even when explosive price signals are brief. Segmentation identifies shifts in return behaviour.

The method divides each series into segments with different fitted levels.

- **Return series:** Breaks identify changes in average daily returns.
- **Log-squared-return series:** Squared returns capture move size. Their log transformation provides a volatility proxy whose breaks indicate changes in variability.
- **Output:** Dates and counts of detected changes for each token and each series.

**Interpretation:** This method describes changes in returns and risk. Bubble detection comes from the price tests.

---

# 13. Bayesian Local ADF: Assessing Local Explosiveness

**Why this matters:** A maximum over historical windows can hide brief disturbances. This model examines support for explosiveness date by date.

The Bayesian model updates its assessment as observations enter, allowing the local price relationship to reset.

- **Positive-slope probability:** Model-based support for an explosive local ADF coefficient.
- **New-run probability:** Model-based support for starting a new regime.
- **Reading guide:** Look for repeated positive-slope probabilities of **at least 95%**, and compare their timing with resets.

**Interpretation:** These probabilities depend on model assumptions. Full-sample scaling makes the reported estimates retrospective.

---

# 14. June Results: Explosive Windows in 9 of 20 Tokens

**Why this matters:** The first result establishes how many token histories contain explosive-window evidence before we examine duration.

Through **30 June 2026**:

| Method | Tokens above the nominal 5% reference |
|---|---:|
| SADF, fixed starting date | 4 of 20 |
| GSADF, flexible starting dates | 9 of 20 |

**Interpretation:** GSADF's wider window search identifies evidence in more token histories. These counts alone do not establish persistent bubbles.

**Caution:** The classifications use published references, with no adjustment for testing 20 tokens.

---

# 15. June Persistence: No Fan Token Reached 30 Days

**Why this matters:** Duration distinguishes brief threshold crossings from intervals that meet the study's persistence rule.

The output below is the longest consecutive BSADF run through **30 June 2026**.

| Series | Longest run |
|---|---:|
| Portugal (POR), longest among fan tokens | 22 days |
| Bitcoin (BTC) | 27 days |
| Ethereum (ETH) | 10 days |
| Chiliz (CHZ) | 53 days |

**Interpretation:** No fan token met the **30-day** rule. CHZ was the only benchmark that did. The June global signals were therefore stronger evidence of brief explosive windows than of persistent fan-token intervals.

---

# 16. June Change Points: Volatility Shifts Dominate

**Why this matters:** Brief explosive signals can coexist with substantial changes in risk. The break counts show which return feature changes most.

The segmentation method reports **125 changes** across the 20 fan tokens.

| Fitted series | Detected changes |
|---|---:|
| Average daily returns | 29 |
| Log-squared returns, the volatility proxy | 96 |

**Main finding:** Volatility-proxy breaks account for **76.8%** of these detections. Return variability changes more frequently than the fitted mean under this specification.

---

# 17. June Bayesian Results: Strong Readings Were Isolated

**Why this matters:** The local model checks whether the historical-window evidence comes with sustained daily support for explosiveness.

Across **37,642 fan-token daily estimates**:

- Only **5 estimates**, about **0.013%**, reached the **95% positive-slope guide**.
- Those readings occurred on isolated dates across four tokens.
- Several coincided with model resets. One occurred at initialization.

**Interpretation:** The model provides limited support for a sustained explosive local coefficient. This helps explain why the June global detections and short dating runs lead to a cautious persistence assessment.

---

# 18. September Extension: Two Intervals Meet the Duration Rule

**Why this matters:** A longer observation window can reveal new episodes and allow an existing signal to accumulate more days.

| Fan-token measure | Through 30 June | Through 19 September |
|---|---:|---:|
| Tokens above the nominal 5% GSADF reference | 9 of 20 | 10 of 20 |
| BSADF intervals lasting at least 30 days | 0 | 2 |

- **Argentina (ARG)** joined the GSADF exceedance group.
- The qualifying intervals belong to **Portugal (POR)** and **Argentina (ARG)**.

**Interpretation:** Additional data change the reported classifications. Both samples use retrospective fits.

---

# 19. September Intervals: Persistent Signals During Price Declines

**Why this matters:** The two qualifying intervals show why a persistent statistical signal needs an economic interpretation.

| Measure | Portugal (POR) | Argentina (ARG) |
|---|---|---|
| Interval in 2026 | 15 June–19 September | 21 July–23 August |
| Consecutive signal duration | 97 days | 34 days |
| First-to-last closing-price change | **−69.9%** | **−44.2%** |
| Status at the September cutoff | Ongoing | Closed |

**Main finding:** Both intervals pass the 30-day rule while prices fall sharply. Neither contains a Bayesian positive-slope probability reaching 95%.

---

# 20. Reading Price, BSADF, and Bayesian Paths Together

**Why this matters:** The diagnostic paths explain how long threshold crossings can coexist with falling prices and limited local explosive support.

- **Price path:** Shows the realised direction and size of the move. Both retained intervals contain large net declines.
- **BSADF path:** Shows daily threshold exceedances. Each endpoint searches windows that can include earlier movements, so the signal can remain high during a decline.
- **Bayesian path:** Shows support for the local explosive coefficient. It stays below the 95% guide throughout both intervals.

**Interpretation:** The price path establishes the economic outcome. The other paths describe different statistical features of that interval.

---

# 21. Synthesis of the Empirical Evidence

**Why this matters:** Combining the results gives a more complete assessment of persistence and risk than any single diagnostic.

| Evidence | What it contributes |
|---|---|
| June: 9 of 20 GSADF exceedances, no 30-day fan-token runs | Unusual windows with limited persistence |
| June: 96 volatility-proxy breaks and 29 mean breaks | Repeated changes in return risk |
| June: five isolated high Bayesian readings | Limited sustained local explosive support |
| September: two retained intervals with large price declines | Persistent signals can accompany corrections |

**Overall interpretation:** The sample shows intermittent explosive dynamics and changing volatility. Evidence of sustained speculative appreciation is limited.

---

# 22. Implications for Market-Risk Monitoring

**Why this matters:** A statistical alert becomes useful for monitoring when its duration, price direction, and risk context are clear.

1. **Record the signal:** Asset, threshold, duration, and whether the interval remains open.
2. **Review the price path:** Calculate the interval gain or loss and inspect reversals within it.
3. **Review risk and context:** Check volatility changes, benchmark movements, and data quality.

**Practical output:** A documented assessment of the flagged interval, including its economic outcome.

**Scope:** This is an implication of the retrospective evidence. The study does not evaluate live alert performance.

---

# 23. Implications for Stress Testing and Exposure Management

**Why this matters:** The observed interval losses provide concrete historical scenarios for examining exposure to fan-token risk.

- **Historical scenarios:** POR fell **69.9%** and ARG fell **44.2%** across their retained intervals.
- **Direct impact calculation:** For a simple unlevered position, scenario gain or loss equals position value multiplied by the scenario return.
- **Additional assumptions:** Combined market shocks and forced-sale costs require explicit inputs. The report does not estimate liquidity or execution costs.

**Interpretation:** These losses provide historical scenario magnitudes. Estimating their future probabilities or worst-case losses requires further analysis.

---

# 24. Limitations That Affect Interpretation

**Why this matters:** The thresholds, sample, and model assumptions determine how confidently we can interpret the reported findings.

- **Approximate references:** Published global values and an SADF-based dating approximation make classifications sensitive to calibration and the 30-day rule.
- **Multiple comparisons and selection:** Twenty token tests have no multiplicity correction. A September category snapshot defines the June universe.
- **Bayesian assumptions:** Priors, fixed variance, and reset choices affect probabilities. Full-sample scaling makes the estimates retrospective.
- **Economic attribution:** The study estimates neither fundamental value nor causal effects of sporting events. All methods share the same prices.

**Consequence:** Results describe this sample under the chosen specifications. Live alert performance and economic bubble attribution remain unestablished.

---

# 25. Proposed Extensions and Their Outputs

**Why this matters:** Further analysis could check robustness and explain the signals more fully. These Phase 2 proposals were not implemented in the Phase 3 results.

| Proposed method | Why it is needed | Expected output |
|---|---|---|
| Wild bootstrap | Address changing volatility | Recalibrated references |
| Alternative duration rules | Check persistence sensitivity | Revised interval counts and dates |
| Sequential Kolmogorov–Smirnov monitoring | Check broader distribution changes | Change alerts and dates |
| Bayesian return-regime model | Assess changes in return risk | Change probabilities |
| Hierarchical dynamic logit | Examine predictors across tokens | Estimated links with the signal state |

**Status:** Future work. The reported results use the methods on slides 10–13.

---

# 26. Conclusions

**Why this matters:** The findings clarify what the study can contribute to understanding and managing fan-token risk.

- **Explosive windows occur:** Nine of 20 tokens exceeded the June GSADF reference, but none met the 30-day dating rule.
- **Return risk changes repeatedly:** Volatility-proxy shifts account for most June fan-token change points.
- **Long signals can accompany losses:** The September POR and ARG intervals combine persistent threshold crossings with severe price declines.

**Conclusion:** Fan-token risk assessment should combine signal duration with the price path and volatility evidence. This sample provides limited evidence of sustained speculative appreciation.

---

# 27. Selected References and Data Sources

**Why this matters:** These sources document the test foundations, prior fan-token research, and the provenance of the price observations.

- **Fan-token research:** Assaf, Demir, and Ersan (2024), *Detecting and date-stamping bubbles in fan tokens*.
- **Recursive tests:** Phillips, Wu, and Yu (2011), and Phillips, Shi, and Yu (2015a, 2015b).
- **Robust inference:** Harvey et al. (2016, 2025), and Lui, Phillips, and Yu (2024).
- **Bayesian framework:** Adams and MacKay (2007).
- **Price and validation sources:** Yahoo Finance, CoinGecko, Binance, and CoinGlass.

Full citations and DOIs appear in the accompanying notes and report references.
