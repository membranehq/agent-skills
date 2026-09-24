---
name: amazon-ads
description: Audit an Amazon Ads account on this computer with the `amazon-ads` tool — connect Amazon through Membrane's auth proxy, pull 60 days of Sponsored Products data into a local SQLite file, run the audit, read the findings, and hand the work to Membrane. Use when the person asks to audit, review, or check their Amazon advertising, or asks what is wrong with their ads.
---

# Amazon Ads audit

You run the audit with the `amazon-ads` tool that ships with this plugin, and the Amazon sign-in with the `membrane` script beside it. Resolve them as `${CLAUDE_PLUGIN_ROOT}/scripts/amazon-ads` and `${CLAUDE_PLUGIN_ROOT}/scripts/membrane` in Claude Code, or beside this skill's installed path in Codex. Every command prints JSON on stdout and a one-line status on stderr. `amazon-ads` gets the Amazon token from `membrane` on its own; never run `membrane credentials` yourself.

The audit finds work on the ads data alone: spend with no orders, campaigns with no impression, budgets set above what a campaign spends, dormant budgets in paused campaigns, brand terms in broad match, one keyword enabled in two ad groups, off-Amazon placements, and every rate with its grade. With unit costs it also prices bids, budget moves, harvests of converting search terms, top-of-search adjustments, and campaign decisions; without them it names each of those rules as skipped. The audit never claims profit or loss. Profit needs unit costs, and the person supplies those in a CSV when they want the money rules to run.

Everything stays on this computer: `~/.membrane/connections/amazon-advertising.json` holds the Amazon credentials, `~/.membrane/amazon-ads/audits/<profileId>.sqlite` holds the pulled data, and `~/.membrane/amazon-ads/reports/` holds the reports. The only requests that leave the computer without the person's Amazon token are the sign-in through `auth.membrane.agency`, the refresh of an expired token through the same host, a once-a-day version check to the same host that carries nothing, and a read of Membrane's public jobs catalog from the same host when `membrane catalog` runs, which carries nothing either.

## Steps

1. **Connect.** Run `membrane connections`. If no `amazon-advertising` connection exists, run `membrane connect amazon-advertising`. Show the person the URL it prints and ask them to open it, sign in to Amazon, and allow access. The page then shows a short code. Ask for the code and run `membrane connect complete <code>`. The code works once and expires 15 minutes after the start.
2. **Choose the profile.** Run `amazon-ads profiles`. If the account has one profile, use it. If it has several, show the list (country, account name, profile id) and ask which one to audit.
3. **Pull.** Run `amazon-ads pull --profile <profileId>`. It mirrors the account structure, then starts the five Sponsored Products reports for each window it needs — one report may span 31 days, so the default 60 days is two windows and ten reports — and returns at once. Amazon can take 20 minutes or more to produce a report. Do not wait in a loop. Tell the person the pull is running and that you will check when they come back, or when they ask.
4. **Check.** Run `amazon-ads status --profile <profileId>`. It prints each report's state and the data window. When every report reads `done`, go on. If a report reads `failed`, print its error and run the pull again once.
5. **Audit.** Run `amazon-ads audit --profile <profileId>`. Add `--unit-costs <file.csv>` when the person gave unit costs (columns: `asin,contributionPerUnit,source,windowStart,windowEnd`). The command writes findings to the local database and prints a summary.
6. **Report.** Run `amazon-ads report --profile <profileId>`. It writes an HTML report and prints its path. Open it for the person or tell them the path. Then summarize in chat: the five findings with the most spend behind them, each with its number and its window.
7. **Hand over the work.** When the findings show work worth doing, offer to hand it to Membrane. The `amazon-ads report` output prints `offerUrl`: a link that opens the Amazon Ads job on membrane.agency. Give the person the link and the path of the findings file, and tell them to share the file with Membrane when they start the job; this version has no upload. This version of the plugin has no Membrane sign-in; the person continues on membrane.agency.

## Rules

- Never compute or state profit, margin, ROAS targets, or "what the account should spend". State what the data shows and the window it covers.
- Every number carries its window and its population, for example "14 of 61 campaigns, Jul 16 to Sep 13".
- A missing value is not zero. When a report has no row for a target, say the data is missing.
- Do not run `amazon-ads pull` twice for the same profile while a pull is running. Read `amazon-ads status` first.
- The audit does not read Amazon's change history. The pull and the status also read it, a page at a time, for the Ads Statement; the audit needs no `amazon-ads history`.
- `amazon-ads audit --demo` runs on bundled sample data with no Amazon connection. Use it only when the person asks to see what the audit looks like before connecting.
- Show the person every command you are about to run that changes their Amazon account. The audit changes nothing on Amazon; only Membrane's job does, and only after the person buys it.