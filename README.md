# Membrane for your AI agent

Membrane's plugin for Claude Code and Codex. It brings your Membrane workspaces into your agent, connects your apps on your computer, and shows Membrane's jobs catalog. Installing it needs no sign-up, and your app tokens stay on your computer.

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

In Codex or the ChatGPT desktop app, open Settings → Hooks once after installing and turn on the `membrane` hook. Without it the plugin still works, but your agent starts without the short guide to it.

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

- **Free.** The plugin is free to use, under the MIT license.
- **No sign-up to install.** Installing needs no Membrane account and no email. The Membrane server asks you to sign in the first time your agent uses it, and it opens only the workspaces you pick. When you connect an app on your computer, you sign in to that app through Membrane's sign-in page, so the app's client secret never sits on your machine.
- **Your tokens stay on your computer.** The plugin keeps each app's tokens under `~/.membrane/`, and its scripts upload nothing. Membrane receives only what your agent does in the workspaces you picked.

## Skills

| Skill | What it does |
| --- | --- |
| Membrane | What Membrane is, what its jobs cost, and how to hand work over to Membrane. |

## Requirements

macOS or Linux, on an x64 or arm64 processor. There's nothing to install. If your computer has Node 22.13 or newer, the plugin runs on it. If it doesn't, the plugin downloads a program that carries its own runtime, and on Linux that program needs glibc. Windows isn't supported yet.

## FAQ

<details>
<summary>What does the plugin send to Membrane?</summary>

The Membrane server, at `api.membrane.agency/mcp`, receives what your agent does in the workspaces you picked, such as a request it answers and a file it attaches to an answer. The plugin's scripts make four kinds of request, all to `auth.membrane.agency`: the sign-in to an app, the refresh of an expired token, one version check a day, and a read of Membrane's public list of jobs when you ask what Membrane offers. The version check sends the plugin version and nothing else, and asks whether this plugin is old enough to be worth updating. If it is, the agent says so once and carries on.

</details>

<details>
<summary>How do I sign in to the Membrane server?</summary>

Start a new session after you install the plugin. The first time your agent uses the Membrane server, it asks you to sign in to Membrane and to pick the workspaces it may open. In Claude Code, run `/mcp`, pick the Membrane server, and sign in there. In Codex, run `codex mcp login membrane` in a terminal. You can change the workspaces or disconnect the agent at any time in your Membrane account, under AI agents.

</details>

<details>
<summary>What does the plugin download?</summary>

Nothing, if your computer has Node 22.13 or newer: the plugin's code is in its repository, `membranehq/agent-skills`, and runs on your Node. Without it, the first command downloads the program for your computer from that repository's GitHub releases: 26 MB on an Apple silicon Mac, 37 MB on Linux. The script checks the download against the SHA-256 written in it and deletes it without running it if the two differ. The program is kept in `~/.membrane/bin/`, under its checksum. A plugin update downloads it again only when the program itself changed. Each download deletes the other copies more than a week old. Set `MEMBRANE_NO_NODE=1` to use the downloaded program even when you have Node.

</details>

<details>
<summary>Does Membrane count who uses the plugin?</summary>

Membrane counts how many installs make the version check each day and keeps no address. Set `MEMBRANE_NO_UPDATE_CHECK=1` to switch the check off.

</details>

## About Membrane

There is a right way to run your operations. Membrane finds it and runs it. AI agents do the around-the-clock work on the tools a company already uses, and a named operator makes the calls and answers for the result. The jobs and their prices are at https://membrane.agency/jobs.

## License

MIT — see [LICENSE](LICENSE).
