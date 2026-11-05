---
name: operate
description: Membrane operators only. Operating Membrane (membrane.agency) client accounts and jobs by the Operator Manual, which Membrane serves to signed-in operators. Use for client operations work in a Membrane workspace, not when developing Membrane as software.
metadata:
  summary: 'For Membrane operators: runs client work by the Operator Manual, which Membrane serves to operators who sign in.'
---

# Operate

Membrane serves this skill's text only to signed-in Membrane operators, so the plugin ships this pointer to it.

`membrane` is the plugin's own command, the file `scripts/membrane` of the plugin. Run it by its full path, because it is not on the PATH: from this skill's folder the path is `../../scripts/membrane`, and in Claude Code it is also `${CLAUDE_PLUGIN_ROOT}/scripts/membrane`. In Codex, run every `membrane` command outside the sandbox: request escalated permissions for it. The command needs the network to reach Membrane, and it writes the sign-in and the cached guides under `~/.membrane`. The person approves the command once, and can approve the `membrane` command for the later calls.

1. Run `membrane guide operate`.
2. The first line of the output names the file the guide is cached in. The second line names the other files beside it. Read the guide's file in full, then the files it tells you to read, before the first step of the work. A host can cut a long output short, and the files are always whole.
3. Follow the guide.

If the command exits 3, the person is not signed in to Membrane. Run `membrane login`, and ask the person to approve the sign-in in the browser. Then run `membrane guide operate` again.

If the command exits 1 with the sentence that the guide is for Membrane operators, tell the person that this skill is for Membrane operators, and stop. Do not look for the guide anywhere else.