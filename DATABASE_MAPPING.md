# DATABASE MAPPING FOR HAU PREADMISSION SYSTEM

| Module Name | Table Name | Primary Key |
| :--- | :--- | :--- |
| **Academic Session Master** | `LUP_AcademicSession_Mst` | `pk_sessionid` |
| **Degree Type Master** | `ACD_DegreeType_Mst` | `pk_dtypeid` |
| **Degree Master** | `ACD_Degree_Mst` | `pk_degreeid` |
| **University Specialization Master** | `PA_Specialization_mst` | `Pk_SID` |
| **Map University Degree & Spec** | `PA_AppearSubjectDegree_Map` | N/A (Composite) |
| **Candidate Qual Master** | `ACD_EducationQualification_Mst` | `Pk_EID` |
| **Candidate Spec Master** | `PA_Education_Specialization_Mst` | `Pk_ESP_Id` |
| **Map Cand. Qual & Spec** | `PA_Education_Specialization_Mapping` | `Pk_ESP_Map_Id` |
| **Map Univ Spec & Cand Qual Spec** | `PA_Spec_Eligible_Criteria_Mapping` | `Pk_ID` |
| **Map College & Univ Spec (Option Form)** | `PA_College_Spec_Map` | `Pk_MapID` |
| **College Master** | `SMS_College_Mst` | `pk_collegeid` |
| **Board Master** | `PA_Board_Mst` | `Pk_BoardId` |
| **Religion Master** | `Religion_Mst` | `pk_religionid` |
| **Student Category Master** | `PA_StudentCategory_Mst` | `Pk_StuCatId` |
| **Previous Exam Master** | `PA_PreviousExam_Mst` | `Pk_PrevExamId` |
| **Previous Exam Stream Master** | `PA_PrevExam_Stream_Mst` | `Pk_PEStreamId` |
| **Attachment Master** | `PA_Attachment_Mst` | `Pk_attachmentId` |
| **Manage Page Rights** | `UM_UserPageRights` | `pk_pagerightid` |
| **List of Notifications & Links** | `PA_Link_Configuration_Mst` | `pk_LinkId` |
| **WebPage Master** | `UM_WebPage_Mst` | `pk_webpageId` |
| **Appear Subject Master** | `PA_AppearSubject_Mst` | `pk_aprsubid` |
| **District Master (City)** | `District_Mst` | `pk_DistrictId` |
| **College Category Master** | `PA_College_Mst` | `Pk_CollegeID` |
| **College Type Master** | `SMS_CollegeTpye_Mst` | `pk_collegetypeid` |
