"""
Workflow engine - reads a master YAML file and executes modules in order.

The workflow YAML specifies:
- Steps to execute in order
- Each step references a module (auth, endpoints, process, template) and its config file
- Data flows between steps as JSON in memory
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .auth import AuthConfig, load_auth_config
from .endpoint import EndpointResult, call_endpoints, load_endpoints
from .process import process
from .template import render_template


class WorkflowError(Exception):
    """Raised when a workflow step fails."""
    pass


def run_workflow(
    workflow_path: str,
    base_dir: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a workflow defined in a YAML file.

    The workflow YAML format:
    ```yaml
    steps:
      - module: auth
        config: auth.yaml

      - module: endpoints
        config: endpoints.yaml

      - module: process
        config: process.jq

      - module: template
        config: template.jinja2
        output: output.txt
    ```
    """
    workflow_file = Path(workflow_path)
    if not workflow_file.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    base = base_dir or str(workflow_file.parent)
    extra_vars = extra_vars or {}

    with open(workflow_path) as f:
        workflow_data = yaml.safe_load(f)

    steps = workflow_data.get("steps", [])
    if not steps:
        raise ValueError("Workflow has no steps defined")

    # Pipeline state: JSON data passed between modules
    pipeline_data: Any = {}
    auth_configs: Dict[str, AuthConfig] = {}

    for i, step in enumerate(steps):
        module = step.get("module", "")
        config_file = step.get("config", "")
        output_file = step.get("output")

        # Resolve config path relative to the workflow file's directory
        config_path = str(Path(base) / config_file) if config_file else ""
        step_desc = f"Step {i+1}: {module}"

        if module == "auth":
            print(f"  {step_desc} - loading auth config from {config_path}")
            auth_configs = load_auth_config(config_path)
            pipeline_data = {
                k: {"host": v.host, "method": v.method.value}
                for k, v in auth_configs.items()
            }

        elif module == "endpoints":
            print(f"  {step_desc} - calling endpoints from {config_path}")
            base_url = step.get("base_url")
            endpoints = load_endpoints(config_path)
            results = call_endpoints(endpoints, auth_configs, base_url=base_url)
            pipeline_data = [
                {
                    "host": r.host,
                    "method": r.method,
                    "uri": r.uri,
                    "status_code": r.status_code,
                    "data": r.data,
                }
                for r in results
            ]

        elif module == "process":
            print(f"  {step_desc} - applying jq filter from {config_path}")
            pipeline_data = process(
                filter_path=config_path,
                input_data=pipeline_data,
                output_file=output_file,
            )

        elif module == "template":
            print(f"  {step_desc} - rendering template from {config_path}")
            if not output_file:
                raise WorkflowError(
                    "Template step requires an 'output' field in the workflow config"
                )
            output_path = str(Path(base) / output_file)
            rendered = render_template(
                template_path=config_path,
                data=pipeline_data,
                output_path=output_path,
            )
            print(f"  {step_desc} - wrote output to {output_path}")
            pipeline_data = rendered

        else:
            print(f"  {step_desc} - WARNING: unknown module '{module}', skipping")

    return pipeline_data