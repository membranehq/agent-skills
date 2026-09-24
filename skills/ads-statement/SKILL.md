---
name: ads-statement
description: Build the Ads Statement of an Amazon Ads account on this computer with the `membrane` tool — what the ads cost and earned in a period, what changed on the account, and which questions to put to whoever runs the ads. Use when the person asks what their ads agency or ads manager did last month, whether the ads paid off, what changed in the account, or what to ask the agency.
---

# Ads Statement

The Ads Statement tells the owner of an Amazon Ads account what happened in one period: what the ads cost, what they were credited with, what was left after landed cost, which changes were recorded on the account and what followed them, and which questions are worth putting to whoever runs the ads. The model in the plugin computes every number, every flag and every question. You do two jobs the model cannot: you judge whether search terms fit the advertised products and which words mark a search for the brand, and you write the summary the owner reads first.

Run every command with the `membrane` tool that ships with this plugin: `${CLAUDE_PLUGIN_ROOT}/scripts/membrane` in Claude Code, or beside this skill's installed path in Codex. Every command prints JSON on stdout and one status line on stderr.

Everything stays on this computer. `~/.membrane/audits/<profileId>.sqlite` holds the pulled data, the change log and the stored statements. `~/.membrane/reports/` holds the HTML statements.

## Steps

1. **Connect.** Run `membrane connections`. If no `amazon-advertising` connection exists, run `membrane connect amazon-advertising`. Show the person the URL it prints and ask them to open it, sign in to Amazon, and allow access. The done page shows a short code. Ask for the code and run `membrane connect complete <code>`. The code works once and expires 15 minutes after the start. Amazon's page asks to allow campaign management: that is the one access Amazon Ads grants to any tool that reads an account. The statement reads the account and changes nothing on it.
2. **Choose the profile.** Run `membrane ads profiles`. If the connection reaches one profile, use it. If it reaches several, show the list and ask which one to state, unless the person already named it.
3. **Pull.** Run `membrane ads pull --profile <profileId> --days 95`. A statement compares the period with the period before it, so it needs the daily reports from the first day of that earlier period. Amazon keeps 95 days of most reports, and the pull asks for no day Amazon no longer holds. The search-term and purchased product reports return rows from about 65 days back only. If a period the statement reads starts before a report's first day, the statement names that day. The pull also reads the titles of the products and starts to read Amazon's change history, which is where the statement's changes come from. Amazon answers one page of 200 changes every 150 seconds, so the pull takes the first page only; `history` in the output says where the read stands, and `changesInLog` counts the changes the log holds. The pull returns at once; Amazon takes 20 minutes or more to produce the reports. Do not wait in a loop. Tell the person the pull is running.
4. **Check.** Run `membrane ads status --profile <profileId>`. When every report reads `done`, go on. If a report reads `failed`, run the pull again once. Each status also reads the next page of the change history when Amazon allows one.
5. **Read the change history** when `history.state` in the pull or status output reads `reading`, or when the statement answers `history-reading` or `history-not-read`. Run `membrane ads history --profile <profileId> --from <day> --to <day>` with the statement's period; without the dates it reads the last whole month. It reads the period and the 16 days before it, in the profile's own days, as three reads with a place of their own: the status changes of keywords, the status changes of product targets, and every change of campaigns, ad groups, ads and negative keywords. Each read asks for the whole span, and a window that Amazon counts at 10,000 changes is split in halves, the newer first. Bid changes of keywords and product targets are not read, and the statement says so. The pace adapts to Amazon's limit: 60 seconds between two pages at first, less after each answer, and twice as long after each refusal. It returns when the read ends. A quiet account takes a few minutes; an account with many campaign and ad group changes takes longer. So run it in the background and tell the person the change history is being read. The statement builds once all three reads cover a day of its month. While the read goes on, `history.reading` in the statement output is `true`, `history.hint` names the days read, and the page says the earlier changes are not recorded yet. Tell the person, and build the statement again when the read ends. If the read ends `stopped`, the next `ads history` reads only the windows not read yet.
6. **Build.** Run `membrane ads statement --profile <profileId> --from <YYYY-MM-DD> --to <YYYY-MM-DD>`. Without dates it states the last whole calendar month the reports cover. Add `--unit-costs <file.csv>` when the person gave unit costs (columns: `asin,contributionPerUnit,source,windowStart,windowEnd`); without them the statement cannot say what the ads left after landed cost. The output names what the statement still needs in `next`.
7. **Review the search terms and the brand words** when `next` is `review`. Read the file at `reviewInputPath`. Follow the review instructions below, word for word, and write the result as JSON to a file of your own: `{"verdicts": [{"searchTerm": "...", "verdict": "relevant" | "irrelevant" | "unsure", "reason": "..."}], "brand": {"words": ["..."], "exclusions": ["..."], "labels": [{"searchTerm": "...", "brand": true}]}}`. If the input holds no `terms`, return an empty `verdicts` list. If the input holds a `brand` section, the result must hold `brand`, even with empty lists. Then run the build again with `--review <your file>`. The statement stores the verdicts and the brand words and uses them from then on.
8. **Write the summary** when `next` is `summary`. Read the file at `summaryInputPath`. Follow the summary instructions below, word for word, and write the result as JSON to a file of your own: `{"headline": "...", "body": "...", "asks": ["...", "..."]}`. Then run the build again with `--summary <your file>`.
9. **Show the statement** when `next` is `done`. Open the HTML file at `reportPath` for the person, or give them the path. In chat, give the headline and the asks from your summary, and nothing more: the statement holds the rest.
10. **Answer the rules.** The statement asks the owner only for the owner's own rules: the most a test may spend before it is stopped, the days to act on it, and the ACOS limit for a product without a landed cost. It states its other decisions, such as the brand words, the days without a change it allows and the spend from which a search term is checked, and the owner may replace one. The HTML lists each rule and each decision with its id. When the person answers one, run `membrane ads statement answer --profile <profileId> --question <id> --value <answer>`, then build the statement again. An empty `--value ""` withdraws an answer. The same command stores the agency's own report or the contract terms as text, with `--question agency-report` or `--question agency-contract`: the statement shows that text under "Compared with the agency" and does not compare it yet.

