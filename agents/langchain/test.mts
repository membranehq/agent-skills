import { ChatPromptTemplate } from '@langchain/core/prompts'
import { ChatOpenAI } from '@langchain/openai'
import { createToolCallingAgent, AgentExecutor } from 'langchain/agents'

import { assert, assertContains, summary } from '../../tests/shared/assert.mjs'
import { MOCK_CONFIG, EXPECTED_TOOL_COUNT } from '../../tests/shared/constants.mjs'
import { toLangChainTools } from './integrate-anything-tools'

console.log('=== LangChain Adapter Test ===\n')

const tools = toLangChainTools(MOCK_CONFIG)
const llm = new ChatOpenAI({ model: 'gpt-4o-mini' })

// ── Test 1: Tool visibility ────────────────────────────────────────────────

console.log('Test 1: Tool visibility')

assert(tools.length === EXPECTED_TOOL_COUNT, `Should have ${EXPECTED_TOOL_COUNT} tools (got ${tools.length})`)

const toolNames = tools.map((t) => t.name)
assertContains(toolNames.join(', '), 'list-connections', 'Tools include list-connections')
assertContains(toolNames.join(', '), 'search-connectors', 'Tools include search-connectors')
assertContains(toolNames.join(', '), 'run-tool', 'Tools include run-tool')

{
  const prompt = ChatPromptTemplate.fromMessages([
    ['system', 'You are a helpful assistant with access to Membrane tools.'],
    ['human', '{input}'],
    ['placeholder', '{agent_scratchpad}'],
  ])

  const agent = createToolCallingAgent({ llm, tools, prompt })
  const executor = new AgentExecutor({ agent, tools, maxIterations: 1 })

  const result = await executor.invoke({
    input: 'What Membrane tools do you have? List all tool names.',
  })

  assertContains(result.output, 'list-connections', 'LLM response mentions list-connections')
  assertContains(result.output, 'search-connectors', 'LLM response mentions search-connectors')
}

// ── Test 2: Tool execution ─────────────────────────────────────────────────

console.log('\nTest 2: Tool execution')

{
  const prompt = ChatPromptTemplate.fromMessages([
    ['system', 'You are a helpful assistant with access to Membrane tools.'],
    ['human', '{input}'],
    ['placeholder', '{agent_scratchpad}'],
  ])

  const agent = createToolCallingAgent({ llm, tools, prompt })
  const executor = new AgentExecutor({ agent, tools, maxIterations: 5 })

  const result = await executor.invoke({
    input: 'List my connections using the list-connections tool.',
  })

  assert(result.output.length > 0, 'LLM produced a final response')
  assertContains(result.output, 'Slack', 'Response mentions Slack connection')
  assertContains(result.output, 'HubSpot', 'Response mentions HubSpot connection')
}

summary('LangChain Adapter')
