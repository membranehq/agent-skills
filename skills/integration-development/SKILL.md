---
name: integration-development
description: Use this skill when writing code that reads, writes, syncs, or reacts to data in an external app. Applies to SaaS products, internal tools, scripts, batch jobs, and CLIs. The skill uses Membrane as the integration engine — it handles OAuth and credential lifecycle (authentication, token refresh, reconnect), exposes vendor operations through a uniform interface, delivers events via webhooks, generates connectors on demand for apps not yet in the workspace, and captures every action run and raw API exchange in structured logs. Works against any external app.
license: MIT
metadata:
  author: Membrane Inc
  version: '1.0.0'
  homepage: https://getmembrane.com
---

# Integration Development

## How integrations work — the five-step mental model

Every Membrane-backed feature walks through the same linear spine.
Steps 0–3 are the core path; step 4 is a capability upgrade you
graduate into when your app isn't bound to one specific vendor.

```
Step 0: Authenticate yourself   — you, the developer; via MCP or `membrane` CLI
Step 1: Authenticate your code  — sign JWTs in your backend
                                  ↳ single-tenant vs multi-tenant decided HERE
Step 2: Create connections      — `membrane.ui.connect()` in your app UI
Step 3: Use connections         — call actions on the external app
                                  ↳ discover via intent search when you don't know what to call
                                  ↳ dispatch: inline api/code | catalog id | workspace key
Step 4 (advanced): Universal    — app-agnostic code via universal actions + cross-connection logic
```

In an MCP session step 0 is already done — `membrane status` confirms.

The most consequential choice — whether your app serves one shared
external account (**single-tenant**: a team CRM, an internal Slack) or
many end users (**multi-tenant**: each user connects their own Gmail,
Linear, etc.) — lives in step 1. It determines what your backend puts
in the JWT it signs, which in turn scopes every connection and action
that follows. Everything downstream of step 1 is uniform: the same
`membrane.ui.connect()` call, the same `/act` dispatch.

## Before you code — typical discovery flow

Four commands cover most starting points:

```bash
# 1. Populate env with real credentials.
membrane credentials --shell > .env.local

# 2. Find the app you're integrating with (returns externalAppId).
membrane external-app list --search <app-name>

# 3. List catalog actions for that app.
membrane action list --externalAppId <id>

# 4. Check existing connections in the current tenant.
membrane connection list
```

> **CLI quick reference.**
>
> - Mint a JWT: `membrane token` (add `--tenantKey <key>` for per-user,
>   `--manager` for `POST /actions` and other manager ops).
> - `membrane --help` or `membrane <command> --help` lists the full surface.

When creating a connection and nothing matches in `connection list`,
pass `connectorKey` (catalog-level, always resolvable) rather than
`integrationKey` (workspace-local) on the first connect.

## Step 0: Authenticate yourself

Confirm you have a live Membrane session.

```bash
membrane status
```

Green "Logged in" plus a workspace → ready. Red "Not logged in" →
authenticate:

```bash
npx @membranehq/cli login
```

A browser window opens for sign-in. Credentials are stored in
`~/.membrane/credentials.json`; every subsequent `membrane` command
reuses them. Re-run when the session expires.

## Step 1: Authenticate your code

Every request your backend makes to Membrane carries a **Membrane
token** — a short-lived HS256 JWT signed with the workspace secret.
Its `tenantKey` determines which isolated scope of connections the
request operates in.

### Payload shape

- **`workspaceKey`** — which Membrane workspace the request runs against.
- **`tenantKey`** — isolated scope of connections within the workspace.
  Different tenants can't see each other's connections.

Plus the **workspace secret** (used to sign) and the **API URL**.

How to choose `tenantKey`:

|                          | Single-tenant                                     | Multi-tenant                                                     |
| ------------------------ | ------------------------------------------------- | ---------------------------------------------------------------- |
| **Use when**             | One shared external-app account (team CRM, Slack) | Each end user has their own external-app account (Gmail, Linear) |
| **`tenantKey` in JWT**   | Constant — e.g. `process.env.MEMBRANE_TENANT_KEY` | The signed-in user's stable id                                   |
| **Connection key shape** | Constant — e.g. `hubspot-prod`                    | Derived from user id — e.g. `gmail-${userId}`                    |
| **Connect UX** (step 2)  | Admin page; one click per app                     | Per-user button; each user connects their own account            |

### Get the values

```bash
membrane credentials --json
# { "apiUri": "...", "workspaceKey": "...", "workspaceSecret": "...", "tenantKey": "..." }
```

Shell-export form for `.env` files: `membrane credentials --shell`.

### Sign the token

Standard HS256 JWT, signed per request with a short TTL.

```ts
import jwt from 'jsonwebtoken'

// tenantKey source:
//   single-tenant  → process.env.MEMBRANE_TENANT_KEY
//   multi-tenant   → the signed-in user's stable id
const token = jwt.sign(
  { workspaceKey: process.env.MEMBRANE_WORKSPACE_KEY, tenantKey },
  process.env.MEMBRANE_WORKSPACE_SECRET,
  { algorithm: 'HS256', expiresIn: '5m' },
)
// Use as Authorization: Bearer <token>, or hand to
// <MembraneProvider fetchToken={…}> on the frontend.
```

For shell testing, `membrane token` mints a tenant-scoped token (add
`--tenantKey <key>` for per-user). `get-membrane-token` is the MCP
equivalent.

### Workspace manager tokens

Tenant-scoped tokens cover `act`, listing, and everything an app's
runtime does. **Manager** tokens (scope of the engine's
`workspaceAsManager` auth layer) are required for:

- `POST /actions` / `PATCH /actions/<id>` / `DELETE /actions/<id>` (workspace-level reusable actions)
- `PATCH /integrations/<id>/parameters` (OAuth credentials, scopes)
- `POST /import` / `GET /export` (workspace config round-trip)

Mint with `membrane token --manager`, or sign directly:

```ts
const managerToken = jwt.sign({ workspaceKey, isAdmin: true }, workspaceSecret, { algorithm: 'HS256', expiresIn: '5m' })
```

## Step 2: Create connections

A **connection** is an authenticated link to one external app. Every
`/act` call routes through a connection's auth.

`membrane.ui.connect(…)` from your frontend is the user-facing connect
flow — it opens the OAuth popup, tracks state, and resolves once the
user finishes.

### Connection lifecycle

| Operation     | CLI                                                          | MCP tool                          |
| ------------- | ------------------------------------------------------------ | --------------------------------- |
| List existing | `membrane connection list`                                   | `list-connections`                |
| Discover apps | `membrane integration list --search "<q>"`                   | `list-integrations`               |
| Create        | `membrane.ui.connect(…)` (prod) / `membrane connect …` (dev) | `connect`                         |
| Reconnect     | `membrane connect --connectionId <id>`                       | `connect` with `{ connectionId }` |
| Delete        | `membrane connection delete <id-or-key>`                     | `delete-connection`               |

### Discover what you can connect to

`list-integrations` searches the workspace's integrations plus catalog
connectors and external apps. Each result carries `connectorId`,
`integrationId`, `externalAppId` — pass any of these to `connect`. If
nothing matches, `connect` also accepts a free-text `intent` and will
build a connector on the fly — the first such connect can take longer
(expect a `BUILDING` phase; inspect `CONFIGURATION_ERROR` /
`SETUP_FAILED` if it fails).

