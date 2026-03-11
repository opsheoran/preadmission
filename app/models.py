from app import db

class AcademicSession(db.Model):
    __tablename__ = 'LUP_AcademicSession_Mst'
    id = db.Column('pk_sessionid', db.Integer, primary_key=True)
    session_name = db.Column('description', db.String(25), nullable=False)
    session_order = db.Column('orderno', db.String(5), nullable=False)
    from_date = db.Column('fromdate', db.Date, nullable=False)
    to_date = db.Column('todate', db.Date, nullable=False)
    remarks = db.Column(db.String(100))
    is_active = db.Column('active', db.Boolean, default=True)

class CollegeCategory(db.Model):
    __tablename__ = 'PA_College_Mst'
    id = db.Column('Pk_CollegeID', db.Integer, primary_key=True)
    name = db.Column('CollegeName', db.String(100), nullable=False)

class CollegeType(db.Model):
    __tablename__ = 'SMS_CollegeTpye_Mst'
    id = db.Column('pk_collegetypeid', db.Integer, primary_key=True)
    description = db.Column('collegypedesc', db.String(50), nullable=False)

class City(db.Model):
    __tablename__ = 'District_Mst'
    id = db.Column('pk_DistrictId', db.Integer, primary_key=True)
    name = db.Column('DistrictName', db.String(50), nullable=False)

