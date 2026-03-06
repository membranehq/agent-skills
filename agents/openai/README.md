# OpenAI SDK Agent

Use [Membrane](https://getmembrane.com) tools with the OpenAI SDK.

## Setup

```bash
cd agents/openai
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

This runs a minimal agent loop that sends "List my connections" to GPT-4o with Membrane tools, executes any tool calls, and prints the final response.

## Customize

- **Swap the model** — change `"gpt-4o"` in `example.ts` to any OpenAI model.
- **Use a subset of tools** — pass an array to `toOpenAITools()`:
  ```typescript
  import { listConnections, searchTools, runTool } from '../../tools/integrate-anything'
  const tools = toOpenAITools([listConnections, searchTools, runTool])
  ```
- **Change the prompt** — edit the initial `messages` array in `example.ts`.

## Files

| File         | Description                                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------------------------- |
| `adapter.ts` | `toOpenAITools()` and `createToolExecutor()` — converts Membrane tool definitions to OpenAI function-calling format |
| `example.ts` | Runnable chat completion loop with tool execution                                                                   |