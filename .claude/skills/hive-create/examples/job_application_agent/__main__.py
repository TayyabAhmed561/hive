"""
CLI entry point for Job Application Agent.
"""

import asyncio
import json
import logging
import sys
import click

from .agent import default_agent, JobApplicationAgent


def setup_logging(verbose=False, debug=False):
    if debug:
        level, fmt = logging.DEBUG, "%(asctime)s %(name)s: %(message)s"
    elif verbose:
        level, fmt = logging.INFO, "%(message)s"
    else:
        level, fmt = logging.WARNING, "%(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stderr)
    logging.getLogger("framework").setLevel(level)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Job Application Agent — Tailor your resume and cover letter to any job."""
    pass


@cli.command()
@click.option("--job", "-j", type=str, required=True, help="Job description text or path to .txt file")
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def run(job, mock, quiet, verbose, debug):
    """Tailor resume and cover letter for a job description."""
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    # Accept either raw text or a file path
    import os
    if os.path.isfile(job):
        with open(job) as f:
            job_description = f.read()
    else:
        job_description = job

    context = {"job_description": job_description}
    result = asyncio.run(default_agent.run(context, mock_mode=mock))

    output_data = {
        "success": result.success,
        "steps_executed": result.steps_executed,
        "output": result.output,
    }
    if result.error:
        output_data["error"] = result.error

    click.echo(json.dumps(output_data, indent=2, default=str))
    sys.exit(0 if result.success else 1)


@cli.command()
@click.option("--mock", is_flag=True)
@click.option("--verbose", "-v", is_flag=True)
@click.option("--debug", is_flag=True)
def tui(mock, verbose, debug):
    """Launch the TUI for interactive job application tailoring."""
    setup_logging(verbose=verbose, debug=debug)

    try:
        from framework.tui.app import AdenTUI
    except ImportError:
        click.echo("TUI requires the 'textual' package: pip install textual")
        sys.exit(1)

    from pathlib import Path
    from framework.llm import LiteLLMProvider
    from framework.runner.tool_registry import ToolRegistry
    from framework.runtime.agent_runtime import create_agent_runtime
    from framework.runtime.execution_stream import EntryPointSpec

    async def run_with_tui():
        agent = JobApplicationAgent()
        agent._tool_registry = ToolRegistry()

        storage_path = Path.home() / ".hive" / "agents" / "job_application_agent"
        storage_path.mkdir(parents=True, exist_ok=True)

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            agent._tool_registry.load_mcp_config(mcp_config_path)

        llm = None
        if not mock:
            llm = LiteLLMProvider(
                model=agent.config.model,
                api_key=agent.config.api_key,
                api_base=agent.config.api_base,
            )

        tools = list(agent._tool_registry.get_tools().values())
        tool_executor = agent._tool_registry.get_executor()
        graph = agent._build_graph()

        runtime = create_agent_runtime(
            graph=graph,
            goal=agent.goal,
            storage_path=storage_path,
            entry_points=[
                EntryPointSpec(
                    id="start",
                    name="Start",
                    entry_node="intake",
                    trigger_type="manual",
                    isolation_level="isolated",
                ),
            ],
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
        )

        await runtime.start()
        try:
            app = AdenTUI(runtime)
            await app.run_async()
        finally:
            await runtime.stop()

    asyncio.run(run_with_tui())


@cli.command()
@click.option("--json", "output_json", is_flag=True)
def info(output_json):
    """Show agent information."""
    info_data = default_agent.info()
    if output_json:
        click.echo(json.dumps(info_data, indent=2))
    else:
        click.echo(f"Agent:   {info_data['name']}")
        click.echo(f"Version: {info_data['version']}")
        click.echo(f"Nodes:   {', '.join(info_data['nodes'])}")
        click.echo(f"Client-facing: {', '.join(info_data['client_facing_nodes'])}")


@cli.command()
def validate():
    """Validate agent structure."""
    validation = default_agent.validate()
    if validation["valid"]:
        click.echo("✓ Agent is valid")
    else:
        click.echo("✗ Agent has errors:")
        for error in validation["errors"]:
            click.echo(f"  ERROR: {error}")
    sys.exit(0 if validation["valid"] else 1)


if __name__ == "__main__":
    cli()
