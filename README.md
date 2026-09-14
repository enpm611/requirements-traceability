# Exercise — Requirements Traceability

**ENPM 611 · Lecture 2 · Requirements Engineering**

---

## Overview

In class, we discussed how GitHub Issues, Pull Requests, and commits form a
lightweight Requirements Traceability Matrix. In this exercise you will build a
Python script that **mines a real open-source repository** and surfaces those
traceability links — or the absence of them.

The repository you will analyze is **`psf/requests`** — the popular Python HTTP
library. It is small enough to be approachable but has thousands of real Issues
and PRs with clear linking conventions.

---

## Setup

### 1. Create a virtual environment and install dependencies

```bash
# Create the virtual environment (one-time setup)
python3 -m venv .venv

# Activate it
# macOS / Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> **Tip:** Your shell prompt will show `(.venv)` when the environment is active.
> You must activate it each time you open a new terminal session.

### 2. Get a GitHub Personal Access Token

The GitHub API allows 60 unauthenticated requests per hour. With a token, that
limit rises to 5,000. You will hit the unauthenticated limit quickly, so a token
is strongly recommended.

**Steps:**

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a name (e.g. `enpm611-exercise`)
4. Under **Scopes**, check **`public_repo`** only — nothing else is needed
5. Click **Generate token** and copy it immediately (GitHub only shows it once)

**Store the token as an environment variable** — never hard-code it in your
script:

```bash
# macOS / Linux
export GITHUB_TOKEN="your_token_here"

# Windows (Command Prompt)
set GITHUB_TOKEN=your_token_here

# Windows (PowerShell)
$env:GITHUB_TOKEN="your_token_here"
```

In your Python script, read it like this:

```python
import os
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
```

### 3. Verify your setup

Make sure the venv is active (`source .venv/bin/activate`), then run:

```python
import requests, os

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

response = requests.get(
    "https://api.github.com/repos/psf/requests/issues/1",
    headers=HEADERS
)
print(response.status_code)   # should print 200
print(response.json()["title"])
```

If you see `200` and a title, you are ready to start.

---

## The Exercise

All three tiers work with the same repository (`psf/requests`) and build toward
the same goal: a script called **`trace_graph.py`** that maps Issues to the PRs
and commits that resolve them.

Commit your work to `github.com/[org]/enpm611-exercise-02`.

---

### 🟢 Starter

**Goal:** Fetch open and closed Issues from `psf/requests` and display them in a
readable format.

Write `trace_graph.py` that:

1. Fetches the **20 most recently closed Issues** from `psf/requests` using the
   GitHub API
2. For each Issue, prints its number, title, and state (`open` / `closed`)
3. Skips any items that are Pull Requests (the GitHub API returns PRs mixed in
   with Issues — filter them out using the `"pull_request"` key)

**Expected output (format):**

```
#3330  closed  "Requests 2.32.3"
#3329  closed  "CookieJar not working with same domain, different ports"
...
```

**Useful API endpoint:**

```
GET https://api.github.com/repos/psf/requests/issues?state=closed&per_page=20
```

**Hint — filtering out PRs:**

```python
for item in response.json():
    if "pull_request" in item:
        continue   # skip PRs
    # process the issue here
```

---

### 🟡 Intermediate

**Goal:** For each Issue, find whether a Pull Request exists that references it —
and report which Issues have no linked PR.

Extend `trace_graph.py` so that for each of the 20 closed Issues from the
Starter tier, it:

1. Searches the Issue's **timeline** for any cross-referenced Pull Request using
   the GitHub API
2. Records the PR number and title if one is found, or `None` if not
3. Prints a traceability report with two sections:

```
=== TRACED Issues (Issue → PR) ===
#3329  →  PR #3331  "Fix cookie handling for same-domain, different-port URLs"
#3320  →  PR #3322  "Update charset_normalizer dependency"
...

=== UNTRACED Issues (no linked PR found) ===
#3315  "Question about timeout behavior"
...
```

**Useful API endpoint for an Issue's timeline:**

```
GET https://api.github.com/repos/psf/requests/issues/{issue_number}/timeline
```

You will need to set an extra header to use the timeline API:

```python
TIMELINE_HEADERS = {
    **HEADERS,
    "Accept": "application/vnd.github.mockingbird-preview+json"
}
```

Look for events where `event == "cross-referenced"` and the source is a Pull
Request (`source.issue.pull_request` exists).

---

### 🔴 Stretch

**Goal:** Extend the report to include commits, output a Mermaid graph, and
surface a gap analysis.

Extend `trace_graph.py` so that it also:

1. **Fetches the merge commit** for each traced PR (available as
   `merge_commit_sha` on the PR object) and adds the short SHA and commit
   message to the traceability record

2. **Writes a Mermaid flowchart** to `trace_report.md` showing the chain
   `Issue → PR → Commit` for every traced Issue. Example node format:

   ```
   graph TD
     I3329["Issue #3329 - Cookie bug"] --> PR3331["PR #3331"]
     PR3331 --> C1a2b3c["commit 1a2b3c"]
   ```

3. **Writes a gap analysis section** in `trace_report.md` listing:
   - Issues with no linked PR ("untraced requirements")
   - PRs where `merge_commit_sha` is `null` ("merged without a recorded commit")

4. **Prints a summary line** to the console:

   ```
   Analyzed 20 issues: 14 traced, 6 untraced. 
   Gap rate: 30%. See trace_report.md for full report.
   ```

---

## Deliverables by Tier

| Tier | File(s) to commit |
| ---- | ----------------- |
| 🟢 Starter | `trace_graph.py` |
| 🟡 Intermediate | `trace_graph.py` (extended) |
| 🔴 Stretch | `trace_graph.py` (extended) + `trace_report.md` |

---

## Key Tools and References

| Tool / Resource | Purpose |
| --------------- | ------- |
| `requests` (pip) | Make HTTP calls to the GitHub API |
| `os.environ` (stdlib) | Read your GitHub token safely |
| [GitHub REST API — Issues](https://docs.github.com/en/rest/issues/issues) | List and fetch Issues |
| [GitHub REST API — Timeline](https://docs.github.com/en/rest/issues/timeline) | Find cross-referenced PRs |
| [GitHub REST API — Pulls](https://docs.github.com/en/rest/pulls/pulls) | Fetch PR details and merge commit |
| Mermaid syntax reference | [mermaid.js.org](https://mermaid.js.org/syntax/flowchart.html) |

---

## Connections to Class Project

The gap analysis you build here — Issues with no linked PR — is a direct model
for the requirements coverage check you can run on your own class project repo.
Any Issue that was never closed by a PR is a requirement that was either never
implemented or never tracked. Both are engineering failures that traceability
makes visible.
