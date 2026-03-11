import os
from io import BytesIO
from xhtml2pdf import pisa
from flask import render_template

def render_to_pdf(template_src, context_dict):
    """Render a Jinja2 template into a PDF file using xhtml2pdf."""
    html = render_template(template_src, **context_dict)
    result = BytesIO()
    
    # Define a custom link_callback to resolve local static files if needed
    # For now we'll just pass the HTML
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None
