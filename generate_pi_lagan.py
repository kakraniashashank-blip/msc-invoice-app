"""
Generate Proforma Invoice for Lagan Engineering Co. Ltd.
Based on Purchase Order P/2627/1633 dated 7-Sep-26
"""
import os
import sys

# Add current dir to path so we can import pdf_generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_generator import generate_invoice_pdf

# --- Client Info ---
client_name = "Lagan Engineering Co. Ltd."
client_info = {
    "address": "14 Mohd. Ishaque Road, Kolkata - 700016",
    "gstin": "19AAACT9986F1ZP",
    "state": "West Bengal   Code: 19",
    "delivery": "Lagan Engineering Co. Ltd., 14 Mohd. Ishaque Road, Kolkata 700016"
}

# --- Invoice Details ---
doc_type = "PROFORMA INVOICE"
inv_no = "PI/07/2026-27"
inv_date = "29-09-2026"
order_no = "P/2627/1633"
order_date = "7-Sep-26"
vehicle_no = ""
payment_terms = ""

# --- Products master (for HSN lookup) ---
products = {
    "09112BL": {"description": "BRIGHT M.S. 1-3/4\" DIA. (TOL. ON DIA. -0.002\"/-0.005\"). LENGTH: 19-20 FT", "hsn": "721550"},
    "09118BL": {"description": "BRIGHT M.S. 1/2\" DIA. (TOL. ON DIA. -0.001\"/-0.003\"). LENGTH: 18-20 FT", "hsn": "721550"},
    "09304BL": {"description": "BRIGHT M.S. 7/8\" DIA. (TOL. ON DIA. -0.001\"/-0.003\"). LENGTH: 11-15 FT", "hsn": "721550"},
    "09246BL": {"description": "M.S. CHANNEL 3\" X 1-1/2\" (75X40MM), LENGTH: 20-22 FT", "hsn": "721610"},
    "09256BL": {"description": "M.S. CHANNEL 4\" X 2\" (100X50MM), LENGTH: MUST BE 18 FEET", "hsn": "721610"},
    "09427BL": {"description": "M.S. ANGLE 3\" X 3\" X 1/4\" (75X75X6 MM), LENGTH: 18-20 FT", "hsn": "721610"},
    "09307BL": {"description": "0.820\" A/F HEXAGONAL BR. MS BAR, LENGTH: 8-10 FEET", "hsn": "721550"},
    "09158BL": {"description": "BRIGHT M.S. GB 45MM DIA., LENGTH: 20 FT", "hsn": "721550"},
    "09111BL": {"description": "BRIGHT M.S. 1-1/4\" DIA. (TOL. ON DIA. -0.002\"/-0.005\"). LENGTH: 20-21 FT", "hsn": "721550"},
    "09393BL": {"description": "BRIGHT M.S. FLAT 31MM OR 32MM X 12MM", "hsn": "721550"},
    "09083BL": {"description": "BRIGHT M.S. 1-31/32\" (50MM) DIA. (TOL. ON DIA. -0.001\"/-0.004\"). LENGTH: 20-22 FT", "hsn": "721550"},
    "09113BL": {"description": "BRIGHT M.S. 2\" DIA. (TOL. ON DIA. +0.005\"/+0.008\"). LENGTH: 19-20 FT", "hsn": "721550"},
    "09283BL": {"description": "BRIGHT M.S. 1-1/2\" DIA. (TOL. ON DIA. -0.002\"/-0.005\"). LENGTH: 18-20 FT", "hsn": "721550"},
    "09816BL": {"description": "1.3/8\" DIA BRIGHT CLASS IV STEEL (G.B)", "hsn": "721550"},
}

