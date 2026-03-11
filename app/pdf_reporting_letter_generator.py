import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black
from sqlalchemy import text
from app import db
from datetime import datetime
from PIL import Image as PILImage


def generate_reporting_letter_pdf(reg_id):
    # Fetch Data
    query = text("""
        SELECT 
            m.regno, m.s_name, m.s_surname, m.f_name, m.m_name,
            m.c_address, m.c_district, m.C_Village, m.c_pincode,
            m.rollno,
            mt.Marks as TotalMarks,
            mt.ObtainMarks as MarksObtained,
            mt.OverAllRank as OverallRank,
            mt.Category as Category,
            mt.AllottedCategory as AllottedCategory,
            mt.AllottedSpecialisation as Specialization,
            d.description as DegreeDesc,
            pc.CollegeName as CollegeName,
            sc.collegename as SMSCollegeName,
            s.description as SessionDesc,
            c.Description as CandidateCategory,
            mt.AllottedPreference,
            doc.imgattach_p
        FROM PA_Registration_Mst m
        LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
        LEFT JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
        LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
        LEFT JOIN PA_College_Mst pc ON mt.Fk_CollegeID = pc.Pk_CollegeID
        LEFT JOIN SMS_College_Mst sc ON mt.fk_allotedcollegeid = sc.pk_collegeid
        LEFT JOIN LUP_AcademicSession_Mst s ON mm.Fk_SessionID = s.pk_sessionid
        LEFT JOIN PA_StudentCategory_Mst c ON m.fk_stucatid_cast = c.Pk_StuCatId
        LEFT JOIN PA_Registration_Document doc ON m.pk_regid = doc.fk_regid
        WHERE m.pk_regid = :reg_id
    """)
    row = db.session.execute(query, {'reg_id': reg_id}).mappings().first()

    if not row:
        return None

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"
    font_italic = "Helvetica-Oblique"
    font_bold_italic = "Helvetica-BoldOblique"

    try:
        if os.path.exists('C:/Windows/Fonts/verdana.ttf'):
            pdfmetrics.registerFont(TTFont('Verdana', 'C:/Windows/Fonts/verdana.ttf'))
            font_regular = 'Verdana'
        if os.path.exists('C:/Windows/Fonts/verdanab.ttf'):
            pdfmetrics.registerFont(TTFont('Verdana-Bold', 'C:/Windows/Fonts/verdanab.ttf'))
            font_bold = 'Verdana-Bold'
        if os.path.exists('C:/Windows/Fonts/verdanai.ttf'):
            pdfmetrics.registerFont(TTFont('Verdana-Italic', 'C:/Windows/Fonts/verdanai.ttf'))
            font_italic = 'Verdana-Italic'
        if os.path.exists('C:/Windows/Fonts/verdanaz.ttf'):
            pdfmetrics.registerFont(TTFont('Verdana-BoldItalic', 'C:/Windows/Fonts/verdanaz.ttf'))
            font_bold_italic = 'Verdana-BoldItalic'
    except:
        pass

    # ── Helper Functions ──────────────────────────────────────────────

    def draw_str(x, y, txt, font=font_regular, size=7.45):
        """Draw string at (x, y-from-top)."""
        pdf.setFont(font, size)
        pdf.drawString(x, height - y, txt)

    def draw_center(x, y, txt, font=font_regular, size=7.45):
        """Draw string centred at x, y-from-top."""
        pdf.setFont(font, size)
        pdf.drawCentredString(x, height - y, txt)

    def draw_right(x, y, txt, font=font_regular, size=7.45):
        """Draw right-aligned string ending at x."""
        pdf.setFont(font, size)
        pdf.drawRightString(x, height - y, txt)

    def word_wrap_lines(txt, font, size, max_width):
        """Split text into lines that fit within max_width."""
        pdf.setFont(font, size)
        words = str(txt).split(' ')
        lines = []
        cur = []
        for w in words:
            test = ' '.join(cur + [w])
            if pdf.stringWidth(test, font, size) <= max_width:
                cur.append(w)
            else:
                if cur:
                    lines.append(' '.join(cur))
                cur = [w]
        if cur:
            lines.append(' '.join(cur))
        return lines

    def draw_justified_line(x, y_top, text_str, font_name, size, max_width):
        """Draw a single line of text fully justified between x and x+max_width."""
        pdf.setFont(font_name, size)
        words = text_str.split(' ')
        if len(words) <= 1:
            pdf.drawString(x, height - y_top, text_str)
            return
        total_text_width = sum(pdf.stringWidth(w, font_name, size) for w in words)
        total_space = max_width - total_text_width
        gap = total_space / (len(words) - 1)
        cx = x
        for i, w in enumerate(words):
            pdf.drawString(cx, height - y_top, w)
            cx += pdf.stringWidth(w, font_name, size) + gap

    def draw_justified_text(x, y_top, txt, font_name=font_regular, size=7.45,
                            max_width=520, line_spacing=12.5, indent_first=0):
        """Draw multi-line fully justified text. Last line is left-aligned."""
        lines = word_wrap_lines(txt, font_name, size, max_width - indent_first)
        cy = y_top
        for i, line in enumerate(lines):
            lx = x + (indent_first if i == 0 else 0)
            lw = max_width - (indent_first if i == 0 else 0)
            if i < len(lines) - 1:
                draw_justified_line(lx, cy, line, font_name, size, lw)
            else:
                pdf.setFont(font_name, size)
                pdf.drawString(lx, height - cy, line)
            cy += line_spacing
        return cy

    def draw_justified_mixed_line(x, y_top, segments, max_width):
        """
        Draw a fully justified line with mixed bold/regular segments.
        segments = [(text, font, size), ...]
        """
        # Calculate total text width
        all_words = []
        for seg_text, seg_font, seg_size in segments:
            words = seg_text.split(' ')
            for w in words:
                if w:
                    all_words.append((w, seg_font, seg_size))

        if len(all_words) <= 1:
            for w, f, s in all_words:
                pdf.setFont(f, s)
                pdf.drawString(x, height - y_top, w)
            return

        total_text_w = sum(pdf.stringWidth(w, f, s) for w, f, s in all_words)
        total_space = max_width - total_text_w
        if total_space < 0:
            total_space = 0
        gap = total_space / (len(all_words) - 1) if len(all_words) > 1 else 0

        cx = x
        for i, (w, f, s) in enumerate(all_words):
            pdf.setFont(f, s)
            pdf.drawString(cx, height - y_top, w)
            cx += pdf.stringWidth(w, f, s) + gap

    def wrap_text_in_cell(x, y_top, txt, font_name, size, max_width, line_spacing=10.9):
        """Wrap text inside a table cell, centered horizontally per line."""
        lines = word_wrap_lines(txt, font_name, size, max_width)
        cy = y_top
        for line in lines:
            pdf.setFont(font_name, size)
            lw = pdf.stringWidth(line, font_name, size)
            lx = x + (max_width - lw) / 2.0
            pdf.drawString(lx, height - cy, line)
            cy += line_spacing
        return cy

    def wrap_text_in_cell_left(x, y_top, txt, font_name, size, max_width, line_spacing=10.9):
        """Wrap text inside a table cell, left-aligned."""
        lines = word_wrap_lines(txt, font_name, size, max_width)
        cy = y_top
        for line in lines:
            pdf.setFont(font_name, size)
            pdf.drawString(x, height - cy, line)
            cy += line_spacing
        return cy

    def hline(x1, x2, y_from_top):
        pdf.line(x1, height - y_from_top, x2, height - y_from_top)

    def vline(x, y1_top, y2_top):
        pdf.line(x, height - y1_top, x, height - y2_top)

    # ══════════════════════════════════════════════════════════════════
    #  HEADER
    # ══════════════════════════════════════════════════════════════════

    logo_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static', 'images', 'hau_logo.png'
    )
    if os.path.exists(logo_path):
        try:
            pdf.drawImage(
                logo_path, 40, height - 90,
                width=64, height=64,
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass

    cx = width / 2 + 10
    draw_center(cx, 32.00, "CHAUDHARY CHARAN SINGH",
                font=font_bold, size=9.95)
    draw_center(cx, 46.50, "HARYANA AGRICULTURAL UNIVERSITY",
                font=font_bold, size=9.95)
    draw_center(cx, 61.00, "HISAR-125004(Haryana)India",
                font=font_bold, size=9.95)
    draw_center(cx, 79.10,
                "(Established by Parliament Act No.16 of 1970)",
                font=font_regular, size=7.45)

    # ── Title with border box ─────────────────────────────────────────
    title_text = "Provisional Seat Allotment Letter"
    title_size = 8.25
    pdf.setFont(font_bold, title_size)
    tw = pdf.stringWidth(title_text, font_bold, title_size)
    tx = cx - tw / 2
    ty = height - 103.45
    pad_x, pad_y = 10, 5
    pdf.setLineWidth(0.8)
    pdf.rect(tx - pad_x, ty - pad_y, tw + 2 * pad_x,
             title_size + 2 * pad_y)
    draw_center(cx, 103.45, title_text, font=font_bold, size=title_size)

    # ── Date / Time (top-right) ───────────────────────────────────────
    now = datetime.now()
    date_str = f"{now.day}/{now.month}/{now.year}"
    time_str = now.strftime("%I:%M:%S %p").lower().lstrip("0")

    draw_str(497.75, 87.30, "Date :", font=font_bold_italic, size=6.60)
    draw_str(530.75, 87.45, date_str, font=font_italic, size=7.20)
    draw_str(495.75, 99.10, "Time :", font=font_bold_italic, size=6.60)
    draw_str(529.25, 98.95, time_str, font=font_italic, size=7.20)

    # ══════════════════════════════════════════════════════════════════
    #  TO SECTION
    # ══════════════════════════════════════════════════════════════════

    draw_str(130.05, 123.70, "To", font=font_bold, size=8.25)

    # ── Student Photo (LEFT side) ─────────────────────────────────────
    photo_x, photo_y_top, photo_w, photo_h = 48, 138, 65, 78
    if row.get('imgattach_p'):
        try:
            p_stream = io.BytesIO(row['imgattach_p'])
            PILImage.open(p_stream).verify()
            p_stream.seek(0)
            img_reader = ImageReader(p_stream)
            pdf.drawImage(
                img_reader,
                photo_x, height - (photo_y_top + photo_h),
                width=photo_w, height=photo_h,
                preserveAspectRatio=True
            )
        except Exception as e:
            print(f"Error drawing photo on Reporting Letter: {e}")

    # ── Name ──────────────────────────────────────────────────────────
    name = f"{row.s_name or ''} {row.s_surname or ''}".strip().upper()
    # Truncate name if too long for available space
    name_max_w = 200
    pdf.setFont(font_bold, 7.45)
    if pdf.stringWidth(name, font_bold, 7.45) > name_max_w:
        while pdf.stringWidth(name + '...', font_bold, 7.45) > name_max_w and len(name) > 0:
            name = name[:-1]
        name = name.strip() + '...'
    draw_str(147.50, 143.05, name, font=font_bold, size=7.45)

    # ── Father / Mother ───────────────────────────────────────────────
    draw_str(147.25, 163.85, "Son/", font=font_regular, size=7.45)
    draw_str(147.25, 174.75, "Daughter of :", font=font_regular, size=7.45)
    father_name = str(row.f_name or "").upper()
    pdf.setFont(font_regular, 7.45)
    father_max_w = 145
    if pdf.stringWidth(father_name, font_regular, 7.45) > father_max_w:
        while pdf.stringWidth(father_name + '...', font_regular, 7.45) > father_max_w and len(father_name) > 0:
            father_name = father_name[:-1]
        father_name = father_name.strip() + '...'
    draw_str(211.75, 169.05, father_name, font=font_regular, size=7.45)

    # ── Address (wrapped) ─────────────────────────────────────────────
    draw_str(148.50, 194.35, "Address", font=font_regular, size=7.45)
    draw_str(196.00, 194.35, ":", font=font_regular, size=7.45)

    addr = (
        f"HouseNo-{row.c_address or ''},"
        f"DistrictName-{row.c_district or ''},"
        f"Ward/Village-{row.C_Village or ''},"
        f"Pin-{row.c_pincode or ''}"
    )
    wrap_text_in_cell_left(213.25, 194.10, addr, font_regular, 7.45,
                           max_width=140, line_spacing=10.9)

    # ── Right-side info fields ────────────────────────────────────────
    colon_x = 449.75
    val_x = 457.75
    val_max_w = 115  # max width for right-side values

    draw_str(364.25, 144.60, "Counselling No.", font=font_regular, size=7.45)
    draw_str(colon_x, 146.10, ":", font=font_regular, size=7.45)
    degree_short = (
        str(row.DegreeDesc or "").replace(".", "").replace(" ", "").upper()
    )
    session_str = row.SessionDesc or "2025-2026"
    couns_no = f"{session_str}/{degree_short}/1/18"
    # Ensure counselling no fits
    pdf.setFont(font_regular, 7.45)
    if pdf.stringWidth(couns_no, font_regular, 7.45) > val_max_w:
        draw_str(val_x, 145.30, couns_no, font=font_regular, size=6.20)
    else:
        draw_str(val_x, 145.30, couns_no, font=font_regular, size=7.45)

    draw_str(364.25, 165.60, "Roll No.", font=font_regular, size=7.45)
    draw_str(colon_x + 0.75, 166.35, ":", font=font_regular, size=7.45)
    draw_str(val_x + 1, 165.05,
             str(row.rollno or ""), font=font_regular, size=7.45)

    draw_str(364.00, 185.10, "Marks", font=font_regular, size=7.45)
    draw_str(colon_x + 0.75, 185.10, ":", font=font_regular, size=7.45)
    try:
        marks_str = f"{float(row.MarksObtained):.2f}"
    except (TypeError, ValueError):
        marks_str = str(row.MarksObtained or "")
    draw_str(val_x, 185.30, marks_str, font=font_regular, size=7.45)

    draw_str(364.75, 205.10, "Registration No.",
             font=font_regular, size=7.45)
    draw_str(colon_x + 0.75, 205.35, ":", font=font_regular, size=7.45)
    draw_str(val_x + 0.75, 205.30,
             str(row.regno or ""), font=font_regular, size=7.45)

    # ══════════════════════════════════════════════════════════════════
    #  SUBJECT LINE
    # ══════════════════════════════════════════════════════════════════

    deg_name = row.DegreeDesc or "M. Sc."
    draw_str(41.75, 241.70, "Subject :", font=font_bold, size=8.25)
    draw_str(134.50, 241.45,
             f"Provisional Seat Allotment For {deg_name}",
             font=font_bold, size=8.25)

    # ══════════════════════════════════════════════════════════════════
    #  PARAGRAPH (fully justified)
    # ══════════════════════════════════════════════════════════════════

    para_left = 41.25
    para_right = 570.0
    para_width = para_right - para_left
    para_indent_first = 90.0  # indent for first line starting after "Chaudhary..."

    para_text = (
        "Chaudhary Charan Singh Haryana Agricultural University "
        "(CCSHAU), Hisar is pleased to inform "
        "you that based upon the available seats and choices "
        "filled-up/submitted by you, the following College/Stream has "
        "been allotted provisional to you on the basis of merit. "
        "Your admission will be subject to the verification of your "
        "certificates/credentials, eligibility and proof of "
        "counselling fee deposition"
    )

    # First line starts indented (after "Subject" area)
    first_line_x = 131.25
    first_line_width = para_right - first_line_x
    all_lines = word_wrap_lines(para_text, font_regular, 7.45, first_line_width)

    # Re-wrap: first line with narrower width, rest with full width
    pdf.setFont(font_regular, 7.45)
    words = para_text.split(' ')
    lines = []
    cur = []
    first_done = False
    for w in words:
        test = ' '.join(cur + [w])
        mw = first_line_width if not first_done else para_width
        if pdf.stringWidth(test, font_regular, 7.45) <= mw:
            cur.append(w)
        else:
            if cur:
                lines.append((' '.join(cur), first_line_x if not first_done else para_left,
                               first_line_width if not first_done else para_width))
                first_done = True
            cur = [w]
    if cur:
        lines.append((' '.join(cur), first_line_x if not first_done else para_left,
                       first_line_width if not first_done else para_width))

    py = 261.35
    p_sp = 16.35  # line spacing to match sample
    for i, (line_text, lx, lw) in enumerate(lines):
        if i < len(lines) - 1:
            draw_justified_line(lx, py, line_text, font_regular, 7.45, lw)
        else:
            pdf.setFont(font_regular, 7.45)
            pdf.drawString(lx, height - py, line_text)
        py += p_sp

    # ══════════════════════════════════════════════════════════════════
    #  TABLE
    # ══════════════════════════════════════════════════════════════════

    col_x = [35, 160, 268, 348, 443, 493, 555]
    tbl_y = [325, 375, 435]

    pdf.setStrokeColor(black)
    pdf.setLineWidth(0.6)

    for yt in tbl_y:
        hline(col_x[0], col_x[-1], yt)

    for xv in col_x:
        vline(xv, tbl_y[0], tbl_y[-1])

    def ccx(i):
        return (col_x[i] + col_x[i + 1]) / 2.0

    hs = 7.45

    draw_center(ccx(0), 337.85, "Alloted", font=font_bold, size=hs)
    draw_center(ccx(0), 348.75, "College", font=font_bold, size=hs)

    draw_center(ccx(1), 337.85, "Alloted", font=font_bold, size=hs)
    draw_center(ccx(1), 348.75, "Stream", font=font_bold, size=hs)

    draw_center(ccx(2), 337.85, "Your", font=font_bold, size=hs)
    draw_center(ccx(2), 348.75, "Category", font=font_bold, size=hs)

    draw_center(ccx(3), 330.00, "Category", font=font_bold, size=hs)
    draw_center(ccx(3), 340.90, "under which", font=font_bold, size=hs)
    draw_center(ccx(3), 351.80, "seat has been", font=font_bold, size=hs)
    draw_center(ccx(3), 362.70, "allotted", font=font_bold, size=hs)

    draw_center(ccx(4), 337.85, "Choice", font=font_bold, size=hs)
    draw_center(ccx(4), 348.75, "No.", font=font_bold, size=hs)

    draw_center(ccx(5), 337.85, "Allotment", font=font_bold, size=hs)
    draw_center(ccx(5), 348.75, "Status", font=font_bold, size=hs)

    # ── Data row with wrapping ────────────────────────────────────────
    data_y = 390
    cell_padding = 5

    # Col 0 – College name (wrapped, centered)
    col_name = str(row.CollegeName or "")
    sms_col_name = str(row.SMSCollegeName or "")
    full_col = (
        f"{col_name} ({sms_col_name})"
        if sms_col_name and sms_col_name != col_name
        else col_name
    )
    col0_w = col_x[1] - col_x[0] - 2 * cell_padding
    wrap_text_in_cell(col_x[0] + cell_padding, data_y, full_col,
                      font_regular, 6.60, col0_w, line_spacing=10.0)

    # Col 1 – Specialisation (wrapped, left-aligned within cell)
    spec = str(row.Specialization or "")
    col1_w = col_x[2] - col_x[1] - 2 * cell_padding
    wrap_text_in_cell_left(col_x[1] + cell_padding, data_y, spec,
                           font_regular, 7.45, col1_w, line_spacing=10.9)

    # Col 2 – Your Category (centered, wrapped if needed)
    col2_w = col_x[3] - col_x[2] - 2 * cell_padding
    cat_text = str(row.CandidateCategory or "GENERAL")
    wrap_text_in_cell(col_x[2] + cell_padding, data_y, cat_text,
                      font_regular, 7.45, col2_w, line_spacing=10.9)

    # Col 3 – Allotted Category (centered, wrapped if needed)
    col3_w = col_x[4] - col_x[3] - 2 * cell_padding
    allot_cat = str(row.AllottedCategory or "GENERAL")
    wrap_text_in_cell(col_x[3] + cell_padding, data_y, allot_cat,
                      font_regular, 7.45, col3_w, line_spacing=10.9)

    # Col 4 – Choice / Preference (centered)
    draw_center(ccx(4), data_y,
                str(row.AllottedPreference or "1"),
                font=font_regular, size=7.45)

    # Col 5 – Allotment Status (centered)
    draw_center(ccx(5), data_y, "YES",
                font=font_regular, size=7.45)

    # ══════════════════════════════════════════════════════════════════
    #  INSTRUCTIONS (fully justified)
    # ══════════════════════════════════════════════════════════════════

    inst_left = 44.85
    txt_x = 56.25
    sub_x = 64.25
    inst_right = 570.0
    inst_width = inst_right - txt_x
    sub_width = inst_right - sub_x
    ly = 466.60
    sp = 12.5

    draw_str(inst_left, ly,
             "However, the student should follow the below "
             "instructions strictly :",
             font=font_bold, size=7.45)

    # ── 1. Reporting (justified mixed bold/regular) ───────────────────
    ly += sp + 2
    draw_str(inst_left, ly, "1.", font=font_regular, size=7.45)

    line1_text = ("For admission, you should report in "
                  "Committee Room of Dean, PGS, CCSHAU, Hisar "
                  "from 11/08/2025 to,")
    # Mixed segments for line 1
    draw_justified_mixed_line(txt_x, ly, [
        ("For admission, you should report in", font_regular, 7.45),
        ("Committee Room of Dean, PGS, CCSHAU, Hisar", font_bold, 7.45),
        ("from", font_regular, 7.45),
        ("11/08/2025", font_bold, 7.45),
        ("to,", font_regular, 7.45),
    ], inst_width)

    ly += sp
    draw_justified_mixed_line(txt_x, ly, [
        ("12/08/2025", font_bold, 7.45),
        ("(from 09.00 AM to 05.00 PM) (excluding Sunday and Gazetted Holidays) along with fee and all", font_regular, 7.45),
    ], inst_width)

    ly += sp
    draw_justified_line(txt_x, ly,
                        "certificates/testimonials in original to prove your "
                        "eligibility along with six latest photographs failing which the",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "allotted seat will be treated as cancelled.",
             font=font_regular, size=7.45)

    # SSP Portal sub-section
    ly += sp
    draw_justified_mixed_line(txt_x, ly, [
        ("After the document verification, candidates are "
         "required to complete the following steps on SSP Portal", font_bold, 7.45),
    ], inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "i.e ssp.hauiums.in:-",
             font=font_bold, size=7.45)

    ly += sp
    draw_str(txt_x, ly, "o", font=font_bold, size=7.45)
    draw_justified_line(sub_x, ly,
                        "Username of the student will remain the same as on "
                        "admission portal and password will be DOB in format",
                        font_regular, 7.45, sub_width)

    ly += sp
    draw_justified_line(txt_x, ly,
                        "dd/mm/yyyy . The SSP Port will be "
                        "activated after the verification of the Documents.",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly, "o", font=font_bold, size=7.45)
    draw_justified_mixed_line(sub_x, ly, [
        ("Fee should be deposited online on SSP Portal through "
         "Debit Card/Credit Card/Net Banking. Cash", font_bold, 7.45),
    ], sub_width)

    ly += sp
    draw_str(sub_x, ly,
             "will not be accepted.",
             font=font_bold, size=7.45)

    # ── 2. Contact HOD (justified) ────────────────────────────────────
    ly += sp
    draw_str(inst_left, ly, "2.", font=font_regular, size=7.45)
    draw_justified_line(txt_x, ly,
                        "Contact Head of the concerned Department for "
                        "registration of courses and classes. Complete contact "
                        "details along",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_justified_line(txt_x, ly,
                        "with email id of Deans, HODs are available on "
                        "University website (hau.ac.in) as well as student",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "portal(https://ssp.hauiums.in).",
             font=font_regular, size=7.45)

    # ── 3. Medical fitness (justified) ────────────────────────────────
    ly += sp
    draw_str(inst_left, ly, "3.", font=font_regular, size=7.45)
    draw_justified_line(txt_x, ly,
                        "Candidates are required to bring with them medical "
                        "fitness certificate (issued by Civil "
                        "Hospital/PHC/CHC/CCSHAU",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_justified_line(txt_x, ly,
                        "Hospital). Please bring two sets of documents along "
                        "with admission and counselling form, duly attested "
                        "as listed",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "against Sr. no 8 in the prospectus at page no. 32.",
             font=font_regular, size=7.45)

    # ── 4. Anti-ragging (justified) ───────────────────────────────────
    ly += sp
    draw_str(inst_left, ly, "4.", font=font_regular, size=7.45)
    draw_justified_line(txt_x, ly,
                        "Candidates are required to bring with them Proforma "
                        "I,II(anti-ragging undertaking) mentioned in the "
                        "prospectus",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "at page no. 70,71.",
             font=font_regular, size=7.45)

    # ── 5. Provisional admission (justified) ──────────────────────────
    ly += sp
    draw_str(inst_left, ly, "5.", font=font_regular, size=7.45)
    draw_justified_line(txt_x, ly,
                        "The Admission will be provisional. If any discrepancy "
                        "is found at any stage, the admission shall stand "
                        "cancelled.",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_justified_line(txt_x, ly,
                        "No responsibility shall be accepted by the University "
                        "for hardships or expenses incurred by the students "
                        "or any",
                        font_regular, 7.45, inst_width)

    ly += sp
    draw_str(txt_x, ly,
             "other person for such changes, additions, omissions "
             "or errors, no matter how these are caused.",
             font=font_regular, size=7.45)

    # ── 6. Upgradation / withdrawal ──────────────────────────────────
    ly += sp
    draw_str(inst_left, ly, "6.", font=font_bold, size=7.45)
    draw_str(txt_x, ly,
             "Candidate must submit the option for upward/ "
             "upgradation/ withdrawal on his/her admission portal.",
             font=font_bold, size=7.45)

    # ══════════════════════════════════════════════════════════════════
    #  SIGNATURE BLOCK (bottom-right)
    # ══════════════════════════════════════════════════════════════════

    draw_right(555, 802.65, "Assistant Registrar (PGS)",
               font=font_bold, size=7.80)
    draw_right(555, 813.45, "For Dean, Post Graduate Studies",
               font=font_bold, size=7.80)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()