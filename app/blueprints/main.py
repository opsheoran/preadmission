from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from app.models import (AcademicSession, College, Degree, Board, Religion, StudentCategory, 
                        DegreeType, PreviousExam, PreviousExamStream, Attachment, 
                        UniversitySpecialization, CollegeSpecMap, CandidateQualification, 
                        CandidateSpecialization, CandidateQualSpecMap, UnivSpecEligibleQualMap,
                        NotificationLink, WebPage, UserPageRight, AppearSubject, DegreeAppearSubjectMap,
                        CollegeCategory, City, CollegeType, Discipline, SMSCollegeDegreeMap, UnivDegreeSpecMap)
from app import db
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main_bp.root_path, '../static/img'), 'favicon.svg', mimetype='image/svg+xml')

@main_bp.route('/')
def index(): return redirect('/login')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': return redirect('/dashboard')
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard(): return render_template('dashboard.html')

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

# ... (Academic Session, Degree Type, Degree Master routes remain as previously updated)

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
                flash("Mapped successfully!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_university_degree_specialization'))
    
    page = request.args.get('page', 1, type=int)
    p = UnivDegreeSpecMap.query.join(Degree).order_by(Degree.name).paginate(page=page, per_page=10)
    degrees = Degree.query.all()
    # For Edit mode, we might need colleges and specs pre-loaded, but JS handles it on change.
    # However, for the initial edit view, we need them for the degree/college selected.
    colleges = []
    specs = []
    if edit_obj:
        # Get colleges for the edit_obj's degree
        mappings = SMSCollegeDegreeMap.query.filter_by(fk_degreeid=edit_obj.fk_degreeid).all()
        seen_ids = set()
        for m in mappings:
            if m.sms_college and m.sms_college.category:
                parent = m.sms_college.category
                if parent.id not in seen_ids:
                    colleges.append(parent)
                    seen_ids.add(parent.id)
        # Get specs for the edit_obj's college
        specs = UniversitySpecialization.query.filter_by(fk_college_id=edit_obj.fk_collegeid).all()

    return render_template('map_university_degree_specialization.html', 
                           mappings=p.items, pagination=p, degrees=degrees, 
                           edit_obj=edit_obj, edit_colleges=colleges, edit_specs=specs)

@main_bp.route('/delete-uds-map/<int:id>')
def delete_uds_map(id):
    obj = UnivDegreeSpecMap.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
    return redirect(url_for('main.map_university_degree_specialization'))

# 6. Candidate Education Qualification Master
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

# 7. Candidate Education Specialization Master
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

# 8. Map Candidate Qualification & Specialization
@main_bp.route('/map-candidate-qualification-specialization', methods=['GET', 'POST'])
def map_candidate_qualification_specialization():
    if request.method == 'POST':
        try:
            new_obj = CandidateQualSpecMap(fk_esp_id=int(request.form.get('spec_id')), fk_eid=int(request.form.get('qual_id')))
            db.session.add(new_obj); db.session.commit(); flash("Mapped!", "success")
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.map_candidate_qualification_specialization'))
    p = get_paginated_data(CandidateQualSpecMap, CandidateQualSpecMap.id); quals = CandidateQualification.query.all(); specs = CandidateSpecialization.query.all(); return render_template('map_candidate_qualification_specialization.html', mappings=p.items, pagination=p, quals=quals, specs=specs)

# 9. Map Univ. Spec. with Eligible Candidate Degree
# 9. Map Univ. Spec. & Eligible Candidate Qual.
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

# 10. Map College & Univ. Spec. (Option Form)
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

# 11. College Master
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

# 12. Board Master
@main_bp.route('/board-master', methods=['GET', 'POST'])
def board_master():
    edit_id = request.args.get('edit_id')
    edit_board = Board.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        board_id = request.form.get('board_id')
        try:
            if board_id:
                obj = Board.query.get(board_id); obj.description = request.form.get('description'); obj.is_approved = request.form.get('is_approved') == 'on'
                flash("Updated successfully!", "success")
            else:
                new_obj = Board(description=request.form.get('description'), is_approved=request.form.get('is_approved') == 'on')
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.board_master'))
    p = get_paginated_data(Board, Board.id); return render_template('board_master.html', boards=p.items, pagination=p, edit_board=edit_board)

# 13. Religion Master
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

# 14. Student Category Master
@main_bp.route('/student-category-master', methods=['GET', 'POST'])
def student_category_master():
    edit_id = request.args.get('edit_id')
    edit_cat = StudentCategory.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        cat_id = request.form.get('cat_id')
        try:
            if cat_id:
                obj = StudentCategory.query.get(cat_id); obj.description = request.form.get('description'); obj.college_cat = request.form.get('college_cat'); obj.order_no = int(request.form.get('order_no')) if request.form.get('order_no') else None
                flash("Updated successfully!", "success")
            else:
                new_obj = StudentCategory(description=request.form.get('description'), college_cat=request.form.get('college_cat'), order_no=int(request.form.get('order_no')) if request.form.get('order_no') else None)
                db.session.add(new_obj); flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(f"Error: {e}", "error"); db.session.rollback()
        return redirect(url_for('main.student_category_master'))
    p = get_paginated_data(StudentCategory, StudentCategory.order_no); return render_template('student_category_master.html', categories=p.items, pagination=p, edit_cat=edit_cat)

# 15. Previous Exam Master
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

# 16. Previous Exam Stream Master
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

# 17. Attachment Master
@main_bp.route('/attachment-master', methods=['GET', 'POST'])
def attachment_master():
    edit_id = request.args.get('edit_id')
    edit_attachment = Attachment.query.get(edit_id) if edit_id else None
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
    edit_id = request.args.get('edit_id')
    edit_obj = NotificationLink.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        nid = request.form.get('nid')
        try:
            if nid:
                obj = NotificationLink.query.get(nid); obj.name = request.form.get('name'); obj.order = int(request.form.get('order')); obj.fk_degreeid = int(request.form.get('degree_id')) if request.form.get('degree_id') else None; obj.fk_sessionid = int(request.form.get('session_id')) if request.form.get('session_id') else None; obj.active = request.form.get('is_active') == 'on'
                flash("Updated!", "success")
            else:
                new_obj = NotificationLink(name=request.form.get('name'), order=int(request.form.get('order')), fk_degreeid=int(request.form.get('degree_id')) if request.form.get('degree_id') else None, fk_sessionid=int(request.form.get('session_id')) if request.form.get('session_id') else None, active=request.form.get('is_active') == 'on')
                db.session.add(new_obj); flash("Added!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.notifications_links'))
    p = get_paginated_data(NotificationLink, NotificationLink.id); degrees = Degree.query.all(); sessions = AcademicSession.query.all(); return render_template('notifications_links.html', links=p.items, pagination=p, edit_obj=edit_obj, degrees=degrees, sessions=sessions)

# 20. Discipline Master
@main_bp.route('/discipline-master', methods=['GET', 'POST'])
def discipline_master():
    edit_id = request.args.get('edit_id')
    edit_obj = Discipline.query.get(edit_id) if edit_id else None
    if request.method == 'POST':
        mid = request.form.get('mid')
        try:
            if mid:
                obj = Discipline.query.get(mid)
                obj.name = request.form.get('name')
                obj.code = request.form.get('code')
                flash("Updated successfully!", "success")
            else:
                new_obj = Discipline(name=request.form.get('name'), code=request.form.get('code'))
                db.session.add(new_obj)
                flash("Added successfully!", "success")
            db.session.commit()
        except Exception as e: flash(str(e), "error"); db.session.rollback()
        return redirect(url_for('main.discipline_master'))
    p = get_paginated_data(Discipline, Discipline.id)
    return render_template('discipline_master.html', items=p.items, pagination=p, edit_obj=edit_obj)

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

@main_bp.route('/delete-notification-link/<int:id>')
def delete_notification_link(id):
    obj = NotificationLink.query.get_or_404(id); db.session.delete(obj); db.session.commit(); flash("Deleted!", "success")
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
