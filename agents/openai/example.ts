import OpenAI from 'openai'

import { toOpenAITools, createToolExecutor } from './integrate-anything-tools'

const config = { apiKey: process.env.MEMBRANE_TOKEN! }
const openai = new OpenAI()
const tools = toOpenAITools()
const executeTool = createToolExecutor(config)

const messages: OpenAI.ChatCompletionMessageParam[] = [{ role: 'user', content: 'List my connections' }]

// Simple tool-calling loop
while (true) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
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

  console.log(choice.message.content)
  break
}
