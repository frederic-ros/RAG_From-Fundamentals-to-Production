# -*- coding: utf-8 -*-
"""
generate_sample_docs.py — builds the test document set of Chapter 6.

Every document is SYNTHETIC, and built around three characters of the book:

  - Claire : a local authority, HR (a service note);
  - Julien : industry, technical (a report with a table of parameters);
  - Sophie : public procurement, legal (a two-column document, with repeated
             running heads and footers).

They are generated deterministically, so they are reproducible and can be
versioned. Run once before the labs:

    python generate_sample_docs.py

Produces, in ./sample_docs:

    claire_service_note.docx      (Lab 6-1: the Word source)
    claire_service_note.html      (Lab 6-1: the same content in HTML)
    claire_service_note.pdf       (Lab 6-1: the same content in native PDF)
    julien_table_report.pdf       (Lab 6-2: a table of technical parameters)
    sophie_contract_2columns.pdf  (Lab 6-3: 2 columns plus repeated heads/footers)
    julien_nameplate.png          (Lab 6-4: a mock equipment nameplate, an image)

Note on the two-column document: the content reads down the LEFT column in full,
then down the right one. A naive parser reads line by line across both columns,
which is precisely the trap Lab 6-3 corrects. The line lengths are chosen so
that the two columns do not overlap; keep them short if you edit the text.

Dependencies: python-docx, reportlab, Pillow.
"""

from pathlib import Path

DOCS = Path(__file__).resolve().parent / "sample_docs"
DOCS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# The shared content of Claire's service note (Lab 6-1)
# ---------------------------------------------------------------------------
NOTE_TITLE = "Service note — Remote work arrangements 2025"
NOTE_META = {
    "author": "Human Resources Department",
    "date": "2025-01-15",
    "reference": "NS-2025-007",
}
NOTE_SECTIONS = [
    ("Purpose",
     "This note sets out the remote work arrangements applicable to all staff "
     "of the authority, with effect from 1 February 2025."),
    ("Number of days",
     "Remote work is authorised up to a limit of two days per week. The days "
     "are agreed with the line manager."),
    ("Eligibility conditions",
     "Staff who have completed their probationary period, and whose duties are "
     "compatible with working at a distance, are eligible."),
    ("Equipment",
     "The authority provides a laptop and a secure connection. The member of "
     "staff undertakes to respect the IT code of practice."),
]


def generate_docx() -> None:
    """Lab 6-1: the service note in Word format."""
    from docx import Document

    doc = Document()
    doc.add_heading(NOTE_TITLE, level=0)

    p = doc.add_paragraph()
    p.add_run(f"Reference: {NOTE_META['reference']}    ").bold = True
    p.add_run(f"Date: {NOTE_META['date']}    ")
    p.add_run(f"Author: {NOTE_META['author']}")

    for title, body in NOTE_SECTIONS:
        doc.add_heading(title, level=1)
        doc.add_paragraph(body)

    out = DOCS / "claire_service_note.docx"
    doc.save(out)
    print(f"  + {out.name}")


def generate_html() -> None:
    """Lab 6-1: the same note, in HTML."""
    sections_html = "\n".join(
        f"  <h2>{title}</h2>\n  <p>{body}</p>"
        for title, body in NOTE_SECTIONS
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="author" content="{NOTE_META['author']}">
  <meta name="date" content="{NOTE_META['date']}">
  <meta name="reference" content="{NOTE_META['reference']}">
  <title>{NOTE_TITLE}</title>
</head>
<body>
  <h1>{NOTE_TITLE}</h1>
  <p class="meta">Reference: {NOTE_META['reference']} —
     Date: {NOTE_META['date']} — Author: {NOTE_META['author']}</p>
{sections_html}
</body>
</html>
"""
    out = DOCS / "claire_service_note.html"
    out.write_text(html, encoding="utf-8")
    print(f"  + {out.name}")


def generate_pdf_note() -> None:
    """Lab 6-1: the same note, as a native PDF with selectable text."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    out = DOCS / "claire_service_note.pdf"
    styles = getSampleStyleSheet()
    story = [Paragraph(NOTE_TITLE, styles["Title"])]
    story.append(Paragraph(
        f"Reference: {NOTE_META['reference']} — Date: {NOTE_META['date']} "
        f"— Author: {NOTE_META['author']}", styles["Normal"]))
    story.append(Spacer(1, 12))
    for title, body in NOTE_SECTIONS:
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(body, styles["Normal"]))
        story.append(Spacer(1, 8))

    SimpleDocTemplate(str(out), pagesize=A4).build(story)
    print(f"  + {out.name}")