## Rules

- Never compute a number the statement does not hold. Quote the statement's figures and its words.
- Say "changes recorded on the account". Never say the agency or anyone else made a change: Amazon's change data names no person.
- A flag of kind Fact is a fact. A flag of kind Needs review says whether a reviewer has checked it. A flag of kind Needs your input is a question for the owner or the agency, as its question says.
- Every dollar figure carries its span, such as "in August 2026". Never scale a figure to a year.
- Do not recommend firing anyone, and use no judgement words about people.
- The brand words carry forward: a later period uses them, and the review input asks about the brand again only when new search terms with high spend appear. If the owner names the brand words, store them with `--question brand-terms`; the owner's list replaces the reviewer's.
- To build the statement of an earlier period again after new data arrives, run the build again. The stored review of that period is kept. The stored summary is kept only while the figures it was written from stay the same; when they change, `next` is `summary` and you write a new one. Pass `--review` or `--summary` again to replace either.

## Review instructions

These are the instructions the Membrane routine gives its own reviewer. Follow them as written.

<!-- BEGIN generated: review-instructions -->

```text
You check whether Amazon search terms fit the products an ad group advertises, and which searches name the brand.

Part 1: relevance. For each search term in "terms", compare it with the titles of the products its ad group advertises, and give one verdict:
- relevant: a shopper who typed this term could want one of these products.
- irrelevant: the term asks for a different kind of product, a different use, or a feature none of these products has.
- unsure: the term is too short, too vague, or in a language you cannot read.

Judge the words only. Spend, clicks and orders are not part of the verdict.
Give a verdict for every search term in "terms", with a reason of at most 20 words that names the mismatch or the match.

Part 2: brand words. If the input holds a "brand" section, it lists the account's profile name, its product titles, its campaign and ad-group names, the brand words and exclusions already chosen, and the search terms with the most spend that no chosen word covers yet.
- A brand word is a word or phrase that means a shopper searched for this brand or one of its product lines by name: the brand name, its spellings with and without a space, and the names of its product lines. Take brand words only from the names, the titles and the listed search terms.
- A product line name is a name the brand gave a range of its products. A phrase that says what a product is, such as "weekly planner", "acrylic calendar" or "chore chart", is never a brand word, even when the account sells nothing else.
- Test each word before you return it: if a shopper who has never heard of this brand could type it, leave it out.
- An exclusion is a search term, or a phrase in one, that holds a brand word but asks for something else, such as another company whose name holds the word.
- Return only words and exclusions to add. The ones already chosen stay.
- If the brand name is an ordinary phrase that shoppers also type for other reasons, or if "mode" is "labels", return no words. Label every listed search term instead: brand true when it is a search for this brand, false when it is not.
If the input holds no "brand" section, return empty lists.
```

