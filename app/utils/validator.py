"""
validator.py — Validasi input form.
"""

PREFERENSI_OPTIONS = ["Alam", "Kota", "Kuliner", "Budaya", "Hiburan"]

MIN_BUDGET = 100_000
MAX_ORANG = 20
MAX_DURASI = 7


def validate_form(kota_asal: str, durasi: int, jumlah_orang: int,
                   budget: int, preferensi: list[str]) -> tuple[bool, str]:
    """
    Validasi seluruh field form input.
    Returns (is_valid, error_message).
    """
    if not kota_asal or len(kota_asal.strip()) < 3:
        return False, "Kota asal harus diisi minimal 3 karakter."

    if durasi < 1 or durasi > MAX_DURASI:
        return False, f"Durasi harus antara 1 - {MAX_DURASI} hari."

    if jumlah_orang < 1 or jumlah_orang > MAX_ORANG:
        return False, f"Jumlah orang harus antara 1 - {MAX_ORANG}."

    if budget < MIN_BUDGET:
        return False, f"Budget minimal Rp {MIN_BUDGET:,}".replace(",", ".")

    if not preferensi or len(preferensi) < 1:
        return False, "Pilih minimal 1 preferensi wisata."

    for pref in preferensi:
        if pref not in PREFERENSI_OPTIONS:
            return False, f"Preferensi '{pref}' tidak valid."

    return True, ""
