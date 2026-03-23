import { z } from 'zod'

// ── Types ───────────────────────────────────────────────────────────────────

export interface MembraneConfig {
  apiKey: string
  apiUrl?: string
}

export interface ToolDefinition<TInput = any> {
  name: string
  description: string
  parameters: z.ZodObject<any>
  execute: (input: TInput, config: MembraneConfig) => Promise<unknown>
}

// ── Client ──────────────────────────────────────────────────────────────────

export class MembraneClient {
  private baseUrl: string
  private apiKey: string

  constructor(config: MembraneConfig) {
    this.baseUrl = (config.apiUrl ?? 'https://api.getmembrane.com').replace(/\/$/, '')
    this.apiKey = config.apiKey
  }

  async request(method: string, path: string, body?: unknown): Promise<any> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Membrane API error ${res.status}: ${text}`)
    }
    return res.json()
  }
}

// ── Helper ──────────────────────────────────────────────────────────────────

function defineTool<T extends z.ZodObject<any>>(def: {
  name: string
  description: string
  parameters: T
  execute: (input: z.infer<T>, config: MembraneConfig) => Promise<unknown>
}): ToolDefinition<z.infer<T>> {
  return def
}

// ── Tool Definitions ────────────────────────────────────────────────────────

export const listConnections = defineTool({
  name: 'list-connections',
  description: 'List all connections. A connection is an authenticated link to an external app (e.g. Slack, HubSpot).',
  parameters: z.object({}),
  execute: async (_input, config) => {
    const client = new MembraneClient(config)
    return client.request('GET', '/connections')
  },
})

export const searchConnectors = defineTool({
  name: 'search-connectors',
  description:
    'Search for available connectors by keyword. A connector is a pre-built adapter for an external app. Returns matching connectors that can be used to create connections.',
  parameters: z.object({
    q: z.string().min(1).max(200).describe('Search query'),
    limit: z.number().int().min(1).max(100).optional().describe('Max results'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    const params = new URLSearchParams({
      q: input.q,
      elementType: 'connector',
    })
    if (input.limit) params.set('limit', String(input.limit))
    return client.request('GET', `/search?${params}`)
  },
})

export const searchTools = defineTool({
  name: 'search-tools',
  description:
    'Search for actions (tools) available on a connection. Describe what you want to do in natural language.',
  parameters: z.object({
    connectionId: z.string().describe('Connection ID to search actions for'),
    intent: z.string().max(200).describe('Natural language description of what you want to do'),
    limit: z.number().int().min(1).max(100).optional().describe('Max results (default 10)'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    const params = new URLSearchParams({
      connectionId: input.connectionId,
      intent: input.intent,
    })
    if (input.limit) params.set('limit', String(input.limit))
    return client.request('GET', `/actions?${params}`)
  },
})

export const runTool = defineTool({
  name: 'run-tool',
  description: "Run an action on a connection. Provide input matching the action's inputSchema.",
  parameters: z.object({
    actionId: z.string().describe('Action ID to run'),
    connectionId: z.string().describe('Connection ID to run the action on'),
    input: z.record(z.string(), z.any()).optional().describe('Action input parameters'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    const params = new URLSearchParams({ connectionId: input.connectionId })
    return client.request('POST', `/actions/${input.actionId}/run?${params}`, {
      input: input.input ?? {},
    })
  },
})

export const ensureConnection = defineTool({
  name: 'ensure-connection',
  description:
    'Find or create a connection to an external app by its URL or domain. Provide the app\'s URL (e.g. "https://slack.com") or bare domain (e.g. "slack.com") — the domain is extracted and matched against known apps to find or create a connection.',
  parameters: z.object({
    appUrl: z.string().describe('URL or domain of the app to connect to (e.g. "https://slack.com", "hubspot.com")'),
    name: z.string().optional().describe('Custom connection name'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    return client.request('POST', '/connections/ensure', input)
  },
})

export const createConnection = defineTool({
  name: 'create-connection',
  description:
    "Create a new connection. Describe what app to connect to using intent (e.g. 'Connect to Slack'). Membrane will find or build the right connector automatically. Use get-connection with wait=true to poll until the connection is ready.",
  parameters: z.object({
    intent: z.string().describe("Natural language description of what to connect to (e.g. 'Connect to Slack')"),
    name: z.string().optional().describe('Custom connection name'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    return client.request('POST', '/connections', input)
  },
})

export const getConnection = defineTool({
  name: 'get-connection',
  description:
    'Get a connection by ID. Use wait=true to long-poll until the connection is no longer in BUILDING state. The response includes state and clientAction that tells you what to do next.',
  parameters: z.object({
    connectionId: z.string().describe('Connection ID'),
    wait: z.boolean().optional().describe('If true, long-poll until connection is no longer BUILDING'),
    timeout: z.number().int().min(1).max(60).optional().describe('Max wait in seconds (default 30)'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    const params = new URLSearchParams()
    if (input.wait !== undefined) params.set('wait', String(input.wait))
    if (input.timeout !== undefined) params.set('timeout', String(input.timeout))
    const qs = params.toString()
    return client.request('GET', `/connections/${input.connectionId}${qs ? `?${qs}` : ''}`)
  },
})

export const requestConnection = defineTool({
  name: 'request-connection',
  description:
    'Create a connection request so the user can authenticate with an external app. Returns a URL the user must open to complete authentication.',
  parameters: z.object({
    connectorId: z.string().optional().describe('Connector ID'),
    integrationId: z.string().optional().describe('Integration ID'),
    integrationKey: z.string().optional().describe('Integration key'),
    connectionId: z.string().optional().describe('Existing connection ID (for reconnecting)'),
    name: z.string().optional().describe('Custom connection name'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    return client.request('POST', '/connection-requests', input)
  },
})

export const checkConnectionResult = defineTool({
  name: 'check-connection-result',
  description: 'Check the status of a connection request. Poll until status is "success" or "error".',
  parameters: z.object({
    requestId: z.string().describe('Connection request ID'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    return client.request('GET', `/connection-requests/${input.requestId}`)
  },
})

export const createAction = defineTool({
  name: 'create-action',
  description:
    "Create a new action using intent. Describe what the action should do (e.g. 'send a message in a channel'). Membrane will build it automatically using an agent. Use get-action with wait=true to poll until the action is ready.",
  parameters: z.object({
    intent: z.string().describe("Natural language description of what the action should do (e.g. 'send a message')"),
    connectionId: z.string().describe('Connection ID to create the action for'),
    name: z.string().optional().describe('Custom action name'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    return client.request('POST', '/actions', input)
  },
})

export const getAction = defineTool({
  name: 'get-action',
  description:
    'Get an action by ID. Use wait=true to long-poll until the action is no longer in BUILDING state. The response includes state that tells you if the action is ready.',
  parameters: z.object({
    actionId: z.string().describe('Action ID'),
    wait: z.boolean().optional().describe('If true, long-poll until action is no longer BUILDING'),
    timeout: z.number().int().min(1).max(60).optional().describe('Max wait in seconds (default 30)'),
  }),
  execute: async (input, config) => {
    const client = new MembraneClient(config)
    const params = new URLSearchParams()
    if (input.wait !== undefined) params.set('wait', String(input.wait))
    if (input.timeout !== undefined) params.set('timeout', String(input.timeout))
    const qs = params.toString()
    return client.request('GET', `/actions/${input.actionId}${qs ? `?${qs}` : ''}`)
  },
})

// ── All Tools ───────────────────────────────────────────────────────────────

export const allTools: ToolDefinition[] = [
  listConnections,
  ensureConnection,
  searchConnectors,
  searchTools,
  runTool,
  createConnection,
  getConnection,
  requestConnection,
  checkConnectionResult,
  createAction,
  getAction,
]
