# apix — API eXecute

> A command line utility designed to make working with APIs as easy as running a command.

apix lets you authenticate, query, transform, and template API data — all from the terminal using simple YAML config files and standard Unix tools.

## Quick Start

```bash
# Install dependencies
pip install click pyyaml httpx jinja2 jq

# Run a full workflow
cd apix
python -m apix.cli run examples/workflow.yaml

# Or use the convenience launcher
./apix.sh run examples/workflow.yaml
```

## Modules

apix has four modules that can be chained together:

### 1. Auth (`apix auth auth.yaml`)

Defines authentication per-host. Supports:
- `bearer` — Bearer token
- `basic` — Username/password
- `api-key` — Custom header-based auth
- `oauth2-client-credentials` — OAuth2 client credentials flow

**auth.yaml:**
```yaml
- host: api.example.com
  method: bearer
  credentials:
    token: "your-token"
```

### 2. Endpoints (`apix endpoints endpoints.yaml`)

Defines API endpoints to call. Supports GET, POST, PUT, PATCH, DELETE.

**endpoints.yaml:**
```yaml
- host: api.example.com
  method: GET
  uri: /users

- host: api.example.com
  method: POST
  uri: /users
  body:
    name: "New User"
    email: "new@example.com"
```

### 3. Process (`apix process filter.jq`)

Applies [jq](https://stedolan.github.io/jq/) filters to transform JSON data from the previous step.

**process.jq:**
```jq
.[] | {id, name, email, username}
```

### 4. Template (`apix template template.jinja2 --output report.txt`)

Renders [Jinja2](https://jinja.palletsprojects.com/) templates with your data.

**template.jinja2:**
```jinja2
{% for user in items %}
User #{{ user.id }}: {{ user.name }} ({{ user.email }})
{% endfor %}
```

## Workflows

A **workflow** chains multiple modules together, passing JSON data between steps automatically.

**workflow.yaml:**
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
    output: report.txt
```

Run it:
```bash
./apix.sh run workflow.yaml
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `apix run workflow.yaml` | Execute a full workflow |
| `apix auth config.yaml` | Display auth configuration |
| `apix endpoints config.yaml` | Call API endpoints |
| `apix process filter.jq --input data.json` | Apply jq filter |
| `apix template file.jinja2 --data data.json -o out.txt` | Render template |

### Options

- `--base-dir`, `-d` — Base directory for resolving relative paths in workflow
- `--auth`, `-a` — Auth config file (for endpoints command)
- `--base-url` — Override base URL for endpoints
- `--input`, `-i` — Input JSON file
- `--output`, `-o` — Output file path
- `--stdin`, `-s` — Read JSON from stdin

## Advanced Usage

### Piping between steps

```bash
# Run endpoints, pipe to jq, then render template
./apix.sh endpoints examples/endpoints.yaml \
  | ./apix.sh process examples/process.jq --stdin \
  | ./apix.sh template examples/template.jinja2 --stdin -o report.txt
```

### Local test server

```bash
# Start the test API (runs on port 9999)
python examples/test_server.py &

# Run the example workflow
./apix.sh run examples/workflow.yaml
```

### Using with authentication

For APIs that require auth, define it in `auth.yaml` and reference matching hosts in your endpoints. The endpoint module automatically applies the correct auth headers.

## Project Structure

```
apix/
├── apix/                    # Python package
│   ├── __init__.py          # Package init
│   ├── cli.py               # Click CLI entry point
│   ├── auth.py              # Auth module (YAML config → HTTP auth)
│   ├── endpoint.py          # Endpoint module (YAML → API calls)
│   ├── process.py           # Processing module (jq filters)
│   ├── template.py          # Template module (Jinja2 rendering)
│   └── workflow.py          # Workflow engine (orchestrator)
├── examples/                # Example configuration
│   ├── auth.yaml
│   ├── endpoints.yaml
│   ├── process.jq
│   ├── template.jinja2
│   ├── workflow.yaml
│   └── test_server.py       # Local test API server
├── apix.sh                  # Convenience launcher
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.9+
- click, pyyaml, httpx, jinja2, jq