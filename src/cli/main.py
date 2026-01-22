"""CLI interface for ConvFinQA Agent."""

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console

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


@app.command()
def chat(
    record_id: str = typer.Argument(..., help="ID of the record to chat about"),
    show_reasoning: bool = typer.Option(True, help="Show reasoning trace"),
) -> None:
    """Start an interactive chat session about a specific record."""
    # Load the record
    record = data_loader.get_record(record_id)
    if not record:
        rprint(f"[red]Record not found: {record_id}[/red]")
        raise typer.Exit(1)

    rprint(Panel(f"[bold]Record:[/bold] {record_id}", title="ConvFinQA Chat"))
    rprint(f"[dim]Document has {len(record.dialogue.conv_questions)} questions[/dim]")
    rprint("[dim]Type 'exit' to quit, 'auto' to run all questions[/dim]\n")

    # Initialize state with document
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
            # Run through all dialogue questions
            _run_auto_dialogue(record, state, show_reasoning)
            break

        # Run agent with user question
        state.current_question = user_input
        result = conversation_agent.invoke(state)

        # Update state from result
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
) -> None:
    """Evaluate agent performance on the dataset."""
    rprint(f"[bold blue]Evaluating on {split} split (limit: {limit})[/bold blue]")

    records = data_loader.get_sample(split, limit)
    correct = 0
    total = 0

    for record in records:
        rprint(f"\n[dim]Record: {record.id}[/dim]")

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

            # Simple string match (can improve later)
            is_correct = gold.lower() in predicted.lower()
            if is_correct:
                correct += 1
            total += 1

            status = "[green]✓[/green]" if is_correct else "[red]✗[/red]"
            rprint(f"  Q{i + 1}: {status} (gold: {gold}, pred: {predicted[:50]})")

    accuracy = correct / total if total > 0 else 0
    rprint(f"\n[bold]Accuracy: {correct}/{total} = {accuracy:.2%}[/bold]")


@app.command()
def info() -> None:
    """Show information about the loaded dataset."""
    data = data_loader.load()
    rprint("[bold]ConvFinQA Dataset Info[/bold]")
    rprint(f"  Train records: {len(data.train):,}")
    rprint(f"  Dev records: {len(data.dev):,}")

    # Sample record info
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


if __name__ == "__main__":
    app()
