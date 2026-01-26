# Project Context

This document consolidates key context for the ConvFinQA agent project.

---

## The Task

We’d like you to demonstrate a **LLM** driven prototype that can answer conversational dialogue questions on any given financial document. For this task we ask you to use a cleaned version of the **ConvFinQA** Dataset. 

<aside>
👉

This dataset consists of multi-hop numerical reasoning questions over semi-structured financial documents, containing text & datatables.

</aside>

We would like to see what you can build with the data provided. Feel free to present the results in any format you prefer and explore any additional ideas you have with the dataset. You may use any model or architecture of your choice. **The goal is to demonstrate your knowledge and experience.** We are particularly interested in the logic and reasoning behind your choice of accuracy metrics and your ability to communicate your solutions and ideas effectively.

### What we give you:

- A repo with *cleaner* version of the ConvFinQA Dataset.
- A dataset card [`dataset.md`](http://dataset.md) which contains information on the dataset fields and key highlights from the original [paper](https://arxiv.org/pdf/2210.03849) .
- Some light boilerplate to get you started

## What to Produce

- **[~75% time allocation]** A solution implementation to ConvFinQA
    - Code quality and structure will be evaluated.
- **[~25% time allocation]** A report write-up of your method, findings and shortcomings
    - Please explain your choice of method for this task.
    - Please include an honest assessment of your system's strengths and limitations
    - **You don't have to implement all your ideas, but do communicate them to us.** What would you do if you had more time?

<aside>
👉

We do not seek overly complicated solutions—we strongly believe in optimal design within the given timeframe. Complexity does not equal sophistication.

</aside>

Please note:

- Blindly reimplementing the same system as the paper with an updated base model is not sufficient. We expect a solution more appropriate to this task given advancements in LLMs since the paper release.


## Assignment Brief

**Goal**: Build an Agentic prototype that answers conversational dialogue questions on any given financial document. The dataset of financial documents is provided in the `data` folder.

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
