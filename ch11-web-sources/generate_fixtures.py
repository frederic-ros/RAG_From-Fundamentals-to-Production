# -*- coding: utf-8 -*-
"""
generate_fixtures.py — the live test sources of Chapter 11.

The network is not always available, nor reproducible. Deterministic LOCAL
sources are generated instead, faithful to what the real web produces, so that
the labs can be run and checked with no connection. The reader can afterwards
point these same labs at real URLs, real feeds and real mailboxes.

Produced in fixtures/:

    web pages (noisy HTML: menus, adverts, banners, footers):
        rule_page_v1.html — a compliance rule, the "2024" version (signal plus noise).
        rule_page_v2.html — the same page, updated for "2026" (the rate changes).
        datasheet_page.html — a supplier datasheet (Julien).

    feed:
        news_feed.xml — an RSS feed of 3 regulatory news items.

    emails:
        datasheet_mail.eml — a multipart email (text and HTML) with a signature, a
            confidentiality notice and a PDF attachment.
        simple_mail.eml — a plain text email.

    local documents (for the merge of Lab 11-1):
        rule_pdf_2024.json — a "local PDF" fragment dated 2024, yesterday's rate.

Deterministic. Run before the labs: python generate_fixtures.py
"""

from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime, timezone
import json
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures"
FIX.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Web pages: a noisy template — menu, advert, content, footer
# ---------------------------------------------------------------------------
def page_html(title: str, main_content: str) -> str:
    """A realistic template: a lot of noise around one useful <article>."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} — Regulatory Portal</title>
  <meta name="description" content="The official portal">
</head>
<body>
  <header class="site-header">
    <div class="logo">REGULATORY PORTAL</div>
    <nav class="main-nav">
      <ul>
        <li><a href="/home">Home</a></li>
        <li><a href="/texts">Texts</a></li>
        <li><a href="/news">News</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
    </nav>
  </header>

  <aside class="sidebar">
    <div class="ad-banner">ADVERTISEMENT — Train up on compliance!</div>
    <div class="widget">Popular articles: A, B, C</div>
  </aside>

  <div class="breadcrumb">Home &gt; Texts &gt; {title}</div>

  <main>
    <article>
      <h1>{title}</h1>
      {main_content}
    </article>
  </main>

  <footer class="site-footer">
    <div>© 2026 Regulatory Portal — Legal notice — Terms</div>
    <div>Follow us: social media</div>
    <nav><a href="/sitemap">Site map</a> | <a href="/gdpr">GDPR</a></nav>
  </footer>
  <script>console.log("tracker");</script>
</body>
</html>"""


def generate_pages() -> None:
    # The 2024 version: the rate is 4.2%.
    content_v1 = """
      <p class="date">Published on 2024-03-01</p>
      <p>This rule sets the rate applicable to compliance files.</p>
      <h2>Applicable rate</h2>
      <p>The applicable rate is 4.2%. This rate applies from publication.</p>
      <h2>Scope</h2>
      <p>The rule covers every file submitted through the portal.</p>
      <ul><li>New files</li><li>Renewals</li></ul>
    """
    # The 2026 version: the rate is raised to 4.7% by the reform.
    content_v2 = """
      <p class="date">Published on 2026-06-01</p>
      <p>This rule sets the rate applicable to compliance files.</p>
      <h2>Applicable rate</h2>
      <p>The applicable rate is 4.7%. A reform raised this rate from June 2026.</p>
      <h2>Scope</h2>
      <p>The rule covers every file submitted through the portal.</p>
      <ul><li>New files</li><li>Renewals</li><li>Files in progress</li></ul>
    """
    datasheet = """
      <p class="date">Published on 2026-02-15</p>
      <p>Technical datasheet for the V2 drive on line 4.</p>
      <h2>Parameters</h2>
      <p>Nominal voltage: 400 V. Maximum temperature: 75 C.</p>
      <h2>Maintenance</h2>
      <p>Check the tightness of the connections every six months.</p>
    """
    (FIX / "rule_page_v1.html").write_text(
        page_html("Compliance rule", content_v1), encoding="utf-8")
    (FIX / "rule_page_v2.html").write_text(
        page_html("Compliance rule", content_v2), encoding="utf-8")
    (FIX / "datasheet_page.html").write_text(
        page_html("V2 drive datasheet", datasheet), encoding="utf-8")
    print("  + rule_page_v1.html, rule_page_v2.html, datasheet_page.html")


