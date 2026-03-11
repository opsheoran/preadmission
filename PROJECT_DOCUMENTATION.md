# HAU Preadmission System - Comprehensive Documentation

## 1. Database Schema & Tables

This project interacts with a SQL Server database containing several schemas (ACD, PA, LUP, UM, SMS). Below is the detailed breakdown of tables used.

### Core Masters
*   **Academic Session (`LUP_AcademicSession_Mst`)**
    *   `pk_sessionid`: Primary Key
    *   `description`: Session name (e.g., 2025-26)
    *   `Active`: Boolean status
*   **Degree Type (`ACD_DegreeType_Mst`)**
    *   `pk_dtypeid`: Primary Key
    *   `description`: Type name (Graduate, Post Graduate)
*   **Degree Master (`ACD_Degree_Mst`)**
    *   `pk_degreeid`: Primary Key
    *   `description`: Degree name
    *   `fk_dtypeid`: FK to Degree Type
    *   `active`: Status
*   **College Category (`PA_College_Mst`)**
    *   `Pk_CollegeID`: Primary Key
    *   `CollegeName`: Parent category name (e.g., College of Agriculture)
*   **Board Master (`PA_Board_Mst`)**
    *   `Pk_BoardId`: Primary Key
    *   `Description`: Board name (e.g., CBSE, HBSE)
*   **Religion Master (`Religion_Mst`)**
    *   `pk_religionid`: Primary Key
    *   `religiontype`: Religion name

### Specialization & Mapping
*   **University Specialization (`PA_Specialization_mst`)**
    *   `Pk_SID`: Primary Key
    *   `Specialization`: Name of specialization
    *   `Fk_CollegeID`: FK to PA_College_Mst
*   **University Degree & Specialization Mapping (`PA_Degree_SpecializationMapping_mst`)**
    *   `Pk_MapId`: Primary Key
    *   `fk_SID`: FK to Specialization
    *   `fk_DegreeId`: FK to Degree
    *   `fk_CollegeId`: FK to College Category (PA_College_Mst)
    *   `ExamType`: Entrance/Non-Entrance indicator
*   **Candidate Qualification & Specialization (`ACD_EducationQualification_Mst` & `PA_Education_Specialization_Mst`)**
    *   Mapped via `PA_Education_Specialization_Mapping`.
*   **Eligibility Mapping (`PA_Spec_Eligible_Criteria_Mapping`)**
    *   The "Bridge" table. It links a `UnivDegreeSpecMap` (Module 5) to multiple `CandidateQualSpecMap` (Module 8). This defines what education a candidate must have to apply for a specific University Degree/Specialization.

### Application Logic (Option Forms)
*   **College & Univ Spec Option (`PA_College_Spec_Map`)**
    *   Used for the "Option Form" where students select preferences.
    *   `fk_collegeID`: FK to specific campus (`SMS_College_Mst`).
    *   `seat`: Number of available seats.
    *   `csir_seat`: Specialized seat count.

---

## 2. Blueprint & Route Logic (`app/blueprints/main.py`)

The application uses a modular Blueprint named `main`. All routes follow a standard **Research -> Strategy -> Execution** pattern with CRUD (Create, Read, Update, Delete) capabilities.

### Standard Patterns Used:
1.  **Pagination:** A helper `get_paginated_data` handles SQL `OFFSET/FETCH` for all grids.
2.  **Edit Mode:** Routes check for an `edit_id` in the URL. If present, they load the object and change the form button from "SAVE" to "UPDATE".
3.  **Filtering:** Complex modules (like Module 10) use GET parameters (`f_session_id`, etc.) to automatically refresh the grid when dropdowns change.
4.  **Relationships:** SQLAlchemy `db.relationship` is used to join tables (e.g., displaying Degree Name instead of ID in grids).

### Key Modules:
*   **Module 5 (Map Univ Degree & Spec):** Includes AJAX APIs to fetch colleges based on degree selection.
*   **Module 9 (Eligible Mapping):** Uses a checkbox list to allow one-to-many mapping between University Specs and Candidate Qualifications.
*   **Module 10 (Option Form Mapping):** Restricted to only show active degrees that have already been mapped in Module 5.

---

## 3. Infrastructure Configuration
*   **Port:** 5013 (External access via IP:5013)
*   **Database:** SQL Server (pyodbc)
*   **Public Access:** Configured to listen on `0.0.0.0` for static IP access.
*   **Backup:** Full source backup taken on 2026-02-27.
*   **Git:** Synchronized with `https://github.com/opsheoran/preadmission.git`.
