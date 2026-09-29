"""
Central configuration for the Research Synthesizer.
All model names, prompts, chunk sizes, and tuning knobs live here.
"""

# ---------------------------------------------------------------------------
# Gemini Models
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "gemini-embedding-2"
GENERATION_MODEL = "gemini-3.5-flash"
CLASSIFICATION_MODEL = "gemini-3.5-flash"

EMBEDDING_DIMENSIONS = 768

# ---------------------------------------------------------------------------
# Crawler Settings
# ---------------------------------------------------------------------------
MAX_CONCURRENT_FETCHES = 5
FETCH_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
MAX_PDF_SIZE_MB = 50

# Links to always skip (regex patterns matched against the full URL)
SKIP_URL_PATTERNS = [
    r"mailto:",
    r"javascript:",
    r"tel:",
    r"#$",                          # bare anchors
    r"(facebook|twitter|linkedin|instagram|youtube\.com/channel)\.com",
    r"(login|signin|signup|register|auth)",
    r"\.(css|js|ico|svg|woff|ttf|eot)$",
    r"\.(jpg|jpeg|png|gif|webp|bmp)$",
]

# ---------------------------------------------------------------------------
# Processing Settings
# ---------------------------------------------------------------------------
CHUNK_SIZE_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 100
# Rough approximation: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4

# ---------------------------------------------------------------------------
# Knowledge Base
# ---------------------------------------------------------------------------
LANCEDB_PATH = "./data/lancedb"
DEFAULT_TOP_K = 6

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
LINK_CLASSIFICATION_PROMPT = """\
You are an expert research analyst. Given a list of links found on a webpage, \
classify each link into one of these categories:

Categories:
- FINANCIAL_REPORT: Annual reports, quarterly results, balance sheets, financial statements
- EARNINGS_TRANSCRIPT: Earnings call transcripts, investor presentations, conference calls
- PRESS_RELEASE: Company announcements, news releases
- REGULATORY_FILING: SEC filings, stock exchange submissions, regulatory documents
- OTHER_RELEVANT: Any other substantive content worth reading (research papers, whitepapers, etc.)
- IRRELEVANT: Privacy policies, careers pages, login/signup, social media, ads, navigation, cookie policies, terms of service

For each link, provide:
- category: one of the categories above
- confidence: float between 0.0 and 1.0
- reason: brief 1-sentence justification
- recommended: boolean — true if this link should be fetched for research

Context: The seed URL is "{seed_url}".

Links to classify (JSON array):
{links_json}

Respond with ONLY a valid JSON array of objects, each with keys: \
url, category, confidence, reason, recommended.
Do NOT wrap in markdown code fences.
"""

RAG_SYSTEM_PROMPT = """\
You are a precise research assistant. Answer the user's question using ONLY \
the provided source documents below. Follow these rules strictly:

1. Base your answer entirely on the provided context. Do not use outside knowledge.
2. Cite sources inline using [1], [2], etc. corresponding to the source numbers.
3. If the context does not contain enough information, say: \
"I don't have enough information in the loaded sources to answer this."
4. Keep answers clear, structured, and concise. Use bullet points or tables where helpful.
5. When quoting directly from a source, use quotation marks and cite the source.

SOURCE DOCUMENTS:
{context}
"""
