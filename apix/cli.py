"""
CLI entry point for apix.

Usage:
    apix run workflow.yaml
    apix auth auth.yaml
    apix endpoints endpoints.yaml
    apix process filter.jq
    apix template template.jinja2 --output output.txt
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .auth import load_auth_config
from .endpoint import call_endpoints, load_endpoints
from .process import process as process_module
from .template import render_template
from .workflow import run_workflow


@click.group()
@click.version_option(version="0.1.0", prog_name="apix")
def main():
    """apix - make working with APIs as easy as running a command."""
    pass


@main.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--base-dir", "-d", type=click.Path(), help="Base directory for resolving relative config paths")
@click.option("--var", "-v", "vars", multiple=True, help="Extra template variables (key=value)")
def run(workflow_file: str, base_dir: Optional[str], vars: tuple):
    """Run a workflow defined in a YAML file.

    The workflow file specifies the modules to run and their order.
    """
    extra_vars = {}
    for v in vars:
        if "=" in v:
            key, val = v.split("=", 1)
            extra_vars[key] = val

    try:
        result = run_workflow(workflow_file, base_dir=base_dir, extra_vars=extra_vars)
        print(json.dumps(result, indent=2) if result else "Workflow completed successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("config", type=click.Path(exists=True))
def auth(config: str):
    """Load and display auth configuration from a YAML file."""
    configs = load_auth_config(config)
    output = {k: {"host": v.host, "method": v.method.value} for k, v in configs.items()}
    click.echo(json.dumps(output, indent=2))


@main.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--auth", "-a", type=click.Path(exists=True), help="Auth YAML config file")
@click.option("--base-url", help="Base URL to prepend to endpoint URIs")
def endpoints(config: str, auth: Optional[str], base_url: Optional[str]):
    """Load and call endpoints from a YAML config file."""
    auth_configs = load_auth_config(auth) if auth else {}
    endpoints_list = load_endpoints(config)
    results = call_endpoints(endpoints_list, auth_configs, base_url=base_url)

    output = [
        {
            "host": r.host,
            "method": r.method,
            "uri": r.uri,
            "status_code": r.status_code,
            "data": r.data,
        }
        for r in results
    ]
    click.echo(json.dumps(output, indent=2))


@main.command()
@click.argument("jq_filter", type=click.Path(exists=True))
@click.option("--input", "-i", "input_file", type=click.Path(exists=True), help="Input JSON file")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--stdin", "-s", "read_stdin", is_flag=True, help="Read JSON from stdin")
def process(jq_filter: str, input_file: Optional[str], output: Optional[str], read_stdin: bool):
    """Apply a jq filter to JSON data and output results."""
    import sys as _sys

    if read_stdin:
        data = json.loads(_sys.stdin.read())
    elif input_file:
        with open(input_file) as f:
            data = json.load(f)
    else:
        click.echo("Error: provide --input, --stdin, or pipe data", err=True)
        sys.exit(1)

    result = process_module(filter_path=jq_filter, input_data=data, output_file=output)
    click.echo(json.dumps(result, indent=2))


@main.command()
@click.argument("template_file", type=click.Path(exists=True))
@click.option("--data", "-d", "data_file", type=click.Path(exists=True), help="JSON data file")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
@click.option("--stdin", "-s", "read_stdin", is_flag=True, help="Read JSON from stdin")
def template(template_file: str, data_file: Optional[str], output: str, read_stdin: bool):
    """Render a Jinja2 template with JSON data and write to a file."""
    import sys as _sys

    if read_stdin:
        data = json.loads(_sys.stdin.read())
    elif data_file:
        with open(data_file) as f:
            data = json.load(f)
    else:
        data = {}

    rendered = render_template(template_file, data, output)
    click.echo(f"Rendered output written to {output}")
    click.echo(rendered)


if __name__ == "__main__":
    main()