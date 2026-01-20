"""CLI interface for ConvFinQA Agent."""

import typer
from rich import print as rprint

app = typer.Typer(
    name="convfinqa",
    help="LLM-driven conversational QA for financial documents",
    add_completion=True,
    no_args_is_help=True,
)


@app.command()
def chat(
    record_id: str = typer.Argument(..., help="ID of the record to chat about"),
) -> None:
    """Start an interactive chat session about a specific record."""
    rprint(f"[bold blue]Loading record:[/bold blue] {record_id}")
    rprint("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")

    history: list[dict[str, str]] = []

    while True:
        try:
            message = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            rprint("\n[yellow]Session ended[/yellow]")
            break

        if message.strip().lower() in {"exit", "quit"}:
            rprint("[yellow]Session ended[/yellow]")
            break

        # TODO: Implement agent call
        response = "[placeholder] Agent response will go here"
        rprint(f"[green][bold]assistant:[/bold] {response}[/green]")
        history.append({"user": message, "assistant": response})


@app.command()
def evaluate(
    split: str = typer.Option("dev", help="Dataset split to evaluate (train/dev)"),
    limit: int = typer.Option(None, help="Limit number of records to evaluate"),
) -> None:
    """Evaluate agent performance on the dataset."""
    rprint(f"[bold blue]Evaluating on {split} split[/bold blue]")
    if limit:
        rprint(f"[dim]Limited to {limit} records[/dim]")

    # TODO: Implement evaluation
    rprint("[yellow]Evaluation not yet implemented[/yellow]")


@app.command()
def info() -> None:
    """Show information about the loaded dataset."""
    # TODO: Load and show dataset stats
    rprint("[bold]ConvFinQA Dataset Info[/bold]")
    rprint("  Train records: 3,037")
    rprint("  Dev records: 421")
    rprint("  Total questions: ~14,115")


if __name__ == "__main__":
    app()
