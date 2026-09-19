# -*- coding: utf-8 -*-
"""
generate_sample_docs.py — the test documents of Chapter 8.

The same remote-work agreement exists in THREE formats, with deliberate
divergences — the conflict of the chapter:

    claire_remote_work_agreement.docx — Word, a working DRAFT (Claire)
        2 days a week, dated 2025-01-10, status draft, working conditions.

    julien_remote_work_agreement.pdf — the official APPROVED PDF, 2 columns
        (circulated). 3 days a week, dated 2025-03-15, status approved and in
        force. This is the one that carries authority.

    sophie_remote_work_agreement.pptx — the deck projected in a meeting (Sophie)
        simplified wording, no date, with presenter notes.

The divergences wired in — days, dates, conditions:

  - days        : Word = 2, PDF = 3, deck = "several";
  - date        : Word = 2025-01-10, PDF = 2025-03-15, deck = absent;
  - eligibility : Word "after 6 months", PDF "after the probationary period",
                  deck not stated;
  - fixed days  : only the PDF mentions "days agreed with the manager".

It is the approved official PDF that carries authority: its status, and the more
recent date.

Deterministic and reproducible. Run before the labs:

    python generate_sample_docs.py

Dependencies: python-docx, reportlab, python-pptx.
"""

from pathlib import Path

DOCS = Path(__file__).resolve().parent / "sample_docs"
DOCS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Word — a working draft (Claire): 2 days
# ---------------------------------------------------------------------------
def generate_docx() -> None:
    from docx import Document

    doc = Document()
    doc.add_heading("Remote work agreement", level=0)

    p = doc.add_paragraph()
    p.add_run("Working document — draft    ").bold = True
    p.add_run("Date: 2025-01-10    Author: HR department    Status: draft")

    doc.add_heading("Purpose", level=1)
    doc.add_paragraph(
        "This agreement sets out the remote work arrangements applicable to the "
        "staff of the authority.")

    doc.add_heading("Number of days", level=1)
    doc.add_paragraph(
        "Remote work is authorised up to a limit of two days per week.")

    doc.add_heading("Eligibility", level=1)
    doc.add_paragraph(
        "Staff with at least six months of service are eligible.")

    doc.add_heading("Equipment conditions", level=1)
    doc.add_paragraph(
        "The authority provides the necessary computer equipment.")

    doc.add_heading("Equipment provided", level=2)
    doc.add_paragraph(
        "A laptop and a secure connection are made available.")

    doc.add_heading("Applicable code of practice", level=2)
    doc.add_paragraph(
        "Staff undertake to respect the authority's IT code of practice.")

    out = DOCS / "claire_remote_work_agreement.docx"
    doc.save(out)
    print(f"  + {out.name}")


# ---------------------------------------------------------------------------
# 2. The approved official PDF — 2 columns (circulated): 3 days, carries authority
# ---------------------------------------------------------------------------
def generate_pdf() -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    out = DOCS / "julien_remote_work_agreement.pdf"
    width, height = A4
    c = canvas.Canvas(str(out), pagesize=A4)

    # Columns: the left one in full, THEN the right one. This is the
    # two-column trap of Lab 8-2. Keep the lines short if you edit them, so the
    # columns do not overlap.
    left_column = [
        "Article 1 - Purpose.",
        "This agreement sets out the",
        "remote work arrangements for",
        "the staff of the authority.",
        "",
        "Article 2 - Number of days.",
        "Remote work is authorised up to",
        "a limit of three days per week.",
        "The days are agreed with the",
        "manager.",
    ]
    right_column = [
        "Article 3 - Eligibility.",
        "Staff who have completed their",
        "probationary period are eligible.",
        "",
        "Article 4 - Entry into force.",
        "This agreement, approved in",
        "committee, enters into force on",
        "the date of its publication.",
        "It cancels and replaces any",
        "earlier version.",
    ]

    # The repeated running head: noise to filter out in Lab 8-2.
    # Keep this string SHORT. It is drawn from x = 2 cm, and Lab 8-2 splits the
    # page at the middle to separate the two columns. A longer head crosses that
    # line, so its tail is picked up as a separate right-column line and escapes
    # the noise filter. The French original fitted by a few millimetres; a
    # literal translation did not.
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, height - 1.2 * cm,
                 "REMOTE WORK AGREEMENT — APPROVED — 2025-03-15")
    c.line(2 * cm, height - 1.35 * cm, width - 2 * cm, height - 1.35 * cm)

    c.setFont("Helvetica", 10)
    y0 = height - 3 * cm
    for i, line in enumerate(left_column):
        c.drawString(2 * cm, y0 - i * 0.62 * cm, line)
    for i, line in enumerate(right_column):
        c.drawString(11 * cm, y0 - i * 0.62 * cm, line)

    # The repeated page footer: noise to filter out.
    c.setFont("Helvetica-Oblique", 8)
    c.line(2 * cm, 1.5 * cm, width - 2 * cm, 1.5 * cm)
    c.drawString(2 * cm, 1.1 * cm, "Official document — Human Resources Department")
    c.drawRightString(width - 2 * cm, 1.1 * cm, "Page 1 / 1")

    c.showPage()
    c.save()
    print(f"  + {out.name}")


# ---------------------------------------------------------------------------
# 3. PowerPoint — the meeting deck (Sophie): simplified, with notes
# ---------------------------------------------------------------------------
def generate_pptx() -> None:
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    blank = prs.slide_layouts[6]  # the blank layout

    def add_slide(title: str, bullets, notes: str) -> None:
        slide = prs.slides.add_slide(blank)
        # The title.
        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(1))
        tf = tb.text_frame
        tf.text = title
        tf.paragraphs[0].runs[0].font.size = Pt(28)
        tf.paragraphs[0].runs[0].font.bold = True
        # The bullets.
        body = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(8.5), Inches(4))
        bf = body.text_frame
        for i, bullet in enumerate(bullets):
            p = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
            p.text = "- " + bullet
            p.runs[0].font.size = Pt(18)
        # The presenter notes: hidden text, used in Lab 8-3.
        slide.notes_slide.notes_text_frame.text = notes

    add_slide(
        "Remote work: what is changing",
        ["More flexibility for staff",
         "Several days a week possible",
         "Subject to the manager's agreement"],
        notes=("Meeting presentation of 20 March. Stress the flexibility. The "
               "exact number of days is still being approved: do not announce a "
               "firm figure. Refer people to the official agreement for detail."),
    )
    add_slide(
        "How to take it up",
        ["Make the request to your manager",
         "Equipment provided by the authority",
         "A code of practice to respect"],
        notes=("Remind them that eligibility depends on length of service. "
               "The precise conditions are in the approved HR document."),
    )

    out = DOCS / "sophie_remote_work_agreement.pptx"
    prs.save(out)
    print(f"  + {out.name}")


def main() -> None:
    print("Generating the Chapter 8 test documents:")
    generate_docx()
    generate_pdf()
    generate_pptx()
    print(f"\nDone. Documents available in: {DOCS}")
    print("The divergence wired in: Word = 2 days (draft), PDF = 3 days (approved, "
          "carries authority), deck = simplified with no date.")


if __name__ == "__main__":
    main()
