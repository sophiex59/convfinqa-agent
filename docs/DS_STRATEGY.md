# Data Science Strategy & Analysis

**Author**: Senior Data Scientist / Agentic AI Lead
**Date**: 2026-01-25

## Executive Summary
While the current engineering test suite (`pytest`) and regression testing (`evaluate`) confirm that the *software* functions, a rigorous Data Science approach requires validating that the *model* generalizes. This document critiques our current approach and outlines a mature validation strategy.

---

## 1. Sampling Strategy: The "Random" Trap

**Current State**: We evaluate on the "First N" records or the full Dev set.
**User Question**: *"Should we be randomly sampling?"*

### The Analysis
1.  **Random Sampling is Insufficient**: Random sampling assumes the underlying distribution is uniform or well-represented in a small sample. In financial data, edge cases (e.g., "negative loss", "fiscal year shift") are rare. A random sample of 50 might miss them entirely.
2.  **The "First N" Bias**: Datasets are often sorted by Company or Date. Evaluating "records 1-50" might over-index on a single industry (e.g., Tech) or year (e.g., 2008), biasing results.

### Recommendation: Large Point-in-Time Evaluation (Current Strategy)
**Status**: ✅ Chosen for Final Report.

Due to time constraints, we are opting for a single **Large Point-in-Time Evaluation** on a substantial slice of the Dev set (N=100-200).
*   **Rationale**: This gives us a statistically tighter error margin ($\pm 6\%$) for the final report compared to repeated small samples.
*   **Trade-off**: It is a "one-off" snapshot. We lose the ability to detect continuous regression during development, but we gain a high-confidence final score.

### Future Recommendation: Stratified "Golden Set"
*   **Status**: ⚠️ Deferred.
*   Ideally, continuous integration would use a fixed Golden Set of 50 diverse questions to catch regressions effectively.


---

## 2. Advanced Metrics: Beyond Accuracy

**Current State**: Execution Accuracy (Correct / Total).
**Critique**: Accuracy is a "lagging" metric. It tells you *if* it failed, not *how* or key trade-offs.

### Proposed Metrics Suite

#### A. Reliability (Calibration)
*   **Metric**: **Rejection Rate** vs **Hallucination Rate**.
*   **Why**: In finance, saying "I don't know" is better than a wrong number.
*   **Implementation**: Measure how often the agent refuses to answer (e.g., returns "N/A") when context is missing.

#### B. Reasoning Fidelity (Logic Consistency)
*   **Metric**: **Program Accuracy** (or Tool Trace match).
*   **Why**: Getting the right number ($42) by the wrong formula ($21 * 2$ instead of $40 + 2$) is a "False Positive" correctness.
*   **Implementation**: Compare the *sequence* of tool calls (Lookup -> Calculate -> Limit) against a gold standard trace.

#### C. Efficiency
*   **Metric**: **Tokens per Specific Correct Answer**.
*   **Why**: Agent A gets 80% accuracy with 10 steps. Agent B gets 79% with 2 steps. Agent B is vastly superior for production latency/cost.

---

## 3. Data Hygiene & The "Test set"

### rigorous Protocol
1.  **Dev Set (Validation)**: Use this for prompt engineering, debugging, and "peeking". We have been using this correctly.
2.  **Test Set (Held-Out)**:
    - **Rule**: NEVER look at failures in the Test Set.
    - **Reason**: Once you inspect a Test Set failure and fix it, that data point becomes part of the Training Set (via your brain).
    - **Current Status**: We use the Dev set effectively. Since the official Test set is hidden (blind submission), we are enforcing this hygiene naturally.

### Bootstrapping Confidence Intervals
*   **Problem**: "77% accuracy" on 100 examples has a large error margin (±8%).
*   **Solution**: Use **Bootstrapping**. Resample the 100 results with replacement 1000 times to calculate a 95% Confidence Interval (e.g., "77% [71% - 82%]").
*   **Why**: Tells us if a +2% improvement is real or noise.

---

## 5. Discussion: Critique of Current Proposals

### User Proposal A: "Random Set of 20" as Golden Set
*Proposal: Create a random set of 20 records (some multi-hop) and use this consistently.*

**Senior DS Critique**:
*   **Pros**:
    *   **Pragmatism**: Quick to generate. "Perfect is the enemy of good".
    *   **Consistency**: Once fixed, it stops the "First N" drift.
*   **Cons (Critical)**:
    *   **Sample Size**: N=20 is statistically insignificant. One failure swings accuracy by 5%. The Confidence Interval on 20 samples is massive (±22%).
    *   **Coverage Risk**: A random draw of 20 has a high probability of missing rare but critical patterns (e.g., negative accounting formats).
*   **Verdict**: **Accepted as MVP**, but with a warning.
    *   *Refinement*: Do not just draw 20 random. Draw 100 random, then hand-pick 20 that cover *at least* 3 different error types (math, lookup, date). Call this the "Silver Set".

### User Proposal B: Metrics Selection
*Proposal: Focus on Reliability (A) and Efficiency (C). Skip Logic Consistency (B) for now.*

**Senior DS Critique**:
*   **Agreement**: Logic Consistency (B) requires measuring the *process*, which demands expensive annotation (Gold Traces) or complex LLM-as-Judge setups. It is high effort.
*   **Efficiency (C) Warning**: Efficiency is a "vanity metric" until Accuracy is >90%. Optimizing tokens for a 40% accurate agent is premature optimization.
*   **Verdict**: Focus on **Reliability (A)** first. A financial agent that says "I don't know" is useful; one that saves tokens but lies is dangerous.

---

## 6. Technical Deep Dive: Confidence Intervals

To report "76.5%" is misleading without error bars. Here is the math we should use.

### The Problem
We treat evaluation as a Bernoulli trial (Success/Fail).
Standard Error (SE) = $\sqrt{p(1-p)/n}$
*   $p$ = accuracy (0.76)
*   $n$ = sample size (20)

For $N=20$:
$SE = \sqrt{0.76 * 0.24 / 20} \approx 0.095$
95% CI $\approx \pm 1.96 * SE \approx \pm 18.7\%$

So our "76%" is actually **57% - 95%**. This explains why scores fluctuate wildly on small runs.

### The Solution: Bootstrap Resampling (Deferred)
**Status**: ⚠️ Recommended for Future, not MVP.

We acknowledge that a point estimate (e.g., "76%") on N=20 has a massive Confidence Interval ($\pm 19\%$). Ideally, we would use bootstrap resampling to report this uncertainty explicitly (e.g., "76% [55-90%]").

**Decision**: We are skipping this for the MVP to prioritize **engineering velocity** and **code simplicity**.
*   **Rationale**: Implementing robust statistical tooling takes time. We accept the risk of noisy metrics in the short term to focus on feature development.
*   **Limitation**: We must treat small-sample improvements (e.g. +2%) with extreme skepticism until validated on the full Dev set.

**Algorithm (for future implementation)**:
1.  Result set `R` (N items).
2.  Resample `R` with replacement $k$ times.
3.  Compute CI from percentiles of the resampled means.


