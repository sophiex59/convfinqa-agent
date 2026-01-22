"""CLI interface for ConvFinQA Agent."""

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

from src.agents.graph import conversation_agent
from src.agents.state import ConversationState
from src.core.data_loader import data_loader

app = typer.Typer(
    name="convfinqa",
    help="LLM-driven conversational QA for financial documents",
    add_completion=True,
    no_args_is_help=True,
)

console = Console()


def normalize_answer(answer: str) -> float | str:
    """Normalize answer for comparison."""
    if not answer:
        return ""
    
    # Clean string
    s = str(answer).strip().lower()
    s = s.replace("$", "").replace(",", "").replace(" million", "").replace(" billion", "")
    s = s.replace("(in thousands)", "").replace("(in millions)", "").strip()
    
    # Handle percentages
    if "%" in s:
        try:
            return float(s.replace("%", "")) / 100
        except ValueError:
            pass
    
    # Try numeric
    try:
        return float(s)
    except ValueError:
        return s


def is_correct(pred: str, gold: str, tol: float = 0.02) -> bool:
    """Check if prediction matches gold with tolerance."""
    pred_n = normalize_answer(pred)
    gold_n = normalize_answer(gold)
    
    # Both numeric
    if isinstance(pred_n, float) and isinstance(gold_n, float):
        if gold_n == 0:
            return abs(pred_n) < tol
        return abs(pred_n - gold_n) / abs(gold_n) < tol
    
    # String comparison
    return str(pred_n) == str(gold_n)


def format_table_for_display(table: dict, max_rows: int = 5) -> str:
    """Format table dict for compact display."""
    lines = []
    for i, (row_key, row_data) in enumerate(table.items()):
        if i >= max_rows:
            lines.append(f"  ... ({len(table) - max_rows} more rows)")
            break
        if isinstance(row_data, dict):
            vals = ", ".join(f"{k}={v}" for k, v in list(row_data.items())[:4])
            lines.append(f"  {row_key}: {vals}")
    return "\n".join(lines)


@app.command()
def chat(
    record_id: str = typer.Argument(..., help="ID of the record to chat about"),
    show_reasoning: bool = typer.Option(True, help="Show reasoning trace"),
) -> None:
    """Start an interactive chat session about a specific record."""
    record = data_loader.get_record(record_id)
    if not record:
        rprint(f"[red]Record not found: {record_id}[/red]")
        raise typer.Exit(1)

    rprint(Panel(f"[bold]Record:[/bold] {record_id}", title="ConvFinQA Chat"))
    rprint(f"[dim]Document has {len(record.dialogue.conv_questions)} questions[/dim]")
    rprint("[dim]Type 'exit' to quit, 'auto' to run all questions[/dim]\n")

    state = ConversationState(
        record_id=record_id,
        pre_text=record.doc.pre_text,
        post_text=record.doc.post_text,
        table=record.doc.table,
    )

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            rprint("\n[yellow]Session ended[/yellow]")
            break

        if user_input.lower() in {"exit", "quit"}:
            rprint("[yellow]Session ended[/yellow]")
            break

        if user_input.lower() == "auto":
            _run_auto_dialogue(record, state, show_reasoning)
            break

        state.current_question = user_input
        result = conversation_agent.invoke(state)
        state = ConversationState(**{**state.model_dump(), **result})

        if show_reasoning and state.reasoning_trace:
            rprint(f"[dim]{state.reasoning_trace}[/dim]\n")

        rprint(f"[green][bold]Answer:[/bold] {state.current_answer}[/green]\n")


def _run_auto_dialogue(record, state: ConversationState, show_reasoning: bool) -> None:
    """Run through all dialogue questions automatically."""
    for i, question in enumerate(record.dialogue.conv_questions):
        gold_answer = record.dialogue.conv_answers[i]
        executed_answer = record.dialogue.executed_answers[i]

        rprint(f"\n[blue]Q{i + 1}:[/blue] {question}")
        rprint(f"[dim]Gold: {gold_answer} (executed: {executed_answer})[/dim]")

        state.current_question = question
        result = conversation_agent.invoke(state)
        state = ConversationState(**{**state.model_dump(), **result})

        if show_reasoning and state.reasoning_trace:
            rprint(f"[dim]{state.reasoning_trace[:500]}...[/dim]")

        rprint(f"[green]Agent: {state.current_answer}[/green]")


