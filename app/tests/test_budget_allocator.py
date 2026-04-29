"""Tests for budget_allocator.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.budget_allocator import allocate_budget, get_budget_per_day, check_budget_fit


def test_allocate_budget():
    result = allocate_budget(1_000_000)
    assert result["hotel"] == 400_000
    assert result["wisata"] == 250_000
    assert result["kuliner"] == 250_000
    assert result["transport"] == 100_000
    assert result["total"] == 1_000_000
    print("✅ test_allocate_budget passed")


def test_budget_per_day():
    alloc = allocate_budget(1_000_000)
    per_day = get_budget_per_day(alloc, 2)
    assert per_day["hotel_per_malam"] == 200_000
    assert per_day["wisata_per_hari"] == 125_000
    print("✅ test_budget_per_day passed")


def test_check_budget_fit():
    alloc = allocate_budget(500_000)
    actual = {"hotel": 180_000, "wisata": 100_000, "kuliner": 120_000, "transport": 50_000}
    result = check_budget_fit(alloc, actual)
    assert result["total"]["sisa"] == 50_000
    assert result["total"]["over_budget"] is False
    print("✅ test_check_budget_fit passed")


if __name__ == "__main__":
    test_allocate_budget()
    test_budget_per_day()
    test_check_budget_fit()
    print("\n🎉 All budget_allocator tests passed!")
