# ConvFinQA Technical Report: Financial Analysis Agent

**Date**: January 25, 2026
**Author**: Sophie Chong
**Version**: 2.2

---

## Executive Summary
### 77.8% End-to-End Accuracy on Conversational Financial Q&A with explicit failure controls
Financial PDFs are unstructured, inconsistent, and expensive to manually analyse for Q&A tasks. Their formats are a pain point for standard NLP models and other retrieval-based systems, which can lead to mistakes and silent hallucinations that are unacceptable in a highly regulated environment. Our solution is an agentic financial PDF parsing system using a **ReAct (Reasoning + Acting)** framework to answer complex conversational financial queries. This has higher accuracy than baseline solutions and considerably lower manual effort. 

The system was evaluated on the ConvFinQA benchmark, achieving up to **77.8% execution accuracy**, outperforming the FinQANet RoBERTa-large baseline by approximately **8–9 percentage points**.

Crucially, we include an explicitly tracked **Rejection Rate**, so the agent can abstain from answering when reliable computation is not possible due to ambiguity, tool failures, errors or complexity. In financial settings, an explicit "I don't know" is safer than a confident error.

The architecture is designed to be modular, extensible, and auditable. Each reasoning step, tool call, and calculation is observable, making the system suitable for inspection, debugging, and, importantly, compliance review. The agent runs out of the box, supports concurrent execution, and can be adapted to much larger document collections with minimal architectural change.

The system is both cost-efficient and deployable. Processing a single document (typically 4–5 questions) takes approximately 27 seconds end-to-end, or ~5–6 seconds per question. Despite multiple agent steps, the use of Gemini 2.5 Flash keeps costs low: total token usage is ~25k-30k tokens per document. At ~$0.30 per 1M tokens, this corresponds to approximately **$0.01 per document**. Evaluating the full ConvFinQA Dev set of 421 documents costs approximately **$4.00 - $5.00**.


## Methodology & Architectural Decisions
### Agent Framework
The system is implemented as a LangGraph ReAct agent. Each query proceeds through a bounded reasoning loop that includes:

- Explicit planning (write_todos)
- Table lookup
- Deterministic calculation
- Standardised answer submission or rejection

We enforce a strict loop limit (10 steps) to prevent infinite reasoning cycles. If the limit is reached, it returns a graceful failure.

### System Prompt
The system processes `ConvFinQARecord` objects (defined in `src/core/schemas.py`) which consist of:
1.  **Pre/Post Text**: Contextual paragraphs surrounding the table.
2.  **Table**: A nested dictionary representing the financial grid.
3.  **Dialogue**: The conversation history (Questions & Answers).
This schema ensures the agent has full access to the document structure, not just a flattened text string.

*   **LangGraph**: Used for state management (the "Brain"). It allows us to persist the conversation history and the "Todo List" across multiple turns of logic.

To achieve higher reliability, we engineered the System Prompt (can be found in `src/agents/react_agent.py`) with specific guardrails:
- Unit Normalization: "If table says '2.2 billion' and question asks for millions, you must return `2200`."
- Ratio Direction: Explicit instructions on how to interpret "A in relation to B" (A/B vs B/A). 
- Negative Handling: "Losses" are implied negative. If table says `-300`, question "what was the loss?" -> Answer `300`. 
- Refusal Policy: "Better to admit 'N/A' than to hallucinate." 


**Context Management**: We leveraged the **1M token window** of Gemini 2.5 Flash to ingest entire tables, avoiding a RAG-based approach. These approaches typically risk breaking structure of tables and thus losing spatial context.

### Tool-Use System Design
The agent is provided with a minimal set of tools. 

#### A. `write_todos(plan)`
*Purpose*: Forces the LLM to pause and break down the problem before acting.
*Example*: "Question: Average revenue growth? Plan: 1. Get 2017 Revenue. 2. Get 2016 Revenue. 3. Calculate difference. 4. Divide by 2016."
*Impact*: Reduces "reasoning jumps" and massively increases explainability and error handling.

#### B. `lookup_value(row, column)`
*Purpose*: Precision data extraction.
*Detail*: We implemented "fuzzy matching" for row headers, allowing the agent to find "Total Assets" even if it asks for "Assets, Total". *Impact*: This was critical for handling the inconsistency in financial reporting terms in the same document.

#### C. `calculate(expression)`
*Purpose*: Safe arithmetic.
*Detail*: Accepts a Python-valid string (e.g., `(23.5 - 20.1) / 20.1`). The tool evaluates this in a sandboxed environment and returns the result to the agent. This guarantees mathematical correctness.

#### D. `submit_answer(value)`
*Purpose*: The "Exit Node".
*Detail*: This tool enforces output standardisation (e.g. rounding to 2 decimal places, handling currency symbols).


Tool use is available but not mandatory, balancing control with flexibility. The agent is instructed to never do any calculating itself regardless of simplicity, and to always use external tools where one exists for its task.

### Reliability & Failure Control
Predictions are marked as Rejected if they:
- Explicitly return "N/A"
- Hit a reasoning step limit
- Encounter tool execution failures

The system rejects approximately 7–10% of queries, primarily due to ambiguity or tool failures.

These rejections are logged and included as an evaluation metric.

