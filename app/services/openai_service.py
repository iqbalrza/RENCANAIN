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


def generate_transport_recommendation(kota_asal: str, jumlah_orang: int, budget: int) -> list[dict]:
    """
    Generate rekomendasi transportasi dari kota asal ke Bandung.

    Returns list of dict, masing-masing berisi:
        moda, emoji, harga_min, harga_max, durasi, keterangan, tujuan_bandung
    """
    if _client and _deployment:
        try:
            system_prompt = """Kamu adalah asisten perjalanan Indonesia yang ahli dalam transportasi antar kota.
Berikan rekomendasi transportasi dari kota asal ke Bandung dalam format JSON.

FORMAT OUTPUT (HARUS valid JSON array):
[
  {
    "moda": "Kereta Api",
    "emoji": "🚆",
    "harga_min": 80000,
    "harga_max": 150000,
    "durasi": "2-3 jam",
    "keterangan": "Argo Parahyangan dari Gambir",
    "tujuan_bandung": "Stasiun Bandung"
  }
]

ATURAN:
- Berikan 2-4 opsi transportasi
- harga_min dan harga_max dalam angka (bukan string), dalam Rupiah per orang
- Urutkan dari yang paling direkomendasikan
- HANYA output JSON, tanpa penjelasan tambahan"""

            user_msg = (
                f"Rekomendasikan transportasi dari {kota_asal} ke Bandung "
                f"untuk {jumlah_orang} orang dengan total budget perjalanan Rp {budget:,}."
            )

            response = _client.chat.completions.create(
                model=_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            raw = response.choices[0].message.content.strip()
            # Bersihkan jika ada markdown code block
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0]
            result = json.loads(raw)
            if isinstance(result, list) and len(result) > 0:
                return result
        except Exception as e:
            logger.error(f"OpenAI transport recommendation failed: {e}")

    # Fallback lokal
    return _generate_local_transport(kota_asal)


def _generate_local_transport(kota_asal: str) -> list[dict]:
    """Generate rekomendasi transportasi fallback tanpa LLM."""
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
             "durasi": "2-4 jam", "keterangan": "Via Tol Cipularang, biaya tol ± Rp 100.000", "tujuan_bandung": "-"},
        ]
    elif kota in ["surabaya", "malang", "semarang", "yogyakarta", "solo"]:
        return [
            {"moda": "Pesawat", "emoji": "✈️", "harga_min": 500000, "harga_max": 1200000,
             "durasi": "1-2 jam", "keterangan": "Direct flight ke Husein Sastranegara", "tujuan_bandung": "Bandara Husein"},
            {"moda": "Kereta Api", "emoji": "🚆", "harga_min": 200000, "harga_max": 450000,
             "durasi": "6-10 jam", "keterangan": "Eksekutif / Bisnis", "tujuan_bandung": "Stasiun Bandung"},
            {"moda": "Bus AKAP", "emoji": "🚌", "harga_min": 150000, "harga_max": 300000,
             "durasi": "8-14 jam", "keterangan": "Bus malam, istirahat di bus", "tujuan_bandung": "Terminal Leuwi Panjang"},
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


