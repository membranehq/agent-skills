import { type Plugin, tool } from '@opencode-ai/plugin'

import { type ToolDefinition, type MembraneConfig, allTools } from '../../../../tools/integrate-anything'

function toOpenCodeTools(
  config: MembraneConfig,
  tools: ToolDefinition[] = allTools,
): Record<string, ReturnType<typeof tool>> {
  return Object.fromEntries(
    tools.map((t) => [
      t.name,
      tool({
        description: t.description,
        args: t.parameters.shape,
        execute: (args) => t.execute(args, config).then((r) => JSON.stringify(r)),
      }),
    ]),
  )
}

export const MembranePlugin: Plugin = async () => ({
  tool: toOpenCodeTools({
    apiKey: process.env.MEMBRANE_TOKEN!,
    apiUrl: process.env.MEMBRANE_API_URL,
  }),
})