# --- All 14 Items from the Purchase Order ---
items = [
    # Page 1 Items (1-10)
    {"code": "09112BL", "desc": "BR.MS. 1-3/4\" DIA. (TOL. ON DIA. -0.002\"/-0.005\"). LENGTH:19-20 FT", "hsn": "721550", "pcs": 0, "qty": 1400.0, "rate": 73.00},
    {"code": "09118BL", "desc": "BR. MS. 1/2\" DIA. (TOL. ON DIA. -0.001\"/-0.003\"). LEN:18 TO 20FT", "hsn": "721550", "pcs": 0, "qty": 300.0, "rate": 74.00},
    {"code": "09304BL", "desc": "BR. MS. 7/8\" DIA. (TOL. ON DIA. -0.001\"/-0.003\"). LEN:11-15FT", "hsn": "721550", "pcs": 0, "qty": 300.0, "rate": 73.00},
    {"code": "09246BL", "desc": "M.S.CHANNEL 3 X1-1/2\" (75X40MM), LEN:20-22 FT", "hsn": "721610", "pcs": 0, "qty": 1500.0, "rate": 61.00},
    {"code": "09256BL", "desc": "M.S.CHANNEL 4\"X 2\"(100 X 50MM), LEN: MUST BE 18 FEET", "hsn": "721610", "pcs": 0, "qty": 300.0, "rate": 61.00},
    {"code": "09427BL", "desc": "M.S.ANGLE 3\"X3\"X1/4\" (75X75X6 MM), LEN: 18-20FT", "hsn": "721610", "pcs": 0, "qty": 900.0, "rate": 61.00},
    {"code": "09307BL", "desc": "0.820\"A/F HEXOGONAL BAR LENGTH:8 TO10FEET", "hsn": "721550", "pcs": 0, "qty": 300.0, "rate": 73.00},
    {"code": "09158BL", "desc": "BRIGHT M.S.GB 45MM DIA. -LTH = 20 FT", "hsn": "721550", "pcs": 0, "qty": 1000.0, "rate": 73.00},
    {"code": "09111BL", "desc": "BR. MS. 1-1/4\"DIA. (TOL. ON DIA. -0.002\"/-0.005\") LEN:20-21FT", "hsn": "721550", "pcs": 0, "qty": 400.0, "rate": 73.00},
    {"code": "09393BL", "desc": "BRIGHT M.S.FLAT 31mm OR 32mm X 12MM", "hsn": "721550", "pcs": 0, "qty": 200.0, "rate": 73.00},
    # Page 2 Items (11-14)
    {"code": "09083BL", "desc": "BR.MS 1-31/32\"(50MM) (TOL. ON DIA. -0.001\"/-0.004\"), LEN: 20-22 FT", "hsn": "721550", "pcs": 0, "qty": 500.0, "rate": 73.00},
    {"code": "09113BL", "desc": "BR. MS. 2\"DIA., (TOL ON DIA. +0.005\"/+0.008\"), LEN:19-20FT", "hsn": "721550", "pcs": 0, "qty": 1000.0, "rate": 73.00},
    {"code": "09283BL", "desc": "BR. M.S.1-1/2\" DIA. (TOL. ON DIA. -0.002\"/-0.005\"), LEN:18-20FT", "hsn": "721550", "pcs": 0, "qty": 4000.0, "rate": 73.00},
    {"code": "09816BL", "desc": "1.3/8\" DIA BRIGHT CLASS IV STEEL(G.B)", "hsn": "721550", "pcs": 0, "qty": 2500.0, "rate": 88.00},
]

del_charges = 0.0

# --- Generate PDF ---
pdf_bytes = generate_invoice_pdf(
    doc_type=doc_type,
    inv_no=inv_no,
    inv_date=inv_date,
    client_name=client_name,
    client_info=client_info,
    order_no=order_no,
    order_date=order_date,
    vehicle_no=vehicle_no,
    payment_terms=payment_terms,
    items=items,
    del_charges=del_charges,
    products=products,
)

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PI_07_2026-27_Lagan.pdf")
with open(output_path, "wb") as f:
    f.write(pdf_bytes)

# Also print a summary
total_qty = sum(i["qty"] for i in items)
total_taxable = sum(i["qty"] * i["rate"] for i in items)
taxable_val = total_taxable + del_charges
cgst = taxable_val * 0.09
sgst = taxable_val * 0.09
grand_total = round(taxable_val + cgst + sgst)

print("Proforma Invoice generated successfully!")
print(f"File: {output_path}")
print("")
print("Summary:")
print(f"   Client: {client_name}")
print(f"   PO Ref: {order_no} dated {order_date}")
print(f"   Items: {len(items)}")
print(f"   Total Qty: {total_qty:,.3f} KG")
print(f"   Total Before Tax: Rs.{total_taxable:,.2f}")
print(f"   CGST @9%: Rs.{cgst:,.2f}")
print(f"   SGST @9%: Rs.{sgst:,.2f}")
print(f"   Grand Total: Rs.{grand_total:,.2f}")