class College(db.Model):
    __tablename__ = 'SMS_College_Mst'
    id = db.Column('pk_collegeid', db.Integer, primary_key=True)
    name = db.Column('collegename', db.String(100), nullable=False)
    code = db.Column('collegecode', db.String(10), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    email = db.Column('emailid', db.String(50), nullable=False)
    contact_person = db.Column('contactperson', db.String(50))
    mobile = db.Column('contactno', db.String(20))
    remarks = db.Column('remarks', db.String(250))
    city_id = db.Column('fk_cityid', db.Integer, db.ForeignKey('District_Mst.pk_DistrictId'))
    type_id = db.Column('fk_collegetypeid', db.Integer, db.ForeignKey('SMS_CollegeTpye_Mst.pk_collegetypeid'))
    website = db.Column('websiteaddress', db.String(50))
    parent_id = db.Column('fk_Parentcollege_mst', db.Integer, db.ForeignKey('PA_College_Mst.Pk_CollegeID'))

    city = db.relationship('City', backref=db.backref('colleges', lazy=True))
    college_type = db.relationship('CollegeType', backref=db.backref('colleges', lazy=True))
    category = db.relationship('CollegeCategory', backref=db.backref('colleges', lazy=True), foreign_keys=[parent_id])

class CandidateEducationTrn(db.Model):
    __tablename__ = 'PA_Registration_CollegeApply_PreExam_Trn'
    id = db.Column('pk_trnid', db.BigInteger, primary_key=True)
    fk_regid = db.Column(db.BigInteger, db.ForeignKey('PA_Registration_Mst.pk_regid'))
    fk_prevexamid = db.Column(db.Integer, db.ForeignKey('PA_PreviousExam_Mst.Pk_PrevExamId'))
    fk_pestreamid = db.Column(db.Integer, db.ForeignKey('PA_Education_Specialization_Mst.Pk_ESP_Id'))
    fk_yearid = db.Column(db.Integer)
    fk_boardid = db.Column(db.Integer, db.ForeignKey('PA_Board_Mst.Pk_BoardId'))
    univboard = db.Column(db.String(255))
    coursedtl = db.Column(db.String(255))
    otherdtl = db.Column(db.String(255))
    isgrade = db.Column(db.Integer)
    grade = db.Column(db.String(50))
    maxmarks = db.Column(db.Float)
    marks = db.Column(db.Float)
    marks_act = db.Column(db.Numeric(18, 2))
    result_await = db.Column(db.Boolean)
    Rollno = db.Column(db.String(50))
    Guilty_Criminal = db.Column(db.String(5))
    Guilty_Criminal_Details = db.Column(db.String(250))
    
    registration = db.relationship('PARegistrationMst', backref=db.backref('education_details', lazy=True, cascade='all, delete-orphan'))
    previous_exam = db.relationship('PreviousExam', backref=db.backref('candidate_records', lazy=True))
    board = db.relationship('Board', backref=db.backref('candidate_records', lazy=True))

class CandidateDocument(db.Model):
    __tablename__ = 'PA_Registration_Document'
    fk_regid = db.Column(db.BigInteger, db.ForeignKey('PA_Registration_Mst.pk_regid'), primary_key=True)
    imgattach_p = db.Column(db.LargeBinary)
    contenttype_p = db.Column(db.String(200))
    filename_p = db.Column(db.String(255))
    imgattach_s = db.Column(db.LargeBinary)
    contenttype_s = db.Column(db.String(200))
    filename_s = db.Column(db.String(255))
    attachment = db.Column(db.LargeBinary)
    contenttype = db.Column(db.String(200))
    filename = db.Column(db.String(255))
    imgattach_t = db.Column(db.LargeBinary)
    contenttype_t = db.Column(db.String(200))
    filename_t = db.Column(db.String(255))
    imgattach_c = db.Column(db.LargeBinary)
    contenttype_c = db.Column(db.String(250))
    filename_c = db.Column(db.String(250))
    
    registration = db.relationship('PARegistrationMst', backref=db.backref('documents', uselist=False, lazy=True, cascade='all, delete-orphan'))

class DegreeType(db.Model):
    __tablename__ = 'ACD_DegreeType_Mst'
    id = db.Column('pk_dtypeid', db.Integer, primary_key=True)
    description = db.Column(db.String(25), nullable=False)
    alias = db.Column(db.String(2))
    is_active = db.Column('active', db.Boolean, default=True)

class Degree(db.Model):
    __tablename__ = 'ACD_Degree_Mst'
    id = db.Column('pk_degreeid', db.Integer, primary_key=True)
    name = db.Column('description', db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    fk_dtypeid = db.Column(db.Integer, db.ForeignKey('ACD_DegreeType_Mst.pk_dtypeid'))
    coursetype = db.Column(db.String(1))
    active = db.Column(db.Boolean, default=True)
    remarks = db.Column(db.String(255))
    is_entrance_exam = db.Column('IsEntranceExam', db.Boolean)
    degree_type = db.relationship('DegreeType', backref=db.backref('degrees', lazy=True))

class SMSCollegeDegreeMap(db.Model):
    __tablename__ = 'SMS_CollegeDegreeBranchMap_Mst'
    id = db.Column('PK_Coldgbrid', db.Integer, primary_key=True)
    fk_collegeid = db.Column('fk_CollegeId', db.Integer, db.ForeignKey('SMS_College_Mst.pk_collegeid'))
    fk_degreeid = db.Column('fk_Degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    sms_college = db.relationship('College', backref=db.backref('branch_mappings', lazy=True))

class UniversitySpecialization(db.Model):
    __tablename__ = 'PA_Specialization_mst'
    id = db.Column('Pk_SID', db.Integer, primary_key=True)
    description = db.Column('Specialization', db.String(100), nullable=False)
    fk_college_id = db.Column('Fk_CollegeID', db.Integer, db.ForeignKey('PA_College_Mst.Pk_CollegeID'))
    code = db.Column('Code', db.String(10))
    college_category = db.relationship('CollegeCategory', backref=db.backref('univ_specializations', lazy=True))

class UnivSpecDegreeMap(db.Model):
    __tablename__ = 'PA_SpecDegree_Map'
    id = db.Column('Pk_Id', db.Integer, primary_key=True)
    fk_sid = db.Column('Fk_SID', db.Integer, db.ForeignKey('PA_Specialization_mst.Pk_SID'))
    fk_degreeid = db.Column('Fk_degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    specialization = db.relationship('UniversitySpecialization', backref=db.backref('degree_mappings', lazy=True))

class UnivDegreeSpecMap(db.Model):
    __tablename__ = 'PA_Degree_SpecializationMapping_mst'
    id = db.Column('Pk_MapId', db.Integer, primary_key=True)
    fk_sid = db.Column('fk_SID', db.Integer, db.ForeignKey('PA_Specialization_mst.Pk_SID'))
    fk_degreeid = db.Column('fk_DegreeId', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    fk_collegeid = db.Column('fk_CollegeId', db.Integer, db.ForeignKey('PA_College_Mst.Pk_CollegeID'))
    exam_type = db.Column('ExamType', db.String(50))
    specialization = db.relationship('UniversitySpecialization', backref=db.backref('univ_mappings', lazy=True))
    degree = db.relationship('Degree', backref=db.backref('univ_spec_mappings', lazy=True))
    college = db.relationship('CollegeCategory', backref=db.backref('univ_spec_mappings', lazy=True))

class Board(db.Model):
    __tablename__ = 'PA_Board_Mst'
    id = db.Column('Pk_BoardId', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(200), nullable=False)
    fk_board_cat_id = db.Column('Fk_BoardCatId', db.SmallInteger, nullable=False, default=1)
    fk_country_id = db.Column('Fk_CountryId', db.Integer, nullable=False, default=17)
    is_approved = db.Column('IsApproved', db.Boolean, default=True)

class Religion(db.Model):
    __tablename__ = 'Religion_Mst'
    id = db.Column('pk_religionid', db.Integer, primary_key=True)
    description = db.Column('religiontype', db.String(100), nullable=False)
    fk_ins_user = db.Column('fk_insUserID', db.String(10), nullable=False, default='1')
    fk_upd_user = db.Column('fk_updUserID', db.String(10), nullable=False, default='1')
    fk_ins_date = db.Column('fk_insDateID', db.String(10), nullable=False, default='1')
    fk_upd_date = db.Column('fk_updDateID', db.String(10), nullable=False, default='1')

class Discipline(db.Model):
    __tablename__ = 'PA_Disciple_Mst'
    id = db.Column('pk_id', db.Integer, primary_key=True)
    name = db.Column('Discipline_Name', db.String(100), nullable=False)
    code = db.Column('Discipline_Code', db.String(50))

class StudentCategory(db.Model):
    __tablename__ = 'PA_StudentCategory_Mst'
    id = db.Column('Pk_StuCatId', db.Integer, primary_key=True)
    college_cat = db.Column('CollegeCat', db.String(1))
    description = db.Column('Description', db.String(100), nullable=False)
    reservation = db.Column('Reservation', db.Integer, nullable=False, default=0)
    order_no = db.Column('OrderNo', db.Integer, nullable=False, default=0)
    is_dependent = db.Column('IsDependent', db.Boolean, nullable=False, default=False)

class PreviousExam(db.Model):
    __tablename__ = 'PA_PreviousExam_Mst'
    id = db.Column('Pk_PrevExamId', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(80), nullable=False)
    order_no = db.Column('OrderNo', db.Integer, nullable=False)

class PreviousExamStream(db.Model):
    __tablename__ = 'PA_PrevExam_Stream_Mst'
    id = db.Column('Pk_PEStreamId', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100), nullable=False)
    fk_previous_exam_id = db.Column('Fk_PrevExamId', db.Integer, db.ForeignKey('PA_PreviousExam_Mst.Pk_PrevExamId'), nullable=False)
    fk_degreeid = db.Column('fk_degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    exam = db.relationship('PreviousExam', backref=db.backref('streams', lazy=True))
    degree = db.relationship('Degree', backref=db.backref('exam_streams', lazy=True))

class Attachment(db.Model):
    __tablename__ = 'PA_Attachment_Mst'
    id = db.Column('Pk_attachmentId', db.Integer, primary_key=True)
    fk_college_id = db.Column('fk_CollegeID', db.Integer, db.ForeignKey('SMS_College_Mst.pk_collegeid'))
    fk_degree_id = db.Column('fk_degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    attachment_name = db.Column('AttachmentType', db.String(255), nullable=False)
    order_by = db.Column('OrderBy', db.Integer, nullable=False)
    max_size_mb = db.Column('MaxSizeInMB', db.Numeric(10, 2), nullable=False)
    is_all_candidates = db.Column('IsAll', db.Boolean, default=False)
    is_mandatory = db.Column('IsMandatory', db.Boolean, default=False)
    is_multiple = db.Column('IsMultiple', db.Boolean, default=False)
    is_active = db.Column('IsActive', db.Boolean, default=True)
    college = db.relationship('College', backref=db.backref('attachments', lazy=True))
    degree = db.relationship('Degree', backref=db.backref('attachments', lazy=True))

class CollegeSpecMap(db.Model):
    __tablename__ = 'PA_College_Spec_Map'
    id = db.Column('Pk_MapID', db.Integer, primary_key=True)
    fk_college_id = db.Column('fk_collegeID', db.Integer, db.ForeignKey('SMS_College_Mst.pk_collegeid'))
    fk_degree_id = db.Column('fk_degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'), nullable=False)
    fk_sid = db.Column('fk_sid', db.Integer, db.ForeignKey('PA_Specialization_mst.Pk_SID'), nullable=False)
    seat = db.Column(db.Integer)
    csir_seat = db.Column('CSIRSeat', db.Integer)
    fk_sessionid = db.Column('fk_sessionID', db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))
    college = db.relationship('College', backref=db.backref('spec_mappings', lazy=True))
    degree = db.relationship('Degree', backref=db.backref('spec_mappings', lazy=True))
    specialization = db.relationship('UniversitySpecialization', backref=db.backref('spec_mappings', lazy=True))
    session = db.relationship('AcademicSession', backref=db.backref('spec_mappings', lazy=True))

class CandidateQualification(db.Model):
    __tablename__ = 'ACD_EducationQualification_Mst'
    id = db.Column('Pk_EID', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100), nullable=False)
    code = db.Column(db.String(10))
    active = db.Column(db.Boolean, default=True)

class CandidateSpecialization(db.Model):
    __tablename__ = 'PA_Education_Specialization_Mst'
    id = db.Column('Pk_ESP_Id', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100), nullable=False)

class AppearSubject(db.Model):
    __tablename__ = 'PA_AppearSubject_Mst'
    id = db.Column('pk_aprsubid', db.Integer, primary_key=True)
    name = db.Column('subname', db.String(100), nullable=False)
    dtype = db.Column(db.String(50))

class DegreeAppearSubjectMap(db.Model):
    __tablename__ = 'PA_AppearSubjectDegree_Map'
    fk_degree_id = db.Column('fk_degreeid', db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'), primary_key=True)
    fk_aprsub_id = db.Column('fk_aprsubid', db.Integer, db.ForeignKey('PA_AppearSubject_Mst.pk_aprsubid'), primary_key=True)
    degree = db.relationship('Degree', backref=db.backref('appear_subject_maps', lazy=True))
    appear_subject = db.relationship('AppearSubject', backref=db.backref('degree_maps', lazy=True))

class CandidateQualSpecMap(db.Model):
    __tablename__ = 'PA_Education_Specialization_Mapping'
    id = db.Column('Pk_ESP_Map_Id', db.Integer, primary_key=True)
    fk_esp_id = db.Column('Fk_ESP_Id', db.Integer, db.ForeignKey('PA_Education_Specialization_Mst.Pk_ESP_Id'))
    fk_eid = db.Column('Fk_EID', db.Integer, db.ForeignKey('ACD_EducationQualification_Mst.Pk_EID'))
    specialization = db.relationship('CandidateSpecialization', backref=db.backref('mappings', lazy=True))
    qualification = db.relationship('CandidateQualification', backref=db.backref('mappings', lazy=True))

class UnivSpecEligibleQualMap(db.Model):
    __tablename__ = 'PA_Spec_Eligible_Criteria_Mapping'
    id = db.Column('Pk_ID', db.Integer, primary_key=True)
    fk_map_id = db.Column('Fk_MapId', db.Integer, db.ForeignKey('PA_Degree_SpecializationMapping_mst.Pk_MapId'))
    fk_esp_map_id = db.Column('Fk_ESP_Map_Id', db.Integer, db.ForeignKey('PA_Education_Specialization_Mapping.Pk_ESP_Map_Id'))
    college_spec_map = db.relationship('UnivDegreeSpecMap', backref=db.backref('eligible_criteria', lazy=True))
    cand_qual_spec_map = db.relationship('CandidateQualSpecMap', backref=db.backref('eligible_criteria', lazy=True))

class NotificationLink(db.Model):
    __tablename__ = 'PA_Link_Configuration_Mst'
    id = db.Column('pk_LinkId', db.Integer, primary_key=True)
    name = db.Column('Link_Name', db.String(255), nullable=False)
    order = db.Column('Order', db.Integer)
    fk_degreeid = db.Column(db.Integer, db.ForeignKey('ACD_Degree_Mst.pk_degreeid'))
    fk_sessionid = db.Column(db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))
    filename = db.Column('Filename', db.String(255))
    active = db.Column('Active', db.Boolean, default=True)
    degree = db.relationship('Degree', backref=db.backref('notifications', lazy=True))
    session = db.relationship('AcademicSession', backref=db.backref('notifications', lazy=True))

class WebPage(db.Model):
    __tablename__ = 'UM_WebPage_Mst'
    id = db.Column('pk_webpageId', db.Integer, primary_key=True)
    caption = db.Column('menucaption', db.String(100))
    name = db.Column('webpagename', db.String(100))

class UserPageRight(db.Model):
    __tablename__ = 'UM_UserPageRights'
    id = db.Column('pk_pagerightid', db.Integer, primary_key=True)
    fk_webpageid = db.Column('fk_webpageId', db.Integer, db.ForeignKey('UM_WebPage_Mst.pk_webpageId'))
    allow_add = db.Column('AllowAdd', db.Boolean)
    allow_update = db.Column('AllowUpdate', db.Boolean)
    allow_delete = db.Column('AllowDelete', db.Boolean)
    allow_view = db.Column('AllowView', db.Boolean)
    webpage = db.relationship('WebPage', backref=db.backref('rights', lazy=True))

class PA_ET_Master(db.Model):
    __tablename__ = 'PA_ET_Master'
    id = db.Column('Pk_ETID', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(30))
    remarks = db.Column('Remarks', db.String(500))
    dated = db.Column('Dated', db.DateTime)
    fk_session_id = db.Column('fk_SessionId', db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))
    letter_no = db.Column('LetterNo', db.String(500))
    letter_date = db.Column('LetterDate', db.DateTime)

    session = db.relationship('AcademicSession', backref=db.backref('et_masters', lazy=True))

class PA_Exam_Center_Mst(db.Model):
    __tablename__ = 'PA_Exam_Center_Mst'
    id = db.Column('pk_examCenterId', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(150), nullable=False)
    address = db.Column('Address', db.String(255), nullable=False)
    code = db.Column('Code', db.String(15))
    is_active = db.Column('IsActive', db.Boolean, nullable=False, default=True)
    center_type = db.Column('Center_Type', db.Integer)
    order_by = db.Column('OrderBy', db.Integer)
    fk_et_id = db.Column('fk_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))
    fk_session_id = db.Column('fk_SessionId', db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))

    et_master = db.relationship('PA_ET_Master', backref=db.backref('exam_centers', lazy=True))
    session = db.relationship('AcademicSession', backref=db.backref('exam_centers', lazy=True))

class PA_Exam_Center_Trn(db.Model):
    __tablename__ = 'PA_Exam_Center_Trn'
    id = db.Column('pk_id', db.Integer, primary_key=True)
    fk_exam_center_id = db.Column('fk_examCenterId', db.Integer, db.ForeignKey('PA_Exam_Center_Mst.pk_examCenterId'), nullable=False)
    room_no = db.Column('RoomNo', db.String(25))
    room_capacity = db.Column('RoomCapacity', db.Integer, nullable=False)
    no_row = db.Column('NoRow', db.String(20))
    no_column = db.Column('NoColumn', db.String(20))
    room_location = db.Column('RoomLocation', db.String(100))
    paper_dist = db.Column('Paper_Dist', db.String(100))
    order_by = db.Column('OrderBy', db.Integer)

    exam_center = db.relationship('PA_Exam_Center_Mst', backref=db.backref('rooms', lazy=True, cascade='all, delete-orphan'))

class StaffType_Mst(db.Model):
    __tablename__ = 'StaffType_Mst'
    id = db.Column('Pk_Staff_TypeID', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(500))

class StaffCategory_Mst(db.Model):
    __tablename__ = 'StaffCategory_Mst'
    id = db.Column('Pk_StaffCatID', db.Integer, primary_key=True)
    description = db.Column('Description', db.String(50), nullable=False)
    amount = db.Column('Amount', db.Numeric(10, 2))
    fk_staff_type_id = db.Column('Fk_Staff_TypeID', db.Integer, db.ForeignKey('StaffType_Mst.Pk_Staff_TypeID'))
    category_order = db.Column('CategoryOrder', db.Integer)
    
    # Audit columns required by DB
    fk_insUserID = db.Column('fk_insUserID', db.String(50), nullable=False, default='admin')
    fk_updUserID = db.Column('fk_updUserID', db.String(50), nullable=False, default='admin')
    fk_insDateID = db.Column('fk_insDateID', db.String(50), nullable=False, default='admin')
    fk_updDateID = db.Column('fk_updDateID', db.String(50), nullable=False, default='admin')

    staff_type = db.relationship('StaffType_Mst', backref=db.backref('categories', lazy=True))

class PA_ExternalStaff_Trn(db.Model):
    __tablename__ = 'PA_ExternalStaff_Trn'
    id = db.Column('PK_ExStaffId', db.BigInteger, primary_key=True)
    name = db.Column('Name', db.String(250))
    department = db.Column('Department', db.String(250))
    designation = db.Column('Designation', db.String(250))
    contact_no = db.Column('ContactNo', db.String(50))
    fk_et_id = db.Column('Fk_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))

    et_master = db.relationship('PA_ET_Master', backref=db.backref('external_staff', lazy=True))

class PA_Exemption_Mst(db.Model):
    __tablename__ = 'PA_Exemption_Mst'
    id = db.Column('Pk_ExemptionID', db.Integer, primary_key=True)
    fk_session_id = db.Column('Fk_SessionId', db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))
    fk_et_id = db.Column('Fk_ETId', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))

    session = db.relationship('AcademicSession', backref=db.backref('exemptions', lazy=True))
    et_master = db.relationship('PA_ET_Master', backref=db.backref('exemptions', lazy=True))

