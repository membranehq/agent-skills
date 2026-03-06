import { tool } from '@opencode-ai/plugin'

import { assert, assertContains, summary } from '../../tests/shared/assert.mjs'
import { MOCK_CONFIG, EXPECTED_TOOL_COUNT } from '../../tests/shared/constants.mjs'
import { type ToolDefinition, type MembraneConfig, allTools } from '../../tools/integrate-anything'

console.log('=== OpenCode Adapter Test ===\n')

// Inline the adapter logic (same as .opencode/plugin/membrane.ts)
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

// ── Test 1: Tool visibility ────────────────────────────────────────────────

console.log('Test 1: Tool visibility')

const tools = toOpenCodeTools(MOCK_CONFIG)
const toolNames = Object.keys(tools)

assert(toolNames.length === EXPECTED_TOOL_COUNT, `Should have ${EXPECTED_TOOL_COUNT} tools (got ${toolNames.length})`)
assertContains(toolNames.join(', '), 'list-connections', 'Tools include list-connections')
assertContains(toolNames.join(', '), 'search-connectors', 'Tools include search-connectors')
assertContains(toolNames.join(', '), 'run-tool', 'Tools include run-tool')

for (const name of toolNames) {
  const t = tools[name]
  assert(typeof t === 'object' && t !== null, `${name} is a valid tool object`)
}

// ── Test 2: Tool execution ─────────────────────────────────────────────────

console.log('\nTest 2: Tool execution')

{
  const listTool = allTools.find((t) => t.name === 'list-connections')!
  const result = await listTool.execute({}, MOCK_CONFIG)
  const text = JSON.stringify(result)

  assert(text.length > 0, 'list-connections returned a response')
  assertContains(text, 'Slack', 'Response mentions Slack connection')
  assertContains(text, 'HubSpot', 'Response mentions HubSpot connection')
}

summary('OpenCode Adapter')
