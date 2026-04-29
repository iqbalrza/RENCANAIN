"""Tests for search_service.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.search_service import search_wisata, search_hotel, search_kuliner, search_all


def test_search_wisata():
    results = search_wisata("alam", top=3)
    assert len(results) > 0
    assert "nama" in results[0]
    print(f"✅ test_search_wisata passed — found {len(results)} results")


def test_search_hotel():
    results = search_hotel("budget", top=3)
    assert len(results) > 0
    print(f"✅ test_search_hotel passed — found {len(results)} results")


def test_search_kuliner():
    results = search_kuliner("sunda", top=3)
    assert len(results) > 0
    print(f"✅ test_search_kuliner passed — found {len(results)} results")


def test_search_all():
    results = search_all("bandung", top_per_category=2)
    assert "wisata" in results
    assert "hotel" in results
    assert "kuliner" in results
    print("✅ test_search_all passed")


if __name__ == "__main__":
    test_search_wisata()
    test_search_hotel()
    test_search_kuliner()
    test_search_all()
    print("\n🎉 All search_service tests passed!")
