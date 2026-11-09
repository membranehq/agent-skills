---
name: handoff
description: Join the Membrane (membrane.agency) browser tab a person handed to this agent. The person pressed Hand off (⌘J) on a Membrane page and pasted the command `/membrane:handoff <code>` (in Codex, `$membrane:handoff <code>`). The skill joins the handoff with the join code through the `membrane` command, so the person's tab shows every Membrane step this agent takes, live. Then it waits for the person's ask, narrates long steps, moves the person's view to what it changes, and ends the handoff when the ask is done. Use only when the person ran that command.
argument-hint: '<join code>'
metadata:
  summary: 'Work in the Membrane tab you hand over: your agent joins it, and you watch each step live.'
---

# Joining a handoff

The person pressed Hand off (⌘J) on a Membrane page and pasted this command here. The command carries
one join code, such as `K7QM-4TXR`. From the join on, the person's tab shows every Membrane command
you run, live, and you can move their view.

Every step below is a `membrane` command. You join as the person, not in one workspace: the person
may have handed over a page in a workspace, or a page outside every workspace, such as the Inbox.
After the join, each `membrane handoff` verb acts in that handoff, on any page the person has open.
`membrane run <command> --workspace <key>` runs a workspace command in any workspace the person can
open, and the person's tab shows it. Without `--workspace`, a workspace command runs in the
workspace the handoff started in. `membrane run <command> --schema` prints the input a command
takes, as JSON Schema.

`membrane` is the plugin's own command, the file `scripts/membrane` of the plugin. Run it by its
full path, because it is not on the PATH: from this skill's folder the path is
`../../scripts/membrane`, and in Claude Code it is also `${CLAUDE_PLUGIN_ROOT}/scripts/membrane`.
In Codex, run every `membrane` command outside the sandbox: request escalated permissions for it.
The command needs the network to reach Membrane, and it writes the sign-in and the handoff under
`~/.membrane`. The person approves the command once, and can approve the `membrane` command for the
later calls.

## 0 · Read the join code

The command carried this argument: `$ARGUMENTS`. In Codex, the argument is the text the person typed
after `$membrane:handoff`.

A join code is eight letters and digits in two groups of four, joined by a dash, such as
`K7QM-4TXR`. If the argument is empty, or is not one join code, run nothing. Ask the person to
press Hand off again and paste the new command here.

## 1 · Join

Run `membrane handoff join <code>`. It prints whose tab you joined, the page the person is on, and
the verbs that drive the tab.

- If it exits 3 with `not-signed-in` or `sign-in-ended`, run `membrane login`. The person approves
  the sign-in in their browser. Then join again.
- If it answers that the code is wrong or used up, ask the person to press Hand off again and paste
  the new command.
- If it answers that this agent already takes part in a handoff, do not end that handoff. One
  sign-in of this computer takes part in one handoff at a time, so another chat on this computer may
  be working in it. Tell the person, and ask them to end the other handoff with End on its page, or
  to finish it in the other chat. When they say it has ended, join again. Run `membrane handoff
done` only if the person tells you to end the other handoff from here.

## 2 · Work the ask

- Wait for the person's ask in this chat. The join is not an ask.
- Before a long step, narrate it in one sentence: `membrane handoff say "<text>"`.
- Before a step that changes data, move the person to the page that shows the result:
  `membrane handoff navigate <path>`. A workspace page's path starts with `/w/<workspace key>/`, as
  the paths `membrane handoff where` prints, and the move may name another workspace than the one
  the person is in. `membrane handoff open <path>` opens a second page instead;
  run it only when the person asks for one, because a browser usually blocks a window that no click
  opened. If `membrane handoff where` then lists no new page, tell the person to click the bar at
  the top of their tab and press Open beside that page.
- `membrane handoff navigate` waits a few seconds for the tab to report the page it moved to, and
  only then says "Moved". If it says that the tab has not confirmed the move yet, run
  `membrane handoff where` before you build on the move.
