# E-commerce back-office skills for your AI agent

Free skills for the back-office work of an e-commerce brand, from Membrane. Your agent runs them on your computer, with no sign-up, and your data stays there. The first skill works on Amazon Ads.

<table>
<tr>
<td width="50%" valign="top">

<img src="assets/claude.svg" width="48" height="48" alt="Claude">

### Claude Code

For the Claude Code CLI and the Claude desktop app. Type these in Claude Code:

```
/plugin marketplace add membranehq/agent-skills
/plugin install membrane@membrane
```

</td>
<td width="50%" valign="top">

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/codex-dark.svg"><img src="assets/codex.svg" width="48" height="48" alt="Codex"></picture>

### Codex

For the Codex CLI and the ChatGPT desktop app. Run these in a terminal:

```
codex plugin marketplace add membranehq/agent-skills
codex plugin add membrane@membrane
```

In Codex or the ChatGPT desktop app, open Settings → Hooks once after installing and turn on the `membrane` hook. Without it the skills still work, but your agent starts without the short guide to them.

</td>
</tr>
</table>

<details>
<summary>Other ways to install</summary>

**Claude Code, from a terminal.** The same install without opening Claude Code.

```
claude plugin marketplace add membranehq/agent-skills
claude plugin install membrane@membrane
```

**The Claude desktop app.** Its Code tab uses the plugins Claude Code installed on this computer. Install with either set of Claude Code commands, then start a new session in the app.

**The ChatGPT desktop app, without a terminal.** Open Settings → Plugins → Add → Add a marketplace, and enter `membranehq/agent-skills`. Open Membrane on the Plugins page and install it. Then turn on its hook under Settings → Hooks.

</details>

## Free and without sign-up

- **Free.** Every skill here is free to use, under the MIT license.
- **No sign-up.** You make no Membrane account and give no email. You sign in only to the app a skill works on, such as Amazon Ads. That sign-in goes through Membrane's sign-in page, so the app's client secret never sits on your machine.
- **Your data stays on your computer.** The skills read your data from the app's API directly and store the tokens and the data under `~/.membrane/`. They upload nothing.

## Skills

### Amazon Ads

Audits 60 days of your Sponsored Products ads for spend with no orders, unused budgets, and duplicate or loose targeting, and states what the ads cost, earned, and changed in a month. More on the skill: https://membrane.agency/agent-skills/amazon-ads

**Run the audit.** Ask your agent to audit your Amazon ads and it follows the steps. These are the commands behind them. The plugin ships two scripts: `membrane` signs you in to Amazon, and `amazon-ads` runs the audit.

- `membrane connect amazon-advertising` — opens Amazon's consent page, then stores the token on your computer.
- `amazon-ads profiles` — lists the advertising profiles on the account.
- `amazon-ads pull --profile <id>` — mirrors the account structure and starts five Sponsored Products reports over 60 days.
- `amazon-ads status --profile <id>` — says which of those reports Amazon has finished.
- `amazon-ads audit --profile <id>` — runs the rules over the pulled data.
- `amazon-ads report --profile <id>` — writes an HTML report and prints its path.

Amazon can take 20 minutes or more to produce a report, so the pull returns at once and `amazon-ads status` tells you when the data is in.

`amazon-ads audit --demo` runs the whole audit on sample data with no Amazon connection, so you can read the output before you connect anything.

**What the audit finds.** On the ads data alone: spend with no orders, campaigns with no impression, budgets set above what a campaign spends, dormant budgets in paused campaigns, brand terms in broad match, one keyword enabled in two ad groups, two ad groups on one product and target, off-Amazon placements, and every rate with its grade.

Some rules need to know what a unit earns you. Pass a CSV with the columns `asin,contributionPerUnit,source,windowStart,windowEnd` to `--unit-costs`, and the audit also prices bids, budget moves, harvests of converting search terms, top-of-search adjustments, and campaign decisions. Without that file it names each of those rules as skipped. It never guesses a unit cost, and it never states a profit it cannot compute.

**Where its data lives.**

- `~/.membrane/connections/amazon-advertising.json` — your Amazon access token and refresh token, readable only by you.
- `~/.membrane/amazon-ads/audits/<profileId>.sqlite` — the campaign, keyword, search-term and placement data the pull fetched.
- `~/.membrane/amazon-ads/reports/` — the HTML reports.

**Hand the work over.** When the audit finds work worth doing, `amazon-ads report` prints a link to Membrane's Amazon Ads job and the path of the findings file to share. Membrane works under a grant you give in Seller Central and end whenever you want, and a named operator is accountable for the result. The service and its prices are at https://membrane.agency/amazon.

## Requirements

Node 22.13 or newer. The skills store their data in the SQLite built into Node, so there is nothing to compile and nothing else to install.

## FAQ

<details>
<summary>What does the plugin send to Membrane?</summary>

Four kinds of request, all to `auth.membrane.agency`: the sign-in, the refresh of an expired token, one version check a day, and a read of Membrane's public list of jobs when you ask what Membrane offers. The version check sends the plugin version and nothing else, and asks whether this plugin is old enough to be worth updating. If it is, the agent says so once and carries on.

</details>

<details>
<summary>Does Membrane count who uses the plugin?</summary>

Membrane counts how many installs make the version check each day and keeps no address. Set `MEMBRANE_NO_UPDATE_CHECK=1` to switch the check off.

</details>

## About Membrane

Membrane runs the back office for e-commerce brands. AI agents do the around-the-clock work on the tools a brand already uses, and a named expert makes the calls and answers for the result. The jobs and their prices are at https://membrane.agency/jobs.

This repository holds the built plugin. Membrane builds it from source and replaces this tree on every release.

## License

MIT — see [LICENSE](LICENSE).
