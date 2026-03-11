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

def generate_application_pdf(reg_id):
    # Fetch Candidate Data
    query = text("""
        SELECT 
            m.pk_regid, m.regno, m.s_name, m.s_surname, m.f_name, m.m_name, m.dob, m.mobileno, m.email,
            m.gender, m.Marital_Status, m.Blood_Group, m.familyId, m.AdharNo, nat.Name as nationality_name,
            m.c_address, m.c_district, m.c_pincode, m.p_address, m.p_district, m.p_pincode,
            m.Parents_Mobileno, m.ChildStatus, m.Resident, m.AnnualIncome, m.FatherOccupation,
            m.LDV, m.FF, m.ESM, m.PH, m.SportsQuota, m.IsWard, 
            m.Alive_Name, m.Alive_Depart, m.totfee as TotFee, m.PayMode, m.dated as SubmissionDate,
            pay.Tracking_id as TransactionId, m.PaymentSuccessTime as DateofDeposit,
            m.C_Village as Village_Name,
            sess.description as session_name,
            deg.description as program_name,
            col.CollegeName as college_name,
            rel.religiontype as religion_name,
            cat.Description as category_name
        FROM PA_Registration_Mst m
        LEFT JOIN LUP_AcademicSession_Mst sess ON m.fk_sessionid = sess.pk_sessionid
        LEFT JOIN ACD_Degree_Mst deg ON m.fk_dtypeid = deg.pk_degreeid
        LEFT JOIN PA_College_Mst col ON m.fk_CollegID = col.Pk_CollegeID
        LEFT JOIN Religion_Mst rel ON m.fk_religionid = rel.pk_religionid
        LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
        LEFT JOIN PA_Nationality_Mst nat ON m.nationality = nat.Code
        LEFT JOIN (
            SELECT Fk_regId, MIN(Tracking_id) as Tracking_id 
            FROM PA_OnlinePayment_Detail 
            WHERE PaymentStatus='Success' AND (isCounsellingFee=0 OR isCounsellingFee IS NULL)
            GROUP BY Fk_regId
        ) pay ON m.pk_regid = pay.Fk_regId
        WHERE m.pk_regid = :reg_id
    """)
    candidate = db.session.execute(query, {'reg_id': reg_id}).mappings().first()

    if not candidate:
        return None

    # Fetch Images
    img_query = text("SELECT imgattach_p, imgattach_s, imgattach_t FROM PA_Registration_Document WHERE fk_regid = :reg_id")
    imgs = db.session.execute(img_query, {'reg_id': reg_id}).mappings().first()

    # Mapping utilities
    def safe_str(val):
        if val is None:
            return ""
        if isinstance(val, bool):
            return "YES" if val else "NO"
        if isinstance(val, datetime):
            return val.strftime('%d/%m/%Y')
        if str(val).strip() == '0' and str(val).isdigit():
            return "NO"
        if str(val).strip() == '1' and str(val).isdigit():
            return "YES"
        return str(val)

    def safe_mark(val):
        if val is None:
            return ""
        val_str = str(val).strip()
        if val_str.endswith('.00'):
            return val_str[:-3]
        if val_str.endswith('.0'):
            return val_str[:-2]
        return val_str

    def safe_date_time_str(val):
        if val is None:
            return ""
        if isinstance(val, datetime):
            return val.strftime('%b %d %Y %#I:%M%p')
        return str(val)

    income_map = {
        '1': 'Up to 1 Lakh',
        '2': '1 Lakh- 3 Lakh',
        '4': '3 Lakh- 6 Lakh',
        '5': '6 Lakh- 8 Lakh',
        '6': 'More than 8 Lakh'
    }
    annual_income = safe_str(candidate.get('AnnualIncome'))
    if annual_income in income_map:
        annual_income = income_map[annual_income]

    blood_group = str(candidate.get('Blood_Group', '')).strip()
    bg_map = {'A +': 'A+', 'B +': 'B+', 'O +': 'O+', 'AB +': 'AB+', 'AP': 'A+', 'BP': 'B+', 'OP': 'O+', 'ABP': 'AB+', 'AN': 'A-', 'BN': 'B-', 'ON': 'O-', 'ABN': 'AB-'}
    if blood_group in bg_map:
        blood_group = bg_map[blood_group]

    # Set up the document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=1, fontSize=16, fontName='Helvetica-Bold', spaceAfter=8, leading=18))
    styles.add(ParagraphStyle(name='SubHeading', alignment=1, fontSize=12, fontName='Helvetica', spaceAfter=15))
    styles.add(ParagraphStyle(name='SectionTitle', alignment=0, fontSize=11, fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4, textColor=colors.HexColor('#000000')))
    styles.add(ParagraphStyle(name='NormalText', fontSize=8, fontName='Helvetica', leading=10))
    styles.add(ParagraphStyle(name='NormalTextBold', fontSize=8, fontName='Helvetica-Bold', leading=10))
    styles.add(ParagraphStyle(name='JustifiedText', fontSize=8, fontName='Helvetica', leading=10, alignment=4))

    # Header
    now_str = datetime.now().strftime("%d-%m-%Y %#I:%M:%S%p")
    elements.append(Paragraph(f"Form Downloaded Time :- {now_str}", styles['NormalText']))
    
    # Adding Logo & Hindi Name
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    hindi_name_path = os.path.join(current_app.root_path, 'static', 'img', 'hindi_name.png')
    
    header_data = []
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=0.8*inch, height=0.8*inch)
    else:
        logo_img = ''

    if os.path.exists(hindi_name_path):
        hindi_img = Image(hindi_name_path, width=3.8*inch, height=0.35*inch)
        header_data = [
            [logo_img, hindi_img],
            ['', Paragraph("CCS Haryana Agricultural University", styles['CenterHeading'])],
            ['', Paragraph("Hisar - 125004, Haryana, India.", styles['SubHeading'])]
        ]
        header_table = Table(header_data, colWidths=[1*inch, 6.27*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'), 
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('SPAN', (0,0), (0,-1))
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("CCS Haryana Agricultural University", styles['CenterHeading']))
        elements.append(Paragraph("Hisar - 125004, Haryana, India.", styles['SubHeading']))

    # Basic Info Table
    basic_info_data = [
        [Paragraph('Application ID', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('regno')), styles['NormalText']), Paragraph('Admission Session', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('session_name')), styles['NormalText'])],
        [Paragraph('Submitted Date&Time', styles['NormalTextBold']), Paragraph(safe_date_time_str(candidate.get('SubmissionDate')), styles['NormalText']), Paragraph('Program Name', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('program_name')), styles['NormalText'])],
        [Paragraph('College Name', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('college_name')), styles['NormalText']), Paragraph('Specialization', styles['NormalTextBold']), Paragraph('', styles['NormalText'])]
    ]
    
    t_basic = Table(basic_info_data, colWidths=[1.6*inch, 2.3*inch, 1.3*inch, 1.0*inch])
    t_basic.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    
    # Adding photo
    photo = ""
    if imgs and imgs.get('imgattach_p'):
        try:
            photo = Image(BytesIO(imgs['imgattach_p']), width=0.9*inch, height=1.1*inch)
        except:
            photo = ""
            
    header_table = Table([[t_basic, photo]], colWidths=[6.1*inch, 1.17*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), 
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    elements.append(header_table)

    # Personal Information
    elements.append(Paragraph("Personal Information", styles['SectionTitle']))
    
    full_name = f"{safe_str(candidate.get('s_name'))} {safe_str(candidate.get('s_surname'))}".strip()
    c_addr = f"{safe_str(candidate.get('c_address'))}, {safe_str(candidate.get('c_district'))} - {safe_str(candidate.get('c_pincode'))}"
    p_addr = f"{safe_str(candidate.get('p_address'))}, {safe_str(candidate.get('p_district'))} - {safe_str(candidate.get('p_pincode'))}"

    nat_name = safe_str(candidate.get('nationality_name')) if safe_str(candidate.get('nationality_name')) else 'INDIAN'
    marital = 'Unmarried' if safe_str(candidate.get('Marital_Status')) in ['NO', '0', ''] else 'Married'
    gender = 'MALE' if safe_str(candidate.get('gender')) == 'M' else ('FEMALE' if safe_str(candidate.get('gender')) == 'F' else safe_str(candidate.get('gender')))

    personal_info_data = [
        [Paragraph('Name of the Applicant', styles['NormalTextBold']), Paragraph(full_name, styles['NormalText']), Paragraph('Religion', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('religion_name')), styles['NormalText'])],
        [Paragraph('Nationality', styles['NormalTextBold']), Paragraph(nat_name, styles['NormalText']), Paragraph('Date of Birth', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('dob')), styles['NormalText'])],
        [Paragraph('Marital Status', styles['NormalTextBold']), Paragraph(marital, styles['NormalText']), Paragraph('Gender', styles['NormalTextBold']), Paragraph(gender, styles['NormalText'])],
        [Paragraph("Father's Name", styles['NormalTextBold']), Paragraph(safe_str(candidate.get('f_name')), styles['NormalText']), Paragraph('Mobile Number', styles['NormalTextBold']), Paragraph(f"+91 - {safe_str(candidate.get('mobileno'))}", styles['NormalText'])],
        [Paragraph("Mother's Name", styles['NormalTextBold']), Paragraph(safe_str(candidate.get('m_name')), styles['NormalText']), Paragraph('Email ID', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('email')), styles['NormalText'])],
        [Paragraph('Region', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Region', 'Rural')), styles['NormalText']), Paragraph('Category', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('category_name')), styles['NormalText'])],
        [Paragraph('Parents Mobile Number', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Parents_Mobileno')), styles['NormalText']), Paragraph('Blood Group', styles['NormalTextBold']), Paragraph(blood_group, styles['NormalText'])],
        [Paragraph('Candidate is a Only Girl Child', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('ChildStatus')), styles['NormalText']), Paragraph('Family ID', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('familyId')), styles['NormalText'])],
        [Paragraph('Permanent Address', styles['NormalTextBold']), Paragraph(p_addr, styles['NormalText']), Paragraph('Correspondence Address', styles['NormalTextBold']), Paragraph(c_addr, styles['NormalText'])]
    ]
    
    t_personal = Table(personal_info_data, colWidths=[2.0*inch, 1.6*inch, 1.6*inch, 2.07*inch])
    t_personal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_personal)

    # Qualification Details
    elements.append(Paragraph("Qualification Details", styles['SectionTitle']))
    
    qual_query = text("""
        SELECT 
            e.fk_EID, e.Year, b.Description as BoardName, e.RollNo, e.MaxMark, e.ObtOrOGPA, e.Percentage, e.Subject, e.Other_board_Univ,
            q.Description as EduName
        FROM ACD_EducationQualification_Details e
        LEFT JOIN ACD_EducationQualification_Mst q ON e.fk_EID = q.Pk_EID
        LEFT JOIN PA_Board_Mst b ON e.fk_BoardId = b.Pk_BoardId
        WHERE e.fk_regid = :reg_id
        ORDER BY e.fk_EID ASC
    """)
    quals = db.session.execute(qual_query, {'reg_id': reg_id}).mappings().all()

    qual_data = [[
        Paragraph('S.No.', styles['NormalTextBold']), 
        Paragraph('Education', styles['NormalTextBold']), 
        Paragraph('Year of Passing', styles['NormalTextBold']), 
        Paragraph('Board / University', styles['NormalTextBold']), 
        Paragraph('Admission No / Enrollment No', styles['NormalTextBold']), 
        Paragraph('Max. Marks', styles['NormalTextBold']), 
        Paragraph('Marks obtained / OGPA/CGPA', styles['NormalTextBold']), 
        Paragraph('%age', styles['NormalTextBold']), 
        Paragraph('Subjects', styles['NormalTextBold'])
    ]]
    for idx, q in enumerate(quals, 1):
        board_name = q.get('BoardName') if q.get('BoardName') else q.get('Other_board_Univ')
        qual_data.append([
            Paragraph(str(idx), styles['NormalText']),
            Paragraph(safe_str(q.get('EduName')), styles['NormalText']),
            Paragraph(safe_str(q.get('Year')), styles['NormalText']),
            Paragraph(safe_str(board_name), styles['NormalText']),
            Paragraph(safe_str(q.get('RollNo')), styles['NormalText']),
            Paragraph(safe_mark(q.get('MaxMark')), styles['NormalText']),
            Paragraph(safe_mark(q.get('ObtOrOGPA')), styles['NormalText']),
            Paragraph(safe_str(q.get('Percentage')), styles['NormalText']),
            Paragraph(safe_str(q.get('Subject')), styles['NormalText'])
        ])

    t_qual = Table(qual_data, colWidths=[0.3*inch, 0.8*inch, 0.6*inch, 1.1*inch, 1.0*inch, 0.5*inch, 0.6*inch, 0.6*inch, 1.77*inch])
    t_qual.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e0e0')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_qual)
    elements.append(Paragraph("* Result Declared", styles['NormalText']))

    # Other Information
    elements.append(Paragraph("Other Information", styles['SectionTitle']))
    other_info_data = [
        [Paragraph('Applicable for LDV', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('LDV')), styles['NormalText']), Paragraph('Village Name', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Village_Name')) if safe_str(candidate.get('Village_Name')) else 'NA', styles['NormalText'])],
        [Paragraph('Freedom Fighter', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('FF')), styles['NormalText']), Paragraph('Ex-Servicemen Category', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('ESM')), styles['NormalText'])],
        [Paragraph('Are you the person with Disability ?', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('PH')), styles['NormalText']), Paragraph('Are you from Sports quota?', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('SportsQuota')), styles['NormalText'])],
        [Paragraph('Are you a ward of University Employee ?', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('IsWard')), styles['NormalText']), Paragraph('HAU Employee Ward -Ex-Gratia ?', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('HAU_Employee_Ward')) if safe_str(candidate.get('HAU_Employee_Ward')) else 'NO', styles['NormalText'])],
        [Paragraph('Employee Name', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Alive_Name')) if safe_str(candidate.get('Alive_Name')) else 'NA', styles['NormalText']), Paragraph('Department', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Alive_Depart')) if safe_str(candidate.get('Alive_Depart')) else 'NA', styles['NormalText'])],
        [Paragraph('Father / Guardian', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('FatherOccupation')) if safe_str(candidate.get('FatherOccupation')) else 'Father', styles['NormalText']), Paragraph('Annual Income', styles['NormalTextBold']), Paragraph(annual_income, styles['NormalText'])],
        [Paragraph('Resident (Domicile)', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('Resident')) if safe_str(candidate.get('Resident')) else 'Haryana', styles['NormalText']), Paragraph('Aadhar Card No', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('AdharNo')), styles['NormalText'])],
        [Paragraph('Are you Ex-Student of HAU?', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('IsExStudent')) if safe_str(candidate.get('IsExStudent')) else 'NO', styles['NormalText']), Paragraph('Old Admission No', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('OldAdmissionNo')) if safe_str(candidate.get('OldAdmissionNo')) else 'NA', styles['NormalText'])],
        [Paragraph('Degree Name', styles['NormalTextBold']), Paragraph('NA', styles['NormalText']), Paragraph('Status (Complete/ Incomplete)', styles['NormalTextBold']), Paragraph('NA', styles['NormalText'])],
        [Paragraph('Migration Certificate is taken from HAU?', styles['NormalTextBold']), Paragraph('NO', styles['NormalText']), Paragraph('Other Information', styles['NormalTextBold']), Paragraph('NA', styles['NormalText'])],
    ]
    t_other = Table(other_info_data, colWidths=[2.4*inch, 1.2*inch, 2.47*inch, 1.2*inch])
    t_other.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_other)

    # Payment Details
    elements.append(Paragraph("Payment Details", styles['SectionTitle']))
    payment_data = [
        [Paragraph('Transaction Id', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('TransactionId')), styles['NormalText']), Paragraph('Amount', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('TotFee')), styles['NormalText'])],
        [Paragraph('Date of Deposit', styles['NormalTextBold']), Paragraph(safe_date_time_str(candidate.get('DateofDeposit')), styles['NormalText']), Paragraph('Paymode', styles['NormalTextBold']), Paragraph(safe_str(candidate.get('PayMode')), styles['NormalText'])]
    ]
    t_pay = Table(payment_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.87*inch])
    t_pay.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_pay)
    elements.append(Spacer(1, 10))

    # Signatures & Thumb
    sign_img = ""
    thumb_img = ""
    if imgs:
        try:
            if imgs.get('imgattach_s'):
                sign_img = Image(BytesIO(imgs['imgattach_s']), width=1.5*inch, height=0.45*inch)
            if imgs.get('imgattach_t'):
                thumb_img = Image(BytesIO(imgs['imgattach_t']), width=1.5*inch, height=0.45*inch)
        except:
            pass

    # Declaration
    elements.append(KeepTogether([
        Paragraph("Declaration", styles['SectionTitle']),
        Paragraph("I hereby affirm that the information given by me in this admission form is complete and true to the best of my knowledge and belief and nothing has been concealed and that I have made this application with the consent and approval of my parent/guardian. In the event of my being admitted to one of the constituent Colleges, I undertake to abide by disciplinary and other rules and regulations of the College and the University. Any rule framed/amended after my admission shall also be binding upon me.If at any time, it is found that I had obtained admission by misrepresentation of facts or that the admission was made erroneously I understand that the admission can be cancelled and fees and all other dues paid upto the date of such removal shall be forfeited besides other action as may be taken against me according to law. I will abide by the rule of 75% attendance for being eligible to appear in the examination.If my attendance in aggregate is below 33% my name may be struck off and I shall not request for re-admission. I will abide by rules regarding Curbing the Menace of Ragging, 2009.", styles['JustifiedText']),
        Spacer(1, 3),
        Paragraph("<b>For claiming any reservation/benefits , candidate is required to upload the documents at the time of counselling.</b>", styles['NormalText']),
        Spacer(1, 3),
        Paragraph("<b>Note : Your application has been successfully submitted to CCSHAU, Hisar. You are not required to send any Documents or Application PDF to the University.</b>", styles['NormalText']),
        Spacer(1, 10),
        Table([
            [sign_img, thumb_img], 
            [Paragraph("Candidate's Signature", ParagraphStyle(name='C', alignment=1, fontSize=8, fontName='Helvetica-Bold')), 
             Paragraph("Candidate's Thumb Impression", ParagraphStyle(name='C', alignment=1, fontSize=8, fontName='Helvetica-Bold'))]
        ], colWidths=[2.5*inch, 2.5*inch], 
        style=TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black), 
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4)
        ]))
    ]))

    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = "Page %s of 2" % page_num
        canvas.drawRightString(7.5*inch, 0.4*inch, text)

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out