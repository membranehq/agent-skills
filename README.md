# Membrane Agent Skills

Agent skills for [Membrane](https://getmembrane.com) — reusable capabilities that let AI coding agents connect to external apps and perform actions.

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

| Skill                                                            | Description                                                                                                  |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [integrate-anything](skills/integrate-anything/)                 | Connects agent to any external app on behalf of the user and lets it take any actions inside those apps      |
| [build-product-integrations](skills/build-product-integrations/) | Build apps that integrate with external services — connection UI, running actions, data sync, AI agent tools |

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