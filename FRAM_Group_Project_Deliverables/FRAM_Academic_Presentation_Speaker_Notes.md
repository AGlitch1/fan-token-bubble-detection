# 01. Bubble Detection and Dating in Fan Tokens

**Visual brief**

Use a white or light background with the title, group, and study period. Use a small schematic price trace if desired. The empirical charts on later slides provide the visual context for the study.

**Report source**

Title page and §6.2, pp. 1, 12.

---

# 02. Research Question and Study Objectives

**Visual brief**

Show four boxes labelled Detection, Dating, Regime Characterization, and Economic Interpretation. Keep the research question above the boxes.

**Report source**

§§3, 4.1, 6.2–6.3, pp. 4–5, 12–13.

---

# 03. Institutional Context and Literature

**Visual brief**

Use a three-column structure for token characteristics, prior evidence, and the empirical problem. A simple ownership-versus-perks diagram can illustrate the asset structure.

**Report source**

§§1–2.5, pp. 1–4. Cite Assaf et al. (2024) and Ante et al. (2024a, 2025).

---

# 04. Sample Construction and Observation Periods

**Visual brief**

Redraw Table 3 as a horizontal sample-coverage chart, with a start marker for each token and vertical lines at the two cutoffs. Place the benchmark names in a separate row.

**Report source**

§§5.1, 5.4, 6.1–6.2 and Tables 2, 3, 6, pp. 7–9, 12.

---

# 05. Data Preparation and Validation

**Visual brief**

Use a validation flow from source data to the analysis panel. Include OG as a small audit example with the overlap and median discrepancy figures.

**Report source**

§§5.1–5.3, pp. 7–8.

---

# 06. Variable Definitions and Transformations

**Visual brief**

Use the table as the slide. Group the rows visually into price inputs, return inputs, and risk measures.

**Report source**

§§5.2, 5.5, 6.3, 6.8 and Table 4, pp. 8–10, 13, 17.

---

# 07. Distributional Properties of Fan-Token Returns

**Visual brief**

Use Figure 1’s indexed-price and rolling-volatility panels. If the original composite is too dense, retain the indexed-price panel and show the volatility and autocorrelation ranges as labelled horizontal intervals.

**Report source**

§5.5, Table 4 and Figure 1, pp. 9–11.

---

# 08. Return Co-Movement and Benchmark Selection

**Presenter explanation**

Each benchmark value averages its correlations with the 20 fan tokens. These are descriptive measures, rather than tests proving market transmission. CHZ provides ecosystem context, while BTC and ETH provide broader crypto context. The separate average across the 190 fan-token pairs is 0.392. The wide range of pairwise correlations means that an average does not describe every token equally well.

**Supporting evidence and technical detail**

| Comparison | Mean correlation | Median correlation | Minimum | Maximum |
|---|---:|---:|---:|---:|
| Fan token versus BTC | 0.314 | 0.316 | 0.119 | 0.406 |
| Fan token versus ETH | 0.338 | 0.345 | 0.091 | 0.440 |
| Fan token versus CHZ | 0.421 | 0.421 | 0.114 | 0.556 |
| Fan-token pairs | 0.392 | 0.387 | −0.010 | 0.849 |

- CHZ has the highest mean token-level benchmark correlation. BTC and ETH provide broader crypto-market comparisons.
- The 190 within-sample token pairs show substantial heterogeneity. This supports distinguishing token-specific exposures from shared movements when interpreting market risk.
- These correlations describe return co-movement. The study does not estimate an ecosystem transmission mechanism or the effects of individual sporting events.

**Visual brief**

Use one horizontal bar chart for the three benchmark means on a common correlation scale. Label the bars directly. Keep the full four-row correlation table, including medians and ranges, in these notes.

**Report source**

§5.6 and Table 5, p. 11.

---

# 09. What Each Method Contributes

**Presenter explanation**

These methods use the same underlying price histories and answer related questions. Their agreement provides complementary evidence, rather than independent replication. SADF means supremum augmented Dickey–Fuller, GSADF means generalized SADF, and BSADF means backward SADF. A supremum here is the largest statistic across the windows searched. Segmentation concerns returns, while the recursive and Bayesian ADF methods concern the log-price process.

**Supporting evidence and technical detail**

| Component | Analysis input | Reported output |
|---|---|---|
| SADF and GSADF | Daily log prices | Full-sample statistic and reference-level classification |
| BSADF date-stamping | Recursive ADF statistics by endpoint | Consecutive days above the dating reference and retained intervals |
| Return segmentation | Standardized returns and log-squared returns | Dates and counts of mean and volatility-proxy changes |
| Bayesian local ADF | Local dynamics of the price process | Daily positive-slope and regime-reset probabilities |

