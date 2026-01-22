# Design Choices

This document records all major design decisions made during development, with rationale and alternatives considered.

---

## 1. Agent Framework

**Choice**: LangGraph

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **LangGraph** | Graph-based flow, state management, checkpointing, extensible | Steeper learning curve, LangChain dependency | ✅ Chosen |
| AutoGen | Multi-agent conversations, async | Overkill for structured QA | ❌ |
| CrewAI | Simple role metaphor, quick setup | Less control over execution flow | ❌ |
| Custom agents | Full control, no dependencies | High development effort, reinventing the wheel | ❌ |

**Rationale**: LangGraph provides the right abstraction level for multi-turn QA. The graph structure makes it easy to visualize and extend the conversation flow, and built-in state management handles context across turns naturally.

---

## 2. LLM Provider

**Choice**: Gemini 2.5 Flash

| Option | Context Window | Strengths | Cost | Verdict |
|--------|----------------|-----------|------|---------|
| **Gemini 2.5** | 1M+ tokens | Native multimodal, strong reasoning | Low | ✅ Chosen |
| GPT-4o | 128K tokens | Best function calling | High | ❌ |
| Claude 3.5 | 200K tokens | Excellent reasoning, safety | Medium | ❌ |
| Llama 3 (local) | 128K tokens | Free, private | Infra cost | ❌ |

**Rationale**: Gemini 2.5's massive context window future-proofs for larger documents. Cost-effectiveness allows more experimentation. Strong structured output support aligns well with financial QA.

---

## 3. Package Manager

**Choice**: Poetry

| Option | Speed | Docker Integration | Ecosystem | Verdict |
|--------|-------|-------------------|-----------|---------|
| **Poetry** | Slower | Excellent | Mature | ✅ Chosen |
| UV | ⚡ Fast | Growing | New | ❌ |
| pip + venv | Medium | Manual | Universal | ❌ |
| Conda | Slow | Complex | Scientific | ❌ |

**Rationale**: Poetry's lock file reliability and Docker integration outweigh UV's speed advantage for this project. Abundant CI/CD examples reduce setup friction.

---

## 4. Document Processing

**Choice**: Direct LLM ingestion (no separate parsing)

| Option | Complexity | Accuracy | Verdict |
|--------|------------|----------|---------|
| **Direct ingestion** | Low | High (LLM handles structure) | ✅ Chosen |
| Separate table parser | Medium | Risky (parsing errors) | ❌ |
| RAG with chunking | High | Overkill for doc sizes | ❌ |

**Rationale**: Analysis showed documents average ~1,000 tokens, max ~3,700 tokens. Well within Gemini's context. Direct ingestion avoids parsing errors and lets the LLM reason over the full context.

**Document size analysis**:
```
Total records: 3,458
Min: 499 chars (~125 tokens)
Max: 14,886 chars (~3,700 tokens)  
Avg: 4,177 chars (~1,000 tokens)
```

---

## 5. Error Handling Strategy

**Choice**: Log + show reasoning trace (no auto-retry)

| Option | Complexity | Learning Value | Verdict |
|--------|------------|----------------|---------|
| **Log + trace** | Low | High (analyze patterns) | ✅ Chosen |
| Auto-retry with reflection | High | Medium | ❌ (future) |
| Silent fail | Low | None | ❌ |

**Rationale**: Per assignment guidance ("complexity ≠ sophistication"), we prioritize learning from errors externally over building complex self-correction loops. The reasoning trace helps debug failures. Auto-retry can be added later if patterns emerge.

---

## 6. Containerization

**Choice**: Single container for MVP

| Option | Complexity | Scalability | Verdict |
|--------|------------|-------------|---------|
| **Single container** | Low | Limited | ✅ Chosen |
| Docker Compose (multi) | Medium | Good | ❌ (future) |
| Kubernetes | High | Excellent | ❌ |

**Rationale**: Single container is sufficient for the assignment scope. Docker Compose scaffolding exists for future async workers if needed.

---

## 7. Evaluation Approach

**Choice**: Execution Accuracy with numeric normalization

| Option | Complexity | Alignment with Paper | Verdict |
|--------|------------|---------------------|---------|
| **Exe Acc + normalization** | Medium | High | ✅ Chosen |
| Exact string match | Low | Poor (format differences) | ❌ |
| Program accuracy | High | High but harder to implement | ❌ (future) |
| LLM-as-judge | Medium | Novel but less comparable | ❌ |

**Rationale**: Execution Accuracy is the primary metric from the original paper, enabling direct comparison with baselines. Numeric normalization handles format differences (142.4% vs 1.42403).

---

## 8. Prompting Strategy

**Choice**: Chain-of-thought with structured output

| Option | Reasoning Quality | Controllability | Verdict |
|--------|-------------------|-----------------|---------|
| **CoT + structured** | High | High | ✅ Chosen |
| Answer-only | Low | High | ❌ |
| Few-shot examples | Medium | Medium | ❌ (combined) |
| DSL generation | High | Very high | ❌ (future) |

**Rationale**: CoT prompting significantly outperforms answer-only (40.63% vs 24.09% in paper). Structured output (REASONING/ANSWER format) enables trace logging. Can add few-shot examples incrementally.

---

## 9. Tool Design

**Choice**: Explicit tools available but not mandatory

| Option | Control | Flexibility | Verdict |
|--------|---------|-------------|---------|
| **Tools available, LLM decides** | Medium | High | ✅ Chosen |
| Mandatory tool calls | High | Low | ❌ |
| No tools (pure LLM) | Low | High | ❌ |

**Rationale**: Gemini 2.5 handles calculations internally well. Tools (`calculator`, `table_lookup`, `text_search`) are available for explicit operations when needed, but the LLM can also reason directly. This balances control with flexibility.

---

## 10. Report Format

**Choice**: Markdown (REPORT.md)

| Option | Portability | Ease | Verdict |
|--------|-------------|------|---------|
| **Markdown** | High | Easy | ✅ Chosen |
| LaTeX | High | Medium | ❌ |
| Jupyter | Medium | Easy | ❌ |

**Rationale**: Markdown renders well on GitHub, is easy to write, and matches the assignment template.

---

## Future Considerations

Decisions deferred for potential future implementation:

1. **Auto-retry with reflection** — If error patterns emerge
2. **Program accuracy metric** — Compare generated DSL to gold
3. **Few-shot prompting** — Add exemplars for hard question types
4. **Multi-container async** — For large-scale evaluation
5. **Fine-tuning** — If base model performance is insufficient
