# Project Context

This document consolidates key context for the ConvFinQA agent project.

---

## Assignment Brief

**Goal**: Build an LLM-driven prototype that answers conversational dialogue questions on financial documents using the ConvFinQA dataset.

**Time allocation**:
- ~75% — Solution implementation
- ~25% — Report write-up (method, findings, shortcomings)

**What matters**:
- Logic and reasoning behind accuracy metric choices
- Ability to communicate solutions effectively
- Code quality and structure
- Honest assessment of strengths and limitations

**What to avoid**:
- Blindly reimplementing the paper with an updated model
- Unnecessary complexity ("Complexity does not equal sophistication")

---

## Dataset: ConvFinQA

### Overview
Conversational Finance Question Answering — multi-hop numerical reasoning over financial documents containing text and tables.

| Metric | Value |
|--------|-------|
| Total conversations | 3,892 |
| Total questions | 14,115 |
| Train / Dev / Test | 3,037 / 421 / 434 |
| Simple conversations | 2,715 |
| Hybrid conversations | 1,177 |

### Document Structure
```python
ConvFinQARecord:
  id: str                    # e.g., "Single_MRO/2007/page_134.pdf-1"
  doc:
    pre_text: str            # Text before the table
    post_text: str           # Text after the table
    table: dict              # Financial data table
  dialogue:
    conv_questions: list     # Questions in order
    conv_answers: list       # Natural language answers
    executed_answers: list   # Programmatic execution results (ground truth)
    turn_program: list       # DSL programs for each turn
```

### Question Types
- **Type I (Simple)**: Single multi-hop question decomposed into steps
- **Type II (Hybrid)**: Two multi-hop questions combined into longer chains

### Known Challenges (from paper)
1. Domain knowledge gaps → wrong value selections
2. Long reasoning chains → errors compound
3. Later turns harder → longer dependencies

---

## Baselines

| Model | Method | Exe Acc |
|-------|--------|---------|
| Human Expert | — | **89.44%** |
| FinQANet (RoBERTa-large) | DSL program | 68.90% |
| GPT-3 | DSL program prompting | 45.15% |
| GPT-3 | Chain-of-thought | 40.63% |
| GPT-3 | Answer-only | 24.09% |
| General Crowd | — | 46.90% |

**Our target**: ≥70% (beat FinQANet)

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | LangGraph | State management, graph-based flow |
| LLM provider | Gemini 2.5 | 1M+ context, cost-effective |
| Package manager | Poetry | Docker/CI integration |
| Container | Single container | Simplicity for MVP |
| Error handling | Log + show trace | No auto-retry, learn externally |

---

## Key Metrics

**Execution Accuracy (Exe Acc)**: Primary metric — does the computed answer match the gold executed answer?

**Challenges for evaluation**:
- Format differences: `142.4%` vs `1.42403`
- Unit variations: `$1.5 million` vs `1500000`
- Floating-point tolerance needed

---

## Deliverables

1. **Solution implementation** — Working agent with CLI
2. **REPORT.md** — Method, findings, limitations, future work
3. **Pull request** — To main branch
