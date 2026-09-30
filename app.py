import streamlit as st
import json
import uuid
import os
import sys
from datetime import date
import google.generativeai as genai

# Disable QuickEdit mode on Windows to prevent the app from freezing
if os.name == 'nt':
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        STD_INPUT_HANDLE = -10
        handle = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value &= ~0x0040  # Remove ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(handle, mode)
    except Exception:
        pass

from extraction import extract_bill_details

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
st.set_page_config(page_title="MSC Invoice Generator", page_icon="📑", layout="centered")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")

# -------------------------------------------------------------
# Data Helpers
# -------------------------------------------------------------
def load_json(path):
    """Load a JSON file. Returns empty dict if file not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(path, data):
    """Save data to a JSON file, creating directories if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_products():
    """Load the products master list (not cached — can be updated at runtime)."""
    return load_json(PRODUCTS_FILE)

def load_clients():
    """Load the clients database."""
    return load_json(CLIENTS_FILE)

# -------------------------------------------------------------
# Gemini API Configuration
# -------------------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_input = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if api_key_input:
        genai.configure(api_key=api_key_input)

# -------------------------------------------------------------
# Load Business Data
# -------------------------------------------------------------
clients = load_clients()
products = load_products()

# ============================================================
# CRITICAL: Process pending extraction BEFORE widgets render
# This is the fix for StreamlitWidgetAlreadyInstantiatedError
# ============================================================
if "_pending_extraction" in st.session_state:
    ext = st.session_state.pop("_pending_extraction")

    # Only fill fields that are currently empty/default
    if ext.get("order_no") and not st.session_state.get("order_no"):
        st.session_state["order_no"] = str(ext["order_no"])
    if ext.get("order_date") and not st.session_state.get("order_date"):
        st.session_state["order_date"] = str(ext["order_date"])
    if ext.get("vehicle_no") and not st.session_state.get("vehicle_no"):
        st.session_state["vehicle_no"] = str(ext["vehicle_no"])
    if ext.get("payment_terms") and not st.session_state.get("payment_terms"):
        st.session_state["payment_terms"] = str(ext["payment_terms"])

    # Delivery charges
    raw_del = ext.get("delivery_charges", 0)
    try:
        dval = float(raw_del) if raw_del not in (None, "") else 0.0
    except (ValueError, TypeError):
        dval = 0.0
    if dval != 0.0 and st.session_state.get("del_charges", 0.0) == 0.0:
        st.session_state["del_charges"] = dval

    # Process extracted items
    new_items = ext.get("items", [])
    learned_count = 0
    if new_items:
        for item in new_items:
            # Assign a unique ID to each item (prevents index-based key collision)
            item["id"] = str(uuid.uuid4())

            code = str(item.get("code", "")).strip().upper()
            item["code"] = code

            # Ensure numeric types
            try:
                item["qty"] = float(item.get("qty", 0) or 0)
            except (ValueError, TypeError):
                item["qty"] = 0.0
            try:
                item["rate"] = float(item.get("rate", 0) or 0)
            except (ValueError, TypeError):
                item["rate"] = 0.0

            # Look up description from master list, or use extracted description
            extracted_desc = str(item.get("desc", "")).strip()
            master_entry = products.get(code, {})
            if master_entry.get("description"):
                item["desc"] = master_entry["description"]
            elif extracted_desc:
                item["desc"] = extracted_desc
            else:
                item["desc"] = code

            # Look up HSN from master list
            item["hsn"] = master_entry.get("hsn", "721550")

            # Auto-learn: add new items to the master list
            if code and code not in products:
                products[code] = {
                    "description": extracted_desc if extracted_desc else code,
                    "hsn": "721550"
                }
                learned_count += 1

        if learned_count > 0:
            save_json(PRODUCTS_FILE, products)
            st.toast(f"📚 Learned {learned_count} new item(s) for next time!")

        if "items_list" not in st.session_state:
            st.session_state["items_list"] = []
        st.session_state["items_list"].extend(new_items)

    st.toast("✅ Data extracted successfully!")

# -------------------------------------------------------------
# Initialize Session State Defaults
# -------------------------------------------------------------
defaults = {
    "order_no": "",
    "order_date": "",
    "vehicle_no": "",
    "payment_terms": "",
    "del_charges": 0.0,
    "items_list": [],
}
for key, default_val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

# ============================================================
# UI
# ============================================================
st.title("📄 Murli Steel Invoicer")

# --- Document Configuration ---
doc_type = st.radio(
    "Document Type",
    ["PROFORMA INVOICE", "TAX INVOICE", "QUOTATION"],
    horizontal=True,
)

if doc_type == "PROFORMA INVOICE":
    default_inv = "PI/07/2026-27"
elif doc_type == "TAX INVOICE":
    default_inv = "MSC/20/2026-27"
else:
    default_inv = "QT/07/2026-27"

c_doc1, c_doc2 = st.columns(2)
inv_no = c_doc1.text_input("Document Number", value=default_inv)
inv_date = c_doc2.text_input("Invoice Date", value=date.today().strftime("%d-%m-%Y"))

selected_client_name = st.selectbox("Select Client", list(clients.keys()) if clients else ["No clients configured"])
client_info = clients.get(selected_client_name, {})

