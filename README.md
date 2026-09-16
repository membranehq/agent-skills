# Membrane for Amazon Ads

Audit your Amazon Ads account on your own computer. The plugin connects your advertising account, pulls the last 60 days of Sponsored Products data into a local database, and tells you what the ads are wasting and what they are missing. It runs in Claude Code, Codex CLI, and the ChatGPT desktop app.

Membrane runs Amazon accounts for brands. The audit is where a brand starts: it runs on your machine, it needs no Membrane account, and it shows you the work before you decide who does it.

This repository holds the built plugin. Membrane builds it from source and replaces this tree on every release.

## Install

Claude Code:

```
/plugin marketplace add membranehq/agent-skills
/plugin install membrane@membrane
```

Codex CLI:

```
codex plugin marketplace add membranehq/agent-skills
codex plugin add membrane@membrane
```

## Run the audit

Ask your agent to audit your Amazon ads and it follows the steps. These are the commands behind them:

- `membrane connect amazon-advertising` — opens Amazon's consent page, then stores the token on your computer.
- `membrane ads profiles` — lists the advertising profiles on the account.
- `membrane ads pull --profile <id>` — mirrors the account structure and starts five Sponsored Products reports over 60 days.
- `membrane ads status --profile <id>` — says which of those reports Amazon has finished.
- `membrane ads audit --profile <id>` — runs the rules over the pulled data.
- `membrane ads report --profile <id>` — writes an HTML report and prints its path.

Amazon can take 20 minutes or more to produce a report, so the pull returns at once and `membrane ads status` tells you when the data is in.

`membrane ads audit --demo` runs the whole audit on sample data with no Amazon connection, so you can read the output before you connect anything.

## What the audit finds

On the ads data alone: spend with no orders, campaigns with no impression, budgets set above what a campaign spends, dormant budgets in paused campaigns, brand terms in broad match, one keyword enabled in two ad groups, two ad groups on one product and target, off-Amazon placements, and every rate with its grade.

Some rules need to know what a unit earns you. Pass a CSV with the columns `asin,contributionPerUnit,source,windowStart,windowEnd` to `--unit-costs`, and the audit also prices bids, budget moves, harvests of converting search terms, top-of-search adjustments, and campaign decisions. Without that file it names each of those rules as skipped. It never guesses a unit cost, and it never states a profit it cannot compute.

## Where your data lives

Everything the audit reads and writes stays on your computer:

- `~/.membrane/connections/amazon-advertising.json` — your Amazon access token and refresh token, readable only by you.
- `~/.membrane/audits/<profileId>.sqlite` — the campaign, keyword, search-term and placement data the pull fetched.
- `~/.membrane/reports/` — the HTML reports.

The pull reads your data from Amazon's advertising API directly. Three requests go to Membrane, all to `auth.membrane.agency`: the Amazon sign-in, which goes through Membrane's auth proxy so Amazon's client secret never sits on your machine, the refresh of an expired Amazon token, and a version check once a day that sends nothing about you or your account and asks one question — whether this plugin is old enough to be worth updating. If it is, the agent says so once and carries on; nothing stops working. Set `MEMBRANE_NO_UPDATE_CHECK=1` to switch that check off. The plugin uploads no advertising data, and this version signs in to no Membrane account.

## Requirements

Node 22.13 or newer. The audit database uses the SQLite built into Node, so there is nothing to compile and nothing else to install.

## Hand the work over

When the audit finds work worth doing, `membrane ads report` prints a link to Membrane's Amazon Ads job and the path of the findings file to share. Membrane works under a grant you give in Seller Central and end whenever you want, and a named operator is accountable for the result. The service and its prices are at https://membrane.agency/amazon.

## License

MIT — see [LICENSE](LICENSE).
