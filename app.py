import streamlit as st
import json
import google.generativeai as genai
from PIL import Image
from datetime import date

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
st.set_page_config(page_title="MSC Invoice Generator", page_icon="📑", layout="centered")

# Get API key from Streamlit secrets or environment
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_input = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if api_key_input:
        genai.configure(api_key=api_key_input)

# Master item descriptions lookup
MASTER_DESCRIPTIONS = {
    "09083BL": 'BRIGHT M.S. 1.31/32" (50MM) DIA. TOLERANCE -0.001"/-0.004" (En3B-BS970:1955)',
    "09118BL": 'BRIGHT M.S. 1/2" DIA. TOLERANCE ON DIA. -0.001"/-0.003". LENGTH: 18-20 FEET (En3B-BS970:1955)',
    "09119BL": 'BRIGHT M.S. 5/8" DIA. TOLERANCE ON DIA. -0.001"/-0.003". LENGTH: 18-20 FEET (En3B-BS970:1955)',
    "09304BL": 'BRIGHT M.S. 7/8" DIA. TOLERANCE ON DIA. -0.001"/-0.003". LENGTH: 11-15 FEET (En3B-BS970:1955)',
    "09113BL": 'BRIGHT M.S. 2" DIA. TOLERANCE ON DIA. +0.005"/+0.008". LENGTH: 18.5 FEET (En3B-BS970:1955)',
    "09114BL": 'BRIGHT M.S. 2.1/4" DIA. TOLERANCE ON DIA. +0.005"/+0.008". LENGTH: 18.5 FEET (En3B-BS970:1955)',
    "09283BL": 'BRIGHT M.S. 1.1/2" DIA. TOLERANCE ON DIA. -0.002"/-0.005". LENGTH: 18-20 FEET (En3B-BS970:1955)',
    "09822BL": 'BRIGHT CK45 STEEL - 2.1/4" DIA. GB TOL ON OD +0.014"/+0.018", HARDNESS 204 TO 249 BHN',
    "09158BL": 'BRIGHT M.S. GB 45MM DIA. TOLERANCE ON DIA.',
    "09110BL": 'BRIGHT M.S. 1" DIA. TOLERANCE -0.005"/-0.008". LENGTH: 8-12 FT (En3B-BS970:1955)',
    "09111BL": 'BRIGHT MS 1.1/4" DIA. TOLERANCE -0.002"/-0.005". LENGTH: 20-21 FEET (En3B-BS970:1955)',
    "09337BL": 'BRIGHT M.S. 3/4" DIA. TOLERANCE -0.001"/-0.003". LENGTH: 8-12 FT (En3B-BS970:1955)',
    "09828BL": 'BRIGHT CK-45, 1.5/8" GB+',
    "09816BL": '1.3/8" DIA BRIGHT CLASS IV STEEL (G.B) TOL ON DIA +0.008"/+0.012"',
    "09246BL": 'M.S. CHANNEL 3" X 1.1/2" (75X40MM), LENGTH: 20-22 FT',
    "09256BL": 'M.S. CHANNEL 4" X 2" (100X50MM)',
    "09427BL": 'M.S. ANGLE 3" X 3" X 1/4" (75X75X6 MM)'
}

HSN_CODES = {
    "09246BL": "721610", "09256BL": "721610", "09427BL": "721610"
}

CLIENT_DATABASE = {
    "Lagan Engineering Co. Ltd.": {
        "Address": "14 KYD Street, Kolkata - 700016",
        "GSTIN": "19AAACT9986F1ZP",
        "State": "West Bengal   Code: 19",
        "Delivery": "Lagan Engineering Co. Ltd., c/o Angus Jute Mills, Bhadeshwar, W.B."
    },
    "Birla Corporation Ltd., Unit Birla Jute Mill": {
        "Address": "9/1 R.N. Mukherjee Road, Kolkata 700001",
        "GSTIN": "19AABCB2075J1ZN",
        "State": "West Bengal   Code: 19",
        "Delivery": "Birla Jute Mill, P.O.Birlapur, 24 Parganas, West Bengal"
    }
}

def num_to_words(num):
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def two_digits(n):
        if n < 20: return units[n]
        return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")

    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    crore = rupees // 10000000; rupees %= 10000000
    lakh = rupees // 100000; rupees %= 100000
    thousand = rupees // 1000; rupees %= 1000
    hundred = rupees // 100; rupees %= 100
    
    parts = []
    if crore > 0: parts.append(two_digits(crore) + " Crore")
    if lakh > 0: parts.append(two_digits(lakh) + " Lakh")
    if thousand > 0: parts.append(two_digits(thousand) + " Thousand")
    if hundred > 0: parts.append(two_digits(hundred) + " Hundred")
    if rupees > 0: parts.append(two_digits(rupees))
    
    words = " ".join(parts) + " Rupees"
    if paise > 0: words += f" and {two_digits(paise)} Paise"
    return words + " Only"

