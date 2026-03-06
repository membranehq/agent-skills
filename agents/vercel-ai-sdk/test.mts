import { openai } from '@ai-sdk/openai'
import { generateText } from 'ai'

import { assert, assertContains, summary } from '../../tests/shared/assert.mjs'
import { MOCK_CONFIG, EXPECTED_TOOL_COUNT } from '../../tests/shared/constants.mjs'
import { toVercelTools } from './integrate-anything-tools'

console.log('=== Vercel AI SDK Adapter Test ===\n')

const tools = toVercelTools(MOCK_CONFIG)

// ── Test 1: Tool visibility ────────────────────────────────────────────────

console.log('Test 1: Tool visibility')

const toolNames = Object.keys(tools)
assert(toolNames.length === EXPECTED_TOOL_COUNT, `Should have ${EXPECTED_TOOL_COUNT} tools (got ${toolNames.length})`)
assertContains(toolNames.join(', '), 'list-connections', 'Tools include list-connections')
assertContains(toolNames.join(', '), 'search-connectors', 'Tools include search-connectors')
assertContains(toolNames.join(', '), 'run-tool', 'Tools include run-tool')

{
  const { text } = await generateText({
    model: openai('gpt-4o-mini'),
    tools,
    maxSteps: 3,
    prompt: 'What Membrane tools do you have? List all tool names. Do not call any tools, just list their names.',
  })

  assertContains(text, 'list-connections', 'LLM response mentions list-connections')
  assertContains(text, 'search-connectors', 'LLM response mentions search-connectors')
}

// ── Test 2: Tool execution ─────────────────────────────────────────────────

console.log('\nTest 2: Tool execution')

{
  const { text } = await generateText({
    model: openai('gpt-4o-mini'),
    tools,
    maxSteps: 10,
    prompt: 'List my connections using the list-connections tool.',
  })

  assert(text.length > 0, 'LLM produced a final response')
  assertContains(text, 'Slack', 'Response mentions Slack connection')
  assertContains(text, 'HubSpot', 'Response mentions HubSpot connection')
}

summary('Vercel AI SDK Adapter')
