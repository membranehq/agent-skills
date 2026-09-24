---
name: membrane
description: What Membrane is, what this plugin does and does not do, and how to hand the work the audit found to Membrane. Use when the person asks who Membrane is, what Membrane would do for their Amazon account, how the sign-in works, what leaves their computer, or what to do with the findings the audit produced.
metadata:
  summary: 'What Membrane is, what its jobs cost, and how to hand over the work a tool found.'
---

# Membrane

Membrane runs Amazon accounts for brands. A named operator is accountable for the result, and agents do the volume of the work. Membrane is a registered Amazon solution provider with a published Selling Partner app. The service and its prices are at https://membrane.agency/amazon.

Nine sub-jobs cover the account. A brand buys the whole service or one sub-job at a time, and each sub-job is priced by its own deliverables. Read the prices on the service page rather than quoting a number from memory.

Membrane works inside a grant the brand gives in Seller Central. Under that grant the work covers catalog and listings, inventory and FBA, advertising and promotions, reports and account health, Seller Support cases and experiments, and buyer messages. The brand chooses what the grant covers and ends it in Seller Central whenever they want. Anything irreversible waits for the brand's approval.

## What this plugin does, and does not do

This plugin audits an Amazon Ads account on the person's own computer. It connects Amazon, pulls the data, and writes two kinds of report from it. The audit says what the ads waste and what they miss; the `amazon-ads` skill has its steps. The Ads Statement says what the ads cost and earned in one period, what changed on the account, and what to ask whoever runs the ads; the `ads-statement` skill has its steps.

What stays here: the Amazon access token and refresh token in `~/.membrane/connections/`, the pulled Sponsored Products data in `~/.membrane/amazon-ads/audits/`, and the reports in `~/.membrane/amazon-ads/reports/`.

What leaves: the Amazon sign-in, which goes through `auth.membrane.agency` so Amazon's client secret never sits on this computer, the refresh of an expired Amazon token through the same host, a version check once a day to the same host that sends nothing about the person or the account, and a read of Membrane's public jobs catalog from the same host when `membrane catalog` runs, which sends nothing either. Nothing else.

This version has no Membrane sign-in and no Membrane account. It cannot read Membrane work, and it uploads nothing. If the person asks to see their Membrane inbox, jobs, or receipts from the terminal, say that this version does not do it and point them to https://membrane.agency.

## Handing the work over

`amazon-ads report --profile <profileId>` prints two things that matter for the hand-over:

- `offerUrl` — the link that opens Membrane's Amazon Ads job. Give the person the link.
- `findingsPath` — the file on this computer holding every finding the audit produced.

Tell the person to share the findings file with Membrane when they start the job. This version has no upload, so the file travels the way they choose. They do not need a Membrane account to run the audit; they get one when they start the job.

State what the audit found and what it costs them today, in their own numbers. Never promise a result, a percentage, or a date that Membrane has not stated.

## When the plugin's scripts are not there

The skills travel further than the scripts. A web-only session — ChatGPT in the browser — gets these instructions and no `membrane` or `amazon-ads` command. When the scripts are missing, say so plainly and tell the person how to get them:

- **Codex CLI:** `codex plugin marketplace add membranehq/agent-skills`, then `codex plugin add membrane@membrane`.
- **Claude Code:** `/plugin marketplace add membranehq/agent-skills`, then `/plugin install membrane@membrane`.

The audit reads the person's own Amazon account and writes files on their own computer, so it runs where their files are. Do not try to work around a missing script.