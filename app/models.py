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
    is_approved = db.Column('IsApproved', db.Boolean, default=True)

class Religion(db.Model):
    __tablename__ = 'Religion_Mst'
    id = db.Column('pk_religionid', db.Integer, primary_key=True)
    description = db.Column('religiontype', db.String(100), nullable=False)

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
    reservation = db.Column('Reservation', db.Integer)
    order_no = db.Column('OrderNo', db.Integer)
    is_dependent = db.Column('IsDependent', db.Boolean)

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
