import { zodToJsonSchema } from 'zod-to-json-schema'

import { type ToolDefinition, type MembraneConfig, allTools } from '../../tools/integrate-anything'

export function toOpenAITools(tools: ToolDefinition[] = allTools) {
  return tools.map((t) => ({
    type: 'function' as const,
    function: {
      name: t.name,
      description: t.description,
      parameters: zodToJsonSchema(t.parameters, { target: 'openAi' }),
    },
  }))
}

export function createToolExecutor(config: MembraneConfig, tools: ToolDefinition[] = allTools) {
  const toolMap = new Map(tools.map((t) => [t.name, t]))

  return async (toolCall: { function: { name: string; arguments: string } }): Promise<string> => {
    const tool = toolMap.get(toolCall.function.name)
    if (!tool) throw new Error(`Unknown tool: ${toolCall.function.name}`)
    const input = JSON.parse(toolCall.function.arguments)
    const result = await tool.execute(input, config)
    return JSON.stringify(result)
  }
}