- The June sample provides the primary results. The September extension evaluates how the classification and dating results change with a longer observation window.
- The diagnostics use the same underlying price histories and address different statistical properties. Agreement is interpreted as complementary evidence within the study.

**Visual brief**

Use the compact question-and-output table. Avoid adding the regression equation, tuning parameters, or numerical results to this overview.

**Report source**

§4.1, §6.3 and Table 7, pp. 4–5, 12–13.

---

# 10. SADF and GSADF: Detecting Explosive Price Dynamics

**Presenter explanation**

The fitted regression is Δyₜ = α + βyₜ₋₁ + εₜ, with yₜ = ln(Pₜ). H₀: β = 0 corresponds to a unit-root or random-walk benchmark, and H₁: β > 0 corresponds to an autoregressive coefficient 1 + β above one. The positive ADF coefficient describes the dynamics of the fitted process. It is not simply a positive return or an upward chart slope. Unlike the usual left-tailed ADF stationarity test, this application examines the right tail for explosiveness. The reported implementation includes an intercept and zero lagged differences. GSADF is useful here because episodes may begin after the token starts trading. Both statistics summarize a search over eligible windows. Published reference exceedances are nominal classifications, rather than estimated probabilities that an economic bubble exists.

**Supporting evidence and technical detail**

- For an admissible window, the implemented regression is **Δyₜ = α + βyₜ₋₁ + εₜ**, where yₜ is log price. The reported regressions use an intercept and zero lagged price differences.
- Test **H₀: β = 0** against **H₁: β > 0**. In the level representation, the autoregressive coefficient is 1 + β. A positive slope is consistent with an explosive root in the fitted window.
- **SADF** fixes the sample start and takes the maximum right-tailed statistic over admissible end dates.
- **GSADF** varies the start and end dates and takes the maximum across all admissible windows. This flexibility can isolate shorter periods of explosiveness within a longer history.
- The Phillips–Shi–Yu minimum-window fraction is **0.01 + 1.8/√T**, where T is the number of observations. The report gives a range of **78 to 108 prices** for the implemented fan-token regressions.
- Global classifications use published 90%, 95%, and 99% reference percentiles. The results emphasize the nominal 5% exceedance count.

**Visual brief**

Use two simple window illustrations, one with a fixed start for SADF and one with moving starts and ends for GSADF. Keep the equation and minimum-window formula in the notes.

**Report source**

§4.2, §§6.3–6.4 and Table 7, pp. 5, 13.

---

# 11. BSADF Dating: Measuring Signal Duration

**Presenter explanation**

Global GSADF and daily BSADF references serve different purposes. The global comparison asks whether a history contains a sufficiently extreme window. The dating comparison classifies individual endpoints. This report approximates the endpoint reference using published SADF-based values, rather than matched BSADF simulations. A run includes every consecutive day above the reference, and the longest run is reported even when it falls below 30 days. The 30-day rule is the implemented Phase 3 retention rule. The alternative five-day filter in the research proposal is future work, as explained on slide 25. Because the endpoint statistic searches windows reaching into the past, a persistent crossing does not imply a rising price on every flagged day.

**Supporting evidence and technical detail**

- At each eligible endpoint, **BSADF** takes the maximum right-tailed ADF statistic over the admissible starting dates ending at that endpoint. The resulting sequence provides a daily view of the signal.
- Compare the daily sequence with the report’s **approximate 95% endpoint dating reference**, derived from published SADF-based values. The global GSADF and endpoint dating references serve different purposes.
- Measure a run from the first day above the endpoint reference through the final consecutive day above it. Retain fan-token intervals with at least **30 consecutive days** above the reference.
- Report the longest run even if it falls short of the retention criterion. When a retained run continues to the observation cutoff, record its endpoint as ongoing at that cutoff.
- A longer run shows persistence of the test statistic. Compare the first and last closing prices and inspect the full path to determine the economic direction of the interval.

**Visual brief**

Show one labelled BSADF path with a horizontal dating reference and two shaded runs. Mark one run as shorter than 30 days and one as qualifying. Label any schematic path as illustrative.

**Report source**

§4.3, Table 7, §§6.5, 6.8, 7.3, pp. 5–6, 13–14, 16–19.

---

# 12. Change Points: Identifying Changes in Return Risk

**Presenter explanation**

