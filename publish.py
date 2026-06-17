#!/usr/bin/env python3
"""
Innovative Hype — Stage 3: Substack Publisher
==============================================
Reads a newsletter Markdown file and publishes it to Substack
via email (SMTP to the publication's secret @substack.com address).

Usage:
    python3 publish.py newsletter.md                    # publish now
    python3 publish.py newsletter.md --dry-run          # preview only
    python3 publish.py newsletter.md --schedule "2026-05-20 09:00"  # schedule
    python3 publish.py newsletter.md --config config.local.yaml
"""

import sys
import os
import re
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone


# ── Config loading ──────────────────────────────────────────────────────────

def load_config(config_path="config.yaml"):
    """Load YAML or JSON config."""
    path = Path(config_path)
    if not path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    except ImportError:
        import json
        with open(path) as f:
            return json.load(f)


# ── Validation ──────────────────────────────────────────────────────────────

def validate_config(config):
    """Check that required config fields are set."""
    issues = []

    substack_addr = config.get("substack", {}).get("posting_address", "")
    if "CHANGEME" in substack_addr or not substack_addr:
        issues.append("substack.posting_address not configured")

    smtp = config.get("smtp", {})
    if "CHANGEME" in smtp.get("username", "") or not smtp.get("username"):
        issues.append("smtp.username not configured")
    if "CHANGEME" in smtp.get("password", "") or not smtp.get("password"):
        issues.append("smtp.password not configured")

    return issues


# ── Email building ──────────────────────────────────────────────────────────

def build_email(markdown_body, config, schedule=None):
    """Build MIME email for Substack posting."""
    substack = config["substack"]
    smtp_cfg = config["smtp"]

    # Extract title from first H1 in markdown
    title_match = re.search(r"^#\s+(.+)$", markdown_body, re.MULTILINE)
    if title_match:
        subject = title_match.group(1).strip()
    else:
        # Use filename date as fallback
        subject = f"Innovative Hype — {datetime.now().strftime('%B %d, %Y')}"

    # Schedule prefix
    if schedule:
        subject = f"[Schedule: {schedule}] {subject}"

    # Substack email publishing: body is markdown, sent as plain text
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["username"]
    msg["To"] = substack["posting_address"]
    msg.attach(MIMEText(markdown_body, "plain", "utf-8"))

    return msg, subject


# ── SMTP Send ───────────────────────────────────────────────────────────────

def send_email(msg, config, dry_run=False):
    """Send email via SMTP. Returns (success, message)."""
    smtp_cfg = config["smtp"]

    if dry_run:
        return True, "DRY RUN — email not sent"

    try:
        with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=30) as server:
            server.starttls()
            server.login(smtp_cfg["username"], smtp_cfg["password"])
            server.send_message(msg)
        return True, "Email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed — check username/password (use App Password if 2FA enabled)"
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to {smtp_cfg['host']}:{smtp_cfg['port']} — check network and firewall"
    except Exception as e:
        return False, f"SMTP error: {e}"


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Publish a newsletter to Substack via email"
    )
    parser.add_argument("newsletter", help="Path to newsletter Markdown file")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--schedule", help="Schedule for later (format: 'YYYY-MM-DD HH:MM')")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Validate
    issues = validate_config(config)
    if issues:
        print("❌ Configuration incomplete. The following are missing:")
        for issue in issues:
            print(f"   - {issue}")
        print(f"\nCopy config.yaml to config.local.yaml and fill in your secrets.")
        if args.dry_run:
            print("Continuing in dry-run mode...\n")
        else:
            sys.exit(1)

    # Read newsletter
    newsletter_path = Path(args.newsletter)
    if not newsletter_path.exists():
        print(f"ERROR: Newsletter file not found: {args.newsletter}")
        sys.exit(1)

    markdown_body = newsletter_path.read_text(encoding="utf-8")

    # Build email
    msg, subject = build_email(markdown_body, config, args.schedule)

    # Preview
    print("=" * 60)
    print(f"FROM:    {msg['From']}")
    print(f"TO:      {msg['To']}")
    print(f"SUBJECT: {subject}")
    print(f"BODY:    {len(markdown_body)} chars ({markdown_body.count(chr(10))+1} lines)")
    print("=" * 60)

    if args.dry_run:
        print("\n--- Newsletter Preview (first 800 chars) ---")
        print(markdown_body[:800])
        if len(markdown_body) > 800:
            print(f"\n... ({len(markdown_body) - 800} more chars)")
        print("\n✅ Dry run complete — no email was sent.")
        return

    # Confirm
    print(f"\nAbout to publish to Substack. Proceed? [y/N] ", end="")
    confirm = input().strip().lower()
    if confirm not in ("y", "yes"):
        print("Aborted.")
        return

    # Send
    success, message = send_email(msg, config)
    if success:
        print(f"\n✅ Published! {message}")
        print(f"   Check innovativehype.substack.com in a few minutes.")
    else:
        print(f"\n❌ Failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
