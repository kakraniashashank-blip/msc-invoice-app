import math
from fpdf import FPDF

def num_to_words(num):
    if num == 0:
        return "Zero Rupees Only"
    
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_below_100(n):
        if n < 20:
            return ones[n]
        else:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
            
    def convert(n):
        if n == 0:
            return ""
        elif n < 100:
            return convert_below_100(n)
        elif n < 1000:
            return ones[n // 100] + " Hundred" + (" " + convert_below_100(n % 100) if n % 100 != 0 else "")
        elif n < 100000:
            return convert(n // 1000) + " Thousand" + (" " + convert(n % 1000) if n % 1000 != 0 else "")
        elif n < 10000000:
            return convert(n // 100000) + " Lakh" + (" " + convert(n % 100000) if n % 100000 != 0 else "")
        else:
            return convert(n // 10000000) + " Crore" + (" " + convert(n % 10000000) if n % 10000000 != 0 else "")

    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    res = "Rupees " + convert(rupees)
    if paise > 0:
        res += " and Paise " + convert(paise)
    res += " Only"
    
    return res

def generate_invoice_pdf(doc_type, inv_no, inv_date, client_name, client_info, order_no, order_date, vehicle_no, payment_terms, items, del_charges, products):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_margins(10, 10, 10)
    
    page_width = 190
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(page_width, 8, doc_type.upper(), border=0, align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_fill_color(240, 240, 240)
    
    pdf.set_font('helvetica', 'B', 20)
    pdf.set_text_color(0, 51, 153)
    pdf.cell(page_width, 10, "MURLI STEEL CORPORATION", align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(page_width, 5, "9/12, Lal Bazar Street, Mercantile Building,", align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(page_width, 5, "'B' Block, 1st Floor, Kolkata - 700001, India", align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(page_width, 5, "Phone: (033) 2210 1650 | Mobile: 9830242818", align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(page_width, 5, "Email: shradkakrania@gmail.com", align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(page_width, 6, "PAN: AKAPK4846L | GSTIN: 19AKAPK4846L1ZS", align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(95, 6, "  BILLED TO PARTY", border='R', fill=True)
    pdf.cell(95, 6, "  INVOICE DETAILS", border=0, fill=True, new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 9)
    
    client_addr = client_info.get('address', '')
    client_gstin = client_info.get('gstin', '')
    client_state = client_info.get('state', '')
    
    pdf.cell(95, 5, f"  Name: {client_name}", border='R')
    pdf.cell(95, 5, f"  Invoice No.: {inv_no}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(95, 5, f"  Address: {client_addr[:45]}", border='R')
    pdf.cell(95, 5, f"  Invoice Date: {inv_date}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(95, 5, f"  GSTIN: {client_gstin}", border='R')
    pdf.cell(95, 5, f"  Terms: {payment_terms}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(95, 5, f"  Order No.: {order_no}", border='R')
    pdf.cell(95, 5, f"  Supply: West Bengal", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(95, 5, f"  Order Date: {order_date}", border='R')
    pdf.cell(95, 5, f"  ", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(95, 5, f"  State: {client_state}", border='R')
    pdf.cell(95, 5, f"  ", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    delivery = client_info.get('delivery', '')
    pdf.cell(page_width, 6, f" Delivery At: {delivery}  |  Transport: Lorry  |  Vehicle: {vehicle_no}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    cols = [8, 25, 70, 16, 11, 20, 16, 24]
    
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(cols[0], 6, "SN", border=1, fill=True, align='C')
    pdf.cell(cols[1], 6, "Code", border=1, fill=True, align='C')
    pdf.cell(cols[2], 6, "Description", border=1, fill=True, align='C')
    pdf.cell(cols[3], 6, "HSN", border=1, fill=True, align='C')
    pdf.cell(cols[4], 6, "Pcs", border=1, fill=True, align='C')
    pdf.cell(cols[5], 6, "Qty", border=1, fill=True, align='C')
    pdf.cell(cols[6], 6, "Rate", border=1, fill=True, align='C')
    pdf.cell(cols[7], 6, "Value", border=1, fill=True, align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 8)
    
    total_qty = 0
    total_pcs = 0
    total_taxable = 0
    
    for i, item in enumerate(items):
        code = item.get('code', '')
        
        desc = item.get('desc', '')
        if not desc and code in products:
            desc = products[code].get('description', '')
            
        hsn = item.get('hsn', '')
        if not hsn and code in products:
            hsn = products[code].get('hsn', '')
        if not hsn:
            hsn = '721550'
            
        try:
            pcs = int(item.get('pcs', 0) or 0)
        except (ValueError, TypeError):
            pcs = 0
        try:
            qty = float(item.get('qty', 0) or 0)
        except (ValueError, TypeError):
            qty = 0.0
        try:
            rate = float(item.get('rate', 0) or 0)
        except (ValueError, TypeError):
            rate = 0.0
        val = qty * rate
        
        total_pcs += pcs
        total_qty += qty
        total_taxable += val
        
        pdf.cell(cols[0], 6, str(i+1), border=1, align='C')
        pdf.cell(cols[1], 6, code, border=1, align='L')
        
        desc_str = str(desc)
        if len(desc_str) > 40:
            desc_str = desc_str[:37] + "..."
        pdf.set_font('helvetica', '', 7)
        pdf.cell(cols[2], 6, desc_str, border=1, align='L')
        pdf.set_font('helvetica', '', 8)
        
        pdf.cell(cols[3], 6, str(hsn), border=1, align='C')
        pdf.cell(cols[4], 6, str(pcs), border=1, align='R')
        pdf.cell(cols[5], 6, f"{qty:.3f}", border=1, align='R')
        pdf.cell(cols[6], 6, f"{rate:.2f}", border=1, align='R')
        pdf.cell(cols[7], 6, f"{val:.2f}", border=1, align='R', new_x='LMARGIN', new_y='NEXT')
        
    pdf.set_font('helvetica', 'B', 8)
    w_before_qty = cols[0] + cols[1] + cols[2] + cols[3] + cols[4]
    pdf.cell(w_before_qty, 6, "TOTAL: ", border=1, align='R')
    pdf.cell(cols[5], 6, f"{total_qty:.3f}", border=1, align='R')
    pdf.cell(cols[6], 6, "", border=1, align='C')
    pdf.cell(cols[7], 6, f"{total_taxable:.2f}", border=1, align='R', new_x='LMARGIN', new_y='NEXT')
    
    taxable_val = total_taxable + del_charges
    cgst = taxable_val * 0.09
    sgst = taxable_val * 0.09
    grand_total = round(taxable_val + cgst + sgst)
    
    amount_text = f"Amount in Words: {num_to_words(grand_total)}"
    
    # Dynamically reduce font size if text is too long (limit: ~118mm)
    pdf.set_font('helvetica', 'B', 8)
    font_size = 8.0
    while pdf.get_string_width(amount_text) > 117 and font_size > 4.5:
        font_size -= 0.5
        pdf.set_font('helvetica', 'B', font_size)
    
    pdf.cell(120, 6, amount_text, border='L', align='L')
    
    # Restore original font size for the rest of the layout
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(46, 6, "Total Before Tax:", border='L', align='L')
    pdf.cell(24, 6, f"{total_taxable:.2f}", border='R', align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 6, "", border='L', align='L')
    pdf.cell(46, 6, "Delivery Charges:", border='L', align='L')
    pdf.cell(24, 6, f"{del_charges:.2f}", border='R', align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 6, "", border='L', align='L')
    pdf.cell(46, 6, "Taxable Value:", border='L', align='L')
    pdf.cell(24, 6, f"{taxable_val:.2f}", border='R', align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 6, "", border='L', align='L')
    pdf.cell(46, 6, "CGST @9%:", border='L', align='L')
    pdf.cell(24, 6, f"{cgst:.2f}", border='R', align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 6, "", border='L', align='L')
    pdf.cell(46, 6, "SGST @9%:", border='L', align='L')
    pdf.cell(24, 6, f"{sgst:.2f}", border='R', align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(120, 6, "", border='LB', align='L')
    pdf.cell(46, 6, "Grand Total:", border='LB', align='L', fill=True)
    pdf.cell(24, 6, f"{grand_total:.2f}", border='BR', align='R', fill=True, new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(120, 5, "Bank Details:", border='L', align='L')
    pdf.cell(70, 5, "Certified that the particulars given above are true & correct", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 8)
    pdf.cell(120, 5, "HDFC Bank Ltd.", border='L', align='L')
    pdf.cell(70, 5, "For MURLI STEEL CORPORATION", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 5, "A/c No.: 00082000057539", border='L', align='L')
    pdf.cell(70, 5, "", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 5, "Branch: Sree Bhumi", border='L', align='L')
    pdf.cell(70, 5, "", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 5, "IFSC: HDFC0004566", border='L', align='L')
    pdf.cell(70, 5, "Authorised Signatory", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(120, 5, "E & O.E.", border='LB', align='L')
    pdf.cell(70, 5, "", border='RB', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.rect(10, 10, 190, pdf.get_y() - 10)
    
    return pdf.output()