The implemented Phase 3 analysis separately segments standardized returns and log-squared returns. A regime here means a segment with different fitted statistical behaviour. Standardization puts the return series on a common scale. Squaring returns captures large moves in either direction, and changes in the fitted log-squared-return level act as a proxy for changes in variability. The fit requires at least 30 observations per segment and uses a penalty of 2 × ln(sample size) to discourage excessive breaks. Its outputs are fitted break dates and counts, rather than probabilities of bubbles. The 30-observation segment constraint differs from the 30-consecutive-day BSADF rule. The sequential Kolmogorov–Smirnov validation described in Phase 2 is a proposed extension, not the segmentation method behind the reported Phase 3 counts.

**Supporting evidence and technical detail**

- Fit separate segmentations to the **mean of standardized daily returns** and to **log-squared returns** for each asset.
- The standardized-return fit identifies shifts in the fitted mean of daily returns. The log-squared-return fit tracks changes in a proxy for return variability.
- Require a minimum of **30 observations per segment** and apply a penalty of **2 × ln(sample size)** to control the number of fitted changes.
- Breaks can occur on different dates in the two series. Report counts by asset and input series and examine whether changes in variability dominate changes in mean returns.
- The segmentation rule and the BSADF rule operate on different series. The former constrains the spacing of fitted breaks. The latter requires consecutive threshold exceedances.

**Visual brief**

Use one two-panel illustration showing a return-mean shift and a volatility-proxy shift. Keep tuning parameters in the notes. Do not add a separate bubble classification to this slide.

**Report source**

Table 7 and §6.6, pp. 13, 15–16.

---

# 13. Bayesian Local ADF: Assessing Local Explosiveness

**Presenter explanation**

The slope is the coefficient β in the local ADF regression, not the visual slope of the price chart. P(βₜ > 0 | data) expresses support for an explosive coefficient under the fitted model. A value of 95% therefore concerns that model coefficient, rather than a 95% chance of an economically defined bubble. The separate new-run probability concerns a regime reset. An isolated high reading at a reset or at initialization needs different interpretation from a sustained sequence of high readings. The implementation uses normal priors, fixed standardized innovation variance, and an expected run length of 365 days. Although the run-length update is sequential in form, the reported full-sample scaling prevents treating these fitted paths as a validated live alert system.

**Supporting evidence and technical detail**

- Fit a local ADF slope under **normal priors** and **fixed standardized innovation variance**. The report specifies an expected run length of **365 days**.
- The run-length framework updates the posterior support for continuing the existing regime versus starting a new regime as each observation enters.
- Track two distinct outputs. **P(βₜ > 0 | data)** measures support for a positive local price slope. The **new-run probability** measures support for a regime reset.
- Use **95%** as a guide for unusually strong positive-slope support. Inspect the sequence for clusters of high readings and compare their timing with resets.
- Reported probabilities use full-sample scaling and are therefore retrospective. Their magnitudes are conditional on the local model, variance specification, priors, and reset rule.

**Visual brief**

Use a small example probability path with a 95% guide and a marked reset date. Label a schematic example as illustrative. Put the priors, variance assumption, and expected run length in the notes.

**Report source**

Table 7, §§6.7–6.7.1, 7.3, pp. 13, 16, 19. Run-length framework attributed to Adams and MacKay (2007).

---

# 14. June Results: Explosive Windows in 9 of 20 Tokens

**Presenter explanation**

Nine tokens exceed the June GSADF reference: OG, ATM, GAL, ASR, JUV, PSG, BAR, POR, and INTER. Four exceed the SADF reference: ATM, BAR, ASR, and POR. The same nine GSADF tokens also exceed the published nominal 1% reference. OG and ATM have the largest statistics, 6.025 and 5.028 respectively. The label nominal 5% acknowledges the reference calibration. It does not establish a calibrated false-positive rate for this entire 20-token analysis, and it does not describe the probability of an economic bubble. Run lengths appear in the supporting table and become the focus of slide 15.

**Supporting evidence and technical detail**

- Through 30 June 2026, **9 of 20 fan tokens (45%)** exceeded the nominal 5% GSADF reference. The same nine exceeded the published nominal 1% GSADF reference.
- **Four tokens** crossed the nominal 5% SADF reference. These were ATM, BAR, ASR, and POR.
- GSADF flagged more tokens because it could search for extreme windows beginning after the first usable observation. The highest statistics were **6.025 for OG** and **5.028 for ATM**.
- Report these classifications as sample-level reference exceedances. The study did not adjust the 20 asset-level comparisons for multiplicity.

