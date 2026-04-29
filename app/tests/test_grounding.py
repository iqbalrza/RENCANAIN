"""Tests for grounding.py"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.grounding import build_context_documents, build_system_prompt


def test_build_context_documents():
    intent = {
        "search_queries": ["Alam"],
        "budget_category": "budget",
        "focus_areas": ["Lembang"],
        "meal_preferences": ["Sunda"],
    }
    form_data = {
        "kota_asal": "Jakarta",
        "durasi": 3,
        "jumlah_orang": 2,
        "budget": 1_000_000,
        "preferensi": ["Alam"],
    }
    context = build_context_documents(intent, form_data)
    assert len(context) > 0
    assert "DESTINASI WISATA" in context
    print("✅ test_build_context_documents passed")


def test_build_system_prompt():
    prompt = build_system_prompt("test context")
    assert "BandungTrip AI" in prompt
    assert "test context" in prompt
    assert "JANGAN" in prompt
    print("✅ test_build_system_prompt passed")


if __name__ == "__main__":
    test_build_context_documents()
    test_build_system_prompt()
    print("\n🎉 All grounding tests passed!")