- The console paths you move the person to. `<workspace>` is the workspace part of the paths
  `membrane handoff where` prints, or the workspace key. Never guess another path: a path the
  console does not know shows "Page not found".

  | Page                       | Path                                               |
  | -------------------------- | -------------------------------------------------- |
  | Home of a workspace        | `/w/<workspace>`                                   |
  | A data table, its records  | `/w/<workspace>/context/tables/<table id>/records` |
  | A data table, its overview | `/w/<workspace>/context/tables/<table id>`         |
  | A screen                   | `/w/<workspace>/screens/<screen id>`               |
  | A job                      | `/w/<workspace>/jobs/<job id>`                     |
  | The Inbox                  | `/dashboard/inbox`                                 |

  The table id is the `id` that `membrane run list-data-tables` prints. The Inbox is one page for
  all the person's workspaces.

- Prefer a screen to a table page. While the person follows the handoff, a screen reloads by itself
  when a table it reads gets new rows, so they watch each figure change as your step runs. A table
  page shows a change only when it opens after the change.
- A screen's path is `/w/<workspace>/screens/<screen id>`. `membrane run list-screens --input
'{"search": "<name>"}'` finds a screen by name. A page inside a screen adds its own part after the
  id, usually the page's name in lower case with dashes between the words, such as `/order-planner`.
- After a move, run `membrane handoff where`. It prints every page the person has open in the
  handoff, with each page's title, path and selected rows. `membrane handoff where --json` prints
  the same pages as JSON, with each page's `selection` and its state line (`summary`). A screen
  reports its page a few seconds after it loads; the title then names the screen and the page. Run
  it before you say "this page" or name what a page shows, because the person can browse on their
  own.
- `selection.ids` lists every selected row only when `selection` has no `all` and no `count` larger
  than the number of ids. The page names at most 20 selected rows by id, so a larger selection
  needs one of the two steps below before any write. Never change only the named rows of a larger
  selection.
- With `all`, the person selected every row the table shows under `selection.view`. Read those rows
  with `membrane run query-data-table-records`: match `view.filter`, and match `view.q` as text in
  the record's name or external id, or in any field when `view.qAllFields` holds. If the number of
  rows you read differs from `selection.count`, do not write: tell the person both numbers and ask
  which rows to change.
- With no `all` and a `count` larger than the number of ids, you cannot read the other selected
  rows. Tell the person how many rows they selected and how many you can see. Ask them to describe
  the rows by a rule you can query, or to filter the table and select every row.
- Before a write to more than one row, tell the person how many rows you will change and which
  ones, and wait for their yes.
- The page is the subject of the ask: "this table" means the element of the page they are on.
- Run each workspace command in the workspace of the page it is about: `--workspace` takes the key
  that follows `/w/` in that page's path.
- Read every value fresh with `membrane run query-data-table-records`. A page title is a name, not
  data.
- Write a row with `membrane run create-data-table-record`, and change one with `membrane run
update-data-table-record`. Membrane checks each write against what the person may do. If it
  refuses a write, do not try another way: tell the person what was refused and why.
- To recalculate after a change, use the control a screen gives its viewers. `membrane run
get-screen-controls` lists the routines a screen lets its viewers start, with each one's latest
  run. `membrane run run-screen-control` starts one. Then run `get-screen-controls` with `waitFor`
  set to the routine's key: the call waits until the run ends, at most `timeout` seconds (30 by
  default). If the run is still `running` when it answers, run it again the same way. Tell the
  person with `membrane handoff say` while it runs. If no screen offers the routine you need, tell
  the person: the recalculation then waits for its next scheduled run.
- If a command answers that the person paused the handoff, stop and wait for them in this chat. The
  `membrane handoff` verbs still work while it is paused; every other command is refused until they
  resume.
- When the ask is done, run `membrane handoff done`.