<!-- END generated: review-instructions -->

## Summary instructions

These are the instructions the Membrane routine gives its own summary writer. Follow them as written. The `body` holds at most 250 words, paragraphs separated by a blank line; `headline` is one sentence; `asks` holds three to five questions.

<!-- BEGIN generated: summary-instructions -->

```text
You write the summary a business owner reads first, above an Ads Statement for one Amazon advertising account and one period. The statement's model has computed every number and decided every flag. Your job is to say what matters, in plain words, and nothing else.

Rules:
1. Use only the numbers in the input. Round them; never compute a new one. Copy a ratio in the statement's own words, such as "$0.57 back for each ad dollar"; never call the ratio itself a loss or a gain.
2. Open with the result: what the ads cost, what they were credited with in sales, and what was left after landed cost and ads. If that amount is below zero, say the ads lost it; never write a negative amount as "left". If the contribution is missing, give the ACOS and its move in the words of "acosMove", say that landed costs are missing, and say what the owner can add to show what the ads left, as "costAsk" asks for it. Then, in one sentence, give the largest move "sections" shows: brand searches against other searches, one product, or one placement, with both periods.
3. If "campaignsOff" lists campaigns that served almost nothing for part of the period, say so right after the result, because it changes how the totals read. Name at most the five it lists, with their days and what the input says about why, and give the count of the rest in the words of "campaignsOffRest". Never state a cause the input does not state.
4. Then cover the flags in the order given, at most five. State each one by its finding and its dollars. Describe the dollars in the exact words of its "what", with any condition those words name, and keep any condition the finding puts on them. When a flag holds "parts", state each part by its own finding; the flag's dollars cover only the parts it counts. Flags can count the same spend, so never add their dollars together. Label every dollar figure with its span, such as "in August 2026". Never scale a figure to a year.
5. A deterministic flag is a fact: state it as one. A needs-review flag says whether a reviewer has checked it. A needs-your-input flag is a question for the owner: ask it. If none of the five flags you cover needs the owner's input, also ask the question of the first needs-your-input flag after them. When you quote a line the flags judge by, such as the test budget or the ACOS limit, take its words from "settings" and say whether the owner set it or the statement chose it. When a figure counts from a line, name the line with the figure.
6. Say "changes recorded on the account", never that the agency made them. Amazon's change data names no person. If "changes.complete" is false, the account can have had more changes than were recorded: a count of recorded changes is exact, and the account's changes were at least that many. Never write "at least" beside "recorded". Never say a span had no change; say that no change was recorded in it.
7. No judgement words about people, such as negligent, lazy or incompetent. No guesses about intent. Do not recommend firing anyone.
8. Mention a limit only when it changes a conclusion you state.
9. Asks: choose three to five questions for the agency. Take them first from the "question" of each flag you covered whose kind is not needs-your-input, then from "questions" in the input whose "to" is "agency". Keep their words; shorten them if you must. Each ask holds the question of one flag or one entry of "questions". Add none of your own, and never put a question for the owner among them.
10. Plain English, short sentences, at most 250 words in the body. No headings. The first time you use ACOS, say what it is: ad spend as a share of the sales credited to the ads.
```

<!-- END generated: summary-instructions -->