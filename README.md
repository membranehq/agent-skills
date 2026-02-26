<div align="center">
  <a href="https://getmembrane.com">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/images/logo-light.png">
      <source media="(prefers-color-scheme: light)" srcset=".github/images/logo-dark.png">
      <img alt="Membrane" src=".github/images/logo-dark.png" width="300">
    </picture>
  </a>

  <h1>Integration Skills by Membrane</h1>

  <p><strong>Give your AI agent the power to connect to any API and take action.</strong></p>

  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://agentskills.io/"><img src="https://img.shields.io/badge/Agent_Skills-compatible-green.svg" alt="Agent Skills"></a>
</div>

<br>

Reusable skills that let AI agents connect to Slack, HubSpot, Salesforce, GitHub, Jira, Google Sheets, and 100,000+ apps through [Membrane](https://getmembrane.com). Built on the open [Agent Skills](https://agentskills.io/) specification.

## What are Integration Skills?

- **Any app, any action** — Connect to any API on the fly. If a connector doesn't exist, Membrane's AI agent builds one for you automatically.
- **Works with your agent** — Drop-in support for Claude Code, Cursor, GitHub Copilot, Gemini CLI, and any agent that supports the Agent Skills spec.
- **Two skills, two use cases** — Use `integrate-anything` to let your agent talk to apps directly. Use `build-product-integrations` when you're building a product that needs integration features.
- **Auth handled for you** — OAuth flows, API keys, token refresh — Membrane manages credentials so your agent doesn't have to.

## Installation

Install all skills:

```bash
npx skills add membranehq/agent-skills
```

Install a specific skill:

```bash
npx skills add membranehq/agent-skills --skill integrate-anything
```

Or using the shorthand:

```bash
npx skills add membranehq/agent-skills@integrate-anything
```

## Available Skills

### `integrate-anything`

**For users and agents.** Install this skill and your AI agent can connect to any external app and take actions on your behalf — send Slack messages, create Jira tickets, update HubSpot contacts, push to GitHub, and more.

```bash
npx skills add membranehq/agent-skills@integrate-anything
```

**Example — what this looks like in practice:**

```
You:    "Send a message to #general on Slack saying the deploy is done"

Agent:  1. Checks for an existing Slack connection (or authenticates you)
        2. Finds the "Send Message" action via natural language search
        3. Runs the action with channel=#general, message="The deploy is done"

Done — message sent. No code written, no API docs, no tokens to manage.
```

```
You:    "Create a Jira ticket for the login bug, assign it to me, priority high"

Agent:  1. Connects to Jira (if not already connected)
        2. Finds the "Create Issue" action
        3. Runs it with project, summary, assignee, and priority fields

Done — ticket created and assigned.
```

---

### `build-product-integrations`

**For developers building products.** This skill teaches your agent how to add integration features to your app — connection UI for your users, OAuth flows, running actions on their behalf, syncing data, handling webhooks, and exposing integrations as AI agent tools.

```bash
npx skills add membranehq/agent-skills@build-product-integrations
```

**Example — what this looks like in practice:**

```
You:    "Add a Slack integration to our app so users can connect their workspace
         and we can send notifications on their behalf"

Agent:  1. Sets up backend token generation for your users
        2. Adds the Membrane React SDK with connection UI components
        3. Wires up the OAuth flow so users can connect their Slack
        4. Creates a sendNotification() function that runs the Send Message action
        5. Handles token refresh and error states

Done — your users can now connect Slack and receive notifications.
```

**Covers:** JavaScript SDK, React SDK, REST API, frontend connection UI, backend token generation, data collections, flows, and more.

---

## Custom Agent Tools

If you're building a custom agent and need Membrane tools embedded directly in your code, see [`agents/`](agents). Each subdirectory contains a ready-to-run agent example with the framework adapter:

| Agent | Framework |
|---|---|
| [openai](agents/openai/) | OpenAI SDK |
| [vercel-ai-sdk](agents/vercel-ai-sdk/) | Vercel AI SDK |
| [langchain](agents/langchain/) | LangChain |
| [opencode](agents/opencode/) | OpenCode Plugin |

Tool definitions live in [`tools/self-integration.ts`](tools/self-integration.ts).

## Resources

- [Membrane Console](https://console.getmembrane.com) — Dashboard for managing workspaces, connections, and API tokens
- [Membrane Docs](https://getmembrane.com) — Full documentation
- [Agent Skills Spec](https://agentskills.io/) — The open specification these skills are built on

## License

MIT
