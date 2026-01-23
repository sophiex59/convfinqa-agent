"""CLI interface for ConvFinQA Agent."""

import asyncio
import time

import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.agents.react_agent import run_react_agent_async
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
    
    s = str(answer).strip().lower()
    s = s.replace("$", "").replace(",", "").replace(" million", "").replace(" billion", "")
    s = s.replace("%", "").strip()
    
    try:
        return float(s)
    except ValueError:
        return s


def is_correct(pred: str, gold: str, tol: float = 0.02) -> bool:
    """Check if prediction matches gold with tolerance."""
    pred_norm = normalize_answer(pred)
    gold_norm = normalize_answer(gold)
    
    if isinstance(pred_norm, float) and isinstance(gold_norm, float):
        if gold_norm == 0:
            return abs(pred_norm) < tol
        return abs(pred_norm - gold_norm) / abs(gold_norm) < tol
    
    return str(pred_norm) == str(gold_norm)


@app.command()
def evaluate(
    split: str = typer.Option("dev", help="Dataset split (train/dev)"),
    limit: int = typer.Option(10, help="Number of records to evaluate"),
    offset: int = typer.Option(0, help="Skip first N records"),
    concurrency: int = typer.Option(10, help="Parallel records"),
    verbose: bool = typer.Option(False, "-v", help="Show detailed errors"),
) -> None:
    """Evaluate ReAct agent on the dataset."""
    
    async def process_record(record, rec_idx: int, semaphore, progress, task_id):
        async with semaphore:
            start_time = time.time()
            results = []
            history = []
            record_correct = 0
            record_total = 0
            has_error = False
            
            for i, question in enumerate(record.dialogue.conv_questions):
                answer, tool_calls, todos = await run_react_agent_async(
                    pre_text=record.doc.pre_text,
                    table=record.doc.table,
                    post_text=record.doc.post_text,
                    question=question,
                    history=history,
                )
                
                gold = str(record.dialogue.executed_answers[i])
                predicted = answer.strip()
                matched = is_correct(predicted, gold)
                
                record_total += 1
                if matched:
                    record_correct += 1
                if predicted.startswith("Error:") or predicted.startswith("[LIMIT]"):
                    has_error = True
                
                results.append({
                    "record_id": record.id,
                    "rec_idx": rec_idx,
                    "q_idx": i + 1,
                    "question": question,
                    "gold": gold,
                    "pred": predicted,
                    "matched": matched,
                    "tool_calls": tool_calls,
                    "todos": todos,
                    # Store document context (same for all questions in record)
                    "pre_text": record.doc.pre_text if i == 0 else None,
                    "post_text": record.doc.post_text if i == 0 else None,
                    "table": record.doc.table if i == 0 else None,
                })
                
                history.append((question, predicted))
            
            elapsed = time.time() - start_time
            status = "[green]✓[/green]" if record_correct == record_total else "[yellow]⚠[/yellow]" if record_correct > 0 else "[red]✗[/red]"
            error_note = " [dim](limit)[/dim]" if has_error else ""
            progress.console.print(f"  {status} Record {rec_idx}: {record_correct}/{record_total} ({elapsed:.1f}s){error_note}")
            progress.advance(task_id)
            return results
    
    async def run_evaluation():
        records = data_loader.get_sample(split, limit, offset)
        semaphore = asyncio.Semaphore(concurrency)
        
        rprint(f"[bold blue]Evaluating on {split}[/bold blue]")
        rprint(f"  Records: {offset+1} to {offset+len(records)}, Concurrency: {concurrency}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Processing...", total=len(records))
            
            tasks = [
                process_record(record, offset + idx, semaphore, progress, task_id) 
                for idx, record in enumerate(records, 1)
            ]
            
            all_results = await asyncio.gather(*tasks)
        
        # Flatten and sort
        flat_results = []
        for record_results in all_results:
            flat_results.extend(record_results)
        flat_results.sort(key=lambda x: (x["rec_idx"], x["q_idx"]))
        
        correct = sum(1 for r in flat_results if r["matched"])
        total = len(flat_results)
        errors = [r for r in flat_results if not r["matched"]]
        
        # Print per-question results
        for r in flat_results:
            status = "[green]✓[/green]" if r["matched"] else "[red]✗[/red]"
            rprint(f"  Record {r['rec_idx']} Q{r['q_idx']}: {status} (gold: {r['gold']}, pred: {r['pred'][:40]})")
        
        accuracy = correct / total if total > 0 else 0
        rprint(f"\n[bold]Accuracy: {correct}/{total} = {accuracy:.2%}[/bold]")
        
        if verbose and errors:
            # Group results by record
            results_by_record = {}
            for r in flat_results:
                rec_idx = r["rec_idx"]
                if rec_idx not in results_by_record:
                    results_by_record[rec_idx] = []
                results_by_record[rec_idx].append(r)
            
            # Find records with any errors
            failed_records = set(r["rec_idx"] for r in errors)
            
            rprint(f"\n[bold red]═══ DETAILED LOGS FOR FAILED RECORDS ({len(failed_records)}) ═══[/bold red]")
            
            for rec_idx in sorted(failed_records):
                record_results = results_by_record[rec_idx]
                record_correct = sum(1 for r in record_results if r["matched"])
                record_total = len(record_results)
                record_id = record_results[0]["record_id"]
                
                rprint(f"\n[bold yellow]{'─'*60}[/bold yellow]")
                rprint(f"[bold yellow]RECORD {rec_idx}: {record_id}[/bold yellow]")
                rprint(f"[bold yellow]Score: {record_correct}/{record_total}[/bold yellow]")
                rprint(f"[bold yellow]{'─'*60}[/bold yellow]")
                
                # Show document context (from first question in record)
                first_q = record_results[0]
                if first_q.get('pre_text'):
                    rprint(f"\n[dim]─── PRE-TEXT ───[/dim]")
                    rprint(f"[dim]{first_q['pre_text'][:500]}{'...' if len(first_q['pre_text']) > 500 else ''}[/dim]")
                
                if first_q.get('table'):
                    rprint(f"\n[dim]─── TABLE ───[/dim]")
                    import json
                    rprint(f"[dim]{json.dumps(first_q['table'], indent=2)[:1000]}[/dim]")
                
                if first_q.get('post_text'):
                    rprint(f"\n[dim]─── POST-TEXT ───[/dim]")
                    rprint(f"[dim]{first_q['post_text'][:500]}{'...' if len(first_q['post_text']) > 500 else ''}[/dim]")
                
                for q in record_results:
                    status = "[green]✓[/green]" if q["matched"] else "[red]✗[/red]"
                    rprint(f"\n[cyan]Q{q['q_idx']}:[/cyan] {q['question']}")
                    rprint(f"  [bold]Gold:[/bold] {q['gold']}")
                    rprint(f"  [bold]Pred:[/bold] {q['pred']} {status}")
                    
                    if q.get('todos'):
                        rprint(f"  [dim]Plan:[/dim]")
                        for todo in q['todos']:
                            rprint(f"    • {todo}")
                    
                    if q.get('tool_calls'):
                        rprint(f"  [dim]Tools:[/dim]")
                        for tc in q['tool_calls']:
                            # Show tool name and args
                            rprint(f"    → {tc}")
    
    asyncio.run(run_evaluation())


