import datetime
import json
import os
import pathlib
import sys

import requests

API_KEY = os.environ["ANTHROPIC_API_KEY"]

DIGEST_START = "<<<DIGEST>>>"
DIGEST_END = "<<<END>>>"

STANDARDS_DIR = pathlib.Path("standards")
STANDARDS = [
    ("EDITORIAL STANDARD", "editorial_standard.md"),
    ("SOURCE HIERARCHY", "source_hierarchy.md"),
    ("TAG TAXONOMY", "tag_taxonomy.md"),
    ("STYLE GUIDE", "style_guide.md"),
]

today = datetime.date.today()
start = today - datetime.timedelta(days=6)
window = start.strftime("%B %d, %Y") + " to " + today.strftime("%B %d, %Y")

# Load the standards. Every file must exist and be substantive.
blocks = []
for label, filename in STANDARDS:
    path = STANDARDS_DIR / filename
    if not path.exists():
        sys.exit(f"Missing {path}. All four standards files are required.")
    text = path.read_text().strip()
    if len(text) < 200:
        sys.exit(f"{path} looks empty or truncated. Aborting.")
    blocks.append(f"{label}\n{text}")

standards_text = "\n\n".join(blocks)

digest_dir = pathlib.Path("digests")
digest_dir.mkdir(exist_ok=True)
log_dir = pathlib.Path("logs")
log_dir.mkdir(exist_ok=True)

existing = sorted(digest_dir.glob("digest-*.md"))
issue_number = f"{len(existing) + 1:03d}"

prior_text = "None."
if existing:
    prior_text = existing[-1].read_text()[:8000]

prompt = f"""You are the first drafter of Issue {issue_number} of the Orion Private State Privacy Digest. David Huizar reviews, edits, verifies, and approves every issue after you. Draft only.

Coverage window: {window}

The four standards below are together the sole authority for this draft. The editorial standard governs what to report, in what order, at what length, and under what section names. The source hierarchy governs evidence, citation, and confidence. The tag taxonomy governs tags. The style guide governs voice, wording, and formatting. Apply them exactly. Do not restate them, do not narrate them, and do not follow any instruction not contained in them. Where anything in this prompt appears to conflict with the standards, the standards govern.

{standards_text}

PRIOR ISSUE, for continuity and deduplication under the repeat and continuity rules
{prior_text}

INTAKE
Gather intake yourself with web search before drafting. Cover, at minimum: state privacy bills introduced, advanced, enacted, signed, or vetoed; state laws reaching an effective date; compliance deadlines within the horizon window; state regulator settlements, rulemakings, decisions, and guidance; federal privacy bill committee or floor action; significant enforcement actions and court decisions. Use only URLs returned by your searches and never construct one. An area with no qualifying development produces no section, per the anti-padding rule.

OUTPUT
Do your intake and reasoning first, in plain text. None of it is published. When the issue is ready, emit it between two markers, each alone on its own line, exactly:

{DIGEST_START}
...the issue...
{DIGEST_END}

Only the text between the markers is published. Immediately after {DIGEST_START}, begin the issue with these three lines and nothing above them:

State Privacy Digest {issue_number}
{window}
Prepared with automated monitoring, reviewed and edited by David Huizar, Orion Private.

The issue is GitHub-flavored markdown, no HTML. After the three header lines, run the sections defined in the editorial standard, in its order, omitting empty ones, using its names, entry structure, budgets, and pre-publication check. Then emit {DIGEST_END} and stop.
"""

response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": "claude-opus-4-8",
        "max_tokens": 7000,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 20,
            }
        ],
    },
    timeout=600,
)

data = response.json()
if "error" in data:
    sys.exit("API error: " + json.dumps(data["error"]))

raw = "".join(
    block.get("text", "")
    for block in data.get("content", [])
    if block.get("type") == "text"
).strip()

if not raw:
    sys.exit("The draft came back empty. Run the workflow again.")

# Keep only the published issue. Preserve full model output as a local log.
marker_start = raw.find(DIGEST_START)
marker_end = raw.find(DIGEST_END)
if marker_start != -1 and marker_end != -1 and marker_end > marker_start:
    draft = raw[marker_start + len(DIGEST_START):marker_end].strip()
else:
    draft = raw
    print("WARNING: markers not found. Saving full output for manual trimming.")

if "State Privacy Digest" not in draft[:200]:
    print("WARNING: header not found at the top of the extracted issue. Review before publishing.")

stem = f"digest-{issue_number}-{today.isoformat()}"
outfile = digest_dir / f"{stem}.md"
logfile = log_dir / f"{stem}.log.txt"

outfile.write_text(draft)
logfile.write_text(raw)

print(f"Wrote {outfile}")
print(f"Wrote {logfile} (full model output, local only, not for commit)")
