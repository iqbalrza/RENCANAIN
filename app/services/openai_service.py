"""
openai_service.py — Azure OpenAI: Intent extraction & generate itinerary narrative.

Saat Azure OpenAI belum dikonfigurasi, module ini akan menggunakan
fallback lokal sehingga aplikasi tetap bisa berjalan.
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Coba import Azure OpenAI ──────────────────────────────────
_client = None
_deployment = None

try:
    from openai import AzureOpenAI
    from config import (
        AZURE_OPENAI_ENDPOINT,
        AZURE_OPENAI_API_KEY,
        AZURE_OPENAI_DEPLOYMENT,
        AZURE_OPENAI_API_VERSION,
    )

    _is_placeholder = (
        not AZURE_OPENAI_ENDPOINT
        or not AZURE_OPENAI_API_KEY
        or "your-" in AZURE_OPENAI_API_KEY
        or "your-" in AZURE_OPENAI_ENDPOINT
    )

    if not _is_placeholder:
        _client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        _deployment = AZURE_OPENAI_DEPLOYMENT
        logger.info("Azure OpenAI client initialized successfully.")
    else:
        logger.warning("Azure OpenAI credentials not set or placeholder — using local fallback.")
except Exception as e:
    logger.warning(f"Azure OpenAI not available: {e} — using local fallback.")


def extract_intent(form_data: dict) -> dict:
    """
    Parse parameter form menjadi query terstruktur untuk retrieval.

    Input: dict dengan keys kota_asal, durasi, jumlah_orang, budget, preferensi
    Output: dict query terstruktur
    """
    if _client and _deployment:
        try:
            system_prompt = """Kamu adalah asisten yang mengekstrak intent wisata dari form input.
Berikan output dalam format JSON dengan keys:
- search_queries: list string query untuk mencari wisata, hotel, dan kuliner
- budget_category: "budget" / "mid-range" / "premium" berdasarkan budget per orang per hari
- focus_areas: list area geografis yang relevan (e.g., "Lembang", "Ciwidey", "Pusat Kota")
- meal_preferences: list tipe kuliner yang cocok"""

            user_msg = json.dumps(form_data, ensure_ascii=False)
            response = _client.chat.completions.create(
                model=_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            logger.error(f"OpenAI intent extraction failed: {e}")

    # Fallback lokal
    budget_per_orang_per_hari = (
        form_data.get("budget", 500000) /
        max(form_data.get("jumlah_orang", 1), 1) /
        max(form_data.get("durasi", 1), 1)
    )

    if budget_per_orang_per_hari >= 500000:
        budget_cat = "premium"
    elif budget_per_orang_per_hari >= 200000:
        budget_cat = "mid-range"
    else:
        budget_cat = "budget"

    return {
        "search_queries": form_data.get("preferensi", ["Alam"]),
        "budget_category": budget_cat,
        "focus_areas": ["Bandung Pusat", "Lembang", "Ciwidey"],
        "meal_preferences": ["Sunda", "Jajanan", "Kafe"],
    }


def generate_narrative(itinerary_data: dict, context_docs: str = "") -> str:
    """
    Generate narasi itinerary dari data terstruktur.

    Menggunakan grounding strategy: hanya berdasarkan data yang diberikan.
    """
    if _client and _deployment:
        try:
            system_prompt = f"""Kamu adalah pemandu wisata profesional Bandung.
Buatkan narasi itinerary yang informatif dan menarik berdasarkan DATA BERIKUT SAJA.
Jangan menambahkan informasi dari pengetahuan umummu — hanya gunakan data yang diberikan.

CONTEXT DOCUMENTS:
{context_docs}

FORMAT OUTPUT:
- Gunakan bahasa Indonesia yang ramah dan informatif
- Sertakan tips perjalanan yang relevan
- Sebutkan estimasi biaya untuk setiap aktivitas"""

            user_msg = json.dumps(itinerary_data, ensure_ascii=False, indent=2)
            response = _client.chat.completions.create(
                model=_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI narrative generation failed: {e}")

    # Fallback: generate simple narrative locally
    return _generate_local_narrative(itinerary_data)


def _generate_local_narrative(itinerary_data: dict) -> str:
    """Generate narasi sederhana tanpa Azure OpenAI."""
    ringkasan = itinerary_data.get("ringkasan", {})
    hotel = itinerary_data.get("hotel", {})
    days = itinerary_data.get("itinerary_per_hari", [])

    lines = []
    lines.append(f"## 🌟 Itinerary Wisata Bandung — {ringkasan.get('durasi', 1)} Hari")
    lines.append(f"**Dari:** {ringkasan.get('kota_asal', '-')} → **Bandung**")
    lines.append(f"**Rombongan:** {ringkasan.get('jumlah_orang', 1)} orang")
    lines.append("")

    if hotel:
        lines.append(f"### 🏨 Hotel: {hotel.get('nama', '-')}")
        lines.append(f"📍 {hotel.get('alamat', '-')}")
        lines.append(f"💰 Rp {hotel.get('harga_per_malam', 0):,}/malam".replace(",", "."))
        lines.append("")

    for day in days:
        lines.append(f"### 📅 Hari {day['hari']}")
        for dest in day.get("destinasi", []):
            lines.append(f"- **{dest['nama']}** — {dest.get('deskripsi', '')}")
            if dest.get("harga_tiket", 0) > 0:
                lines.append(f"  🎫 Rp {dest['harga_tiket']:,}/orang".replace(",", "."))
            lines.append(f"  ⏰ {dest.get('jam_operasional', '-')} ({dest.get('durasi_kunjungan_menit', 60)} menit)")
        lines.append("")
        for meal in day.get("kuliner", []):
            lines.append(f"- 🍽️ **{meal.get('waktu_makan', '')}:** {meal['nama']} (Rp {meal.get('harga_per_orang', 0):,}/orang)".replace(",", "."))
        lines.append("")

    return "\n".join(lines)