| Fan token exceeding GSADF reference | GSADF | 95% global reference | Longest BSADF run |
|---|---:|---:|---:|
| OG | 6.025 | 2.463 | 9 days |
| ATM | 5.028 | 2.463 | 7 days |
| GAL | 4.674 | 2.464 | 11 days |
| ASR | 4.582 | 2.463 | 7 days |
| JUV | 4.353 | 2.468 | 3 days |
| PSG | 4.106 | 2.463 | 10 days |
| BAR | 3.913 | 2.462 | 14 days |
| POR | 3.847 | 2.417 | 22 days |
| INTER | 3.216 | 2.423 | 5 days |

**Visual brief**

Show two directly labelled bars for 4 of 20 and 9 of 20. Keep the nine-token statistics table in the notes so detection and duration remain separate in the audience view.

**Report source**

§6.4, Table 8 and §7.3, pp. 13–14, 19.

---

# 15. June Persistence: No Fan Token Reached 30 Days

**Presenter explanation**

POR is the maximum across all 20 fan tokens, so its 22-day run establishes that none reached 30 days. Its longest June-fit interval was 5–26 August 2022, with another 16-day run in late June 2026. CHZ had a 53-day run from 2 March to 23 April 2021. BTC and ETH provide broad crypto comparisons. A long benchmark signal provides context for duration under the study rules, while economic bubble interpretation still requires the price path and other evidence. The supporting table retains the benchmark SADF and GSADF statistics. AFC illustrates why global and dating classifications differ: it has a 10-day dating run even though its global GSADF statistic lies below its own global reference.

**Supporting evidence and technical detail**

- **No fan token** satisfied the 30-consecutive-day rule. Portugal (POR) recorded the longest fan-token run, **22 days from 5 to 26 August 2022**. The June fit also recorded a separate 16-day run for POR in late June 2026.
- Among selected club tokens, the longest runs were **14 days for BAR**, **11 for GAL**, and **10 each for PSG and AFC**. AFC reached a 10-day endpoint run despite its global GSADF statistic falling below its global reference.
- **CHZ** was the only benchmark above the 30-day duration criterion. Its **53-day** run lasted from **2 March to 23 April 2021**, with the BSADF statistic reaching **8.144 on 12 March**.

| Benchmark | SADF | GSADF | Above nominal 5% GSADF reference | Longest BSADF run |
|---|---:|---:|:---:|---:|
| BTC | 2.290 | 3.889 | Yes | 27 days |
| ETH | 1.712 | 2.228 | No | 10 days |
| CHZ | 5.048 | 8.144 | Yes | 53 days |

**Visual brief**

Use a four-bar run-length chart and a clearly labelled 30-day reference line. Identify POR as the fan-token maximum and identify the other three assets as benchmarks.

**Report source**

§6.5, Tables 8–9 and Figure A.8, pp. 14–15, 30.

---

# 16. June Change Points: Volatility Shifts Dominate

**Presenter explanation**

The 76.8% figure is 96 divided by 125. It is a share of fitted break counts across two different input series, not a percentage of days, tokens, or return variance explained. The three benchmark assets add 17 breaks, giving 142 across all 23 assets. GAL has 10 volatility-proxy changes, ATM has five return-mean changes, and eight tokens have no detected return-mean changes. Break counts depend on the chosen penalty, series transformation, and minimum segment length. They show changing return behaviour without identifying a cause for each change.

**Supporting evidence and technical detail**

| Series or universe | Detected changes |
|---|---:|
| Fan-token return means | 29 |
| Fan-token log-squared returns | 96 |
| Total across the 20 fan tokens | 125 |
| Additional changes across BTC, ETH, and CHZ | 17 |
| Total across all 23 assets | 142 |

- **76.8%** of fan-token detections were in the volatility proxy. This is the share of fitted breaks across the two series.
- **GAL** recorded the largest number of volatility-proxy changes, with **10**. **ATM** recorded **five** return-mean changes. **Eight tokens** had no detected return-mean change.
- The results point to repeated changes in the dispersion of returns across the sample. Material shifts in market risk can occur even when the fitted mean remains stable.

**Visual brief**

Use two directly labelled bars for 29 and 96, with a short annotation giving the 76.8% share. Keep the full by-token plot and all-asset totals in the notes.

**Report source**

§6.6, Figure 2 and Figure A.5, pp. 15–16, 27.

---

# 17. June Bayesian Results: Strong Readings Were Isolated

**Presenter explanation**

The median positive-slope probability was 13.4%. The five high readings occur in ACM, BAR, GAL, and POR, with GAL appearing twice. BAR, the November GAL observation, and POR coincide with near-certain resets. ACM occurs at initialization. A reset means that the model gives strong support to beginning a new local regime, which helps interpret an isolated extreme probability. These remain probabilities conditional on the chosen model and retrospective scaling. The five-row table below retains the exact dates and both probability outputs.

