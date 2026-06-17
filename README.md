# Innovative Hype — AI Newsletter Pipeline

Automated pipeline that researches AI news, drafts a newsletter in the Innovative
Hype brand voice, and publishes to Substack.

## Architecture

```
  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
  │  research.py │ ───▶ │  draft.py    │ ───▶ │  publish.py  │
  │  RSS → JSON  │      │  prompt → MD │      │  SMTP → Sub  │
  └──────────────┘      └──────────────┘      └──────────────┘
       digest.json      newsletter.md       Substack post

  The LLM drafting step (digest → final newsletter) is handled by
  a Hermes cron job that reads newsletter.md and generates the
  finished text in the Innovative Hype voice.
```

## Quick Start

### 1. Configure

```bash
cp config.yaml config.local.yaml
# Edit config.local.yaml and fill in:
#   - substack.posting_address  (your @substack.com secret email)
#   - smtp.username             (Gmail address)
#   - smtp.password             (Gmail App Password — see below)
```

### 2. Test the research stage

```bash
./pipeline.sh --dry-run
# Or individually:
python3 research.py --max-articles 10
python3 draft.py
```

### 3. Publish (when ready)

```bash
# After the Hermes cron agent has generated the final newsletter.md:
python3 publish.py newsletter.md --config config.local.yaml
```

## Files

| File | Purpose |
|------|---------|
| `config.yaml` | Base configuration (RSS feeds, filters, template) |
| `config.local.yaml` | **Create this** — secrets (SMTP, Substack email) |
| `research.py` | Stage 1: RSS aggregation → `digest.json` |
| `draft.py` | Stage 2: Formats digest into LLM prompt → `newsletter.md` |
| `publish.py` | Stage 3: SMTP email to Substack posting address |
| `pipeline.sh` | End-to-end orchestrator |
| `README.md` | This file |

## Dependencies

```bash
pip3 install --break-system-packages feedparser pyyaml
```

All other dependencies (smtplib, json, pathlib, datetime) are Python stdlib.

## Gmail App Password Setup

If you use Gmail with 2FA (recommended):

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password
4. Paste into `config.local.yaml` under `smtp.password`

## Finding Your Substack Posting Address

1. Go to your Substack publication dashboard
2. Settings → Publishing → "Post by email"
3. Copy the secret `@substack.com` email address
4. Paste into `config.local.yaml` under `substack.posting_address`

## Hermes Cron Setup

The pipeline is designed to run via Hermes cron jobs. There are two modes:

### Option A: Two-stage cron (recommended)

**Job 1 — Research (daily, 6:00 AM UTC):**
```
hermes cronjob create \
  --name "IH-Research" \
  --schedule "0 6 * * *" \
  --script "pipeline.sh" \
  --args "--cron-research" \
  --workdir "/Users/micah/.hermes/kanban/workspaces/t_533bf449"
```

**Job 2 — Draft + Publish (daily, 6:30 AM UTC):**
This is an LLM-powered job. The Hermes agent:
1. Reads `digest.json` from the research output
2. Generates a newsletter in Innovative Hype voice
3. Saves it as `newsletter.md`
4. Runs `python3 publish.py newsletter.md --config config.local.yaml`

### Option B: Single cron (simpler, requires SMTP creds in the agent)

Single daily job that runs `pipeline.sh` and the Hermes agent handles drafting
and publishing in one step.

## Manual Publishing Workflow

If you prefer to review before publishing:

```bash
# 1. Research
python3 research.py

# 2. Generate draft prompt
python3 draft.py

# 3. Edit the draft
#    Open newsletter.md, replace the prompt with your final newsletter text.
#    The top section has source articles; the bottom has writing instructions.

# 4. Publish
python3 publish.py newsletter.md --config config.local.yaml
```

## RSS Feed Sources (17 feeds)

| Tier | Source | Status |
|------|--------|--------|
| 1 | TechCrunch AI | ✅ |
| 1 | The Verge AI | ✅ |
| 1 | VentureBeat AI | ✅ |
| 1 | MIT Technology Review | ✅ |
| 1 | Wired AI | ✅ |
| 1 | Ars Technica | ✅ |
| 2 | arXiv CS.AI | ✅ |
| 2 | arXiv CS.CL | ✅ |
| 2 | Simon Willison's Blog | ✅ |
| 2 | Google AI Blog | ✅ |
| 2 | OpenAI Blog | ✅ |
| 2 | DeepMind Blog | ❌ (XML parse error) |
| 2 | Anthropic Research | ❌ (not an RSS feed) |
| 2 | Meta AI Blog | ❌ (XML parse error) |
| 3 | Hacker News (AI) | ✅ |
| 3 | Hacker News | ✅ |
| 3 | Import AI (Substack) | ✅ |

To fix broken feeds: submit the correct RSS/Atom URL and update `config.yaml`.

## Troubleshooting

**"No module named feedparser":**
```bash
pip3 install --break-system-packages feedparser
```

**"No module named yaml":**
```bash
pip3 install --break-system-packages pyyaml
```

**SMTP authentication failed:**
- Make sure you're using a Gmail App Password, not your regular password
- Check that 2FA is enabled: https://myaccount.google.com/security

**Empty digest (0 articles):**
- Check your internet connection
- Increase `filter.max_age_hours` in config.yaml (default: 48)
- Some feeds may be rate-limiting — wait and retry

**Substack post not appearing:**
- Check spam folder of the Substack posting address
- It can take 2-5 minutes for email-to-post conversion
- Verify the posting address in Substack → Settings → Publishing

## Brand Voice Reference

From the Innovative Hype brand audit (parent task t_124f75d6):

- **Tone**: Conversational, opinionated, first-person
- **Style**: Cultural commentary weaving tech, sports, society
- **Format**: Roundup style for news aggregation, long-form analysis
- **Topics**: AI/tech, sports, Web3/crypto, economics, media/culture
- **Cadence target**: Weekly (current: sporadic, months between posts)
