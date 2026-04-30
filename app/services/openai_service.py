"""
openai_service.py — Azure OpenAI dengan RAG grounding.

PERUBAHAN UTAMA:
- generate_narrative() sekarang otomatis build context dari Azure Search
  via grounding.build_context_from_itinerary()
- GPT-4o hanya merespons berdasarkan dokumen yang di-retrieve,
  bukan dari training knowledge (anti-halusinasi)
"""

import json
from utils.logger import get_logger

logger = get_logger(__name__)

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
        logger.info("Azure OpenAI client initialized.")
    else:
        logger.warning("Azure OpenAI credentials not set — using local fallback.")
except Exception as e:
    logger.warning(f"Azure OpenAI not available: {e} — using local fallback.")


def extract_intent(form_data: dict) -> dict:
    """Parse form input → structured query untuk retrieval."""
    if _client and _deployment:
        try:
            system_prompt = """Kamu adalah asisten yang mengekstrak intent wisata dari form input.
Berikan output dalam format JSON dengan keys:
- search_queries: list string query untuk mencari wisata, hotel, dan kuliner
- budget_category: "budget" / "mid-range" / "premium"
- focus_areas: list area geografis yang relevan (e.g., "Lembang", "Ciwidey")
- meal_preferences: list tipe kuliner yang cocok"""

            response = _client.chat.completions.create(
                model=_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(form_data, ensure_ascii=False)},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI intent extraction failed: {e}")

    # Fallback lokal
    budget_per_orang_per_hari = (
        form_data.get("budget", 500000)
        / max(form_data.get("jumlah_orang", 1), 1)
        / max(form_data.get("durasi", 1), 1)
    )
    budget_cat = (
        "premium" if budget_per_orang_per_hari >= 500000
        else "mid-range" if budget_per_orang_per_hari >= 200000
        else "budget"
    )
    return {
        "search_queries": form_data.get("preferensi", ["Alam"]),
        "budget_category": budget_cat,
        "focus_areas": ["Bandung Pusat", "Lembang", "Ciwidey"],
        "meal_preferences": ["Sunda", "Jajanan", "Kafe"],
    }


def generate_narrative(itinerary_data: dict, context_docs: str = "") -> str:
    """
    Generate narasi itinerary dengan RAG grounding.

    Jika context_docs tidak disuplai dari luar, fungsi ini otomatis
    build context dari Azure AI Search via grounding.build_context_from_itinerary().
    Ini memastikan GPT-4o selalu punya grounding data yang akurat.
    """
    # ── Auto-build context dari Azure Search jika belum disuplai ──
    if not context_docs:
        try:
            from services.grounding import build_context_from_itinerary
            context_docs = build_context_from_itinerary(itinerary_data)
            logger.info(f"RAG context built: {len(context_docs)} chars")
        except Exception as e:
            logger.warning(f"Failed to build grounding context: {e}")
            context_docs = ""

    if _client and _deployment:
        try:
            from services.grounding import build_system_prompt
            system_prompt = build_system_prompt(context_docs)

            user_msg = (
                "Buatkan narasi perjalanan yang menarik berdasarkan itinerary berikut:\n\n"
                + json.dumps(itinerary_data.get("ringkasan", {}), ensure_ascii=False, indent=2)
            )

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

    return _generate_local_narrative(itinerary_data)


def _generate_local_narrative(itinerary_data: dict) -> str:
    """Generate narasi sederhana tanpa Azure OpenAI (fallback)."""
    ringkasan = itinerary_data.get("ringkasan", {})
    hotel = itinerary_data.get("hotel", {})
    days = itinerary_data.get("itinerary_per_hari", [])

    lines = [
        f"## 🌟 Itinerary Wisata Bandung — {ringkasan.get('durasi', 1)} Hari",
        f"**Dari:** {ringkasan.get('kota_asal', '-')} → **Bandung**",
        f"**Rombongan:** {ringkasan.get('jumlah_orang', 1)} orang",
        "",
    ]

    if hotel:
        lines += [
            f"### 🏨 Hotel: {hotel.get('nama', '-')}",
            f"📍 {hotel.get('alamat', '-')}",
            f"💰 Rp {hotel.get('harga_per_malam', 0):,.0f}/malam".replace(",", "."),
            "",
        ]

    for day in days:
        lines.append(f"### 📅 Hari {day['hari']}")
        for dest in day.get("destinasi", []):
            lines.append(f"- **{dest['nama']}** — {dest.get('deskripsi', '')}")
            if dest.get("harga_tiket", 0) > 0:
                lines.append(f"  🎫 Rp {dest['harga_tiket']:,.0f}/orang".replace(",", "."))
        lines.append("")
        for meal in day.get("kuliner", []):
            lines.append(
                f"- 🍽️ **{meal.get('waktu_makan', '')}:** {meal['nama']} "
                f"(Rp {meal.get('harga_per_orang', 0):,.0f}/orang)".replace(",", ".")
            )
        lines.append("")

    return "\n".join(lines)


