import { DynamicStructuredTool } from '@langchain/core/tools'

import { type ToolDefinition, type MembraneConfig, allTools } from '../../tools/integrate-anything'

export function toLangChainTools(config: MembraneConfig, tools: ToolDefinition[] = allTools): DynamicStructuredTool[] {
  return tools.map(
    (t) =>
      new DynamicStructuredTool({
        name: t.name,
        description: t.description,
        schema: t.parameters,
        func: (input) => t.execute(input, config).then(JSON.stringify),
      }),
  )
}
