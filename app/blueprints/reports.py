from flask import Blueprint, render_template, request, flash, make_response, jsonify
from app import db
from sqlalchemy import text
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

def safe_all(func, default_val=None):
    try:
        return func()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return default_val if default_val is not None else []

def get_report_masters():
    sessions = safe_all(lambda: db.session.execute(text("SELECT pk_sessionid as id, description as name FROM LUP_AcademicSession_Mst ORDER BY pk_sessionid DESC")).mappings().all(), [])
    degrees = safe_all(lambda: db.session.execute(text("SELECT pk_degreeid as id, description as name FROM ACD_Degree_Mst WHERE active=1 ORDER BY description")).mappings().all(), [])
    colleges = safe_all(lambda: db.session.execute(text("SELECT Pk_CollegeID as id, CollegeName as name FROM PA_College_Mst ORDER BY CollegeName")).mappings().all(), [])
    specializations = safe_all(lambda: db.session.execute(text("SELECT Pk_SID as id, Specialization as name FROM PA_Specialization_mst ORDER BY Specialization")).mappings().all(), [])
    categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StuCatId as id, Description as name FROM PA_StudentCategory_Mst ORDER BY Description")).mappings().all(), [])
    religions = safe_all(lambda: db.session.execute(text("SELECT pk_religionid as id, description as name FROM Religion_Mst ORDER BY description")).mappings().all(), [])
    return sessions, degrees, colleges, specializations, categories, religions


@reports_bp.before_request
def check_admin_auth():
    from flask import session, redirect, url_for, flash, request
    if not session.get('user_id'):
        if request.endpoint and 'login' not in request.endpoint:
            flash('Please login to access this section.', 'error')
            return redirect(url_for('main.login'))

# ─── Candidate Export ─────────────────────────────────────────────────────────
@reports_bp.route('/candidate-export', methods=['GET', 'POST'])
def candidate_export():
    sessions, degrees, colleges, specializations, categories, religions = get_report_masters()

    form_data = {
        'session_id': '71', 'degree_type_id': '', 'college_id': '', 'specialization_id': '',
        'category_id': '', 'religion_id': '', 'from_date': '', 'to_date': '',
        'reg_no': '', 'name': '', 'status': '0', 'service': '0',
        'from_sno': '', 'to_sno': '', 'report_type': '0'
    }

    records = []
    action = 'view'

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'view')

    where_clauses = ["1=1"]
    params = {}

    if form_data['session_id'] and form_data['session_id'] != '0':
        where_clauses.append("m.fk_sessionid = :session_id")
        params['session_id'] = form_data['session_id']
    else:
        where_clauses.append("1=0")

    if request.method != 'POST':
        where_clauses.append("1=0")

    if form_data['degree_type_id'] and form_data['degree_type_id'] != '0':
        where_clauses.append("m.fk_dtypeid = :degree_id")
        params['degree_id'] = form_data['degree_type_id']

    if form_data['college_id'] and form_data['college_id'] != '0':
        where_clauses.append("mt.Fk_CollegeID = :college_id")
        params['college_id'] = form_data['college_id']

    if form_data['specialization_id'] and form_data['specialization_id'] != '0':
        where_clauses.append("mt.AllottedSpec = :spec_id")
        params['spec_id'] = form_data['specialization_id']

    if form_data['category_id'] and form_data['category_id'] != '0':
        where_clauses.append("m.fk_stucatid_cast = :cat_id")
        params['cat_id'] = form_data['category_id']

    if form_data['religion_id'] and form_data['religion_id'] != '0':
        where_clauses.append("m.fk_religionid = :rel_id")
        params['rel_id'] = form_data['religion_id']

    if form_data['from_date']:
        try:
            dt = datetime.strptime(form_data['from_date'], "%d/%m/%Y")
            where_clauses.append("CAST(m.dated AS DATE) >= :from_date")
            params['from_date'] = dt.strftime("%Y-%m-%d")
        except: pass

    if form_data['to_date']:
        try:
            dt = datetime.strptime(form_data['to_date'], "%d/%m/%Y")
            where_clauses.append("CAST(m.dated AS DATE) <= :to_date")
            params['to_date'] = dt.strftime("%Y-%m-%d")
        except: pass

    if form_data['reg_no']:
        where_clauses.append("m.regno = :reg_no")
        params['reg_no'] = form_data['reg_no']

    if form_data['name']:
        where_clauses.append("(ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) LIKE :name")
        params['name'] = f"%{form_data['name']}%"

    if form_data['status'] == '2':
        where_clauses.append("m.IsPaymentSuccess = 1")
    elif form_data['status'] == '3':
        where_clauses.append("m.rollno IS NOT NULL")

    if form_data['service'] == '1':
        where_clauses.append("mt.AllottedCategory = 'In_Service'")
    elif form_data['service'] == '2':
        where_clauses.append("ISNULL(mt.AllottedCategory, '') != 'In_Service'")

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT
            m.pk_regid,
            m.regno,
            (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as CandidateName,
            m.f_name as FatherName,
            pc.CollegeName as College,
            mt.AllottedSpecialisation as Specialization,
            CONVERT(varchar, m.dob, 106) as DOB,
            CONVERT(varchar, m.dated, 106) as Dated,
            m.mobileno as MobileNo,
            m.email as Email,
            d.description as Degree,
            CASE WHEN m.IsPaymentSuccess = 1 THEN 'Success Payment' ELSE 'Registered' END as Status
        FROM PA_Registration_Mst m
        LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
        LEFT JOIN PA_College_Mst pc ON mt.Fk_CollegeID = pc.Pk_CollegeID
        LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
        WHERE {where_str}
        ORDER BY m.dated DESC
    """

    try:
        records = db.session.execute(text(query), params).mappings().all()

        from_sno = int(form_data['from_sno']) if str(form_data.get('from_sno','')).isdigit() else 1
        to_sno = int(form_data['to_sno']) if str(form_data.get('to_sno','')).isdigit() else len(records)
        if from_sno > 0 and to_sno >= from_sno:
            records = records[from_sno-1:to_sno]

        if action == 'export':
            if form_data['report_type'] == '0':
                html = """<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>.table-grid-view td,.table-grid-view th{border:1px solid #B0B0B0;padding:5px;font-family:Arial,sans-serif;font-size:11pt}.header-style th{background-color:#5D7B9D;color:white;font-weight:bold}</style></head><body>
<table class="table-grid-view" cellspacing="1" cellpadding="1" rules="all" border="1" style="border:1px solid #B0B0B0;border-collapse:collapse">
<tr class="header-style"><th>S.No.</th><th>Registration No.</th><th>Candidate Name</th><th>Father Name</th><th>College</th><th>Specialization</th><th>DOB</th><th>Dated</th><th>Mobile No.</th><th>Email</th><th>Degree</th><th>Status</th></tr>"""
                for i, row in enumerate(records, 1):
                    bg = "White" if i % 2 == 1 else "#F8F8F8"
                    html += f'<tr style="background-color:{bg}"><td>{i}</td><td>{row["regno"] or ""}</td><td>{row["CandidateName"] or ""}</td><td>{row["FatherName"] or ""}</td><td>{row["College"] or ""}</td><td>{row["Specialization"] or ""}</td><td>{row["DOB"] or ""}</td><td>{row["Dated"] or ""}</td><td>{row["MobileNo"] or ""}</td><td>{row["Email"] or ""}</td><td>{row["Degree"] or ""}</td><td>{row["Status"] or ""}</td></tr>'
                html += "</table></body></html>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=CandidateExport.xls'
                return response
    except Exception as e:
        flash(f"Error fetching data: {str(e)}", "error")

    return render_template('reports/candidate_export.html',
                           sessions=sessions, degrees=degrees, colleges=colleges,
                           specializations=specializations, categories=categories,
                           religions=religions, form_data=form_data, records=records)

@reports_bp.route('/print-reporting-letter/<int:reg_id>', methods=['GET'])
def print_reporting_letter(reg_id):
    from app.pdf_reporting_letter_generator import generate_reporting_letter_pdf
    pdf_bytes = generate_reporting_letter_pdf(reg_id)
    if pdf_bytes:
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=reporting_letter_{reg_id}.pdf'
        return response
    else:
        return "Could not generate Reporting Letter PDF", 500

# ─── Candidate Dashboard ──────────────────────────────────────────────────────
@reports_bp.route('/candidate-dashboard', methods=['GET', 'POST'])
def candidate_dashboard():
    sessions, degrees, colleges, specializations, categories, religions = get_report_masters()

    form_data = {
        'session_id': '71', 'degree_type_id': '0', 'college_id': '0',
        'status_type': '0', 'payment_for': '1'
    }
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'view')

        where_clauses = ["1=1"]
        params = {}

        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_type_id'] and form_data['degree_type_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :dtype_id")
            params['dtype_id'] = form_data['degree_type_id']
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("mt.Fk_CollegeID = :college_id")
            params['college_id'] = form_data['college_id']
        if form_data['status_type'] == '2':
            where_clauses.append("m.IsPaymentSuccess = 1")

        where_str = " AND ".join(where_clauses)

        query = f'''
            SELECT
                d.description as Degree,
                c.CollegeName as College,
                s.Specialization as Specialization,
                COUNT(m.pk_regid) as Registered,
                SUM(CASE WHEN m.IsPaymentSuccess = 1 THEN 1 ELSE 0 END) as PaymentSuccess,
                SUM(CASE WHEN m.IsPaymentSuccessCouns = 1 THEN 1 ELSE 0 END) as CounsellingSuccess
            FROM PA_Registration_Mst m
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
            LEFT JOIN PA_College_Mst c ON mt.Fk_CollegeID = c.Pk_CollegeID
            LEFT JOIN PA_Specialization_mst s ON mt.AllottedSpec = s.Pk_SID
            WHERE {where_str}
            GROUP BY d.description, c.CollegeName, s.Specialization
            ORDER BY c.CollegeName, s.Specialization
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            if action == 'export':
                html = "<table border='1'><tr><th>Degree</th><th>College</th><th>Specialization</th><th>Registered</th><th>Payment Success</th><th>Counselling Success</th></tr>"
                for r in records:
                    html += f"<tr><td>{r.Degree or ''}</td><td>{r.College or ''}</td><td>{r.Specialization or ''}</td><td>{r.Registered}</td><td>{r.PaymentSuccess}</td><td>{r.CounsellingSuccess}</td></tr>"
                html += "</table>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=DashboardReport.xls'
                return response
        except Exception as e:
            flash(f"Error executing query: {str(e)}", "error")

    return render_template('reports/candidate_dashboard.html',
                           sessions=sessions, colleges=colleges,
                           degrees=degrees, form_data=form_data, records=records)

# ─── Room Availability ────────────────────────────────────────────────────────
@reports_bp.route('/room-availability', methods=['GET', 'POST'])
def room_availability():
    sessions, degrees, colleges, specializations, categories, religions = get_report_masters()
    exam_centers = safe_all(lambda: db.session.execute(text("SELECT pk_examCenterId as id, Name as name, fk_SessionId as session_id, fk_ETID as et_id FROM PA_Exam_Center_Mst ORDER BY Name")).mappings().all(), [])

    form_data = {'session_id': '71', 'degree_id': '', 'exam_center_id': '0'}
    records = []
    grand_total = 0
    max_rooms = 0

    if request.method == 'POST':
        form_data.update(request.form)
        where_clauses = ["1=1"]
        params = {}

        if form_data['session_id']:
            where_clauses.append("c.fk_SessionId = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id']:
            where_clauses.append("c.fk_ETID IN (SELECT Fk_ETID FROM PAD_AdmitCard_Config WHERE Fk_DegreeId = :degree_id)")
            params['degree_id'] = form_data['degree_id']
        if form_data['exam_center_id'] and form_data['exam_center_id'] != '0':
            where_clauses.append("c.pk_examCenterId = :center_id")
            params['center_id'] = form_data['exam_center_id']

        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT c.pk_examCenterId as CenterID, c.Name as CenterName,
                   t.RoomNo, t.RoomCapacity
            FROM PA_Exam_Center_Trn t
            INNER JOIN PA_Exam_Center_Mst c ON t.fk_examCenterId = c.pk_examCenterId
            WHERE {where_str}
            ORDER BY c.Name, t.RoomNo
        '''
        try:
            raw_records = db.session.execute(text(query), params).mappings().all()
            grouped_records = {}
            for r in raw_records:
                cid = r['CenterID']
                if cid not in grouped_records:
                    grouped_records[cid] = {'CenterName': r['CenterName'], 'Rooms': [], 'CenterTotal': 0}
                grouped_records[cid]['Rooms'].append({'RoomNo': r['RoomNo'], 'Capacity': r['RoomCapacity']})
                grouped_records[cid]['CenterTotal'] += r['RoomCapacity']
                grand_total += r['RoomCapacity']
            records = list(grouped_records.values())
            max_rooms = max([len(r['Rooms']) for r in records]) if records else 0
        except Exception as e:
            flash(f"Error executing query: {str(e)}", "error")

    return render_template('reports/room_availability.html',
                           sessions=sessions, degrees=degrees, exam_centers=exam_centers,
                           form_data=form_data, records=records,
                           max_rooms=max_rooms, grand_total=grand_total)

# ─── Candidate Dashboard (Counselling) ───────────────────────────────────────
@reports_bp.route('/candidate-dashboard-counselling', methods=['GET', 'POST'])
def candidate_dashboard_counselling():
    sessions, degrees, _, _, _, _ = get_report_masters()
    form_data = {'session_id': '71', 'degree_id': '0'}
    records = []
    total_qualified = 0
    total_payments = 0
    total_revenue = 0.0

    if request.method == 'POST':
        form_data.update(request.form)
        where_clauses = ["1=1"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                d.description as Degree,
                ISNULL(cat.Description, 'GENERAL') as Category,
                COUNT(m.pk_regid) as TotalQualified,
                SUM(CASE WHEN m.IsPaymentSuccessCouns = 1 THEN 1 ELSE 0 END) as TotalPayments,
                ISNULL(SUM(CASE WHEN m.IsPaymentSuccessCouns = 1 THEN p.Amount ELSE 0 END), 0) as TotalRevenue
            FROM PA_Registration_Mst m
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
            LEFT JOIN (
                SELECT Fk_regId, SUM(Amount) as Amount
                FROM PA_OnlinePayment_Detail
                WHERE isCounsellingFee = 1 AND PaymentStatus = 'Success'
                GROUP BY Fk_regId
            ) p ON m.pk_regid = p.Fk_regId
            WHERE {where_str}
            GROUP BY d.description, cat.Description
            ORDER BY d.description, cat.Description
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            total_qualified = sum(r['TotalQualified'] for r in records)
            total_payments = sum(r['TotalPayments'] for r in records)
            total_revenue = sum(float(r['TotalRevenue'] or 0) for r in records)
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/candidate_dashboard_counselling.html',
                           sessions=sessions, degrees=degrees, form_data=form_data,
                           records=records, total_qualified=total_qualified,
                           total_payments=total_payments, total_revenue=total_revenue)

# ─── Candidate Payment Reports ────────────────────────────────────────────────
@reports_bp.route('/get-payment-dates', methods=['POST'])
def get_payment_dates():
    data = request.get_json()
    session_id = data.get('session_id')
    degree_id = data.get('degree_id')
    if session_id and degree_id:
        query = '''
            SELECT t.Login_PaymentStartDate, t.Login_PaymentEndDate
            FROM PA_AdmissionOpen_Trn t
            INNER JOIN PA_AdmissionOpen_Mst m ON t.Fk_AdmOpenId = m.Pk_AdmOpenId
            WHERE m.Fk_SessionId = :session_id AND t.Fk_DegreeId = :degree_id
        '''
        try:
            res = db.session.execute(text(query), {'session_id': session_id, 'degree_id': degree_id}).mappings().first()
            if res:
                from_date = res['Login_PaymentStartDate'].strftime('%d/%m/%Y') if res['Login_PaymentStartDate'] else ''
                to_date = res['Login_PaymentEndDate'].strftime('%d/%m/%Y') if res['Login_PaymentEndDate'] else ''
                return jsonify({'success': True, 'from_date': from_date, 'to_date': to_date})
        except Exception as e:
            print("Error fetching dates:", e)
    return jsonify({'success': False})

@reports_bp.route('/candidate-payment-reports', methods=['GET', 'POST'])
def candidate_payment_reports():
    sessions, degrees, colleges, specializations, categories, religions = get_report_masters()
    form_data = {
        'session_id': '71', 'degree_id': '0', 'college_id': '0', 'category_id': '0',
        'specialization_id': '0', 'unique_id': '', 'religion_id': '0',
        'from_date': '', 'to_date': '', 'name': '', 'report_type': '0',
        'reg_no': '', 'status': '0'
    }
    candidates = []
    transactions = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'search')

        where_clauses = ["1=1"]
        params = {}

        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        if form_data['category_id'] and form_data['category_id'] != '0':
            where_clauses.append("m.fk_stucatid_cast = :category_id")
            params['category_id'] = form_data['category_id']
        if form_data['religion_id'] and form_data['religion_id'] != '0':
            where_clauses.append("m.fk_religionid = :religion_id")
            params['religion_id'] = form_data['religion_id']
        if form_data['unique_id']:
            where_clauses.append("m.AdharNo = :unique_id")
            params['unique_id'] = form_data['unique_id']
        if form_data['name']:
            where_clauses.append("(ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) LIKE :name")
            params['name'] = f"%{form_data['name']}%"
        if form_data['reg_no']:
            where_clauses.append("m.regno = :reg_no")
            params['reg_no'] = form_data['reg_no']
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("c.Pk_CollegeID = :college_id")
            params['college_id'] = form_data['college_id']
        if form_data['specialization_id'] and form_data['specialization_id'] != '0':
            where_clauses.append("s.Pk_SID = :spec_id")
            params['spec_id'] = form_data['specialization_id']
        if form_data['status'] == '1':
            where_clauses.append("p.PaymentStatus = 'Success'")
        elif form_data['status'] == '2':
            where_clauses.append("(p.PaymentStatus != 'Success' OR p.PaymentStatus IS NULL)")
        if form_data['from_date']:
            try:
                dt = datetime.strptime(form_data['from_date'], "%d/%m/%Y")
                where_clauses.append(f"CAST(p.InitiateTime AS DATE) >= '{dt.strftime('%Y-%m-%d')}'")
            except: pass
        if form_data['to_date']:
            try:
                dt = datetime.strptime(form_data['to_date'], "%d/%m/%Y")
                where_clauses.append(f"CAST(p.InitiateTime AS DATE) <= '{dt.strftime('%Y-%m-%d')}'")
            except: pass

        where_str = " AND ".join(where_clauses)

        cand_query = f'''
            SELECT DISTINCT
                m.regno,
                (ISNULL(m.s_name, '') + ' ' + ISNULL(m.s_surname, '')) as CandidateName,
                ISNULL(m.f_name, '') as FatherName,
                ISNULL(s.Specialization, '') as Specialization,
                ISNULL(cat.Description, 'GENERAL') as Category,
                ISNULL(m.mobileno, '') as Mobile,
                ISNULL(m.rollno, '') as RollNo,
                CASE WHEN m.IsWard = 1 THEN 'Yes' ELSE 'No' END as InService,
                ISNULL(CAST(p.Amount AS DECIMAL(10,2)), 0) as Amount
            FROM PA_Registration_Mst m
            INNER JOIN (
                SELECT Fk_regId, Amount, PaymentStatus, InitiateTime FROM PA_OnlinePayment_Detail
                UNION ALL
                SELECT Fk_regId, Amount, PaymentStatus, InitiateTime FROM PA_StudentGrievancesPayment_Detail
            ) p ON m.pk_regid = p.Fk_regId
            LEFT JOIN PA_College_Mst c ON m.fk_CollegID = c.Pk_CollegeID
            LEFT JOIN PA_Specialization_mst s ON m.fk_SId = s.Pk_SID
            LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
            WHERE {where_str}
            ORDER BY CandidateName ASC
        '''

        tran_query = f'''
            SELECT
                ISNULL(m.AdharNo, '') as UniqueId,
                ISNULL(p.TransactionId, '') as TransactionId,
                ISNULL(p.PaymentId, '') as PaymentId,
                m.regno as RegistrationNo,
                ISNULL(p.ResponseMessage, '') as ResponseMessage,
                CAST(p.Amount AS DECIMAL(10,2)) as PaidAmount,
                CONVERT(varchar, p.InitiateTime, 106) as Dated,
                ISNULL(m.mobileno, '') as MobileNo,
                ISNULL(p.PaymentStatus, 'Failed') as Status
            FROM PA_Registration_Mst m
            INNER JOIN (
                SELECT Fk_regId, TransactionId, PaymentId, Amount, PaymentStatus, ResponseMessage, InitiateTime FROM PA_OnlinePayment_Detail
                UNION ALL
                SELECT Fk_regId, TransactionId, PaymentId, Amount, PaymentStatus, ResponseMessage, InitiateTime FROM PA_StudentGrievancesPayment_Detail
            ) p ON m.pk_regid = p.Fk_regId
            LEFT JOIN PA_College_Mst c ON m.fk_CollegID = c.Pk_CollegeID
            LEFT JOIN PA_Specialization_mst s ON m.fk_SId = s.Pk_SID
            WHERE {where_str}
            ORDER BY m.regno ASC
        '''

        try:
            candidates = db.session.execute(text(cand_query), params).mappings().all()
            transactions = db.session.execute(text(tran_query), params).mappings().all()

            if action == 'export' and (candidates or transactions):
                if form_data['report_type'] == '0':
                    html = "<table border='1'><tr><th>UniqueId</th><th>TransactionId</th><th>Payment Id</th><th>Registration No.</th><th>Response Message</th><th>Paid Amount</th><th>Dated</th><th>Mobile No.</th></tr>"
                    for r in transactions:
                        html += f"<tr><td>{r.UniqueId or ''}</td><td>{r.TransactionId or ''}</td><td>{r.PaymentId or ''}</td><td>{r.RegistrationNo or ''}</td><td>{r.ResponseMessage or ''}</td><td>{r.PaidAmount or ''}</td><td>{r.Dated or ''}</td><td>{r.MobileNo or ''}</td></tr>"
                    html += "</table>"
                    response = make_response(html)
                    response.headers['Content-Type'] = 'application/vnd.ms-excel'
                    response.headers['Content-Disposition'] = 'attachment; filename=CandidateTransactions.xls'
                    return response
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template('reports/candidate_payment_reports.html',
                           sessions=sessions, degrees=degrees, colleges=colleges,
                           specializations=specializations, categories=categories,
                           religions=religions, form_data=form_data,
                           candidates=candidates, transactions=transactions)

# ─── Candidate Payment Reports (Counselling) ─────────────────────────────────
@reports_bp.route('/candidate-payment-reports-counselling', methods=['GET', 'POST'])
def candidate_payment_reports_counselling():
    sessions, degrees, colleges, specializations, categories, religions = get_report_masters()
    form_data = {
        'session_id': '71', 'degree_id': '0', 'college_id': '0', 'category_id': '0',
        'specialization_id': '0', 'unique_id': '', 'religion_id': '0',
        'from_date': '', 'to_date': '', 'name': '', 'report_type': '0', 'reg_no': ''
    }
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'search')

        where_clauses = ["m.IsPaymentSuccessCouns = 1"]
        params = {}

        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        if form_data['category_id'] and form_data['category_id'] != '0':
            where_clauses.append("m.fk_stucatid_cast = :category_id")
            params['category_id'] = form_data['category_id']
        if form_data['religion_id'] and form_data['religion_id'] != '0':
            where_clauses.append("m.fk_religionid = :religion_id")
            params['religion_id'] = form_data['religion_id']
        if form_data['unique_id']:
            where_clauses.append("m.AdharNo = :unique_id")
            params['unique_id'] = form_data['unique_id']
        if form_data['name']:
            where_clauses.append("(ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) LIKE :name")
            params['name'] = f"%{form_data['name']}%"
        if form_data['reg_no']:
            where_clauses.append("m.regno = :reg_no")
            params['reg_no'] = form_data['reg_no']
        if form_data['specialization_id'] and form_data['specialization_id'] != '0':
            where_clauses.append("m.fk_SId = :spec_id")
            params['spec_id'] = form_data['specialization_id']
        if form_data['from_date']:
            try:
                dt = datetime.strptime(form_data['from_date'], "%d/%m/%Y")
                where_clauses.append("CAST(m.PaymentSuccessTimeCouns AS DATE) >= :from_date")
                params['from_date'] = dt.strftime("%Y-%m-%d")
            except: pass
        if form_data['to_date']:
            try:
                dt = datetime.strptime(form_data['to_date'], "%d/%m/%Y")
                where_clauses.append("CAST(m.PaymentSuccessTimeCouns AS DATE) <= :to_date")
                params['to_date'] = dt.strftime("%Y-%m-%d")
            except: pass

        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                m.regno,
                (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                ISNULL(m.f_name,'') as FatherName,
                ISNULL(s.Specialization,'') as Specialization,
                ISNULL(cat.Description,'GENERAL') as Category,
                ISNULL(m.mobileno,'') as Mobile,
                ISNULL(m.rollno,'') as RollNo,
                CASE WHEN m.IsWard=1 THEN 'Yes' ELSE 'No' END as InService,
                ISNULL(CAST(p.Amount AS DECIMAL(10,2)), 0) as Amount
            FROM PA_Registration_Mst m
            LEFT JOIN (
                SELECT Fk_regId, SUM(Amount) as Amount
                FROM PA_OnlinePayment_Detail WHERE isCounsellingFee=1 GROUP BY Fk_regId
            ) p ON m.pk_regid = p.Fk_regId
            LEFT JOIN PA_Specialization_mst s ON m.fk_SId = s.Pk_SID
            LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
            LEFT JOIN PA_College_Mst c ON m.fk_CollegID = c.Pk_CollegeID
            WHERE {where_str}
            ORDER BY CandidateName ASC
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            if action == 'export' and records:
                html = "<table border='1'><tr><th>S.No.</th><th>Reg No.</th><th>Candidate Name</th><th>Father Name</th><th>Specialization</th><th>Category</th><th>Mobile</th><th>Roll No.</th><th>In Service</th><th>Amount</th></tr>"
                for i, r in enumerate(records, 1):
                    html += f"<tr><td>{i}</td><td>{r.regno or ''}</td><td>{r.CandidateName or ''}</td><td>{r.FatherName or ''}</td><td>{r.Specialization or ''}</td><td>{r.Category or ''}</td><td>{r.Mobile or ''}</td><td>{r.RollNo or ''}</td><td>{r.InService or ''}</td><td>{r.Amount or ''}</td></tr>"
                html += "</table>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=CounsellingPayments.xls'
                return response
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/candidate_payment_reports_counselling.html',
                           sessions=sessions, degrees=degrees, colleges=colleges,
                           specializations=specializations, categories=categories,
                           religions=religions, form_data=form_data, records=records)

# ─── Candidates List (Counselling) ────────────────────────────────────────────
@reports_bp.route('/candidate-list-counselling', methods=['GET', 'POST'])
def candidate_list_counselling():
    sessions, degrees, _, _, _, _ = get_report_masters()
    form_data = {'session_id': '71', 'degree_id': '0'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'search')

        where_clauses = ["m.IsPaymentSuccessCouns = 1"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        where_str = " AND ".join(where_clauses)

        query = f'''
            SELECT
                m.regno, ISNULL(m.rollno,'') as rollno,
                (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                ISNULL(m.f_name,'') as FatherName,
                ISNULL(cat.Description,'GENERAL') as Category,
                ISNULL(mt.ObtainMarks, 0) as ObtainMarks,
                ISNULL(mt.OverAllRank, 0) as overallR,
                ISNULL(mt.AllottedCategory,'') as AllottedCategory,
                c.CollegeName as AllottedCollegeName,
                mt.AllottedSpecialisation
            FROM PA_Registration_Mst m
            LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
            LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
            LEFT JOIN PA_College_Mst c ON mt.fk_allotedcollegeid = c.Pk_CollegeID
            WHERE {where_str}
            ORDER BY CandidateName ASC
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            if action == 'export' and records:
                html = "<table border='1'><tr><th>regno</th><th>rollno</th><th>Name</th><th>Father Name</th><th>Category</th><th>Marks</th><th>Rank</th><th>Allotted College</th><th>Allotted Specialization</th></tr>"
                for r in records:
                    html += f"<tr><td>{r.regno or ''}</td><td>{r.rollno or ''}</td><td>{r.CandidateName or ''}</td><td>{r.FatherName or ''}</td><td>{r.Category or ''}</td><td>{r.ObtainMarks or ''}</td><td>{r.overallR or ''}</td><td>{r.AllottedCollegeName or ''}</td><td>{r.AllottedSpecialisation or ''}</td></tr>"
                html += "</table>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=CandidateList.xls'
                return response
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template('reports/candidate_list_counselling.html',
                           sessions=sessions, degrees=degrees,
                           form_data=form_data, records=records)

# ─── Check Payment Status ─────────────────────────────────────────────────────
@reports_bp.route('/check-payment-status', methods=['GET', 'POST'])
def check_payment_status():
    form_data = {'search_type': '1', 'search_value': ''}
    pay_records = []
    grievance_records = []

    if request.method == 'POST':
        form_data.update(request.form)
        val = form_data['search_value'].strip()
        search_type = form_data['search_type']

        if val:
            try:
                if search_type == '1':  # By Registration No
                    reg_query = '''
                        SELECT m.pk_regid, m.regno,
                               (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName
                        FROM PA_Registration_Mst m WHERE m.regno = :val
                    '''
                    reg = db.session.execute(text(reg_query), {'val': val}).mappings().first()
                    if reg:
                        reg_id = reg['pk_regid']
                        pay_records = db.session.execute(text('''
                            SELECT m.regno as RegistrationNo,
                                   (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                                   ISNULL(p.TransactionId,'') as TransactionId,
                                   ISNULL(p.PaymentId,'') as PaymentId,
                                   ISNULL(CAST(p.Amount AS DECIMAL(10,2)),0) as Amount,
                                   ISNULL(p.PaymentStatus,'') as PaymentStatus,
                                   ISNULL(p.ResponseMessage,'') as ResponseMessage,
                                   CONVERT(varchar, p.InitiateTime, 106) as PaymentDate,
                                   ISNULL(p.Mode,'') as Mode
                            FROM PA_OnlinePayment_Detail p
                            INNER JOIN PA_Registration_Mst m ON p.Fk_regId = m.pk_regid
                            WHERE p.Fk_regId = :reg_id
                            ORDER BY p.InitiateTime DESC
                        '''), {'reg_id': reg_id}).mappings().all()
                        grievance_records = db.session.execute(text('''
                            SELECT m.regno as RegistrationNo,
                                   (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                                   ISNULL(g.TransactionId,'') as TransactionId,
                                   ISNULL(g.PaymentId,'') as PaymentId,
                                   ISNULL(CAST(g.Amount AS DECIMAL(10,2)),0) as Amount,
                                   ISNULL(g.PaymentStatus,'') as PaymentStatus,
                                   ISNULL(g.ResponseMessage,'') as ResponseMessage,
                                   CONVERT(varchar, g.InitiateTime, 106) as PaymentDate,
                                   ISNULL(g.Mode,'') as Mode
                            FROM PA_StudentGrievancesPayment_Detail g
                            INNER JOIN PA_Registration_Mst m ON g.Fk_regId = m.pk_regid
                            WHERE g.Fk_regId = :reg_id
                            ORDER BY g.InitiateTime DESC
                        '''), {'reg_id': reg_id}).mappings().all()
                else:  # By Payment ID
                    pay_records = db.session.execute(text('''
                        SELECT m.regno as RegistrationNo,
                               (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                               ISNULL(p.TransactionId,'') as TransactionId,
                               ISNULL(p.PaymentId,'') as PaymentId,
                               ISNULL(CAST(p.Amount AS DECIMAL(10,2)),0) as Amount,
                               ISNULL(p.PaymentStatus,'') as PaymentStatus,
                               ISNULL(p.ResponseMessage,'') as ResponseMessage,
                               CONVERT(varchar, p.InitiateTime, 106) as PaymentDate,
                               ISNULL(p.Mode,'') as Mode
                        FROM PA_OnlinePayment_Detail p
                        INNER JOIN PA_Registration_Mst m ON p.Fk_regId = m.pk_regid
                        WHERE p.PaymentId = :val OR p.TransactionId = :val
                        ORDER BY p.InitiateTime DESC
                    '''), {'val': val}).mappings().all()
                    grievance_records = db.session.execute(text('''
                        SELECT m.regno as RegistrationNo,
                               (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                               ISNULL(g.TransactionId,'') as TransactionId,
                               ISNULL(g.PaymentId,'') as PaymentId,
                               ISNULL(CAST(g.Amount AS DECIMAL(10,2)),0) as Amount,
                               ISNULL(g.PaymentStatus,'') as PaymentStatus,
                               ISNULL(g.ResponseMessage,'') as ResponseMessage,
                               CONVERT(varchar, g.InitiateTime, 106) as PaymentDate,
                               ISNULL(g.Mode,'') as Mode
                        FROM PA_StudentGrievancesPayment_Detail g
                        INNER JOIN PA_Registration_Mst m ON g.Fk_regId = m.pk_regid
                        WHERE g.PaymentId = :val OR g.TransactionId = :val
                        ORDER BY g.InitiateTime DESC
                    '''), {'val': val}).mappings().all()
            except Exception as e:
                flash(f"Error: {e}", "error")

    return render_template('reports/check_payment_status.html',
                           form_data=form_data,
                           pay_records=pay_records,
                           grievance_records=grievance_records)

# ─── Candidate Eligible Specialization Report ─────────────────────────────────
@reports_bp.route('/candidate-eligible-specialization-report', methods=['GET', 'POST'])
def candidate_eligible_specialization_report():
    _, degrees, colleges, _, _, _ = get_report_masters()
    form_data = {'degree_id': '0', 'college_id': '0'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        where_clauses = ["1=1"]
        params = {}
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("dsm.fk_DegreeId = :degree_id")
            params['degree_id'] = form_data['degree_id']
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("dsm.fk_CollegeId = :college_id")
            params['college_id'] = form_data['college_id']
        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                d.description as Degree,
                c.CollegeName as College,
                s.Specialization as Specialization,
                ISNULL(cs.seat, 0) as TotalSeats,
                COUNT(m.pk_regid) as RegisteredCandidates,
                SUM(CASE WHEN m.IsPaymentSuccess=1 THEN 1 ELSE 0 END) as PaidCandidates
            FROM PA_Degree_SpecializationMapping_mst dsm
            INNER JOIN PA_Specialization_mst s ON dsm.fk_SID = s.Pk_SID
            INNER JOIN PA_College_Mst c ON dsm.fk_CollegeId = c.Pk_CollegeID
            INNER JOIN ACD_Degree_Mst d ON dsm.fk_DegreeId = d.pk_degreeid
            LEFT JOIN PA_College_Spec_Map cs ON cs.fk_sid = dsm.fk_SID AND cs.fk_collegeID = dsm.fk_CollegeId AND cs.fk_degreeid = dsm.fk_DegreeId
            LEFT JOIN PA_Registration_Mst m ON m.fk_SId = dsm.fk_SID AND m.fk_dtypeid = dsm.fk_DegreeId
            WHERE {where_str}
            GROUP BY d.description, c.CollegeName, s.Specialization, cs.seat
            ORDER BY c.CollegeName, s.Specialization
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/candidate_eligible_specialization.html',
                           degrees=degrees, colleges=colleges,
                           form_data=form_data, records=records)

# ─── Ex-Student Report ────────────────────────────────────────────────────────
@reports_bp.route('/ex-student-report', methods=['GET', 'POST'])
def ex_student_report():
    sessions, degrees, _, _, _, _ = get_report_masters()
    form_data = {'session_id': '71', 'degree_id': '0', 'report_type': '0'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'search')

        where_clauses = ["1=1"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        where_str = " AND ".join(where_clauses)

        query = f'''
            SELECT DISTINCT
                m.regno,
                (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                ISNULL(m.f_name,'') as FatherName,
                d.description as Degree,
                ISNULL(cat.Description,'GENERAL') as Category,
                ISNULL(m.mobileno,'') as Mobile,
                mt.AllottedSpecialisation as Specialization,
                c.CollegeName as College,
                'Admitted' as Status
            FROM PA_Admission_Trn t
            INNER JOIN PA_Registration_Mst m ON t.fk_regid = m.pk_regid
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            LEFT JOIN PA_StudentCategory_Mst cat ON m.fk_stucatid_cast = cat.Pk_StuCatId
            LEFT JOIN PA_Merit_Trn mt ON mt.fk_regid = m.pk_regid
            LEFT JOIN PA_College_Mst c ON mt.fk_allotedcollegeid = c.Pk_CollegeID
            WHERE {where_str}
            ORDER BY CandidateName ASC
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            if action == 'export' and records:
                html = "<table border='1'><tr><th>S.No.</th><th>Reg No.</th><th>Name</th><th>Father Name</th><th>Degree</th><th>Category</th><th>Specialization</th><th>College</th><th>Mobile</th><th>Status</th></tr>"
                for i, r in enumerate(records, 1):
                    html += f"<tr><td>{i}</td><td>{r.regno or ''}</td><td>{r.CandidateName or ''}</td><td>{r.FatherName or ''}</td><td>{r.Degree or ''}</td><td>{r.Category or ''}</td><td>{r.Specialization or ''}</td><td>{r.College or ''}</td><td>{r.Mobile or ''}</td><td>{r.Status or ''}</td></tr>"
                html += "</table>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=ExStudentReport.xls'
                return response
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/ex_student_report.html',
                           sessions=sessions, degrees=degrees,
                           form_data=form_data, records=records)

# ─── Last Cutoff Report ───────────────────────────────────────────────────────
@reports_bp.route('/last-cutoff-report', methods=['GET', 'POST'])
def last_cutoff_report():
    sessions, degrees, colleges, _, _, _ = get_report_masters()
    form_data = {'session_id': '71', 'degree_id': '0', 'college_id': '0', 'cutoff': '1'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        where_clauses = ["mt.AllottedCategory IS NOT NULL"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        if form_data['college_id'] and form_data['college_id'] != '0':
            where_clauses.append("mt.fk_allotedcollegeid = :college_id")
            params['college_id'] = form_data['college_id']
        # cutoff round filter: WithdrawalCutoff = 0 means active (not withdrawn), use it to filter
        # A cutoff value represents the merit list generation round
        try:
            cutoff_val = int(form_data.get('cutoff', 1))
            where_clauses.append("mt.WithdrawalCutoff <= :cutoff_val")
            params['cutoff_val'] = cutoff_val
        except: pass
        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                c.CollegeName,
                mt.AllottedSpecialisation as Specialization,
                mt.AllottedCategory as Category,
                MIN(mt.OverAllRank) as OpeningRank,
                MAX(mt.OverAllRank) as ClosingRank,
                COUNT(*) as TotalAllotted
            FROM PA_Merit_Trn mt
            INNER JOIN PA_Registration_Mst m ON mt.fk_regid = m.pk_regid
            LEFT JOIN PA_College_Mst c ON mt.fk_allotedcollegeid = c.Pk_CollegeID
            WHERE {where_str}
            GROUP BY c.CollegeName, mt.AllottedSpecialisation, mt.AllottedCategory
            ORDER BY c.CollegeName, mt.AllottedSpecialisation, mt.AllottedCategory
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/last_cutoff_report.html',
                           sessions=sessions, degrees=degrees, colleges=colleges,
                           form_data=form_data, records=records)

# ─── Additional Fee Details ───────────────────────────────────────────────────
@reports_bp.route('/additional-fee-details', methods=['GET', 'POST'])
def additional_fee_details():
    sessions, degrees, _, _, _, _ = get_report_masters()
    form_data = {'session_id': '71', 'degree_id': '0'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        action = request.form.get('action', 'search')
        where_clauses = ["1=1"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                m.regno,
                (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                d.description as Degree,
                ISNULL(CAST(f.Amount AS DECIMAL(10,2)), 0) as AdditionalFee,
                CONVERT(varchar, f.Fromdate, 106) as FromDate,
                CONVERT(varchar, f.Todate, 106) as ToDate
            FROM PA_Registration_Mst m
            INNER JOIN PA_StudentAcademic_Fee f ON m.regno = f.fk_regno
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            WHERE {where_str}
            ORDER BY CandidateName ASC
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
            if action == 'export' and records:
                html = "<table border='1'><tr><th>S.No.</th><th>Reg No.</th><th>Candidate Name</th><th>Degree</th><th>Additional Fee</th><th>From Date</th><th>To Date</th></tr>"
                for i, r in enumerate(records, 1):
                    html += f"<tr><td>{i}</td><td>{r.regno or ''}</td><td>{r.CandidateName or ''}</td><td>{r.Degree or ''}</td><td>{r.AdditionalFee or ''}</td><td>{r.FromDate or ''}</td><td>{r.ToDate or ''}</td></tr>"
                html += "</table>"
                response = make_response(html)
                response.headers['Content-Type'] = 'application/vnd.ms-excel'
                response.headers['Content-Disposition'] = 'attachment; filename=AdditionalFeeDetails.xls'
                return response
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/additional_fee_details.html',
                           sessions=sessions, degrees=degrees,
                           form_data=form_data, records=records)

# ─── Modify Personal Information Request ─────────────────────────────────────
@reports_bp.route('/modify-personal-information-request', methods=['GET', 'POST'])
def modify_personal_information_request():
    sessions, degrees, _, _, _, _ = get_report_masters()
    personal_info_types = safe_all(lambda: db.session.execute(
        text("SELECT pk_PID as id, Description as name FROM PA_PersonalInfo_Mst WHERE IsActive=1 ORDER BY pk_PID")
    ).mappings().all(), [])

    form_data = {'session_id': '71', 'degree_id': '0', 'personal_info': '0'}
    records = []

    if request.method == 'POST':
        form_data.update(request.form)
        where_clauses = ["1=1"]
        params = {}
        if form_data['session_id'] and form_data['session_id'] != '0':
            where_clauses.append("m.fk_sessionid = :session_id")
            params['session_id'] = form_data['session_id']
        if form_data['degree_id'] and form_data['degree_id'] != '0':
            where_clauses.append("m.fk_dtypeid = :degree_id")
            params['degree_id'] = form_data['degree_id']
        if form_data['personal_info'] and form_data['personal_info'] != '0':
            where_clauses.append("mod.FK_PInfoID = :pinfo_id")
            params['pinfo_id'] = form_data['personal_info']
        where_str = " AND ".join(where_clauses)
        query = f'''
            SELECT
                m.regno,
                (ISNULL(m.s_name,'') + ' ' + ISNULL(m.s_surname,'')) as CandidateName,
                d.description as Degree,
                pi.Description as InfoType,
                ISNULL(mod.Old_Value,'') as OldValue,
                ISNULL(mod.New_Value,'') as NewValue,
                CASE
                    WHEN mod.IsModify = 1 THEN 'Approved'
                    WHEN mod.Agree = 1 THEN 'Pending Approval'
                    ELSE 'Pending'
                END as Status,
                CONVERT(varchar, mod.CreatedDate, 106) as RequestDate
            FROM PA_ModifedPersonalInfo_mst mod
            INNER JOIN PA_Registration_Mst m ON mod.fk_RegID = m.pk_regid
            LEFT JOIN PA_PersonalInfo_Mst pi ON mod.FK_PInfoID = pi.pk_PID
            LEFT JOIN ACD_Degree_Mst d ON m.fk_dtypeid = d.pk_degreeid
            WHERE {where_str}
            ORDER BY mod.CreatedDate DESC
        '''
        try:
            records = db.session.execute(text(query), params).mappings().all()
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template('reports/modify_personal_information_request.html',
                           sessions=sessions, degrees=degrees,
                           personal_info_types=personal_info_types,
                           form_data=form_data, records=records)