### Reliability vs Hallucination
We prioritised **High Precision** (Calibration). We tuned the agent to return `N/A` rather than guess. This hurt our raw accuracy score (as "N/A" != Gold Number) but is a great step towards a safer product for financial use cases.

## Costs & Latency
### Latency
Processing a single document (4–5 questions typically) takes approximately 27 seconds end-to-end, or ~5–6 seconds per question. With asynchronous execution and concurrency enabled, we can process documents in parallel, subject to API rate limits.

### Cost
Total token usage is approximately 25k–30k tokens per document (based on sample records from ConvFinQA, plus initial prompt, for 4-5 questions per document). Using Gemini 2.5 Flash pricing: total token usage is ~25k-30k tokens per document. At ~$0.30 per 1M tokens, this corresponds to approximately **$0.01 per document**. Evaluating the full ConvFinQA Dev set of 421 documents costs approximately **$4.00 - $5.00**. Gemini 2.5 Pro could be used for significant gains in internal complex reasoning, at a cost of $2.50 per million tokens and decreased latency.

## Evaluation Results
### Executed Accuracy of 77.8%
The prototype has been evaluated against the ConvFinQA benchmark, which is using their FinQANet model.:

| Metric | Result | Target (FinQANet) | Delta | Implications |
|--------|--------|-------------------|-------|--------------|
| **Execution Accuracy** | **77.8%** | 68.9% | **+7.5%** | Significantly outperforms the specialised neural baseline. |

We are above the target of a 70% accuracy by 7.8%
We include a second metric here of Rejection Rate. When it comes to financial calculations, "I don't know" is better than a guess. We prioritise Rejection Rate to measure safety/hallucination. 

ConvFinQA train dataset subsets of 20-200 were used for development, and recorded results are based on a ConvFinQA dev dataset subset of 100. It has been run on full 421 records in dev, and accuracy remained similar despite numerous rate-limiting errors. This shows performance remains stable as sample size increases, indicating robustness.


**Error Analysis and Statistical Limitations**
We analysed 80+ error cases and found that the remaining failures are dominated by:
- Ratio direction ambiguity (“A in relation to B”). Attempts were made to fix this via prompt engineering, but it did not reduce occurrence completely. This could be fixed through better prompt engineering (testing to find explicit wording that reduces ratio mistakes) or a critic agent.
- Date range interpretation. "From 2015 to 2017" is sometimes interpreted as inclusive (3 years) vs exclusive (2 years). Better data exploration may allow us to prompt the LLM to take one standard approach that matches the marking criteria.
- Agent gives N/A answer sometimes when data is missing from the table, but Gold Label answers expect some inference e.g deriving 2015 from 2016 growth. Extended use of the 'calculate' tool could solve this in future iterations, and a confidence score could allow us to let the Agent make more risky educated guesses, while flagging to us that the output is uncertain.

**Confidence Intervals**: On smaller samples (N=20), the margin of error was ±9.5%. The final large-scale run (N=421) significantly tightened this confidence, but individual failures may still be noisy.


## Engineering Quality & Production Readiness
The codebase follows a modular design with clean separation between:
- Agent logic
- Tool execution
- Core schemas
- CLI interface

Key engineering features include:
- Async-safe execution using contextvars
- Deterministic configuration via pydantic
- Unit and integration testing for all critical components
- Tiered evaluation strategy for regression and benchmarking (Unit Tests -> Smoke Tests -> Full Evaluation)

While this is not a production system, it demonstrates production-grade patterns in observability, failure isolation, and extensibility.

## Future Work

To exceed expert-level performance (89%), we propose the following roadmap for future iterations:

#### Improved Prompt Engineering
Error analysis showed several issues that could have been fixed with improved prompt engineering. Further, the use of an agent to evaluate results and suggest prompt improvements could allow for rapid iterative testing of prompt changes.

#### Orchestrator Pattern (Supervisor-Worker)
The current agent uses a single "Generalist" prompt. To close the remaining accuracy gap, we would implement a **Supervisor-Worker** pattern:
- **Supervisor**: Classifies the question type (e.g., "This is a Ratio Question" vs "This is a Retrieval Question").
- **Worker**: Calls a specialised sub-agent (e.g., "RatioExpert") which has specific few-shot examples for A/B vs B/A logic.
This was scoped out of the MVP due to time constraints, but is a good next step for accuracy.


#### Critic / Reviewer Node
Implementing a secondary LLM call to review the proposed answer before submission has had positive results in the literature. This agent would specifically check for common failure modes like sign errors (losses as positives) and unit scaling, as well as criticise the planning steps of the first agent.

#### Confidence Scoring
Calculating a confidence score based on the token probability/agent self-assessment. This would allow for a Human-In-The-Loop workflow where low-confidence answers are flagged for manual review.



## Conclusion
This project demonstrates that agentic, tool-based reasoning materially improves results in financial conversational QA. By prioritising correctness, explicit execution, and safe failure modes, the system remains explainable while outperforming specialised baselines. By treating financial analysis as a structured reasoning task rather than a text generation task, we achieved **77.8% accuracy**. The core structure of the project is sound, and we believe the remaining gap to - and beyond - human-level performance (89%) is bridgeable through targeted prompt engineering, semantic clarifications, and expanding the agent process - as detailed in Further Work.
