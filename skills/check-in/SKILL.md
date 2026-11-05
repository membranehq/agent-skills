---
name: check-in
description: Membrane operators only. A read-only check-in across every Membrane (membrane.agency) workspace where the operator holds a crew seat, which ends in one follow-up per piece of owed work. Use when the operator asks to check in, triage their accounts, or see what is owed across their workspaces.
metadata:
  summary: 'For Membrane operators: checks every workspace where you hold a crew seat and lists the work you owe.'
---

# Check-in

Membrane serves this skill's text only to signed-in Membrane operators, so the plugin ships this pointer to it.

`membrane` is the plugin's own command, the file `scripts/membrane` of the plugin. Run it by its full path, because it is not on the PATH: from this skill's folder the path is `../../scripts/membrane`, and in Claude Code it is also `${CLAUDE_PLUGIN_ROOT}/scripts/membrane`. In Codex, run every `membrane` command outside the sandbox: request escalated permissions for it. The command needs the network to reach Membrane, and it writes the sign-in and the cached guides under `~/.membrane`. The person approves the command once, and can approve the `membrane` command for the later calls.

1. Run `membrane guide check-in`.
2. The first line of the output names the file the guide is cached in. Read that file in full before the first step. A host can cut a long output short, and the file is always whole.
3. Follow the guide.

If the command exits 3, the person is not signed in to Membrane. Run `membrane login`, and ask the person to approve the sign-in in the browser. Then run `membrane guide check-in` again.

If the command exits 1 with the sentence that the guide is for Membrane operators, tell the person that this skill is for Membrane operators, and stop. Do not look for the guide anywhere else.