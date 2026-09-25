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

| Skill | What it does |
| --- | --- |
| [Amazon Ads](https://membrane.agency/agent-skills/amazon-ads) | Audits 60 days of your Sponsored Products ads for spend with no orders, unused budgets, and duplicate or loose targeting, and states what the ads cost, earned, and changed in a month. |

## Requirements

macOS or Linux, on an x64 or arm64 processor. There's nothing to install. If your computer has Node 22.13 or newer, the plugin runs on it. If it doesn't, the plugin downloads a program that carries its own runtime, and on Linux that program needs glibc. Windows isn't supported yet.

## FAQ

<details>
<summary>What does the plugin send to Membrane?</summary>

Four kinds of request, all to `auth.membrane.agency`: the sign-in, the refresh of an expired token, one version check a day, and a read of Membrane's public list of jobs when you ask what Membrane offers. The version check sends the plugin version and nothing else, and asks whether this plugin is old enough to be worth updating. If it is, the agent says so once and carries on.

</details>

<details>
<summary>What does the plugin download?</summary>

Nothing, if your computer has Node 22.13 or newer: the plugin's code is in this repository and runs on your Node. Without it, the first command downloads the program for your computer from this repository's GitHub releases: 26 MB on an Apple silicon Mac, 37 MB on Linux. The script checks the download against the SHA-256 written in it and deletes it without running it if the two differ. The program is kept in `~/.membrane/bin/`, under its checksum. A plugin update downloads it again only when the program itself changed. Each download deletes the other copies more than a week old. Set `MEMBRANE_NO_NODE=1` to use the downloaded program even when you have Node.

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
