# Live Templates (Configuration Process)

Source folder: `configuration Process\`

When you say **“live templates”**, this refers to these HTML exports and their controls (used as the reference to mimic UI + behavior in this Flask project):

## Menu items (as per live site)
- Application Fee Config → `configuration Process\Application fee Config.html`
- Admission Process Configuration → `configuration Process\admission process configuration.html`
- Counselling Configuration → `configuration Process\councelling configuration.html`
- Student Upward Configuration → `configuration Process\student upward configuration.html`
- Admit Card Configuration → `configuration Process\Admit Card Configuration.html`
- UG Seat Matrix Master → `configuration Process\UG Seat Matrix Master.html`
- Roster Master → `configuration Process\Roaster Master.html`
- Instructions Master → `configuration Process\Instructions Master.html`
- Allotment Letter Master → `configuration Process\Allotment Letter Master.html`
- Duty Letter Configuration → `configuration Process\Duty Letter Configuration.html`
- Category Remuneration Configuration → `configuration Process\Category Remuneration Configuration.html`
- Student Additional Fee Config → `configuration Process\Student Additional Fee Configuration.html`

## Controls checklist (extracted from templates)

## UI note (project standard)
- Use the project calendar icon `app/static/img/calendar.svg` on the right side of date fields (with the project datepicker) for consistent look across pages.

### Application Form Fee Configuration
- Academic Session, Degree Apply For
- Form Fee For PH
- Effective Date
- Late Fee

### Admission Process Configuration
- Academic Session, Dated
- Order/Reference No., Remarks
- Degree/College Type, Login Allowed
- Entrance Date
- Login Start/End
- Login Payment Start/End
- Application Start/End
- End Date (With Late Fee)
- NRI Start/End
- NRI End Date (With Late Fee)
- Grievance Start/End, Fees
- Modify Personal Info Start/End, Fees
- Admit Card Start/End
- RC Start/End
- Marks/Ranks Start/End
- Option Form Start/End
- Apply Upward Start/End

### Counselling Configuration
- College, Degree, Student Category, Session
- CutOffMarks, Exempt checkbox
- Start Date, End Date, Payment Date
- PWD checkbox
- Search Degree (separate dropdown in the template)

### Student Upward Configuration
- Session, Degree, College, CutOff
- Start Date, End Date

### Admit Card Configuration
- Degree Type, Session, Entrance Test
- Instructions (multi-line)
- Date of Exam, Day of Exam
- Reporting Time (H/M/AM-PM)
- No Entry After (H/M/AM-PM)
- Duration of Exam (From H/M/AM-PM) + (To H/M/AM-PM)
- Can Not Leave Before (H/M/AM-PM)

### UG Seat Matrix Master
- Session, Degree
- College, Gender
- Category, Is ESM Seat checkbox
- No of Seats
- LDV, Employee Ward, Sports (seat breakup fields)

### Roster Master (live file uses “Roaster”)
- Session, College Stream Name
- College Name, Degree Type
- Category, Sequence

### Instructions Master
- Academic Session, Degree Type
- Instruction (rich-text editor in live)
- Order By
- Is Active checkbox

### Allotment Letter Master
- Session, Degree
- College, Cut Off
- Report Text From/To Date
- Allotment Print From/To Date
- Allotment No
- Venue (multi-line)
- PH Before Merit checkbox

### Duty Letter Configuration
- Session, Entrance Test
- From Date, To Date
- Active checkbox

### Category Remuneration Configuration
- Session, ET Name, ET Date
- Staff Type, Staff Category
- From Date, To Date
- Remuneration
- Amount
- Search filters: Session, ET Name, Staff Type, Staff Category

### Student Additional Fee Configuration
- Enter Registration ID
