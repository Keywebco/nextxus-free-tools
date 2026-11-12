# Free Tools Assimilation — Maintenance and Adaptation by Automation

Owner: Roger Keyserling. Status: DRAFT, proposed, not canon. Date: 2026-11-12.
Source record: `ASSIMILATION.md`. Data: `assimilation.yaml` (51 tools, 1–51). Index: `index.html`.
Rule: automation proposes only. It never merges, never posts, never spends money,
never deletes anything, never publishes live. Nothing goes live without Roger's exact word.

## 1. What automation does, and what it never does

Automation does, on a schedule:
- Re-checks every link in `assimilation.yaml` (one HEAD/GET per tool, polite rate, no sign-in).
- Re-checks the three free key-less APIs we actually use: arXiv, Open Library, Unpaywall.
  Semantic Scholar is our research backbone; check its API status the same way.
- Detects: dead link, redirect to a new home, price change, free-tier change,
  license change, tool shut down, tool renamed, API removed.
- Files a proposal (issue), with FACT / INFERENCE / UNKNOWN labels, the old value,
  the new value, the date checked, and the source page.

Automation never does:
- Merge a pull request, push to main, publish a page, post to Facebook/Substack,
  send an email, spend money, delete a record or a file, or change a price.
- Copy content, code, images, or text that is not free to copy.
- Claim a recreate is built when it is only planned. Planned recreates stay
  planned in the YAML record until a file exists and is tested.

## 2. Cadence

- Quarterly, full check: every link, every API, every price and license note.
  First full check due: 2027-02-12.
- Monthly, light check: the three gates (ToS;DR, JustDeleteMe, VirusTotal, TinEye),
  the three free APIs, and the five tools customers use most (arXiv, Photopea,
  Unsplash, Pexels, Semantic Scholar).
- On demand: when Roger sends a new link, or when a customer reports a dead link.
  A new link starts a new assimilation, one by one, same method, new id (52, 53, …),
  appended, never renumbering old ids.

## 3. How a check runs (fail-open, mirror not gate)

A GitHub workflow, `.github/workflows/assimilation-check.yml`, proposed, not built yet:
- Trigger: schedule (quarterly / monthly), and manual dispatch only.
- Job: a plain Python script, `scripts/check-links.py`, proposed, not built yet.
  It reads `assimilation.yaml`, checks each URL, writes `checks/<date>.md`
  (tool, old status, new status, HTTP code, redirect target, label).
- The job always succeeds (`continue-on-error`, fail-open). A workflow failure
  can never stop other work, and never blocks a merge. It is a mirror, not a gate.
- On any change, the script opens one issue per changed tool, using the
  offspring-seed issue templates as the shape:
  - `truth_claim.md` for "this link is dead / this price changed" (source, confidence,
    falsifier, label, effect).
  - `proposal.md` for "replace it with X / recreate it / drop it" (why, claims,
    effect, rollback — cleanly undoable yes/no/unknown, kindness/consent, lineage).
- The Ring of Six checklist runs on each proposal, as a comment, in order:
  Plus (what is added), Minus (what is removed), Null (what is unchanged),
  Past (what was true before), Present (what is true now), Future (what it becomes).
  A proposal with an unknown effect escalates to the Twelve gate and waits for
  Roger's exact word.

## 4. How a change is decided

| Change found | Proposal | Who decides |
|---|---|---|
| Dead link, same tool at a new URL | Update URL, keep id, note old URL in record | Roger, merge word |
| Price / free-tier change | Update record, note old price, re-price our offer if it moves our cost + 10% | Roger, merge word (price is his) |
| License change (no longer free to copy/use) | Stop using it, mark record `superseded`, propose a replacement or a recreate | Roger, merge word |
| Tool shut down | Mark record `superseded`, propose replacement from AlternativeTo / our swap directory | Roger, merge word |
| Tool renamed | Update name, keep id, note old name | Roger, merge word |
| New tool Roger sends | New assimilation, new id, same one-by-one method | Roger, merge word |
| Recreate planned → built | Change status `planned` to `built`, only with a tested file and a live check | Roger, merge word |

Append-only: never delete a record. A superseded record stays in the YAML file,
marked `status: superseded`, with `superseded_by` naming the new record or tool.
The YAML database is the brain; the record of what was, is, and is planned to be
stays whole.

## 5. How adaptation works (new tools, new features)

1. Roger sends a link, or automation proposes one from AlternativeTo / a dead-tool
   replacement search.
2. Pontus assimilates it one by one, same method as items 1–51: distinctiveness,
   what we already have inside us that is superior, blend or recreate in our own
   image, use their link/resource if possible, duplicate only if not.
3. A new YAML record is drafted, with a new id, in a branch, never on main.
4. The Ring of Six checklist runs on the proposal. Effectful work (a new price,
   a new public page, a new API use) escalates to the Twelve gate and waits for
   Roger's exact word.
5. Roger gives the merge word for that named PR. Only then does it go live.
6. The index page is rebuilt from `assimilation.yaml` (generated, not hand-edited),
   so the page and the data can never drift apart.
7. The repo that holds the record is updated the same day; a pointer record in
   `nextxus-yaml` (see repo plan in the parent report) is updated with the new count.

## 6. What "good" looks like, quarterly

- 51 records, all checked, none older than one quarter.
- Zero dead links on the public index page.
- Every price in our offer ($49 / $69, API at cost + 10%) still matches the
  provider's current price, or a proposal is open saying it does not.
- Every planned recreate is either still planned (named, not claimed) or built
  (tested file, live check, record updated).
- Every change has a proposal issue, a Ring of Six checklist, and Roger's merge word
  in the record. No silent changes.

## 7. Limits, stated plainly

- A link check proves the page answers, not that the tool still works as described.
  A price check proves the listed price, not what a customer will actually pay.
- Some tools have no public API and no free tier page; those are checked by hand,
  labelled UNKNOWN where the page does not say, and never guessed.
- Automation cannot judge whether a tool is still worth blending. That judgement
  is Roger's, and Pontus's, on the record, one by one.