@app.command()
def chat(
    record_id: str = typer.Argument(..., help="Record ID to chat about"),
) -> None:
    """Interactive chat session about a financial document."""
    record = data_loader.get_record(record_id)
    if not record:
        rprint(f"[red]Record not found: {record_id}[/red]")
        raise typer.Exit(1)
    
    rprint(f"\n[bold]Document: {record_id}[/bold]")
    rprint(f"Questions available: {len(record.dialogue.conv_questions)}")
    rprint("Type 'auto' to run all questions, 'quit' to exit\n")
    
    history = []
    
    while True:
        user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
        
        if user_input.lower() in ("quit", "exit", "q"):
            break
        
        if user_input.lower() == "auto":
            for i, question in enumerate(record.dialogue.conv_questions):
                rprint(f"\n[dim]Q{i+1}: {question}[/dim]")
                answer, tool_calls, todos = asyncio.run(_async_chat(record, question, history))
                gold = str(record.dialogue.executed_answers[i])
                matched = is_correct(answer, gold)
                status = "[green]✓[/green]" if matched else "[red]✗[/red]"
                rprint(f"[bold]Answer:[/bold] {answer} {status} (gold: {gold})")
                history.append((question, answer))
            break
        
        answer, tool_calls, todos = asyncio.run(_async_chat(record, user_input, history))
        rprint(f"[bold]Answer:[/bold] {answer}")
        if todos:
            rprint(f"[dim]Plan: {' → '.join(todos[:3])}[/dim]")
        history.append((user_input, answer))