### Create a connection

Hand `connect` one of:

- `connectorKey` / `connectorId` — a catalog connector (works even in
  a fresh workspace with no integration yet).
- `integrationKey` / `integrationId` — a known integration.
- `intent` — free-text; the server picks or builds a connector.

Optional: your own `connectionKey` for stable lookup; otherwise one is
generated.

`connect` returns the connection (`id`, `key`, `state`, and while the
user is still authenticating, `clientAction.uiUrl`). The CLI blocks
until `state: READY`; in MCP, the connect panel renders the flow.

### Reconnect

Call `connect` with the existing `connectionId` to re-authorize OAuth
without creating a new connection. Use this when an `act` call returns
a disconnected-connection error.

### Delete (archive)

`delete-connection` / `membrane connection delete` archives the
record. It stops appearing in `list-connections` and can no longer be
used by `act`.

### Customize an integration

By default, integrations use Membrane's shared OAuth client. Customize
one to supply your own OAuth credentials, adjust connect-form fields,
or change per-integration behavior. Details in `integration-catalog`.

### Connect UI — single-tenant

One shared account, one admin connect page. Connection key is constant.

```ts
import { MembraneClient } from '@membranehq/sdk'
// The backend mints a token (step 1) and exposes it at /api/membrane-token
// as { token, apiUri }.
const { token, apiUri } = await (await fetch('/api/membrane-token')).json()
const m = new MembraneClient({ token, apiUri })
await m.ui.connect({ connectorKey: 'hubspot', connectionKey: 'hubspot-prod' })
```

### Connect UI — multi-tenant

Each signed-in user connects their own account. Connection key is
derived from the user id.

**With `@membranehq/react`** — wrap the app once with `MembraneProvider`:

```tsx
import { MembraneProvider, useMembrane } from '@membranehq/react'
;<MembraneProvider
  apiUri={process.env.NEXT_PUBLIC_MEMBRANE_API_URI}
  fetchToken={async () => (await (await fetch('/api/membrane-token')).json()).token}
>
  {children}
</MembraneProvider>

// In any component:
const m = useMembrane()
m.ui.connect({ connectorKey: 'gmail', connectionKey: `gmail-${userId}` })
```

**Plain JS** — same pattern, user-scoped connection key:

```ts
await m.ui.connect({ connectorKey: 'gmail', connectionKey: `gmail-${userId}` })
```

Notes on the token route:

- Any server framework with a `GET /api/membrane-token` that returns
  `{ token, apiUri }` works. `fetchToken` is called per request, so
  tokens stay short-lived.
- Vite dev-only apps: add a dev middleware that signs the same JWT
  from step 1. `loadEnv(mode, …)` gives the middleware access to
  `MEMBRANE_*` env vars.
- `m.ui.connect(...)` must be invoked from the browser — it opens the
  OAuth popup. Server-side redirects or CLI commands can't substitute.

### Dashboard catalog page

Settings-style UI where users manage many integrations. Uses
`@membranehq/react` hooks:

```ts
useIntegrations() // → { items: Integration[], loading, loadMore, loadingMore, refresh }
useConnections() //  → { items: Connection[], loading, refresh }
useMembrane() //     → MembraneClient (.ui.connect(…), .connection(id).archive(), …)

type Connection = {
  id: string
  name: string
  integrationId: string
  integration?: { key: string; name: string; logoUri?: string }
  disconnected: boolean
  state: 'READY' | 'BUILDING' | 'DISCONNECTED' | 'ERROR'
}

type Integration = {
  id: string
  key: string
  name: string
  logoUri?: string
}
```

Four unique Membrane calls to wire up:

```ts
// Connect a new integration the user picked from the available list:
m.ui.connect({ integrationKey: i.key })

// Reconnect a disconnected/errored connection:
m.ui.connect({ connectionId: c.id })

// Disconnect (archive):
m.connection(c.id).archive()
```

`state` enum matters for the UI: `BUILDING` is the interval between
user-auth completion and Membrane finalizing the connector (can take
seconds on first-time connect). A boolean connected/disconnected UI
would show `BUILDING` or `ERROR` as "Connected" — they aren't.

## Step 3: Use connections — call actions

`/act` is the one endpoint for doing things. Four dispatch styles,
exactly one per call:

- **`api`** — inline HTTP request through the connection's auth layer
  and base URL. The default building block.
- **`code`** — JS snippet run in a sandbox with an authenticated
  `membrane` client, `connection`, and `integration` pre-wired. Good
  for multi-step composites.
- **`id`** — a specific action (catalog or workspace-local). Catalog
  actions from `action list --externalAppId` only carry `id` (the
  `key` field is empty).
- **`key`** — a workspace-local action's stable handle. Catalog
  actions have no key; workspace-local actions have both and either
  works.

`api` and `code` require a connection (`connectionKey` or
`connectionId`). `key` / `id` route through the action's own scope.

### Run an action

`membrane act` with one of `--api`, `--code`, `--key`, `--id`, plus
connection and input flags.

Response: `{ output, actionRunId }`. On failure the response still
carries `actionRunId` — feed it to the run log for debugging.

### Discover actions by intent

When you know what to do but not how, list actions ranked by intent.

`membrane action list --connectionKey <key> [--intent "<text>"]`

### Dispatch example — catalog action by `id`

Typical flow: step 3 of the discovery workflow gave you a list of
catalog actions with `id`, `name`, `inputSchema`, `config.request`.
Use the matching one by `id` — Membrane owns the vendor-specific
request shape, auth scoping, and retries. Fall back to inline `api:`
only when no catalog action matches.

```ts
// /act body:
{
  id: GMAIL_SEND_MESSAGE_ACTION_ID,   // paste from `membrane action list --externalAppId`
  connectionKey: `gmail-${userId}`,   // or `hubspot-prod` for single-tenant
  input: { to, subject, body },       // matches the action's inputSchema
}

// On failure, detect disconnected connection and forward actionRunId:
const needsReconnect = res.status === 401 || payload?.code === 'CONNECTION_DISCONNECTED'
// Return { error: payload, actionRunId: payload?.actionRunId, needsReconnect }
```

Inline `api:` when no catalog action matches:

```ts
{
  connectionKey,
  api: {
    method: 'POST',
    path: '/<vendor-endpoint>',
    body: { … },
  },
}
```

### Graduate to a workspace-local reusable action

When the same dispatch shape repeats across routes, lift it to a
workspace-local action with a stable `key`. One-time `POST /actions`
with a manager token.

Two ways to create:

- **By intent** — Membrane Agent builds and registers the action.
- **By explicit spec** — you supply `type` + `config`.

```bash
# by intent
membrane action create --intent "<text>" --connectionKey <key>

# by explicit spec
membrane action create --key <key> --type <type> --config '<json>' --integrationKey <key>

# update (merge) / replace (whole) / delete
membrane action update <identifier> --data '<json>'
membrane action replace <identifier> --data '<json>'
membrane action delete <identifier>
```

`POST /actions` body shape (explicit spec):

```json
{
  "key": "create-lead",
  "name": "Create Lead",
  "type": "api-request-to-external-app",
  "externalAppId": "<app-id>",
  "config": {
    "request": { "method": "POST", "path": "/<vendor-endpoint>" }
  },
  "inputSchema": { "type": "object", "required": ["…"], "properties": { "…": "…" } }
}
```

