import io

new_block = """    if st.button("✅ Generate PDF", type="primary", use_container_width=True):
        try:
            from weasyprint import HTML
        except Exception as e:
            st.error("PDF generation is disabled on Windows. Please push to GitHub to use this feature on Streamlit Cloud.")
            st.stop()
            
        rows_html = ""
        for idx, itm in enumerate(edited_items, 1):
            desc = MASTER_DESCRIPTIONS.get(itm['code'], itm['code'])
            hsn = HSN_CODES.get(itm['code'], "721550")
            tax_val = itm['qty'] * itm['rate']
            rows_html += f'''
            <tr>
                <td>{idx}</td>
                <td>{itm['code']}</td>
                <td style="text-align: left; font-size: 9px;">{desc}</td>
                <td>{hsn}</td>
                <td>{itm.get('pcs', '')}</td>
                <td>{itm['qty']:,.2f}</td>
                <td style="text-align: right;">{itm['rate']:,.2f}</td>
                <td style="text-align: right;">{tax_val:,.2f}</td>
            </tr>
            '''

        full_html = f'''
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
                            <tr><td style="width:25%; border:none; padding:3px;">Name:</td><td style="border:none; padding:3px; font-weight:bold;">Lagan Engineering Co. Ltd.</td></tr>
                            <tr><td style="border:none; padding:3px;">Address:</td><td style="border:none; padding:3px;">14 Mohd. Ishaque Road, Kolkata - 700016</td></tr>
                            <tr><td style="border:none; padding:3px;">GSTIN:</td><td style="border:none; padding:3px; font-weight:bold;">19AAACT9986F1ZP</td></tr>
                            <tr><td style="border:none; padding:3px;">Order No.:</td><td style="border:none; padding:3px;">{order_no}</td></tr>
                            <tr><td style="border:none; padding:3px;">Order Date:</td><td style="border:none; padding:3px;">{order_date}</td></tr>
                            <tr><td style="border:none; padding:3px;">State:</td><td style="border:none; padding:3px;">West Bengal &nbsp;&nbsp;&nbsp; Code: 19</td></tr>
                        </table>
                    </td>
                    <td style="padding:0;">
                        <table style="width:100%; border-collapse:collapse;">
                            <tr><td style="width:35%; border:none; padding:3px;">Invoice No.:</td><td style="border:none; padding:3px; font-weight:bold;">{inv_no}</td></tr>
                            <tr><td style="border:none; padding:3px;">Invoice Date:</td><td style="border:none; padding:3px; font-weight:bold;">{inv_date}</td></tr>
                            <tr><td style="border:none; padding:3px;">Terms:</td><td style="border:none; padding:3px;">Proforma Invoice</td></tr>
                            <tr><td style="border:none; padding:3px;">Supply:</td><td style="border:none; padding:3px;">West Bengal</td></tr>
                        </table>
                    </td>
                </tr>
            </table>

            <table class="info-table" style="border-top:none;">
                <tr>
                    <td style="width: 55%; border-top:none;">Delivery At: Lagan Engineering Co. Ltd., Kolkata - 700016</td>
                    <td style="width: 20%; border-top:none;">Transport: Lorry</td>
                    <td style="width: 25%; border-top:none;">Vehicle No. : </td>
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
        '''
        
        pdf_bytes = HTML(string=full_html).write_pdf()
        st.download_button(
            label="📥 Download / Share PDF",
            data=pdf_bytes,
            file_name=f"{inv_no.replace('/', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
"""

with open("app_top.py", "r", encoding="utf-8") as f:
    top_content = f.read()

with open("app.py", "w", encoding="utf-8") as f:
    f.write(top_content)
    f.write(new_block)
