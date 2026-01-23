# Evaluation Strategy

This document details our approach to evaluating the ConvFinQA agent.

---

## Metrics

### Primary Metric: Execution Accuracy (Exe Acc)

The standard metric from the ConvFinQA paper. A prediction is correct if the computed answer matches the gold executed answer after normalization.

```
Exe Acc = Correct Predictions / Total Predictions
```

### Secondary Metrics

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Turn-level accuracy** | Accuracy at each conversation turn | Later turns are harder (longer dependencies) |
| **Conversation accuracy** | % of fully correct conversations | Measures end-to-end success |
| **Type I vs Type II** | Accuracy by question complexity | Hybrid questions are harder |
| **Error type distribution** | Classification of failure modes | Guides improvement priorities |

---

## Evaluation Options

### Option A: Strict String Match ❌ Not Recommended

```python
def is_correct(pred: str, gold: str) -> bool:
    return pred.strip() == gold.strip()
```

**Pros**: Simple, deterministic
**Cons**: Fails on format differences (`142.4%` vs `1.42403`)

### Option B: Numeric Normalization ✅ Recommended

```python
def normalize(answer: str) -> float | str:
    answer = answer.replace("$", "").replace(",", "")
    if "%" in answer:
        return float(answer.replace("%", "")) / 100
    try:
        return float(answer)
    except ValueError:
        return answer.lower().strip()

def is_correct(pred, gold, tol=0.01) -> bool:
    pred_n, gold_n = normalize(pred), normalize(gold)
    if isinstance(pred_n, float) and isinstance(gold_n, float):
        if gold_n == 0:
            return abs(pred_n) < tol
        return abs(pred_n - gold_n) / abs(gold_n) < tol
    return pred_n == gold_n
```

**Pros**: Handles format differences, tolerates floating-point errors
**Cons**: May miss semantic errors in non-numeric answers

### Option C: LLM-as-Judge ⚠️ Future Consideration

```python
def is_correct_llm(pred: str, gold: str, question: str) -> bool:
    prompt = f"""
    Question: {question}
    Gold answer: {gold}
    Predicted answer: {pred}
    
    Are these answers semantically equivalent? Reply YES or NO.
    """
    return llm.invoke(prompt).content.strip() == "YES"
```

**Pros**: Handles semantic equivalence, natural language variations
**Cons**: Expensive, non-deterministic, potential for bias

---

## Baselines for Comparison

| Model | Method | Exe Acc | Notes |
|-------|--------|---------|-------|
| Human Expert | — | **89.44%** | Upper bound |
| FinQANet (RoBERTa) | DSL program | 68.90% | Our target to beat |
| GPT-3 | DSL prompting | 45.15% | With retrieval |
| GPT-3 | Chain-of-thought | 40.63% | Our prompting style |
| GPT-3 | Answer-only | 24.09% | Baseline minimum |
| General Crowd | — | 46.90% | Non-expert human |

**Our target**: ≥70% (beat FinQANet's 68.90%)

---

## Dataset Splits

| Split | Records | Questions | Usage |
|-------|---------|-----------|-------|
| Train | 3,037 | ~11K | Few-shot examples, fine-tuning |
| Dev | 421 | ~1.5K | Iteration, hyperparameter tuning |
| Test | 434 | ~1.5K | Final evaluation (held out by authors) |

> **Note**: Our JSON contains train + dev only. Test set is held out by original authors for blind evaluation.

---

## Evaluation Protocol Options

### Option 1: Dev Set Evaluation ✅ Recommended for Development

```bash
poetry run convfinqa evaluate --split dev --limit 50
```

- Use dev set for iteration
- Sample for quick feedback (--limit)
- Full dev for final pre-submission check

### Option 2: Cross-Validation ⚠️ More Rigorous

Split dev into k folds, evaluate on each, average results.

**Pros**: More robust estimate
**Cons**: k times more API calls, time-consuming

### Option 3: Stratified Sampling ⚠️ Recommended for Error Analysis

Sample ensuring proportional representation of:
- Type I vs Type II questions
- Different turn positions (1st, 2nd, 3rd+)
- Different document lengths

---

## Error Categories

| Category | Description | Example | Fix Strategy |
|----------|-------------|---------|--------------|
| **Extraction** | Wrong value from table/text | Read 2006 instead of 2007 | Improve table lookup tool |
| **Calculation** | Arithmetic error | 60.94 - 25.14 = 35.00 | Use calculator tool |
| **Reference** | Lost context from previous turn | "it" refers to wrong value | Improve state tracking |
| **Format** | Correct value, wrong format | 0.25 instead of 25% | Post-processing |
| **Hallucination** | Made up values | Invented numbers | Better grounding |

---

## Running Evaluation

### CLI Commands

```bash
# Evaluate ReAct agent on dev set
poetry run convfinqa evaluate --limit 10 -v

# With custom concurrency and offset
poetry run convfinqa evaluate --limit 20 --concurrency 5 --offset 10

# Trace single question step-by-step (debugging)
poetry run convfinqa trace -q 1
```

### Options

| Flag | Description |
|------|-------------|
| `--limit N` | Number of records to evaluate |
| `--offset N` | Skip first N records |
| `--concurrency N` | Parallel records (default: 10) |
| `-v` | Verbose: show detailed errors |

---

## Current Results

**Date**: 2026-01-23  
**Model**: gemini-2.5-flash  
**Agent**: ReAct with tool calling  
**Split**: dev (20 records, 81 questions)

### Summary

| Metric | Value | Notes |
|--------|-------|-------|
| **Execution Accuracy** | **76.54%** | 62/81 questions correct |
| Fully Correct Records | 12/20 (60%) | All questions correct |
| Target | ≥70% | **Target exceeded ✓** |

### Per-Record Results

| Record | Correct | Status |
|--------|---------|--------|
| 1, 4, 7, 9, 12, 19, 20 | 100% | ✓ Perfect |
| 3, 6, 8, 11, 14 | 100% | ✓ Perfect |
| 2, 10, 13, 16, 18 | Partial | ⚠ Some errors |
| 5, 15, 17 | Poor | ✗ Most wrong |

### Error Analysis (19 errors)

| Error Type | Count | Example |
|------------|-------|---------|
| Wrong value lookup | 6 | Read wrong row/year |
| Inverted ratio | 4 | Calculated A/B instead of B/A |
| Sign errors | 4 | Negative when positive expected |
| Format confusion | 3 | "2.7 million" vs "2.7" |
| Hallucination | 2 | "no" instead of number |

### Comparison to Baselines

| Approach | Accuracy | Notes |
|----------|----------|-------|
| Human Expert | 89.44% | Upper bound |
| **ReAct Agent (ours)** | **76.54%** | Tool-calling agent |
| FinQANet (paper) | 68.90% | Our target (**beaten**) |
| Pure LLM (Gemini) | ~69% | Direct prompting |

---

## Key Improvements Made

1. **Concurrency bug fix** — Used `contextvars` for async-safe task-local storage
2. **Iteration limit tuning** — Increased from 5 to 10 for complex reasoning
3. **Tool-calling architecture** — `write_todos` → `lookup_value` → `calculate` → `submit_answer`
4. **Percentage handling** — Only converts if `%` sign present in string