Returns `{ id, key, state: 'READY', inputSchema, outputSchema, … }`.
Invoke at runtime with `{ key: '<your-key>', connectionKey, input }`.

**Action scope follows which fields you set:**

- `connectionKey` / `connectionId` set → connection-level (one connection).
- `integrationKey` / `integrationId` set (no connection) →
  integration-level (shared across every connection on that
  integration). A universal action can be customized per integration
  this way — same `key`, different field mapping, pre/post hooks.
- Neither set → universal action (see step 4).

Manager token is required for `POST /actions`; tenant tokens get 403.

### Debug a failing action

Every `act` response carries `actionRunId`. Feed it to the run log
(`--details` / `includeDetails: true` also pulls the raw HTTP exchange
with the external app).

`membrane action-run-log get <actionRunId> --details`

## Step 4 (advanced): Universal integrations

Steps 0–3 assume your code knows which external app it's talking to.
Step 4 is for the other shape: your app provides value regardless of
which vendor the user connects — a "send email" feature that works
across Gmail, Outlook, SendGrid; a CRM-sync layer that treats
Salesforce, HubSpot, Pipedrive uniformly.

This is a different dispatch path. Reach for it only when
vendor-agnostic behavior is a first-class product requirement.

### Universal actions

A universal action is registered **without** `externalAppId` or
`integrationKey`. It names an intent ("create contact", "send
message", "list invoices") and ships an input/output schema shared
across every integration that implements it. Dispatch routes through
whichever integration the caller's connection belongs to.

```bash
# Create by intent — Membrane builds a shared schema at workspace scope.
membrane action create --intent "send an email" --key send-email
```

Dispatch — no `externalAppId`; the action adapts to the connection:

```ts
await act({
  key: 'send-email',
  connectionKey: userPickedConnection, // Gmail, Outlook, SendGrid, etc.
  input: { to, subject, body },
})
```

Vendor-specific tweaks (different field names, extra hooks for one
vendor) override at integration level: create a second action with the
same `key` but `integrationKey: "gmail"`. Runtime dispatch picks up
the override automatically when a Gmail connection is used.

### Cross-connection logic

Membrane doesn't model multi-connection actions directly. When work
spans multiple connections:

- **Orchestrate from your backend**: sequential `/act` calls, each
  with its own connection.
- **`code:` dispatch**: a short JS snippet with one connection
  pre-wired; reach for the second connection inside the snippet via
  the `membrane` client.

### Workspace settings for universal flows

Toggled via `PATCH /workspaces/:id` with a manager token:

- **`useMembraneUniverse`** — action discovery spans universal actions
  across every catalog integration, not just workspace integrations.
- **`autoGenerateIntegrationsFromConnectors`** — creates integrations
  on demand when a new connector is used. Needed for universal UX:
  the user picks any connector, and the integration exists for your
  universal action to dispatch through.
- **`autoGenerateIntegrationsFromExternalApps`** — generates
  integrations from the external-apps catalog on demand.

Opt-in because they expand what's visible to the app's users.

### When to stay on step 3 instead

- Vendor-specific headers or edge cases → step 3 catalog `id` or
  inline `api:`.
- Repeated calls to the same app → graduate to a workspace-local
  reusable action (step 3) by `key`.
- Single-vendor product on a deadline → universal is extra design
  work; revisit later.

## Error recovery

When `/act` returns a disconnected-connection error, surface the
`connectionId` back to the UI (or to your ops channel) and let the
user reconnect. Don't create a new connection — the existing one's
OAuth just needs re-authorization.

```ts
if (err.status === 401 || err.payload?.code === 'CONNECTION_DISCONNECTED') {
  // Interactive path: return 409 with the connectionId; frontend
  // calls m.ui.connect({ connectionId }) and retries after the user
  // completes the popup.
  //
  // Unattended workload (cron, worker, sync): log the connectionId
  // and actionRunId, emit an alert, and bail. The next run picks up
  // once an admin has reconnected via the Settings page.
}
```

## Beyond the exposed tools — raw API

Anything the Membrane REST API supports is reachable from code by
minting a token with `get-membrane-token` and calling the endpoint
directly. Notable endpoints not covered by a first-class tool:

- **Restore archived action / connection** — `POST /actions/:id/restore`,
  `POST /connections/:id/restore`.
- **Replace action wholesale** — `PUT /actions/:id` (MCP
  `update-action` only merges).
- **Patch connection** — `PATCH /connections/:id`.
- **Refresh connection credentials** — `POST /connections/:id/refresh`.
- **Inspect / customize integration** — `GET /integrations/:id`,
  `PATCH /integrations/:id`. See `integration-catalog`.

Full API reference:
[docs.getmembrane.com/reference](https://docs.getmembrane.com/reference).
Use `search-docs` to find specific endpoints before calling them.

---

# Frontend Setup

How to initialize Membrane in browser code — React apps, other browser
frameworks, embedded UI. Anything that renders a connect dialog or
reconnect flow belongs here, because it needs a real browser to run
OAuth.

**Golden rule:** the browser never sees your workspace secret. Sign the
token on your server and hand it to the frontend through a
`fetchToken`-style callback. See `backend-setup` for the server route
that mints it.

## Next.js / React

Install `@membranehq/react`. Wrap your app with `MembraneProvider` and
give it a `fetchToken` function that hits your backend:

```tsx
// app/layout.tsx
import { MembraneProvider } from '@membranehq/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <MembraneProvider
          fetchToken={async () => {
            const res = await fetch('/api/membrane-token')
            return (await res.json()).token
          }}
        >
          {children}
        </MembraneProvider>
      </body>
    </html>
  )
}
```

Then anywhere inside the provider tree:

```tsx
import { useMembrane } from '@membranehq/react'

function ConnectButton() {
  const membrane = useMembrane()
  return <button onClick={() => membrane.ui.connect({ integrationKey: 'hubspot' })}>Connect HubSpot</button>
}
```

**Next.js gotcha:** add
`transpilePackages: ['@membranehq/react', '@membranehq/sdk']` to
`next.config.ts`.

## Non-React browser code

Use `@membranehq/sdk` directly. Same token-from-backend pattern — pass
`fetchToken` (or a static `token`) to `MembraneClient`:

```ts
import { MembraneClient } from '@membranehq/sdk'

const membrane = new MembraneClient({
  fetchToken: async () => {
    const res = await fetch('/api/membrane-token')
    return (await res.json()).token
  },
})

await membrane.ui.connect({ integrationKey: 'hubspot' })
```

Vue, Svelte, Angular, plain-JS — same shape. The SDK handles token
refresh automatically when `fetchToken` is provided.

## When to call the frontend SDK

- **UI flows that need user interaction** — `membrane.ui.connect(...)`,
  reconnect dialogs, connection management screens. These must run in
  the browser.
- **Read-only reads tied to the signed-in user** — listing a tenant's
  own connections, reading their own action results — are fine from
  the frontend, because the token is already tenant-scoped.
- **Everything else** — writes on behalf of the app, background syncs,
  workspace-wide admin — belongs on the backend. See `backend-setup`.

## See also

- [React SDK](doc:react)
- [Authentication](doc:authentication)
- [CSP rules](doc:csp-rules) — needed when
  embedding the iframe-based UI helpers.

---

# Backend Setup

How to initialize Membrane in server code — backend routes, background
workers, cron jobs, CLIs, and one-off scripts. Anywhere the workspace
secret can live safely and no user-facing UI flow is running.

This is also where you implement the `/api/membrane-token` route that
`frontend-setup` points at: the frontend asks the backend for a
tenant-scoped JWT, the backend signs one and hands it back.

**Golden rule:** the workspace secret stays on the server. Don't embed
it in browser bundles, mobile apps, desktop apps your users run, or
anywhere a user can inspect the binary.

## The two canonical flows

1. **Credentials-based client** — hand `MembraneClient` your
   `workspaceKey`, `workspaceSecret`, and `tenantKey`; it mints and
   refreshes tokens for you. Best for long-running code with one tenant
   at a time (workers, scripts, CLIs, single-tenant backends).
2. **Token-based client / raw HTTP** — mint a JWT yourself and either
   feed it to `MembraneClient({ token })` or pass it in an
   `Authorization: Bearer <token>` header on a raw `fetch`. Best when
   you need explicit control — multi-tenant request handlers, the
   `/api/membrane-token` route, non-JS services.

Both flows talk to the same API. Pick based on how much control you
need over token lifecycle.

## Using MembraneClient with workspace credentials

Drop-in for scripts, workers, and single-tenant backends.

```ts
import { MembraneClient } from '@membranehq/sdk'

const membrane = new MembraneClient({
  workspaceKey: process.env.MEMBRANE_WORKSPACE_KEY!,
  workspaceSecret: process.env.MEMBRANE_WORKSPACE_SECRET!,
  tenantKey: process.env.MEMBRANE_TENANT_KEY!, // or the end-user id
  apiUri: process.env.MEMBRANE_API_URL,
})

const connections = await membrane.connections.find()
```

The SDK mints an HS256 token per call and refreshes it before expiry.
Swap `tenantKey` per request (by constructing a scoped client) in a
multi-tenant backend.

## Minting a token and calling the API directly

Use this shape when you need fine-grained control, are in a
non-JavaScript runtime, or are writing the `/api/membrane-token` route
for the frontend.

```ts
import jwt from 'jsonwebtoken'

function membraneTokenForTenant(tenantKey: string) {
  return jwt.sign(
    {
      workspaceKey: process.env.MEMBRANE_WORKSPACE_KEY!,
      tenantKey,
    },
    process.env.MEMBRANE_WORKSPACE_SECRET!,
    { algorithm: 'HS256', expiresIn: 3600 },
  )
}

// Example: Next.js API route that vends tokens to the browser
export async function GET(req: Request) {
  const tenantKey = await resolveTenantForUser(req) // your auth system
  return Response.json({ token: membraneTokenForTenant(tenantKey) })
}

// Or: call Membrane directly from the server
async function listConnections(tenantKey: string) {
  const token = membraneTokenForTenant(tenantKey)
  const res = await fetch(`${process.env.MEMBRANE_API_URL}/connections`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.json()
}
```

The `get-membrane-token` tool has the full payload reference and
signing examples in Python, Go, Ruby, Java, and PHP if you're not in
a JS runtime.

## Scripts and CLIs

Same model as a backend route: pull the workspace credentials from a
local env file (or `get-credentials`), mint a token, call the API.
Single-tenant scripts can hardcode the tenant key tied to your console
session — that's the tenant `get-credentials` returns by default.

```ts
// scripts/sync-hubspot.ts
import { MembraneClient } from '@membranehq/sdk'

const membrane = new MembraneClient({
  workspaceKey: process.env.MEMBRANE_WORKSPACE_KEY!,
  workspaceSecret: process.env.MEMBRANE_WORKSPACE_SECRET!,
  tenantKey: process.env.MEMBRANE_TENANT_KEY!,
})

const contacts = await membrane.connection('hubspot-prod').action('list-contacts').run({})
```

## See also

- [Authentication](doc:authentication)
- [Tenants](doc:tenants)
- The `get-credentials` tool — returns `workspaceKey`,
  `workspaceSecret`, `tenantKey`, and `apiUrl` for the current
  environment.
- The `get-membrane-token` tool — returns a signed JWT ready to use.

---

# Integration Catalog

How to set up and configure the workspace's integration catalog — the
set of integrations your product (or your scripts) reference by
`integrationKey` at runtime. Configuration work that happens at build
or admin time, not runtime.

## Runtime UI pattern

If you're building an integrations page in your product, the standard
runtime shape is:

1. Fetch the current tenant's `connections`
2. Fetch available `integrations`
3. Render connected accounts separately from apps the user can still connect
4. Use `membrane.ui.connect(...)` to launch connect or reconnect
5. Archive a connection to disconnect it

```tsx
import { useConnections, useIntegrations, useMembrane } from '@membranehq/react'

function IntegrationsPage() {
  const membrane = useMembrane()
  const { items: integrations = [] } = useIntegrations()
  const { items: connections = [] } = useConnections()

  const connectedIntegrationIds = new Set(connections.map((c) => c.integrationId))
  const availableIntegrations = integrations.filter((i) => !connectedIntegrationIds.has(i.id))

  return (
    <>
      {connections.map((connection) => (
        <div key={connection.id}>
          <span>{connection.name}</span>
          {connection.disconnected ? (
            <button onClick={() => membrane.ui.connect({ connectionId: connection.id })}>Reconnect</button>
          ) : (
            <button onClick={() => membrane.connection(connection.id).archive()}>Disconnect</button>
          )}
        </div>
      ))}

      {availableIntegrations.map((integration) => (
        <button key={integration.id} onClick={() => membrane.ui.connect({ integrationKey: integration.key })}>
          Connect {integration.name}
        </button>
      ))}
    </>
  )
}
```

For non-React frontend apps, follow the same shape: fetch a transient
token from your backend, list integrations and connections in the UI,
and trigger the same connect / reconnect flow from frontend code. For
backend routes, workers, or cron jobs behind that UI, use raw API calls
plus a short-lived Membrane token rather than using the server-side SDK.

### Backend-only scaffold? Add a minimal frontend.

If the scaffold is an API-only Express / Fastify / Next route handler
with no UI, you still need a frontend surface for the connect flow.
Serve a single static HTML page from your backend; it fetches a
per-user token from your app and calls `membrane.ui.connect` via the
browser SDK:

```html
<!-- served as GET / or GET /admin from your backend -->
<!doctype html>
<html>
  <body>
    <button id="connect-github">Connect GitHub</button>
    <script type="module">
      import { MembraneClient } from 'https://esm.sh/@membranehq/sdk'
      const { token } = await (await fetch('/api/membrane-token')).json()
      const m = new MembraneClient({ token, apiUri: 'https://api.getmembrane.com' })
      document.getElementById('connect-github').onclick = () =>
        m.ui.connect({ connectorKey: 'github', connectionKey: 'github-dev' })
    </script>
  </body>
</html>
```

The `/api/membrane-token` route is a thin backend endpoint that signs
the JWT (see Authentication in the kit) and returns `{ token }`.
This is the **only** correct end-user connect pattern — do not ship
CLI instructions to end users, and do not have the backend return
`clientAction.uiUrl` for the user to manually paste.

### React hook / client quick reference

All come from `@membranehq/react`:

```ts
// client — has all the methods you call imperatively
const m = useMembrane()
m.ui.connect({ connectorKey })            // new connection (catalog-level)
m.ui.connect({ integrationKey })          // new connection (workspace-level)
m.ui.connect({ connectionId })            // reconnect an existing connection
m.connection(id).archive()                // disconnect

// hooks — SWR-style; re-render on changes
const { items: integrations, loading, error } = useIntegrations({ search?: string })
const { items: connections, loading, error } = useConnections({ integrationKey?: string })

// shape of a Connection
type Connection = {
  id: string
  key: string
  name: string
  integrationId: string
  disconnected: boolean
  state: 'READY' | 'DISCONNECTED' | 'ERROR' | 'BUILDING' | ...
}

// shape of an Integration
type Integration = {
  id: string
  key: string
  name: string
  logoUri?: string
}
```

## Where actions fit

Once an app is connected, product features usually do not need anything
more complicated than actions:

- Run inline `act` calls with `api` or `code` directly from your
  backend, worker, or cron job
- Mint the token for those backend calls with `get-credentials` or
  `get-membrane-token`; keep SDK usage in the frontend layer
- Save a reusable action only when you want a stable key, schema, or
  shared abstraction across many call sites
- A "sync" is often just repeated action execution on a schedule from
  your own job runner

Reach for richer Membrane primitives like data sources, field mappings,
and flows when you want Membrane to own more of the sync orchestration,
event handling, or tenant-customizable mappings.

## Create an integration from a connector

Every integration is backed by a **connector** (the vendor-specific
adapter Membrane keeps in its catalog). Create an integration once,
reference it by a stable `integrationKey` forever after.

```bash
curl -X POST $API/integrations -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"key":"github","name":"GitHub","connectorKey":"github"}'
```

The resulting integration accepts connections (`connect
--integrationKey github`) and reusable actions (`create-action
--integrationKey github`).

## Integration parameters

Parameters configure how an integration behaves: OAuth client
credentials, default scopes, API-specific settings. They live on the
integration and can be updated without recreating it.

```bash
# fetch
curl -sG $API/integrations/<id>/parameters -H "Authorization: Bearer $TOKEN"

# set
curl -X PATCH $API/integrations/<id>/parameters -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"clientId":"...","clientSecret":"..."}'
```

## Auto-generated integrations

With `connectors=1` / `externalApps=1` (see `list-integrations`), the
workspace synthesises integrations from the catalog on demand —
agents can connect to an app that doesn't yet have a dedicated
integration, and one is created automatically. Explicit
`POST /integrations` is only needed when you want to pre-seed the
catalog with custom names, parameters, or connector versions.

The first such connect can take longer than a normal connection flow:
Membrane may search the catalog, create the integration record, or spin
up an agent to build a new connector. Expect an initial `BUILDING`
phase. If that build/setup path fails, you'll usually see
`CONFIGURATION_ERROR` or `SETUP_FAILED`; refine the intent or inspect
the exact failure before retrying.

## Archive and restore

Integrations can be archived instead of deleted — `DELETE
/integrations/<id>` archives by default. Archived integrations are
hidden from `list-integrations` unless `includeArchived=1` is set.
Restore with `POST /integrations/<id>/restore`.

## See also

- [Integrations (API)](ref:integrations)
- [Product Integrations](doc:product-integrations)
- [React SDK](doc:react)
- [Integration Catalog guide](doc:integration-catalog)
- [Data Integrations](doc:data-integrations)
- [Create integration](ref:create-integration)
- [Set integration parameters](ref:set-integration-parameters)
- [Import and Export](doc:import-and-export)

---

# Troubleshooting

When something breaks in Membrane, the fix almost always involves two
resources at once — a failing `act` call and the connection it runs
through. This context captures the cross-cutting workflow; the per-tool
docs cover mechanics (how to reconnect, what the log schema looks
like, what each state means).

## The diagnostic loop

Follow this loop when an action call fails. Each step feeds the next:

1. **Read the response.** Every `act` response carries an
   `actionRunId` — on success _and_ on 4xx. Grab it.
2. **Pull the run log.** Call `get-action-run-log` with
   `includeDetails: true`. This is the fastest way to see Membrane's
   mapped input, the output, the error, and — crucially — the **raw
   HTTP exchange with the external app**. Most failures are answered
   here without looking anywhere else.
3. **Classify what the log shows.** Route to the matching fix:
   - Auth / disconnected → reconnect.
   - Wrong input shape / missing field → fix the `act` input and
     retry (inline `api` / `code` is the smallest test bed).
   - External app returned an error → read its body in the log; fix
     the input or change the endpoint.
   - Connector configuration missing → see `integration-catalog`.
4. **Retry with the smallest possible call.** Reduce a failing sync or
   reusable action down to a single inline `act` (`api` or `code`)
   first. Once that works, promote back up.

## Log layers — drill top-down

Membrane records three layers of evidence; read them in order:

1. **Action run log** — one record per `act` call. Contains Membrane's
   view of the call: input, output, error, state transitions, and (with
   `includeDetails: true`) the raw HTTP exchange. Start here.
2. **External API log** — the raw request/response sent to the vendor,
   visible under `includeDetails`. Use when the action run log says
   "external error" and you need to see the vendor's exact response
   body / status code.
3. **Webhook log** — raw incoming payloads from the vendor. Use only
   when debugging event-driven flows; irrelevant for synchronous `act`
   calls.

You rarely need to drop below layer 2.

## Symptom → tool mapping

| Symptom                                            | First move                                            |
| -------------------------------------------------- | ----------------------------------------------------- |
| `act` returned an error with an `actionRunId`      | `get-action-run-log` with `includeDetails: true`      |
| Auth error / "connection disconnected"             | `connect` with the failing `connectionId`             |
| Connection is in `BUILDING` too long               | Wait, then `list-connections` to see final state      |
| Connection landed in `CONFIGURATION_ERROR`         | Re-run `connect`; inspect the returned error          |
| Connection landed in `SETUP_FAILED`                | Connector couldn't be built; try a different `intent` |
| "Integration not found" / "no matching action"     | `list-integrations` or `list-actions` before retrying |
| Reusable action produces the wrong output          | Rebuild it inline with `act` + `api` / `code` first   |
| Issue feels platform-wide (many tenants, webhooks) | `search-docs` for the affected feature                |

## See also

- [Monitoring and Troubleshooting](doc:monitoring-troubleshooting)
- [Logs](doc:logs)
- [API Errors](ref:errors)
- [Action run log](ref:get-action-run-log)

## Tools

### Get Credentials

```bash
membrane credentials
```

Get the credentials needed to talk to Membrane from any backend.
Use this for backend routes, workers, cron jobs, or server-side scripts.
Frontend code should fetch a transient token from your backend and then
use the frontend SDK.

Returns:

- **Workspace key** — which Membrane workspace to hit.
- **Workspace secret** — used to sign JWTs. Keep server-side only.
- **Tenant key** — scopes calls to one user's set of connections.
  Use the console-session tenant for testing; in production, substitute
  a unique identifier for the current end-user.
- **API URL** — the Membrane endpoint for the current environment.

If you get 401 errors later, the workspace secret may have been
rotated — call this tool again to get the fresh one.

**In code**

Use the returned values to mint a JWT and authenticate API calls:

```bash
# 1. Mint a token (HS256, 1-hour expiry)
TOKEN=$(node -e "
  const jwt = require('jsonwebtoken');
  console.log(jwt.sign(
    {
      workspaceKey: '<workspaceKey>',
      tenantKey: '<tenantKey>',
      name: 'Acme Inc'
    },
    '<workspaceSecret>',
    { algorithm: 'HS256', expiresIn: 3600 }
  ))
")

# 2. Use it
curl -sG $API/connections -H "Authorization: Bearer $TOKEN"
```

Any language with a JWT library works — the payload is
`{ "workspaceKey": "<workspaceKey>", "tenantKey": "<tenantKey>" }`
plus optional display metadata like `name`, signed with the workspace
secret. Never expose the secret in browser/client code.

### Get Membrane Token

```bash
membrane token [--tenantKey <key>] [--manager] [--expiresIn <duration>] [--json]
```

Generate a Membrane token — a short-lived JWT used to authenticate
requests to the Membrane API. Call this tool when you need a token for
`Authorization: Bearer <token>` headers from backend code. Frontend code
should ask your backend for a transient token and then use the frontend
SDK.

**Input**

- `tenantKey` (optional) — identifies the isolated scope of connections
  the token will access. Defaults to the tenant tied to your current
  console session.
- `manager` (optional, CLI only) — mint a **workspace manager token**
  for workspace-level mutations like `POST /actions`, integration
  parameter edits, and import/export. Matches the engine's
  `workspaceAsManager` auth layer. Tenant key is optional when
  `manager` is set. (Payload carries `isAdmin: true` for backwards
  compatibility with the engine's existing auth resolution.)
- `expiresIn` (optional, CLI only) — token lifetime, e.g. `5m`, `1h`,
  `24h`. Default: `1h`.

**Response**

A JWT string. Pass it as `Authorization: Bearer <token>` on every
API call.

**Token payload**

| Field          | Required | Description                                                                         |
| -------------- | -------- | ----------------------------------------------------------------------------------- |
| `workspaceKey` | Yes      | Your workspace key.                                                                 |
| `tenantKey`    | No       | Identifier of the tenant (user, team, or org). Omit for workspace-level operations. |
| `name`         | No       | Human-readable tenant name (helps with troubleshooting).                            |
| `fields`       | No       | Additional metadata to store about the tenant.                                      |
| `isAdmin`      | No       | Set `true` for a **workspace management token** (no `tenantKey`).                   |

**In code**

Three to five lines in any language with a JWT library. Always sign
server-side — anyone with the workspace secret can mint tokens for any
tenant.

```javascript
import jwt from 'jsonwebtoken'

const token = jwt.sign(
  {
    workspaceKey: '<WORKSPACE_KEY>',
    tenantKey: '<TENANT_ID>',
    name: '<TENANT_NAME>',
  },
  '<WORKSPACE_SECRET>',
  { expiresIn: 7200, algorithm: 'HS256' },
)
```

```python
import datetime, jwt

token = jwt.encode(
    {
        "workspaceKey": "<WORKSPACE_KEY>",
        "tenantKey": "<TENANT_ID>",
        "name": "<TENANT_NAME>",
        "exp": datetime.datetime.now() + datetime.timedelta(seconds=7200),
    },
    "<WORKSPACE_SECRET>",
    algorithm="HS256",
)
```

```go
import (
    "time"
    "github.com/golang-jwt/jwt/v5"
)

claims := jwt.MapClaims{
    "workspaceKey": "<WORKSPACE_KEY>",
    "tenantKey":    "<TENANT_ID>",
    "name":         "<TENANT_NAME>",
    "exp":          time.Now().Add(time.Hour * 2).Unix(),
}
token, _ := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).
    SignedString([]byte("<WORKSPACE_SECRET>"))
```

```ruby
require 'jwt'

payload = {
  workspaceKey: '<WORKSPACE_KEY>',
  tenantKey: '<TENANT_ID>',
  name: '<TENANT_NAME>',
  exp: Time.now.to_i + 7200,
}
token = JWT.encode(payload, '<WORKSPACE_SECRET>', 'HS256')
```

```java
String token = Jwts.builder()
    .claim("workspaceKey", "<WORKSPACE_KEY>")
    .claim("tenantKey", "<TENANT_ID>")
    .claim("name", "<TENANT_NAME>")
    .setExpiration(Date.from(Instant.now().plusSeconds(7200)))
    .signWith(
        new SecretKeySpec("<WORKSPACE_SECRET>".getBytes(), "HmacSHA256"),
        SignatureAlgorithm.HS256)
    .compact();
```

```php
$token = JWT::encode([
    'workspaceKey' => '<WORKSPACE_KEY>',
    'tenantKey'    => '<TENANT_ID>',
    'name'         => '<TENANT_NAME>',
    'exp'          => time() + 7200,
], '<WORKSPACE_SECRET>', 'HS256');
```

```bash
# Shell: sign via Node for a one-off curl call
TOKEN=$(node -e "
  const jwt = require('jsonwebtoken');
  console.log(jwt.sign(
    { workspaceKey: '<WORKSPACE_KEY>', tenantKey: '<TENANT_ID>' },
    '<WORKSPACE_SECRET>',
    { algorithm: 'HS256', expiresIn: 3600 }
  ));
")
curl -sG $API/connections -H "Authorization: Bearer $TOKEN"
```

**Other ways to get a token**

- **Public/private key signing** — for stricter key management, sign
  with a workspace-owned private key using any asymmetric algorithm
  (`ES256`, `RS256`, `PS256`, …) and register the public key in
  workspace settings. Drop-in replacement for the examples above.
- **Workspace management token** — add `isAdmin: true` (and omit
  `tenantKey`) for operations that span tenants: managing tenants,
  workspace settings, import/export.
- **Test token** — grab a pre-generated one from the Access page in
  Console Settings when you just need to poke the API quickly.
- **Long-lived token** — create one from the Client Tokens section on
  the Access page when you need a token that doesn't expire (e.g. for
  a server-to-server job that can't refresh mid-run).
- **Developer token** — acts on behalf of your Membrane account across
  all your workspaces. Issued from API Tokens in Console Settings.

See the [authentication docs](https://docs.getmembrane.com/docs/authentication.md)
for the full reference.

### List Connections

```bash
membrane connection list [--integrationKey <key>] [--search "<text>"] [--limit <n>] [--cursor <cursor>]
```

List active connections for the current tenant. Use it to check
whether a connection already exists before asking the user to
authenticate again.

**Filters**

- `integrationKey` / `integrationId` — narrow to one integration.
- `search` — free-text match on name / key.
- `limit`, `cursor` — standard pagination.

**Response**

Each record carries identifiers like `id`, `key`, `integrationId`,
connection name, and connection status. Feed `connectionId` or
`connectionKey` into `act` to run actions on the connection.

**In code**

```bash
# all connections
curl -sG $API/connections -H "Authorization: Bearer $TOKEN"

# filter to one integration
curl -sG $API/connections -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'integrationKey=github'
```

### Delete Connection

```bash
membrane connection delete <identifier> [--json]
```

Archive a connection by id or key. The connection stops appearing in
`list-connections` and can no longer be used by `act`. This is the
disconnect operation — Membrane soft-deletes by default; use the raw
API to restore or purge.

**Input**

- `connectionId` — the connection's database id.

**When to use**

- Revoking a user's connection (e.g. the user disconnects HubSpot
  from your app's settings).
- Tenant deletion or account cleanup — archive every connection tied
  to the tenant.
- Replacing a misconfigured connection with a freshly created one.

**In code**

```bash
# Shell
curl -s -X DELETE "$API/connections/<id>" -H "Authorization: Bearer $TOKEN"
```

```ts
// SDK
import { MembraneClient } from '@membranehq/sdk'
const membrane = new MembraneClient({ token })
await membrane.connection('<id>').archive()
```

### List Integrations

```bash
membrane integration list [--search "<text>"] [--connectors 1] [--externalApps 1] [--limit <n>] [--cursor <cursor>]
```

Browse what the user can connect to. Returns workspace integrations
plus, when enabled, synthetic integrations derived from catalog
connectors and external apps (candidates that can become full
integrations when someone connects to them).

**Filters**

- `search` — free-text on name / key / description. Omit to browse the
  full catalog.
- `connectors` — include synthetic integrations sourced from
  connectors in the Membrane catalog (`1` enable, `0` disable;
  workspace default applies when omitted).
- `externalApps` — same for external apps not yet turned into
  integrations.
- `limit`, `cursor` — standard pagination.

**Response**

Each item carries enough identifiers (`id`, `key`, `connectorKey`
where relevant, display name, logo) to hand straight to `connect`.

If nothing matches the user's intent, skip this step and call
`connect` with `intent: "…"` — the server will search connectors and
spin up an agent to build one on the fly if needed.

**In code**

```bash
# free-text search
curl -sG $API/integrations -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'search=crm'

# include catalog candidates that could become integrations
curl -sG $API/integrations -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'connectors=1' --data-urlencode 'externalApps=1'
```

### Connect

```bash
membrane connect [--integrationKey <key>] [--integrationId <id>] [--connectorKey <key>] [--connectorId <id>] [--connectionId <id>] [--connectionKey <key>] [--intent "<text>"] [--name <name>] [--non-interactive]
```

Create a connection to an external app — or reconnect an existing
one. Returns the connection with `id`, `state`, and, while the user
still needs to authenticate, `clientAction.uiUrl` — hand that URL to
the user so they can finish the OAuth flow.

The returned `id` is the connection id to reuse for reconnects,
lookups, and future debugging.

**How you tell it what to connect**

- `integrationKey` / `integrationId` — a known integration in the
  workspace.
- `connectorKey` / `connectorId` — a connector (useful when no
  integration exists yet; the server creates an integration on
  demand).
- `intent` — free-text description of what the user wants to connect
  to. The server searches connectors/integrations and picks a match;
  if nothing fits, it spins up an agent to build a connector.
- `connectionId` — reconnect an existing connection (same OAuth flow,
  same record).

Feed any concrete identifier you get from `list-integrations`
straight into one of these. Mix freely — e.g. `integrationKey` +
`connectionKey` to create a new connection under a stable key.

When `intent` or a catalog candidate requires generating something new,
the first connect may take longer than a normal OAuth redirect. Expect a
short `BUILDING` phase while Membrane searches the catalog, creates an
integration, or builds a connector. If that path fails, the connection
will land in `CONFIGURATION_ERROR` or `SETUP_FAILED`.

**Connection key**

Pass your own `connectionKey` to identify the connection later (`act
{ connectionKey, ... }`, `list-connections`, reconnect). If you omit
it, the server assigns one.

**Reconnect**

Call `connect` with `connectionId` pointing at an existing
connection (e.g. one that hit an auth error). Same OAuth flow, same
record — no new connection is created.

**Response**

A full connection object:

```
{
  "id": "...",
  "key": "...",
  "state": "BUILDING" | "CLIENT_ACTION_REQUIRED" | "READY" | "CONFIGURATION_ERROR" | "SETUP_FAILED",
  "clientAction": { "type": "connect", "uiUrl": "..." }?,
  ...
}
```

Interactive CLI blocks until `state` is `READY`. On MCP, the connect
panel renders `clientAction.uiUrl` and updates the connection state
when the user finishes.

**In code**

Connecting requires user interaction — the OAuth / consent flow has
to run in a real browser — so it lives on the **front-end** and goes
through the Membrane SDK's UI helper. Do not hand-roll HTTP calls;
`membrane.ui.connect(...)` opens the hosted connect screen as an
iframe overlay, handles the OAuth round-trip and any agent-built
connector flow, and resolves with the finished connection (or `null`
if the user closes the dialog).

```ts
import { MembraneClient } from '@membranehq/sdk'

// Mint the token on your backend with get-membrane-token and hand it
// to the browser — never embed workspace secrets in front-end code.
const membrane = new MembraneClient({ token })

// Connect by connector key (catalog-level; resolves in a fresh workspace)
const connection = await membrane.ui.connect({
  connectorKey: 'github',
  connectionKey: 'github-dev',
})

// Connect by integration key (only once you've confirmed the
// integration exists in the current workspace, e.g. via
// `membrane integration list --search github`)
const existing = await membrane.ui.connect({
  integrationKey: 'github',
  connectionKey: 'github-dev',
})

// Connect by intent (agent may build a connector if needed)
const built = await membrane.ui.connect({
  intent: 'connect my GitHub account',
})

// Reconnect an existing connection (same record, fresh OAuth)
const reconnected = await membrane.ui.connect({
  connectionId: existing.id,
})

if (!connection) {
  // User closed the dialog before completing the flow
  return
}
```

In React, use `@membranehq/react`'s `useMembrane()` hook to get the
same client — `useMembrane().ui.connect({...})` — so you don't have
to wire up `MembraneClient` manually.

### List Actions

```bash
membrane action list [--connectionId <id>] [--connectionKey <key>] [--intent "<text>"] [--limit <n>]
```

Find reusable actions in the workspace. Use it to discover what can be
run by `key` before reaching for `act` (run) or `create-action` (save
a new one).

**Filters**

- `connectionId` / `connectionKey` — narrow to a specific connection's
  action surface.
- `intent` — natural-language description. Paired with a connection
  (id or key), results are ranked by semantic match. Without a
  connection, `intent` is ignored.
- `limit`, `cursor` — standard pagination.

**Response**

Each item carries `id`, `key`, `name`, `description`, `integrationKey`,
`layer`, `inputSchema`, and `outputSchema` — enough to feed straight
into `act`. If nothing matches, move on to `create-action` (intent
path) to build one.

Catalog actions (returned when you filter by `--externalAppId`) come
back with an empty `key` field — dispatch them via `act --id <hex>`.
Workspace-local actions have a non-empty `key` and can be dispatched
either way.

**In code**

```bash
# semantic match on a specific connection
curl -sG $API/actions -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'connectionId=<id>' \
  --data-urlencode 'intent=create a contact'
```

### Act

```bash
membrane act [--id <id>] [--key <key>] [--integrationKey <key>] [--connectionKey <key>] [--connectionId <id>] [--api <json>] [--code <text>] [--input <json>] [--meta <json>]
```

Run an action. One unified call — reusable action or inline spec — via
`POST /act`.

Inline `api` and `code` execution is the default building block for app
features, scripts, and sync jobs. Use reusable actions when you want a
stable key, shared schema, or abstraction you can call from many places.

**Exactly one dispatch field**

- `id` — a reusable action's database id.
- `key` — a reusable action's key. Pair with `integrationKey` /
  `integrationId` / `connectionId` / `connectionKey` when the same key
  exists across integrations.

Catalog/public actions (from `list-actions --externalAppId …`) return
an `id` but no `key` — dispatch them by `id`. For workspace-local
actions, `id` and `key` are interchangeable.

- `api` — an inline HTTP request sent through the resolved connection's
  auth layer and base URL: `{ method, path, body?, headers?, query? }`.
- `code` — inline JavaScript run in a sandbox:
  `module.exports = ({ input, membrane, connection, integration }) => …`.
  Its return value is the action output.

`api` and `code` require a connection. Provide `connectionId` /
`connectionKey` / `integrationId` / `integrationKey`, or rely on the
workspace default.

**Connection resolution**

Priority: `connectionId` → `connectionKey` → integration default (from
`integrationId` or `integrationKey`) → workspace default. Same chain as
`POST /actions/:selector/run`.

**Response**

```
{ "output": ..., "actionRunId": "..." }
```

On 4xx the response still carries `actionRunId` — use it with the
action run log to debug.

**In code**

```bash
# reusable action by key
curl -X POST $API/act -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"key":"create-issue","integrationKey":"github","input":{"title":"Hello"}}'

# inline HTTP through a connection
curl -X POST $API/act -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"api":{"method":"GET","path":"/user/repos"},"connectionKey":"github-dev"}'

# inline JS
curl -X POST $API/act -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"code":"module.exports = ({ input }) => ({ echoed: input })","input":{"hi":1},"connectionKey":"github-dev"}'
```

### Create Action

```bash
membrane action create [--intent "<text>"] [--key <key>] [--name <name>] [--type <type>] [--config <json>] [--inputSchema <json>] [--integrationId <id>] [--integrationKey <key>] [--connectionId <id>]
```

Save a reusable action into the workspace. Two paths:

**By intent** — pass `intent: "…"` + an integration or connection
context. A Membrane Agent builds the action against the vendor's API,
validates it, and registers it. Response returns the action `id` in
`BUILDING` state; poll `list-actions` (filter by id) until `state` is
`READY`, then run it with `act`.

**By explicit spec** — pass `type` (e.g. `api-request-to-external-app`,
`run-javascript`, `list-data-records`, …), `config` (the type-specific
payload), and optional `key` / `name` / `inputSchema`. Use when you
already know the shape — e.g. you tested it as an inline `act` call
and now want to reuse it.

**Where it lives**

- `connectionId` set → connection-level action instance (scoped to one
  connection).
- `integrationId` / `integrationKey` set (no connection) →
  integration-level action (available to every connection on that
  integration).
- Neither → universal action (available across all integrations that
  support the shape).

**Response**

```
{ "id": "...", "state": "BUILDING" | "READY" | "ERROR", ...standard action fields }
```

Once the action is `READY`, run it with `act` by `id` or by
`{ integrationKey, key }`.

**In code**

```bash
# intent
curl -X POST $API/actions -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"intent":"open a pull request","integrationKey":"github"}'

# explicit spec
curl -X POST $API/actions -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"key":"list-users","type":"api-request-to-external-app","integrationKey":"github",
       "config":{"request":{"method":"GET","path":"/users"}}}'
```

### Get Action

```bash
membrane action get <id> [--wait] [--timeout <seconds>] [--json]
```

Fetch a single reusable action by id. Returns the full record —
`id`, `key`, `name`, `state`, `type`, `config`, `inputSchema`,
`outputSchema`, and the owning `integrationId` / `connectionId`.

**Input**

- `id` — the action's database id. Works for both integration-level
  Actions and connection-level ActionInstances.

**When to use**

- After `create-action` returned `state: BUILDING` — poll with this
  until `state: READY`.
- Before calling `act` by `id` / `key` to confirm the action exists
  and matches the shape you expect.
- When an `act` call returns an error that looks like an action
  config problem — inspect the stored `config` / `inputSchema`.

**In code**

```bash
# Shell
curl -s "$API/actions/<id>" -H "Authorization: Bearer $TOKEN"
```

```ts
// SDK
import { MembraneClient } from '@membranehq/sdk'
const membrane = new MembraneClient({ token })
const action = await membrane.action('<id>').get()
```

### Update Action

```bash
membrane action update <selector> [--connectionId <id>] [--integrationId <id>] --data <json> [--json]
```

Partially update a reusable action by id or key. Merge semantics —
pass only the fields you want to change. For whole-record replacement
use the raw API (`PUT /actions/:selector`).

**Input**

- `id` — the action's database id (or use CLI `<selector>` which
  accepts id or key).
- `data` — fields to merge. Common ones: `name`, `description`,
  `config`, `inputSchema`, `key`. The exact shape depends on the
  action `type`.

**Scope hints (CLI only)**

- `--connectionId` / `--integrationId` — disambiguate when a key
  exists on both a connection-level instance and an integration-level
  action. Not needed when you pass a database id.

**When to use**

- Iterating on a reusable action you just built — tighten the prompt,
  rename it, adjust the schema — without recreating.
- Promoting a tested inline `act` into a reusable action usually
  happens via `create-action`, but tweaking its `config` afterward
  uses this tool.

**In code**

```bash
# Shell — merge update
curl -s -X PATCH "$API/actions/<id>" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Create HubSpot contact"}'
```

```ts
// SDK
import { MembraneClient } from '@membranehq/sdk'
const membrane = new MembraneClient({ token })
const updated = await membrane.action('<id>').patch({ name: 'Create HubSpot contact' })
```

### Delete Action

```bash
membrane action delete <selector> [--connectionId <id>] [--integrationId <id>] [--json]
```

Archive a reusable action by id or key. Archived actions stop
appearing in `list-actions` and can no longer be called by `act`.
Membrane soft-deletes by default — use the raw API to restore
(`POST /actions/:id/restore`) or to purge permanently.

**Input**

- `id` — the action's database id (or CLI `<selector>` accepts id or
  key).

**Scope hints (CLI only)**

- `--connectionId` / `--integrationId` — disambiguate when a key
  exists on both a connection-level instance and an integration-level
  action. Not needed when you pass a database id.

**When to use**

- Cleaning up experiment actions that didn't pan out.
- Removing stale integration-level actions superseded by newer keys.

**In code**

```bash
# Shell
curl -s -X DELETE "$API/actions/<id>" -H "Authorization: Bearer $TOKEN"
```

```ts
// SDK
import { MembraneClient } from '@membranehq/sdk'
const membrane = new MembraneClient({ token })
await membrane.action('<id>').archive()
```

### Get Action Run Log

```bash
membrane action-run-log get <actionRunId> [--details]
```

Fetch Membrane's record of a single action run. Every `act` response
carries an `actionRunId` (present on both success and 4xx errors) —
feed it in here to see what actually happened.

**Input**

- `actionRunId` — the id returned by `act`.
- `details` (optional) — when true, also includes the detailed run
  content: the raw HTTP exchange with the external app, the mapped
  input, the output.

**Response**

```
{
  "id": "...", "status": "success" | "error",
  "action": { ... }, "connection": { ... }, "integration": { ... },
  "input": ..., "output": ..., "error": ...,
  "details"?: { "request": {...}, "response": {...}, ... }
}
```

Summary fields tell you the shape of the call. If the action failed,
pull up `details` to see the exact HTTP request Membrane made and
what the external app returned.

**In code**

```bash
# summary
curl -sG $API/action-run-logs/<runId> -H "Authorization: Bearer $TOKEN"

# raw HTTP exchange (request/response content)
curl -sG $API/action-run-logs/<runId>/details -H "Authorization: Bearer $TOKEN"
```