**Supporting evidence and technical detail**

- Across **37,642 fan-token daily estimates**, the median posterior probability of a positive local slope was **13.4%**.
- **Five estimates (approximately 0.013%)** reached the 95% guide. They were isolated in time and occurred across four tokens.
- BAR, the November GAL observation, and POR coincided with near-certain model resets. The ACM observation occurred at initialization.
- The estimated probabilities provide limited support for a persistently positive local slope, even though GSADF identified extreme windows for several assets.

| Token | Date | Positive-slope probability | New-run probability |
|---|---|---:|---:|
| ACM | 24 February 2021 | 98.84% | 0.27% |
| BAR | 7 April 2021 | 99.05% | 100.00% |
| GAL | 14 May 2021 | 98.61% | 11.50% |
| GAL | 17 November 2021 | 96.03% | 100.00% |
| POR | 11 March 2024 | 95.47% | 100.00% |

**Visual brief**

Use a timeline with five labelled observations and distinguish the reset-associated dates. Give the count of five out of 37,642 clear prominence. Keep the detailed probability table in the notes.

**Report source**

§§6.7–6.7.1, Table 10, §7.3 and Figures A.6–A.7, pp. 16, 19, 28–29.

---

# 18. September Extension: Two Intervals Meet the Duration Rule

**Presenter explanation**

Both cutoffs are in 2026. The extension adds 1,620 fan-token price observations, taking the count from 37,662 to 39,282. ARG's qualifying interval lies entirely after June, while POR's interval starts in June and accumulates most of its duration after that cutoff. This compares fits at two sample lengths. It does not measure real-time alert accuracy or guarantee that an interval would have been known with its final dates as events unfolded. The supporting table keeps the all-asset break and Bayesian-record counts separate from the fan-token measures shown on the slide.

**Supporting evidence and technical detail**

| Measure | Through 30 June 2026 | Through 19 September 2026 |
|---|---:|---:|
| Fan-token price observations | 37,662 | 39,282 |
| Fan tokens exceeding the nominal 5% GSADF reference | 9 of 20 | 10 of 20 |
| Fan-token BSADF intervals of at least 30 days | 0 | 2 |
| Detected changes across all 23 assets | 142 | 150 |
| Daily Bayesian records across all 23 assets | 45,672 | 47,535 |

- The extension added **1,620 fan-token prices**. Argentina (ARG) joined the nominal 5% GSADF exceedance group.
- The qualifying ARG interval fell entirely after the June cutoff. The qualifying POR interval started in June and accrued most of its duration in the extended sample.
- Both samples are retrospective fits. The comparison shows how additional observations changed the reported classifications and intervals.

**Visual brief**

Use the two-row comparison table with both cutoffs clearly labelled as 2026. Emphasize the change from zero to two retained intervals. Keep observation totals and all-asset diagnostics in the notes.

**Report source**

§6.1, Table 6, §6.8 and Table 11, pp. 12, 16–17.

---

# 19. September Intervals: Persistent Signals During Price Declines

**Presenter explanation**

The interval returns are simple first-to-last USD closing-price changes, rather than average daily log returns. They are not maximum drawdowns. The mean Bayesian positive-slope probability is 40.5% for POR and 31.1% for ARG, and neither interval contains a reading at or above 95%. POR also has a volatility-proxy change point on 1 August 2026. An ongoing endpoint means the BSADF run continues to the last observation. It gives no information about what happened after the cutoff. The findings describe severe downward repricing within long statistical signals, with limited local-model support for sustained explosiveness.

**Supporting evidence and technical detail**

| Measure | Portugal (POR) | Argentina (ARG) |
|---|---|---|
| Retained interval | 15 June–19 September 2026 | 21 July–23 August 2026 |
| Consecutive run | 97 days | 34 days |
| First-to-last USD close change | −69.9% | −44.2% |
| Mean Bayesian positive-slope probability | 40.5% | 31.1% |
| Endpoint status | Ongoing at cutoff | Closed |

- Neither interval contained a day with a Bayesian positive-slope probability at or above **95%**.
- Portugal also registered a **volatility-proxy change point on 1 August 2026**.
- The intervals meet the statistical duration rule. Their realized price changes characterize them economically as periods of severe downward repricing.

**Visual brief**

Use this compact comparison table. Emphasize the two price losses. Keep mean posterior probabilities and the POR change-point date in the notes, and use slide 20 to explain how the diagnostic paths fit together.

**Report source**

§6.8 and Table 11, pp. 16–17.

---

# 20. Reading Price, BSADF, and Bayesian Paths Together

