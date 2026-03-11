import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from sqlalchemy import text
from app import db
from datetime import datetime


def generate_score_card_pdf(reg_id):
    # Fetch Data
    query = text("""
        SELECT 
            m.regno, m.s_name, m.s_surname, m.f_name, m.m_name,
            m.rollno,
            mt.Marks as TotalMarks,
            mt.ObtainMarks as MarksObtained,
            mt.OverAllRank as OverallRank,
            cm.Categoryrank as CategoryRank,
            mt.Category as Category,
            mt.AllottedCategory as AllottedCategory,
            mt.AllottedSpecialisation as Specialization,
            d.description as DegreeDesc,
            pc.CollegeName as CollegeName,
            s.description as SessionDesc,
            et.Dated as ExamDate
        FROM PA_Registration_Mst m
        LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
        LEFT JOIN PA_Candidate_Marks cm ON m.rollno = cm.RollNo
        LEFT JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
        LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
        LEFT JOIN PA_College_Mst pc ON mt.Fk_CollegeID = pc.Pk_CollegeID
        LEFT JOIN LUP_AcademicSession_Mst s ON mm.Fk_SessionID = s.pk_sessionid
        LEFT JOIN PA_SeatAllotment_Details sa ON sa.fk_regid = m.pk_regid
        LEFT JOIN PA_ET_Master et ON sa.Fk_ETID = et.Pk_ETID
        WHERE m.pk_regid = :reg_id
    """)
    row = db.session.execute(query, {'reg_id': reg_id}).mappings().first()

    if not row:
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"
    font_italic = "Helvetica-Oblique"

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
    except:
        pass

    # ── Helper Functions ──────────────────────────────────────────────

    def draw_str(x, y, txt, font=font_regular, size=8.25):
        c.setFont(font, size)
        c.drawString(x, height - y, txt)

    def draw_center(x, y, txt, font=font_regular, size=8.25):
        c.setFont(font, size)
        c.drawCentredString(x, height - y, txt)

    def draw_right(x, y, txt, font=font_regular, size=8.25):
        c.setFont(font, size)
        c.drawRightString(x, height - y, txt)

    def hline(x1, x2, y_top):
        c.line(x1, height - y_top, x2, height - y_top)

    def vline(x, y1_top, y2_top):
        c.line(x, height - y1_top, x, height - y2_top)

    def draw_justified_line(x, y_top, text_str, font_name, size, max_width):
        """Draw a single line fully justified."""
        c.setFont(font_name, size)
        words = text_str.split(' ')
        words = [w for w in words if w]
        if len(words) <= 1:
            c.drawString(x, height - y_top, text_str)
            return
        total_text_width = sum(c.stringWidth(w, font_name, size) for w in words)
        total_space = max_width - total_text_width
        if total_space < 0:
            total_space = 0
        gap = total_space / (len(words) - 1)
        cx = x
        for i, w in enumerate(words):
            c.drawString(cx, height - y_top, w)
            cx += c.stringWidth(w, font_name, size) + gap

    def draw_justified_mixed_line(x, y_top, segments, max_width):
        """
        Draw a fully justified line with mixed bold/regular segments.
        segments = [(text, font, size), ...]
        """
        all_words = []
        for seg_text, seg_font, seg_size in segments:
            words = seg_text.split(' ')
            for w in words:
                if w:
                    all_words.append((w, seg_font, seg_size))
        if len(all_words) <= 1:
            for w, f, s in all_words:
                c.setFont(f, s)
                c.drawString(x, height - y_top, w)
            return
        total_text_w = sum(c.stringWidth(w, f, s) for w, f, s in all_words)
        total_space = max_width - total_text_w
        if total_space < 0:
            total_space = 0
        gap = total_space / (len(all_words) - 1) if len(all_words) > 1 else 0
        cx = x
        for i, (w, f, s) in enumerate(all_words):
            c.setFont(f, s)
            c.drawString(cx, height - y_top, w)
            cx += c.stringWidth(w, f, s) + gap

    def word_wrap_lines(txt, font_name, size, max_width):
        """Split text into lines that fit within max_width."""
        c.setFont(font_name, size)
        words = str(txt).split(' ')
        lines = []
        cur = []
        for w in words:
            test = ' '.join(cur + [w])
            if c.stringWidth(test, font_name, size) <= max_width:
                cur.append(w)
            else:
                if cur:
                    lines.append(' '.join(cur))
                cur = [w]
        if cur:
            lines.append(' '.join(cur))
        return lines

    def truncate_text(txt, font_name, size, max_width):
        """Truncate text with ellipsis if it exceeds max_width."""
        c.setFont(font_name, size)
        if c.stringWidth(txt, font_name, size) <= max_width:
            return txt
        while c.stringWidth(txt + '...', font_name, size) > max_width and len(txt) > 0:
            txt = txt[:-1]
        return txt.strip() + '...'

    # ══════════════════════════════════════════════════════════════════
    #  HEADER SECTION
    # ══════════════════════════════════════════════════════════════════

    cx_page = width / 2.0

    # ── University Logo (top-left) ────────────────────────────────────
    logo_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static', 'images', 'hau_logo.png'
    )
    if os.path.exists(logo_path):
        try:
            c.drawImage(
                logo_path, 33, height - 95,
                width=75, height=75,
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass

    # ── Hindi Name Image (top-right of logo) ──────────────────────────
    hindi_img_path = os.path.join('D:', os.sep, 'Preadmission', 'app', 'static', 'img', 'hindi_name.png')
    # Also try relative path
    hindi_img_alt = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'static', 'img', 'hindi_name.png'
    )
    hindi_path = hindi_img_path if os.path.exists(hindi_img_path) else hindi_img_alt

    if os.path.exists(hindi_path):
        try:
            c.drawImage(
                hindi_path, 130, height - 55,
                width=420, height=35,
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass

    # ── "Score Card" title ────────────────────────────────────────────
    draw_center(cx_page, 72.00, "Score Card", font=font_bold, size=14.0)

    # ── Course description line (centered, wrapped if needed) ─────────
    degree = row.DegreeDesc or "Ph.D."
    college = row.CollegeName or "College of Basic Sciences & Humanities"
    spec = row.Specialization or "Zoology"
    header_text = f"Entrance Test for Admission to {degree} ({college}) ({spec}) Course"

    c.setFont(font_bold, 8.25)
    header_w = c.stringWidth(header_text, font_bold, 8.25)
    max_header_w = width - 70
    if header_w <= max_header_w:
        draw_center(cx_page, 92.00, header_text, font=font_bold, size=8.25)
    else:
        # Wrap to two lines centered
        lines = word_wrap_lines(header_text, font_bold, 8.25, max_header_w)
        hy = 88.00
        for line in lines:
            draw_center(cx_page, hy, line, font=font_bold, size=8.25)
            hy += 13.0

    # ── Held On date ──────────────────────────────────────────────────
    try:
        if row.get('ExamDate'):
            exam_date = row.ExamDate
            if isinstance(exam_date, str):
                date_str = exam_date
            else:
                date_str = exam_date.strftime("%d.%m.%Y")
        else:
            date_str = datetime.now().strftime("%d.%m.%Y")
    except:
        date_str = datetime.now().strftime("%d.%m.%Y")

    draw_center(cx_page, 118.00, f"Held On - {date_str}", font=font_bold, size=8.25)

    # ── Note line ─────────────────────────────────────────────────────
    draw_str(33.75, 136.00, "Note: Kindly bring the copy of result at the time of Counselling.",
             font=font_bold, size=8.25)

    # ══════════════════════════════════════════════════════════════════
    #  APPLICANT DETAILS TABLE
    # ══════════════════════════════════════════════════════════════════

    c.setStrokeColor(black)
    c.setLineWidth(0.6)

    # Table dimensions
    tbl_left = 33.0
    tbl_right = 560.0
    tbl_col_div = 210.0  # divider between label and value columns
    row_h = 18.5  # row height

    detail_labels = [
        "Application Id",
        "Applicant's Name",
        "Father's Name",
        "Mother's Name",
        "Roll No.",
        "Category",
    ]

    name = f"{row.s_name or ''} {row.s_surname or ''}".strip().upper()

    detail_values = [
        str(row.regno or ""),
        name,
        str(row.f_name or "").upper(),
        str(row.m_name or "").upper(),
        str(row.rollno or ""),
        str(row.Category or "GENERAL"),
    ]

    tbl_top = 148.00
    val_max_w = tbl_right - tbl_col_div - 10

    # Draw table rows
    for i in range(len(detail_labels)):
        y_top = tbl_top + i * row_h
        y_bot = y_top + row_h

        # Horizontal lines
        hline(tbl_left, tbl_right, y_top)

        # Label
        draw_str(tbl_left + 4, y_top + 13.0, detail_labels[i],
                 font=font_bold, size=8.25)

        # Value (truncate if needed)
        val_text = truncate_text(detail_values[i], font_regular, 8.95, val_max_w)
        draw_str(tbl_col_div + 8, y_top + 13.0, val_text,
                 font=font_regular, size=8.95)

    # Bottom line of details table
    details_bottom = tbl_top + len(detail_labels) * row_h
    hline(tbl_left, tbl_right, details_bottom)

    # Vertical lines for details table
    vline(tbl_left, tbl_top, details_bottom)
    vline(tbl_col_div, tbl_top, details_bottom)
    vline(tbl_right, tbl_top, details_bottom)

    # ══════════════════════════════════════════════════════════════════
    #  "Result" HEADING (centered)
    # ══════════════════════════════════════════════════════════════════

    result_heading_y = details_bottom + 22.0
    draw_center(cx_page, result_heading_y, "Result", font=font_bold, size=11.0)

    # ══════════════════════════════════════════════════════════════════
    #  RESULT TABLE
    # ══════════════════════════════════════════════════════════════════

    result_tbl_top = result_heading_y + 14.0

    result_labels = [
        "Total Marks",
        "Marks Obtained",
        "OverAll Rank",
        "Category Rank",
    ]

    try:
        total_marks = f"{float(row.TotalMarks):.2f}" if row.TotalMarks else "100.00"
    except (TypeError, ValueError):
        total_marks = str(row.TotalMarks or "100.00")

    try:
        marks_obtained = f"{float(row.MarksObtained):.2f}" if row.MarksObtained else "0.00"
    except (TypeError, ValueError):
        marks_obtained = str(row.MarksObtained or "0.00")

    overall_rank = str(row.OverallRank or "NA")
    try:
        category_rank = str(row.CategoryRank or "-")
    except:
        category_rank = "-"

    result_values = [
        total_marks,
        marks_obtained,
        overall_rank,
        category_rank,
    ]

    for i in range(len(result_labels)):
        y_top = result_tbl_top + i * row_h
        y_bot = y_top + row_h

        hline(tbl_left, tbl_right, y_top)

        draw_str(tbl_left + 4, y_top + 13.0, result_labels[i],
                 font=font_bold, size=8.25)

        draw_str(tbl_col_div + 8, y_top + 13.0, result_values[i],
                 font=font_regular, size=8.95)

    result_bottom = result_tbl_top + len(result_labels) * row_h
    hline(tbl_left, tbl_right, result_bottom)

    # Vertical lines for result table
    vline(tbl_left, result_tbl_top, result_bottom)
    vline(tbl_col_div, result_tbl_top, result_bottom)
    vline(tbl_right, result_tbl_top, result_bottom)

    # ══════════════════════════════════════════════════════════════════
    #  BOTTOM NOTES (fully justified)
    # ══════════════════════════════════════════════════════════════════

    note_left = 33.75
    note_right = 560.0
    note_width = note_right - note_left
    note_size = 8.25
    note_sp = 13.5  # line spacing

    note_y = result_bottom + 30.0

    # ── "Note :" bold + first line justified ──────────────────────────

    note_para1 = (
        "Rank number of those who have qualified the ET-V has been indicated against each Figure in "
        "brackets indicates number of candidates obtaining same marks. For example 2(3) indicates that there "
        "are 3 candidates at Rank 2 and thus next candidates on merit has been given rank 5. Rank indicated "
        "above is tentative and final rank will be decided at time of counseling subject to verification of "
        "documents as per rule laid down in the prospectus."
    )

    # Draw "Note :" bold
    draw_str(note_left, note_y, "Note :", font=font_bold, size=9.10)
    c.setFont(font_bold, 9.10)
    note_label_w = c.stringWidth("Note :", font_bold, 9.10) + 6

    # Wrap first paragraph
    # First line starts after "Note :"
    first_line_x = note_left + note_label_w
    first_line_w = note_right - first_line_x
    full_para_w = note_width

    c.setFont(font_regular, note_size)
    words = note_para1.split(' ')
    words = [w for w in words if w]
    para1_lines = []
    cur = []
    first_done = False

    for w in words:
        test = ' '.join(cur + [w])
        mw = first_line_w if not first_done else full_para_w
        if c.stringWidth(test, font_regular, note_size) <= mw:
            cur.append(w)
        else:
            if cur:
                para1_lines.append((
                    ' '.join(cur),
                    first_line_x if not first_done else note_left,
                    first_line_w if not first_done else full_para_w
                ))
                first_done = True
            cur = [w]
    if cur:
        para1_lines.append((
            ' '.join(cur),
            first_line_x if not first_done else note_left,
            first_line_w if not first_done else full_para_w
        ))

    ny = note_y
    for i, (line_text, lx, lw) in enumerate(para1_lines):
        if i < len(para1_lines) - 1:
            draw_justified_line(lx, ny, line_text, font_regular, note_size, lw)
        else:
            # Last line left-aligned
            c.setFont(font_regular, note_size)
            c.drawString(lx, height - ny, line_text)
        ny += note_sp

    # ── Second paragraph (admission info) ─────────────────────────────
    ny += note_sp * 0.5  # extra gap between paragraphs

    note_para2 = (
        "Admission will made through online counseling only. Candidates are required to register for counseling "
        "and follow the admission/counseling procedure given in prospectus for online counseling at University "
        "website i.e. http://www.hau.ac.in/ , http://admissions.hau.ac.in/."
    )

    para2_lines_raw = word_wrap_lines(note_para2, font_regular, note_size, full_para_w)
    for i, line_text in enumerate(para2_lines_raw):
        if i < len(para2_lines_raw) - 1:
            draw_justified_line(note_left, ny, line_text, font_regular, note_size, full_para_w)
        else:
            c.setFont(font_regular, note_size)
            c.drawString(note_left, height - ny, line_text)
        ny += note_sp

    # ══════════════════════════════════════════════════════════════════
    #  FOOTER
    # ══════════════════════════════════════════════════════════════════

    draw_right(560.0, 770.00, "Page 1 of 1", font=font_regular, size=8.95)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()