<div align="center">
  <a href="https://getmembrane.com">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/images/logo-light.png">
      <source media="(prefers-color-scheme: light)" srcset=".github/images/logo-dark.png">
      <img alt="Membrane" src=".github/images/logo-dark.png" width="300">
    </picture>
  </a>

  <h1>Agent Skills</h1>

  <p><strong>Agent skills for [Membrane](https://getmembrane.com) — reusable capabilities that let AI coding agents connect to external apps and perform actions.</strong></p>

<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://agentskills.io/"><img src="https://img.shields.io/badge/Agent_Skills-compatible-green.svg" alt="Agent Skills"></a>

</div>

<br>
Built on the open [Agent Skills](https://agentskills.io/) specification. Works with Claude Code, OpenClaw, Cursor, GitHub Copilot, Gemini CLI, and other compatible agents.

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

| Skill                                                      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [integrate-anything](skills/integrate-anything/)           | Connects agent to any external app on behalf of the user and lets it take any actions inside those apps                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| [integration-development](skills/integration-development/) | Use this skill when writing code that reads, writes, syncs, or reacts to data in an external app. Applies to SaaS products, internal tools, scripts, batch jobs, and CLIs. The skill uses Membrane as the integration engine — it handles OAuth and credential lifecycle (authentication, token refresh, reconnect), exposes vendor operations through a uniform interface, delivers events via webhooks, generates connectors on demand for apps not yet in the workspace, and captures every action run and raw API exchange in structured logs. Works against any external app. |

## Setup

All skills require a Membrane API token:

1. Sign up at [getmembrane.com](https://getmembrane.com)
2. Get your API token from the [dashboard](https://console.getmembrane.com)
3. Set the environment variable:
   ```bash
   export MEMBRANE_TOKEN="your-token-here"
   ```

Optionally set a custom API URL (defaults to `https://api.getmembrane.com`):

```bash
export MEMBRANE_API_URL="https://your-instance.example.com"
```

## Custom Agent Tools

If you're building a custom agent and need Membrane tools embedded directly in your code, see [`agents/`](agents). Each subdirectory contains a ready-to-run agent example with the framework adapter:

| Agent                                  | Framework       |
| -------------------------------------- | --------------- |
| [openai](agents/openai/)               | OpenAI SDK      |
| [vercel-ai-sdk](agents/vercel-ai-sdk/) | Vercel AI SDK   |
| [langchain](agents/langchain/)         | LangChain       |
| [opencode](agents/opencode/)           | OpenCode Plugin |

Tool definitions live in [`tools/integrate-anything.ts`](tools/integrate-anything.ts).

## License

MIT