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

## Running `membrane`

`membrane` is the plugin's own command, the file `scripts/membrane` of the plugin. Run it by its full path, because it is not on the PATH. From this skill's folder the path is `../../scripts/membrane`, so `membrane catalog` means `<this skill's folder>/../../scripts/membrane catalog`. In Claude Code the same file is also `${CLAUDE_PLUGIN_ROOT}/scripts/membrane`.

In Codex, run every `membrane` command outside the sandbox: request escalated permissions for it. The command needs the network to reach Membrane, and it writes the sign-in and its cache under `~/.membrane`. The sandbox blocks both. The person approves the command once, and can approve the `membrane` command for the later calls.

Every command except `membrane catalog` needs a sign-in. `membrane whoami` says whether this computer is signed in. With no sign-in, run `membrane login` first.

## What Membrane offers, and what it costs

`membrane catalog` prints the jobs Membrane offers, read from Membrane's public catalog: each job's title, what it does, its category, whether it can be bought now, the page it is sold on, and each deliverable with its prices exactly as the catalog states them. Run it when the person asks what Membrane does or what a job costs, and answer from its output. Quote a price only as the catalog states it, and give the person the job's page.

## What this plugin does, and does not do

This plugin signs this computer in to Membrane, runs Membrane commands on that sign-in, and connects the person's apps on their own computer. This version ships no tool that reads a connected app.

`membrane login` signs this computer in to the person's Membrane account. It opens Membrane's consent page in the browser and waits for the approval. The person picks the workspaces this computer may open on that page, and Membrane lists the sign-in under AI agents, as Membrane CLI. If `membrane login` exits 3, the person has not approved yet: ask them to approve, then run it again. `membrane whoami` says who is signed in and which workspaces the sign-in may open. `membrane logout` revokes the sign-in and deletes it from this computer.

Membrane gives each signed-in person the agent guides their role may read. The session hook caches them under `~/.membrane/guides/`, and `membrane guide <id>` prints one: its path, the other files beside it, and its text.

`membrane connect <key>` starts the sign-in to a provider, and `membrane connections` lists what this computer is connected to.

What stays here: the Membrane sign-in, in `~/.membrane/sign-in.json`; the cached guides, in `~/.membrane/guides/`; the workspace of a joined handoff, in `~/.membrane/handoff.json`; and each provider's access token and refresh token, in `~/.membrane/connections/`. Never read or print `sign-in.json` or a connection file.

What leaves, to `api.membrane.agency`: the Membrane sign-in, the refresh of its token, the list and text of the person's guides, the list of the person's commands, and each command your agent runs with `membrane run` or `membrane handoff`, with its input.

What leaves, to `auth.membrane.agency`: a provider sign-in, so the provider's client secret never sits on this computer; the refresh of an expired provider token; a version check once a day that sends the plugin version and nothing else; and a read of Membrane's public jobs catalog when `membrane catalog` runs, which sends nothing. Membrane counts how many installs make the version check each day and keeps no address.

The scripts upload nothing else.

## Membrane commands

`membrane commands [filter]` lists the commands this sign-in may run: each command's name, scope, route, and the first sentence of what it does. The filter keeps the names that hold it, such as `membrane commands intake`. `membrane run <command> --schema` prints the input a command takes, as JSON Schema. `membrane run <command> --input '<json>'` runs the command and prints Membrane's answer as JSON. `--input-file <path>` reads the input from a file, and `--stdin` reads it from stdin.

Through these commands you read and answer the person's requests, search their knowledge, query their data tables, and use their connections and actions. Run `membrane guide overview` first: it describes Membrane's entities and how they fit together.

A command whose scope is `workspace` runs in one workspace. Pass `--workspace <key>`; `membrane whoami` lists the workspaces this computer may open, which are the workspaces the person can open. During a handoff, a workspace command runs in the workspace the handoff started in by default. Membrane checks each call against what the person may do. When it refuses a call, `membrane run` exits 1 and prints Membrane's reason.

When a command exits 3 with `not-signed-in` or `sign-in-ended`, run `membrane login`. When it exits 3 with `workspace-not-granted`, the person cannot open that workspace: check the key with `membrane whoami`. A person with no Membrane account gets one when they start a job.

### Filling a request

When you fill one of the person's requests (an intake), answer only from a real source, with `membrane run answer-intake-ask`. Say which questions you skipped and why. Submit with `done: true` only after the person agrees.

### When Membrane cannot do a step

When Membrane itself lacks what a step needs, send one record: `membrane run send-feedback --workspace <key> --input '{"message": "<what you tried, and what stopped you>"}'`. Send it when no command, field or connector does the step, a command fails like a bug in Membrane, or Membrane's docs are wrong about the product. Do not send it when the person can close the gap. Ask them for access the sign-in lacks, and offer to connect an app that is missing. Do not send it instead of trying: read `membrane guide overview` first. After you send it, tell the person plainly what could not be done. Never promise that Membrane will build it, or when.

## Handing the work over

When the person wants Membrane to do a job, give them the job's page from `membrane catalog`. They start the job there, and they get a Membrane account when they start it. After that, `membrane run` reaches their workspace once the person ticks it for this computer: at `membrane login`, or later in their Membrane account, under AI agents.

Never promise a result, a percentage, or a date that Membrane has not stated.

## When the plugin's scripts are not there

This skill travels further than the script. A web-only session — ChatGPT in the browser — gets these instructions and no `membrane` command. This section applies only when the file `../../scripts/membrane` is missing from this skill's folder. A `membrane` that the shell does not find on the PATH is not missing: run it by its full path. When the file is missing, say so plainly, point the person to https://membrane.agency/jobs for the catalog, and tell them how to get the plugin:

- **Codex CLI:** `codex plugin marketplace add membranehq/agent-skills`, then `codex plugin add membrane@membrane`.
- **Claude Code:** `/plugin marketplace add membranehq/agent-skills`, then `/plugin install membrane@membrane`.

The sign-in to a provider keeps its tokens on the person's own computer, so it runs where their files are. Do not try to work around a missing script.