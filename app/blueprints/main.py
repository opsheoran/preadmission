from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from app.models import (AnswerKeyExamType, AcademicSession, College, Degree, Board, Religion, StudentCategory, 
                        DegreeType, PreviousExam, PreviousExamStream, Attachment, 
                        UniversitySpecialization, CollegeSpecMap, CandidateQualification, 
                        CandidateSpecialization, CandidateQualSpecMap, UnivSpecEligibleQualMap,
                        MainpageNavigation, WebPage, UserPageRight, AppearSubject, DegreeAppearSubjectMap,
                        CollegeCategory, City, CollegeType, Discipline, SMSCollegeDegreeMap, UnivDegreeSpecMap, PARegistrationMst, CandidateEducationTrn, CandidateDocument, PAFamilyAdditionalInfo)
from werkzeug.security import generate_password_hash, check_password_hash
from app.json_store import load_records, save_records, next_id
from app import db
from datetime import datetime
import os
from sqlalchemy import text, Table, MetaData, select, and_, delete as sa_delete, insert as sa_insert, func

main_bp = Blueprint('main', __name__)

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main_bp.root_path, '../static/img'), 'favicon.svg', mimetype='image/svg+xml')

@main_bp.route('/')
def index(): return redirect('/candidate_landing')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user_id'] = 'admin'
        return redirect('/dashboard')
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard(): return render_template('dashboard.html')

# ==========================================
# CANDIDATE PORTAL ROUTES
# ==========================================

@main_bp.route('/candidate_landing')
def candidate_landing():
    div1_links = MainpageNavigation.query.filter_by(active=True, div='1').order_by(MainpageNavigation.order_by).all()
    div2_links = MainpageNavigation.query.filter_by(active=True, div='2').order_by(MainpageNavigation.order_by).all()
    div3_links = MainpageNavigation.query.filter_by(active=True, div='3').order_by(MainpageNavigation.order_by).all()
    degree_types = DegreeType.query.filter_by(is_active=True).all()
    return render_template('candidate_landing.html', div1=div1_links, div2=div2_links, div3=div3_links, degree_types=degree_types)

@main_bp.route('/api/get_degrees/<int:dtype_id>')
def api_get_degrees(dtype_id):
    degrees = Degree.query.filter_by(fk_dtypeid=dtype_id, active=True).all()
    return jsonify([{'id': d.id, 'name': d.name} for d in degrees])

# ==========================================
# DEVELOPMENT PPP API SIMULATOR
# ==========================================
import time

@main_bp.route('/api/ppp_dev/get_members', methods=['POST'])
def ppp_dev_get_members():
    time.sleep(0.5) # Simulate network latency
    data = request.get_json()
    family_id = data.get('family_id', '').upper()
    
    if len(family_id) >= 5:
        # Simulate a successful API response from Haryana Govt
        return jsonify({
            'status': 'success',
            'members': [
                {'member_id': 'MEM001', 'name': 'Dashrath Kumar'},
                {'member_id': 'MEM002', 'name': 'Sneh Lata'},
                {'member_id': 'MEM003', 'name': 'Vanshika'}
            ]
        })
    return jsonify({'status': 'error', 'message': 'Invalid Family ID format according to Govt API.'}), 400

@main_bp.route('/api/ppp_dev/send_otp', methods=['POST'])
def ppp_dev_send_otp():
    time.sleep(0.5)
    data = request.get_json()
    member_id = data.get('member_id')
    if member_id:
        return jsonify({
            'status': 'success', 
            'message': 'OTP Sent to your registered mobile No. ******6397.',
            'txn_id': 'TXN123456789' # Simulating transaction ID
        })
    return jsonify({'status': 'error', 'message': 'Member ID missing'}), 400

@main_bp.route('/api/ppp_dev/verify_otp', methods=['POST'])
def ppp_dev_verify_otp():
    time.sleep(0.5)
    data = request.get_json()
    otp = data.get('otp')
    member_id = data.get('member_id')
    
    if otp == '123456': # Our dev testing OTP
        # Simulate the final payload we will get from the real API on Monday
        mock_api_payload = {
            'status': 'success',
            'data': {
                'name': 'Dashrath Kumar' if member_id == 'MEM001' else 'Vanshika',
                'f_name': 'HARI SINGH',
                'm_name': 'PARMESHRI',
                'dob': '1982-12-12',
                'gender': 'M',
                'mobile': '9729976397'
            }
        }
        return jsonify(mock_api_payload)
    return jsonify({'status': 'error', 'message': 'Invalid OTP entered.'}), 400


@main_bp.route('/candidate_instruction')
def candidate_instruction():
    return render_template('candidate_instruction.html')

@main_bp.route('/candidate_domicile_ppp', methods=['GET', 'POST'])
def candidate_domicile_ppp():
    if request.method == 'POST':
        # Capture mocked data from PPP verification and store in session for the next step
        session['ppp_data'] = {
            'dtype_id': request.form.get('dtype_id'),
            'degree_id': request.form.get('degree_id'),
            'name': request.form.get('name'),
            'family_id': request.form.get('family_id'),
            'mobile': request.form.get('mobile'),
            'f_name': request.form.get('f_name'),
            'm_name': request.form.get('m_name'),
            'dob': request.form.get('dob'),
            'gender': request.form.get('gender'),
            'domicile': request.form.get('domicile')
        }
        return redirect(url_for('main.candidate_register', dtype_id=request.form.get('dtype_id'), degree_id=request.form.get('degree_id')))
    return render_template('candidate_domicile_ppp.html')

