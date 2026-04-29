"""
config.py — Load environment variables & Azure credentials.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── Azure OpenAI ──────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# ── Azure AI Search ──────────────────────────────────────────
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
AZURE_SEARCH_INDEX_WISATA = os.getenv("AZURE_SEARCH_INDEX_WISATA", "wisata-alam")
AZURE_SEARCH_INDEX_HOTEL = os.getenv("AZURE_SEARCH_INDEX_HOTEL", "hotel-budget")
AZURE_SEARCH_INDEX_KULINER = os.getenv("AZURE_SEARCH_INDEX_KULINER", "kuliner-lokal")

# ── Azure Maps ───────────────────────────────────────────────
AZURE_MAPS_API_KEY = os.getenv("AZURE_MAPS_API_KEY", "")

# ── Budget Allocation Ratios ─────────────────────────────────
BUDGET_RATIO_HOTEL = 0.40
BUDGET_RATIO_WISATA = 0.25
BUDGET_RATIO_KULINER = 0.25
BUDGET_RATIO_TRANSPORT = 0.10

# ── Bandung Center Coordinate ────────────────────────────────
BANDUNG_LAT = -6.9175
BANDUNG_LNG = 107.6191
