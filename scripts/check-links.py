#!/usr/bin/env python3
"""Check the Federation Free Tools links in assimilation.yaml.

Automation proposes only. This script NEVER merges, posts, spends money,
deletes anything, or pushes to main. It only:
  - reads assimilation.yaml,
  - checks each tool's URL (one polite request, no sign-in),
  - checks the free key-less APIs we actually use (arXiv, Open Library,
    Unpaywall, plus Semantic Scholar, our research backbone),
  - writes a dated report to checks/<YYYY-MM-DD>.md,
  - optionally (--open-issues, with GITHUB_TOKEN set) opens ONE GitHub
    issue per tool whose status changed to DEAD, in the shape of the
    offspring-seed truth_claim / proposal templates, with the Ring of Six
    checklist and an escalation note: unknown effect waits for Roger's
    exact word. Issues are proposals only; nothing is merged by this script.

Exit code is always 0 (fail-open): a check failure must never stop other
work and never block a merge. A link check proves the page answers, not
that the tool still works as described. HTTP 403 / 429 is labelled
UNKNOWN (the page may block bots), never DEAD. A tool with no public API
is checked by its page only, by hand if needed.

Usage:
  python3 scripts/check-links.py [--yaml assimilation.yaml]
      [--out-dir checks] [--mode full|light] [--date YYYY-MM-DD]
      [--open-issues] [--repo Keywebco/nextxus-free-tools]

Light mode checks: the gates (ToS;DR, JustDeleteMe, VirusTotal, TinEye),
the three free APIs, and the five tools customers use most (arXiv,
Photopea, Unsplash, Pexels, Semantic Scholar). Full mode checks all 51.
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# Free API endpoints we actually use. No key, no sign-in.
API_CHECKS = {
    "arXiv API": "https://export.arxiv.org/api/query?search_query=all:electron&max_results=1",
    "Open Library API": "https://openlibrary.org/search.json?q=test&limit=1",
    "Unpaywall API": "https://api.unpaywall.org/v2/10.1038/nature12373?email=check@next-xus.net",
    "Semantic Scholar API": "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/nature12373?fields=title",
}

GATE_NAMES = ["tosdr.org", "justdeleteme", "virustotal", "tineye"]
MOST_USED_NAMES = ["arxiv", "photopea", "unsplash", "pexels", "semantic scholar"]
API_TOOL_NAMES = ["arxiv", "open library", "unpaywall"]

USER_AGENT = "Federation-Free-Tools-Check/1.0 (https://github.com/Keywebco/nextxus-free-tools; polite link check, one request per tool)"


def load_tools(yaml_path):
    """Load tools from assimilation.yaml. PyYAML if present, else a small
    fallback that reads the id / name / url lines we write."""
    try:
        import yaml  # type: ignore
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        tools = data["assimilation"]["tools"]
        return [{"id": t["id"], "name": t["name"], "url": t["url"],
                 "category": t.get("category", ""), "status": t.get("status", "")}
                for t in tools]
    except ImportError:
        tools, cur = [], None
        with open(yaml_path) as f:
            for line in f:
                m = re.match(r"\s+- id: (\d+)\s*$", line)
                if m:
                    cur = {"id": int(m.group(1))}
                    tools.append(cur)
                    continue
                if cur is None:
                    continue
                for key in ("name", "url", "category", "status"):
                    m = re.match(r"\s+%s: (.+?)\s*$" % key, line)
                    if m:
                        cur[key] = m.group(1).strip().strip("'\"")
        return tools


def check_url(url, timeout=20):
    """One polite request. Returns (label, http_code, final_url, note).
    HEAD first, GET fallback (some servers refuse HEAD)."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", USER_AGENT)
        req.add_header("Accept", "*/*")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final = resp.geturl()
                code = resp.status
                if code < 400:
                    label = "OK" if final == url else "REDIRECT"
                    note = "" if label == "OK" else "now at %s" % final
                    return label, code, final, note
                return "UNKNOWN", code, final, "HTTP %d (page answered, status unclear)" % code
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (405, 501):
                continue  # server refuses HEAD; try GET
            if e.code in (403, 429):
                return "UNKNOWN", e.code, url, "HTTP %d — page may block bots; not proof of dead" % e.code
            if e.code == 404:
                return "DEAD", 404, url, "HTTP 404 not found"
            if e.code >= 500:
                return "DEAD", e.code, url, "HTTP %d server error" % e.code
            return "UNKNOWN", e.code, url, "HTTP %d" % e.code
        except urllib.error.URLError as e:
            if method == "HEAD":
                continue
            return "DEAD", 0, url, "could not reach: %s" % e.reason
        except Exception as e:  # timeout etc. — never fatal, fail-open
            if method == "HEAD":
                continue
            return "UNKNOWN", 0, url, "check failed: %s" % e
        time.sleep(1)  # polite rate: one request per second
    return "UNKNOWN", 0, url, "no answer"


def ring_of_six_lines(name, old, new):
    return (
        "- Plus (what is added): a proposal to update the record for %s.\n"
        "- Minus (what is removed): nothing is deleted; the old value stays in the record.\n"
        "- Null (what is unchanged): the tool id, its history, and every other record.\n"
        "- Past (what was true before): %s\n"
        "- Present (what is true now): %s\n"
        "- Future (what it becomes): the record updated, or marked superseded with a replacement, only on Roger's merge word.\n"
        % (name, old, new)
    )