def extract_bill_details(image_file):
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = """
    Extract all billing and item details from this bill/PO into a clean JSON structure:
    {
      "order_no": "P/2627/1552",
      "order_date": "07-08-2026",
      "delivery_charges": 16500,
      "vehicle_no": "WB 23C 1234",
      "items": [
        {
          "code": "09083BL",
          "pcs": 0,
          "qty": 560.0,
          "rate": 70.0
        }
      ]
    }
    Extract handwritten overrides if present. Return ONLY valid JSON.
    """
    
    # Send directly to Gemini without extra libraries
    if image_file.name.lower().endswith('.pdf'):
        payload = [prompt, {"mime_type": "application/pdf", "data": image_file.getvalue()}]
    else:
        img = Image.open(image_file)
        payload = [prompt, img]

    response = model.generate_content(payload)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except Exception:
        return {}

# -------------------------------------------------------------
# Streamlit App UI
# -------------------------------------------------------------
st.title("📄 Murli Steel Invoicer")

doc_type = st.radio("Document Type", ["PROFORMA INVOICE", "TAX INVOICE", "QUOTATION"], horizontal=True)

if doc_type == "PROFORMA INVOICE":
    default_inv = "PI/07/2026-27"
elif doc_type == "TAX INVOICE":
    default_inv = "MSC/20/2026-27"
else:
    default_inv = "QT/07/2026-27"

inv_no = st.text_input("Document Number", value=default_inv)
inv_date = st.text_input("Invoice Date", value=date.today().strftime("%d-%m-%Y"))

selected_client_name = st.selectbox("Select Client", list(CLIENT_DATABASE.keys()))
client_info = CLIENT_DATABASE[selected_client_name]

if "Lagan" in selected_client_name:
    default_terms = "Proforma invoice"
elif "Birla" in selected_client_name:
    default_terms = "30 days"
else:
    default_terms = doc_type

payment_terms = st.text_input("Payment Terms", value=default_terms)