@main_bp.route('/candidate_register', methods=['GET', 'POST'])
def candidate_register():
    dtype_id = request.args.get('dtype_id')
    degree_id = request.args.get('degree_id')
    ppp_data = session.get('ppp_data', {})

    if request.method == 'POST':
        # Form Data
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        dtype_id = request.form.get('dtype_id')
        degree_id = request.form.get('degree_id')
        
        # Extended fields from Personal Info
        f_name = request.form.get('f_name', '').upper()
        m_name = request.form.get('m_name', '').upper()
        dob_str = request.form.get('dob')
        gender = request.form.get('gender')
        familyId = request.form.get('familyId', '').upper()
        AdharNo = request.form.get('AdharNo')
        religion_id = request.form.get('religion_id')
        nationality = request.form.get('nationality')
        Parents_Mobileno = request.form.get('Parents_Mobileno')
        Marital_Status = request.form.get('Marital_Status')
        ChildStatus = request.form.get('ChildStatus')
        Blood_Group = request.form.get('Blood_Group')
        category_id = request.form.get('category_id')
        Resident = request.form.get('Resident')
        LDV = request.form.get('LDV')
        FatherGuargian = request.form.get('FatherGuargian')
        FatherOccupation = request.form.get('FatherOccupation')
        AnnualIncome = request.form.get('AnnualIncome')
        FF = request.form.get('FF')
        ESM = request.form.get('ESM')
        PH = request.form.get('PH')
        SportsQuota = request.form.get('SportsQuota')
        IsWard = request.form.get('IsWard')

        existing_user = PARegistrationMst.query.filter((PARegistrationMst.email == email) | (PARegistrationMst.mobileno == mobile)).first()
        if existing_user:
            flash('Email or Mobile already registered.', 'error')
            return redirect(url_for('main.candidate_register', dtype_id=dtype_id, degree_id=degree_id))

        active_session = AcademicSession.query.filter_by(is_active=True).first()
        if not active_session:
            active_session = AcademicSession.query.order_by(AcademicSession.id.desc()).first()
            
        max_regno_str = db.session.query(func.max(PARegistrationMst.regno)).scalar()
        if max_regno_str and max_regno_str.isdigit():
            new_regno = str(int(max_regno_str) + 1)
        else:
            new_regno = "100000001"

        new_user = PARegistrationMst(
            s_name=name,
            email=email,
            mobileno=mobile,
            pwd=generate_password_hash(password),
            fk_dtypeid=dtype_id,
            fk_degreeid=degree_id,
            fk_sessionid=active_session.id if active_session else 0,
            regno=new_regno,
            
            f_name=f_name,
            m_name=m_name,
            dob=datetime.strptime(dob_str, '%Y-%m-%d') if dob_str else datetime(1900, 1, 1),
            gender=gender,
            familyId=familyId,
            AdharNo=AdharNo,
            fk_religionid=int(religion_id) if religion_id else None,
            nationality=nationality,
            Parents_Mobileno=Parents_Mobileno,
            Marital_Status=Marital_Status,
            ChildStatus=ChildStatus,
            Blood_Group=Blood_Group,
            fk_stucatid_cast=int(category_id) if category_id else 1,
            Resident=Resident,
            LDV=LDV,
            FatherGuargian=FatherGuargian,
            FatherOccupation=FatherOccupation,
            AnnualIncome=AnnualIncome,
            FF=FF,
            ESM=ESM,
            PH=PH,
            SportsQuota=SportsQuota,
            IsWard=IsWard,
            fk_stypeid=1,
            c_address='N/A', c_district='N/A', c_pincode='000000',
            p_address='N/A', p_district='N/A', p_pincode='000000',
            step1=True
        )
        db.session.add(new_user)
        try:
            db.session.commit()
            session.pop('ppp_data', None) # Clear mock data
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('main.candidate_login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration: ' + str(e), 'error')

    selected_dtype = DegreeType.query.get(dtype_id) if dtype_id else None
    selected_degree = Degree.query.get(degree_id) if degree_id else None
    categories = StudentCategory.query.order_by(StudentCategory.order_no).all()
    religions = Religion.query.order_by(Religion.description).all()
    
    return render_template('candidate_register.html', dtype=selected_dtype, degree=selected_degree, 
                           ppp_data=ppp_data, categories=categories, religions=religions)

@main_bp.route('/candidate_login', methods=['GET', 'POST'])
def candidate_login():
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')

        user = PARegistrationMst.query.filter((PARegistrationMst.email == login_id) | (PARegistrationMst.mobileno == login_id)).first()

        if user and (check_password_hash(user.pwd, password) or user.pwd == password):
            session['candidate_id'] = user.id
            session['candidate_name'] = user.s_name
            flash('Logged in successfully', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('candidate_login.html')

@main_bp.route('/candidate_logout')
def candidate_logout():
    session.pop('candidate_id', None)
    session.pop('candidate_name', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.candidate_landing'))

@main_bp.route('/candidate_dashboard')
def candidate_dashboard():
    if 'candidate_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('main.candidate_login'))
    user = PARegistrationMst.query.get(session['candidate_id'])
    degree = Degree.query.get(user.fk_degreeid) if user.fk_degreeid else None
    add_info = PAFamilyAdditionalInfo.query.filter_by(fk_regid=user.id).first()
    has_additional_info = bool(add_info)
    return render_template('candidate_dashboard.html', user=user, degree=degree, has_additional_info=has_additional_info)

@main_bp.route('/candidate_address_info', methods=['GET', 'POST'])
def candidate_address_info():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    # Security check: Ensure step 1 is done
    if not user.step1:
        flash('Please complete Personal Information first.', 'error')
        return redirect(url_for('main.candidate_dashboard'))
    
    if request.method == 'POST':
        try:
            # Correspondence Address
            user.c_address = request.form.get('c_address', '').upper()
            user.C_Village = request.form.get('c_village', '').upper()
            user.c_district = request.form.get('c_district', '').upper()
            user.c_fk_stateid = int(request.form.get('c_fk_stateid')) if request.form.get('c_fk_stateid') else None
            user.c_pincode = request.form.get('c_pincode')

            # Permanent Address
            user.p_address = request.form.get('p_address', '').upper()
            user.P_Village = request.form.get('p_village', '').upper()
            user.p_district = request.form.get('p_district', '').upper()
            user.p_fk_stateid = int(request.form.get('p_fk_stateid')) if request.form.get('p_fk_stateid') else None
            user.p_pincode = request.form.get('p_pincode')
            
            # Handle Documents
            doc = CandidateDocument.query.filter_by(fk_regid=user.id).first()
            if not doc:
                doc = CandidateDocument(fk_regid=user.id)
                db.session.add(doc)
                
            def process_file(file_key, img_col, type_col, name_col):
                f = request.files.get(file_key)
                if f and f.filename:
                    file_bytes = f.read()
                    if len(file_bytes) > 0:
                        setattr(doc, img_col, file_bytes)
                        setattr(doc, type_col, f.content_type)
                        setattr(doc, name_col, f.filename)
            
            process_file('photo', 'imgattach_p', 'contenttype_p', 'filename_p')
            process_file('signature', 'imgattach_s', 'contenttype_s', 'filename_s')
            process_file('thumb', 'imgattach_t', 'contenttype_t', 'filename_t')
            
            # Mark step 2 as complete
            user.step2 = True
            db.session.commit()
            flash('Address and Photo Information saved successfully.', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving address: {str(e)}', 'error')
            
    doc = CandidateDocument.query.filter_by(fk_regid=user.id).first()
    return render_template('candidate_address_info.html', user=user, doc=doc)
@main_bp.route('/candidate_education_info', methods=['GET', 'POST'])
def candidate_education_info():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    if not user.step2:
        flash('Please complete Address Information first.', 'error')
        return redirect(url_for('main.candidate_dashboard'))

    # Retrieve existing educational details if any
    edu1 = CandidateEducationTrn.query.filter_by(fk_regid=user.id, fk_prevexamid=27).first() # Matric
    edu2 = CandidateEducationTrn.query.filter_by(fk_regid=user.id, fk_prevexamid=26).first() # 10+2
    
    if request.method == 'POST':
        try:
            # Helper to save or update an education record
            def save_edu(edu_obj, exam_id_val, prefix):
                if not edu_obj:
                    edu_obj = CandidateEducationTrn(fk_regid=user.id, fk_prevexamid=exam_id_val)
                    db.session.add(edu_obj)
                
                edu_obj.fk_yearid = request.form.get(f'year_{prefix}')
                edu_obj.fk_boardid = request.form.get(f'board_{prefix}')
                edu_obj.Rollno = request.form.get(f'rollno_{prefix}')
                edu_obj.grade = request.form.get(f'marks_type_{prefix}')
                edu_obj.maxmarks = request.form.get(f'max_marks_{prefix}')
                edu_obj.marks = request.form.get(f'obt_marks_{prefix}')
                edu_obj.coursedtl = request.form.get(f'subjects_{prefix}')
                
                # Specialization and Result Awaited for 10+2
                if prefix == '2':
                    spec_id = request.form.get(f'specialization_{prefix}')
                    if spec_id:
                        edu_obj.fk_pestreamid = int(spec_id)
                    res_await = request.form.get(f'result_await_{prefix}')
                    edu_obj.result_await = True if res_await == 'N' else False
                else:
                    edu_obj.result_await = False
                
                # Fix for SQL Server strict NOT NULL columns
                edu_obj.marks_act = request.form.get(f'obt_marks_{prefix}')
                edu_obj.isgrade = 0
                
                guilty_val = request.form.get('guilty', 'No')
                edu_obj.Guilty_Criminal = guilty_val
                if guilty_val == 'Yes':
                    edu_obj.Guilty_Criminal_Details = request.form.get('guilty_details')
                else:
                    edu_obj.Guilty_Criminal_Details = ''

            save_edu(edu1, 27, '1')
            save_edu(edu2, 26, '2')
            
            user.step3 = True
            db.session.commit()
            
            flash('Educational Qualification saved successfully.', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving educational qualification: {str(e)}', 'error')

    boards = Board.query.order_by(Board.description).all()
    
    # Only fetch specializations mapped to 10+2 (Qual ID 2)
    mapped_spec_ids = [m.fk_esp_id for m in CandidateQualSpecMap.query.filter_by(fk_eid=2).all()]
    specializations = CandidateSpecialization.query.filter(CandidateSpecialization.id.in_(mapped_spec_ids)).order_by(CandidateSpecialization.description).all()
    
    return render_template('candidate_education_info.html', user=user, edu1=edu1, edu2=edu2, boards=boards, specializations=specializations)


@main_bp.route('/candidate_additional_info', methods=['GET', 'POST'])
def candidate_additional_info():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))

    user = PARegistrationMst.query.get(session['candidate_id'])

    if not user.step3:
        flash('Please complete Educational Qualification first.', 'error')
        return redirect(url_for('main.candidate_dashboard'))

    add_info = PAFamilyAdditionalInfo.query.filter_by(fk_regid=user.id).first()

    if request.method == 'POST':
        try:
            if not add_info:
                add_info = PAFamilyAdditionalInfo(fk_regid=user.id)
                db.session.add(add_info)

            add_info.Ex_Student = request.form.get('is_ex_student')
            add_info.ReleventStatus = request.form.get('any_other_info')
            if add_info.ReleventStatus == 'Y':
                add_info.OtherInformation = request.form.get('other_info_text')
            else:
                add_info.OtherInformation = ''
            add_info.RuralOrUrban = request.form.get('rural_urban')

            db.session.commit()
            flash('Additional Information saved successfully.', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving information: {str(e)}', 'error')

    return render_template('candidate_additional_info.html', user=user, add_info=add_info)
@main_bp.route('/candidate_upload_docs', methods=['GET', 'POST'])
def candidate_upload_docs():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    add_info = PAFamilyAdditionalInfo.query.filter_by(fk_regid=user.id).first()
    if not add_info:
        flash('Please complete Additional Information first.', 'error')
        return redirect(url_for('main.candidate_dashboard'))

    doc = CandidateDocument.query.filter_by(fk_regid=user.id).first()
    
    if request.method == 'POST':
        try:
            if not doc:
                doc = CandidateDocument(fk_regid=user.id)
                db.session.add(doc)
            
            # Helper to process file
            def process_file(file_key, img_col, type_col, name_col):
                f = request.files.get(file_key)
                if f and f.filename:
                    # Validate size (simple check, could use f.seek to end and tell())
                    file_bytes = f.read()
                    if len(file_bytes) > 0:
                        setattr(doc, img_col, file_bytes)
                        setattr(doc, type_col, f.content_type)
                        setattr(doc, name_col, f.filename)
            
            process_file('photo', 'imgattach_p', 'contenttype_p', 'filename_p')
            process_file('signature', 'imgattach_s', 'contenttype_s', 'filename_s')
            process_file('thumb', 'imgattach_t', 'contenttype_t', 'filename_t')
            process_file('category_proof', 'imgattach_c', 'contenttype_c', 'filename_c')
            
            user.step4 = True
            db.session.commit()
            flash('Documents uploaded successfully.', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading documents: {str(e)}', 'error')

    return render_template('candidate_upload_docs.html', user=user, doc=doc)

@main_bp.route('/candidate_personal_info', methods=['GET', 'POST'])
def candidate_personal_info():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        try:
            # Basic Details
            dob_str = request.form.get('dob')
            if dob_str:
                user.dob = datetime.strptime(dob_str, '%Y-%m-%d')
            user.f_name = request.form.get('f_name', '').upper()
            user.m_name = request.form.get('m_name', '').upper()
            user.gender = request.form.get('gender')
            
            # Identity & Demographic
            user.AdharNo = request.form.get('AdharNo')
            rel_id = request.form.get('religion_id')
            if rel_id:
                user.fk_religionid = int(rel_id)
            user.nationality = request.form.get('nationality')
            user.Parents_Mobileno = request.form.get('Parents_Mobileno')
            user.Marital_Status = request.form.get('Marital_Status')
            user.ChildStatus = request.form.get('ChildStatus')
            user.Blood_Group = request.form.get('Blood_Group')
            
            # Category & Domicile
            cat_id = request.form.get('category_id')
            if cat_id:
                user.fk_stucatid_cast = int(cat_id)
            user.Resident = request.form.get('Resident')
            user.familyId = request.form.get('familyId', '').upper()
            
            # Handle category document
            doc = CandidateDocument.query.filter_by(fk_regid=user.id).first()
            if not doc:
                doc = CandidateDocument(fk_regid=user.id)
                db.session.add(doc)
            
            f = request.files.get('category_document')
            if f and f.filename:
                file_bytes = f.read()
                if len(file_bytes) > 0:
                    doc.imgattach_c = file_bytes
                    doc.contenttype_c = f.content_type
                    doc.filename_c = f.filename
            
            # Other Specifics
            user.LDV = request.form.get('LDV')
            user.FatherGuargian = request.form.get('FatherGuargian')
            user.FatherOccupation = request.form.get('FatherOccupation')
            user.AnnualIncome = request.form.get('AnnualIncome')
            user.FF = request.form.get('FF')
            user.ESM = request.form.get('ESM')
            user.PH = request.form.get('PH')
            user.SportsQuota = request.form.get('SportsQuota')
            user.IsWard = request.form.get('IsWard')
                
            # Mark step 1 as complete
            user.step1 = True
            db.session.commit()
            flash('Personal Information saved successfully.', 'success')
            return redirect(url_for('main.candidate_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving information: {str(e)}', 'error')
            
    categories = StudentCategory.query.order_by(StudentCategory.order_no).all()
    religions = Religion.query.order_by(Religion.description).all()
            
    return render_template('candidate_personal_info.html', user=user, categories=categories, religions=religions)


@main_bp.route('/candidate_declaration', methods=['GET', 'POST'])
def candidate_declaration():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    add_info = PAFamilyAdditionalInfo.query.filter_by(fk_regid=user.id).first()
    if not add_info:
        flash('Please complete Additional Information first.', 'error')
        return redirect(url_for('main.candidate_dashboard'))

    if request.method == 'POST':
        user.confirm_dec = True
        user.step5 = True
        
        # Calculate mock fee based on category (Standard Logic: 1500 for General, 375 for SC/BC/EWS in Haryana)
        if user.fk_stucatid_cast in [2, 3, 4] and user.Resident == '1': # Assuming 2,3,4 are reserved cats in Haryana
            user.totfee = 375.00
        else:
            user.totfee = 1500.00
            
        db.session.commit()
        return redirect(url_for('main.candidate_payment'))

    return render_template('candidate_declaration.html', user=user)

@main_bp.route('/candidate_payment', methods=['GET', 'POST'])
def candidate_payment():
    if 'candidate_id' not in session:
        flash('Please login to continue.', 'error')
        return redirect(url_for('main.candidate_login'))
        
    user = PARegistrationMst.query.get(session['candidate_id'])
    
    if not user.confirm_dec:
        return redirect(url_for('main.candidate_declaration'))

    if request.method == 'POST':
        # Simulate Payment Gateway Success
        user.IsPaymentSuccess = True
        db.session.commit()
        flash('Payment Successful! Your application is complete.', 'success')
        return redirect(url_for('main.candidate_dashboard'))

    return render_template('candidate_payment.html', user=user)

@main_bp.route('/api/get-colleges-by-degree/<int:degree_id>')
def get_colleges_by_degree(degree_id):
    # Mapping: SMS_CollegeDegreeBranchMap_Mst -> SMS_College_Mst -> PA_College_Mst
    mappings = SMSCollegeDegreeMap.query.filter_by(fk_degreeid=degree_id).all()
    colleges = []
    seen_ids = set()
    for m in mappings:
        if m.sms_college and m.sms_college.category:
            parent = m.sms_college.category
            if parent.id not in seen_ids:
                colleges.append({'id': parent.id, 'name': parent.name})
                seen_ids.add(parent.id)
    return jsonify(colleges)

@main_bp.route('/api/get-specializations-by-college/<int:college_id>')
def get_specializations_by_college(college_id):
    # Filter University Specializations by the PA_College_Mst ID
    specs = UniversitySpecialization.query.filter_by(fk_college_id=college_id).all()
    return jsonify([{'id': s.id, 'name': s.description} for s in specs])

def get_paginated_data(model, order_by_col):
    page = request.args.get('page', 1, type=int)
    return model.query.order_by(order_by_col).paginate(page=page, per_page=10)

def safe_all(query_fn, default=None):
    try:
        return query_fn()
    except Exception:
        return [] if default is None else default

def get_edit_record(records, edit_id):
    if not edit_id:
        return None
    for r in records:
        try:
            if int(r.get("id")) == int(edit_id):
                return r
        except Exception:
            continue
    return None

def upsert_record(store_key, record_id, payload):
    records = load_records(store_key)
    if record_id:
        for idx, r in enumerate(records):
            try:
                if int(r.get("id")) == int(record_id):
                    records[idx] = {"id": int(record_id), **payload}
                    save_records(store_key, sorted(records, key=lambda x: int(x.get("id", 0))))
                    return int(record_id), "Updated successfully!"
            except Exception:
                continue
    new_id = next_id(records)
    records.append({"id": new_id, **payload})
    save_records(store_key, sorted(records, key=lambda x: int(x.get("id", 0))))
    return new_id, "Added successfully!"

def delete_record(store_key, record_id):
    records = load_records(store_key)
    kept = []
    for r in records:
        try:
            if int(r.get("id")) != int(record_id):
                kept.append(r)
        except Exception:
            kept.append(r)
    save_records(store_key, sorted(kept, key=lambda x: int(x.get("id", 0))))

# 1. Academic Session Master
@main_bp.route('/academic-session', methods=['GET', 'POST'])
def academic_session():
    edit_id = request.args.get('edit_id')
    edit_session = AcademicSession.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        session_id = request.form.get('session_id')
        try:
            from_dt = datetime.strptime(request.form.get('from_date'), '%Y-%m-%d').date()
            to_dt = datetime.strptime(request.form.get('to_date'), '%Y-%m-%d').date()
            if session_id:
                obj = AcademicSession.query.get(session_id)
                obj.session_name = request.form.get('session_name'); obj.session_order = request.form.get('session_order')
                obj.from_date = from_dt; obj.to_date = to_dt; obj.remarks = request.form.get('remarks'); obj.is_active = request.form.get('is_active') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = AcademicSession(session_name=request.form.get('session_name'), session_order=request.form.get('session_order'), from_date=from_dt, to_date=to_dt, remarks=request.form.get('remarks'), is_active=request.form.get('is_active') == 'on' )
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.academic_session'))
    p = get_paginated_data(AcademicSession, AcademicSession.id); return render_template('academic_session.html', sessions=p.items, pagination=p, edit_session=edit_session)

# 2. Degree Type Master
@main_bp.route('/degree-type-master', methods=['GET', 'POST'])
def degree_type_master():
    edit_id = request.args.get('edit_id')
    edit_dt = DegreeType.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        dt_id = request.form.get('dt_id')
        try:
            if dt_id:
                obj = DegreeType.query.get(dt_id); obj.description = request.form.get('description'); obj.alias = request.form.get('alias'); obj.is_active = request.form.get('is_active') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = DegreeType(description=request.form.get('description'), alias=request.form.get('alias'), is_active=request.form.get('is_active') == 'on')
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.degree_type_master'))
    p = get_paginated_data(DegreeType, DegreeType.id); return render_template('degree_type_master.html', degree_types=p.items, pagination=p, edit_dt=edit_dt)

# 3. Degree Master
@main_bp.route('/degree-master', methods=['GET', 'POST'])
def degree_master():
    edit_id = request.args.get('edit_id')
    edit_degree = Degree.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        degree_id = request.form.get('degree_id')
        try:
            if degree_id:
                obj = Degree.query.get(degree_id); obj.name = request.form.get('name'); obj.code = request.form.get('code'); obj.fk_dtypeid = int(request.form.get('degree_type_id')) if request.form.get('degree_type_id') else None; obj.remarks = request.form.get('remarks'); obj.active = request.form.get('is_active') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = Degree(name=request.form.get('name'), code=request.form.get('code'), fk_dtypeid=int(request.form.get('degree_type_id')) if request.form.get('degree_type_id') else None, remarks=request.form.get('remarks'), active=request.form.get('is_active') == 'on')
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.degree_master'))
    p = get_paginated_data(Degree, Degree.id); degree_types = DegreeType.query.all(); return render_template('degree_master.html', degrees=p.items, pagination=p, degree_types=degree_types, edit_degree=edit_degree)

# 4. University Specialization Master
@main_bp.route('/university-specialization-master', methods=['GET', 'POST'])
def university_specialization_master():
    edit_id = request.args.get('edit_id')
    edit_spec = UniversitySpecialization.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        spec_id = request.form.get('spec_id')
        try:
            if spec_id:
                obj = UniversitySpecialization.query.get(spec_id); obj.description = request.form.get('description'); obj.code = request.form.get('code'); obj.fk_college_id = int(request.form.get('college_id')) if request.form.get('college_id') else None
                flash("Updated successfully!", "success")
            else:
                new_obj = UniversitySpecialization(description=request.form.get('description'), code=request.form.get('code'), fk_college_id=int(request.form.get('college_id')) if request.form.get('college_id') else None)
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.university_specialization_master'))
    p = get_paginated_data(UniversitySpecialization, UniversitySpecialization.id); colleges = CollegeCategory.query.all(); return render_template('university_specialization_master.html', specs=p.items, pagination=p, edit_spec=edit_spec, colleges=colleges)

@main_bp.route('/api/get-specializations/<int:degree_id>/<int:college_id>')
def get_specializations(degree_id, college_id):
    # Filter University Specializations by PA_College_Mst ID
    specs = UniversitySpecialization.query.filter_by(fk_college_id=college_id).all()
    return jsonify([{'id': s.id, 'name': s.description} for s in specs])

# 5. Map University Degree & Specialization
@main_bp.route('/map-university-degree-specialization', methods=['GET', 'POST'])
def map_university_degree_specialization():
    edit_id = request.args.get('edit_id')
    edit_obj = UnivDegreeSpecMap.query.get(edit_id) if edit_id else None
    
    edit_colleges = []
    edit_specs = []
    if edit_obj:
        # Load colleges tied to the degree (or just load all colleges if not explicitly tied)
        # Assuming fetchColleges API uses PA_College_Mst, let's pass all colleges or filtered ones
        edit_colleges = CollegeCategory.query.all()
        # Filter specs by college
        edit_specs = UniversitySpecialization.query.filter_by(fk_college_id=edit_obj.fk_collegeid).all()

    if request.method == 'POST':
        mid = request.form.get('mid')
        try:
            if mid:
                obj = UnivDegreeSpecMap.query.get(mid)
                obj.fk_degreeid = int(request.form.get('degree_id'))
                obj.fk_collegeid = int(request.form.get('college_id'))
                obj.fk_sid = int(request.form.get('spec_id'))
                obj.exam_type = request.form.get('exam_type')
                flash("Updated successfully!", "success")
            else:
                new_obj = UnivDegreeSpecMap(
                    fk_degreeid=int(request.form.get('degree_id')),
                    fk_collegeid=int(request.form.get('college_id')),
                    fk_sid=int(request.form.get('spec_id')),
                    exam_type=request.form.get('exam_type')
                )
                db.session.add(new_obj)
                flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e:
            flash(str(e), "error")
            db.session.rollback()
        return redirect(url_for('main.map_university_degree_specialization'))
        
    p = get_paginated_data(UnivDegreeSpecMap, UnivDegreeSpecMap.id)
    degrees = Degree.query.all()
    specs = UniversitySpecialization.query.all()
    colleges = CollegeCategory.query.all()
    exam_types = AnswerKeyExamType.query.all()
    
    # Create a mapping dictionary for the template
    exam_type_map = {et.exam_type_id: et.exam_type_desc for et in exam_types}
    
    return render_template('map_university_degree_specialization.html',
                           mappings=p.items,
                           pagination=p,
                           edit_obj=edit_obj,
                           degrees=degrees,
                           specs=specs,
                           colleges=colleges,
                           edit_colleges=edit_colleges if 'edit_colleges' in locals() else [],
                           edit_specs=edit_specs if 'edit_specs' in locals() else [],
                           exam_types=exam_types,
                           exam_type_map=exam_type_map)
# 17. Attachment Master
@main_bp.route('/attachment-master', methods=['GET', 'POST'])
def attachment_master():
    edit_id = request.args.get('edit_id'); edit_attachment = Attachment.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        att_id = request.form.get('att_id')
        try:
            if att_id:
                obj = Attachment.query.get(att_id); obj.fk_college_id = int(request.form.get('college_id')) if request.form.get('college_id') else None; obj.fk_degree_id = int(request.form.get('degree_id')) if request.form.get('degree_id') else None; obj.attachment_name = request.form.get('attachment_name'); obj.order_by = int(request.form.get('order_by')); obj.max_size_mb = float(request.form.get('max_size_mb')); obj.is_all_candidates = request.form.get('is_all') == 'on'; obj.is_mandatory = request.form.get('is_mandatory') == 'on'; obj.is_multiple = request.form.get('is_multiple') == 'on'; obj.is_active = request.form.get('is_active') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = Attachment(fk_college_id=int(request.form.get('college_id')) if request.form.get('college_id') else None, fk_degree_id=int(request.form.get('degree_id')) if request.form.get('degree_id') else None, attachment_name=request.form.get('attachment_name'), order_by=int(request.form.get('order_by')), max_size_mb=float(request.form.get('max_size_mb')), is_all_candidates=request.form.get('is_all') == 'on', is_mandatory=request.form.get('is_mandatory') == 'on', is_multiple=request.form.get('is_multiple') == 'on', is_active=request.form.get('is_active') == 'on')
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.attachment_master'))
    p = get_paginated_data(Attachment, Attachment.id); colleges = CollegeCategory.query.all(); degrees = Degree.query.all(); return render_template('attachment_master.html', attachments=p.items, pagination=p, colleges=colleges, degrees=degrees, edit_attachment=edit_attachment)

# 18. Manage Page Rights
@main_bp.route('/manage-page-rights', methods=['GET', 'POST'])
def manage_page_rights():
    p = get_paginated_data(UserPageRight, UserPageRight.id); return render_template('manage_page_rights.html', rights=p.items, pagination=p)

# 19. List of Notifications & Links
@main_bp.route('/notifications-links', methods=['GET', 'POST'])
def notifications_links():
    edit_id = request.args.get('edit_id'); edit_obj = MainpageNavigation.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        nid = request.form.get('nid')
        try:
            filename_val = None
            f = request.files.get('pdf_file')
            if f and f.filename:
                import os
                filename_val = f.filename
                upload_dir = os.path.join('app', 'static', 'uploads')
                if not os.path.exists(upload_dir): os.makedirs(upload_dir)
                f.save(os.path.join(upload_dir, filename_val))

            if nid:
                obj = MainpageNavigation.query.get(nid)
                obj.noticetext = request.form.get('name')
                obj.order_by = int(request.form.get('order') or 0)
                obj.div = request.form.get('div_type')
                obj.active = request.form.get('is_active') == 'on'
                obj.is_new = request.form.get('is_new') == 'on'
                if filename_val: obj.filename = filename_val
                flash("Updated!", "success")
            else:
                new_obj = MainpageNavigation(
                    noticetext=request.form.get('name'), 
                    order_by=int(request.form.get('order') or 0), 
                    div=request.form.get('div_type'),
                    active=request.form.get('is_active') == 'on', 
                    is_new=request.form.get('is_new') == 'on',
                    filename=filename_val
                )
                db.session.add(new_obj); flash("Added!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.notifications_links'))
    p = get_paginated_data(MainpageNavigation, MainpageNavigation.id); return render_template('notifications_links.html', links=p.items, pagination=p, edit_obj=edit_obj)

# 20. Discipline Master
@main_bp.route('/discipline-master', methods=['GET', 'POST'])
def discipline_master():
    edit_id = request.args.get('edit_id'); edit_obj = Discipline.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        mid = request.form.get('mid')
        try:
            if mid:
                obj = Discipline.query.get(mid); obj.name = request.form.get('name'); obj.code = request.form.get('code')
                flash("Updated successfully!", "success")
            else:
                new_obj = Discipline(name=request.form.get('name'), code=request.form.get('code')); db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.discipline_master'))
    p = get_paginated_data(Discipline, Discipline.id); return render_template('discipline_master.html', items=p.items, pagination=p, edit_obj=edit_obj)

# 21. Map Required Univ Spec & Cand Qual Spec (Eligible Mapping)
@main_bp.route('/map-required-spec-qual', methods=['GET', 'POST'])
def map_required_spec_qual():
    if request.method == 'POST':
        try:
            univ_map_id = int(request.form.get('univ_map_id')); cand_map_ids = request.form.getlist('cand_map_ids')
            for cm_id in cand_map_ids:
                exists = UnivSpecEligibleQualMap.query.filter_by(fk_map_id=univ_map_id, fk_esp_map_id=int(cm_id)).first()
                if not exists:
                    new_obj = UnivSpecEligibleQualMap(fk_map_id=univ_map_id, fk_esp_map_id=int(cm_id)); db.session.add(new_obj)
            db.session.commit(); flash("Mapped successfully!", "success")
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_univ_spec_eligible_candidate'))
    p = get_paginated_data(UnivSpecEligibleQualMap, UnivSpecEligibleQualMap.id); colleges = CollegeCategory.query.all(); univ_maps = UnivDegreeSpecMap.query.all(); cand_maps = CandidateQualSpecMap.query.all(); return render_template('map_univ_spec_eligible_candidate.html', mappings=p.items, pagination=p, colleges=colleges, univ_maps=univ_maps, cand_maps=cand_maps)



@main_bp.route('/delete-uds-map/<int:id>')
def delete_uds_map(id):
    obj = UnivDegreeSpecMap.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.map_university_degree_specialization'))

@main_bp.route('/candidate-qualification-master', methods=['GET', 'POST'])
def candidate_qualification_master():
    edit_id = request.args.get('edit_id')
    edit_obj = CandidateQualification.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        qid = request.form.get('qid')
        try:
            if qid:
                obj = CandidateQualification.query.get(qid); obj.description = request.form.get('description'); obj.code = request.form.get('code'); obj.active = request.form.get('is_active') == 'on'
                flash("Updated!", "success")
            else:
                new_obj = CandidateQualification(description=request.form.get('description'), code=request.form.get('code'), active=request.form.get('is_active') == 'on')
                db.session.add(new_obj); flash("Added!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.candidate_qualification_master'))
    p = get_paginated_data(CandidateQualification, CandidateQualification.id); return render_template('candidate_qualification_master.html', items=p.items, pagination=p, edit_obj=edit_obj)

@main_bp.route('/candidate-specialization-master', methods=['GET', 'POST'])
def candidate_specialization_master():
    edit_id = request.args.get('edit_id')
    edit_obj = CandidateSpecialization.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        sid = request.form.get('sid')
        try:
            if sid:
                obj = CandidateSpecialization.query.get(sid); obj.description = request.form.get('description')
                flash("Updated!", "success")
            else:
                new_obj = CandidateSpecialization(description=request.form.get('description'))
                db.session.add(new_obj); flash("Added!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.candidate_specialization_master'))
    p = get_paginated_data(CandidateSpecialization, CandidateSpecialization.id); return render_template('candidate_specialization_master.html', items=p.items, pagination=p, edit_obj=edit_obj)

@main_bp.route('/map-candidate-qualification-specialization', methods=['GET', 'POST'])
def map_candidate_qualification_specialization():
    if request.method == 'POST':
        try:
            new_obj = CandidateQualSpecMap(fk_esp_id=int(request.form.get('spec_id')), fk_eid=int(request.form.get('qual_id')))
            db.session.add(new_obj); db.session.commit(); flash("Mapped!", "success")
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_candidate_qualification_specialization'))
    p = get_paginated_data(CandidateQualSpecMap, CandidateQualSpecMap.id); quals = CandidateQualification.query.all(); specs = CandidateSpecialization.query.all(); return render_template('map_candidate_qualification_specialization.html', mappings=p.items, pagination=p, quals=quals, specs=specs)

@main_bp.route('/map-univ-spec-eligible-candidate', methods=['GET', 'POST'])
def map_univ_spec_eligible_candidate():
    # Filters
    f_college_id = request.args.get('f_college_id', type=int)
    f_map_id = request.args.get('f_map_id', type=int)

    if request.method == 'POST':
        try:
            univ_map_id = int(request.form.get('univ_map_id'))
            cand_map_ids = request.form.getlist('cand_map_ids')
            for cm_id in cand_map_ids:
                exists = UnivSpecEligibleQualMap.query.filter_by(fk_map_id=univ_map_id, fk_esp_map_id=int(cm_id)).first()
                if not exists:
                    new_obj = UnivSpecEligibleQualMap(fk_map_id=univ_map_id, fk_esp_map_id=int(cm_id))
                    db.session.add(new_obj)
            db.session.commit()
            flash("Mapped successfully!", "success")
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_univ_spec_eligible_candidate', 
                                f_college_id=request.form.get('college_id'),
                                f_map_id=request.form.get('univ_map_id')))
    
    page = request.args.get('page', 1, type=int)
    query = UnivSpecEligibleQualMap.query.join(UnivDegreeSpecMap, UnivSpecEligibleQualMap.fk_map_id == UnivDegreeSpecMap.id)
    
    if f_college_id:
        query = query.filter(UnivDegreeSpecMap.fk_collegeid == f_college_id)
    if f_map_id:
        query = query.filter(UnivSpecEligibleQualMap.fk_map_id == f_map_id)
        
    p = query.order_by(UnivDegreeSpecMap.id.desc()).paginate(page=page, per_page=10)
    
    colleges = CollegeCategory.query.all()
    
    # Univ Mappings filtered by college if selected
    univ_maps_query = UnivDegreeSpecMap.query
    if f_college_id:
        univ_maps_query = univ_maps_query.filter_by(fk_collegeid=f_college_id)
    univ_maps = univ_maps_query.all()
    
    # All candidate mappings for the checkbox list
    cand_maps = CandidateQualSpecMap.query.all()
    
    # Existing mappings for the selected f_map_id (to show as checked)
    existing_cand_map_ids = []
    if f_map_id:
        existing_cand_map_ids = [m.fk_esp_map_id for m in UnivSpecEligibleQualMap.query.filter_by(fk_map_id=f_map_id).all()]
    
    return render_template('map_univ_spec_eligible_candidate.html', 
                           mappings=p.items, pagination=p, 
                           colleges=colleges, univ_maps=univ_maps, cand_maps=cand_maps,
                           f_college_id=f_college_id, f_map_id=f_map_id,
                           existing_cand_map_ids=existing_cand_map_ids)

@main_bp.route('/delete-univ-spec-eligible-map/<int:id>')
def delete_univ_spec_eligible_map(id):
    obj = UnivSpecEligibleQualMap.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash("Deleted successfully!", "success")
    return redirect(url_for('main.map_univ_spec_eligible_candidate'))

@main_bp.route('/map-college-univ-spec-option', methods=['GET', 'POST'])
def map_college_univ_spec_option():
    edit_id = request.args.get('edit_id')
    edit_obj = CollegeSpecMap.query.get(edit_id) if edit_id else None

    # Filter parameters from GET request (automatic filtering)
    f_session_id = request.args.get('f_session_id', type=int)
    f_college_id = request.args.get('f_college_id', type=int)
    f_degree_id = request.args.get('f_degree_id', type=int)
    f_spec_id = request.args.get('f_spec_id', type=int)

    if request.method == 'POST':
        mid = request.form.get('mid')
        try:
            if mid:
                obj = CollegeSpecMap.query.get(mid)
                obj.fk_college_id = int(request.form.get('college_id'))
                obj.fk_degree_id = int(request.form.get('degree_id'))
                obj.fk_sid = int(request.form.get('spec_id'))
                obj.seat = int(request.form.get('seat'))
                obj.csir_seat = int(request.form.get('csir_seat')) if request.form.get('csir_seat') else 0
                obj.fk_sessionid = int(request.form.get('session_id'))
                flash("Updated successfully!", "success")
            else:
                new_obj = CollegeSpecMap(
                    fk_college_id=int(request.form.get('college_id')), 
                    fk_degree_id=int(request.form.get('degree_id')), 
                    fk_sid=int(request.form.get('spec_id')), 
                    seat=int(request.form.get('seat')), 
                    csir_seat=int(request.form.get('csir_seat')) if request.form.get('csir_seat') else 0, 
                    fk_sessionid=int(request.form.get('session_id'))
                )
                db.session.add(new_obj)
                flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_college_univ_spec_option', 
                                f_session_id=request.form.get('session_id'),
                                f_college_id=request.form.get('college_id'),
                                f_degree_id=request.form.get('degree_id'),
                                f_spec_id=request.form.get('spec_id')))
    
    page = request.args.get('page', 1, type=int)
    query = CollegeSpecMap.query.join(College, CollegeSpecMap.fk_college_id == College.id).join(Degree)
    
    # Apply filters if present
    if f_session_id: query = query.filter(CollegeSpecMap.fk_sessionid == f_session_id)
    if f_college_id: query = query.filter(CollegeSpecMap.fk_college_id == f_college_id)
    if f_degree_id: query = query.filter(CollegeSpecMap.fk_degree_id == f_degree_id)
    if f_spec_id: query = query.filter(CollegeSpecMap.fk_sid == f_spec_id)

    p = query.order_by(College.name, Degree.name).paginate(page=page, per_page=10)
    
    colleges = College.query.order_by(College.name).all() 
    degrees = Degree.query.filter_by(active=True).order_by(Degree.name).all()
    specs = UniversitySpecialization.query.order_by(UniversitySpecialization.description).all()
    sessions = AcademicSession.query.order_by(AcademicSession.session_name.desc()).all()
    
    return render_template('map_college_univ_spec_option.html', 
                           mappings=p.items, pagination=p, edit_obj=edit_obj, 
                           colleges=colleges, degrees=degrees, specs=specs, sessions=sessions,
                           f_session_id=f_session_id, f_college_id=f_college_id, 
                           f_degree_id=f_degree_id, f_spec_id=f_spec_id)

@main_bp.route('/delete-college-spec-option/<int:id>')
def delete_college_spec_option(id):
    obj = CollegeSpecMap.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash("Deleted successfully!", "success")
    return redirect(url_for('main.map_college_univ_spec_option'))

@main_bp.route('/college-master', methods=['GET', 'POST'])
def college_master():
    edit_id = request.args.get('edit_id')
    edit_college = College.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        college_id = request.form.get('college_id')
        try:
            if college_id:
                obj = College.query.get(college_id); obj.name = request.form.get('name'); obj.code = request.form.get('code'); obj.address = request.form.get('address'); obj.email = request.form.get('email'); obj.contact_person = request.form.get('contact_person'); obj.mobile = request.form.get('contact_number'); obj.remarks = request.form.get('remarks'); obj.city_id = int(request.form.get('city')) if request.form.get('city') else None; obj.type_id = int(request.form.get('type')) if request.form.get('type') else None; obj.website = request.form.get('website'); obj.parent_id = int(request.form.get('category')) if request.form.get('category') else None
                flash("Updated successfully!", "success")
            else:
                new_obj = College(name=request.form.get('name'), code=request.form.get('code'), address=request.form.get('address'), email=request.form.get('email'), contact_person=request.form.get('contact_person'), mobile=request.form.get('contact_number'), remarks=request.form.get('remarks'), city_id=int(request.form.get('city')) if request.form.get('city') else None, type_id=int(request.form.get('type')) if request.form.get('type') else None, website=request.form.get('website'), parent_id=int(request.form.get('category')) if request.form.get('category') else None)
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.college_master'))
    p = get_paginated_data(College, College.id); cities = City.query.order_by(City.name).all(); types = CollegeType.query.all(); categories = CollegeCategory.query.all(); return render_template('college_master.html', colleges=p.items, pagination=p, edit_college=edit_college, cities=cities, types=types, categories=categories)

@main_bp.route('/board-master', methods=['GET', 'POST'])
def board_master():
    edit_id = request.args.get('edit_id')
    edit_board = Board.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        board_id = request.form.get('board_id')
        try:
            bcat = int(request.form.get('board_cat_id') or 1)
            if board_id:
                obj = Board.query.get(board_id)
                obj.description = request.form.get('description')
                obj.fk_board_cat_id = bcat
                obj.is_approved = request.form.get('is_approved') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = Board(description=request.form.get('description'), fk_board_cat_id=bcat,
                                fk_country_id=17, is_approved=request.form.get('is_approved') == 'on')
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.board_master'))
    p = get_paginated_data(Board, Board.id)
    return render_template('board_master.html', boards=p.items, pagination=p, edit_board=edit_board)

@main_bp.route('/religion-master', methods=['GET', 'POST'])
def religion_master():
    edit_id = request.args.get('edit_id')
    edit_religion = Religion.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        religion_id = request.form.get('religion_id')
        try:
            if religion_id:
                obj = Religion.query.get(religion_id); obj.description = request.form.get('description')
                flash("Updated successfully!", "success")
            else:
                new_obj = Religion(description=request.form.get('description'))
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.religion_master'))
    p = get_paginated_data(Religion, Religion.id); return render_template('religion_master.html', religions=p.items, pagination=p, edit_religion=edit_religion)

@main_bp.route('/student-category-master', methods=['GET', 'POST'])
def student_category_master():
    edit_id = request.args.get('edit_id')
    edit_cat = StudentCategory.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        cat_id = request.form.get('cat_id')
        try:
            res_val = int(request.form.get('reservation') or 0)
            ord_val = int(request.form.get('order_no') or 0)
            dep_val = request.form.get('is_dependent') == 'on'
            if cat_id:
                obj = StudentCategory.query.get(cat_id)
                obj.description = request.form.get('description')
                obj.college_cat = request.form.get('college_cat')
                obj.reservation = res_val
                obj.order_no = ord_val
                obj.is_dependent = dep_val
                flash("Updated successfully!", "success")
            else:
                new_obj = StudentCategory(description=request.form.get('description'),
                                          college_cat=request.form.get('college_cat'),
                                          reservation=res_val, order_no=ord_val, is_dependent=dep_val)
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.student_category_master'))
    p = get_paginated_data(StudentCategory, StudentCategory.order_no)
    return render_template('student_category_master.html', categories=p.items, pagination=p, edit_cat=edit_cat)

@main_bp.route('/previous-exam-master', methods=['GET', 'POST'])
def previous_exam_master():
    edit_id = request.args.get('edit_id')
    edit_exam = PreviousExam.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        exam_id = request.form.get('exam_id')
        try:
            if exam_id:
                obj = PreviousExam.query.get(exam_id); obj.description = request.form.get('description'); obj.order_no = int(request.form.get('order_no'))
                flash("Updated successfully!", "success")
            else:
                new_obj = PreviousExam(description=request.form.get('description'), order_no=int(request.form.get('order_no')))
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.previous_exam_master'))
    p = get_paginated_data(PreviousExam, PreviousExam.order_no); return render_template('previous_exam_master.html', exams=p.items, pagination=p, edit_exam=edit_exam)

@main_bp.route('/previous-exam-stream-master', methods=['GET', 'POST'])
def previous_exam_stream_master():
    edit_id = request.args.get('edit_id')
    edit_stream = PreviousExamStream.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        stream_id = request.form.get('stream_id')
        try:
            if stream_id:
                obj = PreviousExamStream.query.get(stream_id); obj.description = request.form.get('description'); obj.fk_previous_exam_id = int(request.form.get('exam_id')); obj.fk_degreeid = int(request.form.get('degree_id')) if request.form.get('degree_id') else None
                flash("Updated successfully!", "success")
            else:
                new_obj = PreviousExamStream(description=request.form.get('description'), fk_previous_exam_id=int(request.form.get('exam_id')), fk_degreeid=int(request.form.get('degree_id')) if request.form.get('degree_id') else None)
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.previous_exam_stream_master'))
    p = get_paginated_data(PreviousExamStream, PreviousExamStream.id); exams = PreviousExam.query.all(); degrees = Degree.query.all(); return render_template('previous_exam_stream_master.html', streams=p.items, pagination=p, exams=exams, degrees=degrees, edit_stream=edit_stream)

# DELETE ROUTES
@main_bp.route('/delete-college/<int:id>')
def delete_college(id):
    obj = College.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.college_master'))

@main_bp.route('/delete-degree-type/<int:id>')
def delete_degree_type(id):
    obj = DegreeType.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.degree_type_master'))

@main_bp.route('/delete-degree/<int:id>')
def delete_degree(id):
    obj = Degree.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.degree_master'))

@main_bp.route('/delete-specialization/<int:id>')
def delete_specialization(id):
    obj = UniversitySpecialization.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.university_specialization_master'))

@main_bp.route('/delete-candidate-qualification/<int:id>')
def delete_candidate_qualification(id):
    obj = CandidateQualification.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.candidate_qualification_master'))

@main_bp.route('/delete-candidate-specialization/<int:id>')
def delete_candidate_specialization(id):
    obj = CandidateSpecialization.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.candidate_specialization_master'))

@main_bp.route('/delete-map-cand-qual-spec/<int:id>')
def delete_map_cand_qual_spec(id):
    obj = CandidateQualSpecMap.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash("Deleted successfully!", "success")
    return redirect(url_for('main.map_candidate_qualification_specialization'))

@main_bp.route('/delete-notification-link/<int:id>')
def delete_notification_link(id):
    obj = MainpageNavigation.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.notifications_links'))

@main_bp.route('/delete-board/<int:id>')
def delete_board(id):
    obj = Board.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.board_master'))

@main_bp.route('/delete-religion/<int:id>')
def delete_religion(id):
    obj = Religion.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.religion_master'))

@main_bp.route('/delete-student-category/<int:id>')
def delete_student_category(id):
    obj = StudentCategory.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.student_category_master'))

@main_bp.route('/delete-previous-exam/<int:id>')
def delete_previous_exam(id):
    obj = PreviousExam.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.previous_exam_master'))

@main_bp.route('/delete-previous-exam-stream/<int:id>')
def delete_previous_exam_stream(id):
    obj = PreviousExamStream.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.previous_exam_stream_master'))

@main_bp.route('/delete-attachment/<int:id>')
def delete_attachment(id):
    obj = Attachment.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.attachment_master'))

@main_bp.route('/delete-discipline/<int:id>')
def delete_discipline(id):
    obj = Discipline.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.discipline_master'))

@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))
