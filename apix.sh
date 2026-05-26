#!/usr/bin/env bash
# Convenience launcher for apix
# Usage: ./apix.sh run workflow.yaml
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$DIR" python -m apix.cli "$@"