uploaded_file = st.file_uploader("📷 Snap Photo or Upload Bill", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    if "extracted_data" not in st.session_state or st.button("🔄 Re-Scan Image"):
        with st.spinner("Analyzing document..."):
            extracted = extract_bill_details(uploaded_file)
            if not extracted:
                st.error("Couldn't read the document clearly. Try a clearer image or manually enter details.")
                st.session_state.extracted_data = {"items": []}
            else:
                if "items" not in extracted:
                    extracted["items"] = []
                st.session_state.extracted_data = extracted

    data = st.session_state.extracted_data
    if "items" not in data:
        data["items"] = []
    
    st.subheader("Step 1: Check Details")
    c1, c2 = st.columns(2)
    order_no = c1.text_input("Order No.", value=data.get("order_no", ""))
    order_date = c2.text_input("Order Date", value=data.get("order_date", ""))
    del_charges = st.number_input("Delivery Charges (₹)", value=float(data.get("delivery_charges", 0.0)))
    vehicle_no = st.text_input("Vehicle No.", value=data.get("vehicle_no", ""))
    
    data["order_no"] = order_no
    data["order_date"] = order_date
    data["delivery_charges"] = del_charges
    data["vehicle_no"] = vehicle_no
    
    st.write("**Items List (Tap any box to adjust):**")
    
    items_list = data["items"]
    edited_items = []
    
    for i, itm in enumerate(items_list):
        with st.expander(f"Item #{i+1} - {itm.get('code', '')}", expanded=True):
            col_a, col_b = st.columns([1, 3])
            code = col_a.text_input("Code", value=itm.get("code", ""), key=f"code_{i}")
            
            # Default desc mapping if empty
            default_desc = itm.get("desc", "")
            if not default_desc:
                default_desc = MASTER_DESCRIPTIONS.get(code, code)
                
            desc = col_b.text_input("Description", value=default_desc, key=f"desc_{i}")
            
            col_c, col_d, col_e = st.columns(3)
            pcs = col_c.text_input("Pcs", value=str(itm.get("pcs", "")), key=f"pcs_{i}")
            qty = col_d.number_input("Qty (kg)", value=float(itm.get("qty", 0.0)), key=f"qty_{i}")
            rate = col_e.number_input("Rate (₹/kg)", value=float(itm.get("rate", 0.0)), key=f"rate_{i}")
            
            # Update source of truth so edits persist
            itm["code"] = code
            itm["desc"] = desc
            itm["pcs"] = pcs
            itm["qty"] = qty
            itm["rate"] = rate
            
            edited_items.append(itm)
            
            if st.button("🗑️ Delete this item", key=f"delete_{i}"):
                items_list.pop(i)
                st.rerun()

    if st.button("➕ Add New Item"):
        items_list.append({
            "code": "",
            "desc": "",
            "pcs": "",
            "qty": 0.0,
            "rate": 0.0
        })
        st.rerun()

    # Calculations
    del_charges = data["delivery_charges"]
    total_taxable = sum(it["qty"] * it["rate"] for it in edited_items)
    taxable_val = total_taxable + del_charges
    cgst = taxable_val * 0.09
    sgst = taxable_val * 0.09
    grand_total = taxable_val + cgst + sgst
    
    st.markdown("---")
    st.write(f"**Total Before Tax:** ₹{total_taxable:,.2f}")
    st.write(f"**Taxable Value:** ₹{taxable_val:,.2f}")
    st.write(f"### **Grand Total:** ₹{grand_total:,.2f}")

    if st.button("✅ Generate PDF", type="primary", use_container_width=True):
        try:
            from weasyprint import HTML
        except Exception as e:
            st.error("PDF generation is disabled on Windows. Please push to GitHub to use this feature on Streamlit Cloud.")
            st.stop()
            
        rows_html = ""
        for idx, itm in enumerate(edited_items, 1):
            hsn = HSN_CODES.get(itm['code'], "721550")
            tax_val = itm['qty'] * itm['rate']
            rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{itm['code']}</td>
                <td style="text-align: left; font-size: 9px;">{itm['desc']}</td>
                <td>{hsn}</td>
                <td>{itm.get('pcs', '')}</td>
                <td>{itm['qty']:,.2f}</td>
                <td style="text-align: right;">{itm['rate']:,.2f}</td>
                <td style="text-align: right;">{tax_val:,.2f}</td>
            </tr>
            """

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            * {{ box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; font-size: 11px; margin: 0; padding: 0; color: #000; }}
            .invoice-box {{ border: 1px solid #000; width: 100%; }}
            .header {{ text-align: center; border-bottom: 1px solid #000; padding: 5px; }}
            .company-name {{ font-size: 24px; font-weight: bold; color: #003399; margin: 5px 0; }}
            .info-table {{ width: 100%; border-collapse: collapse; border-bottom: 1px solid #000; }}
            .info-table td {{ border: 1px solid #000; padding: 4px; vertical-align: top; }}
            .section-title {{ text-align: center; font-weight: bold; background-color: #f0f0f0; }}
            .items-table {{ width: 100%; border-collapse: collapse; }}
            .items-table th, .items-table td {{ border: 1px solid #000; padding: 4px; text-align: center; }}
            .items-table th {{ background-color: #f0f0f0; font-size: 10px; }}
            .min-height-row td {{ height: 100px; }}
            .totals-box {{ width: 40%; float: right; border-collapse: collapse; }}
            .totals-box td {{ border: 1px solid #000; padding: 4px; text-align: right; }}
            .footer-table {{ width: 100%; border-collapse: collapse; border-top: 1px solid #000; }}
            .footer-table td {{ padding: 4px; vertical-align: top; }}
            .clear {{ clear: both; }}
        </style>
        </head>
        <body>
        <div class="invoice-box">
            
            <div class="header">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="width:33%; border: none;"></td>
                        <td style="width:34%; text-align:center; border: none;">
                            <span style="border: 1px solid #000; padding: 2px 10px; font-weight: bold; font-size:12px;">{doc_type}</span>
                        </td>
                        <td style="width:33%; text-align:right; font-size:10px; border: none;">Original for Buyer/ Seller</td>
                    </tr>
                </table>
                <div class="company-name">MURLI STEEL CORPORATION</div>
                <div style="font-size:11px;">9/12, Lal Bazar Street, Mercantile Building, 'B' Block, 1st Floor, Kolkata - 700001, India</div>
                <div style="font-size:11px;">Phone: (033) 2210 1650 | Mobile: 9830242818 | Email: shradkakrania@gmail.com</div>
                <div style="font-weight:bold; font-size:12px; margin-top:5px;">PAN: AKAPK4846L | GSTIN: 19AKAPK4846L1ZS</div>
            </div>

            <table class="info-table">
                <tr>
                    <td style="width: 50%;" class="section-title">BILLED TO PARTY</td>
                    <td style="width: 50%;" class="section-title">INVOICE DETAILS</td>
                </tr>
                <tr>
                    <td style="padding:0;">
                        <table style="width:100%; border-collapse:collapse;">
                            <tr><td style="width:25%; border:none; padding:3px;">Name:</td><td style="border:none; padding:3px; font-weight:bold;">{selected_client_name}</td></tr>
                            <tr><td style="border:none; padding:3px;">Address:</td><td style="border:none; padding:3px;">{client_info['Address']}</td></tr>
                            <tr><td style="border:none; padding:3px;">GSTIN:</td><td style="border:none; padding:3px; font-weight:bold;">{client_info['GSTIN']}</td></tr>
                            <tr><td style="border:none; padding:3px;">Order No.:</td><td style="border:none; padding:3px;">{order_no}</td></tr>
                            <tr><td style="border:none; padding:3px;">Order Date:</td><td style="border:none; padding:3px;">{order_date}</td></tr>
                            <tr><td style="border:none; padding:3px;">State:</td><td style="border:none; padding:3px;">{client_info['State']}</td></tr>
                        </table>
                    </td>
                    <td style="padding:0;">
                        <table style="width:100%; border-collapse:collapse;">
                            <tr><td style="width:35%; border:none; padding:3px;">Invoice No.:</td><td style="border:none; padding:3px; font-weight:bold;">{inv_no}</td></tr>
                            <tr><td style="border:none; padding:3px;">Invoice Date:</td><td style="border:none; padding:3px; font-weight:bold;">{inv_date}</td></tr>
                            <tr><td style="border:none; padding:3px;">Terms:</td><td style="border:none; padding:3px;">{payment_terms}</td></tr>
                            <tr><td style="border:none; padding:3px;">Supply:</td><td style="border:none; padding:3px;">West Bengal</td></tr>
                        </table>
                    </td>
                </tr>
            </table>

            <table class="info-table" style="border-top:none;">
                <tr>
                    <td style="width: 55%; border-top:none;">Delivery At: {client_info['Delivery']}</td>
                    <td style="width: 20%; border-top:none;">Transport: Lorry</td>
                    <td style="width: 25%; border-top:none;">Vehicle No. : {vehicle_no}</td>
                </tr>
            </table>

            <table class="items-table" style="border-top:none;">
                <tr>
                    <th style="width: 4%;">SN</th>
                    <th style="width: 14%;">Item Code</th>
                    <th style="width: 38%;">Description</th>
                    <th style="width: 8%;">HSN</th>
                    <th style="width: 6%;">Pcs</th>
                    <th style="width: 10%;">Qty</th>
                    <th style="width: 8%;">Rate</th>
                    <th style="width: 12%;">Value (INR)</th>
                </tr>
                {rows_html}
                <tr class="min-height-row">
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                    <td style="border-bottom:none; border-top:none;"></td>
                </tr>
                <tr>
                    <td colspan="4" style="text-align: right; font-weight: bold;">TOTAL:</td>
                    <td></td>
                    <td style="font-weight: bold;">{sum(it['qty'] for it in edited_items):,.2f}</td>
                    <td></td>
                    <td style="font-weight: bold; text-align: right;">{total_taxable:,.2f}</td>
                </tr>
            </table>

            <div style="width: 100%;">
                <div style="width: 55%; float: left; padding: 10px;">
                    <div style="font-weight:bold;">Total Invoice Amount in Words:</div>
                    <div style="margin-top: 5px;">{num_to_words(grand_total)}</div>
                </div>
                <table class="totals-box">
                    <tr><td style="text-align: left;">Total Amount Before Tax</td><td style="width: 40%;">{total_taxable:,.2f}</td></tr>
                    <tr><td style="text-align: left;">Delivery Charges</td><td>{del_charges:,.2f}</td></tr>
                    <tr><td style="text-align: left;">Taxable Value</td><td>{taxable_val:,.2f}</td></tr>
                    <tr><td style="text-align: left;">Add: CGST @ 9%</td><td>{cgst:,.2f}</td></tr>
                    <tr><td style="text-align: left;">Add: SGST @ 9%</td><td>{sgst:,.2f}</td></tr>
                    <tr style="background-color: #f0f0f0;"><td style="text-align: left; font-weight:bold;">Grand Total</td><td style="font-weight:bold;">{grand_total:,.2f}</td></tr>
                </table>
                <div class="clear"></div>
            </div>

            <table class="footer-table">
                <tr>
                    <td style="width: 50%; border-right: 1px solid #000; padding: 8px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">Bank Details :</div>
                        <div>HDFC Bank Ltd. | A/c No.: 00082000057539</div>
                        <div>Branch: Sree Bhumi | IFSC: HDFC0004566</div>
                        <div style="margin-top: 15px; font-size: 9px;">Goods once sold will not be taken back. E & O.E.</div>
                    </td>
                    <td style="width: 50%; text-align: left; padding: 8px; padding-left: 20px;">
                        <div style="font-size: 10px;">Certified that the particulars given above are true and correct.</div>
                        <div style="font-weight: bold; margin-top: 10px;">For MURLI STEEL CORPORATION</div>
                        <div style="margin-top: 35px;">Authorised Signatory</div>
                    </td>
                </tr>
            </table>
        </div>
        </body>
        </html>
        """
        
        pdf_bytes = HTML(string=full_html).write_pdf()
        st.download_button(
            label="📥 Download / Share PDF",
            data=pdf_bytes,
            file_name=f"{inv_no.replace('/', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )