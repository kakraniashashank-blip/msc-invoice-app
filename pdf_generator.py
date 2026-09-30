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
    
    res = convert(rupees) + " Rupees"
    if paise > 0:
        res += " and " + convert(paise) + " Paise"
    res += " Only"
    
    return res

def generate_invoice_pdf(doc_type, inv_no, inv_date, client_name, client_info, order_no, order_date, vehicle_no, payment_terms, items, del_charges, products):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_margins(10, 10, 10)
    
    page_width = 190
    
    # Top section: TAX INVOICE
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_y(10)
    pdf.cell(190, 5, "", border=0, new_x='LMARGIN', new_y='NEXT') 
    
    text_w = pdf.get_string_width("TAX INVOICE") + 6
    pdf.set_xy((210 - text_w) / 2, 10)
    pdf.cell(text_w, 5, "TAX INVOICE", border=1, align='C')
    
    pdf.set_font('helvetica', '', 7)
    pdf.set_xy(10, 10)
    pdf.cell(190, 5, "Original for Buyer/ Seller", border=0, align='R')
    pdf.set_xy(10, 16)
    
    # Company Header
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(0, 51, 153)
    pdf.cell(page_width, 8, "MURLI STEEL CORPORATION", align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', '', 8)
    pdf.cell(page_width, 4, "9/12, Lal Bazar Street, Mercantile Building, 'B' Block, 1st Floor, Kolkata - 700001, India", align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(page_width, 4, "Phone: (033) 2210 1650 | Mobile: 9830242818 | Email: shradkakrania@gmail.com", align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(page_width, 5, "PAN: AKAPK4846L | GSTIN: 19AKAPK4846L1ZS", align='C', new_x='LMARGIN', new_y='NEXT')
    
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)
    
    # Billed To Section
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(95, 5, "BILLED TO PARTY", border='R', align='C')
    pdf.cell(95, 5, "INVOICE DETAILS", border=0, align='C', new_x='LMARGIN', new_y='NEXT')
    
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)
    
    client_addr = client_info.get('address', '')
    client_gstin = client_info.get('gstin', '')
    client_state = client_info.get('state', '')
    
    # Details Row 1
    pdf.set_font('helvetica', '', 8)
    pdf.cell(18, 5, "Name:", border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(77, 5, f"{client_name}", border='R')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(25, 5, "Invoice No.:", border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(70, 5, f"{inv_no}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    # Details Row 2
    pdf.set_font('helvetica', '', 8)
    pdf.cell(18, 5, "Address:", border=0)
    pdf.cell(77, 5, f"{client_addr[:50]}", border='R')
    pdf.cell(25, 5, "Invoice Date:", border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(70, 5, f"{inv_date}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    # Details Row 3
    pdf.set_font('helvetica', '', 8)
    pdf.cell(18, 5, "GSTIN:", border=0)
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(77, 5, f"{client_gstin}", border='R')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(25, 5, "Terms:", border=0)
    pdf.cell(70, 5, f"{payment_terms}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    # Details Row 4
    pdf.cell(18, 5, "Order No.:", border=0)
    pdf.cell(77, 5, f"{order_no}", border='R')
    pdf.cell(25, 5, "Supply:", border=0)
    pdf.cell(70, 5, "West Bengal", border=0, new_x='LMARGIN', new_y='NEXT')
    
    # Details Row 5
    pdf.cell(18, 5, "Order Date:", border=0)
    pdf.cell(77, 5, f"{order_date}", border='R')
    pdf.cell(95, 5, "", border=0, new_x='LMARGIN', new_y='NEXT')
    
    # Details Row 6
    pdf.cell(18, 5, "State:", border=0)
    pdf.cell(77, 5, f"{client_state}", border='R')
    pdf.cell(95, 5, "", border=0, new_x='LMARGIN', new_y='NEXT')
    
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)
    
    delivery = client_info.get('delivery', '')
    pdf.cell(95, 6, f"Delivery At: {delivery}", border='R')
    pdf.cell(45, 6, "Transport: Lorry", border='R')
    pdf.cell(50, 6, f"Vehicle No. : {vehicle_no}", border=0, new_x='LMARGIN', new_y='NEXT')
    
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)
    
    # Table Header
    cols = [8, 25, 70, 16, 11, 20, 16, 24]
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(cols[0], 6, "SN", border=1, align='C')
    pdf.cell(cols[1], 6, "Item Code", border=1, align='C')
    pdf.cell(cols[2], 6, "Description", border=1, align='C')
    pdf.cell(cols[3], 6, "HSN", border=1, align='C')
    pdf.cell(cols[4], 6, "Pcs", border=1, align='C')
    pdf.cell(cols[5], 6, "Qty", border=1, align='C')
    pdf.cell(cols[6], 6, "Rate", border=1, align='C')
    pdf.cell(cols[7], 6, "Value (INR)", border=1, align='C', new_x='LMARGIN', new_y='NEXT')
    
    # Table Body
    table_start_y = pdf.get_y()
    
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
            
        try: pcs = int(item.get('pcs', 0) or 0)
        except: pcs = 0
        try: qty = float(item.get('qty', 0) or 0)
        except: qty = 0.0
        try: rate = float(item.get('rate', 0) or 0)
        except: rate = 0.0
        val = qty * rate
        
        total_pcs += pcs
        total_qty += qty
        total_taxable += val
        
        desc_str = str(desc)
        desc_line1 = desc_str
        desc_line2 = ""
        if len(desc_str) > 40:
            split_idx = desc_str[:40].rfind(' ')
            if split_idx == -1: split_idx = 40
            desc_line1 = desc_str[:split_idx]
            desc_line2 = desc_str[split_idx:].strip()
            if len(desc_line2) > 40:
                desc_line2 = desc_line2[:37] + "..."
                
        row_height = 4.5
        pdf.set_font('helvetica', '', 8)
        pdf.cell(cols[0], row_height, str(i+1), border=0, align='C')
        pdf.cell(cols[1], row_height, code, border=0, align='C')
        pdf.set_font('helvetica', '', 7)
        pdf.cell(cols[2], row_height, desc_line1, border=0, align='L')
        pdf.set_font('helvetica', '', 8)
        pdf.cell(cols[3], row_height, str(hsn), border=0, align='C')
        pdf.cell(cols[4], row_height, str(pcs), border=0, align='C')
        pdf.cell(cols[5], row_height, f"{qty:,.2f}", border=0, align='R')
        pdf.cell(cols[6], row_height, f"{rate:,.2f}", border=0, align='R')
        pdf.cell(cols[7], row_height, f"{val:,.2f}", border=0, align='R', new_x='LMARGIN', new_y='NEXT')
        
        if desc_line2:
            pdf.cell(cols[0], row_height, "", border=0, align='C')
            pdf.cell(cols[1], row_height, "", border=0, align='C')
            pdf.set_font('helvetica', '', 7)
            pdf.cell(cols[2], row_height, desc_line2, border=0, align='L')
            pdf.set_font('helvetica', '', 8)
            pdf.cell(cols[3], row_height, "", border=0, align='C')
            pdf.cell(cols[4], row_height, "", border=0, align='C')
            pdf.cell(cols[5], row_height, "", border=0, align='R')
            pdf.cell(cols[6], row_height, "", border=0, align='R')
            pdf.cell(cols[7], row_height, "", border=0, align='R', new_x='LMARGIN', new_y='NEXT')
            
        current_y = pdf.get_y()
        pdf.line(10, current_y, 200, current_y)
        
    table_bottom_y = max(pdf.get_y(), 195)
    
    # Draw vertical lines for the table
    x_pos = 10
    for w in cols:
        pdf.line(x_pos, table_start_y, x_pos, table_bottom_y)
        x_pos += w
    pdf.line(200, table_start_y, 200, table_bottom_y)
    
    pdf.set_y(table_bottom_y)
    pdf.line(10, table_bottom_y, 200, table_bottom_y)
    
    # Total Row
    pdf.set_font('helvetica', 'B', 8)
    w_before_qty = cols[0] + cols[1] + cols[2] + cols[3] + cols[4]
    pdf.cell(w_before_qty, 6, "TOTAL: ", border=1, align='R')
    pdf.cell(cols[5], 6, f"{total_qty:,.2f}", border=1, align='R')
    pdf.cell(cols[6], 6, "", border=1, align='C')
    pdf.cell(cols[7], 6, f"{total_taxable:,.2f}", border=1, align='R', new_x='LMARGIN', new_y='NEXT')
    
    # Totals Section
    taxable_val = total_taxable + del_charges
    cgst = taxable_val * 0.09
    sgst = taxable_val * 0.09
    grand_total = round(taxable_val + cgst + sgst)
    
    amount_text = f"{num_to_words(grand_total)}"
    words = amount_text.split()
    amount_words_list = []
    cur_line = ""
    for w in words:
        if pdf.get_string_width(cur_line + w + " ") < 115:
            cur_line += w + " "
        else:
            amount_words_list.append(cur_line)
            cur_line = w + " "
    amount_words_list.append(cur_line)
    
    def fmt(v): return f"{v:,.2f}"
    
    pdf.cell(120, 5, "Total Invoice Amount in Words:", border='L', align='L')
    pdf.cell(46, 5, "Total Amount Before Tax", border='L', align='L')
    pdf.cell(24, 5, fmt(total_taxable), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    
    txt = amount_words_list[0] if len(amount_words_list) > 0 else ""
    pdf.cell(120, 5, f"  {txt}", border='L', align='L')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(46, 5, "Delivery Charges", border='L', align='L')
    pdf.cell(24, 5, fmt(del_charges), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('helvetica', 'B', 8)
    txt = amount_words_list[1] if len(amount_words_list) > 1 else ""
    pdf.cell(120, 5, f"  {txt}", border='L', align='L')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(46, 5, "Taxable Value", border='L', align='L')
    pdf.cell(24, 5, fmt(taxable_val), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('helvetica', 'B', 8)
    txt = amount_words_list[2] if len(amount_words_list) > 2 else ""
    pdf.cell(120, 5, f"  {txt}", border='L', align='L')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(46, 5, "Add: CGST @ 9%", border='L', align='L')
    pdf.cell(24, 5, fmt(cgst), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    
    pdf.cell(120, 5, "", border='L', align='L')
    pdf.cell(46, 5, "Add: SGST @ 9%", border='L', align='L')
    pdf.cell(24, 5, fmt(sgst), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(120, 6, "", border='L', align='L')
    pdf.cell(46, 6, "Grand Total", border='L', align='L')
    pdf.cell(24, 6, fmt(grand_total), border='LR', align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # Bank Details
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(100, 5, "Bank Details :", border='L', align='L')
    pdf.set_font('helvetica', '', 7)
    pdf.cell(90, 5, "Certified that the particulars given above are true and correct.", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 8)
    pdf.cell(100, 5, "HDFC Bank Ltd. | A/c No.: 00082000057539", border='L', align='L')
    pdf.set_font('helvetica', 'B', 8)
    pdf.cell(90, 5, "For MURLI STEEL CORPORATION", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 8)
    pdf.cell(100, 5, "Branch: Sree Bhumi | IFSC: HDFC0004566", border='L', align='L')
    pdf.cell(90, 5, "", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.cell(100, 5, "", border='L', align='L')
    pdf.cell(90, 5, "", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('helvetica', '', 7)
    pdf.cell(100, 5, "Goods once sold will not be taken back. E & O.E.", border='L', align='L')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(90, 5, "Authorised Signatory", border='R', align='L', new_x='LMARGIN', new_y='NEXT')
    
    pdf.rect(10, 10, 190, pdf.get_y() - 10)
    return pdf.output()