**Presenter explanation**

Figure 3 on report page 18 supplies the aligned USD price, BSADF, and Bayesian panels for POR and ARG. The shaded regions are the retained BSADF intervals, the dotted vertical line marks 30 June, and the dashed horizontal lines identify the dating reference and Bayesian guide. The BSADF maximum can select windows containing price movements well before the endpoint, so its daily value need not describe only the latest local behaviour. In addition, an explosive-root coefficient concerns the fitted price process rather than a simple positive daily return. The Bayesian model uses a different local specification and asks about a positive coefficient conditional on its assumptions. These differences explain why the diagnostics need to be read alongside the actual price path. Figure A.9 compares the June and September fits.

**Supporting evidence and technical detail**

- **Price series.** The USD closes show a net decline across each shaded interval. The price paths establish the realized direction and timing of the repricing.
- **BSADF sequence.** The statistic remains above the approximate dating reference for extended periods. Each endpoint statistic is selected from windows that can include earlier price movements, so the path can remain elevated during a decline.
- **Bayesian series.** The local positive-slope probabilities stay below the 95% guide over the two retained intervals. This diagnostic gives limited support for sustained local explosiveness.
- Read the three series together. The duration of a threshold exceedance, evidence about the current local slope, and the realized economic outcome are different features of an interval.

**Visual brief**

Use the POR price, BSADF, and probability panels from Figure 3 as one vertically aligned worked example. Preserve interval shading and reference lines. Place a short reading guide beside each panel. Keep the complete two-asset figure available in the notes.

**Report source**

§§6.8.1–6.9, Figure 3 and Figure A.9, pp. 17–18, 31.

---

# 21. Synthesis of the Empirical Evidence

**Presenter explanation**

The June and September statements concern different observation cutoffs and should retain those labels. Global statistics identify extreme windows, dating measures endpoint persistence, segmentation describes changes in return behaviour, and the Bayesian model assesses a local ADF coefficient. The methods share the same underlying prices, so their combined use is complementary rather than independent confirmation. The study does not estimate fundamental values, identify causal effects of fan attention, or demonstrate that every flagged interval is an economic bubble.

**Supporting evidence and technical detail**

| Diagnostic | What the reported evidence supports | Interpretation boundary |
|---|---|---|
| Global recursive tests | Episodes of unusually strong price dynamics within several histories | The maximum statistic summarizes a window search and carries no direct measure of duration |
| BSADF dating | Measurement of persistence under a specified endpoint reference and duration rule | An interval can persist during falling prices |
| Return segmentation | Frequent shifts in return variability relative to mean shifts | Break counts depend on the selected series, penalty, and segment length |
| Bayesian local ADF | Brief increases in local positive-slope support and occasional resets | Posterior probabilities depend on the fitted model and scaling |

- Taken together, the diagnostics support a characterization of **intermittent price explosiveness and changing volatility regimes**.
- The evidence for **sustained speculative appreciation** is comparatively limited. An economic interpretation depends on the realized price path and the local behavior of the series.

**Visual brief**

Use this compact evidence table with one row per finding. Avoid adding the full method-boundary matrix to the same audience slide. Retain that matrix below as supporting detail.

**Report source**

§§6.4–6.9 and §§7.1–7.2, pp. 13–19.

---

# 22. Implications for Market-Risk Monitoring

**Presenter explanation**

The report supports a review process, rather than an estimated trading rule. Record the model specification and reference alongside the peak statistic and duration so the alert is interpretable. Compare the full price path and interval change, because a signal can remain high during a decline. Volatility may change even if the fitted return mean is stable. BTC, ETH, and CHZ provide market context, while vendor and exchange checks help assess whether unusual observations are credible. These checks inform interpretation without establishing a causal transmission channel.

**Supporting evidence and technical detail**

- **Signal identification.** Record the asset, model specification, reference level, peak statistic, run length, and whether the interval remains open.
- **Price-path review.** Compare the full USD price path with the flagged period and calculate realized gain or loss across the interval. Distinguish a rising trajectory from a reversal or a sustained decline.
- **Volatility review.** Check rolling volatility and fitted volatility-proxy breaks. Escalation can be warranted when dispersion rises even if the return-mean fit is stable.
- **Benchmark and data review.** Compare the move with BTC, ETH, and CHZ. Review vendor discrepancies, exchange records, and any indication of stale or low-activity observations before attributing the move to token-specific behavior.
- This framework is a **risk-monitoring implication** drawn from the evidence. The report’s retrospective fits do not measure real-time alert performance.

**Visual brief**

Use one simple sequence of the three numbered review steps. Keep the scope statement visible. Put the full list of recorded fields in these notes.

