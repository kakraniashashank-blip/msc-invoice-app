import json
import google.generativeai as genai


def _notify(msg, level="info"):
    """Show notification via Streamlit if available, else print."""
    try:
        import streamlit as st
        if level == "error":
            st.error(msg)
        else:
            st.toast(msg)
    except Exception:
        print(f"[{level.upper()}] {msg}")


def extract_bill_details(image_files):
    """
    Extract billing and item details from uploaded bill/PO images using Gemini.
    
    Args:
        image_files: List of file-like objects with .name, .getvalue(), .seek() methods
    
    Returns:
        dict with keys: order_no, order_date, vehicle_no, payment_terms, 
                       delivery_charges, items (list of dicts with code, desc, pcs, qty, rate)
        Empty dict on failure.
    """
    prompt = """
    Extract all billing and item details from these bill/PO images into a clean JSON structure.
    Combine items from all images into a single 'items' array.
    {
      "order_no": "P/2627/1552",
      "order_date": "07-08-2026",
      "vehicle_no": "WB-02-1234",
      "payment_terms": "Net 30 Days",
      "delivery_charges": 16500,
      "items": [
        {
          "code": "09083BL",
          "desc": "BR.MS 1-31/32\"(50MM) DIA. TOL -0.001\"/-0.004\"",
          "pcs": 0,
          "qty": 560.0,
          "rate": 70.0
        }
      ]
    }
    IMPORTANT RULES:
    - Extract the 'code' from the 'Part No.' column (e.g. 09083BL, 09112BL)
    - Extract 'desc' from the 'Description of Goods' column - use the FULL description text
    - Extract 'qty' as a number in KG
    - Extract 'rate' as a number per KG
    - For 'vehicle_no', also check 'Lorry No' or 'Transport No'
    - Extract handwritten overrides if present
    - If any field is missing, use null or 0
    - Return ONLY valid JSON, no markdown fences
    """

    try:
        payload = [prompt]
        for image_file in image_files:
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            file_bytes = image_file.getvalue()

            name = image_file.name.lower()
            if name.endswith('.pdf'):
                mime = "application/pdf"
            elif name.endswith('.png'):
                mime = "image/png"
            else:
                mime = "image/jpeg"

            payload.append({"mime_type": mime, "data": file_bytes})

        # Model fallback cascade
        fallback_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
        ]

        last_err = None
        for i, model_name in enumerate(fallback_models):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    payload, request_options={"timeout": 600}
                )
                clean_text = (
                    response.text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                if i > 0:
                    _notify(f"✅ Succeeded using fallback model: {model_name}")
                return json.loads(clean_text)
            except Exception as e:
                last_err = e
                error_msg = str(e).lower()
                if "api key" in error_msg or "invalid argument" in error_msg:
                    raise e
                _notify(f"Model {model_name} busy. Trying next...")
                continue

        raise last_err or Exception("All Gemini models failed due to server load.")

    except Exception as e:
        _notify(f"API Error during extraction: {str(e)}", level="error")
        return {}
