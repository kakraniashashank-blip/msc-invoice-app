import streamlit as st
import json
from xhtml2pdf import pisa
from io import BytesIO
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
    img = Image.open(image_file)
    response = model.generate_content([prompt, img])
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)

# -------------------------------------------------------------
# Streamlit App UI
# -------------------------------------------------------------
st.title("📄 Murli Steel Invoicer")

doc_type = st.radio("Document Type", ["PROFORMA INVOICE", "TAX INVOICE"], horizontal=True)
inv_no = st.text_input("Invoice Number", value="PI/07/2026-27" if doc_type == "PROFORMA INVOICE" else "MSC/20/2026-27")
inv_date = st.text_input("Invoice Date", value=date.today().strftime("%d-%m-%Y"))

uploaded_file = st.file_uploader("📷 Snap Photo or Upload Bill", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    if "extracted_data" not in st.session_state or st.button("🔄 Re-Scan Image"):
        with st.spinner("Analyzing document..."):
            st.session_state.extracted_data = extract_bill_details(uploaded_file)

    data = st.session_state.extracted_data
    
    st.subheader("Step 1: Check Details")
    c1, c2 = st.columns(2)
    order_no = c1.text_input("Order No.", value=data.get("order_no", ""))
    order_date = c2.text_input("Order Date", value=data.get("order_date", ""))
    del_charges = st.number_input("Delivery Charges (₹)", value=float(data.get("delivery_charges", 0.0)))
    
    st.write("**Items List (Tap any box to adjust):**")
    edited_items = []
    for i, itm in enumerate(data.get("items", []), 1):
        with st.expander(f"Item #{i} - {itm.get('code', '')}", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            code = col_a.text_input(f"Code #{i}", value=itm.get("code", ""), key=f"c_{i}")
            qty = col_b.number_input(f"Qty (kg) #{i}", value=float(itm.get("qty", 0.0)), key=f"q_{i}")
            rate = col_c.number_input(f"Rate (₹/kg) #{i}", value=float(itm.get("rate", 0.0)), key=f"r_{i}")
            edited_items.append({"code": code, "qty": qty, "rate": rate, "pcs": itm.get("pcs", "")})

    # Calculations
    total_taxable = sum(it["qty"] * it["rate"] for it in edited_items)
    taxable_val = total_taxable + del_charges
    cgst = taxable_val * 0.09
    sgst = taxable_val * 0.09
    grand_total = taxable_val + cgst + sgst
    
    st.markdown("---")
    st.write(f"**Total Before Tax:** ₹{total_taxable:,.2f}")
    st.write(f"**Taxable Value:** ₹{taxable_val:,.2f}")
    st.write(f"### **Grand Total:** ₹{grand_total:,.2f}")

