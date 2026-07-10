# -weekly-privacy-reports
# State Privacy Digest

A weekly digest of US state privacy law developments, published by [Orion Private](https://orionprivate.com). Each issue covers a seven-day window: legislation, effective dates, rulemaking, enforcement, and court decisions, edited to what changes compliance planning.

## How it works

A GitHub Actions workflow runs weekly. `draft_digest.py` loads the editorial standards, gathers intake through web search, and produces a first draft. Every draft is then reviewed, verified against primary sources, edited, and approved by a human before publication. Nothing ships unreviewed.

The drafting rules are data, not code. The pipeline reads them at run time from `standards/`, so editorial changes never require a code change.

## Repository map

```
digest-bot/
├── standards/
│   ├── editorial_standard.md   what to write, sections, gates, budgets
│   ├── source_hierarchy.md     how evidence is ranked and cited
│   ├── tag_taxonomy.md         the allowed tags
│   └── style_guide.md          voice, wording, formatting
├── draft_digest.py             the drafter
├── digests/                    published issues
└── logs/                       run logs, not committed
```

## Editorial principles

Every reported item rests on a dated official act inside the coverage window. Claims are stated at the strength the evidence bears. Primary sources outrank secondary ones. Items considered and excluded are listed by name with the reason, because the value of a digest is what it leaves out.

## Running it

Requires an `ANTHROPIC_API_KEY` secret and Python with `requests`.

```
python draft_digest.py
```

Drafts are written to `digests/`. The full model output for each run is written to `logs/` for review and should not be committed. Add `logs/` to `.gitignore`.
