import { tool } from 'ai'

import { type ToolDefinition, type MembraneConfig, allTools } from '../../tools/integrate-anything'

export function toVercelTools(
  config: MembraneConfig,
  tools: ToolDefinition[] = allTools,
): Record<string, ReturnType<typeof tool>> {
  return Object.fromEntries(
    tools.map((t) => [
      t.name,
      tool({
        description: t.description,
        parameters: t.parameters,
        execute: (input) => t.execute(input, config),
      }),
    ]),
  )
}
