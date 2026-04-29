---
name: integrate-anything
description: Connect to any external app and perform actions on it. Use when the user wants to interact with external services like Slack, Linear, HubSpot, Salesforce, Jira, GitHub, Google Sheets, or any other app — send messages, create tasks, sync data, manage contacts, or perform any API operation.
license: MIT
metadata:
  author: Membrane Inc
  version: '1.5.0'
  homepage: https://getmembrane.com
---

# Self-Integration

Connect to any external app and perform actions on it. Uses the [Membrane](https://getmembrane.com) CLI.

## Authentication

Authenticate with the Membrane CLI:

```bash
npx @membranehq/cli login --tenant
```

Alternatively, you can install the membrane CLI globally (`npm i -g @membranehq/cli@latest`) and use `membrane login --tenant` instead.

Always use `--tenant` to get a tenant-scoped token — this authenticates on behalf of a specific tenant (workspace + customer) in Membrane, so you don't need to pass `--workspaceKey` and `--tenantKey` on every subsequent command.

This will either open a browser for authentication or print an authorization URL to the console, depending on whether interactive mode is available. The user authenticates in Membrane, then selects a workspace and tenant (user inside workspace).

When login process is completed, the credentials are stored locally in `~/.membrane/credentials.json` and used in subsequent commands automatically.

### Non-interactive Authentication

If interactive browser login is not possible (e.g. remote/headless environment) the `membrane login` command will print an authorization URL to the terminal. The user can then open the URL in their browser and complete the login process.

If this is the case, ask the user to enter the code they see in the browser after completing the login process.

When user enters the code, complete the login process with:

```bash
npx @membranehq/cli login complete <code>
```

All commands below use `npx @membranehq/cli` (or just `membrane` if installed globally). Add `--json` to any command for machine-readable JSON output to stdout. Command without `--json` flag will print the result in a human-readable (and often shorter) format.

## Workflow

### Step 1: Get a Connection

A connection is an authenticated link to an external app (e.g. a user's Slack workspace, a HubSpot account). You need one before you can run actions.

#### 1a. Find or create a connection

Use `connection ensure` to find or create a connection by app URL or domain:

```bash
npx @membranehq/cli connection ensure "https://slack.com" --json
```

You can also use a bare domain:

```bash
npx @membranehq/cli connection ensure "slack.com" --json
```

This is the fastest way to get a connection. The URL is normalized to a domain and matched against known apps. If no app is found, one is created and a connector is built automatically.

If the returned connection has `state: "READY"`, skip to **Step 2**.

#### 1b. Wait for the connection to be ready

If the connection is in `BUILDING` state, poll until it's ready:

```bash
npx @membranehq/cli connection get <id> --wait --json
```

The `--wait` flag long-polls (up to `--timeout` seconds, default 30) until the state changes. Keep polling until `state` is no longer `BUILDING`.

The resulting state tells you what to do next:

- **`READY`** — connection is fully set up. Skip to **Step 2**.
- **`CLIENT_ACTION_REQUIRED`** — the user or agent needs to do something. The `clientAction` object describes the required action:
  - `clientAction.type` — the kind of action needed:
    - `"connect"` — user needs to authenticate (OAuth, API key, etc.). This covers initial authentication and re-authentication for disconnected connections.
    - `"provide-input"` — more information is needed (e.g. which app to connect to).
  - `clientAction.description` — human-readable explanation of what's needed.
  - `clientAction.uiUrl` (optional) — URL to a pre-built UI where the user can complete the action. Show this to the user when present.
  - `clientAction.agentInstructions` (optional) — instructions for the AI agent on how to proceed programmatically.

  After the user completes the action (e.g. authenticates in the browser), poll again with `connection get <id> --json` to check if the state moved to `READY`.

- **`CONFIGURATION_ERROR`** or **`SETUP_FAILED`** — something went wrong. Check the `error` field for details.

#### Alternative: Create a connection with more control

If you need more control over the connection creation, you can use `connection create` instead:

```bash
npx @membranehq/cli connection create "Connect to Slack" --json
```

This creates a new connection with an intent and starts building in the background. Then follow step 1b to wait for it.

### Step 2: Get an Action

An action is an operation you can perform on a connected app (e.g. "Create task", "Send message", "List contacts").

#### 2a. Search for actions

Search using a natural language description of what you want to do:

```bash
npx @membranehq/cli action list --connectionId abc123 --intent "send a message" --limit 10 --json
```

You should always search for actions in the context of a specific connection.

Each result includes `id`, `name`, `description`, `inputSchema` (what parameters the action accepts), and `outputSchema` (what it returns).

If no suitable action exists, go to step 2b.

#### 2b. Create an action (if none exists)

Describe what you want the action to do — Membrane will build it automatically using an agent:

```bash
npx @membranehq/cli action create "send a message in a channel" --connectionId abc123 --json
```

This returns an action object. The action starts in `BUILDING` state while Membrane builds it in the background.

#### 2c. Wait for the action to be ready

Poll until the action leaves the `BUILDING` state:

```bash
npx @membranehq/cli action get <id> --wait --json
```

The `--wait` flag long-polls (up to `--timeout` seconds, default 30) until the state changes. Keep polling until `state` is no longer `BUILDING`.

The resulting state tells you what to do next:

- **`READY`** — action is fully built. Proceed to **Step 3**.
- **`CONFIGURATION_ERROR`** or **`SETUP_FAILED`** — something went wrong. Check the `error` field for details.

After the action is built, you can also search for it again (step 2a) to confirm.

### Step 3: Run an Action

Execute the action using the action ID from step 2 and the connection ID from step 1:

```bash
npx @membranehq/cli action run <actionId> --connectionId abc123 --input '{"channel": "#general", "text": "Hello!"}' --json
```

Provide `--input` matching the action's `inputSchema`.

The result is in the `output` field of the response.

## Proxy requests

When the available actions don't cover your use case, you can send requests directly to the connected app's API through Membrane's proxy. Membrane automatically appends the base URL to the path you provide and injects the correct authentication headers — including transparent credential refresh if they expire.

```bash
npx @membranehq/cli request <connectionId> /path/to/endpoint
```

Examples:

```bash
npx @membranehq/cli request <connectionId> /v1/me --json
npx @membranehq/cli request <connectionId> /v1/messages -X POST -d '{"text":"hi"}' --json
```

Common options:

| Flag | Description |
|------|-------------|
| `-X, --method` | HTTP method (GET, POST, PUT, PATCH, DELETE). Defaults to GET |
| `-H, --header` | Add a request header (repeatable), e.g. `-H "Accept: application/json"` |
| `-d, --data` | Request body. JSON strings are auto-parsed (use `--rawData` to send as a literal string) |
| `--rawData` | Send `--data` as a plain string without JSON parsing |
| `--query` | Query-string parameter (repeatable), e.g. `--query "limit=10"` |
| `--pathParam` | Path parameter (repeatable), e.g. `--pathParam "id=123"` |
| `--json` | Output the full response object (status, headers, body) as JSON |

Use this for one-off raw API calls. If you need a reusable, schema-typed action that can be discovered and re-run, prefer `action create` (Step 2b) instead.

## CLI Reference

All commands support `--json` for structured JSON output to stdout. Add `--workspaceKey <key>` and `--tenantKey <key>` to override project defaults.

### connection

```bash
npx @membranehq/cli connection ensure <appUrl> [--name <name>] [--json]         # Find or create connection by URL/domain (recommended)
npx @membranehq/cli connection list [--json]                                    # List all connections
npx @membranehq/cli connection get <id> [--wait] [--timeout <n>] [--json]       # Get connection (--wait to long-poll)
npx @membranehq/cli connection create <intent> [--name <name>] [--json]         # Create connection with intent
```

### action

```bash
npx @membranehq/cli action list [--connectionId <id>] [--intent <text>] [--limit <n>] [--json]                  # List/search actions
npx @membranehq/cli action create <intent> --connectionId <id> [--name <name>] [--json]                          # Create action with intent
npx @membranehq/cli action get <id> [--wait] [--timeout <n>] [--json]                                            # Get action (--wait to long-poll)
npx @membranehq/cli action run <actionId> --connectionId <id> [--input <json>] [--json]                          # Run an action
```

### search

```bash
npx @membranehq/cli search <query> [--elementType <type>] [--limit <n>] [--json]   # Search connectors, integrations, etc.
```

### request

```bash
npx @membranehq/cli request <connectionId> <path> [-X <method>] [-H <key:value>] [-d <body>] [--rawData] [--query <key=value>] [--pathParam <key=value>] [--json]   # Proxy a raw HTTP request to the connected app's API
```

## Fallback: Raw API

If the CLI is not available, you can make direct API requests.

Base URL: `https://api.getmembrane.com`
Auth header: `Authorization: Bearer $MEMBRANE_TOKEN`

Get the API token from the [Membrane dashboard](https://console.getmembrane.com).

| CLI Command                                                  | API Equivalent                                                       |
| ------------------------------------------------------------ | -------------------------------------------------------------------- |
| `connection ensure "<url>" --json`                           | `POST /connections/ensure` with `{"appUrl": "<url>"}`                |
| `connection list --json`                                     | `GET /connections`                                                   |
| `connection get <id> --wait --json`                          | `GET /connections/:id?wait=true`                                     |
| `connection create "<text>" --json`                          | `POST /connections` with `{"intent": "<text>"}`                      |
| `search <q> --json`                                          | `GET /search?q=<q>`                                                  |
| `action list --connectionId <id> --intent <text> --json`     | `GET /actions?connectionId=<id>&intent=<text>`                       |
| `action create "<text>" --connectionId <cid> --json`         | `POST /actions` with `{"intent": "<text>", "connectionId": "<cid>"}` |
| `action get <id> --wait --json`                              | `GET /actions/:id?wait=true`                                         |
| `action run <id> --connectionId <cid> --input <json> --json` | `POST /actions/:id/run?connectionId=<cid>` with `{"input": <json>}`  |
| `request <id> <path> [-X <method>] [-d <body>] ...`          | `POST /connections/:id/request` with `{"path", "method", "query"?, "pathParameters"?, "headers"?, "data"?}` |

## External Endpoints

All requests go to the Membrane API. No other external services are contacted directly by this skill.

| Endpoint                        | Data Sent                                                             |
| ------------------------------- | --------------------------------------------------------------------- |
| `https://api.getmembrane.com/*` | Auth credentials, connection parameters, action inputs, agent prompts |

## Security & Privacy

- All data is sent to the Membrane API over HTTPS.
- CLI credentials are stored locally in `~/.membrane/` with restricted file permissions.
- Connection authentication (OAuth, API keys) is handled by Membrane — credentials for external apps are stored by the Membrane service, not locally.
- Action inputs and outputs pass through the Membrane API to the connected external app.

By using this skill, data is sent to [Membrane](https://getmembrane.com). Only install if you trust Membrane with access to your connected apps.