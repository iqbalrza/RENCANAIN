"""
upload_index.py — Upload dataset ke 3 Azure AI Search index.

Usage:
    python scripts/upload_index.py

Prerequisite:
    - Azure AI Search service sudah aktif
    - .env sudah dikonfigurasi dengan credentials yang benar
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    AZURE_SEARCH_INDEX_WISATA,
    AZURE_SEARCH_INDEX_HOTEL,
    AZURE_SEARCH_INDEX_KULINER,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_data(filename: str) -> list[dict]:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def upload_to_index(index_name: str, documents: list[dict]):
    """Upload documents ke Azure AI Search index."""
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential

        client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=index_name,
            credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
        )

        result = client.upload_documents(documents=documents)
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"  ✅ {succeeded}/{len(documents)} documents uploaded to '{index_name}'")

    except Exception as e:
        print(f"  ❌ Failed to upload to '{index_name}': {e}")


def main():
    print("📤 Uploading datasets to Azure AI Search...\n")

    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
        print("⚠️  Azure AI Search credentials not configured in .env")
        print("   Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY first.")
        return

    datasets = [
        ("wisata.json", AZURE_SEARCH_INDEX_WISATA),
        ("hotel.json", AZURE_SEARCH_INDEX_HOTEL),
        ("kuliner.json", AZURE_SEARCH_INDEX_KULINER),
    ]

    for filename, index_name in datasets:
        print(f"📁 {filename} → index '{index_name}'")
        data = load_data(filename)
        upload_to_index(index_name, data)

    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
