# Vercel AI SDK Agent

Use [Membrane](https://getmembrane.com) tools with the [Vercel AI SDK](https://sdk.vercel.ai/).

## Setup

```bash
cd agents/vercel-ai-sdk
npm install
```

Set your API keys:

```bash
export MEMBRANE_TOKEN="your-membrane-token"
export OPENAI_API_KEY="your-openai-key"
```

## Run

```bash
npx tsx example.ts
```

This calls `generateText()` with Membrane tools and `maxSteps: 10`, letting the model autonomously call tools and return a final answer.

## Customize

- **Swap the model** — replace `openai("gpt-4o")` with any Vercel AI SDK provider (e.g. `anthropic("claude-sonnet-4-20250514")`).
- **Use a subset of tools** — pass an array to `toVercelTools()`:
  ```typescript
  import { listConnections, searchTools, runTool } from '../../tools/integrate-anything'
  const tools = toVercelTools(config, [listConnections, searchTools, runTool])
  ```
- **Streaming** — replace `generateText` with `streamText` for streaming responses.

## Files

| File         | Description                                                                         |
| ------------ | ----------------------------------------------------------------------------------- |
| `adapter.ts` | `toVercelTools()` — converts Membrane tool definitions to Vercel AI SDK tool format |
| `example.ts` | Runnable example using `generateText()` with multi-step tool use                    |