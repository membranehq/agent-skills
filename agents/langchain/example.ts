import { ChatPromptTemplate } from '@langchain/core/prompts'
import { ChatOpenAI } from '@langchain/openai'
import { createToolCallingAgent, AgentExecutor } from 'langchain/agents'

import { toLangChainTools } from './integrate-anything-tools'

const config = { apiKey: process.env.MEMBRANE_TOKEN! }
const tools = toLangChainTools(config)
const llm = new ChatOpenAI({ model: 'gpt-4o' })

const prompt = ChatPromptTemplate.fromMessages([
  ['system', 'You are a helpful assistant with access to Membrane tools.'],
  ['human', '{input}'],
  ['placeholder', '{agent_scratchpad}'],
])

const agent = createToolCallingAgent({ llm, tools, prompt })
const executor = new AgentExecutor({ agent, tools })

const result = await executor.invoke({ input: 'List my connections' })
console.log(result.output)
