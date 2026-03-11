import os
from flask import current_app
from app import db
from sqlalchemy import text
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_couns_pdf(reg_id):
    # Fetch Candidate Data based on the counselling PDF requirements
    query = text("""
        SELECT 
            m.pk_regid, m.regno, m.s_name, m.s_surname,
            m.rollno, cm.ObtainMarks as EntranceMarks, cm.overallR as OverallRank, cm.Categoryrank as CategoryRank,
            cat.Description as Category,
            m.LDV, m.FF, m.ESM, m.PH, m.SportsQuota, m.IsWard, 
            pay.Tracking_id as TransactionId, pay.Amount, pay.DateCreated as PaymentDate,
            sess.description as session_name,
            deg.description as program_name,
            pref.Preference, pref_col.CollegeName as PreferenceCollege,
            spec.Specialization as PreferenceSpec
        FROM PA_Registration_Mst m
        LEFT JOIN LUP_AcademicSession_Mst sess ON m.fk_sessionid = sess.pk_sessionid
        LEFT JOIN ACD_Degree_Mst deg ON m.fk_dtypeid = deg.pk_degreeid
        LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
        LEFT JOIN PA_Candidate_Marks cm ON m.rollno = cm.RollNo AND m.fk_sessionid = cm.fk_sessionid
        LEFT JOIN PA_StudentCollegePreference_Details pref ON m.pk_regid = pref.fk_regid
        LEFT JOIN SMS_College_Mst pref_col ON pref.fk_CollegeId = pref_col.pk_collegeid
        LEFT JOIN PA_Specialization_mst spec ON pref.fk_SId = spec.Pk_SID
        LEFT JOIN (
            SELECT Fk_regId, MIN(Tracking_id) as Tracking_id, MAX(Amount) as Amount, MAX(DateCreated) as DateCreated
            FROM PA_OnlinePayment_Detail 
            WHERE PaymentStatus='Success' AND isCounsellingFee=1
            GROUP BY Fk_regId
        ) pay ON m.pk_regid = pay.Fk_regId
        WHERE m.pk_regid = :reg_id
        ORDER BY pref.Preference ASC
    """)
    rows = db.session.execute(query, {'reg_id': reg_id}).mappings().all()

    if not rows:
        return None

    candidate = rows[0]

    # Fetch Images (Signature)
    img_query = text("SELECT imgattach_s FROM PA_Registration_Document WHERE fk_regid = :reg_id")
    imgs = db.session.execute(img_query, {'reg_id': reg_id}).mappings().first()

    def safe_str(val):
        if val is None:
            return "NA"
        if isinstance(val, bool):
            return "Yes" if val else "No"
        if str(val).strip() == '0' and str(val).isdigit():
            return "No"
        if str(val).strip() == '1' and str(val).isdigit():
            return "Yes"
        return str(val)

    def safe_date_time_str(val):
        if val is None:
            return "NA"
        if isinstance(val, datetime):
            return val.strftime('%b %d %Y %#I:%M%p')
        return str(val)

    thesis_query = text("""
        SELECT COUNT(d.PkId) 
        FROM PA_CandidateAttachment_Details d 
        LEFT JOIN PA_Attachment_Mst m ON d.fk_attachmentId = m.Pk_attachmentId 
        WHERE d.Fk_regId = :reg_id AND (m.AttachmentType LIKE '%Thesis%' OR m.AttachmentType LIKE '%Dissertation%')
    """)
    has_thesis = db.session.execute(thesis_query, {'reg_id': reg_id}).scalar() > 0

    sports_query = text("SELECT g.GameName, s.LevelName, s.PartDate FROM PA_CandidateSports_Trn s LEFT JOIN PA_GameList_Mst g ON s.Fk_GameID = g.Pk_GameID WHERE s.fk_regid = :reg_id")
    sports_rows = db.session.execute(sports_query, {'reg_id': reg_id}).mappings().all()

    # ─── Document Setup ───────────────────────────────────────────────────────
    buffer = BytesIO()
    PAGE_W = A4[0]
    PAGE_H = A4[1]
    L_MARGIN = R_MARGIN = 0.5 * inch
    T_MARGIN = B_MARGIN = 0.5 * inch
    CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN  # ~7.27 inch

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=R_MARGIN, leftMargin=L_MARGIN,
        topMargin=T_MARGIN, bottomMargin=B_MARGIN
    )

    # ─── Styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name=name, **kw)

    uni_name_style   = S('UniName',   fontName='Helvetica-Bold', fontSize=15, alignment=1, leading=18, spaceAfter=2)
    sub_title_style  = S('SubTitle',  fontName='Helvetica',      fontSize=9,  alignment=1, leading=12, spaceAfter=2)
    session_style    = S('Session',   fontName='Helvetica-Bold', fontSize=9,  alignment=1, leading=12)
    dt_style         = S('DT',        fontName='Helvetica-Bold', fontSize=8,  alignment=0, leading=11)
    dt_right_style   = S('DTR',       fontName='Helvetica-Bold', fontSize=8,  alignment=2, leading=11)
    name_style       = S('NameStyle', fontName='Helvetica-Bold', fontSize=9,  alignment=0, leading=12)
    name_right_style = S('NameR',     fontName='Helvetica-Bold', fontSize=9,  alignment=2, leading=12)
    sec_hdr_style    = S('SecHdr',    fontName='Helvetica-Bold', fontSize=9,  alignment=1, leading=12, textColor=colors.black)
    cell_lbl_style   = S('CellLbl',   fontName='Helvetica-Bold', fontSize=8,  alignment=0, leading=11)
    cell_val_style   = S('CellVal',   fontName='Helvetica',      fontSize=8,  alignment=0, leading=11)
    decl_style       = S('Decl',      fontName='Helvetica',      fontSize=8,  alignment=4, leading=11)
    sig_style        = S('Sig',       fontName='Helvetica-Bold', fontSize=9,  alignment=1, leading=12,
                         borderWidth=0, borderColor=colors.black)

    GRAY_BG   = colors.HexColor('#d9d9d9')
    BLACK     = colors.black
    GRID_CLR  = colors.black
    OUTER_BOX = colors.black

    # ─── Helper: outer-border table ──────────────────────────────────────────
    def outer_box(inner_elements, col_w=None):
        col_w = col_w or [CONTENT_W]
        t = Table([[inner_elements]], colWidths=col_w)
        t.setStyle(TableStyle([
            ('BOX',        (0,0), (-1,-1), 0.8, OUTER_BOX),
            ('LEFTPADDING',  (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING',   (0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ]))
        return t

    elements = []

    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    logo_path       = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    hindi_name_path = os.path.join(current_app.root_path, 'static', 'img', 'hindi_name.png')

    prog_spec = (
        f"{safe_str(candidate.get('program_name'))}({safe_str(candidate.get('PreferenceSpec'))})"
        if candidate.get('PreferenceSpec')
        else safe_str(candidate.get('program_name'))
    )

    logo_cell = Image(logo_path, width=0.85*inch, height=0.85*inch) if os.path.exists(logo_path) else ''

    if os.path.exists(hindi_name_path):
        hindi_img = Image(hindi_name_path, width=3.2*inch, height=0.32*inch)
        center_col = [
            hindi_img,
            Paragraph("CCS Haryana Agricultural University", uni_name_style),
            Paragraph(f"Preferences filled for online Counselling for admission in {prog_spec} programme", sub_title_style),
        ]
    else:
        center_col = [
            Paragraph("CCS Haryana Agricultural University", uni_name_style),
            Paragraph(f"Preferences filled for online Counselling for admission in {prog_spec} programme", sub_title_style),
        ]

    # Wrap center column items in a nested table so they stack vertically
    center_inner = Table([[item] for item in center_col], colWidths=[5.27*inch])
    center_inner.setStyle(TableStyle([
        ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 1),
        ('BOTTOMPADDING',(0,0), (-1,-1), 1),
    ]))

    now_str_date = datetime.now().strftime("%d/%m/%Y")
    now_str_time = datetime.now().strftime("%I:%M:%S %p").lower()

    date_time_col = Table(
        [[Paragraph(f"Date : {now_str_date}", dt_style)],
         [Paragraph(f"Time : {now_str_time}", dt_right_style)]],
        colWidths=[1.15*inch]
    )
    date_time_col.setStyle(TableStyle([
        ('ALIGN',   (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 1),
        ('BOTTOMPADDING',(0,0), (-1,-1), 1),
    ]))

    header_table = Table(
        [[logo_cell, center_inner, date_time_col]],
        colWidths=[0.85*inch, 5.27*inch, 1.15*inch]
    )
    header_table.setStyle(TableStyle([
        ('ALIGN',   (0,0), (0,0), 'LEFT'),
        ('ALIGN',   (1,0), (1,0), 'CENTER'),
        ('ALIGN',   (2,0), (2,0), 'RIGHT'),
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',   (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',(0,0), (-1,-1), 0),
        ('LEFTPADDING',  (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4))

    # ─── Name / Reg / Roll row ────────────────────────────────────────────────
    full_name = f"{safe_str(candidate.get('s_name'))} {safe_str(candidate.get('s_surname'))}".replace(' NA','').replace('NA ','').strip()

    name_row = Table(
        [[Paragraph(f"Name : {full_name}", name_style),
          Paragraph(f"Registration No. : {safe_str(candidate.get('regno'))}", name_style),
          Paragraph(f"Roll No. : {safe_str(candidate.get('rollno'))}", name_right_style)]],
        colWidths=[2.42*inch, 2.62*inch, 2.23*inch]
    )
    name_row.setStyle(TableStyle([
        ('ALIGN',  (0,0), (-1,-1), 'LEFT'),
        ('ALIGN',  (2,0), (2,0),   'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    elements.append(name_row)
    elements.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════════════════════════════════
    # ENTRANCE MARKS / RANK  — full-width outer box
    # ═══════════════════════════════════════════════════════════════════════════
    marks_val = safe_str(candidate.get('EntranceMarks'))
    if marks_val.endswith('.00'):  marks_val = marks_val[:-3]
    elif marks_val.endswith('.0'): marks_val = marks_val[:-2]

    em_header = Table(
        [[Paragraph("Entrance Marks/Rank", sec_hdr_style)]],
        colWidths=[CONTENT_W - 2]
    )
    em_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    em_data = [
        [Paragraph('Entrance Marks :', cell_lbl_style),
         Paragraph(marks_val, cell_val_style),
         Paragraph('Category :', cell_lbl_style),
         Paragraph(safe_str(candidate.get('Category')), cell_val_style)],
        [Paragraph('Overall Rank :', cell_lbl_style),
         Paragraph(safe_str(candidate.get('OverallRank')), cell_val_style),
         Paragraph('Category Rank :', cell_lbl_style),
         Paragraph(safe_str(candidate.get('CategoryRank')), cell_val_style)],
    ]
    em_table = Table(em_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.27*inch])
    em_table.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    em_outer = Table(
        [[em_header], [em_table]],
        colWidths=[CONTENT_W]
    )
    em_outer.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.8, OUTER_BOX),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('LINEBELOW',     (0,0), (-1,0),  0.5, GRID_CLR),
    ]))
    elements.append(em_outer)
    elements.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════════════════════════════════
    # COLLEGE PREFERENCE
    # ═══════════════════════════════════════════════════════════════════════════
    cp_header = Table(
        [[Paragraph("College Preference", sec_hdr_style)]],
        colWidths=[CONTENT_W - 2]
    )
    cp_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    pref_rows = [[
        Paragraph('S.No', cell_lbl_style),
        Paragraph('College Name', cell_lbl_style),
        Paragraph('Preference', cell_lbl_style),
    ]]

    seen_colleges = set()
    display_idx = 1
    for p in rows:
        col_name = p.get('PreferenceCollege')
        if col_name and col_name not in seen_colleges:
            seen_colleges.add(col_name)
            pref_rows.append([
                Paragraph(str(display_idx), cell_val_style),
                Paragraph(safe_str(col_name), cell_val_style),
                Paragraph(str(p.get('Preference')), cell_val_style),
            ])
            display_idx += 1

    pref_table = Table(pref_rows, colWidths=[0.6*inch, 5.5*inch, 1.17*inch])
    pref_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',          (0,0), (-1,-1), 0.5, GRID_CLR),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    cp_outer = Table(
        [[cp_header], [pref_table]],
        colWidths=[CONTENT_W]
    )
    cp_outer.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.8, OUTER_BOX),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('LINEBELOW',     (0,0), (-1,0),  0.5, GRID_CLR),
    ]))
    elements.append(cp_outer)
    elements.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════════════════════════════════
    # INFO GRID  (LDV / FF / ESM / PH / etc.)
    # ═══════════════════════════════════════════════════════════════════════════
    def info_row(label1, val1, label2=None, val2=None):
        if label2 is None:
            return [
                Paragraph(label1, cell_lbl_style), Paragraph(f': {val1}', cell_val_style),
                '', ''
            ]
        return [
            Paragraph(label1, cell_lbl_style), Paragraph(f': {val1}', cell_val_style),
            Paragraph(label2, cell_lbl_style), Paragraph(f': {val2}', cell_val_style),
        ]

    ldv_val  = f"{safe_str(candidate.get('LDV'))}()"
    ff_val   = safe_str(candidate.get('FF'))
    esm_val  = f"{safe_str(candidate.get('ESM'))}(())"
    ph_val   = f"{safe_str(candidate.get('PH'))}(%)"
    ward_val = f"{safe_str(candidate.get('IsWard'))}(----)"
    sq_val   = safe_str(candidate.get('SportsQuota'))
    thesis_val = 'Yes' if has_thesis else 'No'

    info_grid_data = [
        info_row('Land Donated Village(LDV)', ldv_val,  'Freedom Fighter(FF) Category', ff_val),
        info_row('Ex-serviceman(ESM) Category', esm_val),
        info_row('Person with Disability', ph_val, 'In-service Candidate', 'NO(())'),
        info_row('Under CCS HAU Employee Ward-Ex-Gratia', ward_val),
        info_row('Candidate with fellowship from CSIR/UGC/ other Govt. organization', 'NO',
                 'Sports quota', sq_val),
        info_row('Thesis/ Dissertation', thesis_val),
    ]

    info_grid = Table(
        info_grid_data,
        colWidths=[2.4*inch, 1.3*inch, 2.2*inch, 1.37*inch]
    )
    info_grid.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('LINEBELOW',     (0,0), (-1,-2), 0.5, GRID_CLR),
        ('LINEBEFORE',    (2,0), (2,-1),  0.5, GRID_CLR),
    ]))

    info_outer = Table([[info_grid]], colWidths=[CONTENT_W])
    info_outer.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.8, OUTER_BOX),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    elements.append(info_outer)
    elements.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════════════════════════════════
    # SPORTS QUOTA
    # ═══════════════════════════════════════════════════════════════════════════
    sq_header = Table(
        [[Paragraph("Sports Quota", sec_hdr_style)]],
        colWidths=[CONTENT_W - 2]
    )
    sq_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    sq_rows = [[
        Paragraph('S.No',             cell_lbl_style),
        Paragraph('Game Name',        cell_lbl_style),
        Paragraph('Gradation',        cell_lbl_style),
        Paragraph('Participation Date', cell_lbl_style),
    ]]

    if sports_rows:
        for idx, s in enumerate(sports_rows, 1):
            sq_rows.append([
                Paragraph(str(idx), cell_val_style),
                Paragraph(safe_str(s.get('GameName')),  cell_val_style),
                Paragraph(safe_str(s.get('LevelName')), cell_val_style),
                Paragraph(safe_str(s.get('PartDate')),  cell_val_style),
            ])
    else:
        sq_rows.append([Paragraph('1', cell_val_style), '', '', ''])

    sq_table = Table(sq_rows, colWidths=[0.6*inch, 2.5*inch, 1.8*inch, 2.37*inch])
    sq_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',          (0,0), (-1,-1), 0.5, GRID_CLR),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    sq_outer = Table(
        [[sq_header], [sq_table]],
        colWidths=[CONTENT_W]
    )
    sq_outer.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.8, OUTER_BOX),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('LINEBELOW',     (0,0), (-1,0),  0.5, GRID_CLR),
    ]))
    elements.append(sq_outer)
    elements.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT DETAILS
    # ═══════════════════════════════════════════════════════════════════════════
    pd_header = Table(
        [[Paragraph("Payment Details", sec_hdr_style)]],
        colWidths=[CONTENT_W - 2]
    )
    pd_header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    pd_rows = [[
        Paragraph('S.No',          cell_lbl_style),
        Paragraph('Transition ID', cell_lbl_style),
        Paragraph('Amount',        cell_lbl_style),
        Paragraph('Payment Date',  cell_lbl_style),
    ]]

    if candidate.get('TransactionId'):
        amount_val = candidate.get('Amount', 0)
        try:
            amount_str = f"{float(amount_val):,.2f}"
        except (TypeError, ValueError):
            amount_str = safe_str(amount_val)

        pd_rows.append([
            Paragraph('1', cell_val_style),
            Paragraph(safe_str(candidate.get('TransactionId')), cell_val_style),
            Paragraph(amount_str, cell_val_style),
            Paragraph(safe_date_time_str(candidate.get('PaymentDate')), cell_val_style),
        ])
    else:
        pd_rows.append([Paragraph('1', cell_val_style), '', '', ''])

    pd_table = Table(pd_rows, colWidths=[0.6*inch, 2.5*inch, 1.8*inch, 2.37*inch])
    pd_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  GRAY_BG),
        ('ALIGN',         (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',          (0,0), (-1,-1), 0.5, GRID_CLR),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))

    pd_outer = Table(
        [[pd_header], [pd_table]],
        colWidths=[CONTENT_W]
    )
    pd_outer.setStyle(TableStyle([
        ('BOX',           (0,0), (-1,-1), 0.8, OUTER_BOX),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('LINEBELOW',     (0,0), (-1,0),  0.5, GRID_CLR),
    ]))
    elements.append(pd_outer)
    elements.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════════════════════
    # DECLARATION + SIGNATURE
    # ═══════════════════════════════════════════════════════════════════════════
    decl_text = (
        "I declare that the informations furnished in this form are correct to the best of my "
        "knowledge and belief.I am conscious that if any information is found incorrect, my "
        "admission is liable to be cancelled during my degree programme.I also certify that to "
        "the best of my knowledge,If fulfill the eligibility conditions for the course for which "
        "I am applying for admission."
    )

    # Signature block — bottom right, underlined label
    sig_block = Table(
        [[Paragraph("<u>Signature</u>", sig_style)]],
        colWidths=[1.5*inch]
    )
    sig_block.setStyle(TableStyle([
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))

    # Row that holds empty space left + signature label right
    sig_row = Table(
        [['' , sig_block]],
        colWidths=[CONTENT_W - 1.5*inch, 1.5*inch]
    )
    sig_row.setStyle(TableStyle([
        ('ALIGN',         (0,0), (0,0), 'LEFT'),
        ('ALIGN',         (1,0), (1,0), 'RIGHT'),
        ('VALIGN',        (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))

    decl_section = KeepTogether([
        Paragraph("<b>Declaration</b>", 
                  ParagraphStyle(name='DeclHdr', fontName='Helvetica-Bold', 
                                 fontSize=9, leading=12, spaceAfter=4,
                                 underlineProportion=0.05)),
        Paragraph(decl_text, decl_style),
        Spacer(1, 45),   # blank space for manual signature
        sig_row,
    ])

    elements.append(decl_section)

    # ═══════════════════════════════════════════════════════════════════════════
    # BUILD PDF
    # ═══════════════════════════════════════════════════════════════════════════
    doc.build(elements)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out