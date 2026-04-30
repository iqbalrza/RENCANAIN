"""
create_index.py — Buat schema index di Azure AI Search.

HARUS dijalankan SEBELUM upload_index.py.
Mendefinisikan field schema yang benar agar OData filter
(harga_tiket le 50000, rating ge 4.0, dll) bisa berfungsi.

Tanpa schema yang benar, Azure Search tidak tahu tipe data tiap field
sehingga filter numerik akan gagal.

Usage:
    cd app
    python scripts/create_index.py
"""

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


def create_indexes():
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_API_KEY:
        print("⚠️  Azure AI Search credentials tidak ditemukan di .env")
        print("   Set AZURE_SEARCH_ENDPOINT dan AZURE_SEARCH_API_KEY terlebih dahulu.")
        return

    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex,
            SearchField,
            SearchFieldDataType,
            SimpleField,
            SearchableField,
            ComplexField,
        )
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        print("❌ Package azure-search-documents belum terinstall.")
        print("   Jalankan: pip install azure-search-documents")
        return

    client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    # ── Schema wisata ────────────────────────────────────────
    wisata_fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="nama", type=SearchFieldDataType.String, sortable=True),
        SimpleField(name="kategori", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="deskripsi", type=SearchFieldDataType.String),
        SearchableField(name="alamat", type=SearchFieldDataType.String),
        SimpleField(name="harga_tiket", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="lat", type=SearchFieldDataType.Double),
        SimpleField(name="lng", type=SearchFieldDataType.Double),
        SimpleField(name="jam_operasional", type=SearchFieldDataType.String),
        SimpleField(name="durasi_kunjungan_menit", type=SearchFieldDataType.Int32),
        # tags: Collection of String agar bisa di-search per tag
        SearchableField(
            name="tags",
            type=SearchFieldDataType.String,
            collection=True,
            filterable=True,
            facetable=True,
        ),
        SearchableField(
            name="fasilitas",
            type=SearchFieldDataType.String,
            collection=True,
        ),
    ]

    # ── Schema hotel ─────────────────────────────────────────
    hotel_fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="nama", type=SearchFieldDataType.String, sortable=True),
        SimpleField(name="kategori", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="deskripsi", type=SearchFieldDataType.String),
        SearchableField(name="alamat", type=SearchFieldDataType.String),
        # harga_per_malam harus Int32/Int64 agar filter "le 500000" bisa jalan
        SimpleField(name="harga_per_malam", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="lat", type=SearchFieldDataType.Double),
        SimpleField(name="lng", type=SearchFieldDataType.Double),
        SearchableField(
            name="fasilitas",
            type=SearchFieldDataType.String,
            collection=True,
            filterable=True,
        ),
        SearchableField(
            name="tags",
            type=SearchFieldDataType.String,
            collection=True,
            filterable=True,
            facetable=True,
        ),
    ]

    # ── Schema kuliner ───────────────────────────────────────
    kuliner_fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="nama", type=SearchFieldDataType.String, sortable=True),
        SimpleField(name="kategori", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="deskripsi", type=SearchFieldDataType.String),
        SearchableField(name="alamat", type=SearchFieldDataType.String),
        SimpleField(name="harga_per_orang", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="lat", type=SearchFieldDataType.Double),
        SimpleField(name="lng", type=SearchFieldDataType.Double),
        SimpleField(name="jam_operasional", type=SearchFieldDataType.String),
        SearchableField(
            name="tags",
            type=SearchFieldDataType.String,
            collection=True,
            filterable=True,
            facetable=True,
        ),
    ]

    indexes = [
        (AZURE_SEARCH_INDEX_WISATA,  wisata_fields,  "wisata"),
        (AZURE_SEARCH_INDEX_HOTEL,   hotel_fields,   "hotel"),
        (AZURE_SEARCH_INDEX_KULINER, kuliner_fields, "kuliner"),
    ]

    for index_name, fields, label in indexes:
        try:
            index = SearchIndex(name=index_name, fields=fields)
            result = client.create_or_update_index(index)
            print(f"  ✅ Index '{result.name}' created/updated ({label})")
        except Exception as e:
            print(f"  ❌ Gagal membuat index '{index_name}': {e}")


def main():
    print("🏗️  Creating Azure AI Search indexes...\n")
    create_indexes()
    print("\n✅ Selesai! Sekarang jalankan: python scripts/upload_index.py")


if __name__ == "__main__":
    main()