# Development Progress Diary

A chronological record of the ConvFinQA agent development, documenting iterations, decisions, and learnings. NOTE: DO NOT REMOVE ANYTHING FROM THIS FILE - ONLY ADD NEW PHASES AND SUB-PHASES.

---

## Phase 1: Initial Setup & Pure LLM Baseline

### What We Built
- Poetry project structure with LangGraph, Gemini 2.5 Flash
- Basic CLI with `chat` and `evaluate` commands
- Data loader for ConvFinQA JSON dataset
- Pure LLM prompting with chain-of-thought reasoning

### Results
- **Accuracy: ~27%** (initial)
- Simple string matching for evaluation

### Key Learnings
- Gemini could understand financial tables but struggled with precise calculations
- Answer format variations caused many false negatives

---

## Phase 2: Evaluation Improvements

### Changes Made
1. **Numeric normalization** — Handle `142.4%` vs `1.42403` format differences
2. **Tolerance-based matching** — 2% tolerance for floating point
3. **Improved context passing** — Pass full Q&A history, not just previous answers
4. **Better table formatting** — Markdown format with headers

### Results
- **Accuracy: 69%** (matched FinQANet's 68.9% baseline!)

### Key Learnings
- Evaluation methodology matters as much as the model
- Context formatting significantly impacts LLM comprehension

---

## Phase 3: Tool-Calling ReAct Agent

### Architecture Shift
Moved from pure LLM prompting to a ReAct agent with explicit tools:

| Tool | Purpose |
|------|---------|
| `write_todos` | Force explicit planning before action |
| `lookup_value` | Retrieve specific table values |
| `calculate` | Safe arithmetic with rounding |
| `submit_answer` | Structured final answer |

### Initial Implementation
- LangGraph-based agent with tool nodes
- 25 iteration limit (LangGraph default)

### Results
- **Accuracy: 40.74%** (worse than pure LLM!)
- Many "Recursion limit of 25" errors

### Problems Identified
1. Agent stuck in tool-calling loops
2. `lookup_value` too strict on row/column matching
3. Iteration limit reached before `submit_answer`

---

## Phase 4: Iteration Limit Tuning

### Changes Made
1. Reduced iteration limit: 25 → 5 → 10
2. Added graceful fallback: `[LIMIT] Could not find answer...`
3. Made limit errors visible in CLI output

### Results
- **Accuracy: ~27-40%** (still poor)
- Errors now visible and debuggable

### Key Learnings
- 5 iterations too tight for multi-step reasoning
- 10 iterations allows complex chains while limiting runaway loops

---

## Phase 5: CLI Simplification

### Changes Made
Reduced from 18 functions to 5 commands:

| Command | Purpose |
|---------|---------|
| `evaluate` | Run evaluation with progress bar |
| `chat` | Interactive session |
| `trace` | Step-by-step debugging |
| `info` | Dataset info |
| `list-records` | List available records |

**Deleted**: `evaluate-async`, `evaluate-react`, `evaluate-react-async`, `analyze-answers`

### Impact
- CLI code reduced from 546 lines to ~360 lines
- Cleaner, more focused interface

---

## Phase 6: Critical Concurrency Bug Fix ⭐

### The Bug
```python
# BROKEN: Global state shared across async tasks
_current_table: dict = {}
_current_todos: list[str] = []
```

When running concurrent records, table contexts polluted each other:
- Record 1 questions would use Record 2's table data
- Todos from different records mixed together

### The Fix
```python
# FIXED: Task-local storage with contextvars
from contextvars import ContextVar
_current_table: ContextVar[dict] = ContextVar("current_table", default={})
```

### Results
- **Accuracy: 100%** on 9 questions (2 records)
- Records no longer interfere with each other

### Key Learnings
- Concurrency bugs are insidious and hard to spot
- Global state + async = disaster
- `contextvars` is Python's solution for async-safe context

---

## Phase 7: Tools Refactoring

### Before
```
src/tools/
├── agent_tools.py      # 7KB monolithic file
├── calculator.py       # Old utility, unused
├── table_lookup.py     # Old utility, unused
└── text_search.py      # Never used
```

### After
```
src/tools/
├── __init__.py         # Clean exports
├── context.py          # Shared state (contextvars)
├── write_todos.py      # Planning tool
├── lookup_value.py     # Table lookup with fuzzy matching
├── calculate.py        # Safe arithmetic
└── submit_answer.py    # Answer formatting
```

### Impact
- One tool per file (easier to maintain)
- Clear separation of concerns
- Deleted 4 unused/duplicate files

---

## Phase 8: Percentage Format Fix

### The Bug
```python
# BROKEN: Assumed values > 1 needed conversion
if abs(num_value) > 1:
    num_value = num_value / 100  # 1.42403 → 0.01424 ❌
```

### The Fix
```python
# FIXED: Only convert if % sign present
if "%" in str_value:
    num_value = float(str_value.replace("%", "")) / 100
else:
    num_value = float(str_value)  # Pass through unchanged
```

---

## Final Results Summary

| Phase | Accuracy | Key Change |
|-------|----------|------------|
| 1. Pure LLM (basic) | 27% | Initial implementation |
| 2. Pure LLM (improved) | 69% | Better evaluation & context |
| 3. ReAct (initial) | 40% | Tool calling, but buggy |
| 4. ReAct (tuned) | 40% | Iteration limit adjustments |
| 5. ReAct (simplified) | — | CLI cleanup |
| 6. ReAct (concurrency fix) | 100%* | `contextvars` for async safety |
| 7. ReAct (refactored) | 100%* | Clean tool structure |
| 8. ReAct (final, 20 records) | **76.54%** | Larger evaluation (62/81 questions) |

*Small sample (2 records)

---

## Git Commit History

```
fix: uppack error
fix: improve % logic
refactor: deleted unused functions in main
refactor: tools into individual modules
feat: progress bar, changed concurrency
[earlier commits...]
```

---

## Lessons Learned

1. **Evaluation first** — Invest in robust evaluation before optimizing the model
2. **Concurrency is hard** — Global state + async = subtle bugs
3. **Simpler is better** — 4 CLI commands beats 18
4. **Tool design matters** — `write_todos` adds interpretability
5. **Context pollution** — Each async task needs isolated state
6. **Format handling** — Small parsing bugs cause big accuracy drops

---

## Future Work

- [ ] Run larger evaluation (20+ records)
- [ ] Add fuzzy matching to `lookup_value`
- [ ] Implement retry logic for rate limiting
- [ ] Add caching for repeated table lookups
- [ ] Fine-tune prompts based on error analysis