def open_issue(repo, token, title, body):
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/issues" % repo,
        data=json.dumps({"title": title, "body": body,
                         "labels": ["assimilation-check"]}).encode(),
        method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "replace")[:400]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yaml", default="assimilation.yaml")
    ap.add_argument("--out-dir", default="checks")
    ap.add_argument("--mode", choices=["full", "light"], default="full")
    ap.add_argument("--date", default=None,
                    help="Report date YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--open-issues", action="store_true",
                    help="Open one issue per DEAD tool (needs GITHUB_TOKEN)")
    ap.add_argument("--repo", default="Keywebco/nextxus-free-tools")
    args = ap.parse_args()

    date = args.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    tools = load_tools(args.yaml)
    print("loaded %d tools from %s" % (len(tools), args.yaml))

    if args.mode == "light":
        def keep(t):
            n = t["name"].lower()
            u = t["url"].lower()
            return (any(g in n or g in u for g in GATE_NAMES)
                    or any(m in n for m in MOST_USED_NAMES)
                    or any(a in n for a in API_TOOL_NAMES))
        checked_tools = [t for t in tools if keep(t)]
    else:
        checked_tools = tools
    print("mode=%s, checking %d tools" % (args.mode, len(checked_tools)))

    rows = []
    for t in checked_tools:
        label, code, final, note = check_url(t["url"])
        rows.append({"id": t["id"], "name": t["name"], "url": t["url"],
                     "label": label, "code": code, "final": final, "note": note})
        print("  [%s] %d %s %s" % (label, t["id"], t["name"], note))
        time.sleep(1)

    api_rows = []
    for name, url in API_CHECKS.items():
        label, code, final, note = check_url(url)
        api_rows.append({"name": name, "url": url, "label": label,
                         "code": code, "note": note})
        print("  [API %s] %s %s" % (label, name, note))
        time.sleep(1)

    ok = sum(1 for r in rows if r["label"] == "OK")
    redir = sum(1 for r in rows if r["label"] == "REDIRECT")
    dead = [r for r in rows if r["label"] == "DEAD"]
    unknown = [r for r in rows if r["label"] == "UNKNOWN"]

    lines = []
    lines.append("# Free Tools link check — %s (%s mode)" % (date, args.mode))
    lines.append("")
    lines.append("Source: `assimilation.yaml` (%d tools). Automation proposes only — "
                 "nothing here merges, posts, spends, deletes, or goes live. "
                 "A link check proves the page answers, not that the tool still "
                 "works as described. HTTP 403 / 429 is UNKNOWN, never DEAD." % len(tools))
    lines.append("")
    lines.append("Summary: %d checked, %d OK, %d redirected, %d dead, %d unknown." %
                 (len(rows), ok, redir, len(dead), len(unknown)))
    lines.append("")
    lines.append("## Tools")
    lines.append("")
    lines.append("| id | tool | status | HTTP | note |")
    lines.append("|---:|---|---|---:|---|")
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s |" %
                     (r["id"], r["name"], r["label"], r["code"] or "-",
                      (r["note"] or "-").replace("|", "/")))
    lines.append("")
    lines.append("## Free APIs")
    lines.append("")
    lines.append("| api | status | HTTP | note |")
    lines.append("|---|---|---:|---|")
    for r in api_rows:
        lines.append("| %s | %s | %s | %s |" %
                     (r["name"], r["label"], r["code"] or "-",
                      (r["note"] or "-").replace("|", "/")))
    lines.append("")
    if dead:
        lines.append("## Needs a proposal (DEAD)")
        lines.append("")
        for r in dead:
            lines.append("- #%d %s (%s): %s" % (r["id"], r["name"], r["url"], r["note"]))
        lines.append("")
        lines.append("Each DEAD tool gets one issue, in the truth_claim / proposal "
                     "shape, with the Ring of Six checklist. Effect unknown "
                     "escalates to the Twelve gate and waits for Roger's exact word.")
        lines.append("")
    else:
        lines.append("## Needs a proposal (DEAD)")
        lines.append("")
        lines.append("None. No DEAD tools in this check.")
        lines.append("")

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, date + ".md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print("wrote %s" % out_path)

    if args.open_issues and dead:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("GITHUB_TOKEN not set — skipping issue creation (proposals only in report).")
        else:
            for r in dead:
                title = "Link check %s: %s is DEAD (%s)" % (date, r["name"], r["url"])
                body = (
                    "Source: automated link check %s (%s mode), report `checks/%s.md`.\n\n"
                    "Claim (truth_claim shape): the link for #%d %s no longer answers.\n"
                    "- Source: %s\n- Confidence: checked once, %s\n"
                    "- Falsifier: the page answers again, or the tool moved to a new URL.\n"
                    "- Label: INFERENCE (one check proves the page did not answer, not that the tool is gone).\n"
                    "- Effect: unknown — escalates to the Twelve gate and waits for Roger's exact word.\n\n"
                    "Proposal (proposal shape): update the URL, mark the record superseded with a "
                    "replacement, or recreate it in our own image. Rollback: cleanly undoable — "
                    "the old value stays in the record. Kindness/consent: no one is named, no data is shared.\n\n"
                    "Ring of Six checklist:\n%s\n"
                    "Automation proposes only. Nothing merges, posts, spends, or deletes from this issue."
                    % (date, args.mode, date, r["id"], r["name"], r["url"], r["note"],
                       ring_of_six_lines(r["name"], "link answered", "link did not answer: " + r["note"])))
                status, resp = open_issue(args.repo, token, title, body)
                print("  issue for #%d %s: %s %s" % (r["id"], r["name"], status,
                      resp.get("html_url", resp)))

    print("summary: %d checked, %d OK, %d redirected, %d dead, %d unknown — exit 0 (fail-open)" %
          (len(rows), ok, redir, len(dead), len(unknown)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