**Report source**

Implications derived from §§5.2–5.3, 5.6, 6.5–6.9, and 7.2–7.3, pp. 8, 11, 14–19.

---

# 23. Implications for Stress Testing and Exposure Management

**Presenter explanation**

The scenario returns are observed first-to-last changes over two particular 2026 intervals. Applying them to a position is a hypothetical exposure calculation, not a forecast, a probability estimate, or an investment recommendation. A scenario review can also consider changes in volatility and concentration across individual teams, the fan-token ecosystem, and broader crypto assets. Any joint shock should state how its components combine. Forced-sale scenarios need spread, depth, and execution-cost assumptions supported by suitable market data. The project did not estimate those inputs.

**Supporting evidence and technical detail**

- **Historical downside scenarios.** Use the observed **−44.2% ARG** and **−69.9% POR** interval returns as case-based stress inputs. For a simple unlevered exposure, multiply position value by the scenario return to estimate the direct mark-to-market impact.
- **Volatility-sensitive exposure review.** Reassess position sizes and loss limits when volatility changes materially. A historical volatility estimate covering several regimes can obscure the current level of risk.
- **Concentration and joint shocks.** Examine exposure to individual teams, the fan-token ecosystem, and broad crypto markets. Construct explicitly hypothetical combined shocks where both token-specific and common-market risk matter.
- **Liquidity and execution.** If the scenario includes forced selling, add spread, depth, and execution-cost assumptions using consistent market data. The report did not estimate liquidity or trading costs.
- The observed declines provide **historical scenario magnitudes**. Loss probabilities and worst-case losses require separate estimation.

**Visual brief**

Show the two observed losses and the simple position-value calculation. Keep hypothetical joint shocks and execution assumptions visibly separate from the historical observations.

**Report source**

Implications derived from §§5.2, 5.5–5.6, 6.6, 6.8–6.9 and 7.2–7.3, pp. 8–11, 15–19.

---

# 24. Limitations That Affect Interpretation

**Presenter explanation**

Published global reference values are interpolated or extrapolated, and the endpoint reference uses an SADF-based approximation rather than a matched BSADF simulation. Changing volatility can affect test calibration, motivating asset-specific bootstrap work. Applying 20 asset-level comparisons without a multiplicity correction affects how a collection of exceedances should be read. Fixing the June universe from a later category snapshot creates potential selection and survivorship effects. Bayesian probabilities depend on the local model and scaling, and common price inputs limit independence across diagnostics. No causal sporting-event analysis, fundamental-valuation model, or complete formation–burst–decline classification was implemented in these results.

**Supporting evidence and technical detail**

- **Critical-value calibration.** The study interpolates or extrapolates published global references and uses an SADF-based approximation for endpoint dating. Asset-specific bootstrap calibration would address changing volatility more directly.
- **Decision-rule sensitivity.** The observed counts and dates depend on the reference values and the 30-day duration criterion. The 20 global tests are reported without a multiplicity correction.
- **Sample selection.** Defining the June universe using a September category snapshot creates potential selection and survivorship effects. Results apply to the retained 20-token sample.
- **Bayesian assumptions.** Fixed innovation variance, prior and reset choices, and full-sample standardization affect the posterior paths. Full-sample scaling makes the reported estimates retrospective.
- **Attribution.** The methods share underlying price data and do not estimate causal effects of matches, attention, or liquidity. The study does not estimate fundamental values or classify the full formation, burst, and decline life cycle.

**Visual brief**

Use the four limitation bullets with the short consequence beneath them. Keep detailed calibration and model settings in the notes.

**Report source**

§6.3 and §7.3, pp. 13, 19.

---

# 25. Proposed Extensions and Their Outputs

**Presenter explanation**

These proposals address different limitations and should not be described as completed validation. The wild bootstrap would produce new critical references suited to changing volatility, allowing revised reference comparisons. Alternative duration filters would show whether classifications depend heavily on the minimum run length. Sequential Kolmogorov–Smirnov monitoring compares distributions and would provide change alerts and estimated change dates, including changes beyond the mean. A Bayesian return-regime model would estimate probabilities of shifts in return means and variances. A hierarchical dynamic logit would pool information across tokens to estimate associations between candidate predictors and the BSADF-derived state. Those associations would not establish causation. The exact proposed settings, including bootstrap count and monitoring thresholds, remain in the supporting table. A separate sporting-event dataset would be needed for formal event-window analysis.

**Supporting evidence and technical detail**

