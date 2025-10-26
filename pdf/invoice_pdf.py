from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice_pdf(invoice_id, filename="invoice.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    c.drawString(50, 800, f"Invoice #{invoice_id}")
    c.drawString(50, 780, "Customer: John Doe")
    c.drawString(50, 760, "Total: 100.00€")
    c.save()
