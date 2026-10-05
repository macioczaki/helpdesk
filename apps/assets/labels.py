import os
from io import BytesIO
from tempfile import NamedTemporaryFile

import qrcode
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


LABEL_W = 50 * mm
LABEL_H = 30 * mm
MARGIN = 5 * mm
COLS = 4
ROWS = 9

FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"


def _register_fonts():
    """Rejestruje fonty TTF raz na proces."""
    try:
        pdfmetrics.getFont(FONT_REGULAR)
        return
    except KeyError:
        pass
    regular = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
    bold = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, regular))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, bold))


def _truncate(text, limit):
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_labels_pdf(assets, base_url=""):
    _register_fonts()

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x0 = (width - (COLS * LABEL_W + (COLS - 1) * 2 * mm)) / 2
    y0 = height - MARGIN - LABEL_H

    x, y = x0, y0
    col, row = 0, 0

    for asset in assets:
        _draw_label(c, asset, x, y)

        col += 1
        if col >= COLS:
            col = 0
            row += 1
            x = x0
            y -= LABEL_H + 2 * mm
            if row >= ROWS:
                c.showPage()
                row = 0
                y = y0
        else:
            x += LABEL_W + 2 * mm

    c.save()
    buf.seek(0)
    return buf.getvalue()


def _draw_label(c, asset, x, y):
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.rect(x, y, LABEL_W, LABEL_H)

    # QR
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(asset.tag)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    qr_size = 22 * mm
    with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img.save(tmp.name)
        c.drawImage(
            tmp.name,
            x + 2 * mm,
            y + (LABEL_H - qr_size) / 2,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )
        tmp_path = tmp.name

    # Tekst — dostępna szerokość to ~20mm (od x+26mm do x+48mm)
    text_x = x + qr_size + 4 * mm   # ~26mm od lewej krawędzi etykiety
    text_max = 20                    # maksymalna liczba znaków

    c.setFont(FONT_BOLD, 7)
    c.drawString(text_x, y + LABEL_H - 7 * mm, _truncate(asset.tag, text_max))

    c.setFont(FONT_REGULAR, 6)
    c.drawString(text_x, y + LABEL_H - 12 * mm, _truncate(asset.name, text_max))

    c.setFont(FONT_REGULAR, 5)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(text_x, y + 4 * mm, "Urząd Gminy")
    c.setFillColorRGB(0, 0, 0)

    try:
        os.unlink(tmp_path)
    except OSError:
        pass