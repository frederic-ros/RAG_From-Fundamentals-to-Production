# -*- coding: utf-8 -*-
"""
Lab 11-6 — The email funnel: processing the asynchronous flow (Julien)

Learning objective
------------------
After the web and the feeds, email is the most critical live source in a
business: part of an organisation's memory exists nowhere else — decisions,
arbitrations, justifications. But an email is a complex object: strict metadata,
a body often duplicated (text and HTML), signatures and legal notices to
discard, attachments to extract and to LINK to the message, on pain of losing
the context.

This lab reads local, deterministic .eml files with no connection; the reader can
plug the same logic into imaplib for a real mailbox. Each email becomes a JSON
document with source_type="email", its attachments linked in the metadata.

No API key. Dependencies: email, beautifulsoup4 (standard library plus bs4).
Run generate_fixtures.py first.
"""

import email
import json
import re
from email import policy
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

FIX = Path(__file__).resolve().parent / "fixtures"
ATTACH_DIR = Path(__file__).resolve().parent / "attachments"
ATTACH_DIR.mkdir(exist_ok=True)

# The markers that begin a signature or a legal notice: the text is cut before.
# Both languages are kept, because a real mailbox is rarely monolingual.
SIGNATURE_MARKERS = [
    re.compile(r"^--\s*$"),
    re.compile(r"this email is confidential", re.IGNORECASE),
    re.compile(r"ce (?:courriel|message) est confidentiel", re.IGNORECASE),
]


# Attachments to ignore: the small images that belong to a signature.
def is_signature_image(name: str, size: int) -> bool:
    return name.lower().endswith((".png", ".gif", ".jpg", ".jpeg")) and size < 10_000


def extract_body(msg) -> str:
    """Prefer the plain text; failing that, convert the HTML to text."""
    text = None
    html = None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if part.is_attachment():
                continue
            if ctype == "text/plain" and text is None:
                text = part.get_content()
            elif ctype == "text/html" and html is None:
                html = part.get_content()
    else:
        if msg.get_content_type() == "text/html":
            html = msg.get_content()
        else:
            text = msg.get_content()

    if text is None and html is not None:
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return text or ""


def cut_signature(body: str) -> str:
    """Cut the text before the first signature or confidentiality notice."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if any(m.search(line) for m in SIGNATURE_MARKERS):
            return "\n".join(lines[:i]).strip()
    # If the body came from the HTML, a single line, cut on the legal notice.
    for m in SIGNATURE_MARKERS:
        found = m.search(body)
        if found:
            return body[:found.start()].strip()
    return body.strip()


def date_iso(msg) -> str:
    """Convert the sending date to ISO 8601 format."""
    dt = msg.get("Date")
    if not dt:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(dt)
        return parsed.isoformat()
    except Exception:
        return dt


def extract_attachments(msg, message_id: str) -> List[Dict]:
    """Extract the attachments, bar signature images, write them, link them."""
    attachments = []
    for part in msg.iter_attachments():
        name = part.get_filename() or "attachment"
        data = part.get_payload(decode=True) or b""
        if is_signature_image(name, len(data)):
            continue
        # A safe file name, prefixed by the message id.
        key = re.sub(r"[^A-Za-z0-9_.-]", "_", message_id.strip("<>"))
        path = ATTACH_DIR / f"{key}__{name}"
        path.write_bytes(data)
        attachments.append({
            "name": name,
            "type": part.get_content_type(),
            "size_bytes": len(data),
            "path": str(path.relative_to(Path(__file__).resolve().parent)),
        })
    return attachments


def process_email(eml_path: Path) -> Dict:
    """Turn a .eml into a JSON document with its attachments linked."""
    msg = email.message_from_bytes(eml_path.read_bytes(), policy=policy.default)
    message_id = msg.get("Message-ID", eml_path.name)

    body = cut_signature(extract_body(msg))
    attachments = extract_attachments(msg, message_id)

    return {
        "id": message_id,
        "type": "email",
        "subject": msg.get("Subject", ""),
        "content": body,
        "metadata": {
            "source_type": "email",
            "sender": msg.get("From", ""),
            "recipient": msg.get("To", ""),
            "date": date_iso(msg),
            "message_id": message_id,
            "attachments": attachments,
        },
    }


def main() -> None:
    print("=" * 78)
    print("Lab 11-6 — The email funnel: processing the asynchronous flow (Julien)")
    print("=" * 78)

    if not FIX.exists():
        print("\nFixtures not found. Run this first: python generate_fixtures.py")
        return

    emls = sorted(FIX.glob("*.eml"))
    documents = []
    seen = set()

    for path in emls:
        doc = process_email(path)
        # Deduplication by the immutable Message-ID.
        if doc["id"] in seen:
            continue
        seen.add(doc["id"])
        documents.append(doc)

        print(f"\n--- {path.name} ---")
        print(f"  Subject   : {doc['subject']}")
        print(f"  Sender    : {doc['metadata']['sender']}")
        print(f"  ISO date  : {doc['metadata']['date']}")
        print("  Body, with the signature cut away:")
        print(f"    \"{doc['content'][:90]}…\"")
        attachments = doc["metadata"]["attachments"]
        if attachments:
            for a in attachments:
                print(f"  Attached  : {a['name']} ({a['type']}, {a['size_bytes']} bytes) "
                      f"-> {a['path']}")
        else:
            print("  Attached  : (none kept)")

    out = FIX / "normalised_emails.json"
    out.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name} ({len(documents)} emails)")

    print("\n" + "=" * 78)
    print("WHAT THE EMAIL FUNNEL DOES")
    print("=" * 78)
    print("- It prefers the plain text, or converts the HTML — never both, duplicated.")
    print("- It cuts the signatures and confidentiality notices: the postal noise.")
    print("- It extracts the useful attachments and LINKS them to the parent message.")
    print("- It deduplicates by Message-ID and dates in ISO 8601 format.")

    print("\nWHAT TO REMEMBER")
    print("- Indexing an email without its attachment destroys the context of the answer.")
    print("- Email knowledge is precious but carries no status: it has to be governed.")
    print("- Like everything else, email arrives at the same JSON document.")


if __name__ == "__main__":
    main()
