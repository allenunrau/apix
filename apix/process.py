"""
Processing module - applies jq filters to JSON data from previous pipeline stage.

Input: a jq filter/expression + optional JSON data file path.
Applies the jq filter to the JSON data and returns the result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jq


def load_json(data_source: Union[str, Path, List, Dict, None] = None) -> Any:
    """Load JSON from a file path or return the data as-is if already a dict/list."""
    if data_source is None:
        return {}
    if isinstance(data_source, (str, Path)):
        filepath = Path(data_source)
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        # If it's a string but not a file path, try to parse as JSON
        try:
            return json.loads(data_source)
        except (json.JSONDecodeError, ValueError):
            return data_source
    return data_source


def apply_jq(jq_filter: str, data: Any) -> Any:
    """Apply a jq filter to the given data.

    The data can be loaded from a JSON file or passed directly.
    Returns the processed result.
    """
    compiled = jq.compile(jq_filter)
    result = compiled.input(data).all()
    # jq returns a list of results; if single item, unwrap
    if len(result) == 1:
        return result[0]
    return result


def process(
    filter_path: Optional[str] = None,
    filter_expr: Optional[str] = None,
    input_data: Any = None,
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
) -> Any:
    """Main entry point for the Processing module.

    Args:
        filter_path: Path to a file containing the jq filter.
        filter_expr: Inline jq filter expression (alternative to filter_path).
        input_data: JSON data to process (from previous pipeline stage).
        input_file: Path to a JSON file to use as input instead of input_data.
        output_file: Optional path to write the output JSON.

    Returns:
        The processed JSON data.
    """
    # Determine the filter expression
    if filter_path:
        with open(filter_path) as f:
            jq_expr = f.read().strip()
    elif filter_expr:
        jq_expr = filter_expr
    else:
        raise ValueError("Either filter_path or filter_expr must be provided")

    # Determine the input data
    if input_file:
        data = load_json(input_file)
    else:
        data = input_data if input_data is not None else {}

    # Apply the jq filter
    result = apply_jq(jq_expr, data)

    # Optionally write to file
    if output_file:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

    return result