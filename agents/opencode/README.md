# OpenCode Plugin

Use [Membrane](https://getmembrane.com) tools as an [OpenCode](https://opencode.ai/) plugin.

## Setup

1. Copy the `agents/opencode/` directory (or its `.opencode/` subdirectory) into your project root:

```bash
cp -r agents/opencode/.opencode /path/to/your-project/.opencode
```

2. Install plugin dependencies:

```bash
cd /path/to/your-project/.opencode
npm install
```

3. Set your API key:

```bash
export MEMBRANE_TOKEN="your-membrane-token"
```

## Run

Start OpenCode from your project directory — the plugin loads automatically:

```bash
opencode
```

The Membrane tools will appear in OpenCode's tool list.

## Customize

Edit `.opencode/plugin/membrane.ts` to change which tools are available:

```typescript
import { listConnections, searchTools, runTool } from '../../../../tools/integrate-anything'

export const MembranePlugin: Plugin = async () => ({
  tool: toOpenCodeTools({ apiKey: process.env.MEMBRANE_TOKEN! }, [listConnections, searchTools, runTool]),
})
```

## Files

| File                           | Description                                            |
| ------------------------------ | ------------------------------------------------------ |
| `.opencode/plugin/membrane.ts` | OpenCode plugin entry point — registers Membrane tools |
| `.opencode/package.json`       | Plugin dependencies                                    |