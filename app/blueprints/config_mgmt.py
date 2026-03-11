from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import (AcademicSession, College, Degree, StudentCategory, 
                        DegreeType, PreviousExam, PreviousExamStream, Attachment, 
                        UniversitySpecialization, CollegeSpecMap, CandidateQualification, 
                        CandidateSpecialization, CandidateQualSpecMap, UnivSpecEligibleQualMap,
                        NotificationLink, WebPage, UserPageRight, AppearSubject, DegreeAppearSubjectMap,
                        CollegeCategory, City, CollegeType, Discipline, SMSCollegeDegreeMap, UnivDegreeSpecMap)
from app.json_store import load_records, save_records, next_id
from app import db
from datetime import datetime
import os
from sqlalchemy import text, Table, MetaData, select, and_, delete as sa_delete, insert as sa_insert
import math

config_mgmt_bp = Blueprint('config_mgmt', __name__)

class Pagination:
    def __init__(self, page, per_page, total):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = int(math.ceil(total / float(per_page))) if total > 0 else 0
    @property
    def has_prev(self): return self.page > 1
    @property
    def has_next(self): return self.page < self.pages
    @property
    def prev_num(self): return self.page - 1
    @property
    def next_num(self): return self.page + 1
    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last + 1 != num: yield None
                yield num
                last = num

# --- Helper Functions ---

def _db_ping():
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:
        try: db.session.rollback()
        except: pass
        return False

def format_dt(val):
    if not val: return ""
    if isinstance(val, datetime): return val.strftime('%d/%m/%Y')
    if hasattr(val, 'strftime'): return val.strftime('%d/%m/%Y')
    return str(val)

def parse_dt(val):
    if not val or not str(val).strip(): return None
    v = str(val).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try: return datetime.strptime(v, fmt).date()
        except: continue
    return None

def safe_all(query_fn, default=None):
    try: return query_fn()
    except Exception: return [] if default is None else default

# --- MODULE 1: ADMISSION PROCESS CONFIGURATION ---


@config_mgmt_bp.before_request
def check_admin_auth():
    from flask import session, redirect, url_for, flash, request
    if not session.get('user_id'):
        if request.endpoint and 'login' not in request.endpoint:
            flash('Please login to access this section.', 'error')
            return redirect(url_for('main.login'))

@config_mgmt_bp.route('/admission-process-configuration', methods=['GET', 'POST'])
def admission_process_configuration():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    degrees = safe_all(lambda: db.session.execute(text("SELECT d.pk_degreeid as id, d.description + ' (' + dt.description + ')' as name FROM ACD_Degree_Mst d JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid=dt.pk_dtypeid WHERE d.active=1 ORDER BY d.description")).mappings().all(), default=[])
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); detail_id = request.args.get('detail_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    edit_record = None; detail_records = []; edit_detail = None
    if edit_id:
        er = db.session.execute(text("SELECT * FROM PA_AdmissionOpen_Mst WHERE Pk_AdmOpenId=:rid"), {"rid": edit_id}).mappings().first()
        if er:
            edit_record = {"id": er["Pk_AdmOpenId"], "session_id": str(er["Fk_SessionId"]), "order_no": er["Order_RefNo"], "dated": format_dt(er["Dated"]), "remarks": er["Remarks"]}
            drows = db.session.execute(text("SELECT t.*, d.description + ' (' + dt.description + ')' as dname FROM PA_AdmissionOpen_Trn t JOIN ACD_Degree_Mst d ON t.Fk_DegreeId=d.pk_degreeid JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid=dt.pk_dtypeid WHERE t.Fk_AdmOpenId=:rid"), {"rid": edit_id}).mappings().all()
            detail_records = [{"id": d["Pk_TrnId"], "degree_name": d["dname"], "degree_id": str(d["Fk_DegreeId"]), "login_allowed": bool(d["LoginAllowed"]), "entrance_date": format_dt(d["Entrance_date"]), "login_start": format_dt(d["Login_StartDate"]), "login_end": format_dt(d["Login_EndDate"]), "pay_start": format_dt(d["Login_PaymentStartDate"]), "pay_end": format_dt(d["Login_PaymentEndDate"]), "reg_start": format_dt(d["StartDate"]), "reg_end": format_dt(d["EndDate"]), "reg_late": format_dt(d["EndDateWithLateFee"]), "nri_start": format_dt(d["StartDateNRI"]), "nri_end": format_dt(d["EndDateNRI"]), "nri_late": format_dt(d["EndDateWithLateFeeNRI"]), "griv_start": format_dt(d["Grievances_StartDate"]), "griv_end": format_dt(d["Grievances_EndDate"]), "griv_fee": d["Grievances_Fees"], "mod_start": format_dt(d["ModifyPersonalStartDate"]), "mod_end": format_dt(d["ModifyPersonalEndDate"]), "mod_fee": d["PersonalInfoFee"], "admit_start": format_dt(d["Admit_Card_StartDate"]), "admit_end": format_dt(d["Admit_Card_EndDate"])} for d in drows]
            if detail_id: edit_detail = next((d for d in detail_records if str(d["id"]) == str(detail_id)), None)
    if request.method == 'POST':
        flash("Saved Successfully!", "success")
        return redirect(url_for('config_mgmt.admission_process_configuration', edit_id=request.form.get('id'), session_id=request.form.get('session_id'), _anchor='admForm'))
    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND m.Fk_SessionId = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_AdmissionOpen_Mst m " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT m.*, s.description as sname FROM PA_AdmissionOpen_Mst m JOIN LUP_AcademicSession_Mst s ON m.Fk_SessionId = s.pk_sessionid " + where + " ORDER BY m.Pk_AdmOpenId DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["Pk_AdmOpenId"], "session_name": r["sname"], "order_no": r["Order_RefNo"], "dated": format_dt(r["Dated"]), "remarks": r["Remarks"]} for r in rows]
    return render_template('admission_process_configuration.html', records=display_records, edit_record=edit_record, edit_detail=edit_detail, detail_records=detail_records, sessions=sessions, degrees=degrees, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

# --- MODULE 2: APPLICATION FEE CONFIGURATION ---

@config_mgmt_bp.route('/application-fee-config', methods=['GET', 'POST'])
def application_fee_config():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    # Corrected Degree List query for dropdown
    degrees_sql = """
        SELECT CAST(d.pk_degreeid AS VARCHAR) as id, 
               ISNULL(d.description, '') + ' (' + ISNULL(dt.description, 'N/A') + ')' as description 
        FROM ACD_Degree_Mst d 
        LEFT JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid = dt.pk_dtypeid 
        WHERE d.active = 1 
        ORDER BY d.description
    """
    degrees = safe_all(lambda: db.session.execute(text(degrees_sql)).mappings().all(), default=[])
    categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StuCatId as id, Description as name FROM PA_StudentCategory_Mst ORDER BY Description")).mappings().all(), default=[])
    
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 20; use_db = _db_ping()
    
    edit_record = None; detail_rows = []
    if edit_id:
        er = db.session.execute(text("SELECT * FROM PA_ApplicationFormFee_Config WHERE pk_feeconfigid=:rid"), {"rid": edit_id}).mappings().first()
        if er:
            edit_record = {"id": er["pk_feeconfigid"], "session_id": str(er["fk_sessionid"]), "degree_type_id": str(er["fk_degreeid"] or er["fk_dtypeid"]), "form_fee_ph": er["formfee_ph"], "effective_date": format_dt(er["effectivefrom"]), "late_fee": er["LateFee"]}
            drows = db.session.execute(text("SELECT t.*, cat.Description as catname FROM PA_ApplicationFormFee_Config_Trn t JOIN PA_StudentCategory_Mst cat ON t.fk_stucatid=cat.Pk_StuCatId WHERE t.fk_feeconfigid=:rid"), {"rid": edit_id}).mappings().all()
            detail_rows = [{"cat_id": d["fk_stucatid"], "cat_name": d["catname"], "min_age": d["minage"], "max_age": d["maxage"], "form_fee": d["formfee"], "late_form_fee": d["Late_formfee"], "other_form_fee": d["Other_formfee"], "other_late_form_fee": d["Other_Late_formfee"], "counse_fee": d["Counsefee"], "other_counse_fee": d["Other_Counsefee"], "age_re": d["AgeRe"], "as_on_date": format_dt(d["AsOnDate"])} for d in drows]
    
    if not edit_id:
        detail_rows = [{"cat_id": c["id"], "cat_name": c["name"], "min_age": 16, "max_age": 40, "form_fee": 0, "late_form_fee": 0, "other_form_fee": 0, "other_late_form_fee": 0, "counse_fee": 0, "other_counse_fee": 0, "age_re": 0, "as_on_date": datetime.now().strftime('%d/%m/%Y')} for c in categories]

    if request.method == 'POST':
        flash("Saved Successfully!", "success")
        return redirect(url_for('config_mgmt.application_fee_config', session_id=request.form.get("session_id"), _anchor='feeForm'))

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND m.fk_sessionid = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_ApplicationFormFee_Config m " + where), params).scalar()
        off = (page - 1) * per_page
        # Final robust Grid query: Handling string IDs and multiple join paths
        grid_sql = f"""
            SELECT m.*, s.description as sname, 
                   COALESCE(d.description, dt.description, 'Unknown') as target_name 
            FROM PA_ApplicationFormFee_Config m 
            JOIN LUP_AcademicSession_Mst s ON m.fk_sessionid = s.pk_sessionid 
            LEFT JOIN ACD_Degree_Mst d ON (CASE WHEN ISNUMERIC(m.fk_degreeid)=1 THEN CAST(m.fk_degreeid AS INT) ELSE NULL END) = d.pk_degreeid 
            LEFT JOIN ACD_DegreeType_Mst dt ON m.fk_dtypeid = dt.pk_dtypeid 
            {where} 
            ORDER BY m.pk_feeconfigid DESC 
            OFFSET {off} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        rows = db.session.execute(text(grid_sql), params).mappings().all()
        display_records = [{"id": r["pk_feeconfigid"], "session_name": r["sname"], "degree_type_name": r["target_name"], "effective_date": format_dt(r["effectivefrom"])} for r in rows]
    
    return render_template('application_fee_config.html', records=display_records, edit_record=edit_record, detail_rows=detail_rows, sessions=sessions, degree_types=degrees, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

# --- MODULE 3: COUNSELLING CONFIGURATION ---

@config_mgmt_bp.route('/counselling-configuration', methods=['GET', 'POST'])
def counselling_configuration():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    degrees = safe_all(lambda: Degree.query.order_by(Degree.id).all())
    colleges = safe_all(lambda: db.session.execute(text("SELECT Pk_CollegeID as id, CollegeName as name FROM PA_College_Mst ORDER BY CollegeName")).mappings().all(), default=[])
    # Aliased properly for template
    student_categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StuCatId as id, Description as description FROM PA_StudentCategory_Mst ORDER BY Description")).mappings().all(), default=[])
    
    selected_session_id = request.args.get('session_id') or "71"
    search_degree_id = request.args.get('search_degree_id') or "0"; edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); did = request.form.get("degree_id"); cid = request.form.get("college_id"); catid = request.form.get("cat_id"); cut = request.form.get("cutoff") or "0"; exm = 1 if request.form.get("exempt") == "on" else 0; sd = parse_dt(request.form.get("start_date")); ed = parse_dt(request.form.get("end_date")); pd = parse_dt(request.form.get("payment_date")); pwd = 1 if request.form.get("pwd") == "on" else 0
            if use_db:
                if rid: db.session.execute(text("UPDATE PA_CounCutOff_Mst SET Fk_DegreeID=:did, fk_collegeid=:cid, Fk_StuCatID=:catid, CutOffMarks=:cut, CounsDate=:sd, CounsEndDate=:ed, fk_Sessoinid=:sid, Exempt=:exm, paymentdate=:pd, pwd=:pwd WHERE Pk_CounsCutoffID=:rid"), {"rid": rid, "did": did, "cid": cid, "catid": catid, "cut": cut, "sd": sd, "ed": ed, "sid": sid, "exm": exm, "pd": pd, "pwd": pwd})
                else: db.session.execute(text("INSERT INTO PA_CounCutOff_Mst (Fk_DegreeID, fk_collegeid, Fk_StuCatID, CutOffMarks, CounsDate, CounsEndDate, fk_Sessoinid, Exempt, paymentdate, pwd) VALUES (:did, :cid, :catid, :cut, :sd, :ed, :sid, :exm, :pd, :pwd)"), {"did": did, "cid": cid, "catid": catid, "cut": cut, "sd": sd, "ed": ed, "sid": sid, "exm": exm, "pd": pd, "pwd": pwd})
                db.session.commit()
            flash("Record Saved Successfully!", "success")
        except Exception as e: flash(f"Error: {e}", "error")
        return redirect(url_for('config_mgmt.counselling_configuration', session_id=sid))

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND c.fk_Sessoinid = :sid"; params["sid"] = selected_session_id
        if search_degree_id and search_degree_id != "0": where += " AND c.Fk_DegreeID = :did"; params["did"] = search_degree_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_CounCutOff_Mst c " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT c.*, s.description AS sname, d.description AS dname, cat.Description AS catname, col.CollegeName AS colname FROM PA_CounCutOff_Mst c LEFT JOIN LUP_AcademicSession_Mst s ON c.fk_Sessoinid = s.pk_sessionid LEFT JOIN ACD_Degree_Mst d ON c.Fk_DegreeID = d.pk_degreeid LEFT JOIN PA_StudentCategory_Mst cat ON c.Fk_StuCatID = cat.Pk_StuCatId LEFT JOIN PA_College_Mst col ON c.fk_collegeid = col.Pk_CollegeID " + where + " ORDER BY c.Pk_CounsCutoffID DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["Pk_CounsCutoffID"], "session_name": r["sname"], "degree_name": r["dname"], "college_name": r["colname"] or "University Level", "cat_name": r["catname"], "cutoff": r["CutOffMarks"], "start_date": format_dt(r["CounsDate"]), "end_date": format_dt(r["CounsEndDate"]), "session_id": str(r["fk_Sessoinid"]), "degree_id": str(r["Fk_DegreeID"]), "college_id": str(r["fk_collegeid"]), "cat_id": str(r["Fk_StuCatID"]), "exempt": bool(r["Exempt"]), "payment_date": format_dt(r["paymentdate"]), "pwd": bool(r["pwd"])} for r in rows]
    
    edit_record = next((r for r in display_records if str(r["id"]) == str(edit_id)), None) if edit_id else None
    
    return render_template('counselling_configuration.html', records=display_records, edit_record=edit_record, sessions=sessions, degrees=degrees, colleges=colleges, student_categories=student_categories, search_degree_id=search_degree_id, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-counselling-configuration/<int:id>')
def delete_counselling_configuration(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PA_CounCutOff_Mst WHERE Pk_CounsCutoffID=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.counselling_configuration'))

# --- MODULE 4: STUDENT UPWARD CONFIGURATION ---

@config_mgmt_bp.route('/student-upward-configuration', methods=['GET', 'POST'])
def student_upward_configuration():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    degrees = safe_all(lambda: Degree.query.order_by(Degree.id).all())
    colleges = safe_all(lambda: db.session.execute(text("SELECT Pk_CollegeID as id, CollegeName as name FROM PA_College_Mst ORDER BY CollegeName")).mappings().all(), default=[])
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); did = request.form.get("degree_id"); cid = request.form.get("college_id"); cut = request.form.get("cutoff"); sd = parse_dt(request.form.get("start_date")); ed = parse_dt(request.form.get("end_date"))
            if use_db:
                if rid: db.session.execute(text("UPDATE pa_Student_Upward_Configuration_mst SET fk_sessionId=:sid, fk_DegreeID=:did, fk_CollegeID=:cid, fk_CutOff=:cut, fromdate=:sd, todate=:ed WHERE pk_id=:rid"), {"rid": rid, "sid": sid, "did": did, "cid": cid, "cut": cut, "sd": sd, "ed": ed})
                else: db.session.execute(text("INSERT INTO pa_Student_Upward_Configuration_mst (fk_sessionId, fk_DegreeID, fk_CollegeID, fk_CutOff, fromdate, todate) VALUES (:sid, :did, :cid, :cut, :sd, :ed)"), {"sid": sid, "did": did, "cid": cid, "cut": cut, "sd": sd, "ed": ed})
                db.session.commit()
            flash("Saved Successfully!", "success")
        except Exception as e: flash(f"Error: {e}", "error")
        return redirect(url_for('config_mgmt.student_upward_configuration', session_id=sid))

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND u.fk_sessionId = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM pa_Student_Upward_Configuration_mst u " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT u.*, s.description AS sname, d.description AS dname, c.CollegeName AS colname FROM pa_Student_Upward_Configuration_mst u LEFT JOIN LUP_AcademicSession_Mst s ON u.fk_sessionId = s.pk_sessionid LEFT JOIN ACD_Degree_Mst d ON u.fk_DegreeID = d.pk_degreeid LEFT JOIN PA_College_Mst c ON u.fk_CollegeID = c.Pk_CollegeID " + where + " ORDER BY u.pk_id DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["pk_id"], "session_name": r["sname"], "degree_name": r["dname"], "college_name": r["colname"] or "N/A", "cutoff": r["fk_CutOff"], "start_date": format_dt(r["fromdate"]), "end_date": format_dt(r["todate"]), "session_id": str(r["fk_sessionId"]), "degree_id": str(r["fk_DegreeID"]), "college_id": str(r["fk_CollegeID"])} for r in rows]
    
    edit_record = next((r for r in display_records if str(r["id"]) == str(edit_id)), None) if edit_id else None
    
    return render_template('student_upward_configuration.html', records=display_records, edit_record=edit_record, sessions=sessions, degrees=degrees, colleges=colleges, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-student-upward-configuration/<int:id>')
def delete_student_upward_configuration(id):
    if _db_ping(): db.session.execute(text("DELETE FROM pa_Student_Upward_Configuration_mst WHERE pk_id=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.student_upward_configuration'))

# --- MODULE 5: ADMIT CARD CONFIGURATION ---

@config_mgmt_bp.route('/admit-card-configuration', methods=['GET', 'POST'])
def admit_card_configuration():
    degrees = safe_all(lambda: Degree.query.filter(Degree.active==1).order_by(Degree.name).all())
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    selected_session_id = request.args.get('session_id') or "71"
    selected_degree_id = request.args.get('degree_id') or "0"
    selected_et_id = request.args.get('entrance_test_id') or "0"
    et_stmt = text("SELECT Pk_ETID, Description FROM PA_ET_Master WHERE fk_SessionId=:sid ORDER BY Description")
    entrance_tests = safe_all(lambda: db.session.execute(et_stmt, {"sid": selected_session_id}).mappings().all(), default=[])
    centers = []
    if selected_session_id != "0" and selected_et_id != "0":
        centers = safe_all(lambda: db.session.execute(text("SELECT pk_examCenterId AS pk_Examcid, Name AS Description, Code AS CentreCode FROM PA_Exam_Center_Mst WHERE fk_SessionId=:sid AND fk_ETID=:etid AND IsActive=1"), {"sid": selected_session_id, "etid": selected_et_id}).mappings().all(), default=[])
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    auto_data = None
    
    # If edit_id is passed, load that specific configuration directly.
    if edit_id:
        row = db.session.execute(text("SELECT TOP 1 * FROM PAD_AdmitCard_Config WHERE Fk_Examcid=:eid"), {"eid": edit_id}).mappings().first()
        if row:
            selected_degree_id = str(row['Fk_DegreeId'])
            selected_session_id = str(row['Fk_SessionId'])
            selected_et_id = str(row['Fk_ETID'])
            
            # Repopulate entrance tests and centers based on the loaded record
            et_stmt = text("SELECT Pk_ETID, Description FROM PA_ET_Master WHERE fk_SessionId=:sid ORDER BY Description")
            entrance_tests = safe_all(lambda: db.session.execute(et_stmt, {"sid": selected_session_id}).mappings().all(), default=[])
            centers = safe_all(lambda: db.session.execute(text("SELECT pk_examCenterId AS pk_Examcid, Name AS Description, Code AS CentreCode FROM PA_Exam_Center_Mst WHERE fk_SessionId=:sid AND fk_ETID=:etid AND IsActive=1"), {"sid": selected_session_id, "etid": selected_et_id}).mappings().all(), default=[])

            auto_data = {
                "id": row['Fk_Examcid'],
                "entrance_test_id": str(row['Fk_ETID']),
                "date_of_exam": format_dt(row["DateofExam"]), "day_of_exam": str(row["DayofExam"]),
                "reporting_time_h": str(row["ReportingTimeH"]), "reporting_time_m": str(row["ReportingTimeM"]), "reporting_time_ampm": str(row["ReportingTimeAPM"]).strip(),
                "duration_from_h": str(row["DurationFromH"]), "duration_from_m": str(row["DurationFromM"]), "duration_from_ampm": str(row["DurationFromAPM"]).strip(),
                "duration_to_h": str(row["DurationToH"]), "duration_to_m": str(row["DurationToM"]), "duration_to_ampm": str(row["DurationToAPM"]).strip(),
                "no_entry_after_h": str(row["NoEntryAfterH"]), "no_entry_after_m": str(row["NoEntryAfterM"]), "no_entry_after_ampm": str(row["NoEntryAfterAPM"]).strip(),
                "cannot_leave_h": str(row["CanotLeaveBeforeH"]), "cannot_leave_m": str(row["CanotLeaveBeforeM"]), "cannot_leave_ampm": str(row["CanotLeaveBeforeAPM"]).strip(),        
                "instructions": row["Instructions"]
            }
            # The specific configuration might belong to a group of centers configured at the same time
            checked_rows = []
            if selected_et_id and selected_et_id != 'None':
                checked_rows = db.session.execute(text("SELECT Fk_Examcid FROM PAD_AdmitCard_Config WHERE Fk_DegreeId=:did AND Fk_SessionId=:sid AND Fk_ETID=:etid"), {"did": selected_degree_id, "sid": selected_session_id, "etid": selected_et_id}).mappings().all()
            auto_data["checked_centers"] = [str(r["Fk_Examcid"]) for r in checked_rows]

    # Original auto-fill logic if just changing dropdowns
    elif selected_session_id != "0" and selected_degree_id != "0":
        inst_fallback = db.session.execute(text("SELECT TOP 1 Instruction FROM Pa_Instruction_mst WHERE fk_DegreeID=:did AND fk_SessionID=:sid AND Active=1"), {"did": selected_degree_id, "sid": selected_session_id}).scalar()
        prev_config = db.session.execute(text("SELECT TOP 1 Instructions FROM PAD_AdmitCard_Config WHERE Fk_DegreeId=:did AND Instructions IS NOT NULL AND LEN(CAST(Instructions AS VARCHAR(MAX))) > 10 ORDER BY Fk_SessionId DESC"), {"did": selected_degree_id}).scalar()
        final_inst = prev_config if prev_config else inst_fallback
        row = db.session.execute(text("SELECT TOP 1 * FROM PAD_AdmitCard_Config WHERE Fk_DegreeId=:did AND Fk_SessionId=:sid AND Fk_ETID=:etid"), {"did": selected_degree_id, "sid": selected_session_id, "etid": selected_et_id}).mappings().first()
        if row:
            auto_data = {
                "date_of_exam": format_dt(row["DateofExam"]), "day_of_exam": str(row["DayofExam"]),
                "reporting_time_h": str(row["ReportingTimeH"]), "reporting_time_m": str(row["ReportingTimeM"]), "reporting_time_ampm": str(row["ReportingTimeAPM"]).strip(),
                "duration_from_h": str(row["DurationFromH"]), "duration_from_m": str(row["DurationFromM"]), "duration_from_ampm": str(row["DurationFromAPM"]).strip(),
                "duration_to_h": str(row["DurationToH"]), "duration_to_m": str(row["DurationToM"]), "duration_to_ampm": str(row["DurationToAPM"]).strip(),
                "no_entry_after_h": str(row["NoEntryAfterH"]), "no_entry_after_m": str(row["NoEntryAfterM"]), "no_entry_after_ampm": str(row["NoEntryAfterAPM"]).strip(),
                "cannot_leave_h": str(row["CanotLeaveBeforeH"]), "cannot_leave_m": str(row["CanotLeaveBeforeM"]), "cannot_leave_ampm": str(row["CanotLeaveBeforeAPM"]).strip(),        
                "instructions": row["Instructions"] or final_inst
            }
            checked_rows = []
            if selected_et_id and selected_et_id != 'None':
                checked_rows = db.session.execute(text("SELECT Fk_Examcid FROM PAD_AdmitCard_Config WHERE Fk_DegreeId=:did AND Fk_SessionId=:sid AND Fk_ETID=:etid"), {"did": selected_degree_id, "sid": selected_session_id, "etid": selected_et_id}).mappings().all()
            auto_data["checked_centers"] = [str(r["Fk_Examcid"]) for r in checked_rows]
        elif final_inst:
            auto_data = {"instructions": final_inst}

    if request.method == 'POST':
        try:
            sid = request.form.get("session_id"); did = request.form.get("degree_id"); etid = request.form.get("entrance_test_id"); inst = request.form.get("instructions"); doe = parse_dt(request.form.get("date_of_exam")); day = request.form.get("day_of_exam"); rth = request.form.get("reporting_time_h"); rtm = request.form.get("reporting_time_m"); rtp = request.form.get("reporting_time_ampm"); neh = request.form.get("no_entry_after_h"); nem = request.form.get("no_entry_after_m"); nep = request.form.get("no_entry_after_ampm"); dfh = request.form.get("duration_from_h"); dfm = request.form.get("duration_from_m"); dfp = request.form.get("duration_from_ampm"); dth = request.form.get("duration_to_h"); dtm = request.form.get("duration_to_m"); dtp = request.form.get("duration_to_ampm"); clh = request.form.get("cannot_leave_h"); clm = request.form.get("cannot_leave_m"); clp = request.form.get("cannot_leave_ampm"); selected_centers = request.form.getlist("exam_center_ids")
            if use_db:
                db.session.execute(text("DELETE FROM PAD_AdmitCard_Config WHERE Fk_DegreeId=:did AND Fk_SessionId=:sid AND Fk_ETID=:etid"), {"did": did, "sid": sid, "etid": etid})
                for cid in selected_centers:
                    db.session.execute(text("INSERT INTO PAD_AdmitCard_Config (DateofExam, DayofExam, ReportingTimeH, ReportingTimeM, ReportingTimeAPM, DurationFromH, DurationFromM, DurationFromAPM, DurationToH, DurationToM, DurationToAPM, NoEntryAfterH, NoEntryAfterM, NoEntryAfterAPM, CanotLeaveBeforeH, CanotLeaveBeforeM, CanotLeaveBeforeAPM, Fk_DegreeId, Fk_SessionId, Instructions, Fk_ETID, Fk_Examcid) VALUES (:doe, :day, :rth, :rtm, :rtp, :dfh, :dfm, :dfp, :dth, :dtm, :dtp, :neh, :nem, :nep, :clh, :clm, :clp, :did, :sid, :inst, :etid, :cid)"), {"doe": doe, "day": day, "rth": rth, "rtm": rtm, "rtp": rtp, "dfh": dfh, "dfm": dfm, "dfp": dfp, "dth": dth, "dtm": dtm, "dtp": dtp, "neh": neh, "nem": nem, "nep": nep, "clh": clh, "clm": clm, "clp": clp, "did": did, "sid": sid, "inst": inst, "etid": etid, "cid": cid})
                db.session.commit()
            flash("Saved Successfully!", "success"); selected_session_id = sid
        except Exception as e: flash(f"Error: {e}", "error")
        return redirect(url_for('config_mgmt.admit_card_configuration', session_id=selected_session_id))
    
    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND c.Fk_SessionId = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PAD_AdmitCard_Config c " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT c.*, s.description AS sname, d.description AS dname, et.Description AS etname FROM PAD_AdmitCard_Config c LEFT JOIN LUP_AcademicSession_Mst s ON c.Fk_SessionId = s.pk_sessionid LEFT JOIN ACD_Degree_Mst d ON c.Fk_DegreeId = d.pk_degreeid LEFT JOIN PA_ET_Master et ON c.Fk_ETID = et.Pk_ETID " + where + " ORDER BY c.Fk_Examcid DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["Fk_Examcid"], "session_name": r["sname"], "degree_name": r["dname"], "et_name": r["etname"], "date_of_exam": format_dt(r["DateofExam"]), "reporting_time_h": r["ReportingTimeH"], "reporting_time_m": r["ReportingTimeM"], "reporting_time_ampm": r["ReportingTimeAPM"], "session_id": str(r["Fk_SessionId"]), "degree_id": str(r["Fk_DegreeId"]), "entrance_test_id": str(r["Fk_ETID"])} for r in rows]
    
    final_edit_record = auto_data if auto_data else None
    checked_centers = auto_data.get("checked_centers", []) if auto_data else []
    return render_template('admit_card_configuration.html', records=display_records, edit_record=final_edit_record, checked_centers=checked_centers, sessions=sessions, degrees=degrees, entrance_tests=entrance_tests, centers=centers, selected_session_id=selected_session_id, selected_degree_id=selected_degree_id, pagination=Pagination(page, per_page, total_records))

# --- MODULE 6: ROSTER MASTER ---

@config_mgmt_bp.route('/roster-master', methods=['GET', 'POST'])
def roster_master():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    streams = safe_all(lambda: db.session.execute(text("SELECT pk_collegetypeid as id, description as name FROM ACD_CollegeType_Mst ORDER BY description")).mappings().all(), default=[])
    colleges = safe_all(lambda: db.session.execute(text("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst ORDER BY collegename")).mappings().all(), default=[])
    
    degree_sql = """
        SELECT d.pk_degreeid as id, 
               ISNULL(d.description, '') + ' (' + ISNULL(dt.description, 'N/A') + ')' as description 
        FROM ACD_Degree_Mst d 
        LEFT JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid = dt.pk_dtypeid 
        WHERE d.active = 1 
        ORDER BY d.description
    """
    degree_types = safe_all(lambda: db.session.execute(text(degree_sql)).mappings().all(), default=[])
    
    categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StuCatId as id, Description as description FROM PA_StudentCategory_Mst ORDER BY Description")).mappings().all(), default=[])
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); stid = request.form.get("stream_id"); cid = request.form.get("college_id"); dtid = request.form.get("degree_type_id"); catid = request.form.get("category_id"); seq = request.form.get("sequence")
            if use_db:
                if rid: db.session.execute(text("UPDATE PA_Roaster_Master SET fk_sessionid=:sid, fk_StreamID=:stid, fk_CollegeID=:cid, fk_degreeid=:dtid, Fk_StuCatId=:catid, Sequence=:seq WHERE PK_RID=:rid"), {"rid": rid, "sid": sid, "stid": stid, "cid": cid, "dtid": dtid, "catid": catid, "seq": seq})
                else: db.session.execute(text("INSERT INTO PA_Roaster_Master (fk_sessionid, fk_StreamID, fk_CollegeID, fk_degreeid, Fk_StuCatId, Sequence) VALUES (:sid, :stid, :cid, :dtid, :catid, :seq)"), {"sid": sid, "stid": stid, "cid": cid, "dtid": dtid, "catid": catid, "seq": seq})
                db.session.commit()
            flash("Saved Successfully!", "success")
        except Exception as e: flash(f"Error: {e}", "error")
        return redirect(url_for('config_mgmt.roster_master', session_id=selected_session_id))
    
    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND r.fk_sessionid = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_Roaster_Master r " + where), params).scalar()
        off = (page - 1) * per_page
        
        stmt = text(f"""
            SELECT r.*, s.description as sname, st.description as stname, c.collegename as cname, 
                   ISNULL(d.description, '') + ' (' + ISNULL(dt.description, 'N/A') + ')' as dtname, 
                   cat.Description as catname 
            FROM PA_Roaster_Master r 
            LEFT JOIN LUP_AcademicSession_Mst s ON r.fk_sessionid = s.pk_sessionid 
            LEFT JOIN ACD_CollegeType_Mst st ON r.fk_StreamID = st.pk_collegetypeid 
            LEFT JOIN SMS_College_Mst c ON r.fk_CollegeID = c.pk_collegeid 
            LEFT JOIN ACD_Degree_Mst d ON r.fk_degreeid = d.pk_degreeid 
            LEFT JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid = dt.pk_dtypeid 
            LEFT JOIN PA_StudentCategory_Mst cat ON r.Fk_StuCatId = cat.Pk_StuCatId 
            {where} 
            ORDER BY r.PK_RID DESC 
            OFFSET {off} ROWS FETCH NEXT {per_page} ROWS ONLY
        """)
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["PK_RID"], "session_name": r["sname"], "stream_name": r["stname"], "college_name": r["cname"], "degree_type_name": r["dtname"], "category_name": r["catname"], "sequence": r["Sequence"], "session_id": str(r["fk_sessionid"]), "stream_id": str(r["fk_StreamID"]), "college_id": str(r["fk_CollegeID"]), "degree_type_id": str(r["fk_degreeid"]), "category_id": str(r["Fk_StuCatId"])} for r in rows]
    
    edit_record = next((r for r in display_records if str(r["id"]) == str(edit_id)), None) if edit_id else None
    
    return render_template('roster_master.html', records=display_records, edit_record=edit_record, sessions=sessions, streams=streams, colleges=colleges, degree_types=degree_types, categories=categories, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

# --- MODULE 7: UG SEAT MATRIX MASTER ---

@config_mgmt_bp.route('/ug-seat-matrix-master', methods=['GET', 'POST'])
def ug_seat_matrix_master():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    degrees = safe_all(lambda: Degree.query.filter(Degree.active==1).order_by(Degree.name).all())
    colleges = safe_all(lambda: db.session.execute(text("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst ORDER BY collegename")).mappings().all(), default=[])
    student_categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StuCatId, Description FROM PA_StudentCategory_Mst ORDER BY Description")).mappings().all(), default=[])
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); detail_id = request.args.get('detail_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    edit_record = None; detail_records = []; other_seats = {"ldv": 0, "emp_ward": 0, "sports": 0}; edit_detail = None
    if edit_id:
        er = db.session.execute(text("SELECT * FROM PA_SeatMatrix_Mst WHERE Pk_SeatMatrixID=:rid"), {"rid": edit_id}).mappings().first()
        if er:
            edit_record = {"id": er["Pk_SeatMatrixID"], "session_id": str(er["Fk_Sessionid"]), "degree_id": str(er["Fk_DegreeID"]), "college_id": str(er["Fk_collegeid"])}
            drows = db.session.execute(text("SELECT t.*, cat.Description as catname FROM PA_SeatMatrix_Trn t LEFT JOIN PA_StudentCategory_Mst cat ON t.Fk_StuCatID=cat.Pk_StuCatId WHERE t.Fk_SeatMatrixID=:rid"), {"rid": edit_id}).mappings().all()
            detail_records = [{"id": d["Pk_SeatMatrixTrnID"], "gender": d["GenderID"], "category_name": d["catname"], "cat_id": str(d["Fk_StuCatID"]), "is_esm": d["ESMSeat"], "seats": d["CollegeWiseSeat"]} for d in drows]
            oth = db.session.execute(text("SELECT * FROM PA_SeatMatrixOther_Trn WHERE Fk_SeatMatrixID=:rid"), {"rid": edit_id}).mappings().first()
            if oth: other_seats = {"ldv": oth["LDVSeat"], "emp_ward": oth["EmployeeWardSeat"], "sports": oth["Sports"]}
            if detail_id: edit_detail = next((d for d in detail_records if str(d["id"]) == str(detail_id)), None)
    if request.method == 'POST':
        flash("Saved Successfully!", "success")
        return redirect(url_for('config_mgmt.ug_seat_matrix_master', edit_id=request.form.get('id'), session_id=request.form.get('session_id'), _anchor='seatMatrixForm'))
    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND m.Fk_Sessionid = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_SeatMatrix_Mst m " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT m.Pk_SeatMatrixID as id, s.description as sname, d.description as dname, c.collegename as cname FROM PA_SeatMatrix_Mst m JOIN LUP_AcademicSession_Mst s ON m.Fk_Sessionid = s.pk_sessionid JOIN ACD_Degree_Mst d ON m.Fk_DegreeID = d.pk_degreeid JOIN SMS_College_Mst c ON m.Fk_collegeid = c.pk_collegeid " + where + " ORDER BY m.Pk_SeatMatrixID DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["id"], "session_name": r["sname"], "degree_name": r["dname"], "college_name": r["cname"]} for r in rows]
    return render_template('ug_seat_matrix_master.html', records=display_records, edit_record=edit_record, edit_detail=edit_detail, detail_records=detail_records, other_seats=other_seats, sessions=sessions, degrees=degrees, colleges=colleges, student_categories=student_categories, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

# --- STUBS ---
@config_mgmt_bp.route('/instructions-master', methods=['GET', 'POST'])
def instructions_master():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    
    degree_sql = """
        SELECT d.pk_degreeid as id, 
               ISNULL(d.description, '') + ' (' + ISNULL(dt.description, 'N/A') + ')' as description 
        FROM ACD_Degree_Mst d 
        LEFT JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid = dt.pk_dtypeid 
        WHERE d.active = 1 
        ORDER BY d.description
    """
    degrees = safe_all(lambda: db.session.execute(text(degree_sql)).mappings().all(), default=[])
    
    selected_session_id = request.args.get('session_id') or "0"
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); did = request.form.get("degree_id"); inst = request.form.get("instruction"); ob = request.form.get("order_by") or "1"; active = 1 if request.form.get("is_active") == "on" else 0
            if use_db:
                if rid: db.session.execute(text("UPDATE Pa_Instruction_mst SET fk_SessionID=:sid, fk_DegreeID=:did, Instruction=:inst, OrderBy=:ob, Active=:active WHERE pk_ID=:rid"), {"rid": rid, "sid": sid, "did": did, "inst": inst, "ob": ob, "active": active})
                else: db.session.execute(text("INSERT INTO Pa_Instruction_mst (fk_SessionID, fk_DegreeID, Instruction, OrderBy, Active) VALUES (:sid, :did, :inst, :ob, :active)"), {"sid": sid, "did": did, "inst": inst, "ob": ob, "active": active})
                db.session.commit()
            flash("Record Saved Successfully!", "success")
            return redirect(url_for('config_mgmt.instructions_master', session_id=sid, _anchor='instForm'))
        except Exception as e: flash(f"Error: {e}", "error")

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND i.fk_SessionID = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM Pa_Instruction_mst i " + where), params).scalar()
        off = (page - 1) * per_page
        
        stmt = text(f"""
            SELECT i.*, s.description as sname, 
                   ISNULL(d.description, '') + ' (' + ISNULL(dt.description, 'N/A') + ')' as dname 
            FROM Pa_Instruction_mst i 
            LEFT JOIN LUP_AcademicSession_Mst s ON i.fk_SessionID = s.pk_sessionid 
            LEFT JOIN ACD_Degree_Mst d ON i.fk_DegreeID = d.pk_degreeid 
            LEFT JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid = dt.pk_dtypeid 
            {where} 
            ORDER BY i.pk_ID DESC 
            OFFSET {off} ROWS FETCH NEXT {per_page} ROWS ONLY
        """)
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["pk_ID"], "session_name": r["sname"], "degree_name": r["dname"], "instruction": r["Instruction"], "active": bool(r["Active"]), "order_by": r["OrderBy"], "session_id": str(r["fk_SessionID"]), "degree_id": str(r["fk_DegreeID"])} for r in rows]
    
    edit_record = None
    if edit_id:
        er = db.session.execute(text("SELECT * FROM Pa_Instruction_mst WHERE pk_ID=:rid"), {"rid": edit_id}).mappings().first()
        if er: edit_record = {"id": er["pk_ID"], "session_id": str(er["fk_SessionID"]), "degree_id": str(er["fk_DegreeID"]), "instruction": er["Instruction"], "order_by": er["OrderBy"], "active": bool(er["Active"])}

    return render_template('instructions_master.html', records=display_records, edit_record=edit_record, sessions=sessions, degrees=degrees, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-instructions-master/<int:id>')
def delete_instructions_master(id):
    if _db_ping(): db.session.execute(text("DELETE FROM Pa_Instruction_mst WHERE pk_ID=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.instructions_master'))
@config_mgmt_bp.route('/allotment-letter-master', methods=['GET', 'POST'])
def allotment_letter_master():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    degrees = safe_all(lambda: db.session.execute(text("SELECT d.pk_degreeid as id, d.description + ' (' + dt.description + ')' as description FROM ACD_Degree_Mst d JOIN ACD_DegreeType_Mst dt ON d.fk_dtypeid=dt.pk_dtypeid WHERE d.active=1 ORDER BY d.description")).mappings().all(), default=[])
    colleges = safe_all(lambda: db.session.execute(text("SELECT pk_collegeid as id, collegename as name FROM SMS_College_Mst ORDER BY collegename")).mappings().all(), default=[])
    
    selected_session_id = request.args.get('session_id') or "71"
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); did = request.form.get("degree_id"); cid = request.form.get("college_id")
            cut = request.form.get("cutoff"); ven = request.form.get("venue"); ano = request.form.get("allotment_no")
            rf = parse_dt(request.form.get("report_from")); rt = parse_dt(request.form.get("report_to"))
            pf = parse_dt(request.form.get("print_from")); pt = parse_dt(request.form.get("print_to"))
            ph = 1 if request.form.get("ph_before_merit") == "on" else 0
            if use_db:
                if rid: db.session.execute(text("UPDATE PA_AllotmentLetter_Mst SET Fk_DegreeId=:did, Fk_CollegeId=:cid, Fk_SessionId=:sid, CutOff=:cut, Venue=:ven, ReportTextFromDate=:rf, ReportTextEndDate=:rt, AllotmentPrintFrom=:pf, AllotmentPrintTo=:pt, IsPH_BeforeMerit=:ph, AllotmentNo=:ano WHERE Pk_AllotmentId=:rid"), {"rid": rid, "did": did, "cid": cid, "sid": sid, "cut": cut, "ven": ven, "rf": rf, "rt": rt, "pf": pf, "pt": pt, "ph": ph, "ano": ano})
                else: db.session.execute(text("INSERT INTO PA_AllotmentLetter_Mst (Fk_DegreeId, Fk_CollegeId, Fk_SessionId, CutOff, Venue, ReportTextFromDate, ReportTextEndDate, AllotmentPrintFrom, AllotmentPrintTo, IsPH_BeforeMerit, AllotmentNo) VALUES (:did, :cid, :sid, :cut, :ven, :rf, :rt, :pf, :pt, :ph, :ano)"), {"did": did, "cid": cid, "sid": sid, "cut": cut, "ven": ven, "rf": rf, "rt": rt, "pf": pf, "pt": pt, "ph": ph, "ano": ano})
                db.session.commit()
            flash("Record Saved Successfully!", "success")
            return redirect(url_for('config_mgmt.allotment_letter_master', session_id=sid, _anchor='allotForm'))
        except Exception as e: flash(f"Error: {e}", "error")

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND a.Fk_SessionId = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_AllotmentLetter_Mst a " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT a.*, s.description as sname, d.description as dname, c.collegename as cname FROM PA_AllotmentLetter_Mst a JOIN LUP_AcademicSession_Mst s ON a.Fk_SessionId = s.pk_sessionid JOIN ACD_Degree_Mst d ON a.Fk_DegreeId = d.pk_degreeid JOIN SMS_College_Mst c ON a.Fk_CollegeId = c.pk_collegeid " + where + " ORDER BY a.Pk_AllotmentId DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["Pk_AllotmentId"], "session_name": r["sname"], "degree_name": r["dname"], "college_name": r["cname"], "cutoff": r["CutOff"], "allotment_no": r["AllotmentNo"], "print_from": format_dt(r["AllotmentPrintFrom"]), "print_to": format_dt(r["AllotmentPrintTo"]), "is_ph": bool(r["IsPH_BeforeMerit"])} for r in rows]
    
    edit_record = None
    if edit_id:
        er = db.session.execute(text("SELECT * FROM PA_AllotmentLetter_Mst WHERE Pk_AllotmentId=:rid"), {"rid": edit_id}).mappings().first()
        if er: edit_record = {"id": er["Pk_AllotmentId"], "session_id": str(er["Fk_SessionId"]), "degree_id": str(er["Fk_DegreeId"]), "college_id": str(er["Fk_CollegeId"]), "cutoff": er["CutOff"], "venue": er["Venue"], "report_from": format_dt(er["ReportTextFromDate"]), "report_to": format_dt(er["ReportTextEndDate"]), "print_from": format_dt(er["AllotmentPrintFrom"]), "print_to": format_dt(er["AllotmentPrintTo"]), "allotment_no": er["AllotmentNo"], "ph_before_merit": bool(er["IsPH_BeforeMerit"])}

    return render_template('allotment_letter_master.html', records=display_records, edit_record=edit_record, sessions=sessions, degrees=degrees, colleges=colleges, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-allotment-letter-master/<int:id>')
def delete_allotment_letter_master(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PA_AllotmentLetter_Mst WHERE Pk_AllotmentId=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.allotment_letter_master'))
@config_mgmt_bp.route('/duty-letter-configuration', methods=['GET', 'POST'])
def duty_letter_configuration():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    selected_session_id = request.args.get('session_id') or "71"
    entrance_tests = safe_all(lambda: db.session.execute(text("SELECT Pk_ETID, Description FROM PA_ET_Master WHERE fk_SessionId=:sid ORDER BY Description"), {"sid": selected_session_id}).mappings().all(), default=[])
    
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); etid = request.form.get("et_id")
            fd = parse_dt(request.form.get("from_date")); td = parse_dt(request.form.get("to_date"))
            active = 1 if request.form.get("is_active") == "on" else 0
            if use_db:
                if rid: db.session.execute(text("UPDATE PA_DutyLetter_Config SET FK_ETID=:etid, FK_sessionid=:sid, FromDate=:fd, ToDate=:td, Active=:active WHERE pk_dutyConfig=:rid"), {"rid": rid, "etid": etid, "sid": sid, "fd": fd, "td": td, "active": active})
                else: db.session.execute(text("INSERT INTO PA_DutyLetter_Config (FK_ETID, FK_sessionid, FromDate, ToDate, Active) VALUES (:etid, :sid, :fd, :td, :active)"), {"etid": etid, "sid": sid, "fd": fd, "td": td, "active": active})
                db.session.commit()
            flash("Record Saved Successfully!", "success")
            return redirect(url_for('config_mgmt.duty_letter_configuration', session_id=sid, _anchor='dutyForm'))
        except Exception as e: flash(f"Error: {e}", "error")

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND d.FK_sessionid = :sid"; params["sid"] = selected_session_id
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_DutyLetter_Config d " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text("SELECT d.*, s.description as sname, et.Description as etname FROM PA_DutyLetter_Config d LEFT JOIN LUP_AcademicSession_Mst s ON d.FK_sessionid = s.pk_sessionid LEFT JOIN PA_ET_Master et ON d.FK_ETID = et.Pk_ETID " + where + " ORDER BY d.pk_dutyConfig DESC OFFSET " + str(off) + " ROWS FETCH NEXT " + str(per_page) + " ROWS ONLY")
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["pk_dutyConfig"], "session_name": r["sname"], "et_name": r["etname"], "from_date": format_dt(r["FromDate"]), "to_date": format_dt(r["ToDate"]), "active": bool(r["Active"])} for r in rows]
    
    edit_record = None
    if edit_id:
        er = db.session.execute(text("SELECT * FROM PA_DutyLetter_Config WHERE pk_dutyConfig=:rid"), {"rid": edit_id}).mappings().first()
        if er: edit_record = {"id": er["pk_dutyConfig"], "session_id": str(er["FK_sessionid"]), "et_id": str(er["FK_ETID"]), "from_date": format_dt(er["FromDate"]), "to_date": format_dt(er["ToDate"]), "active": bool(er["Active"])}

    return render_template('duty_letter_configuration.html', records=display_records, edit_record=edit_record, sessions=sessions, entrance_tests=entrance_tests, selected_session_id=selected_session_id, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-duty-letter-configuration/<int:id>')
def delete_duty_letter_configuration(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PA_DutyLetter_Config WHERE pk_dutyConfig=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.duty_letter_configuration'))
@config_mgmt_bp.route('/category-remuneration-configuration', methods=['GET', 'POST'])
def category_remuneration_configuration():
    sessions = safe_all(lambda: AcademicSession.query.order_by(AcademicSession.id.desc()).all())
    selected_session_id = request.args.get('session_id') or "71"
    
    entrance_tests = safe_all(lambda: db.session.execute(text("SELECT Pk_ETID as id, Description as name FROM PA_ET_Master WHERE fk_SessionId=:sid ORDER BY Description"), {"sid": selected_session_id}).mappings().all(), default=[])
    staff_types = safe_all(lambda: db.session.execute(text("SELECT Pk_Staff_TypeID as id, Description as name FROM StaffType_Mst ORDER BY Description")).mappings().all(), default=[])
    staff_categories = safe_all(lambda: db.session.execute(text("SELECT Pk_StaffCatID as id, Description as name FROM StaffCategory_Mst ORDER BY Description")).mappings().all(), default=[])
    remunerations = [{"id": "Fixed", "name": "Fixed"}, {"id": "Day Wise", "name": "Day Wise"}]
    
    edit_id = request.args.get('edit_id'); page = request.args.get('page', 1, type=int); per_page = 10; use_db = _db_ping()
    
    if request.method == 'POST':
        try:
            rid = request.form.get('id'); sid = request.form.get("session_id"); etid = request.form.get("et_id")
            etd = parse_dt(request.form.get("et_date")); fd = parse_dt(request.form.get("from_date")); td = parse_dt(request.form.get("to_date"))
            rem = request.form.get("remuneration"); amt = request.form.get("amount"); scid = request.form.get("staff_category")
            if use_db:
                if rid: db.session.execute(text("UPDATE PA_Cat_Remuneration_Configuration SET Fk_ETID=:etid, ETDate=:etd, FromDate=:fd, ToDate=:td, Remuneration=:rem, Amount=:amt, Pk_StaffCatID=:scid, fk_sessionid=:sid WHERE Pk_Id=:rid"), {"rid": rid, "etid": etid, "etd": etd, "fd": fd, "td": td, "rem": rem, "amt": amt, "scid": scid, "sid": sid})
                else: db.session.execute(text("INSERT INTO PA_Cat_Remuneration_Configuration (Fk_ETID, ETDate, FromDate, ToDate, Remuneration, Amount, Pk_StaffCatID, fk_sessionid) VALUES (:etid, :etd, :fd, :td, :rem, :amt, :scid, :sid)"), {"etid": etid, "etd": etd, "fd": fd, "td": td, "rem": rem, "amt": amt, "scid": scid, "sid": sid})
                db.session.commit()
            flash("Record Saved Successfully!", "success")
            return redirect(url_for('config_mgmt.category_remuneration_configuration', session_id=sid, _anchor='remForm'))
        except Exception as e: flash(f"Error: {e}", "error")

    display_records = []; total_records = 0
    if use_db:
        where = " WHERE 1=1"; params = {}
        if selected_session_id != "0": where += " AND c.fk_sessionid = :sid"; params["sid"] = selected_session_id
        
        # Additional search filters
        f_et = request.args.get("f_et")
        if f_et: where += " AND c.Fk_ETID = :fet"; params["fet"] = f_et
        
        f_staff_cat = request.args.get("f_staff_cat")
        if f_staff_cat: where += " AND c.Pk_StaffCatID = :fsc"; params["fsc"] = f_staff_cat
        
        total_records = db.session.execute(text("SELECT COUNT(*) FROM PA_Cat_Remuneration_Configuration c " + where), params).scalar()
        off = (page - 1) * per_page
        stmt = text(f"""
            SELECT c.*, s.description as sname, et.Description as etname, sc.Description as scname, st.Description as stname 
            FROM PA_Cat_Remuneration_Configuration c 
            LEFT JOIN LUP_AcademicSession_Mst s ON c.fk_sessionid = s.pk_sessionid 
            LEFT JOIN PA_ET_Master et ON c.Fk_ETID = et.Pk_ETID 
            LEFT JOIN StaffCategory_Mst sc ON c.Pk_StaffCatID = sc.Pk_StaffCatID 
            LEFT JOIN StaffType_Mst st ON sc.Fk_Staff_TypeID = st.Pk_Staff_TypeID 
            {where} ORDER BY c.Pk_Id DESC OFFSET {off} ROWS FETCH NEXT {per_page} ROWS ONLY
        """)
        rows = db.session.execute(stmt, params).mappings().all()
        display_records = [{"id": r["Pk_Id"], "session_name": r["sname"], "et_name": r["etname"], "staff_type": r["stname"], "staff_category": r["scname"], "et_date": format_dt(r["ETDate"]), "from_date": format_dt(r["FromDate"]), "to_date": format_dt(r["ToDate"]), "remuneration": r["Remuneration"], "amount": r["Amount"]} for r in rows]
    
    edit_record = None
    if edit_id:
        er = db.session.execute(text("SELECT c.*, sc.Fk_Staff_TypeID FROM PA_Cat_Remuneration_Configuration c LEFT JOIN StaffCategory_Mst sc ON c.Pk_StaffCatID = sc.Pk_StaffCatID WHERE c.Pk_Id=:rid"), {"rid": edit_id}).mappings().first()
        if er: edit_record = {"id": er["Pk_Id"], "session_id": str(er["fk_sessionid"]), "et_id": str(er["Fk_ETID"]), "et_date": format_dt(er["ETDate"]), "from_date": format_dt(er["FromDate"]), "to_date": format_dt(er["ToDate"]), "remuneration": er["Remuneration"], "amount": er["Amount"], "staff_category": str(er["Pk_StaffCatID"]), "staff_type": str(er["Fk_Staff_TypeID"])}

    return render_template('category_remuneration_configuration.html', records=display_records, edit_record=edit_record, sessions=sessions, entrance_tests=entrance_tests, staff_types=staff_types, staff_categories=staff_categories, remunerations=remunerations, selected_session_id=selected_session_id, f_et=f_et, f_staff_cat=f_staff_cat, pagination=Pagination(page, per_page, total_records))

@config_mgmt_bp.route('/delete-category-remuneration-configuration/<int:id>')
def delete_category_remuneration_configuration(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PA_Cat_Remuneration_Configuration WHERE Pk_Id=:id"), {"id": id}); db.session.commit()
    flash("Deleted Successfully!", "success"); return redirect(url_for('config_mgmt.category_remuneration_configuration'))
@config_mgmt_bp.route('/student-additional-fee-config', methods=['GET', 'POST'])
def student_additional_fee_config(): return render_template('student_additional_fee_config.html', records=[])
@config_mgmt_bp.route('/delete-roster-master/<int:id>')
def delete_roster_master(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PA_Roaster_Master WHERE PK_RID=:id"), {"id": id}); db.session.commit()
    return redirect(url_for('config_mgmt.roster_master'))
@config_mgmt_bp.route('/delete-ug-seat-matrix-master/<int:id>')
def delete_ug_seat_matrix_master(id):
    if _db_ping():
        db.session.execute(text("DELETE FROM PA_SeatMatrix_Trn WHERE Fk_SeatMatrixID=:id"), {"id": id})
        db.session.execute(text("DELETE FROM PA_SeatMatrixOther_Trn WHERE Fk_SeatMatrixID=:id"), {"id": id})
        db.session.execute(text("DELETE FROM PA_SeatMatrix_Mst WHERE Pk_SeatMatrixID=:id"), {"id": id})
        db.session.commit()
    return redirect(url_for('config_mgmt.ug_seat_matrix_master'))
@config_mgmt_bp.route('/delete-admit-card-configuration/<int:id>')
def delete_admit_card_configuration(id):
    if _db_ping(): db.session.execute(text("DELETE FROM PAD_AdmitCard_Config WHERE Fk_Examcid=:id"), {"id": id}); db.session.commit()
    return redirect(url_for('config_mgmt.admit_card_configuration'))
