from flask import Blueprint, render_template, request, flash, url_for, redirect, send_file, make_response, jsonify
from app import db
from sqlalchemy import text
import io
from app.utils_pdf import render_to_pdf
from datetime import datetime

merit_reports_bp = Blueprint('merit_reports', __name__, url_prefix='/merit-reports')

def safe_all(func, default_val=None):
    try:
        return func()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return default_val if default_val is not None else []

def get_common_masters():
    sessions = safe_all(lambda: db.session.execute(text("SELECT pk_sessionid as id, description as name FROM LUP_AcademicSession_Mst ORDER BY pk_sessionid DESC")).mappings().all(), [])
    degrees = safe_all(lambda: db.session.execute(text("SELECT pk_degreeid as id, description as name FROM ACD_Degree_Mst WHERE active=1 ORDER BY description")).mappings().all(), [])
    colleges = safe_all(lambda: db.session.execute(text("SELECT Pk_CollegeID as id, CollegeName as name FROM PA_College_Mst ORDER BY CollegeName")).mappings().all(), [])
    return sessions, degrees, colleges


@merit_reports_bp.before_request
def check_admin_auth():
    from flask import session, redirect, url_for, flash, request
    if not session.get('user_id'):
        if request.endpoint and 'login' not in request.endpoint:
            flash('Please login to access this section.', 'error')
            return redirect(url_for('main.login'))

@merit_reports_bp.route('/check-documents', methods=['GET', 'POST'])
def check_documents():
    sessions, degrees, colleges = get_common_masters()
    students = []
    form_data = {'session_id': '71', 'degree_type_id': '', 'college_id': '', 'status': '1', 'reg_no': ''}

    if request.method == 'POST':
        form_data.update(request.form)

        where_clauses = []
        params = {}

        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']

        if form_data['degree_type_id'] and form_data['degree_type_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_type_id']

        if form_data['reg_no']:
            where_clauses.append("m.regno = :reg_no")
            params['reg_no'] = form_data['reg_no']
            
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("cm.fk_collegeid = :college_id")
            params['college_id'] = form_data['college_id']

        if form_data['status'] == '2':
            where_clauses.append("mt.ProcessStatus IS NOT NULL AND mt.ProcessStatus != ''")
        elif form_data['status'] == '3':
            where_clauses.append("(mt.ProcessStatus IS NULL OR mt.ProcessStatus = '')")

        where_str = " AND ".join(where_clauses)
        if where_str:
            where_str = "WHERE " + where_str

        query = f"""
            SELECT DISTINCT
                m.pk_regid,
                m.regno,
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as student_name,
                m.mobileno,
                d.description as degree_name,
                c.Description as category_name,
                m.Resident as resident,
                m.rollno,
                ISNULL(CAST(cm.ObtainMarks as VARCHAR), '') as obtain_marks, 
                ISNULL(b.Description, eq.Other_board_Univ) as board_name,
                ISNULL(mt.ProcessStatus, '') as status,
                ISNULL(mt.ProcessRemarks, '') as reason
            FROM PA_Registration_Mst m
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            LEFT JOIN PA_StudentCategory_Mst c ON m.fk_stucatid_cast = c.Pk_StuCatId
            INNER JOIN PA_Candidate_Marks cm ON m.rollno = cm.RollNo AND m.fk_sessionid = cm.fk_sessionid
            LEFT JOIN (
                SELECT fk_regid, fk_BoardId, Other_board_Univ,
                       ROW_NUMBER() OVER(PARTITION BY fk_regid ORDER BY fk_EID DESC) as rn
                FROM ACD_EducationQualification_Details
            ) eq ON eq.fk_regid = m.pk_regid AND eq.rn = 1
            LEFT JOIN PA_Board_Mst b ON eq.fk_BoardId = b.Pk_BoardId
            LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
            WHERE m.IsPaymentSuccessCouns = 1 
              AND m.pk_regid IN (SELECT Fk_regId FROM PA_CandidateAttachment_Details)
              {(' AND ' + ' AND '.join(where_clauses)) if where_clauses else ''}
            ORDER BY ISNULL(CAST(cm.ObtainMarks as VARCHAR), '') DESC, m.regno ASC
        """

        try:
            students = db.session.execute(text(query), params).mappings().all()
        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "error")

    return render_template('merit_reports/check_documents.html', sessions=sessions, degrees=degrees, colleges=colleges, students=students, form_data=form_data)