# ---------------------------------------------------------------------------
# The RSS feed
# ---------------------------------------------------------------------------
def generate_stream() -> None:
    items = [
        ("Reform of the compliance rate", "https://portal.example/news/rate-reform",
         "The rate rises to 4.7% in June 2026.", "Mon, 01 Jun 2026 08:00:00 +0000"),
        ("New submission procedure", "https://portal.example/news/submission",
         "The submission procedure is simplified.", "Tue, 15 Apr 2026 09:30:00 +0000"),
        ("Forms updated", "https://portal.example/news/forms",
         "The 2026 forms are available.", "Wed, 12 Mar 2026 10:00:00 +0000"),
    ]
    items_xml = "\n".join(f"""    <item>
      <title>{t}</title>
      <link>{link}</link>
      <description>{desc}</description>
      <pubDate>{date}</pubDate>
      <guid>{link}</guid>
    </item>""" for (t, link, desc, date) in items)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Regulatory Portal — News</title>
    <link>https://portal.example/news</link>
    <description>The regulatory news feed</description>
{items_xml}
  </channel>
</rss>"""
    (FIX / "news_feed.xml").write_text(rss, encoding="utf-8")
    print("  + news_feed.xml")


# ---------------------------------------------------------------------------
# Emails (.eml)
# ---------------------------------------------------------------------------
def generate_emails() -> None:
    # A multipart email with a PDF attachment: a tiny but valid PDF.
    pdf_minimal = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Root 1 0 R/Size 4>>\nstartxref\n0\n%%EOF\n"
    )

    msg = EmailMessage()
    msg["From"] = "supplier@example.com"
    msg["To"] = "julien@tech-orleans.example"
    msg["Subject"] = "V2 drive datasheet update"
    msg["Date"] = format_datetime(datetime(2026, 2, 15, 14, 30, tzinfo=timezone.utc))
    msg["Message-ID"] = "<datasheet-v2-2026@example.com>"

    text_body = (
        "Hello Julien,\n\n"
        "Please find attached the updated datasheet for the V2 drive. "
        "The maximum temperature rises to 75 C.\n\n"
        "Kind regards,\n"
        "The technical department\n"
        "-- \n"
        "Technical Department | Supplier Ltd\n"
        "Tel: 01 23 45 67 89 | www.supplier.example\n"
        "This email is confidential and intended solely for the addressee. "
        "If you are not the intended recipient, please delete it.\n"
    )
    html_body = (
        "<html><body>"
        "<p>Hello Julien,</p>"
        "<p>Please find attached the updated datasheet for the V2 drive. "
        "The maximum temperature rises to <b>75 C</b>.</p>"
        "<p>Kind regards,<br>The technical department</p>"
        "<hr>"
        '<div class="signature">'
        "<img src=\"logo.png\" alt=\"logo\"> Technical Department | Supplier Ltd<br>"
        "Tel: 01 23 45 67 89 | www.supplier.example"
        "</div>"
        "<p style=\"color:gray;font-size:10px\">This email is confidential and "
        "intended solely for the addressee. If you are not the intended recipient, "
        "please delete it.</p>"
        "</body></html>"
    )
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    msg.add_attachment(pdf_minimal, maintype="application", subtype="pdf",
                       filename="datasheet_V2_2026.pdf")
    (FIX / "datasheet_mail.eml").write_bytes(msg.as_bytes())

    # A simple, text-only email.
    msg2 = EmailMessage()
    msg2["From"] = "sophie@authority.example"
    msg2["To"] = "team@tech-orleans.example"
    msg2["Subject"] = "Reminder: the rate reform"
    msg2["Date"] = format_datetime(datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc))
    msg2["Message-ID"] = "<rate-reminder-2026@authority.example>"
    msg2.set_content(
        "For information, the compliance rate rose to 4.7% in June 2026.\n"
        "Please take this into account for files in progress.\n"
    )
    (FIX / "simple_mail.eml").write_bytes(msg2.as_bytes())
    print("  + datasheet_mail.eml, simple_mail.eml")


# ---------------------------------------------------------------------------
# A local document, a PDF already ingested, for the merge and arbitration of Lab 11-1
# ---------------------------------------------------------------------------
def generate_local_doc() -> None:
    fragment = {
        "id": "rule_pdf_2024",
        "content": "The rate applicable to compliance files is 4.2%.",
        "metadata": {
            "source_type": "pdf",
            "title": "Compliance rule (internal PDF)",
            "date": "2024-03-01",
            "status": "internal",
        },
    }
    (FIX / "rule_pdf_2024.json").write_text(
        json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  + rule_pdf_2024.json")


def main() -> None:
    print("Generating the Chapter 11 live test sources:")
    generate_pages()
    generate_stream()
    generate_emails()
    generate_local_doc()
    print(f"\nDone. Fixtures available in: {FIX}")


if __name__ == "__main__":
    main()