class PA_Exemption_Detail(db.Model):
    __tablename__ = 'PA_Exemption_Detail'
    id = db.Column('Pk_ExempID', db.Integer, primary_key=True)
    fk_exemption_id = db.Column('Fk_ExemptionId', db.Integer, db.ForeignKey('PA_Exemption_Mst.Pk_ExemptionID'))
    emp_id = db.Column('Emp_Id', db.String(50))
    staff_name = db.Column('StaffName', db.String(250))
    department = db.Column('Department', db.String(250))
    designation = db.Column('Designation', db.String(250))
    contact_no = db.Column('ContactNo', db.String(15))
    fk_et_id = db.Column('FK_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))

    exemption = db.relationship('PA_Exemption_Mst', backref=db.backref('details', lazy=True, cascade='all, delete-orphan'))

class PA_StaffDuties_Mst(db.Model):
    __tablename__ = 'PA_StaffDuties_Mst'
    id = db.Column('Pk_Staffid', db.Integer, primary_key=True)
    fk_session_id = db.Column('fk_sessionid', db.Integer, db.ForeignKey('LUP_AcademicSession_Mst.pk_sessionid'))
    fk_et_id = db.Column('Fk_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))

    session = db.relationship('AcademicSession', backref=db.backref('duties_mst', lazy=True))
    et_master = db.relationship('PA_ET_Master', backref=db.backref('duties_mst', lazy=True))

class PA_StaffDuties_Trn(db.Model):
    __tablename__ = 'PA_StaffDuties_Trn'
    id = db.Column('pk_Trnid', db.Integer, primary_key=True)
    fk_staff_id = db.Column('fk_Staffid', db.Integer, db.ForeignKey('PA_StaffDuties_Mst.Pk_Staffid'), nullable=False)
    staff_name = db.Column('StaffName', db.String(50), nullable=False)
    department = db.Column('Department', db.String(250))
    designation = db.Column('Designation', db.String(50), nullable=False)
    contact_no = db.Column('ContactNo', db.String(15), nullable=False)
    staff_type_desc = db.Column('StaffType', db.String(50))
    fk_exam_center_id = db.Column('fk_examCenterId', db.Integer, db.ForeignKey('PA_Exam_Center_Mst.pk_examCenterId'))
    room_no = db.Column('RoomNo', db.String)
    fk_staff_cat_id = db.Column('Fk_StaffCatID', db.Integer, db.ForeignKey('StaffCategory_Mst.Pk_StaffCatID'))
    fk_staff_type_id = db.Column('Fk_Staff_TypeID', db.Integer, db.ForeignKey('StaffType_Mst.Pk_Staff_TypeID'))
    amount = db.Column('Amount', db.Numeric(10, 2))
    emp_id = db.Column('Emp_Id', db.String(50))
    emp_code = db.Column('EmpCode', db.String(50))
    fk_et_id = db.Column('Fk_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))
    remuneration_type = db.Column('Remuneration_Type', db.String(20))
    rate = db.Column('Rate', db.Numeric(10, 2))
    from_date = db.Column('FromDate', db.String(15))
    to_date = db.Column('ToDate', db.String(15))
    fk_ex_staff_id = db.Column('FK_ExStaffId', db.BigInteger, db.ForeignKey('PA_ExternalStaff_Trn.PK_ExStaffId'))

    duty_mst = db.relationship('PA_StaffDuties_Mst', backref=db.backref('duties', lazy=True, cascade='all, delete-orphan'))
    exam_center = db.relationship('PA_Exam_Center_Mst', backref=db.backref('assigned_staff', lazy=True))
    category = db.relationship('StaffCategory_Mst', backref=db.backref('assigned_staff', lazy=True))
    staff_type = db.relationship('StaffType_Mst', backref=db.backref('assigned_staff_trn', lazy=True))
    et_master = db.relationship('PA_ET_Master', backref=db.backref('duties_trn', lazy=True))

class PA_StaffDuties_Room_Details(db.Model):
    __tablename__ = 'PA_StaffDuties_Room_Details'
    id = db.Column('Pk_Id', db.BigInteger, primary_key=True)
    fk_room_id = db.Column('Fk_RoomId', db.Integer, db.ForeignKey('PA_Exam_Center_Trn.pk_id'))
    room_no = db.Column('RoomNo', db.String(50))
    fk_et_id = db.Column('Fk_ETID', db.Integer, db.ForeignKey('PA_ET_Master.Pk_ETID'))
    fk_staff_id_mst = db.Column('FK_SfaffId', db.Integer, db.ForeignKey('PA_StaffDuties_Mst.Pk_Staffid'))
    fk_trn_id = db.Column('Fk_Trnid', db.Integer, db.ForeignKey('PA_StaffDuties_Trn.pk_Trnid'))
    emp_id = db.Column('Emp_Id', db.String(50))
    fk_ex_staff_id = db.Column('FK_ExStaffId', db.BigInteger, db.ForeignKey('PA_ExternalStaff_Trn.PK_ExStaffId'))

    room = db.relationship('PA_Exam_Center_Trn', backref=db.backref('duty_allocations', lazy=True))
    duty_mst = db.relationship('PA_StaffDuties_Mst', backref=db.backref('room_details', lazy=True))
    duty_trn = db.relationship('PA_StaffDuties_Trn', backref=db.backref('assigned_rooms', lazy=True))


class UM_Users_Mst(db.Model):
    __tablename__ = 'UM_Users_Mst'
    id = db.Column('pk_userId', db.String(15), primary_key=True)
    fk_empId = db.Column('fk_empId', db.String(15))
    loginname = db.Column('loginname', db.String(50))
    name = db.Column('name', db.String(100))
    dept = db.Column('dept', db.String(100))
    desig = db.Column('desig', db.String(100))
    email = db.Column('email', db.String(100))
    active = db.Column('active', db.Boolean)

class PARegistrationMst(db.Model):
    __tablename__ = 'PA_Registration_Mst'
    id = db.Column('pk_regid', db.BigInteger, primary_key=True)
    fk_sessionid = db.Column(db.Integer)
    regno = db.Column(db.String(9))
    mobileno = db.Column(db.String(15))
    email = db.Column(db.String(50))
    pwd = db.Column(db.String(255))
    s_name = db.Column(db.String(100))
    dob = db.Column(db.DateTime)
    fk_dtypeid = db.Column(db.Integer)
    fk_degreeid = db.Column('fk_examid', db.Integer) # mapping to degree/exam
    f_name = db.Column(db.String(100))
    m_name = db.Column(db.String(100))
    gender = db.Column(db.String(1))
    fk_stucatid_cast = db.Column(db.Integer)
    fk_stypeid = db.Column(db.Integer)
    
    # Extra Personal Info fields
    AdharNo = db.Column(db.String(50))
    Parents_Mobileno = db.Column(db.String(15))
    Marital_Status = db.Column(db.String(10))
    ChildStatus = db.Column(db.String(10))
    Blood_Group = db.Column(db.String(5))
    nationality = db.Column(db.String(10))
    FatherGuargian = db.Column(db.String(10))
    FatherOccupation = db.Column(db.String(100))
    AnnualIncome = db.Column(db.String(50))
    FF = db.Column(db.String(5))
    ESM = db.Column(db.String(5))
    PH = db.Column(db.String(5))
    familyId = db.Column(db.String(50))
    SportsQuota = db.Column(db.String(5))
    IsWard = db.Column(db.String(5))
    Resident = db.Column(db.String(50))
    LDV = db.Column(db.String(5))
    fk_religionid = db.Column(db.Integer)
    
    # Step 2 Address Info
    c_address = db.Column(db.String(255))
    c_district = db.Column(db.String(50))
    c_fk_stateid = db.Column(db.Integer)
    c_pincode = db.Column(db.String(10))
    C_Village = db.Column(db.String(50))
    
    p_address = db.Column(db.String(255))
    p_district = db.Column(db.String(50))
    p_fk_stateid = db.Column(db.Integer)
    p_pincode = db.Column(db.String(10))
    P_Village = db.Column(db.String(50))
    
    step1 = db.Column(db.Boolean, default=False)
    step2 = db.Column(db.Boolean, default=False)
    step3 = db.Column(db.Boolean, default=False)
    step4 = db.Column(db.Boolean, default=False)
    step5 = db.Column(db.Boolean, default=False)
    confirm_dec = db.Column(db.Boolean, default=False)
    totfee = db.Column(db.Numeric(10, 2))
    IsPaymentSuccess = db.Column(db.Boolean, default=False)


class PAFamilyAdditionalInfo(db.Model):
    __tablename__ = 'REC_FamilyandAdditional_Information'
    Pk_FId = db.Column(db.Integer, primary_key=True)
    fk_regid = db.Column(db.BigInteger)
    Ex_Student = db.Column(db.String(1))
    OtherInformation = db.Column(db.String(255))
    ReleventStatus = db.Column(db.String(1))
    RuralOrUrban = db.Column(db.String(1))


class MainpageNavigation(db.Model):
    __tablename__ = 'PA_Mainpage_Navigation'
    id = db.Column('MN_Pkid', db.Integer, primary_key=True)
    div = db.Column('Div', db.String(10))
    contenttype = db.Column('Contenttype', db.String(500))
    filetype = db.Column('Filetype', db.String(1000))
    filetext = db.Column('Filetext', db.String(500))
    filename = db.Column('FileName', db.String(500))
    noticetext = db.Column('Noticetext', db.String(1000))
    active = db.Column('Active', db.Boolean, default=True)
    order_by = db.Column('Orderby', db.Integer)
    is_new = db.Column('IsNew', db.Boolean, default=False)

class AnswerKeyExamType(db.Model):
    __tablename__ = 'PA_AnswerKeyExamType_mst'
    id = db.Column('pk_ID', db.Integer, primary_key=True)
    exam_type_id = db.Column('ExamTypeID', db.String(5))
    exam_type_desc = db.Column('ExamType', db.String(200))
    degree_id = db.Column('DegreeID', db.Integer)