@merit_reports_bp.route('/view_candidate_documents/<int:reg_id>', methods=['GET'])
def view_candidate_documents(reg_id):
    query = text("""
        SELECT d.PkId, d.AttachmentName as file_name, d.OldAttachmentName as old_name, 
               m.AttachmentType as type, m.MaxSizeInMB, d.Description, d.IsReject,
               d.InputBasedAlias
        FROM PA_CandidateAttachment_Details d 
        LEFT JOIN PA_Attachment_Mst m ON d.fk_attachmentId = m.Pk_attachmentId 
        WHERE d.Fk_regId = :reg_id
    """)
    rows = db.session.execute(query, {'reg_id': reg_id}).mappings().all()
    
    docs_section1 = []
    docs_section2 = []
    for r in rows:
        if r['type'] is not None:
            docs_section1.append(r)
        else:
            docs_section2.append(r)
            
    return render_template('merit_reports/_candidate_documents_partial.html', 
                           docs_section1=docs_section1, docs_section2=docs_section2, reg_id=reg_id)

import os
from flask import send_from_directory, current_app

@merit_reports_bp.route('/download_document/<int:pkid>', methods=['GET'])
def download_document(pkid):
    # Fetch document metadata
    query = text("SELECT AttachmentFileName, AttachmentName, ContentType FROM PA_CandidateAttachment_Details WHERE PkId = :pkid")
    doc = db.session.execute(query, {'pkid': pkid}).mappings().first()
    
    if not doc:
        return "Document not found", 404

    file_name = doc['AttachmentFileName']
    
    # Try to locate the file in local Uploads directory (assuming user might have mapped it)
    # Common paths where the physical Uploads folder might be placed by the user
    possible_upload_dirs = [
        os.path.join(current_app.root_path, '..', 'Uploads', 'CandidateDocuments'),
        os.path.join(current_app.root_path, 'static', 'uploads'),
        os.path.join('C:\\', 'inetpub', 'wwwroot', 'Preadm', 'Uploads', 'CandidateDocuments')
    ]
    
    for upload_dir in possible_upload_dirs:
        if os.path.exists(os.path.join(upload_dir, file_name)):
            return send_from_directory(upload_dir, file_name)

    # Fallback: Generate a PDF response as a placeholder indicating the file is missing locally
    context = {"reg_id": pkid, "title": f"Document Missing Locally: {doc['AttachmentName']}", "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    pdf_bytes = render_to_pdf("merit_reports/dummy_pdf.html", context)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{doc["AttachmentName"]}"'
        return response
        
    return "Error generating document view", 500

@merit_reports_bp.route('/application_print/<int:reg_id>', methods=['GET'])
def application_print(reg_id):
    from app.pdf_application_generator import generate_application_pdf
    pdf_bytes = generate_application_pdf(reg_id)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=application_{reg_id}.pdf'
        return response
    return "Error generating PDF", 500
@merit_reports_bp.route('/couns_print/<int:reg_id>', methods=['GET'])
def couns_print(reg_id):
    from app.pdf_couns_generator import generate_couns_pdf
    pdf_bytes = generate_couns_pdf(reg_id)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=couns_{reg_id}.pdf'
        return response
    else:
        return "Could not generate PDF", 500

@merit_reports_bp.route('/score_card_print/<int:reg_id>', methods=['GET'])
def score_card_print(reg_id):
    from app.pdf_score_card_generator import generate_score_card_pdf
    pdf_bytes = generate_score_card_pdf(reg_id)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=score_card_{reg_id}.pdf'
        return response
    else:
        return "Could not generate Score Card PDF", 500


@merit_reports_bp.route('/filled-vacant-seat', methods=['GET', 'POST'])
def filled_vacant_seat():
    sessions, degrees, colleges = get_common_masters()
    form_data = {'session_id': '71', 'degree_type_id': '', 'college_id': '0', 'cutoff': '1', 'report_for': '0'}
    results = []
    show_grid = False

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action')
        
        session_id = form_data.get('session_id')
        degree_type_id = form_data.get('degree_type_id')
        college_id = form_data.get('college_id')
        cutoff = form_data.get('cutoff', '1')
        report_for = form_data.get('report_for', '0')
        
        if session_id and degree_type_id and session_id != '0' and degree_type_id != '0':
            params = {'session_id': session_id, 'degree_id': degree_type_id, 'cutoff': cutoff}
            
            # 1. Fetch Seat Matrix (Total Seats) from PA_College_Spec_Map
            seat_sql = """
                SELECT 
                    d.description AS Degree,
                    c.collegename AS AllotedCollege,
                    :cutoff AS CutOff,
                    s.Specialization AS Specialization,
                    m.seat AS seat,
                    m.fk_collegeID,
                    m.fk_sid
                FROM PA_College_Spec_Map m
                JOIN ACD_Degree_Mst d ON m.fk_degreeid = d.pk_degreeid
                JOIN SMS_College_Mst c ON m.fk_collegeID = c.pk_collegeid
                JOIN PA_Specialization_mst s ON m.fk_sid = s.Pk_SID
                WHERE m.fk_sessionID = :session_id AND m.fk_degreeid = :degree_id
            """
            if college_id and college_id != '0':
                # Note: filter by SMS college ID if provided, but we need to find which SMS colleges map to the selected PA college
                # Actually, the form provides PA_College_Mst IDs in get_common_masters()
                seat_sql += " AND c.fk_Parentcollege_mst = :college_id "
                params['college_id'] = college_id

            try:
                seats_data = db.session.execute(text(seat_sql), params).mappings().all()
                
                # 2. Fetch Allotted Counts (Filled Seats) from PA_Merit_Trn & PA_Merit_Bsc_Trn
                # We group by SMS college ID and Specialization ID
                merit_sql = """
                    SELECT 
                        U.fk_allotedcollegeid,
                        U.fk_sid,
                        COUNT(*) as filled_count
                    FROM (
                        SELECT t.fk_allotedcollegeid, t.AllottedSpec as fk_sid
                        FROM PA_Merit_Trn t
                        JOIN PA_Merit_Mst mm ON t.Fk_MeritID = mm.Pk_MeritID
                        WHERE mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id AND mm.CutOff = :cutoff
                        
                        UNION ALL
                        
                        SELECT t.AllottedCollegeID as fk_allotedcollegeid, NULL as fk_sid -- B.Sc. uses SubjectName usually, but we need an ID
                        FROM PA_Merit_Bsc_Trn t
                        JOIN PA_Merit_Mst mm ON t.Fk_MeritID = mm.Pk_MeritID
                        WHERE mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id AND mm.CutOff = :cutoff
                    ) U
                    GROUP BY U.fk_allotedcollegeid, U.fk_sid
                """
                
                filled_data = db.session.execute(text(merit_sql), params).mappings().all()
                
                # Create a map for quick lookup: key is (college_id, sid)
                filled_map = {}
                for row in filled_data:
                    key = (row['fk_allotedcollegeid'], row['fk_sid'])
                    filled_map[key] = row['filled_count']
                
                # 3. Combine results
                for row in seats_data:
                    total_seats = int(row['seat']) if row['seat'] else 0
                    key = (row['fk_collegeID'], row['fk_sid'])
                    filled_seats = filled_map.get(key, 0)
                    vacant_seats = total_seats - filled_seats
                    
                    res_row = {
                        "Degree": row['Degree'],
                        "AllotedCollege": row['AllotedCollege'],
                        "CutOff": row['CutOff'],
                        "Specialization": row['Specialization'],
                        "seat": total_seats
                    }
                    
                    if report_for == '0': # Vacant
                        res_row["VacantSeat"] = vacant_seats
                    else: # Filled
                        res_row["FilledSeat"] = filled_seats
                        res_row["UnfilledSeat"] = vacant_seats
                        
                    results.append(res_row)
                    
                show_grid = True
                
                if action == 'export':
                    is_vacant = (report_for == '0')
                    # Generate simple HTML table for Excel export (mimicking the original behavior)
                    html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    .table-grid-view td, .table-grid-view th {{ border: 1px solid #B0B0B0; padding: 5px; font-family: Arial, sans-serif; font-size: 11pt; }}
    .header-style th {{ background-color: #5D7B9D; color: white; font-weight: bold; }}
</style>
</head>
<body>
<table class="table-grid-view" cellspacing="1" cellpadding="5" rules="all" border="1" style="border:1px solid #B0B0B0;border-collapse:collapse; width:100%;">
    <tr class="header-style">
        <th>Degree</th><th>AllotedCollege</th><th>CutOff</th><th>Specialization</th><th>seat</th>"""
                    
                    if is_vacant:
                        html += "<th>VacantSeat</th>"
                    else:
                        html += "<th>FilledSeat</th><th>UnfilledSeat</th>"
                    html += "</tr>"
                    
                    for index, row in enumerate(results):
                        bg_color = "White" if index % 2 == 0 else "#F7F6F3"
                        html += f'<tr style="background-color:{bg_color}; color:#333333; text-align:center; height:25px;">'
                        html += f'<td>{row["Degree"]}</td><td>{row["AllotedCollege"]}</td><td>{row["CutOff"]}</td><td>{row["Specialization"]}</td><td>{row["seat"]}</td>'
                        if is_vacant:
                            html += f'<td>{row["VacantSeat"]}</td>'
                        else:
                            html += f'<td>{row.get("FilledSeat", 0)}</td><td>{row.get("UnfilledSeat", 0)}</td>'
                        html += '</tr>'
                        
                    html += "</table></body></html>"
                    
                    filename = "PA_VacantSeat_Report.xls" if is_vacant else "PA_FilledSeat_Report.xls"
                    response = make_response(html)
                    response.headers['Content-Type'] = 'application/vnd.ms-excel'
                    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
                    return response
                    
            except Exception as e:
                flash(f"Error fetching data: {str(e)}", "error")
        else:
            flash("Session and Degree Type are required.", "warning")

    return render_template('merit_reports/filled_vacant_seat.html', 
                           sessions=sessions, degrees=degrees, colleges=colleges, 
                           form_data=form_data, results=results, show_grid=show_grid)


@merit_reports_bp.route('/student-upward-upgradation', methods=['GET', 'POST'])
def student_upward_upgradation():
    sessions, degrees, colleges = get_common_masters()
    form_data = {'session_id': '71', 'degree_type_id': '', 'college_id': '', 'cutoff': '0'}
    students = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action')
        
        where_clauses = []
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("mm.Fk_SessionID = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_type_id'] and form_data['degree_type_id'] != '0':
            where_clauses.append("mm.Fk_DegreeID = :degree_id")
            params['degree_id'] = form_data['degree_type_id']
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("mt.Fk_CollegeID = :college_id")
            params['college_id'] = form_data['college_id']
        if form_data['cutoff'] and form_data['cutoff'] != '0':
            where_clauses.append("u.fk_CutOff = :cutoff")
            params['cutoff'] = form_data['cutoff']
        
        where_str = " AND ".join(where_clauses)
        if where_str:
            where_str = "WHERE " + where_str

        query = f"""
            SELECT DISTINCT
                m.pk_regid,
                m.regno,
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as student_name,
                d.description as degree_name,
                col.CollegeName as college_name,
                CASE WHEN u.IsUpwardUpgradation = 1 THEN 'Yes' ELSE 'No' END as is_upward,
                CASE WHEN u.IsWithdraw = 1 THEN 'Yes' ELSE 'No' END as is_withdraw,
                u.fk_CutOff as cutoff
            FROM pa_Student_Upward_Upgradation_mst u
            JOIN PA_Registration_Mst m ON u.fk_RegId = m.pk_regid
            JOIN PA_Merit_Trn mt ON m.pk_regid = mt.fk_regid
            JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
            LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
            LEFT JOIN PA_College_Mst col ON mt.Fk_CollegeID = col.Pk_CollegeID
            {where_str}
            ORDER BY m.regno
        """
        try:
            students = db.session.execute(text(query), params).mappings().all()
            
            if action == 'export':
                html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    .table-grid-view td, .table-grid-view th {{ border: 1px solid #B0B0B0; padding: 5px; font-family: Arial, sans-serif; font-size: 11pt; }}
    .header-style th {{ background-color: #5D7B9D; color: white; font-weight: bold; }}
</style>
</head>
<body>
<table class="table-grid-view" cellspacing="1" cellpadding="5" rules="all" border="1" style="border:1px solid #B0B0B0;border-collapse:collapse; width:100%;">
    <tr class="header-style">
        <th>S.No.</th>
        <th>Candidate Name</th>
        <th>Registration Number</th>
        <th>Degree Name</th>
        <th>College</th>
        <th>Upward Upgradation</th>
        <th>Is Withdraw</th>
        <th>CutOff</th>
    </tr>"""
                for index, student in enumerate(students):
                    bg_color = "White" if index % 2 == 0 else "#F7F6F3"
                    html += f'<tr style="background-color:{bg_color}; color:#333333; text-align:center; height:25px;">'
                    html += f'<td>{index + 1}</td>'
                    html += f'<td style="text-align:left;">{student.student_name}</td>'
                    html += f'<td>{student.regno}</td>'
                    html += f'<td style="text-align:left;">{student.degree_name}</td>'
                    html += f'<td style="text-align:left;">{student.college_name}</td>'
                    html += f'<td>{student.is_upward}</td>'
                    html += f'<td>{student.is_withdraw}</td>'
                    html += f'<td>{student.cutoff}</td>'
                    html += '</tr>'
                html += "</table></body></html>"
                
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=PA_UpwardUpgradation_Report.xls'
                return response
                
        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "error")

    return render_template('merit_reports/student_upward_upgradation.html', sessions=sessions, degrees=degrees, colleges=colleges, students=students, form_data=form_data)

@merit_reports_bp.route('/final-seat-allocation', methods=['GET', 'POST'])
def final_seat_allocation():
    sessions, degrees, colleges = get_common_masters()
    form_data = {'session_id': '71', 'degree_type_id': '', 'college_id': ''}
    
    if request.method == 'POST':
        form_data.update(request.form)
        
        session_id = form_data.get('session_id')
        degree_id = form_data.get('degree_type_id')
        college_id = form_data.get('college_id')
        
        if not session_id or not degree_id or session_id == '0' or degree_id == '0':
            flash("Session and Degree Type are required.", "warning")
            return render_template('merit_reports/final_seat_allocation.html', sessions=sessions, degrees=degrees, colleges=colleges, form_data=form_data)
        
        params = {'session_id': session_id, 'degree_id': degree_id}
        
        # Build where clause
        where_pg = "mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id"
        where_ug = "mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id"
        
        if college_id and college_id != '0':
            where_pg += " AND mt.Fk_CollegeID = :college_id"
            where_ug += " AND mt.AllottedCollegeID = :college_id" # This might be SMS college or PA college depending on schema
            params['college_id'] = college_id
            
        query = f"""
            SELECT 
                m.regno, 
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as Name, 
                c.Description as Category, 
                d.description as Degree, 
                pc.CollegeName as collegeName, 
                mm.CutOff as cutoff, 
                mt.AllottedCategory, 
                sc.collegename as AllottedCollege, 
                mt.AllottedSpecialisation as AllotedSpecialization
            FROM PA_Merit_Trn mt
            JOIN PA_Registration_Mst m ON mt.fk_regid = m.pk_regid
            JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
            LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
            LEFT JOIN PA_College_Mst pc ON mt.Fk_CollegeID = pc.Pk_CollegeID
            LEFT JOIN SMS_College_Mst sc ON mt.fk_allotedcollegeid = sc.pk_collegeid
            LEFT JOIN PA_StudentCategory_Mst c ON m.fk_stucatid_cast = c.Pk_StuCatId
            WHERE {where_pg}
            
            UNION ALL
            
            SELECT 
                m.regno, 
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as Name, 
                c.Description as Category, 
                d.description as Degree, 
                pc.CollegeName as collegeName, 
                mm.CutOff as cutoff, 
                mt.AllottedCategory, 
                mt.AllottedCollege as AllottedCollege, 
                mt.SubjectName as AllotedSpecialization
            FROM PA_Merit_Bsc_Trn mt
            JOIN PA_Registration_Mst m ON mt.fk_regid = m.pk_regid
            JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
            LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
            LEFT JOIN PA_College_Mst pc ON mt.AllottedCollegeID = pc.Pk_CollegeID
            LEFT JOIN PA_StudentCategory_Mst c ON m.fk_stucatid_cast = c.Pk_StuCatId
            WHERE {where_ug}
            
            ORDER BY Name
        """
        
        try:
            records = db.session.execute(text(query), params).mappings().all()
            
            html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    .table-grid-view td, .table-grid-view th {{ border: 1px solid #B0B0B0; padding: 5px; font-family: Arial, sans-serif; font-size: 11pt; }}
    .header-style th {{ background-color: #5D7B9D; color: white; font-weight: bold; }}
</style>
</head>
<body>
<div id="Anthem_ctl00_ContentPlaceHolder1_dgExport__">
<table class="table-grid-view" cellspacing="1" cellpadding="1" rules="all" border="1" id="ctl00_ContentPlaceHolder1_dgExport" style="border:1px solid #B0B0B0;border-collapse:collapse; margin:15px 0;">
    <tr class="header-style">
        <th>SNo</th><th>regno</th><th>Name</th><th>Category</th><th>Degree</th><th>collegeName</th><th>cutoff</th><th>AllottedCategory</th><th>AllottedCollege</th><th>AllotedSpecialization</th>
    </tr>"""
            
            for index, row in enumerate(records):
                bg_color = "White" if index % 2 == 0 else "#F8F8F8"
                html += f'<tr class="dgitem-style" style="background-color:{bg_color};">'
                html += f'<td>{index + 1}</td>'
                html += f'<td>{row["regno"]}</td>'
                html += f'<td>{row["Name"]}</td>'
                html += f'<td>{row["Category"] or ""}</td>'
                html += f'<td>{row["Degree"] or ""}</td>'
                html += f'<td>{row["collegeName"] or ""}</td>'
                html += f'<td>{row["cutoff"] or ""}</td>'
                html += f'<td>{row["AllottedCategory"] or ""}</td>'
                html += f'<td>{row["AllottedCollege"] or ""}</td>'
                html += f'<td>{row["AllotedSpecialization"] or ""}</td>'
                html += '</tr>'
                
            html += "</table></div></body></html>"
            
            # Fetch Degree Name for the filename
            degree_name = "Allocation"
            if records and records[0]["Degree"]:
                degree_name = records[0]["Degree"].replace(" ", "_").replace("/", "_")
            
            response = make_response(html)
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
            response.headers['Content-Disposition'] = f'attachment; filename=Final_Admitted_{degree_name}.xls'
            return response
            
        except Exception as e:
            flash(f"Error generating report: {str(e)}", "error")
        
    return render_template('merit_reports/final_seat_allocation.html', sessions=sessions, degrees=degrees, colleges=colleges, form_data=form_data)

@merit_reports_bp.route('/collegewise-departmentwise', methods=['GET', 'POST'])
def collegewise_departmentwise():
    sessions, degrees, colleges = get_common_masters()
    form_data = {'session_id': '71', 'degree_type_id': '', 'college_id': '', 'cutoff': '0', 'report_type': '0'}
    
    if request.method == 'POST':
        form_data.update(request.form)
        
        session_id = form_data.get('session_id')
        degree_id = form_data.get('degree_type_id')
        college_id = form_data.get('college_id')
        cutoff = form_data.get('cutoff')
        report_type = form_data.get('report_type')
        
        if not session_id or not degree_id or session_id == '0' or degree_id == '0':
            flash("Session and Degree Type are required.", "warning")
            return render_template('merit_reports/collegewise_departmentwise.html', sessions=sessions, degrees=degrees, colleges=colleges, form_data=form_data)
            
        if report_type not in ['1', '2']:
            flash("Please select a valid Report Type.", "warning")
            return render_template('merit_reports/collegewise_departmentwise.html', sessions=sessions, degrees=degrees, colleges=colleges, form_data=form_data)
        
        params = {'session_id': session_id, 'degree_id': degree_id}
        where_pg = "mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id"
        where_ug = "mm.Fk_SessionID = :session_id AND mm.Fk_DegreeID = :degree_id"
        
        if college_id and college_id != '0':
            where_pg += " AND mt.Fk_CollegeID = :college_id"
            where_ug += " AND mt.AllottedCollegeID = :college_id"
            params['college_id'] = college_id
            
        if cutoff and cutoff != '0':
            where_pg += " AND mm.CutOff = :cutoff"
            where_ug += " AND mm.CutOff = :cutoff"
            params['cutoff'] = cutoff
            
        query = f"""
            SELECT 
                s.description as Session,
                d.description as Degree,
                pc.CollegeName as College,
                mm.CutOff as Cutoff,
                m.regno as RegistrationNo,
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as Name,
                m.f_name as FatherName,
                CAST(mt.ObtainMarks AS DECIMAL(10,2)) as ETMarks,
                CAST(mt.LastQualifyingPer AS DECIMAL(10,2)) as Lastqualifiedmarks,
                '' as OldAllotment,
                sc.collegename + ' (' + ISNULL(mt.AllottedSpecialisation, '') + ')' as NewAllotement,
                'New Entry' as Status,
                ISNULL(mt.AllottedSpecialisation, '') as Specialization
            FROM PA_Merit_Trn mt
            JOIN PA_Registration_Mst m ON mt.fk_regid = m.pk_regid
            JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
            LEFT JOIN LUP_AcademicSession_Mst s ON mm.Fk_SessionID = s.pk_sessionid
            LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
            LEFT JOIN PA_College_Mst pc ON mt.Fk_CollegeID = pc.Pk_CollegeID
            LEFT JOIN SMS_College_Mst sc ON mt.fk_allotedcollegeid = sc.pk_collegeid
            WHERE {where_pg}
            
            UNION ALL
            
            SELECT 
                s.description as Session,
                d.description as Degree,
                pc.CollegeName as College,
                mm.CutOff as Cutoff,
                m.regno as RegistrationNo,
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as Name,
                m.f_name as FatherName,
                CAST(mt.ObtainMarks AS DECIMAL(10,2)) as ETMarks,
                CAST(mt.LastQualifyingPerCalculated AS DECIMAL(10,2)) as Lastqualifiedmarks,
                '' as OldAllotment,
                pc.CollegeName + ' (' + ISNULL(mt.SubjectName, '') + ')' as NewAllotement,
                'New Entry' as Status,
                ISNULL(mt.SubjectName, '') as Specialization
            FROM PA_Merit_Bsc_Trn mt
            JOIN PA_Registration_Mst m ON mt.fk_regid = m.pk_regid
            JOIN PA_Merit_Mst mm ON mt.Fk_MeritID = mm.Pk_MeritID
            LEFT JOIN LUP_AcademicSession_Mst s ON mm.Fk_SessionID = s.pk_sessionid
            LEFT JOIN ACD_Degree_Mst d ON mm.Fk_DegreeID = d.pk_degreeid
            LEFT JOIN PA_College_Mst pc ON mt.AllottedCollegeID = pc.Pk_CollegeID
            WHERE {where_ug}
            
            ORDER BY Specialization, Name
        """
        
        try:
            records = db.session.execute(text(query), params).mappings().all()
            
            # Formulate Degree/College names for file name
            degree_name = "Degree"
            college_name = "College"
            if records and len(records) > 0:
                degree_name = str(records[0]["Degree"]).replace(" ", "_").replace("/", "_")
                college_name = str(records[0]["College"]).replace(" ", "_").replace("/", "_")
            
            file_base_name = f"CollegeWise_DepartmentWise_{degree_name}_{college_name}_{cutoff if cutoff != '0' else 'All'}"
            
            if report_type == '1': # Excel
                html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
    .table-grid-view td, .table-grid-view th {{ border: 1px solid #B0B0B0; padding: 5px; font-family: Arial, sans-serif; font-size: 11pt; }}
    .header-style th {{ background-color: #5D7B9D; color: white; font-weight: bold; }}
</style>
</head>
<body>
<div id="Anthem_ctl00_ContentPlaceHolder1_dgExport__">
<table class="table-grid-view" cellspacing="1" cellpadding="1" rules="all" border="1" id="ctl00_ContentPlaceHolder1_dgExport" style="border:1px solid #B0B0B0;border-collapse:collapse; margin:15px 0;">
    <tr class="header-style">
        <th>SNo</th><th>Session</th><th>Degree</th><th>College</th><th>Cutoff</th><th>RegistrationNo</th><th>Name</th><th>FatherName</th><th>ETMarks</th><th>Lastqualifiedmarks</th><th>OldAllotment</th><th>NewAllotement</th><th>Status</th>
    </tr>"""
                
                for index, row in enumerate(records):
                    bg_color = "White" if index % 2 == 0 else "#F8F8F8"
                    html += f'<tr class="dgitem-style" style="background-color:{bg_color};">'
                    html += f'<td>{index + 1}</td>'
                    html += f'<td>{row["Session"] or ""}</td>'
                    html += f'<td>{row["Degree"] or ""}</td>'
                    html += f'<td>{row["College"] or ""}</td>'
                    html += f'<td>{row["Cutoff"] or ""}</td>'
                    html += f'<td>{row["RegistrationNo"]}</td>'
                    html += f'<td>{row["Name"]}</td>'
                    html += f'<td>{row["FatherName"] or ""}</td>'
                    html += f'<td>{row["ETMarks"] or ""}</td>'
                    html += f'<td>{row["Lastqualifiedmarks"] or ""}</td>'
                    html += f'<td>{row["OldAllotment"] or "&nbsp;"}</td>'
                    html += f'<td>{row["NewAllotement"] or ""}</td>'
                    html += f'<td>{row["Status"] or ""}</td>'
                    html += '</tr>'
                    
                html += "</table></div></body></html>"
                
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = f'attachment; filename={file_base_name}.xls'
                return response
                
            elif report_type == '2': # PDF
                from app.pdf_collegewise_generator import generate_collegewise_pdf
                pdf_bytes = generate_collegewise_pdf(records)
                if pdf_bytes:
                    response = make_response(pdf_bytes)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename={file_base_name}.pdf'
                    return response
                else:
                    flash("Error generating PDF document.", "error")
            
        except Exception as e:
            flash(f"Error generating report: {str(e)}", "error")
        
    return render_template('merit_reports/collegewise_departmentwise.html', sessions=sessions, degrees=degrees, colleges=colleges, form_data=form_data)
