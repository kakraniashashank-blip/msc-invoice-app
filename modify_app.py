import sys

def modify_app():
    with open("app.py", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_lines = lines[:186]
    
    custom_block = [
        '# Initialize global fields in session state',
        'if "order_no" not in st.session_state: st.session_state.order_no = ""',
        'if "order_date" not in st.session_state: st.session_state.order_date = ""',
        'if "vehicle_no" not in st.session_state: st.session_state.vehicle_no = ""',
        'if "payment_terms" not in st.session_state: st.session_state.payment_terms = ""',
        'if "del_charges" not in st.session_state: st.session_state.del_charges = 0.0',
        'if "items_list" not in st.session_state: st.session_state.items_list = []',
        '',
        'st.subheader("Step 1: Order & Delivery Details")',
        'c1, c2, c3 = st.columns(3)',
        'order_no = c1.text_input("Order No.", key="order_no")',
        'order_date = c2.text_input("Order Date", key="order_date")',
        'vehicle_no = c3.text_input("Vehicle No.", key="vehicle_no")',
        '',
        'c4, c5 = st.columns(2)',
        'payment_terms = c4.text_input("Payment Terms", key="payment_terms")',
        'del_charges = c5.number_input("Delivery Charges (₹)", key="del_charges")',
        '',
        'st.subheader("Step 2: Upload Bills (Optional)")',
        'uploaded_files = st.file_uploader("📷 Snap Photos or Upload Bills", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)',
        '',
        'if uploaded_files:',
        '    if st.button("🔄 Scan Images & Extract Data"):',
        '        with st.spinner("Analyzing documents..."):',
        '            extracted_items = st.session_state.items_list.copy()',
        '            ',
        '            for i, file in enumerate(uploaded_files):',
        '                extracted = extract_bill_details(file)',
        '                if not extracted: continue',
        '                ',
        '                if i == 0:',
        '                    if not st.session_state.order_no and extracted.get("order_no"):',
        '                        st.session_state.order_no = extracted.get("order_no")',
        '                    if not st.session_state.order_date and extracted.get("order_date"):',
        '                        st.session_state.order_date = extracted.get("order_date")',
        '                    if not st.session_state.vehicle_no and extracted.get("vehicle_no"):',
        '                        st.session_state.vehicle_no = extracted.get("vehicle_no")',
        '                    if not st.session_state.payment_terms and extracted.get("payment_terms"):',
        '                        st.session_state.payment_terms = extracted.get("payment_terms")',
        '                    ',
        '                    if st.session_state.del_charges == 0.0:',
        '                        raw_del = extracted.get("delivery_charges", 0.0)',
        '                        try:',
        '                            dval = float(raw_del) if raw_del not in (None, "") else 0.0',
        '                        except:',
        '                            dval = 0.0',
        '                        if dval != 0.0:',
        '                            st.session_state.del_charges = dval',
        '                            ',
        '                extracted_items.extend(extracted.get("items", []))',
        '                ',
        '            st.session_state.items_list = extracted_items',
        '            st.rerun()',
        '',
        'st.subheader("Step 3: Items List")',
        'st.write("**Items List (Tap any box to adjust):**")',
        '',
        'edited_items = []',
        'for i, itm in enumerate(st.session_state.items_list):',
        '    with st.expander(f"Item #{i+1} - {itm.get(\'code\', \'\')}", expanded=True):',
        '        col_a, col_b = st.columns([1, 3])',
        '        code = col_a.text_input("Code", value=itm.get("code", ""), key=f"code_{i}")',
        '        ',
        '        default_desc = itm.get("desc", "")',
        '        if not default_desc or default_desc == code:',
        '            default_desc = MASTER_DESCRIPTIONS.get(code, code)',
        '            ',
        '        desc = col_b.text_input("Description", value=default_desc, key=f"desc_{i}")',
        '        ',
        '        col_h, col_c, col_d, col_e = st.columns([1, 1, 1, 1])',
        '        default_hsn = itm.get("hsn", "") or HSN_CODES.get(code, "721550")',
        '        hsn = col_h.text_input("HSN Code", value=default_hsn, key=f"hsn_{i}")',
        '        ',
        '        pcs = col_c.text_input("Pcs", value=str(itm.get("pcs", "")), key=f"pcs_{i}")',
        '        qty = col_d.number_input("Qty (kg)", value=float(itm.get("qty", 0.0)), key=f"qty_{i}")',
        '        rate = col_e.number_input("Rate (₹/kg)", value=float(itm.get("rate", 0.0)), key=f"rate_{i}")',
        '        ',
        '        itm["code"] = code',
        '        itm["desc"] = desc',
        '        itm["hsn"] = hsn',
        '        itm["pcs"] = pcs',
        '        itm["qty"] = qty',
        '        itm["rate"] = rate',
        '        ',
        '        edited_items.append(itm)',
        '        ',
        '        if st.button("🗑️ Delete this item", key=f"delete_{i}"):',
        '            st.session_state.items_list.pop(i)',
        '            st.rerun()',
        '',
        'if st.button("➕ Add New Item"):',
        '    st.session_state.items_list.append({',
        '        "code": "", "desc": "", "pcs": "", "qty": 0.0, "rate": 0.0',
        '    })',
        '    st.rerun()',
        ''
    ]
    
    new_lines.extend(custom_block)
    
    for line in lines[277:]:
        if line.startswith("    "):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
            
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(chr(10).join(new_lines) + chr(10))

if __name__ == "__main__":
    modify_app()
