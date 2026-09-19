# -*- coding: utf-8 -*-
"""
generate_sample_docs.py — the test images of Chapter 10.

Three visual documents, deterministic, illustrating the frontier between OCR and
vision:

    clean_scan.png — a "clean" scanned note, plain text on a light ground.
        OCR is enough: the case where a vision model is unnecessary.

    electrical_plan.png — a building's electrical plan (Julien, line 4).
        OCR recovers only isolated markers (T1, A4, V2 and so on); the MEANING is
        in the spatial arrangement. A vision model is required.

    temperature_chart.png — a temperature curve (the paradox of the chart).
        Very little text, but a trend and a peak. The information is in the
        SHAPE, not in the words.

Deterministic and reproducible. Run before the labs:
    python generate_sample_docs.py

Dependencies: Pillow, matplotlib.
"""

from pathlib import Path

DOCS = Path(__file__).resolve().parent / "sample_docs"
DOCS.mkdir(exist_ok=True)


def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    names = (["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 1. The clean scan — OCR is enough
# ---------------------------------------------------------------------------
def generate_clean_scan() -> None:
    from PIL import Image, ImageDraw

    w, h = 800, 560
    img = Image.new("RGB", (w, h), "#f7f6f2")  # a faint paper tone
    d = ImageDraw.Draw(img)

    # Plain, well-contrasted text: ideal for OCR.
    lines = [
        ("MAINTENANCE NOTE", 34, True),
        ("", 10, False),
        ("Reference: NOTE-2026-014", 22, False),
        ("Date: 2026-01-15", 22, False),
        ("", 8, False),
        ("Battery BAT005 on line 4 is critical.", 22, False),
        ("Measured voltage: 10.9 V.", 22, False),
        ("Action: immediate replacement required.", 22, False),
        ("Technician: Nguyen.", 22, False),
    ]
    y = 50
    for text, size, bold in lines:
        if text:
            d.text((60, y), text, fill="#1a1a1a", font=_font(size, bold))
        y += size + 16

    out = DOCS / "clean_scan.png"
    img.save(out)
    print(f"  + {out.name}")


# ---------------------------------------------------------------------------
# 2. The electrical plan — OCR fails, vision is required
# ---------------------------------------------------------------------------
def generate_electrical_plan() -> None:
    from PIL import Image, ImageDraw

    w, h = 800, 600
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)

    # The frame of the plan.
    d.rectangle([20, 20, w - 20, h - 20], outline="#222222", width=3)
    d.text((30, 28), "ELECTRICAL PLAN - LINE 4", fill="#222222", font=_font(18, True))

    # The main distribution board, a rectangle, and the circuits leaving it.
    # The MEANING is in the connections, not in the few labels.
    d.rectangle([60, 120, 180, 240], outline="#003366", width=3)
    d.text((78, 165), "T1", fill="#003366", font=_font(22, True))

    # Three circuits leaving the board towards equipment.
    equipment = [
        (520, 140, "A4"),   # a cabinet
        (520, 300, "V2"),   # a variable-speed drive
        (520, 460, "M1"),   # a motor
    ]
    for (ex, ey, marker) in equipment:
        d.rectangle([ex, ey, ex + 90, ey + 70], outline="#660000", width=3)
        d.text((ex + 30, ey + 22), marker, fill="#660000", font=_font(22, True))
        # The connection from board T1: broken lines are the cabling.
        d.line([180, 180, 360, 180], fill="#000000", width=2)
        d.line([360, 180, 360, ey + 35], fill="#000000", width=2)
        d.line([360, ey + 35, ex, ey + 35], fill="#000000", width=2)

    # A temperature sensor, wired to the V2 drive.
    d.ellipse([400, 320, 440, 360], outline="#006600", width=3)
    d.text((408, 330), "C", fill="#006600", font=_font(18, True))
    d.line([440, 340, 520, 335], fill="#006600", width=2)
    d.text((300, 365), "12", fill="#333333", font=_font(16))

    out = DOCS / "electrical_plan.png"
    img.save(out)
    print(f"  + {out.name}")


# ---------------------------------------------------------------------------
# 3. The temperature chart — the paradox
# ---------------------------------------------------------------------------
def generate_chart() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hours = [8, 9, 10, 11, 12, 13, 14, 15, 16]
    temperatures = [42, 48, 55, 63, 72, 80, 78, 70, 60]  # the peak at 13:00 is 80 C

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=110)
    ax.plot(hours, temperatures, marker="o", color="#c0392b", linewidth=2)
    ax.set_title("Motor M1 temperature — the day of 2026-01-15")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Temperature (C)")
    ax.grid(True, alpha=0.3)
    ax.axhline(75, color="#888888", linestyle="--", linewidth=1)
    ax.annotate("threshold 75 C", xy=(8.1, 76), color="#555555", fontsize=9)

    out = DOCS / "temperature_chart.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  + {out.name}")


def main() -> None:
    print("Generating the Chapter 10 test images:")
    generate_clean_scan()
    generate_electrical_plan()
    generate_chart()
    print(f"\nDone. Images available in: {DOCS}")


if __name__ == "__main__":
    main()
