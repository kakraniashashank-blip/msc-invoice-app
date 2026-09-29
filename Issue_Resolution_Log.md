# Issue & Resolution Log: MSC Invoice App

This document serves as a detailed post-mortem of all technical bottlenecks encountered during the recent debugging session, identifying exactly why the app broke and how each issue was permanently resolved.

---

### 1. The Streamlit Cloud Build Crash
*   **Symptom:** The Streamlit app completely failed to deploy, throwing an Apt-Get error: `Package libgdk-pixbuf2.0-0 is not available`.
*   **Root Cause:** Streamlit Cloud upgraded its underlying operating system to a newer Debian version (Trixie), which officially obsoleted and removed the old `libgdk-pixbuf2.0-0` library required by WeasyPrint (the PDF generator).
*   **Resolution:** Updated `packages.txt` to use the modernized package names (`libgdk-pixbuf-2.0-0` and `libgdk-pixbuf-xlib-2.0-0`), successfully restoring the cloud build environment.

### 2. The "Red Box" Crash on Phone Uploads
*   **Symptom:** When uploading challan photos from a phone and clicking scan, the app would crash entirely, displaying a massive red `grpc._channel._InactiveRpcError` traceback and leaving all fields blank. 
*   **Root Cause:** The code was using `PIL.Image` to pass the photo to the Gemini SDK. High-resolution phone photos caused the payload size to bloat enormously during gRPC serialization, exceeding Google's maximum API payload limits and triggering a fatal crash that killed the Streamlit process before the UI could update.
*   **Resolution:** Rewrote the extraction pipeline to bypass the PIL library entirely. The app now extracts the raw, compressed bytes directly from the Streamlit uploader (`file.getvalue()`) and passes them with explicit MIME types. Wrapped the API call in a `try/except` block so that any future API failures result in a clean, user-friendly pop-up rather than an app-killing crash.

### 3. The 429 "Quota Exceeded" Block
*   **Symptom:** The user received a red UI error: `API Error during extraction: 429 You exceeded your current quota`.
*   **Root Cause:** Two intersecting issues:
    1. The code used a `for` loop to send each uploaded image as a separate API request. Uploading 2 images fired 2 requests instantly, tripping Google's strict Requests-Per-Minute (RPM) anti-spam limits.
    2. The app was hardcoded to use `gemini-3.6-flash`, which has an extremely restrictive Free Tier limit of just 20 Requests Per Day (RPD).
*   **Resolution:** 
    1. Re-architected the code to package all uploaded images into a **single** API request, bypassing the RPM burst limit.
    2. Switched the primary model to `gemini-3.5-flash-lite`, which grants a massive **500 RPD** allowance on the Free Tier.

### 4. UI Data Loss on Page-by-Page Scans
*   **Symptom:** If a user scanned Page 1 of an invoice, cleared the uploader, and then scanned Page 2, the items from Page 2 would completely overwrite the items from Page 1.
*   **Root Cause:** The state management logic was explicitly replacing the existing list (`st.session_state.items_list = new_items`) upon every successful scan.
*   **Resolution:** Updated the session state logic to **append** (`extend`) new items to the bottom of the list. Users can now safely process massive invoices one page at a time without losing previous data.

### 5. Server Timeouts & Google 503 Outages
*   **Symptom:** The app would hang on "Analyzing documents...", eventually failing. When tested, the Google API was directly returning a `503 Service Unavailable` error due to high global demand on the Free Tier.
*   **Root Cause:** 
    1. Multi-page OCR tasks take longer, sometimes hitting the default 60-second SDK timeout.
    2. Google aggressively deprioritizes/blocks Free Tier API keys during peak traffic spikes, locking the app out entirely.
*   **Resolution:** 
    1. Increased the explicit API timeout to 10 minutes (`timeout=600`) for large jobs.
    2. Adopted the user's `DRHP Analyzer` strategy: implemented an **Automatic Model Fallback Loop**. If the primary model (`3.5-flash-lite`) gets hit with a 503 outage or 429 limit, the app intercepts the failure, displays a toast notification (`"Model busy. Trying next..."`), and instantly retries the payload against a cascading list of alternative models (`3.6`, `3.8`, `3.7`, `3.5-flash`) until one succeeds.
