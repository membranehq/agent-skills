---
name: handoff
description: Join the Membrane (membrane.agency) browser tab a person handed to this agent. The person pressed Hand off (⌘J) on a Membrane page and pasted the command `/membrane:handoff <code>` (in Codex, `$membrane:handoff <code>`). The skill joins the handoff with the join code through the Membrane server, so the person's tab shows every Membrane step this agent takes, live. Then it waits for the person's ask, narrates long steps, moves the person's view to what it changes, and ends the handoff when the ask is done. Use only when the person ran that command.
argument-hint: '<join code>'
metadata:
  summary: 'Work in the Membrane tab you hand over: your agent joins it, and you watch each step live.'
---

# Joining a handoff

The person pressed Hand off (⌘J) on a Membrane page and pasted this command here. The command carries
one join code, such as `K7QM-4TXR`. From the join on, the person's tab shows every step you take on
the Membrane server, live, and you can move their view.

Every tool below is a tool of the Membrane server (`membrane`). Each one except `join-agent-handoff`
takes `workspaceId`, the id of the handoff's workspace.

## 0 · Read the join code

The command carried this argument: `$ARGUMENTS`. In Codex, the argument is the text the person typed
after `$membrane:handoff`.

A join code is eight letters and digits in two groups of four, joined by a dash, such as
`K7QM-4TXR`. If the argument is empty, or is not one join code, call nothing. Ask the person to
press Hand off again and paste the new command here.

## 1 · Join

Call `join-agent-handoff` with `code` set to the join code. It answers with the handoff's workspace
and the page the person is on. Keep the workspace id: every later tool takes it as `workspaceId`.

- The first call to the Membrane server asks the person to sign in and pick the workspaces this agent
  may open. Wait until they finish, then call `join-agent-handoff` again.
- If the join answers that this agent may not open the handoff's workspace, ask the person to connect
  the Membrane server again and tick that workspace, then join again.
- If the join answers that the code is wrong or used up, ask the person to press Hand off again and
  paste the new command.
- If the join answers that this agent already takes part in a handoff, do not end that handoff. One
  sign-in of this agent takes part in one handoff at a time, so another chat of this agent may be
  working in it. Tell the person, and ask them to end the other handoff with End on its page, or to
  finish it in the other chat. When they say it has ended, join again. Call `end-agent-handoff` only
  if the person tells you to end the other handoff from here.

## 2 · Work the ask

- Wait for the person's ask in this chat. The join is not an ask.
- Before a long step, narrate it in one sentence: `say-agent-handoff` with `text`.
- Before a step that changes data, move the person to the page that shows the result:
  `navigate-agent-handoff` with `path`. A path starts with `/w/<workspace id>/`. Move the tab the
  person follows. Set `newWindow` only when the person asks for a second page: a browser usually
  blocks a window that no click opened. If `get-agent-handoff-page` then lists no new page, tell the
  person to click the bar at the top of their tab and press Open beside that page.
- Prefer a screen to a table page. While the person follows the handoff, a screen reloads by itself
  when a table it reads gets new rows, so they watch each figure change as your step runs. A table
  page shows a change only when it opens after the change.
- A screen's path is `/w/<workspace id>/screens/<screen id>`. `list-screens` with `search` finds a
  screen by name. A page inside a screen adds its own part after the id, usually the page's name in
  lower case with dashes between the words, such as `/order-planner`.
- After a move, call `get-agent-handoff-page`. It answers every page the person has open in the
  handoff, with each page's path, title, selected rows (`selection`) and state line (`summary`).
  A screen reports its page a few seconds after it loads; the title then names the screen and the
  page. Call it before you say "this page" or name what a page shows, because the person can browse
  on their own.
- `selection.ids` lists every selected row only when `selection` has no `all` and no `count` larger
  than the number of ids. The page names at most 20 selected rows by id, so a larger selection
  needs one of the two steps below before any write. Never change only the named rows of a larger
  selection.
- With `all`, the person selected every row the table shows under `selection.view`. Read those rows
  with `query-data-table-records`: match `view.filter`, and match `view.q` as text in the record's
  name or external id, or in any field when `view.qAllFields` holds. If the number of rows you read
  differs from `selection.count`, do not write: tell the person both numbers and ask which rows to
  change.
- With no `all` and a `count` larger than the number of ids, you cannot read the other selected
  rows. Tell the person how many rows they selected and how many you can see. Ask them to describe
  the rows by a rule you can query, or to filter the table and select every row.
- Before a write to more than one row, tell the person how many rows you will change and which
  ones, and wait for their yes.
- The page is the subject of the ask: "this table" means the element of the page they are on.
- Read every value fresh with `query-data-table-records`. A page title is a name, not data.
- Write a row with `create-data-table-record`, and change one with `update-data-table-record`.
  Membrane checks each write against what the person may do. If it refuses a write, do not try
  another way: tell the person what was refused and why.
- To recalculate after a change, use the control a screen gives its viewers. `get-screen-controls`
  lists the routines a screen lets its viewers start, with each one's latest run. `run-screen-control`
  starts one. Call `get-screen-controls` again until that run's `status` is no longer `running`; tell
  the person with `say-agent-handoff` while it runs. If no screen offers the routine you need, tell
  the person: the recalculation then waits for its next scheduled run.
- If a tool answers that the person paused the handoff, stop and wait for them in this chat. The
  handoff tools still work while it is paused; every other tool is refused until they resume.
- When the ask is done, call `end-agent-handoff`.