# --- Order & Delivery Details (all editable) ---
st.subheader("Step 1: Order & Delivery Details")
c1, c2, c3 = st.columns(3)
order_no = c1.text_input("Order No.", key="order_no")
order_date = c2.text_input("Order Date", key="order_date")
vehicle_no = c3.text_input("Vehicle No.", key="vehicle_no")

c4, c5 = st.columns(2)
payment_terms = c4.text_input("Payment Terms", key="payment_terms")
del_charges = c5.number_input("Delivery Charges (₹)", key="del_charges", min_value=0.0, format="%.2f")

# --- Upload & Scan ---
st.subheader("Step 2: Upload Bills (Optional)")
uploaded_files = st.file_uploader(
    "📷 Snap Photos or Upload Bills",
    type=["jpg", "jpeg", "png", "pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.button("🔄 Scan Images & Extract Data", use_container_width=True):
        with st.spinner("Analyzing documents with Gemini AI..."):
            extracted = extract_bill_details(uploaded_files)
            if extracted:
                # Store extraction for processing on next rerun (BEFORE widgets)
                st.session_state["_pending_extraction"] = extracted
                st.rerun()
            else:
                st.warning("Could not extract data. Please enter details manually.")

# --- Items List (fully editable) ---
st.subheader("Step 3: Items List")
st.caption("**Tap any field to edit. All fields are fully editable.**")

# Reload products in case new items were learned
products = load_products()

edited_items = []
items_to_delete = None

for i, itm in enumerate(st.session_state.items_list):
    item_id = itm.get("id", str(uuid.uuid4()))
    itm["id"] = item_id  # ensure every item has an ID

    with st.expander(f"Item #{i + 1} — {itm.get('code', 'New Item')}", expanded=True):
        col_a, col_b = st.columns([1, 3])
        code = col_a.text_input("Code", value=itm.get("code", ""), key=f"code_{item_id}")

        # Look up description: use current value, or master list, or code
        current_desc = itm.get("desc", "")
        if not current_desc or current_desc == itm.get("code", ""):
            current_desc = products.get(code, {}).get("description", code)

        desc = col_b.text_input("Description", value=current_desc, key=f"desc_{item_id}")

        col_h, col_c, col_d, col_e = st.columns([1, 1, 1, 1])
        default_hsn = itm.get("hsn", "") or products.get(code, {}).get("hsn", "721550")
        hsn = col_h.text_input("HSN Code", value=default_hsn, key=f"hsn_{item_id}")

        pcs_val = str(itm.get("pcs", ""))
        pcs = col_c.text_input("Pcs", value=pcs_val, key=f"pcs_{item_id}")

        qty = col_d.number_input(
            "Qty (kg)", value=float(itm.get("qty", 0.0)),
            min_value=0.0, format="%.2f", key=f"qty_{item_id}"
        )
        rate = col_e.number_input(
            "Rate (₹/kg)", value=float(itm.get("rate", 0.0)),
            min_value=0.0, format="%.2f", key=f"rate_{item_id}"
        )

        # Update the item dict with current widget values
        itm["code"] = code
        itm["desc"] = desc
        itm["hsn"] = hsn
        itm["pcs"] = pcs
        itm["qty"] = qty
        itm["rate"] = rate

        edited_items.append(itm)

        if st.button("🗑️ Delete this item", key=f"del_{item_id}"):
            items_to_delete = item_id

# Handle deletion outside the loop to avoid index issues
if items_to_delete:
    st.session_state.items_list = [
        it for it in st.session_state.items_list if it.get("id") != items_to_delete
    ]
    st.rerun()

if st.button("➕ Add New Item"):
    st.session_state.items_list.append({
        "id": str(uuid.uuid4()),
        "code": "",
        "desc": "",
        "hsn": "721550",
        "pcs": "",
        "qty": 0.0,
        "rate": 0.0,
    })
    st.rerun()

# --- Calculations ---
total_taxable = sum(it.get("qty", 0) * it.get("rate", 0) for it in edited_items)
taxable_val = total_taxable + del_charges
cgst = taxable_val * 0.09
sgst = taxable_val * 0.09
grand_total = taxable_val + cgst + sgst

st.markdown("---")
mc1, mc2, mc3 = st.columns(3)
mc1.metric("Total Before Tax", f"₹{total_taxable:,.2f}")
mc2.metric("Taxable Value", f"₹{taxable_val:,.2f}")
mc3.metric("Grand Total", f"₹{grand_total:,.2f}")

# --- PDF Generation ---
if st.button("✅ Generate PDF", type="primary", use_container_width=True):
    if not edited_items:
        st.warning("Add at least one item before generating a PDF.")
    else:
        try:
            from pdf_generator import generate_invoice_pdf

            pdf_bytes = generate_invoice_pdf(
                doc_type=doc_type,
                inv_no=inv_no,
                inv_date=inv_date,
                client_name=selected_client_name,
                client_info=client_info,
                order_no=order_no,
                order_date=order_date,
                vehicle_no=vehicle_no,
                payment_terms=payment_terms,
                items=edited_items,
                del_charges=del_charges,
                products=products,
            )

            st.download_button(
                label="📥 Download / Share PDF",
                data=bytes(pdf_bytes),
                file_name=f"{inv_no.replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("PDF generated successfully!")
        except Exception as e:
            st.error(f"PDF generation failed: {str(e)}")
            st.exception(e)
