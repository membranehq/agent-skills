# LangChain Agent

Use [Membrane](https://getmembrane.com) tools with [LangChain](https://js.langchain.com/).

## Setup

```bash
cd agents/langchain
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

This creates an `AgentExecutor` with a tool-calling agent, sends "List my connections", and prints the result.

## Customize

- **Swap the model** — replace `ChatOpenAI` with any LangChain chat model (e.g. `ChatAnthropic`).
- **Use a subset of tools** — pass an array to `toLangChainTools()`:
  ```typescript
  import { listConnections, searchTools, runTool } from '../../tools/integrate-anything'
  const tools = toLangChainTools(config, [listConnections, searchTools, runTool])
  ```
- **Change the system prompt** — edit the `ChatPromptTemplate` in `example.ts`.

## Files

| File         | Description                                                                                              |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| `adapter.ts` | `toLangChainTools()` — converts Membrane tool definitions to LangChain `DynamicStructuredTool` instances |
| `example.ts` | Runnable agent executor example                                                                          |