async def _async_chat(record, question: str, history: list):
    """Helper for async chat."""
    return await run_react_agent_async(
        pre_text=record.doc.pre_text,
        table=record.doc.table,
        post_text=record.doc.post_text,
        question=question,
        history=history,
    )


@app.command()
def info() -> None:
    """Show dataset information."""
    data = data_loader.load()
    rprint(f"[bold]Dataset:[/bold] {data_loader.data_path}")
    rprint(f"  Train: {len(data.train)} records")
    rprint(f"  Dev: {len(data.dev)} records")


@app.command(name="list-records")
def list_records(
    split: str = typer.Option("dev", help="Dataset split"),
    limit: int = typer.Option(20, help="Records to show"),
) -> None:
    """List available record IDs."""
    records = data_loader.get_sample(split, limit)
    for i, r in enumerate(records, 1):
        rprint(f"{i:3}. {r.id} ({len(r.dialogue.conv_questions)} questions)")

@app.command()
def trace(
    record_id: str = typer.Argument(None, help="Record ID (or uses first dev record)"),
    question: int = typer.Option(1, "-q", help="Question number (1-indexed)"),
) -> None:
    """Trace tool calls step-by-step for one question."""
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.tools import AGENT_TOOLS, set_table_context, clear_todos, get_todos
    from src.agents.react_agent import SYSTEM_PROMPT, format_table_for_prompt, format_history_for_prompt
    from src.core.config import settings
    
    # Get record
    if record_id:
        record = data_loader.get_record(record_id)
        if not record:
            rprint(f"[red]Record not found: {record_id}[/red]")
            raise typer.Exit(1)
    else:
        records = data_loader.get_sample("dev", 1)
        record = records[0]
    
    # Get question
    q_idx = question - 1
    if q_idx >= len(record.dialogue.conv_questions):
        rprint(f"[red]Question {question} not found (max: {len(record.dialogue.conv_questions)})[/red]")
        raise typer.Exit(1)
    
    q = record.dialogue.conv_questions[q_idx]
    gold = record.dialogue.executed_answers[q_idx]
    
    rprint(f"\n[bold blue]Tracing: {record.id}[/bold blue]")
    rprint(f"[bold]Question {question}:[/bold] {q}")
    rprint(f"[dim]Gold answer: {gold}[/dim]\n")
    
    # Setup
    set_table_context(record.doc.table)
    clear_todos()
    
    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        temperature=0,
        google_api_key=settings.google_api_key,
    )
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)
    
    # Build prompt
    table_str = format_table_for_prompt(record.doc.table)
    history_str = format_history_for_prompt([])
    
    user_message = f"""## Financial Document

### Text Before Table
{record.doc.pre_text}

### Financial Data Table
{table_str}

### Text After Table
{record.doc.post_text}

### Conversation History
{history_str}

### Current Question
{q}

Begin by calling write_todos to plan your approach, then use tools to find the answer."""
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]
    
    # Run agent loop with live output
    max_iterations = 5
    tool_map = {t.name: t for t in AGENT_TOOLS}
    
    for i in range(max_iterations):
        rprint(f"[cyan]--- Iteration {i+1}/{max_iterations} ---[/cyan]")
        
        # Get LLM response
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        # Check for tool calls
        if not response.tool_calls:
            rprint(f"[dim]No tool calls, LLM responded:[/dim]")
            rprint(f"  {response.content[:200] if response.content else '(empty)'}")
            break
        
        # Execute each tool call
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            
            rprint(f"[yellow]→ {tool_name}[/yellow]({tool_args})")
            
            # Execute tool
            if tool_name in tool_map:
                result = tool_map[tool_name].invoke(tool_args)
                rprint(f"  [green]Result:[/green] {result[:100]}")
                
                # Check for final answer
                if "FINAL_ANSWER:" in result:
                    answer = result.split("FINAL_ANSWER:")[1].strip()
                    matched = is_correct(answer, str(gold))
                    status = "[green]✓ CORRECT[/green]" if matched else "[red]✗ WRONG[/red]"
                    rprint(f"\n[bold]Final Answer: {answer}[/bold] {status}")
                    rprint(f"[dim]Gold: {gold}[/dim]")
                    return
                
                # Add tool result to messages (simplified)
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    
    rprint(f"\n[red]Hit iteration limit without answer[/red]")
    if get_todos():
        rprint(f"[cyan]Todos were:[/cyan] {get_todos()}")


if __name__ == "__main__":
    app()
