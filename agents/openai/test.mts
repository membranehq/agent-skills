import OpenAI from 'openai'

import { assert, assertContains, summary } from '../../tests/shared/assert.mjs'
import { MOCK_CONFIG, EXPECTED_TOOL_COUNT } from '../../tests/shared/constants.mjs'
import { toOpenAITools, createToolExecutor } from './integrate-anything-tools'

console.log('=== OpenAI Adapter Test ===\n')

const openai = new OpenAI()
const tools = toOpenAITools()
const executeTool = createToolExecutor(MOCK_CONFIG)

// ── Test 1: Tool visibility ────────────────────────────────────────────────

console.log('Test 1: Tool visibility')

assert(tools.length === EXPECTED_TOOL_COUNT, `Should have ${EXPECTED_TOOL_COUNT} tools (got ${tools.length})`)

const toolNames = tools.map((t) => t.function.name)
assertContains(toolNames.join(', '), 'list-connections', 'Tools include list-connections')
assertContains(toolNames.join(', '), 'search-connectors', 'Tools include search-connectors')
assertContains(toolNames.join(', '), 'run-tool', 'Tools include run-tool')

{
  const messages: OpenAI.ChatCompletionMessageParam[] = [
    { role: 'user', content: 'What Membrane tools do you have? List all tool names.' },
  ]

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    tools,
    messages,
  })

  const content = response.choices[0].message.content || ''
  assertContains(content, 'list-connections', 'LLM response mentions list-connections')
  assertContains(content, 'search-connectors', 'LLM response mentions search-connectors')
}

// ── Test 2: Tool execution ─────────────────────────────────────────────────

console.log('\nTest 2: Tool execution')

{
  const messages: OpenAI.ChatCompletionMessageParam[] = [
    { role: 'user', content: 'List my connections using the list-connections tool.' },
  ]

  let iterations = 0
  let finalContent = ''

  while (iterations < 5) {
    iterations++
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      tools,
      messages,
    })

    const choice = response.choices[0]
    messages.push(choice.message)

    if (choice.finish_reason === 'tool_calls') {
      for (const call of choice.message.tool_calls ?? []) {
        const result = await executeTool(call)
        messages.push({ role: 'tool', tool_call_id: call.id, content: result })
      }
      continue
    }

    finalContent = choice.message.content || ''
    break
  }

  assert(finalContent.length > 0, 'LLM produced a final response')
  assertContains(finalContent, 'Slack', 'Response mentions Slack connection')
  assertContains(finalContent, 'HubSpot', 'Response mentions HubSpot connection')
}

summary('OpenAI Adapter')