@app.command()
def evaluate(
    split: str = typer.Option("dev", help="Dataset split to evaluate (train/dev)"),
    limit: int = typer.Option(10, help="Limit number of records to evaluate"),
    verbose: bool = typer.Option(False, "-v", help="Show detailed errors"),
) -> None:
    """Evaluate agent performance on the dataset."""
    rprint(f"[bold blue]Evaluating on {split} split (limit: {limit})[/bold blue]")

    records = data_loader.get_sample(split, limit)
    correct = 0
    total = 0
    errors = []

    for rec_idx, record in enumerate(records, 1):
        rprint(f"\n[dim]Record {rec_idx}/{limit}: {record.id}[/dim]")

        state = ConversationState(
            record_id=record.id,
            pre_text=record.doc.pre_text,
            post_text=record.doc.post_text,
            table=record.doc.table,
        )

        for i, question in enumerate(record.dialogue.conv_questions):
            state.current_question = question
            result = conversation_agent.invoke(state)
            state = ConversationState(**{**state.model_dump(), **result})

            gold = str(record.dialogue.executed_answers[i])
            predicted = state.current_answer.strip()

            # Use proper numeric comparison
            matched = is_correct(predicted, gold)
            if matched:
                correct += 1
            else:
                errors.append({
                    "record": record.id,
                    "q_idx": i + 1,
                    "question": question,
                    "gold": gold,
                    "pred": predicted[:80],
                    "table": record.doc.table,
                    "pre_text": record.doc.pre_text[:200],
                })
            total += 1

            status = "[green]✓[/green]" if matched else "[red]✗[/red]"
            rprint(f"  Q{i + 1}: {status} (gold: {gold}, pred: {predicted[:50]})")

    accuracy = correct / total if total > 0 else 0
    rprint(f"\n[bold]Accuracy: {correct}/{total} = {accuracy:.2%}[/bold]")

    # Show detailed errors if verbose
    if verbose and errors:
        rprint(f"\n[bold red]Errors ({len(errors)}):[/bold red]")
        for err in errors[:5]:  # Show first 5 errors
            rprint(f"\n[yellow]Record: {err['record']} Q{err['q_idx']}[/yellow]")
            rprint(f"  Question: {err['question']}")
            rprint(f"  Gold: {err['gold']}")
            rprint(f"  Pred: {err['pred']}")
            rprint(f"  Table preview:")
            rprint(format_table_for_display(err['table']))


@app.command()
def info() -> None:
    """Show information about the loaded dataset."""
    data = data_loader.load()
    rprint("[bold]ConvFinQA Dataset Info[/bold]")
    rprint(f"  Train records: {len(data.train):,}")
    rprint(f"  Dev records: {len(data.dev):,}")

    sample = data.dev[0] if data.dev else data.train[0]
    rprint(f"\n[bold]Sample record:[/bold] {sample.id}")
    rprint(f"  Questions: {len(sample.dialogue.conv_questions)}")
    rprint(f"  Type 2 question: {sample.features.has_type2_question}")


@app.command()
def list_records(
    split: str = typer.Option("dev", help="Dataset split"),
    limit: int = typer.Option(20, help="Number of records to show"),
) -> None:
    """List available record IDs."""
    records = data_loader.get_sample(split, limit)
    rprint(f"[bold]{split.upper()} records:[/bold]")
    for r in records:
        rprint(f"  {r.id} ({len(r.dialogue.conv_questions)} questions)")


@app.command()
def analyze_answers(
    split: str = typer.Option("dev", help="Dataset split"),
    limit: int = typer.Option(100, help="Records to analyze"),
) -> None:
    """Analyze answer formats in the dataset."""
    records = data_loader.get_sample(split, limit)
    
    numeric_count = 0
    percent_count = 0
    text_count = 0
    total = 0
    
    for record in records:
        for ans in record.dialogue.executed_answers:
            total += 1
            if isinstance(ans, (int, float)):
                if 0 < abs(ans) < 2:  # Likely a ratio/percentage
                    percent_count += 1
                else:
                    numeric_count += 1
            else:
                text_count += 1
    
    rprint("[bold]Answer Format Analysis[/bold]")
    rprint(f"  Total answers: {total}")
    rprint(f"  Numeric (absolute): {numeric_count} ({100*numeric_count/total:.1f}%)")
    rprint(f"  Numeric (ratio/pct): {percent_count} ({100*percent_count/total:.1f}%)")
    rprint(f"  Text: {text_count} ({100*text_count/total:.1f}%)")


if __name__ == "__main__":
    app()
