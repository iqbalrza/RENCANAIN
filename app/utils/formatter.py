"""
formatter.py — Format rupiah, waktu, dan jarak.
"""


def format_rupiah(amount: int | float) -> str:
    """Format angka menjadi format Rupiah Indonesia."""
    if amount >= 1_000_000:
        return f"Rp {amount:,.0f}".replace(",", ".")
    return f"Rp {amount:,.0f}".replace(",", ".")


def format_durasi(menit: int) -> str:
    """Format menit menjadi jam dan menit yang readable."""
    if menit < 60:
        return f"{menit} menit"
    jam = menit // 60
    sisa = menit % 60
    if sisa == 0:
        return f"{jam} jam"
    return f"{jam} jam {sisa} menit"


def format_jarak(km: float) -> str:
    """Format jarak dalam km."""
    if km < 1:
        return f"{km * 1000:.0f} m"
    return f"{km:.1f} km"


def format_rating(rating: float) -> str:
    """Format rating dengan bintang unicode."""
    full_stars = int(rating)
    half = rating - full_stars >= 0.3
    stars = "⭐" * full_stars
    if half:
        stars += "½"
    return f"{stars} ({rating:.1f})"