def generate_transport_recommendation(kota_asal: str, jumlah_orang: int, budget: int) -> list[dict]:
    """Generate rekomendasi transportasi kota asal → Bandung."""
    if _client and _deployment:
        try:
            system_prompt = """Kamu adalah asisten perjalanan Indonesia yang ahli transportasi antar kota.
Berikan rekomendasi transportasi dari kota asal ke Bandung dalam format JSON array.

FORMAT (valid JSON array, HANYA JSON tanpa penjelasan):
[{"moda":"...","emoji":"...","harga_min":0,"harga_max":0,"durasi":"...","keterangan":"...","tujuan_bandung":"..."}]

ATURAN:
- 2-4 opsi, harga dalam Rupiah (integer), urutkan dari paling direkomendasikan"""

            response = _client.chat.completions.create(
                model=_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Transportasi dari {kota_asal} ke Bandung "
                        f"untuk {jumlah_orang} orang, budget total Rp {budget:,}."
                    )},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(raw)
            if isinstance(result, list) and result:
                return result
        except Exception as e:
            logger.error(f"OpenAI transport recommendation failed: {e}")

    return _generate_local_transport(kota_asal)


def _generate_local_transport(kota_asal: str) -> list[dict]:
    """Fallback rekomendasi transport lokal."""
    kota = kota_asal.strip().lower()

    if kota in ["jakarta", "bekasi", "tangerang", "depok", "bogor"]:
        return [
            {"moda": "Kereta Api", "emoji": "🚆", "harga_min": 80000, "harga_max": 150000,
             "durasi": "2-3 jam", "keterangan": "Argo Parahyangan / Pangandaran", "tujuan_bandung": "Stasiun Bandung"},
            {"moda": "Bus AKAP", "emoji": "🚌", "harga_min": 60000, "harga_max": 120000,
             "durasi": "3-4 jam", "keterangan": "Primajasa / X-Trans", "tujuan_bandung": "Terminal Leuwi Panjang"},
            {"moda": "Travel", "emoji": "🚐", "harga_min": 100000, "harga_max": 150000,
             "durasi": "3-4 jam", "keterangan": "Door-to-door, Cititrans / Baraya", "tujuan_bandung": "Berbagai titik"},
            {"moda": "Mobil Pribadi", "emoji": "🚗", "harga_min": 100000, "harga_max": 200000,
             "durasi": "2-4 jam", "keterangan": "Via Tol Cipularang, tol ± Rp 100.000", "tujuan_bandung": "-"},
        ]
    elif kota in ["surabaya", "malang", "semarang", "yogyakarta", "solo"]:
        return [
            {"moda": "Pesawat", "emoji": "✈️", "harga_min": 500000, "harga_max": 1200000,
             "durasi": "1-2 jam", "keterangan": "Direct ke Husein Sastranegara", "tujuan_bandung": "Bandara Husein"},
            {"moda": "Kereta Api", "emoji": "🚆", "harga_min": 200000, "harga_max": 450000,
             "durasi": "6-10 jam", "keterangan": "Eksekutif / Bisnis", "tujuan_bandung": "Stasiun Bandung"},
            {"moda": "Bus AKAP", "emoji": "🚌", "harga_min": 150000, "harga_max": 300000,
             "durasi": "8-14 jam", "keterangan": "Bus malam", "tujuan_bandung": "Terminal Leuwi Panjang"},
        ]
    else:
        return [
            {"moda": "Pesawat", "emoji": "✈️", "harga_min": 500000, "harga_max": 1500000,
             "durasi": "1-3 jam", "keterangan": "Direct / connecting ke Husein Sastranegara", "tujuan_bandung": "Bandara Husein"},
            {"moda": "Kereta + Sambung", "emoji": "🚆", "harga_min": 200000, "harga_max": 500000,
             "durasi": "Bervariasi", "keterangan": "Via Jakarta, lanjut ke Bandung", "tujuan_bandung": "Stasiun Bandung"},
            {"moda": "Bus AKAP", "emoji": "🚌", "harga_min": 150000, "harga_max": 400000,
             "durasi": "Bervariasi", "keterangan": "Tergantung jarak", "tujuan_bandung": "Terminal Leuwi Panjang"},
        ]