def generate_pdf_table() -> None:
    """Lab 6-2: Julien's report, with a table of technical parameters."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    out = DOCS / "julien_table_report.pdf"
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Technical report — the MX compressor family", styles["Title"]),
        Paragraph("Design office — Julien Bauer — 2025-03-02", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(
            "The table below summarises the nominal parameters of the three "
            "models in the range. These values are the reference for technical "
            "support and after-sales.", styles["Normal"]),
        Spacer(1, 12),
    ]

    # The parameter table: model against characteristics.
    data = [
        ["Model", "Max pressure (bar)", "Flow (m3/h)", "Tightening torque (N.m)", "Voltage (V)"],
        ["MX-100", "8.0", "120", "45", "230"],
        ["MX-200", "12.5", "180", "60", "400"],
        ["MX-300", "16.0", "240", "85", "400"],
    ]
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF1F8")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Warning: the maximum pressure of the MX-200, 12.5 bar, must never be "
        "exceeded in continuous operation.", styles["Normal"]))

    SimpleDocTemplate(str(out), pagesize=A4).build(story)
    print(f"  + {out.name}")


def generate_pdf_two_columns() -> None:
    """Lab 6-3: Sophie's procurement document, 2 columns, repeated heads and footers."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    out = DOCS / "sophie_contract_2columns.pdf"
    width, height = A4
    c = canvas.Canvas(str(out), pagesize=A4)

    # Two columns of legal text. The content reads down the LEFT column in
    # full, THEN down the right one. A naive parser reads line by line across
    # both columns: that is the trap Lab 6-3 corrects.
    left_column = [
        "Article 1 - Purpose of the contract.",
        "The purpose of this contract is",
        "the supply and installation of",
        "computer equipment for the",
        "departments of the authority.",
        "It forms part of the programme",
        "to modernise the existing estate.",
        "",
        "Article 2 - Duration.",
        "The contract is concluded for a",
        "period of twenty-four months",
        "from its notification to the",
        "successful contractor.",
    ]
    right_column = [
        "Article 3 - Conditions.",
        "The contractor undertakes to meet",
        "the delivery times set out in",
        "the technical annex to this",
        "contractual document.",
        "Any delay will give rise to",
        "penalties under the agreed scale.",
        "",
        "Article 4 - Termination.",
        "The authority reserves the right",
        "to terminate the contract in the",
        "event of a serious breach of the",
        "contractual obligations.",
    ]

    def draw_page(page_number: int) -> None:
        # The repeated running head: noise to strip in Lab 6-3.
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(2 * cm, height - 1.2 * cm,
                     "PUBLIC CONTRACT No. 2025-MP-014 — TOWN OF VAL-SUR-LOIRE")
        c.line(2 * cm, height - 1.35 * cm, width - 2 * cm, height - 1.35 * cm)

        # The columns.
        c.setFont("Helvetica", 10)
        y0 = height - 3 * cm
        for i, line in enumerate(left_column):
            c.drawString(2 * cm, y0 - i * 0.6 * cm, line)
        for i, line in enumerate(right_column):
            c.drawString(11 * cm, y0 - i * 0.6 * cm, line)

        # The repeated page footer: noise to strip in Lab 6-3.
        c.setFont("Helvetica-Oblique", 8)
        c.line(2 * cm, 1.5 * cm, width - 2 * cm, 1.5 * cm)
        c.drawString(2 * cm, 1.1 * cm,
                     "Confidential document — reproduction prohibited")
        c.drawRightString(width - 2 * cm, 1.1 * cm, f"Page {page_number} / 1")

    draw_page(1)
    c.showPage()
    c.save()
    print(f"  + {out.name}")


def generate_plate_image() -> None:
    """Lab 6-4: a mock equipment nameplate, as a PNG image."""
    from PIL import Image, ImageDraw, ImageFont

    out = DOCS / "julien_nameplate.png"
    w, h = 600, 380
    img = Image.new("RGB", (w, h), "#d9dadb")
    d = ImageDraw.Draw(img)

    def font(size: int):
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except Exception:
            return ImageFont.load_default()

    # The metal frame.
    d.rectangle([10, 10, w - 10, h - 10], outline="#333333", width=4)
    d.rectangle([10, 10, w - 10, 70], fill="#2E75B6")
    d.text((28, 26), "MECATECH — MX-200 COMPRESSOR", fill="white", font=font(22))

    lines = [
        "Reference: MX-200-400V",
        "Serial no.: MT2025-018342",
        "Max pressure: 12.5 bar",
        "Nominal flow: 180 m3/h",
        "Voltage: 400 V three-phase",
        "Power: 15 kW",
        "Year: 2025",
        "Conformity: CE / ISO 1217",
    ]
    yy = 95
    for line in lines:
        d.text((30, yy), line, fill="#111111", font=font(20))
        yy += 33

    # A mock warning symbol.
    d.polygon([(500, 250), (560, 350), (440, 350)], outline="#b00000", width=4)
    d.text((492, 300), "!", fill="#b00000", font=font(34))

    img.save(out)
    print(f"  + {out.name}")


def main() -> None:
    print("Generating the Chapter 6 test documents:")
    generate_docx()
    generate_html()
    generate_pdf_note()
    generate_pdf_table()
    generate_pdf_two_columns()
    generate_plate_image()
    print(f"\nDone. Documents available in: {DOCS}")


if __name__ == "__main__":
    main()
