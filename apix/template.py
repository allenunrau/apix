"""
Template module - applies Jinja2 templates to JSON data and writes output to a file.

Input: a Jinja2 template file path + JSON data from the previous pipeline stage.
Outputs rendered content to a file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, Template as JinjaTemplate


def render_template(
    template_path: str,
    data: Any,
    output_path: str,
    search_path: Optional[str] = None,
) -> str:
    """Render a Jinja2 template with data and write to output file.

    Args:
        template_path: Path to the Jinja2 template file.
        data: JSON data to inject into the template context.
        output_path: Path to write the rendered output.
        search_path: Optional directory to search for template includes.

    Returns:
        The rendered string content.
    """
    template_file = Path(template_path).name
    template_dir = str(Path(template_path).parent)

    if search_path:
        loader = FileSystemLoader([template_dir, search_path])
    else:
        loader = FileSystemLoader(template_dir)

    env = Environment(loader=loader, autoescape=False)
    template = env.get_template(template_file)

    # If data is a dict, use it directly as context; otherwise wrap it
    if isinstance(data, dict):
        context = data
    elif isinstance(data, list):
        context = {"items": data, "data": data}
    else:
        context = {"data": data}

    rendered = template.render(**context)

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(rendered)

    return rendered