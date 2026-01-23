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
# Pure LLM (no tools) - baseline
poetry run convfinqa evaluate --limit 20
poetry run convfinqa evaluate-async --limit 20 --concurrency 10

# ReAct agent (with tools)
poetry run convfinqa evaluate-react --limit 10 -v
poetry run convfinqa evaluate-react-async --limit 20 --concurrency 10 -v
```

### Sampling Behavior

**Sampling is deterministic** — `--limit N` always returns the **first N records** from the dev set in order. This ensures reproducible results across runs.

To evaluate different records:
- Use `--split train` for training set
- Or modify `data_loader.get_sample()` to shuffle

### Concurrency

Default concurrency is **10 parallel records**. Each record's questions run sequentially (due to context dependencies), but multiple records process simultaneously.

| Concurrency | ~Time for 20 records |
|-------------|---------------------|
| 1 | ~8 min |
| 5 | ~2 min |
| 10 | ~1.5 min |

---

## Results Template

```markdown
## Evaluation Results

**Date**: YYYY-MM-DD
**Model**: gemini-2.5-flash
**Split**: dev
**Records evaluated**: N

### Summary
| Metric | Value |
|--------|-------|
| Execution Accuracy | X.XX% |
| Conversation Accuracy | X.XX% |
| Avg turns per conversation | X.X |

### By Turn Position
| Turn | Accuracy | Count |
|------|----------|-------|
| 1 | X.XX% | N |
| 2 | X.XX% | N |
| 3+ | X.XX% | N |

### Error Breakdown
| Type | Count | % |
|------|-------|---|
| Extraction | N | X% |
| Calculation | N | X% |
| Reference | N | X% |
| Format | N | X% |
```
