"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    from time import perf_counter
    from multi_agent_research_lab.services.llm_client import LLMClient
    
    console.print(f"[bold blue]Running Single-Agent Baseline LLM query...[/bold blue]\nQuery: {query}")
    
    start_time = perf_counter()
    try:
        client = LLMClient()
        response = client.complete(
            system_prompt="You are a helpful research assistant. Write a comprehensive, detailed, and well-structured report answering the query.",
            user_prompt=query,
        )
        latency = perf_counter() - start_time
        state.final_answer = response.content
        
        # Display the result
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline Answer"))
        
        # Display metrics
        cost_str = f"${response.cost_usd:.5f}" if response.cost_usd is not None else "Unknown"
        console.print(
            f"[bold green]Metrics:[/bold green]\n"
            f"- Latency: {latency:.2f} seconds\n"
            f"- Input Tokens: {response.input_tokens}\n"
            f"- Output Tokens: {response.output_tokens}\n"
            f"- Cost: {cost_str}"
        )
    except Exception as e:
        console.print(f"[bold red]Error running baseline: {e}[/bold red]")
        raise e


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both single-agent baseline and multi-agent workflow, and generate benchmark report."""
    _init()
    
    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report
    import os
    
    # 1. Runner for baseline
    def run_baseline(q: str) -> ResearchState:
        from multi_agent_research_lab.services.llm_client import LLMClient
        state_baseline = ResearchState(request=ResearchQuery(query=q))
        client = LLMClient()
        response = client.complete(
            system_prompt="You are a helpful research assistant. Write a comprehensive, detailed, and well-structured report answering the query.",
            user_prompt=q,
        )
        state_baseline.final_answer = response.content
        state_baseline.add_trace_event("baseline_llm", {"cost_usd": response.cost_usd})
        return state_baseline

    # 2. Runner for multi-agent
    def run_multi_agent(q: str) -> ResearchState:
        state_multi = ResearchState(request=ResearchQuery(query=q))
        workflow = MultiAgentWorkflow()
        return workflow.run(state_multi)

    console.print("[bold yellow]Starting Benchmark Run...[/bold yellow]")
    
    # Run Baseline
    console.print("\n[bold blue]Running Single-Agent Baseline...[/bold blue]")
    baseline_state, baseline_metrics = run_benchmark("Single-Agent Baseline", query, run_baseline)
    
    # Run Multi-Agent
    console.print("\n[bold blue]Running Multi-Agent Workflow...[/bold blue]")
    multi_state, multi_metrics = run_benchmark("Multi-Agent Workflow", query, run_multi_agent)
    
    # Report
    metrics_list = [baseline_metrics, multi_metrics]
    report_content = render_markdown_report(metrics_list)
    
    # Write report to reports/benchmark_report.md
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/benchmark_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    console.print(f"\n[bold green]Benchmark completed successfully![/bold green]")
    console.print(f"Report saved to: {report_path}")
    console.print(Panel.fit(report_content, title="Benchmark Report Summary"))


if __name__ == "__main__":
    app()

