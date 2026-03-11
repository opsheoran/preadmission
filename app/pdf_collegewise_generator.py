import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from flask import current_app

class FooterCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
    
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(landscape(A4)[0] - 0.5 * inch, 0.5 * inch, page_str)

def generate_collegewise_pdf(records):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=14, fontName='Helvetica-Bold', spaceAfter=2)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], alignment=1, fontSize=12, fontName='Helvetica-Bold', spaceAfter=15)
    
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    
    cell_style_center = ParagraphStyle('CellCenter', parent=styles['Normal'], alignment=1, fontSize=8, fontName='Helvetica')
    cell_style_left = ParagraphStyle('CellLeft', parent=styles['Normal'], alignment=0, fontSize=8, fontName='Helvetica')
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], alignment=1, fontSize=8, fontName='Helvetica-Bold')
    
    elements = []
    
    # Image paths
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    hindi_path = os.path.join(current_app.root_path, 'static', 'img', 'hindi_name.png')
    
    has_logo = os.path.exists(logo_path)
    has_hindi = os.path.exists(hindi_path)
    
    # Group records by Specialization
    grouped_records = {}
    for row in records:
        spec = row.get("Specialization", "")
        if spec not in grouped_records:
            grouped_records[spec] = []
        grouped_records[spec].append(row)
        
    # Sort groups by specialization name
    sorted_specs = sorted(grouped_records.keys())
    
    now = datetime.now()
    date_str = now.strftime("%m/%d/%Y")
    time_str = now.strftime("%I:%M:%S %p").lower()
    
    for idx, spec in enumerate(sorted_specs):
        group = grouped_records[spec]
        first_row = group[0]
        
        session_val = first_row.get('Session', '')
        degree_val = first_row.get('Degree', '')
        cutoff_val = first_row.get('Cutoff', '')
        
        # Header with Logo and Text
        header_table_data = []
        
        logo_img = Image(logo_path, width=1*inch, height=1*inch) if has_logo else ""
        hindi_img = Image(hindi_path, width=4*inch, height=0.4*inch) if has_hindi else ""
        
        if has_logo or has_hindi:
            header_table_data = [
                [logo_img, hindi_img],
                ["", Paragraph("CCS Haryana Agricultural University", title_style)],
                ["", Paragraph("Collegewise Departmentwise Report", subtitle_style)]
            ]
            header_table = Table(header_table_data, colWidths=[1.2*inch, 7.5*inch])
            header_table.setStyle(TableStyle([
                ('SPAN', (0,0), (0,2)),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))
        else:
            elements.append(Paragraph("CCS Haryana Agricultural University", title_style))
            elements.append(Paragraph("Collegewise Departmentwise Report", subtitle_style))
            elements.append(Spacer(1, 15))
        
        # Meta info table
        meta_data = [
            [Paragraph(f"<b>Session</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {session_val}", info_style),
             Paragraph(f"<b>Date</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {date_str}", ParagraphStyle('R', parent=info_style, alignment=2))],
            [Paragraph(f"<b>Degree</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {degree_val}", info_style),
             Paragraph(f"<b>Time</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {time_str}", ParagraphStyle('R', parent=info_style, alignment=2))],
            [Paragraph(f"<b>Specialization</b> : {spec}", info_style),
             Paragraph(f"<b>Cutoff</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {cutoff_val}", ParagraphStyle('R', parent=info_style, alignment=2))]
        ]
        
        meta_table = Table(meta_data, colWidths=[4*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))
        
        # Data Table
        table_data = [[
            Paragraph("S.No.", header_style), 
            Paragraph("Registration<br/>No", header_style), 
            Paragraph("Name", header_style), 
            Paragraph("Father Name", header_style), 
            Paragraph("ET Marks", header_style), 
            Paragraph("Last Qalified<br/>Marks", header_style), 
            Paragraph("Old Allotment", header_style), 
            Paragraph("New Allotment", header_style), 
            Paragraph("Status", header_style), 
            Paragraph("Signature", header_style)
        ]]
        
        for i, row in enumerate(group):
            sno = str(i + 1)
            regno = str(row.get('RegistrationNo', ''))
            name = str(row.get('Name', ''))
            fname = str(row.get('FatherName', ''))
            etmarks = str(row.get('ETMarks', '')) if row.get('ETMarks') is not None else ''
            lastqual = str(row.get('Lastqualifiedmarks', '')) if row.get('Lastqualifiedmarks') is not None else ''
            oldallot = str(row.get('OldAllotment', ''))
            newallot = str(row.get('NewAllotement', ''))
            status = str(row.get('Status', ''))
            signature = ""
            
            table_data.append([
                Paragraph(sno, cell_style_center), 
                Paragraph(regno, cell_style_center), 
                Paragraph(name, cell_style_left), 
                Paragraph(fname, cell_style_left), 
                Paragraph(etmarks, cell_style_center), 
                Paragraph(lastqual, cell_style_center), 
                Paragraph(oldallot, cell_style_left), 
                Paragraph(newallot, cell_style_left), 
                Paragraph(status, cell_style_center), 
                Paragraph(signature, cell_style_center)
            ])
            
        col_widths = [0.4*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.6*inch, 0.8*inch, 1.2*inch, 2.5*inch, 0.7*inch, 0.8*inch]
        
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
            
        elements.append(t)
        
        if idx < len(sorted_specs) - 1:
            elements.append(PageBreak())
            
    doc.build(elements, canvasmaker=FooterCanvas)
    
    return buffer.getvalue()
