---
name: membrane
description: What Membrane is, what its jobs cost, what this plugin does and does not do, and how to hand work over to Membrane. Use when the person asks who Membrane is, what Membrane would do for their business or their Amazon account, what a job costs, how the sign-in works, or what leaves their computer.
metadata:
  summary: 'What Membrane is, what its jobs cost, and how to hand work over to Membrane.'
---

# Membrane

There is a right way to run your operations. Membrane finds it and runs it. AI agents do the around-the-clock work on the tools a company already uses, and a named operator makes the calls and answers for the result. The jobs and their prices are at https://membrane.agency/jobs.

On Amazon, Membrane is a registered Amazon solution provider with a published Selling Partner app. The Amazon service and its prices are at https://membrane.agency/amazon.

Nine sub-jobs cover an Amazon account. A company buys the whole service or one sub-job at a time, and each sub-job is priced by its own deliverables. Read the prices on the service page rather than quoting a number from memory.

Membrane works inside a grant the seller gives in Seller Central. Under that grant the work covers catalog and listings, inventory and FBA, advertising and promotions, reports and account health, Seller Support cases and experiments, and buyer messages. The seller chooses what the grant covers and ends it in Seller Central whenever they want. Anything irreversible waits for the seller's approval.

## What Membrane offers, and what it costs

`membrane catalog` prints the jobs Membrane offers, read from Membrane's public catalog: each job's title, what it does, its category, whether it can be bought now, the page it is sold on, and each deliverable with its prices exactly as the catalog states them. Run it when the person asks what Membrane does or what a job costs, and answer from its output. Quote a price only as the catalog states it, and give the person the job's page.

## What this plugin does, and does not do

This plugin connects the person's apps on their own computer. `membrane connect <key>` starts the sign-in to a provider and `membrane connections` lists what this computer is connected to. This version ships no tool that reads a connected app.

What stays here: each provider's access token and refresh token, in `~/.membrane/connections/`.

What leaves: a provider sign-in, which goes through `auth.membrane.agency` so the provider's client secret never sits on this computer, the refresh of an expired token through the same host, a version check once a day to the same host that sends the plugin version and nothing else, and a read of Membrane's public jobs catalog from the same host when `membrane catalog` runs, which sends nothing. Nothing else. Membrane counts how many installs make the version check each day and keeps no address.

The scripts have no Membrane sign-in and upload nothing.

## The Membrane server

The plugin also adds the Membrane MCP server, at `https://api.membrane.agency/mcp`. The person signs in to Membrane the first time it is used and picks the workspaces it may open. Through it you read and answer the person's requests, search their knowledge, query their data tables, and use their connections and actions. Call its `overview` tool first: it is the guide to the other tools.

When the server's tools are missing, the person has not signed in yet. In Claude Code, ask them to run `/mcp`, pick the Membrane server, and sign in. In Codex, ask them to run `codex mcp login membrane` in a terminal. A person with no Membrane account gets one when they start a job. The server shows no inbox, jobs, or receipts; for those, point the person to https://membrane.agency.

## Handing the work over

When the person wants Membrane to do a job, give them the job's page from `membrane catalog`. They start the job there, and they get a Membrane account when they start it. After that, the Membrane server reaches their workspace.

Never promise a result, a percentage, or a date that Membrane has not stated.

## When the plugin's scripts are not there

This skill travels further than the script. A web-only session — ChatGPT in the browser — gets these instructions and no `membrane` command. When the script is missing, say so plainly, point the person to https://membrane.agency/jobs for the catalog, and tell them how to get the plugin:

- **Codex CLI:** `codex plugin marketplace add membranehq/agent-skills`, then `codex plugin add membrane@membrane`.
- **Claude Code:** `/plugin marketplace add membranehq/agent-skills`, then `/plugin install membrane@membrane`.

The sign-in to a provider keeps its tokens on the person's own computer, so it runs where their files are. Do not try to work around a missing script.