| Proposed extension | Specification in the research design | Purpose |
|---|---|---|
| Robust recursive inference | 999 wild-bootstrap replications, BIC lag selection, volatility-rescaled checks, and a dependence-robust procedure where indicated | Evaluate how sensitive exceedance counts are to changing volatility and dependence |
| Alternative dating rules | Proposed five-day primary filter, with three-, seven-, and 14-day sensitivity checks | Assess how persistence classifications vary with the required run length |
| Sequential nonparametric validation | Kolmogorov–Smirnov change-point monitoring, with average run lengths of 500 and 1,000 and a seven-day boundary-matching window | Assess distributional changes around dated intervals |
| Bayesian return-regime validation | Regime-specific return means and variances, with a 90-day expected segment length and a 0.8 posterior change-point guide | Compare return-regime change probabilities with dated price signals |
| Hierarchical dynamic logit | Pool information across tokens using lagged signal status, return, volatility, activity, and BTC, ETH, and CHZ returns | Evaluate predictors of the BSADF-derived state in the unbalanced panel |

- These specifications belong to the **Phase 2 proposal**. The **Phase 3 results** use the implemented methods on slides 9–13.
- An additional event dataset would allow formal analysis of sporting-event windows and the timing of potential formation, reversal, and decline phases.

**Visual brief**

Use the compact method-purpose-output table. Make the proposed status visible above the table. Keep every numerical tuning parameter in the notes.

**Report source**

§2.5, §§4.2–4.6, transition to §6, and §7.3, pp. 3–7, 12, 19.

---

# 26. Conclusions

**Presenter explanation**

The conclusions apply to the retained 20-token sample and the reported nominal references, duration filter, segmentation settings, and Bayesian model. June supplies the primary evidence on brief signals and changes in risk. The September extension demonstrates why a qualifying statistical duration needs an economic reading of the actual prices. The study supports an integrated interpretation of diagnostics without estimating a causal mechanism, fundamental values, or a real-time trading strategy.

**Supporting evidence and technical detail**

- The study finds stronger evidence of localized explosive price behavior than of sustained speculative appreciation across the fan-token sample.
- Shifts in return variability are central to the risk interpretation. They help explain why exposure can change materially in periods with limited evidence of sustained price acceleration.
- The extension shows that a statistical signal can persist through a severe correction. Price direction and realized loss therefore belong alongside signal duration in risk assessment.
- For financial risk management, the study supports an integrated assessment of price dynamics, volatility regimes, benchmark co-movement, and the economic outcome of each flagged interval.

**Visual brief**

Use the three concise findings and the concluding sentence. Avoid repeating the large synthesis table or the detailed limitations on this closing slide.

**Report source**

§§7.1–7.3, p. 19.

---

# 27. Selected References and Data Sources

**Presenter explanation**

Assaf et al. motivate the fan-token application. Phillips and co-authors provide the recursive explosive-root testing foundations. The robustness references motivate methodological extensions without implying those corrections were implemented in Phase 3. Adams and MacKay provide the run-length framework discussed for the local Bayesian model. Archived Yahoo histories supply the primary prices, while the other named sources provide classification, comparison, or corroborating evidence as described in the report. CoinGlass is corroboration for the flagged OG move, rather than the primary source for all token prices.

**Supporting evidence and technical detail**

- Assaf, A., Demir, E., & Ersan, O. (2024). Detecting and date-stamping bubbles in fan tokens. *International Review of Economics & Finance, 92*, 98–113. DOI 10.1016/j.iref.2024.01.039.
- Phillips, P. C. B., Wu, Y., & Yu, J. (2011). Explosive behavior in the 1990s Nasdaq: When did exuberance escalate asset values? *International Economic Review, 52*(1), 201–226. DOI 10.1111/j.1468-2354.2010.00625.x.
- Phillips, P. C. B., Shi, S., & Yu, J. (2015a, 2015b). Testing for multiple bubbles. *International Economic Review, 56*(4), 1043–1078 and 1079–1134. DOIs 10.1111/iere.12132 and 10.1111/iere.12131.
- Harvey et al. (2016, 2025) and Lui, Phillips, & Yu (2024). Methods for explosive-root inference under changing volatility and dependence. Full citations appear in the report.
- Adams & MacKay (2007). Bayesian run-length framework cited in the report’s discussion of the local ADF model.
- **Data sources.** Archived Yahoo Finance daily histories, CoinGecko category and historical data, Binance candles and listing records, and CoinGlass corroboration for the flagged OG move.

**Visual brief**

Use a simple references list with sufficient space between entries. Keep full publication metadata and DOI strings in these notes rather than reducing the slide font size.

**Report source**

§6.7.1 and report references and data sources, pp. 16, 20–22.
