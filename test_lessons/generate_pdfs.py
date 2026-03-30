"""Generate PDF versions of the test lesson TXT files using PyMuPDF."""
import fitz
import os

LESSONS_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_SIZE_TITLE = 16
FONT_SIZE_HEADING = 13
FONT_SIZE_BODY = 10.5
LINE_HEIGHT = 14
MARGIN_LEFT = 56
MARGIN_TOP = 56
MARGIN_BOTTOM = 56
MARGIN_RIGHT = 56


def txt_to_pdf(txt_path: str, pdf_path: str):
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    y = MARGIN_TOP
    max_width = 612 - MARGIN_LEFT - MARGIN_RIGHT

    for line in lines:
        line = line.rstrip("\n")

        # Determine formatting
        if line.startswith("===") or not line:
            if not line:
                y += LINE_HEIGHT * 0.5
            continue

        if line.startswith("SECTION") or (line.isupper() and len(line) > 10):
            font_size = FONT_SIZE_HEADING
            font_name = "helv"
            y += LINE_HEIGHT * 0.5
        elif line == lines[0].rstrip("\n") or (
            "Complete Lesson" in line or "FUNDAMENTALS" in line.upper()
        ):
            font_size = FONT_SIZE_TITLE
            font_name = "helv"
        else:
            font_size = FONT_SIZE_BODY
            font_name = "helv"

        # Word-wrap long lines
        words = line.split()
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip()
            tw = fitz.get_text_length(test, fontname=font_name, fontsize=font_size)
            if tw > max_width and current_line:
                # Flush current_line
                if y + font_size > 792 - MARGIN_BOTTOM:
                    page = doc.new_page(width=612, height=792)
                    y = MARGIN_TOP
                page.insert_text(
                    (MARGIN_LEFT, y),
                    current_line,
                    fontname=font_name,
                    fontsize=font_size,
                    color=(0.1, 0.1, 0.18),
                )
                y += LINE_HEIGHT
                current_line = word
            else:
                current_line = test

        if current_line:
            if y + font_size > 792 - MARGIN_BOTTOM:
                page = doc.new_page(width=612, height=792)
                y = MARGIN_TOP
            color = (0.02, 0.15, 0.4) if font_size > FONT_SIZE_BODY else (0.1, 0.1, 0.18)
            page.insert_text(
                (MARGIN_LEFT, y),
                current_line,
                fontname=font_name,
                fontsize=font_size,
                color=color,
            )
            y += LINE_HEIGHT

    doc.save(pdf_path)
    doc.close()
    print(f"Created: {pdf_path} ({doc.page_count if False else 'done'})")


if __name__ == "__main__":
    for name in ["chemistry_chemical_bonding", "dsp_fundamentals"]:
        txt_path = os.path.join(LESSONS_DIR, f"{name}.txt")
        pdf_path = os.path.join(LESSONS_DIR, f"{name}.pdf")
        if os.path.exists(txt_path):
            txt_to_pdf(txt_path, pdf_path)
            # Verify
            doc = fitz.open(pdf_path)
            print(f"  {name}.pdf: {doc.page_count} pages")
            doc.close()
        else:
            print(f"  Skipping {name}: TXT not found")
